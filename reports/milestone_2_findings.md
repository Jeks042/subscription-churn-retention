# Milestone 2 — completed SQL foundation

**22 September 2026: complete.** The full build exited successfully, preserved all 4,384,573 eligible customer/date rows, and produced a separate 38-predictor model-input table. No predictive model has been fitted.

Evidence: [full build manifest](listening_build_summary.json), [independent listening check](listening_feature_check.json), [transaction build](sql_build_summary.json), [label implementation check](sql_reconstruction_check.json), [SQL workflow and dictionary](../docs/sql_workflow.md), and [model handoff](../docs/model_handoff.md).

## Delivered

- Versioned transaction and listening SQL, with 7/30/90-day features strictly before scoring.
- One row per eligible customer/date, with key, row-count, cutoff, duration-bound and target-exclusion assertions.
- Explicit no-record, unusable-duration and capped-duration indicators; no customer exclusions for missing member records.
- Training-only median fills for three duration totals and listening recency, plus four missingness indicators. The fit uses 2,389,257 training rows through the 1 August 2016 scoring date.
- Descriptive renewal summaries with explicit mature denominators; holdout outcomes are excluded from engagement comparisons.
- A reproducible audited-cache input, recorded source/code hashes, isolated temporary storage and invalidation of downstream features when transaction cohorts are rebuilt.

## Observed coverage and quality

| Scoring date | Eligible snapshots | No logs in prior 90 days | Without member record | Customers with capped duration |
|---|---:|---:|---:|---:|
| 2016-05-01 | 575,183 | 106,268 | 70,937 | 2,354 |
| 2016-06-01 | 582,690 | 107,785 | 71,175 | 2,234 |
| 2016-07-01 | 598,400 | 111,036 | 72,535 | 2,195 |
| 2016-08-01 | 632,984 | 119,922 | 78,259 | 2,186 |
| 2016-10-01 | 649,745 | 123,734 | 80,530 | 2,525 |
| 2016-12-01 | 665,170 | 132,224 | 83,386 | 2,493 |
| 2017-02-01 | 680,401 | 133,486 | 85,887 | 3,121 |

All seven scoring dates have 90 distinct source calendar days in their lookback. Individual customers average about 37–39 recorded days; roughly 18–20% have no logs in the window. Absence of a record is not proof of inactivity or missing acquisition. Customer tenure and historical ingestion availability remain unknown.

Among the eligible snapshots, 108, 77 and 27 have negative durations in the May, June and July lookbacks respectively; later lookbacks have none. Raw duration totals have no missing values in these observed cohorts because each window either contains a usable duration or no records (defined total zero). Recency is missing for the no-log group and is filled using the training median of one day, with both no-log and missingness indicators retained. All other raw predictor columns have zero missing values. The model-input table has no NULL or nonfinite predictors.

## Descriptive renewal by recorded activity

The following combines the six non-holdout expiry cohorts. Counts are customer/date snapshots; people can recur. Every included label is mature under the frozen historical definition.

| Recorded days in prior 30 days | Mature snapshots | Reconstructed churn | Renewal rate |
|---|---:|---:|---:|
| 0 | 831,956 | 33,425 | 95.9824% |
| 1–7 | 625,786 | 44,192 | 92.9382% |
| 8–20 | 1,042,813 | 67,766 | 93.5016% |
| 21–30 | 1,203,617 | 57,939 | 95.1863% |

There is no simple monotonic relationship between recorded listening days and renewal in these cohorts. In particular, the no-record group has a high renewal rate. Treat missing listening history as a separate segment, and evaluate transaction-only versus combined baselines before assuming behavioural features add value. These descriptive rates do not identify causal drivers, treatment effects or profitable interventions. Source-version sensitivity also remains material.

## Validation and handoff

Fifteen synthetic tests pass, including exact date boundaries, capped/negative/nonfinite durations, absent logs, missing members, no future feature leakage, training-only parameter fitting, holdout-report exclusion and stale-table invalidation. All full-data SQL assertions passed. A separate Python aggregation checked 16,100 listening feature values across 700 sampled customer/date rows and found zero differences. The earlier independent label check covers 7,000 sampled rows with zero implementation disagreements.

Milestone 3 can now build and evaluate baselines using the explicit predictor list and temporal partitions. Retain the [source-validation limits](validation_findings.md): the target is reconstructed, 22 supplied-label differences remain unexplained, release versions affect outcomes, and event dates do not prove operational availability. No exact competition reproduction or production-readiness claim is approved.
