# Analytical design

**Design status: calendar v1 and transaction SQL implemented for a retrospective event-time study; model fitting and operational claims remain gated.**

## Population, grain and target

The intended grain is one eligible subscriber per scoring date. Eligibility must reflect customers who could actually receive an intervention before the relevant renewal decision.

Implemented target: no recorded non-cancellation renewal with a gap below 30 days from effective expiry. A gap of exactly 30 days is churn. Cancellation flags alone are not churn. Source same-day ordering, a seven-day contact lead, and full original-expiry-plus-30-day follow-up are documented in the [label examples](label_examples.md) and [calendar](temporal_feasibility.md). Supplied competition labels are diagnostic; the study uses separately reconstructed historical cohorts.

## Time contract

For each snapshot record scoring time T, feature cutoff, expiry horizon, intervention lead time and label-maturity date. Include only events available before T; distinguish event date from availability date where the source allows it.

Initial feature windows are 7, 30 and 90 days ending before T, conditional on source coverage. Any partial-history window must carry coverage indicators.

A negative label requires complete follow-up through the grace window. Right-censored cases must not be silently coded non-churn.

## Evaluation calendar

Training, tuning, calibration and final holdout move forward in time. Every training label must mature before the next evaluation scoring date. Overlapping outcome windows must be purged or separated by an appropriate gap.

Historical outcomes are reconstructed from recorded transactions using the published SQL contract. Source release sensitivity and missing ingestion timestamps limit this to retrospective event-time evaluation. The dataset does not support an exact competition reproduction or proven historical deployment claim.

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
