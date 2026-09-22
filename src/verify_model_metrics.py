"""Independently check published aggregates against private frozen predictions."""
import argparse
import json
from pathlib import Path

import joblib
import numpy as np
from sklearn.metrics import average_precision_score, brier_score_loss, log_loss, roc_auc_score


def main():
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument('--run-dir', type=Path, required=True)
    p.add_argument('--output', type=Path, required=True)
    args = p.parse_args()
    private = joblib.load(args.run_dir/'holdout_predictions.joblib')
    report = json.loads((args.run_dir/'model_evaluation.json').read_text(encoding='utf-8'))
    y = private['y']
    differences, checked = {}, 0
    for name, scores in private['predictions'].items():
        if not np.isfinite(scores).all() or (scores < 0).any() or (scores > 1).any():
            raise ValueError('Invalid probabilities')
        expected = {'log_loss': log_loss(y, scores), 'brier': brier_score_loss(y, scores),
                    'average_precision': average_precision_score(y, scores), 'roc_auc': roc_auc_score(y, scores)}
        ordering = np.lexsort((private['tie'], -scores))
        for percent in [5, 10, 20]:
            k = len(y)*percent//100
            top = y[ordering[:k]]
            expected.update({f'tp_{percent}pct': int(top.sum()), f'precision_{percent}pct': float(top.mean()),
                f'recall_{percent}pct': float(top.sum()/y.sum()), f'lift_{percent}pct': float(top.mean()/y.mean())})
        for key, value in expected.items():
            checked += 1
            actual = report['models'][name]['calibrated'][key]
            if not np.isclose(actual, value, atol=1e-10, rtol=1e-10):
                differences[name+'/'+key] = {'reported': actual, 'independent': float(value)}
    result = {'rows': len(y), 'models': len(private['predictions']), 'aggregate_values_checked': checked,
              'differences': differences, 'method': 'scikit-learn metrics and independent exact top-k array counts against saved frozen holdout predictions'}
    args.output.write_text(json.dumps(result, indent=2)+'\n', encoding='utf-8')
    print(json.dumps(result, indent=2))
    if differences:
        raise ValueError('Model metric discrepancy')


if __name__ == '__main__':
    main()
