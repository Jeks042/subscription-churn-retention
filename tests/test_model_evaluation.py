import unittest

import numpy as np
from sklearn.metrics import average_precision_score, brier_score_loss, log_loss, roc_auc_score

from src.evaluate_models import (FAMILIES, MODEL_PREDICTORS, RankedMetrics, calibrate,
    calibration_bins, choose_family, feature_names, fit_base, fit_calibrator,
    metrics, predict_base, transformed)


class ModelEvaluationTests(unittest.TestCase):
    def test_weighted_tied_scores_match_independent_library(self):
        y = np.array([0, 1, 1, 0, 0, 1, 0, 1])
        p = np.array([.1, .7, .7, .3, .7, .9, .2, .7])
        w = np.array([2, 3, 0, 1, 4, 2, 1, 3])
        r = RankedMetrics(y, p, np.arange(len(y))).evaluate(w)
        self.assertAlmostEqual(r['average_precision'], average_precision_score(y, p, sample_weight=w))
        self.assertAlmostEqual(r['roc_auc'], roc_auc_score(y, p, sample_weight=w))
        self.assertAlmostEqual(r['log_loss'], log_loss(y, p, sample_weight=w))
        self.assertAlmostEqual(r['brier'], brier_score_loss(y, p, sample_weight=w))
        expanded = np.repeat(np.arange(len(y)), w)
        order = expanded[np.lexsort((expanded, -p[expanded]))]
        for pct in [5, 10, 20]:
            k = int(len(expanded)*pct/100)
            if k:
                self.assertEqual(r[f'tp_{pct}pct'], y[order[:k]].sum())

    def test_constant_model_has_chance_discrimination_and_deterministic_ties(self):
        y = np.tile([0, 1, 0, 0, 0], 20)
        p = np.full(len(y), .2)
        tie = np.arange(len(y))[::-1]
        r = metrics(y, p, tie)
        self.assertAlmostEqual(r['roc_auc'], .5)
        self.assertAlmostEqual(r['average_precision'], .2)
        self.assertEqual(r['contacts_10pct'], 10)
        self.assertEqual(r['tp_10pct'], y[-10:].sum())

    def test_capacity_floor_and_accounting(self):
        y = np.array([1, 0]*51+[0])
        p = np.linspace(.01, .99, len(y))
        r = metrics(y, p, np.arange(len(y)))
        self.assertEqual(r['contacts_5pct'], 5)
        for pct in [5, 10, 20]:
            self.assertEqual(r[f'tp_{pct}pct']+r[f'fp_{pct}pct'], r[f'contacts_{pct}pct'])
            self.assertEqual(r[f'tp_{pct}pct']+r[f'fn_{pct}pct'], y.sum())

    def test_simplest_within_margin_and_ablation_cannot_win(self):
        s = {n: {'log_loss': .3} for n in FAMILIES}
        s['transactions']['log_loss'] = .2008
        s['combined']['log_loss'] = .2
        s['no_duration'] = {'log_loss': .1}
        self.assertEqual(choose_family(s), 'transactions')
        s['transactions']['log_loss'] = .202
        self.assertEqual(choose_family(s), 'combined')

    def test_scaler_uses_training_and_prediction_does_not_mutate(self):
        rng = np.random.default_rng(21)
        x = rng.uniform(0, 100, (300, len(MODEL_PREDICTORS)))
        y = (x[:, 1] > 50).astype(int)
        model = fit_base('recency', x, y, .01)
        np.testing.assert_allclose(model['scaler'].mean_, transformed(x[:, [1]]).mean(axis=0))
        before = model['scaler'].mean_.copy()
        future = np.full((20, len(MODEL_PREDICTORS)), 100000.)
        self.assertTrue(np.isfinite(predict_base(model, future)).all())
        np.testing.assert_array_equal(before, model['scaler'].mean_)
        self.assertFalse(any('bounded_seconds' in n for n in feature_names('no_duration')))
        self.assertEqual(len(feature_names('no_duration')), 32)

    def test_sigmoid_is_monotone_and_bins_reconcile(self):
        rng = np.random.default_rng(32)
        p = np.linspace(.01, .99, 2000)
        y = rng.binomial(1, p)
        cal = fit_calibrator(p, y)
        q = calibrate(cal, p)
        self.assertTrue((np.diff(q) > 0).all())
        self.assertEqual(sum(r['rows'] for r in calibration_bins(y, q)), len(y))
        self.assertEqual(fit_calibrator(np.full(2000, .2), y), {'constant': y.mean()})


if __name__ == '__main__':
    unittest.main()
