import unittest

import numpy as np

from src.build_commercial import economics, select_list, value_index
from src.experiment_power import commercial_margin_per_arm, proportion_power, required_per_arm, binomial_simulation


class CommercialTests(unittest.TestCase):
    def case(self, effect_type='conditional', effect=.1, churn=20, weighted=1200):
        return economics(100, churn, 6000, weighted, effect_type, effect, .5, 10, .3, .3)

    def test_conditional_absolute_equivalence_under_uniform_value(self):
        conditional = self.case()
        absolute = self.case('absolute', .02)
        self.assertAlmostEqual(conditional['scenario_benefit_cu'], 120)
        self.assertAlmostEqual(absolute['scenario_benefit_cu'], 120)  # Never multiply an absolute effect by q again.
        self.assertAlmostEqual(conditional['net_contribution_cu'], -230)
        self.assertAlmostEqual(conditional['break_even_absolute_effect'], 350/6000)

    def test_zero_effect_and_costs_for_would_be_renewers(self):
        zero = self.case(effect=0)
        self.assertEqual(zero['net_contribution_cu'], -350)
        self.assertEqual(zero['incentive_cost_would_renew_cu'], 240)
        self.assertEqual(zero['incentive_cost_would_churn_cu'], 60)
        adverse = self.case('absolute', -.01)
        self.assertEqual(adverse['net_contribution_cu'], -410)

    def test_break_even_identity_and_impossible_or_invalid_cases(self):
        e = self.case()
        at_break_even = self.case(effect=e['break_even_conditional_save'])
        self.assertAlmostEqual(at_break_even['net_contribution_cu'], 0)
        no_churn = self.case(churn=0, weighted=0)
        self.assertIsNone(no_churn['break_even_conditional_save'])
        self.assertFalse(no_churn['absolute_break_even_group_feasible'])
        with self.assertRaises(ValueError):
            self.case('absolute', .21)
        with self.assertRaises(ValueError):
            self.case(effect=1.01)

    def test_heterogeneous_value_changes_conditional_benefit_and_redemption_split(self):
        e = economics(2, 1, 180, 120, 'conditional', .2, 1, 10, .2, .6, fixed_cost=5)
        self.assertEqual(e['scenario_benefit_cu'], 24)
        self.assertEqual(e['total_cost_cu'], 15)
        self.assertEqual(e['net_contribution_cu'], 9)
        a = economics(2, 1, 180, 120, 'absolute', .1, 1, 10, .2, .6, fixed_cost=5)
        self.assertEqual(a['scenario_benefit_cu'], 18)  # Same average retention gain need not save the same value.

    def test_value_proxy_zero_fallback_caps_and_policy_outcome_independence(self):
        amounts = np.array([0., -1., 20., 100., 900.])
        index = value_index(amounts, 100)
        np.testing.assert_array_equal(index, [1, 1, .5, 1, 2])
        score = np.array([.9, .8, .5, .4, .3])
        tie = np.array(['e', 'd', 'c', 'b', 'a'])
        np.testing.assert_array_equal(select_list(score, index, tie, .6, 'risk_only'), [0,1,2])
        np.testing.assert_array_equal(select_list(score, index, tie, .6, 'risk_x_value_proxy'), [0,1,4])
        np.testing.assert_array_equal(select_list(score, np.ones(5), tie, .6, 'risk_x_value_proxy'), select_list(score,index,tie,.6,'risk_only'))
        tied = select_list(np.ones(5), index, tie, .4, 'risk_only')
        np.testing.assert_array_equal(tied, [4,3])

    def test_power_inversion_and_more_demanding_thresholds(self):
        n = required_per_arm(.6, .02, .8)
        self.assertGreaterEqual(proportion_power(.6, .02, n), .8)
        self.assertLess(proportion_power(.6, .02, n-1), .8)
        self.assertGreater(required_per_arm(.6, .02, .9), n)
        self.assertGreater(required_per_arm(.6, .01, .8), n)
        self.assertAlmostEqual(proportion_power(.6, 0, n), .05)
        self.assertGreater(commercial_margin_per_arm(.0583333, .08), commercial_margin_per_arm(0, .08))
        with self.assertRaises(ValueError):
            commercial_margin_per_arm(.09, .08)

    def test_binomial_simulation_matches_planned_rejection_rate(self):
        n = required_per_arm(.65, .02, .8)
        simulation = binomial_simulation(.65, .02, n, replicates=10000, seed=31)
        self.assertLess(abs(simulation['rejection_rate']-.8), .02)


if __name__=='__main__':
    unittest.main()
