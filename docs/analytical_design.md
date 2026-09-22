# Analytical design

**Design status: proposed; exact dates and source semantics must be validated in Milestone 1.**

## Population, grain and target

The intended grain is one eligible subscriber per scoring date. Eligibility must reflect customers who could actually receive an intervention before the relevant renewal decision.

Working target: non-renewal within 30 days following subscription expiry, subject to confirmation against the official competition definition and transaction ordering. Cancellation flags alone are not assumed to equal churn. Renewals, refunds/cancellations, overlapping plans and multiple transactions require documented ordering rules.

## Time contract

For each snapshot record scoring time T, feature cutoff, expiry horizon, intervention lead time and label-maturity date. Include only events available before T; distinguish event date from availability date where the source allows it.

Initial feature windows are 7, 30 and 90 days ending before T, conditional on source coverage. Any partial-history window must carry coverage indicators.

A negative label requires complete follow-up through the grace window. Right-censored cases must not be silently coded non-churn.

## Evaluation calendar

Training, tuning, calibration and final holdout move forward in time. Every training label must mature before the next evaluation scoring date. Overlapping outcome windows must be purged or separated by an appropriate gap.

Do not invent historical churn labels or claim rolling validation before proving reconstruction is feasible. If the available files support only a narrower temporal comparison, revise the design and record its limits.

Recurring customers across time may be appropriate for an existing-subscriber use case. Customer IDs are not predictors; report overlap and use customer-aware uncertainty estimates. A new-customer generalisation claim requires its own evaluation.

## Feature and cohort controls

Aggregate transactions and listening logs separately before joining. Check key uniqueness and row counts at every stage. Exclude labels, post-cutoff renewals and post-outcome fields from features. Fit preprocessing only on the training partition.

Cohort retention tables must state entry definitions, periods at risk, denominators and incomplete follow-up. Distinguish renewal cohorts from registration cohorts.

## Model assessment

Begin with prevalence and simple operational rules, then logistic regression. Add a challenger only if justified. Select models and calibrators on earlier data; freeze capacity thresholds before final holdout evaluation.

Report log loss, Brier score, calibration bins with counts, PR-AUC, ROC-AUC, precision/recall/lift at capacity and appropriate uncertainty. Review cohort and segment stability, including missing-data groups. Associations and model explanations are not causal drivers.

## Commercial and intervention evaluation

Compare risk-only and risk-plus-value ranking, with explicit horizon and cost assumptions. Export sensitivity and break-even scenarios. Do not label scenario totals as realised savings.

Propose a randomised retention test with eligibility, assignment unit, treatment/control, outcome horizon, incremental contribution, retention, opt-outs and discount cost as appropriate. Power and minimum detectable effect remain to be calculated from verified baseline rates.

## Required validation evidence

Source manifest; grain/key tests; chronology and label examples; split calendar; leakage checks; baseline comparison; calibration and capacity tables; scenario assumptions; final limitations.
