# Proposed retention experiment

**Design only: no customers have been assigned, contacted or offered incentives.** The present decision is further validation before any launch. Historical risk scores do not identify who an intervention can persuade to stay.

## Decision and readiness

Test whether one renewal reminder plus a defined optional retention offer increases paid renewal enough to cover its full incremental cost without unacceptable customer harm. Use the risk-only policy as the initial candidate; the value-proxy comparison does not establish future margin or a superior operational policy.

Before launch, the product/data owner must reconcile an operational event source and customer identity, verify actual scoring-time availability and contact eligibility, and run a shadow scoring period. Finance must replace generic CU inputs with actual recognised contribution, offer cost/redemption, contact and fixed setup costs. The intervention owner must specify the channel, wording, offer eligibility, duration and exact treatment dose. Freeze the endpoint, list rule, sample size, guardrails and analysis before assignment. These are conditions of the proposed future experiment, not evidence already available in this portfolio project.

## Population and allocation

Use a prospectively defined top-10%-risk eligible pool from an upcoming scoring cohort, with expiry at least seven days after scoring and complete expected follow-up. Apply contact permission, do-not-contact, duplicate-account and concurrent-campaign rules before ranking. This operational pool can differ from the historical population; re-estimate baseline outcomes in it rather than assuming historical precision transfers.

Randomise customers 1:1 within risk quintile, preassignment expiry week and no-listening-record indicator, using centrally generated concealed permuted blocks. Persist the allocation and its seed/version in an auditable private assignment table. Keep one assignment per customer; do not re-enrol the same customer in later monthly snapshots during the study. Linked accounts require either a single customer-level identity or a redesigned cluster trial and power calculation.

If the pool exceeds the enrolment target, sample customers within the same strata before randomisation. Do not take an even higher-risk sublist without revising its control-rate assumptions. Balance treatment and control within strata. Offer delivery staff see only the operational treatment queue; the analyst can work with masked arm labels until the agreed analysis is locked.

Treatment receives the specified reminder and offer. Control receives normal service and mandatory communications but no additional retention treatment. Avoid cross-arm campaign contamination and log all other promotions. The effect is for the combined reminder-plus-offer package; this two-arm study does not separate the reminder's effect from the offer's effect.

The 10% pool is an **eligibility/ranking scenario**. Half the enrolled customers receive treatment; it does not mean contacting the entire historical 10% list. The planning example below enrolls 23,564 customers and treats 11,782.

## Outcomes and follow-up

**Primary outcome:** at least one qualifying positive-paid, non-refunded renewal after randomisation and by 30 days after the expiry date frozen before assignment. Specify valid renewal transaction types and refund reconciliation before launch. A free extension alone does not count as a paid renewal. Treatment-induced changes to expiry must not move the assessment deadline. This operational definition deliberately avoids a post-treatment moving deadline; it is not identical to the historical effective-expiry reconstruction. Historical rates below are planning proxies requiring prospective confirmation.

Follow every randomised customer through this fixed deadline, including non-delivery, non-opening, refusal and non-redemption. With month-start scoring and expiry in that month, primary observation can extend to about 60 days after scoring. Add a predeclared reconciliation lag appropriate to the real ledger; the proposed working assumption is 14 days, subject to actual refund/data latency validation.

**Commercial outcome:** observed incremental contribution per randomised customer over the 90 days beginning at the frozen expiry date, including assigned contact/offer costs incurred before that window. Use recognised net service revenue less attributable variable service costs, refunds and incremental campaign costs. If discounts already reduce net revenue, do not subtract them again as an incentive expense. Include costs for customers who would renew anyway. Show setup costs separately and in the rollout business case. The final commercial readout can require roughly 120 days after the last scoring date, plus reconciliation lag. Early primary success does not justify claiming 90-day contribution before it is observed.

Track opt-outs, complaints, accidental duplicate contacts, refund/cancellation rates, delivery failures and net contribution. Proposed planning guardrails are an upper 95% confidence bound below +0.5 percentage points for incremental opt-outs and +0.2 points for incremental complaints. These tolerances are not company-approved or powered guarantees; validate their acceptability and achievable precision before launch. Severe customer incidents trigger operational review independently of statistical significance. Failure to rule out unacceptable harm means no rollout recommendation, even if retention improves.

## Analysis and missingness

Analyse intention to treat: all randomised customers remain in their assigned arm. The primary estimate is a stratum-weighted treatment-minus-control risk difference, weighted by enrolled stratum size. Report absolute percentage points, a two-sided 95% interval and the corresponding relative effect as secondary context. Use a prespecified stratification-adjusted estimator with robust variance; report the unadjusted randomised difference as a sensitivity check. The planning calculation uses independent equal-arm binomial approximations and does not assume a precision benefit from adjustment.

Do not compare only redeemers, delivered messages or contacted churners. Those groups are selected after assignment and do not identify the intention-to-treat effect. Do not interpret risk-model feature coefficients as causal mechanisms. Subgroup results for value-proxy, listening absence and risk bands are exploratory unless separately powered and registered.

