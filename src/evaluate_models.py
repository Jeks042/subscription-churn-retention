"""Frozen temporal baselines and one-shot retrospective holdout assessment.

All private model bundles, scores and customer keys remain under data/models.
Only explicitly aggregate JSON/SVG artifacts may be published.
"""
import argparse
import hashlib
import importlib.metadata
import json
import math
import platform
import tempfile
import warnings
from datetime import datetime, timezone
from pathlib import Path

import duckdb
import joblib
import numpy as np
from scipy.special import expit, logit
from sklearn.exceptions import ConvergenceWarning
from sklearn.linear_model import LogisticRegression
from sklearn.preprocessing import StandardScaler
from threadpoolctl import threadpool_limits

try:
    from .build_sql import CALENDAR
    from .feature_contract import MODEL_PREDICTORS, TRANSACTION_FEATURES
except ImportError:
    from build_sql import CALENDAR
    from feature_contract import MODEL_PREDICTORS, TRANSACTION_FEATURES

ROOT = Path(__file__).resolve().parents[1]
CAPACITIES = (0.05, 0.10, 0.20)
SEED = 20260922
FAMILIES = ['prevalence', 'renewal_rule', 'recency', 'transactions', 'combined']
BOOTSTRAPS = 200


def digest(path):
    with Path(path).open('rb') as stream:
        return hashlib.file_digest(stream, 'sha256').hexdigest()


def write_json(path, value):
    Path(path).write_text(json.dumps(value, indent=2, default=str, allow_nan=False)+'\n', encoding='utf-8')


def rows(con, query, params=None):
    cur = con.execute(query, params or [])
    return [dict(zip([d[0] for d in cur.description], row)) for row in cur.fetchall()]


def feature_names(family):
    if family == 'recency':
        return ['transaction_recency_days']
    if family == 'transactions':
        return TRANSACTION_FEATURES
    if family == 'no_duration':
        return [n for n in MODEL_PREDICTORS if 'listening_bounded_seconds' not in n]
    return MODEL_PREDICTORS


def transformed(x):
    return np.sign(x)*np.log1p(np.abs(x))


def renewal_group(x):
    cancel = x[:, MODEL_PREDICTORS.index('cancellation_count_90d')] > 0
    no_auto = x[:, MODEL_PREDICTORS.index('auto_renew_flag_count_90d')] == 0
    return cancel.astype(int)*2 + no_auto.astype(int)


def fit_base(family, x, y, c=1):
    if family == 'prevalence':
        return {'family': family, 'probability': float(y.mean())}
    if family == 'renewal_rule':
        g = renewal_group(x)
        rate = [(float(y[g == j].sum())+100*y.mean())/(int((g == j).sum())+100) for j in range(4)]
        return {'family': family, 'rates': rate}
    names = feature_names(family)
    indices = [MODEL_PREDICTORS.index(n) for n in names]
    z = transformed(x[:, indices])
    scaler = StandardScaler(copy=False).fit(z)
    z = scaler.transform(z)
    estimator = LogisticRegression(C=c, solver='lbfgs', max_iter=1000, tol=1e-7)
    with warnings.catch_warnings():
        warnings.simplefilter('error', ConvergenceWarning)
        estimator.fit(z, y)
    return {'family': family, 'names': names, 'indices': indices,
            'scaler': scaler, 'estimator': estimator, 'C': c}


def predict_base(model, x):
    if model['family'] == 'prevalence':
        return np.full(len(x), model['probability'])
    if model['family'] == 'renewal_rule':
        return np.asarray(model['rates'])[renewal_group(x)]
    z = model['scaler'].transform(transformed(x[:, model['indices']]))
    return model['estimator'].predict_proba(z)[:, 1]


