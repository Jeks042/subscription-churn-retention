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

Account sign-in and competition agreement acceptance verified on 22 September 2026. Acceptance followed explicit user confirmation. The labeller, both label releases, both transaction releases, members and both listening-log releases have been downloaded.

Correction to the first log diagnosis: the six-field row at line 103,280,203 was at the end of an incomplete 8,037,335,040-byte extraction. The archive lists 30,514,081,415 uncompressed bytes. A fresh extraction completed with exit code zero and matches that size exactly. The authoritative local copy is `data/raw/original_logs_complete/user_logs.csv`; the shorter copy and its audit hardlink were moved into ignored `data/quarantine/` with `.incomplete` extensions to prevent accidental reuse. The full SQL audit is complete: 392,106,543 records, 5,234,111 customers, 26 months, no duplicate customer/date keys, missing keys or invalid dates. Duration anomalies and missing-member groups are retained for explicit feature handling. No source rows were repaired or discarded.

## Source-code boundary

The supplied labeller treats a gap below 30 days as renewal and a gap of at least 30 as churn. It orders same-day plan events and allows cancellation to shorten the effective expiry before the first subsequent renewal. Our tests cover these boundaries. The supplied code remains in ignored local storage; it is not redistributed in the public repository.
