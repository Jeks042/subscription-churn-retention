"""Retrospective commercial scenarios; hypothetical money and treatment effects."""
import argparse
import hashlib
import itertools
import json
import math
from pathlib import Path

import duckdb
import joblib
import numpy as np

try:
    from .experiment_power import required_per_arm, proportion_power, commercial_margin_per_arm, binomial_simulation
except ImportError:
    from experiment_power import required_per_arm, proportion_power, commercial_margin_per_arm, binomial_simulation

ROOT = Path(__file__).resolve().parents[1]


def sha(path):
    with Path(path).open('rb') as f:
        return hashlib.file_digest(f, 'sha256').hexdigest()


def write_json(path, data):
    # Explicit LF gives portable byte-level provenance across Windows and GitHub.
    with Path(path).open('w', encoding='utf-8', newline='\n') as stream:
        json.dump(data, stream, indent=2, allow_nan=False)
        stream.write('\n')


def value_index(amounts, training_median, low=.5, high=2., unknown=1.):
    if training_median <= 0 or not 0 < low <= unknown <= high or not np.isfinite(amounts).all():
        raise ValueError('Invalid value-proxy inputs')
    return np.where(amounts > 0, np.clip(amounts/training_median, low, high), unknown)


def select_list(scores, indices, tie, capacity, policy):
    if not 0 < capacity <= 1 or policy not in ['risk_only', 'risk_x_value_proxy']:
        raise ValueError('Invalid targeting policy')
    priority = scores if policy == 'risk_only' else scores*indices
    return np.lexsort((tie, -priority))[:int(len(scores)*capacity)]


def economics(n, churn_units, value_sum, churn_value_sum, effect_type, effect,
              contact_cost, incentive_cost, redemption_churn, redemption_renew, fixed_cost=0.):
    if n <= 0 or not 0 <= churn_units <= n or value_sum <= 0 or not 0 <= churn_value_sum <= value_sum+1e-8:
        raise ValueError('Invalid scenario totals')
    if min(contact_cost, incentive_cost, fixed_cost) < 0 or not all(0 <= r <= 1 for r in [redemption_churn, redemption_renew]):
        raise ValueError('Invalid cost or redemption assumptions')
    q = churn_units/n
    if effect_type == 'conditional':
        if not 0 <= effect <= 1:
            raise ValueError('Conditional saves must be between zero and one')
        saved, benefit = effect*churn_units, effect*churn_value_sum
    elif effect_type == 'absolute':
        if not -(1-q) <= effect <= q:
            raise ValueError('Absolute effect violates group probability bounds')
        saved, benefit = effect*n, effect*value_sum
    else:
        raise ValueError('Unknown effect type')
    churner_offers = churn_units*redemption_churn*incentive_cost
    renewer_offers = (n-churn_units)*redemption_renew*incentive_cost
    contact = n*contact_cost
    cost = contact+churner_offers+renewer_offers+fixed_cost
    s_be = cost/churn_value_sum if churn_value_sum else None
    delta_be = cost/value_sum
    return {'assumed_additional_retained': saved, 'assumed_absolute_effect': saved/n,
            'scenario_benefit_cu': benefit, 'contact_cost_cu': contact,
            'incentive_cost_would_churn_cu': churner_offers,
            'incentive_cost_would_renew_cu': renewer_offers,
            'fixed_cost_cu': fixed_cost, 'total_cost_cu': cost,
            'net_contribution_cu': benefit-cost, 'net_per_contact_cu': (benefit-cost)/n,
            'break_even_conditional_save': s_be,
            'conditional_break_even_feasible': s_be is not None and s_be <= 1,
            'break_even_absolute_effect': delta_be,
            'absolute_break_even_group_feasible': delta_be <= q}


def economic_case(profile, scenario, config):
    v = config['monthly_fee_cu']*config['horizon_days']/config['days_per_scenario_month']*scenario['margin']
    return economics(profile['contacts'], profile['churn_units'], v*profile['value_index_sum'],
        v*profile['churn_value_index_sum'], scenario['effect_type'], scenario['effect'],
        scenario['contact_cost'], scenario['incentive_cost'], scenario['redemption'], scenario['redemption'],
        config['fixed_cost_cu'])


def reference_scenario(config):
    return {'effect_type': 'conditional', 'effect': .1, 'margin': config['reference_margin'],
            'contact_cost': config['reference_contact_cost_cu'],
            'incentive_cost': config['reference_incentive_cost_cu'],
            'redemption': config['reference_redemption_churn']}