def fit_calibrator(p, y):
    if np.ptp(p) < 1e-12:
        return {'constant': float(y.mean())}
    estimator = LogisticRegression(C=1e6, solver='lbfgs', max_iter=1000, tol=1e-7)
    with warnings.catch_warnings():
        warnings.simplefilter('error', ConvergenceWarning)
        estimator.fit(logit(np.clip(p, 1e-12, 1-1e-12)).reshape(-1, 1), y)
    slope, intercept = float(estimator.coef_[0, 0]), float(estimator.intercept_[0])
    if slope <= 0:
        raise ValueError('Calibration reversed ranking; stop for review before holdout')
    return {'slope': slope, 'intercept': intercept}


def calibrate(cal, p):
    if 'constant' in cal:
        return np.full(len(p), cal['constant'])
    return expit(cal['intercept']+cal['slope']*logit(np.clip(p, 1e-12, 1-1e-12)))


class RankedMetrics:
    """Reuse sorted arrays for weighted customer-bootstrap metrics, including ties."""
    def __init__(self, y, p, tie):
        self.order = np.lexsort((tie, -p))
        self.y, self.p = np.asarray(y)[self.order], np.asarray(p)[self.order]
        self.ends = np.r_[np.flatnonzero(np.diff(self.p) != 0), len(y)-1]
        p_safe = np.clip(self.p, 1e-12, 1-1e-12)
        self.loss = -(self.y*np.log(p_safe)+(1-self.y)*np.log1p(-p_safe))
        self.squared = (self.p-self.y)**2

    def evaluate(self, weights=None):
        w = np.ones(len(self.y)) if weights is None else np.asarray(weights, dtype=float)[self.order]
        total = float(w.sum())
        positives = float(w @ self.y)
        negatives = total-positives
        cw = np.cumsum(w)
        cp = np.cumsum(w*self.y)
        tp, fp = cp[self.ends], (cw-cp)[self.ends]
        dtp, dfp = np.diff(np.r_[0, tp]), np.diff(np.r_[0, fp])
        ap = float(np.sum(dtp*np.divide(tp, tp+fp, out=np.zeros_like(tp), where=(tp+fp)>0))/positives) if positives else None
        auc = float(np.sum(dfp*(tp-dtp/2))/(positives*negatives)) if positives and negatives else None
        result = {'rows': int(total), 'churn': int(positives), 'prevalence': positives/total,
                  'mean_prediction': float(w @ self.p/total), 'log_loss': float(w @ self.loss/total),
                  'brier': float(w @ self.squared/total), 'average_precision': ap, 'roc_auc': auc}
        for f in CAPACITIES:
            k = int(math.floor(total*f))
            label = f'{int(f*100)}pct'
            if k == 0:
                continue
            end = int(np.searchsorted(cw, k, side='left'))
            prior_w = cw[end-1] if end else 0
            true = (cp[end-1] if end else 0)+(k-prior_w)*self.y[end]
            precision = float(true/k)
            result.update({f'contacts_{label}': k, f'tp_{label}': int(true), f'fp_{label}': int(k-true),
                           f'fn_{label}': int(positives-true), f'precision_{label}': precision,
                           f'recall_{label}': float(true/positives) if positives else None,
                           f'lift_{label}': precision/(positives/total) if positives else None})
        return result


def metrics(y, p, tie):
    return RankedMetrics(y, p, tie).evaluate()


def calibration_bins(y, p):
    result = []
    bins = np.minimum((p*10).astype(int), 9)
    for i in range(10):
        mask = bins == i
        result.append({'low': i/10, 'high': (i+1)/10, 'rows': int(mask.sum()),
                       'mean_prediction': float(p[mask].mean()) if mask.any() else None,
                       'churn_rate': float(y[mask].mean()) if mask.any() else None})
    return result


def score_deciles(y, p):
    # Equal-frequency descriptive bins; equal scores can cross bin boundaries.
    return [{'rows': len(ix), 'mean_prediction': float(p[ix].mean()), 'churn_rate': float(y[ix].mean())}
            for ix in np.array_split(np.argsort(p, kind='stable'), 10) if len(ix)]


def choose_family(selection):
    best = min(selection[n]['log_loss'] for n in FAMILIES)
    return next(n for n in FAMILIES if selection[n]['log_loss'] <= best*1.005)


