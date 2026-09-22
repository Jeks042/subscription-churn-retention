# Reproducible SQL foundation

The pipeline builds retrospective transaction cohorts, listening features and a combined model-input table. It does not fit a predictive model or claim historical operational availability: the releases have event dates but no ingestion timestamps.

The successful full-data [run manifest](../reports/sql_build_summary.json) and [independent reconstruction check](../reports/sql_reconstruction_check.json) contain aggregate evidence only. The manifest records 4,384,573 eligible feature rows and passed SQL assertions; the separate check found no disagreements across 7,000 sampled customer/date records.

## Run

From the repository root, with authorised `transactions.csv` and `transactions_v2.csv` in `data/raw/`:

```powershell
.\.venv\Scripts\python.exe src/build_sql.py --input-dir data/raw --output-dir data/analytics
.\.venv\Scripts\python.exe src/build_listening.py --database data/analytics/analytics.duckdb --log-database data/validation/original_complete/auxiliary.duckdb --audit-report data/validation/original_complete/auxiliary_audit.json --output-dir data/analytics
.\.venv\Scripts\python.exe src/verify_listening_features.py --database data/analytics/analytics.duckdb --log-database data/validation/original_complete/auxiliary.duckdb --output data/validation/listening_feature_check.json
.\.venv\Scripts\python.exe -m unittest discover -s tests -v
```

The pinned DuckDB version is in requirements.txt. Allow several minutes and local disk space for the database and spill files. The runner reports each stage, writes the database atomically in one transaction and writes a success manifest only after all assertions pass. Reruns replace analytical tables; a failed rerun rolls back and removes any stale success manifest. Raw files remain untouched. The manifest records source and SQL hashes, population counts and assertions. Permanent outputs remain in ignored `data/analytics/`; temporary DuckDB spill files use an isolated system temporary directory outside OneDrive and are cleaned after a successful run. This avoids the database-close failure observed with spill files in the synced workspace.

## Tables and source policy

| SQL | Output | Contract |
|---|---|---|
| 001_stage_transactions.sql | stg_transactions | Original release plus March-only v2; collapse exact nine-field duplicates |
| 002_cohorts.sql | cohort_candidates, cohort_labels | Customer/scoring-date key; upcoming month expiry; source ordering; 30-day follow-up |
| 003_transaction_features.sql | transaction_features, cohort_summary | At least seven-day intervention lead; strictly pre-scoring features; explicit denominators |
| 004_assertions.sql | Fails run on violations | Unique keys, population reconciliation, cutoff boundaries and separate targets |
| 005_listening_features.sql | listening_features | Per-customer 7/30/90-day log aggregates, bounded durations, anomaly flags and observed calendar coverage |
| 006_combine_features.sql | customer_features, feature_quality_summary, renewal_by_engagement | One-to-one feature join; member presence diagnostic; outcome joins only for aggregate renewal analysis |
| 007_feature_assertions.sql | Fails run on violations | Listening cutoffs, combined keys/counts, bounded durations and summary denominators |
| src/feature_contract.py | preprocessing_parameters, model_features | Explicit 38-predictor allowlist; training-only median fills plus missingness indicators |

The v2 release contains backdated rows that materially change historical outcomes. The baseline freezes original history, uses March-only records to extend February follow-up, and keeps the full-union treatment as a sensitivity study. This is an explicit analytical convention, not proof that the original version is the definitive corrected truth. Models must be interpreted alongside this sensitivity. Source dates alone cannot prove there were no missing renewals.

Monthly eligibility uses the last effective expiry known before scoring, applying the supplied labeller's event ordering. All pre-scoring history is used; the competition demo's one-month history filter is not reproduced. The target is our reconstructed historical renewal outcome, not a concatenation of supplied labels. A cancellation may shorten expiry before the first renewal; a renewal gap of exactly 30 days is churn. Full follow-up is required through the original expiry plus 30 days. Labels and feature tables are separate.

`cohort_summary` reports candidates, lead-eligible customers, mature and censored denominators, churn and renewed counts. Renewal rate divides renewals by mature lead-eligible customers. It is an expiry-cohort renewal rate, not a registration-cohort survival curve or intervention effect.

## Feature dictionary