Reconcile the assignment list to outcome and ledger coverage. A confirmed lack of qualifying renewal under complete observation is a non-renewal; a missing or corrupted feed is an unknown outcome. Report unknown outcomes by arm. For unresolved unknowns, the primary robustness rule uses bounds over all randomised customers: if S is known renewals, M unknown outcomes and N assigned customers, arm retention lies between S/N and (S+M)/N. The effect's lower bound treats treatment unknowns as non-renewals and control unknowns as renewals; the upper bound reverses those assignments. Apply the same stratum weighting and add sampling uncertainty at the endpoints. Do not silently exclude unknown outcomes or select a favourable imputation. Require the decision to survive these bounds; otherwise report inconclusive. Any model-based imputation is exploratory sensitivity only. The 5% recruitment allowance below is capacity planning, not a correction for attrition bias, and it does not guarantee the missing-outcome bounds will clear the commercial threshold.

No repeated unadjusted significance checks or outcome-based early stopping. Analyse at the fixed sample and maturity point. Monitor delivery/data quality and serious harm separately. Report any assignment-ratio discrepancy and its cause before interpreting results; investigate implementation failures rather than treating an unexplained imbalance as harmless. Predefine any sequential harm rules and multiplicity handling in the actual launch protocol.

## Sample size and commercial relevance

The [reproducible power calculation](../src/experiment_power.py) uses pooled null and nonpooled alternative variances for two independent proportions, numerically solving for equal-arm sample size. This follows the method described in [statsmodels' proportion-power documentation](https://www.statsmodels.org/stable/generated/statsmodels.stats.proportion.power_proportions_2indep.html). All calculations are approximations; six independent binomial simulations of 50,000 trials each check nominal type-I error and planned 90% power for a two-point effect.

For a **2-percentage-point absolute retention improvement**, two-sided alpha 5%, the complete-equivalent and 5%-allowance sizes are:

| Control retention proxy | Power | Complete-equivalent per arm | Enrol per arm | Total enrolment |
|---|---:|---:|---:|---:|
| Matched baseline: 64.15% | 80% | 8,909 | 9,378 | 18,756 |
| Matched baseline: 64.15% | 90% | 11,926 | 12,554 | 25,108 |
| Matched full union: 76.61% | 80% | 6,819 | 7,178 | 14,356 |
| Matched full union: 76.61% | 90% | 9,128 | 9,609 | 19,218 |
| Conservative 50% | 80% | 9,806 | 10,323 | 20,646 |
| Conservative 50% | 90% | 13,127 | 13,818 | 27,636 |

These historical label proxies come from the matched top-10% risk list, not the overall 5.59% churn prevalence. Effects of 1, 3 and 6 points are also calculated in [experiment_power.json](../reports/experiment_power.json). They are alternative planning targets, not estimated treatment effects.

Detecting a two-point gain is not sufficient for the reference economics: 0.02 × 60 − 3.50 = **−2.30 CU per treated customer**. With uniform 60 CU retained contribution and 3.50 CU expected contact/offer cost, the minimum worthwhile absolute effect is **5.833 percentage points**.

For an assumed true effect of **8 points**, plan for the lower endpoint of a two-sided 95% interval to exceed 5.833 points. A conservative variance bound of 0.25 per Bernoulli arm gives:

`n per arm = ceil[0.5 × (z(0.975) + z(power))² / (0.08 − 3.50/60)²]`

| Probability of clearing commercial threshold | Complete-equivalent per arm | Enrol per arm with 5% allowance | Total | Expected treatment variable cost, CU |
|---|---:|---:|---:|---:|
| 80% | 8,360 | 8,800 | 17,600 | 30,800 |
| 90% | 11,192 | 11,782 | 23,564 | 41,237 |

The **23,564-customer** design is a provisional commercial planning example, not an approved launch size or a promise of 90% power for every guardrail or the actual financial outcome. The 41,237 CU is an expected variable cost, not a spending ceiling: if every treated customer redeems a 10 CU offer, 0.50 CU outreach plus incentive could cost 123,711 CU before fixed costs. Recalculate with actual costs, value uncertainty, control rate, delivery rate and the chosen primary estimator. Direct financial-outcome power requires variance evidence that these data do not supply; a retention proxy cannot establish it.

## Decision rule

An eight-point absolute gain would correspond to conditional saves of approximately 22.32% under the matched baseline risk or 34.20% under full-union risk, if benefits came only from would-be churners. That is stronger than the 20% conditional-save example. The eight-point alternative is a sizing assumption requiring evidence; choosing it does not make that response plausible. An actual effect only slightly above break-even would require substantially more evidence to clear the commercial threshold.

The present recommendation is **further validation, then consider a controlled pilot**. No rollout recommendation follows from this historical project.

For a later experiment, require a credible positive primary retention effect, a lower confidence bound on measured incremental net contribution above zero after the full financial window, acceptable guardrails and robust missing-data conclusions. Under the reference uniform-value simplification, clearing the 5.833-point threshold is an additional planning criterion; it is not a substitute for actual contribution measurement. A statistically positive but commercially negative result means no rollout. If intervals are too wide or data quality changes the conclusion, report inconclusive rather than selecting a favourable source, segment or horizon afterwards.

General design background: [GOV.UK's randomised-comparison guidance](https://www.gov.uk/guidance/randomised-controlled-trial-comparative-studies) explains random allocation and consistent outcome assessment. Its domain is digital health; this subscription proposal is our application of those general design principles, not a claim that sector-specific rules apply here.