def bootstrap_comparison(y, predictions, ties, selected, comparator, replicates=BOOTSTRAPS):
    rng = np.random.default_rng(SEED)
    names = list(dict.fromkeys([selected, comparator]))
    rankers = {n: RankedMetrics(y, predictions[n], ties) for n in names}
    fields = ['log_loss', 'brier', 'average_precision', 'roc_auc'] + [f'{m}_{int(c*100)}pct' for c in CAPACITIES for m in ['precision', 'recall', 'lift']]
    samples = {n: {k: [] for k in fields} for n in names}
    differences = {k: [] for k in fields}
    for r in range(replicates):
        w = rng.poisson(1, len(y)).astype(float)
        measured = {n: rankers[n].evaluate(w) for n in names}
        for n in names:
            for k in fields:
                samples[n][k].append(measured[n][k])
        for k in fields:
            differences[k].append(measured[selected][k]-measured[comparator][k])
        if (r+1) % 50 == 0:
            print(f'Customer bootstrap {r+1}/{replicates}', flush=True)
    interval = lambda d: {k: [float(v) for v in np.quantile(a, [.025, .975])] for k, a in d.items()}
    return {'method': 'Poisson(1) customer weights; one row/customer in holdout; conditional on frozen fits',
            'replicates': replicates, 'seed': SEED, 'interval_level': .95,
            'models': {n: interval(v) for n, v in samples.items()},
            'paired_difference': {'selected': selected, 'comparator': comparator, 'intervals': interval(differences)}}


def connect(database):
    con = duckdb.connect(str(database), read_only=True)
    con.execute('SET threads=4')
    con.execute("SET memory_limit='3GB'")
    return con


def verify_inputs(con, database):
    parent = database.parent
    manifests = {}
    for name in ['sql_build_summary.json', 'listening_build_summary.json']:
        p = parent/name
        report = json.loads(p.read_text(encoding='utf-8'))
        if report['assertions'] != 'passed':
            raise ValueError('Feature build not validated')
        for filename, checksum in report['sql_sha256'].items():
            if digest(ROOT/'sql'/filename) != checksum:
                raise ValueError('SQL changed after build: '+filename)
        for filename, checksum in report.get('python_sha256', {}).items():
            if digest(ROOT/'src'/filename) != checksum:
                raise ValueError('Feature code changed after build: '+filename)
        manifests[name] = digest(p)
    checked = ROOT/'reports/listening_feature_check.json'
    check = json.loads(checked.read_text(encoding='utf-8'))
    if check['mismatches_by_feature'] or check['feature_values_checked'] != 16100:
        raise ValueError('Independent feature check missing or failed')
    manifests[checked.name] = digest(checked)
    calendar = [(str(d), s) for d, s in con.execute('SELECT * FROM scoring_calendar ORDER BY scoring_date').fetchall()]
    if calendar != CALENDAR:
        raise ValueError('Calendar differs from frozen plan')
    for before, after in [('train', 'selection'), ('selection', 'calibration'), ('calibration', 'holdout')]:
        last = con.execute('SELECT max(maturity_date) FROM cohort_labels WHERE split=? AND lead_eligible', [before]).fetchone()[0]
        first = con.execute('SELECT min(scoring_date) FROM scoring_calendar WHERE split=?', [after]).fetchone()[0]
        if last >= first:
            raise ValueError('Labels not mature before next stage')
    for table in ['model_features', 'cohort_labels']:
        if con.execute(f'SELECT count(*)-count(DISTINCT (msno,scoring_date)) FROM {table}').fetchone()[0]:
            raise ValueError('Duplicate keys: '+table)
    n = con.execute('SELECT count(*) FROM model_features').fetchone()[0]
    valid = con.execute('SELECT count(*) FROM model_features JOIN cohort_labels USING(msno,scoring_date) WHERE lead_eligible AND mature AND is_churn IN (0,1)').fetchone()[0]
    if valid != n or n != report['feature_rows']:
        raise ValueError('Feature/label population mismatch')
    return manifests


