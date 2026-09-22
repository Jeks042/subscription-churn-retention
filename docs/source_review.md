# KKBox source review

Reviewed 22 September 2026 against the [official data description](https://www.kaggle.com/competitions/kkbox-churn-prediction-challenge/data).

## Verified source documentation

- Churn requires no valid renewal within 30 days after expiry. Cancellation can represent a plan change and is not sufficient by itself.
- Kaggle lists 10 files totalling 8.95 GB: nine 7z archives and a Scala label generator.
- Label files: train.csv and train_v2.csv. Submission templates contain prediction targets, not observed outcomes.
- Transaction and listening histories have original and v2 releases; documentation gives February and March 2017 coverage endpoints respectively.
- members_v3.csv replaces the earlier member snapshot and removes its expiry field. Member coverage is incomplete and age values require quality checks.
- WSDMChurnLabeller.scala defines source labelling logic. Its example dates require careful interpretation.

These are documentation statements, not measurements of downloaded files.

## Design implications to verify

The refreshed label release must not automatically be paired with every refreshed feature record. We must establish the actual prediction cutoff first. Future transactions may help establish outcomes while being inadmissible as predictors.

The final temporal test needs enough follow-up for every included expiry. A convenient month-to-month split may fail this requirement. We will resolve exact boundary behaviour and transaction ordering against the labeller and actual files before approving a calendar.

## Access state

Account sign-in and competition agreement acceptance verified on 22 September 2026. Acceptance followed explicit user confirmation. The labeller, both label releases, both transaction releases, members and both listening-log releases have been downloaded. The original log is present locally, but a strict parse stopped at line 103,280,203 on a malformed-width row (six fields where nine were expected); the full inventory and deterministic handling rule are still pending.

## Source-code boundary

The supplied labeller treats a gap below 30 days as renewal and a gap of at least 30 as churn. It orders same-day plan events and allows cancellation to shorten the effective expiry before the first subsequent renewal. Our tests cover these boundaries. The supplied code remains in ignored local storage; it is not redistributed in the public repository.

