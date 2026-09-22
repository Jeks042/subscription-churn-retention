# Temporal feasibility review

**Calendar v1: implemented for retrospective SQL reconstruction. This is not a claim to reproduce the competition split or operational data availability.**

The source covers transaction event dates from January 2015 through March 2017. Baseline history uses the original release; March-only refreshed transactions extend final follow-up. The full-union version is a sensitivity analysis because its backdated records change historical populations and outcomes.

## Calendar and observed cohort counts

| Role | Scoring date | Lead-eligible, mature customers | Reconstructed churn | Churn rate | Latest maturity |
|---|---|---:|---:|---:|---|
| Training | 1 May 2016 | 575,183 | 36,805 | 6.3988% | 30 June 2016 |
| Training | 1 June 2016 | 582,690 | 36,113 | 6.1976% | 30 July 2016 |
| Training | 1 July 2016 | 598,400 | 31,160 | 5.2072% | 30 August 2016 |
| Training | 1 August 2016 | 632,984 | 30,679 | 4.8467% | 30 September 2016 |
| Selection | 1 October 2016 | 649,745 | 33,390 | 5.1389% | 30 November 2016 |
| Calibration | 1 December 2016 | 665,170 | 35,175 | 5.2881% | 30 January 2017 |
| Final holdout | 1 February 2017 | 680,401 | 38,037 | 5.5904% | 30 March 2017 |

There are 4,384,573 eligible customer/date records, not necessarily distinct people. All seven baseline cohorts have complete calendar follow-up under the recorded source endpoint. The original-only February cohort has 680,401 censored cases; March data are necessary to label it. Endpoint coverage does not establish that the source recorded every real transaction.

## Frozen SQL rules

- Score on the first day of the month; all features end the previous day.
- Use all available pre-scoring history to determine effective expiry with the supplied labeller's same-day ordering.
- Require expiry in that calendar month and at least seven days after scoring.
- Require observation through original expiry plus 30 days, including for early renewals.
- Gap below 30 days is renewal; gap of at least 30 is churn. Cancellations can shorten effective expiry before the first renewal.
- Aggregate 7/30/90-day features over [T-N,T); keep labels in a separate table.
- Do not fit transformations on later partitions. Recurring customer IDs are join keys, never predictors.

Every stage's latest maturity precedes the next stage's first scoring date. The SQL runner asserts this. The holdout outcome period is fully observed by 31 March 2017. Model/threshold selection must not use holdout outcomes, beyond these source-validation counts.

## Remaining interpretation limits

There are no ingestion timestamps or dated historical member snapshots. This supports a retrospective event-time study; it does not establish what a deployed system could actually have known on each scoring date. Supplied Kaggle labels remain diagnostic because they do not exactly match the reconstructed historical cohorts.

Release sensitivity is material: for February, the full union gives 679,310 eligible customers and 26,420 churn outcomes, versus 680,401 and 38,037 for the frozen baseline. Selection and calibration are affected too. Any later predictive findings must address this dependence before recommending an operational pilot. No claim of exact competition reproduction, causal retention effect or production readiness is approved.
