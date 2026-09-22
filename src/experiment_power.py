"""Planning approximations and independent binomial simulation; no real trial."""
import math

import numpy as np
from scipy.optimize import brentq
from scipy.stats import norm


def proportion_power(control_rate, absolute_effect, per_arm, alpha=.05):
    treatment_rate = control_rate+absolute_effect
    if not 0 < control_rate < 1 or not 0 < treatment_rate < 1 or per_arm <= 0 or not 0 < alpha < 1:
        raise ValueError('Invalid binomial planning parameters')
    pooled = (control_rate+treatment_rate)/2
    null_se = math.sqrt(2*pooled*(1-pooled)/per_arm)
    alternative_se = math.sqrt((control_rate*(1-control_rate)+treatment_rate*(1-treatment_rate))/per_arm)
    critical = norm.ppf(1-alpha/2)*null_se
    return float(norm.sf((critical-absolute_effect)/alternative_se)+norm.cdf((-critical-absolute_effect)/alternative_se))


def required_per_arm(control_rate, absolute_effect, power=.8, alpha=.05):
    if absolute_effect <= 0 or not alpha < power < 1:
        raise ValueError('Need positive effect and target power above alpha')
    solution = brentq(lambda n: proportion_power(control_rate, absolute_effect, n, alpha)-power, 2, 1e9)
    return int(math.ceil(solution))


def commercial_margin_per_arm(null_margin, true_effect, power=.9, alpha=.05):
    """Conservative equal-arm bound: each Bernoulli variance is at most .25.

    Probability that the lower two-sided normal CI clears null_margin under
    true_effect. This plans an economic margin, not merely an effect above zero.
    """
    if not 0 <= null_margin < true_effect < 1:
        raise ValueError('Alternative must exceed the commercial threshold')
    return math.ceil(.5*(norm.ppf(1-alpha/2)+norm.ppf(power))**2/(true_effect-null_margin)**2)


def binomial_simulation(control_rate, effect, per_arm, alpha=.05, replicates=50000, seed=20260922):
    """Check planned power with independent simulated counts and pooled z-tests."""
    rng = np.random.default_rng(seed)
    control = rng.binomial(per_arm, control_rate, size=replicates)
    treatment = rng.binomial(per_arm, control_rate+effect, size=replicates)
    pooled = (control+treatment)/(2*per_arm)
    se = np.sqrt(pooled*(1-pooled)*2/per_arm)
    difference = (treatment-control)/per_arm
    z = np.divide(difference, se, out=np.zeros_like(difference), where=se>0)
    measured = float(np.mean(np.abs(z)>norm.ppf(1-alpha/2)))
    return {'replicates': replicates, 'seed': seed, 'rejection_rate': measured,
            'monte_carlo_se': math.sqrt(measured*(1-measured)/replicates)}