def experiment_report(profiles, config):
    assumptions = config['experiment']
    controls = {'conservative_50pct': .5}
    for source in ['common_baseline', 'common_full_union']:
        p = next(p for p in profiles if p['source_case']==source and p['policy']=='risk_only' and p['value_case']=='uniform' and p['capacity']==.1)
        controls[source] = 1-p['churn_units']/p['contacts']
    power_rows = []
    for source, control in controls.items():
        for delta, power in itertools.product(assumptions['absolute_effects'], assumptions['powers']):
            n = required_per_arm(control, delta, power, assumptions['alpha'])
            enrolled = math.ceil(n/(1-assumptions['missing_outcome_allowance']))
            power_rows.append({'control_rate_source': source, 'control_retention_proxy': control,
                'absolute_retention_effect': delta, 'target_power': power, 'per_arm_complete_equivalent': n,
                'achieved_approximate_power': proportion_power(control, delta, n, assumptions['alpha']),
                'per_arm_enrolment_allowance': enrolled, 'total_enrolment': enrolled*2})
    value = config['monthly_fee_cu']*config['horizon_days']/config['days_per_scenario_month']*config['reference_margin']
    cost = config['reference_contact_cost_cu']+config['reference_incentive_cost_cu']*config['reference_redemption_churn']
    margin = cost/value
    commercial = []
    for power in assumptions['powers']:
        n = commercial_margin_per_arm(margin, assumptions['commercial_alternative_absolute_effect'], power, assumptions['alpha'])
        enrolled = math.ceil(n/(1-assumptions['missing_outcome_allowance']))
        commercial.append({'target_power': power, 'null_commercial_margin': margin,
            'assumed_true_absolute_effect': assumptions['commercial_alternative_absolute_effect'],
            'per_arm_complete_equivalent': n, 'per_arm_enrolment_allowance': enrolled,
            'total_enrolment': enrolled*2, 'reference_expected_treatment_cost_cu': enrolled*cost})
    simulations = []
    for source in ['common_baseline', 'common_full_union', 'conservative_50pct']:
        row = next(r for r in power_rows if r['control_rate_source']==source and r['absolute_retention_effect']==.02 and r['target_power']==.9)
        for delta in [.0, .02]:
            simulated = binomial_simulation(row['control_retention_proxy'], delta, row['per_arm_complete_equivalent'],
                assumptions['alpha'], assumptions['simulation_replicates'], assumptions['seed'])
            expected = assumptions['alpha'] if delta==0 else row['achieved_approximate_power']
            if abs(simulated['rejection_rate']-expected) > max(.005, 5*simulated['monte_carlo_se']):
                raise ValueError('Binomial simulation does not support power approximation')
            simulations.append({'source': source, 'effect': delta, 'expected_rejection_rate': expected, **simulated})
    return {'status': 'planning only; no experiment executed', 'assumptions': assumptions,
        'binary_endpoint_power': power_rows, 'commercial_margin_power': commercial, 'simulation_checks': simulations,
        'method': 'Equal independent arms; pooled null and nonpooled alternative normal SE; numerical power inversion. Commercial margin uses worst-case Bernoulli variance and 95% lower-bound criterion.',
        'limits': 'Historical label rates are planning proxies for a prospectively fixed paid-renewal endpoint. Re-estimate operational rates and real economics before launch; missing-outcome allowance does not authorise dropping ITT subjects.'}