def load_split(con, split):
    if split not in ['train', 'selection', 'calibration', 'holdout']:
        raise ValueError('Unrecognised split')
    cols = ','.join('f.'+n for n in MODEL_PREDICTORS)
    data = con.execute(f'''SELECT f.msno, f.scoring_date, sha256(f.msno) tie,
        l.is_churn, {cols} FROM model_features f JOIN cohort_labels l USING(msno,scoring_date)
        WHERE l.split=? AND l.lead_eligible AND l.mature ORDER BY f.scoring_date,f.msno''', [split]).fetchnumpy()
    x = np.column_stack([data.pop(n) for n in MODEL_PREDICTORS])
    if not np.isfinite(x).all():
        raise ValueError('Nonfinite predictors')
    return {'x': x, 'y': data['is_churn'].astype(np.int8), 'ids': data['msno'],
            'date': data['scoring_date'], 'tie': data['tie']}


def code_manifest():
    paths = [ROOT/'docs/evaluation_plan.md', ROOT/'src/evaluate_models.py', ROOT/'src/feature_contract.py', ROOT/'src/build_source_sensitivity.py']
    return {str(p.relative_to(ROOT)).replace('\\', '/'): digest(p) for p in paths}


def model_description(model):
    public = {k: v for k, v in model.items() if k not in ['estimator', 'scaler', 'indices']}
    if 'estimator' in model:
        public.update({'coefficients_standardised_log1p': dict(zip(model['names'], model['estimator'].coef_[0].tolist())),
                       'intercept': float(model['estimator'].intercept_[0]),
                       'iterations': int(model['estimator'].n_iter_[0]),
                       'scaler_mean': model['scaler'].mean_.tolist(), 'scaler_scale': model['scaler'].scale_.tolist()})
    return public


def fit(args):
    out = args.output_dir
    out.mkdir(parents=True, exist_ok=True)
    if (out/'model_freeze.json').exists() or (out/'holdout_started.json').exists():
        raise ValueError('Frozen run already exists; refuse to overwrite')
    con = connect(args.database)
    manifests = verify_inputs(con, args.database)
    print('Reading training and selection only', flush=True)
    train, selection = load_split(con, 'train'), load_split(con, 'selection')
    models, selections, grid = {}, {}, []
    for family in FAMILIES+['no_duration']:
        best = None
        for c in ([.01, 1] if family in ['recency', 'transactions', 'combined', 'no_duration'] else [1]):
            print(f'Fitting {family}, C={c}', flush=True)
            model = fit_base(family, train['x'], train['y'], c)
            evaluated = metrics(selection['y'], predict_base(model, selection['x']), selection['tie'])
            grid.append({'family': family, 'C': c, **evaluated})
            if best is None or evaluated['log_loss'] < best[0]['log_loss']:
                best = evaluated, model
            print(f'Selection log loss={evaluated["log_loss"]:.6f}, AP={evaluated["average_precision"]:.6f}', flush=True)
        selections[family], models[family] = best
    selected = choose_family(selections)
    comparator = min(FAMILIES[:3], key=lambda n: selections[n]['log_loss'])
    train_summary = {'rows': len(train['y']), 'churn': int(train['y'].sum()), 'unique_customers': len(set(train['ids']))}
    train_ids = set(train['ids'])
    overlap = {'selection': {'rows': len(selection['y']), 'seen_in_training': sum(i in train_ids for i in selection['ids'])}}
    # Training moments only, retained for later feature drift diagnostics.
    drift_reference = {'mean': train['x'].mean(axis=0), 'std': train['x'].std(axis=0)}
    del train, selection
    print(f'Selected {selected}; fitting December sigmoid calibration', flush=True)
    calibration = load_split(con, 'calibration')
    overlap['calibration'] = {'rows': len(calibration['y']), 'seen_in_training': sum(i in train_ids for i in calibration['ids'])}
    calibrators, calibration_metrics = {}, {}
    for family, model in models.items():
        p = predict_base(model, calibration['x'])
        cal = fit_calibrator(p, calibration['y'])
        calibrators[family] = cal
        calibration_metrics[family] = {'raw': metrics(calibration['y'], p, calibration['tie']),
            'calibrated_fit_diagnostic': metrics(calibration['y'], calibrate(cal, p), calibration['tie'])}
    con.close()
    bundle = {'models': models, 'calibrators': calibrators, 'selected': selected, 'comparator': comparator,
              'drift_reference': drift_reference, 'train_ids': train_ids}
    joblib.dump(bundle, out/'models.joblib', compress=3)
    freeze = {'status': 'frozen before reading holdout labels', 'frozen_utc': datetime.now(timezone.utc).isoformat(),
              'calendar': CALENDAR, 'predictors': MODEL_PREDICTORS, 'selection_policy': 'simplest within 0.5% of minimum October log loss',
              'selected': selected, 'simple_comparator': comparator, 'capacities': CAPACITIES,
              'seed': SEED, 'bootstrap_replicates': BOOTSTRAPS,
              'train': train_summary, 'overlap': overlap, 'selection_grid': grid, 'selection': selections,
              'calibration': calibration_metrics, 'calibrators': calibrators,
              'model_parameters': {n: model_description(m) for n, m in models.items()},
              'feature_manifest_sha256': manifests, 'code_sha256': code_manifest(),
              'model_bundle_sha256': digest(out/'models.joblib'),
              'versions': {p: importlib.metadata.version(p) for p in ['numpy', 'scipy', 'scikit-learn', 'duckdb', 'joblib', 'threadpoolctl', 'matplotlib']},
              'python': platform.python_version()}
    write_json(out/'model_freeze.json', freeze)
    print('Model freeze saved; holdout has not been evaluated', flush=True)