| Column | Meaning and availability |
|---|---|
| scoring_date, msno | Join keys; customer identifier is excluded from prediction |
| days_to_expiry | Effective pre-scoring expiry minus scoring date; eligibility requires >=7 |
| transaction_recency_days | Days since latest pre-scoring transaction, using all available original history |
| transaction_coverage_days_90 | Days of dataset calendar coverage capped at 90; does not assert individual subscriber tenure |
| transaction_count_7d/30d/90d | Deduplicated transaction events in [T-N,T); includes cancellations |
| cancellation_count_90d | Recorded cancellation events; not equivalent to churn |
| subscription_count_90d | Recorded non-cancellation events |
| auto_renew_flag_count_90d | Events marked auto-renew; not an inferred current subscription status |
| subscription_recorded_amount_90d | Sum of recorded amounts on non-cancellation events; not net revenue, profit or lifetime value |
| expiry_before_event_count_90d | Quality flag count; anomalous events are retained |
| max_feature_event_date | Audit field excluded from prediction; must precede T |

Transaction counts and window amounts use zero for no observed events; transaction recency uses history beyond the window. Member attributes remain excluded because snapshot availability at historic cutoffs is unproven. No scaling, categorical encoding or predictive model has been fitted.

## Listening feature dictionary

The original log provides the pre-scoring history for all seven dates. The latest scoring date is 1 February 2017, so no refreshed March listening records are needed. The source has one row per customer/day; an observed row is a recorded log day, not proof of active subscription or continuous listening.

For each N in 7, 30 and 90, windows are [T-N,T):

| Column | Meaning and handling |
|---|---|
| listening_log_days_Nd | Number of recorded customer/day rows; zero means no observed records, not proven inactivity |
| listening_bounded_seconds_Nd | Sum of finite nonnegative recorded seconds capped at 86,400 per daily record; zero for no rows, NULL if rows exist but all durations are unusable |
| listening_usable_duration_days_Nd | Records with a finite nonnegative duration; includes capped records |
| listening_negative_seconds_days_Nd | Records with negative finite durations, excluded from duration totals but retained in record counts |
| listening_over_24h_days_Nd | Records above 86,400 seconds, retained with the explicit feature cap and this flag |
| listening_missing_seconds_days_Nd | Missing, unparseable or nonfinite duration values |
| log_source_days_Nd | Distinct calendar days with any source record in the window; dataset coverage, not individual tenure |
| listening_recency_90d | Days since the most recent recorded log in the 90-day window; NULL when none exists |
| no_listening_logs_90d | Explicit no-records indicator |
| max_listening_event_date | Audit-only field, excluded from predictors; must be before T |

The cap is a declared robust feature definition, not a correction to source truth. Multi-device or logging semantics may yield unusually large recorded values; raw values remain in the private source cache for sensitivity work. Customers with anomalies remain eligible. Individual observation is represented by recorded-day counts, no-record flags, unusable-duration counts and recency missingness. The data cannot distinguish all causes of an absent daily log or establish individual tenure.

## Audited cache and reproducibility

Build `original_complete/auxiliary.duckdb` from the authorised CSV with the exact [audit command](validation_workflow.md). The listening runner checks the audited row count, source key/date checks and member uniqueness; it fingerprints the read-only cache and audit report. It never modifies that source database. The cache is a reproducible intermediate, not an additional downloaded data release. The full pipeline is source audit -> transaction build -> listening build -> independent verification.

Both build stages use transactions and isolated system temporary directories. The listening run emits a new success manifest only after assertions, commit and database close. A transaction rebuild invalidates the downstream listening/combined/model tables and the listening success manifest in the same output directory, preventing accidental reuse of stale model inputs. Re-run the listening stage whenever the transaction tables change. Public reports contain only aggregates; databases and all customer-level tables stay local.

## Training-only preparation and handoff

`customer_features` retains raw missing values and audit dates. `model_features` selects only the 34 declared transaction/listening predictors, plus four missingness indicators, with customer/date keys for joining. It contains no outcomes, split labels, member presence, identifiers as predictors, or audit dates as predictors. Use the ordered `MODEL_PREDICTORS` allowlist from `src/feature_contract.py` when constructing a model matrix; never use SELECT * as a predictor list.

Medians for the three bounded-duration totals and 90-day listening recency are fitted only on calendar rows labelled train (May–August 2016). Each receives a missingness indicator. If an entire training feature is missing, a recorded fixed zero fallback applies. Counts are defined as zero for no observed events and need no learned fill. `preprocessing_parameters` records the training count, final fitting date, medians and nonmissing training counts. Selection, calibration and holdout values cannot change these parameters. Model-specific scaling, if needed, must also be fitted on training only in milestone 3.

`renewal_by_engagement` gives expiry-cohort renewal rates by 0, 1–7, 8–20 and 21–30 recorded days in the prior 30 days for the training, selection and calibration dates. Holdout outcomes are excluded from this exploratory comparison until final model evaluation; an assertion enforces that boundary. Denominators and censored counts are explicit. These are descriptive associations, not evidence that inducing listening activity causes retention. The member-snapshot join is restricted to `feature_quality_summary` so unmatched customers are counted without being removed or used as a predictor.