def draw(report, path):
    import matplotlib
    matplotlib.use('Agg')
    import matplotlib.pyplot as plt
    plt.rcParams.update({'svg.fonttype': 'none', 'font.size': 10})
    fig, axes = plt.subplots(1, 2, figsize=(12, 4.8))
    config = report['config']
    reference_value = config['monthly_fee_cu']*config['horizon_days']/config['days_per_scenario_month']*config['reference_margin']
    reference_cost = config['reference_contact_cost_cu']+config['reference_incentive_cost_cu']*config['reference_redemption_churn']
    colors = {'common_baseline': '#137c83', 'common_full_union': '#b26036'}
    for source, label in [('common_baseline', 'Baseline labels'), ('common_full_union', 'Full-union labels')]:
        profiles = [p for p in report['policy_profiles'] if p['source_case']==source and p['policy']=='risk_only' and p['value_case']=='uniform']
        profiles.sort(key=lambda p:p['capacity'])
        axes[0].plot([p['capacity']*100 for p in profiles], [p['reference_economics']['break_even_conditional_save']*100 for p in profiles], 'o-', label=label, color=colors[source])
        p = next(p for p in profiles if p['capacity']==.1)
        q = p['churn_units']/p['contacts']
        s = np.linspace(0, .35, 100)
        axes[1].plot(s*100, (q*s*reference_value-reference_cost)*1000, label=label, color=colors[source])
    axes[0].set(xlabel='Contact capacity (%)', ylabel='Conditional save fraction required (%)', title='Break-even response among would-be churners', xticks=[5,10,20])
    axes[1].axhline(0, color='#888888', linestyle='--')
    axes[1].set(xlabel='Assumed conditional save fraction (%)', ylabel='Scenario net CU per 1,000 contacts', title='10% capacity: response and source sensitivity')
    for ax in axes:
        ax.legend(); ax.grid(alpha=.15)
    fig.suptitle(f'Hypothetical economics | {reference_value:g} CU retained contribution; {reference_cost:.2f} CU/contact', fontsize=14)
    fig.tight_layout()
    fig.savefig(path, format='svg', metadata={'Date': None})
    fig.savefig(path.with_suffix('.png'), dpi=140)
    plt.close(fig)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--database', type=Path, required=True)
    parser.add_argument('--model-dir', type=Path, required=True)
    parser.add_argument('--sensitivity-database', type=Path, required=True)
    parser.add_argument('--output-dir', type=Path, required=True)
    parser.add_argument('--config', type=Path, default=ROOT/'docs/commercial_assumptions.json')
    args = parser.parse_args()
    config = json.loads(args.config.read_text(encoding='utf-8'))
    if config['reference_redemption_churn'] != config['reference_redemption_renew']:
        raise ValueError('The common-cost reference experiment requires equal redemption assumptions; revise its plan before using group-specific rates')
    args.output_dir.mkdir(parents=True, exist_ok=True)
    frozen = json.loads((args.model_dir/'model_freeze.json').read_text(encoding='utf-8'))
    evaluated = json.loads((args.model_dir/'model_evaluation.json').read_text(encoding='utf-8'))
    if sha(args.model_dir/'model_freeze.json') != evaluated['freeze_sha256'] or sha(args.model_dir/'models.joblib') != frozen['model_bundle_sha256']:
        raise ValueError('Model artifacts no longer match the milestone 3 freeze')
    print('Reading saved frozen scores; no fitting or recalibration', flush=True)
    saved = joblib.load(args.model_dir/'holdout_predictions.joblib')
    scores, ids, y, tie = saved['predictions'][frozen['selected']], saved['ids'], saved['y'], saved['tie']
    con = duckdb.connect(str(args.database), read_only=True)
    con.execute('SET threads=4')
    con.execute("SET memory_limit='2GB'")
    median = float(con.execute("SELECT median(subscription_recorded_amount_90d) FROM model_features JOIN scoring_calendar USING(scoring_date) WHERE split='train' AND subscription_recorded_amount_90d>0").fetchone()[0])
    payments = con.execute("SELECT msno,subscription_recorded_amount_90d amount FROM model_features WHERE scoring_date='2017-02-01' ORDER BY msno").fetchnumpy()
    con.close()
    if not np.array_equal(payments['msno'], ids) or len(set(ids)) != len(ids):
        raise ValueError('Payment/score keys or order do not reconcile')
    amounts = payments['amount']
    ix = value_index(amounts, median, config['value_index_floor'], config['value_index_ceiling'], config['unknown_value_index'])
    con = duckdb.connect(str(args.sensitivity_database), read_only=True)
    alt = dict(con.execute("SELECT msno,is_churn FROM alternative_labels WHERE split='holdout'").fetchall()); con.close()
    common = np.array([i in alt for i in ids])
    alt_y = np.array([alt[i] for i in ids[common]], dtype=float)
    populations = {'full_baseline': (np.arange(len(ids)), y), 'common_baseline': (np.flatnonzero(common), y[common]),
                   'common_full_union': (np.flatnonzero(common), alt_y),
                   'full_model_probability': (np.arange(len(ids)), scores),
                   'common_model_probability': (np.flatnonzero(common), scores[common])}
    profiles = []
    for source, (positions, q) in populations.items():
        for capacity in config['capacities']:
            chosen = {p: select_list(scores[positions], ix[positions], tie[positions], capacity, p) for p in ['risk_only', 'risk_x_value_proxy']}
            overlap = len(np.intersect1d(chosen['risk_only'], chosen['risk_x_value_proxy']))
            for policy, selected in chosen.items():
                global_ix = positions[selected]
                for value_case in ['uniform', 'payment_proxy']:
                    weights = np.ones(len(selected)) if value_case=='uniform' else ix[global_ix]
                    profile = {'source_case': source, 'risk_basis': 'frozen_probability' if 'probability' in source else 'retrospective_label',
                        'eligible_population': len(positions), 'capacity': capacity, 'policy': policy, 'value_case': value_case,
                        'contacts': len(selected), 'churn_units': float(q[selected].sum()),
                        'predicted_churn_units': float(scores[global_ix].sum()),
                        'value_index_sum': float(weights.sum()), 'churn_value_index_sum': float(q[selected] @ weights),
                        'unknown_value_contacts': int((amounts[global_ix]<=0).sum()),
                        'floor_index_contacts': int(((amounts[global_ix]>0)&(amounts[global_ix]/median<config['value_index_floor'])).sum()),
                        'ceiling_index_contacts': int((amounts[global_ix]/median>config['value_index_ceiling']).sum()),
                        'overlap_with_other_policy': overlap, 'displaced_vs_other_policy': len(selected)-overlap}
                    profile['reference_economics'] = economic_case(profile, reference_scenario(config), config)
                    profiles.append(profile)
    for source in ['full_baseline', 'common_baseline', 'common_full_union']:
        existing = evaluated['models'][frozen['selected']]['calibrated'] if source=='full_baseline' else next(s for s in evaluated['source_sensitivity'] if s['split']=='holdout')['baseline_labels' if source=='common_baseline' else 'alternative_labels']
        for c in config['capacities']:
            p = next(p for p in profiles if p['source_case']==source and p['policy']=='risk_only' and p['value_case']=='uniform' and p['capacity']==c)
            if p['contacts'] != existing[f'contacts_{int(c*100)}pct'] or p['churn_units'] != existing[f'tp_{int(c*100)}pct']:
                raise ValueError('Frozen risk-only policy does not reproduce milestone 3')
    cases = []
    for p in profiles:
        for s in config['scenarios']:
            cases.append({'source_case': p['source_case'], 'capacity': p['capacity'], 'policy': p['policy'],
                'value_case': p['value_case'], 'scenario': s['name'], **economic_case(p, s, config)})
    grid = []
    grid_names = ['margin', 'contact_cost', 'incentive_cost', 'redemption', 'conditional_save']
    for source in ['common_baseline', 'common_full_union']:
        p = next(p for p in profiles if p['source_case']==source and p['policy']=='risk_only' and p['value_case']=='uniform' and p['capacity']==.1)
        for values in itertools.product(*(config['grid'][n] for n in grid_names)):
            s = dict(zip(grid_names, values)); s.update(effect_type='conditional', effect=s['conditional_save'])
            e = economic_case(p, s, config)
            grid.append([source, *values, e['net_contribution_cu'], e['break_even_conditional_save'], e['break_even_absolute_effect']])
    report = {'status': 'milestone 4 scenarios complete; hypothetical economics, no campaign executed',
        'config': config, 'value_proxy': {'positive_training_median_recorded_amount': median,
            'holdout_unknown_value_rows': int((amounts<=0).sum()), 'holdout_floor_rows': int(((amounts>0)&(amounts/median<config['value_index_floor'])).sum()),
            'holdout_ceiling_rows': int((amounts/median>config['value_index_ceiling']).sum()),
            'claim': 'Dimensionless past-payment index, not measured contribution or LTV'},
        'policy_profiles': profiles, 'scenarios': cases,
        'assertions': 'passed: unique keys, score/payment reconciliation, existing risk-only lists/counts reproduced',
        'input_sha256': {'model_freeze': sha(args.model_dir/'model_freeze.json'), 'model_evaluation': sha(args.model_dir/'model_evaluation.json'),
            'private_predictions': sha(args.model_dir/'holdout_predictions.joblib'), 'config': sha(args.config),
            'holdout_payment_values_float64': hashlib.sha256(np.asarray(amounts, dtype='<f8').tobytes()).hexdigest()},
        'code_sha256': {n: sha(ROOT/n) for n in ['src/build_commercial.py','src/experiment_power.py','docs/commercial_plan.md']},
        'limits': ['Generic CU; no real prices, margins, campaign costs or response estimates.',
            'Post-holdout policy illustration, not independent validation or a selected replacement policy.',
            'Value proxy is not future contribution; uniform value is a competing scenario.',
            'Source cases are separate and not chosen using scenario profitability.',
            'No incremental retention, savings, ROI or production readiness is established.']}
    write_json(args.output_dir/'commercial_evaluation.json', report)
    write_json(args.output_dir/'commercial_sensitivity_grid.json', {'scope': 'common population, risk-only, 10% capacity, uniform value',
        'columns': ['source_case', *grid_names, 'net_contribution_cu', 'break_even_conditional_save', 'break_even_absolute_effect'], 'rows': grid})
    print('Sizing hypothetical experiment and simulating binomial checks', flush=True)
    power = experiment_report(profiles, config)
    write_json(args.output_dir/'experiment_power.json', power)
    draw(report, args.output_dir/'commercial_scenarios.svg')
    print(json.dumps({'profiles': len(profiles), 'scenarios': len(cases), 'sensitivity_rows': len(grid),
        'power_cases': len(power['binary_endpoint_power']), 'simulation_checks': len(power['simulation_checks']),
        'assertions': 'passed'}, indent=2), flush=True)


if __name__=='__main__':
    main()