def segment_report(data, p, train_ids, missing_member):
    x, y = data['x'], data['y']
    no_log = x[:, MODEL_PREDICTORS.index('no_listening_logs_90d')] > 0
    capped = x[:, MODEL_PREDICTORS.index('listening_over_24h_days_90d')] > 0
    seen = np.asarray([i in train_ids for i in data['ids']])
    masks = {'no_listening_90d': no_log, 'has_listening_90d': ~no_log,
             'member_absent': missing_member, 'member_present': ~missing_member,
             'seen_in_training': seen, 'unseen_in_training': ~seen,
             'capped_duration': capped, 'no_capped_duration': ~capped}
    order = np.lexsort((data['tie'], -p))
    global_contacts = {f: np.zeros(len(y), dtype=bool) for f in CAPACITIES}
    for f in CAPACITIES:
        global_contacts[f][order[:int(len(y)*f)]] = True
    report = {}
    for name, mask in masks.items():
        if not mask.any():
            continue
        r = metrics(y[mask], p[mask], data['tie'][mask])
        r['global_policy'] = {}
        for f, chosen in global_contacts.items():
            local = chosen & mask
            r['global_policy'][str(f)] = {'contacted': int(local.sum()), 'contact_rate': float(local.sum()/mask.sum()),
                'churn_captured': int(y[local].sum()), 'precision': float(y[local].mean()) if local.any() else None}
        report[name] = r
    return report


