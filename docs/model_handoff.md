# Milestone 2 model handoff

The private analytical database is `data/analytics/analytics.duckdb`. Reproduce it using the [SQL workflow](sql_workflow.md). Do not commit or redistribute its customer-level tables.

## Inputs for milestone 3

| Object | Intended use |
|---|---|
| model_features | Customer/date keys plus the explicit 38-predictor list; four missingness indicators included |
| cohort_labels | Reconstructed outcome, maturity and eligibility; join by both customer and scoring date |
| scoring_calendar | Training, selection, calibration and holdout assignment |
| preprocessing_parameters | Training-only median parameters, fitting counts and final fitting date |
| customer_features | Raw feature values and audit fields for debugging; not a SELECT * model matrix |
| feature_quality_summary | Observation coverage, missingness, anomalies and unmatched-member counts by scoring date |
| renewal_by_engagement | Descriptive renewal comparisons on non-holdout dates only |

Use `MODEL_PREDICTORS` from `src/feature_contract.py` in its defined order. Keys, split labels, outcome fields, audit dates and member presence are excluded. The expected analytical grain is one eligible customer per scoring date; recurring customers across dates are intentional. Do not use a random row split.

## Fit and evaluation contract

1. Read the existing calendar: train May–August 2016; select October; calibrate December; evaluate February 2017 once the model and capacity policies are frozen.
2. Verify the two feature-build manifests and the independent feature check before reading model inputs. All feature rows must join to exactly one mature label for this approved calendar.
3. Use the existing training-only median fills and missingness indicators. If fitting scaling, transformations or additional feature selection, fit them only on training; tune on selection and calibrate on calibration.
4. Keep holdout outcomes out of engagement exploration and selection. Source-validation prevalence/counts are already published; they must not drive model or threshold choices.
5. Compare prevalence and simple operational baselines with logistic regression before adding complexity. Preserve separate transaction-only and transaction-plus-listening models to measure the value of behavioural features.
6. Carry source-release sensitivity, 22 unresolved supplied-label differences, duration-capping assumptions and unproven ingestion availability into the evaluation. Do not select the source convention by holdout performance.
7. Report customer-aware uncertainty because subscribers can recur across dates. Missing-member customers remain in the population.

The prepared data support the documented retrospective target only. Model scores cannot establish persuadability, incremental retention impact, realised savings or readiness for operational deployment.