def source_sensitivity(con, bundle, sensitivity_db, main_data, main_predictions):
    con.execute("ATTACH '"+str(sensitivity_db).replace("'", "''")+"' AS sensitivity (READ_ONLY)")
    result = []
    family = bundle['selected']
    for split in ['selection', 'calibration', 'holdout']:
        data = main_data if split == 'holdout' else load_split(con, split)
        p = main_predictions if split == 'holdout' else calibrate(bundle['calibrators'][family], predict_base(bundle['models'][family], data['x']))
        alternate = dict(con.execute('SELECT msno,is_churn FROM sensitivity.alternative_labels WHERE split=?', [split]).fetchall())
        common = np.array([i in alternate for i in data['ids']])
        alt_y = np.array([alternate[i] for i in data['ids'][common]], dtype=np.int8)
        result.append({'split': split, 'baseline_eligible': len(data['y']), 'alternative_eligible': len(alternate),
            'common_eligible': int(common.sum()), 'baseline_only': int((~common).sum()),
            'alternative_only': len(alternate)-int(common.sum()),
            'changed_labels_on_common': int((data['y'][common] != alt_y).sum()),
            'baseline_labels': metrics(data['y'][common], p[common], data['tie'][common]),
            'alternative_labels': metrics(alt_y, p[common], data['tie'][common]),
            'calibration_context': 'December-calibrated fixed scores; October is retrospective sensitivity, December is calibration-fit diagnostic, February is final test'})
    return result


def plot_report(report, destination):
    import matplotlib
    matplotlib.use('Agg')
    import matplotlib.pyplot as plt
    plt.rcParams.update({'font.size': 10, 'svg.fonttype': 'none'})
    names = FAMILIES
    fig, axes = plt.subplots(1, 3, figsize=(15, 4.8))
    colours = ['#8c96a0', '#be7c3b', '#6496ad', '#5465a9', '#158177']
    for name, colour in zip(names, colours):
        bins = report['models'][name]['score_deciles']
        axes[0].plot([r['mean_prediction'] for r in bins], [r['churn_rate'] for r in bins], 'o-', label=name.replace('_', ' '), color=colour)
        m = report['models'][name]['calibrated']
        axes[1].plot([5, 10, 20], [m[f'lift_{c}pct'] for c in [5, 10, 20]], 'o-', color=colour)
    axes[0].plot([0, 1], [0, 1], '--', color='#aaaaaa', label='ideal')
    axes[0].set(xlabel='Mean predicted churn risk', ylabel='Observed churn rate', title='Calibration by score decile')
    maximum = max(max(r['mean_prediction'], r['churn_rate']) for n in names for r in report['models'][n]['score_deciles'])
    bound = min(1, max(.1, maximum*1.1))
    axes[0].set_xlim(0, bound); axes[0].set_ylim(0, bound)
    axes[0].legend(fontsize=8)
    axes[1].axhline(1, linestyle='--', color='#aaaaaa')
    axes[1].set(xlabel='Contact capacity (%)', ylabel='Lift over population prevalence', title='Prioritisation at fixed capacities', xticks=[5, 10, 20])
    axes[2].barh([n.replace('_', ' ') for n in names], [report['models'][n]['calibrated']['average_precision'] for n in names], color=colours)
    axes[2].axvline(report['models']['prevalence']['calibrated']['prevalence'], linestyle='--', color='#aaaaaa')
    axes[2].set(xlabel='Average precision (AP)', title='Ranking quality')
    fig.suptitle('February 2017 holdout | Reconstructed historical churn', fontsize=15)
    fig.tight_layout()
    fig.savefig(destination, format='svg', metadata={'Date': None})
    plt.close(fig)


def evaluate(args):
    out = args.output_dir
    freeze = json.loads((out/'model_freeze.json').read_text(encoding='utf-8'))
    if digest(out/'models.joblib') != freeze['model_bundle_sha256'] or code_manifest() != freeze['code_sha256']:
        raise ValueError('Frozen code or model artifact changed')
    if not args.sensitivity_database or not args.log_database:
        raise ValueError('Sensitivity and member-diagnostic database paths required')
    con = connect(args.database)
    if verify_inputs(con, args.database) != freeze['feature_manifest_sha256']:
        raise ValueError('Feature manifests changed after freeze')
    marker = out/'holdout_started.json'
    with marker.open('x', encoding='utf-8') as stream:
        json.dump({'started_utc': datetime.now(timezone.utc).isoformat(), 'freeze_sha256': digest(out/'model_freeze.json')}, stream)
    bundle = joblib.load(out/'models.joblib')
    print('Reading frozen final holdout once', flush=True)
    data = load_split(con, 'holdout')
    if len(set(data['ids'])) != len(data['ids']):
        raise ValueError('Holdout must have one row per customer for bootstrap')
    predictions, model_results = {}, {}
    for family, model in bundle['models'].items():
        print('Final evaluation: '+family, flush=True)
        raw = predict_base(model, data['x'])
        p = calibrate(bundle['calibrators'][family], raw)
        predictions[family] = p
        model_results[family] = {'raw': metrics(data['y'], raw, data['tie']),
            'calibrated': metrics(data['y'], p, data['tie']), 'calibration_bins': calibration_bins(data['y'], p),
            'score_deciles': score_deciles(data['y'], p)}
    # Private checkpoint permits inspection if a downstream reporting step fails.
    joblib.dump({'ids': data['ids'], 'y': data['y'], 'tie': data['tie'], 'predictions': predictions}, out/'holdout_predictions.joblib', compress=3)
    write_json(out/'holdout_metrics_checkpoint.json', model_results)
    selected = bundle['selected']
    intervals = bootstrap_comparison(data['y'], predictions, data['tie'], selected, bundle['comparator'])
    con.execute("ATTACH '"+str(args.log_database).replace("'", "''")+"' AS member_source (READ_ONLY)")
    member_ids = set(r[0] for r in con.execute('SELECT msno FROM member_source.members').fetchall())
    missing_member = np.array([i not in member_ids for i in data['ids']])
    del member_ids
    segments = segment_report(data, predictions[selected], bundle['train_ids'], missing_member)
    drift = []
    for j, name in enumerate(MODEL_PREDICTORS):
        mean, std = bundle['drift_reference']['mean'][j], bundle['drift_reference']['std'][j]
        later_mean = float(data['x'][:, j].mean())
        drift.append({'feature': name, 'train_mean': float(mean), 'holdout_mean': later_mean,
                      'standardised_mean_shift': float((later_mean-mean)/std) if std else None,
                      'constant_in_training': bool(std == 0)})
    print('Assessing fixed-score source-label sensitivity', flush=True)
    sensitivity = source_sensitivity(con, bundle, args.sensitivity_database, data, predictions[selected])
    con.close()
    report = {'status': 'milestone 3 frozen holdout evaluation complete', 'selected': selected,
        'simple_comparator': bundle['comparator'], 'models': model_results, 'uncertainty': intervals,
        'segments_selected_model': segments, 'feature_drift': drift, 'source_sensitivity': sensitivity,
        'holdout_customers_seen_in_training': int(sum(i in bundle['train_ids'] for i in data['ids'])),
        'freeze_sha256': digest(out/'model_freeze.json'), 'holdout_marker_sha256': digest(marker),
        'sensitivity_build_report_sha256': digest(args.sensitivity_database.parent/'source_sensitivity_build.json'),
        'limits': ['Retrospective event dates; ingestion availability unknown.',
                  'Reconstructed labels; 22 supplied-label differences unresolved.',
                  'Source sensitivity holds baseline features and fitted scores fixed, not full alternative-source retraining.',
                  'No-duration ablation tests reliance on duration magnitudes; it does not identify the correct cap.',
                  'Intervals condition on fitted models and one month; no training or temporal uncertainty.',
                  'Risk is not persuadability; contact budgets are scenarios, not measured retention or savings.']}
    write_json(out/'model_evaluation.json', report)
    plot_report(report, out/'model_evaluation.svg')
    print(json.dumps({'status': report['status'], 'selected': selected, 'metrics': model_results[selected]['calibrated']}, indent=2), flush=True)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('stage', choices=['fit', 'evaluate'])
    parser.add_argument('--database', type=Path, required=True)
    parser.add_argument('--output-dir', type=Path, required=True)
    parser.add_argument('--sensitivity-database', type=Path)
    parser.add_argument('--log-database', type=Path)
    args = parser.parse_args()
    with threadpool_limits(limits=4):
        (fit if args.stage == 'fit' else evaluate)(args)


if __name__ == '__main__':
    main()
