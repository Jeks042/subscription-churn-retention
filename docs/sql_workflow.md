# Reproducible SQL foundation

This first implementation builds retrospective transaction cohorts and features. It does not fit a model or claim historical operational availability: the releases have event dates but no ingestion timestamps. Listening features are a subsequent stage after the complete original log passes validation.

The successful full-data [run manifest](../reports/sql_build_summary.json) and [independent reconstruction check](../reports/sql_reconstruction_check.json) contain aggregate evidence only. The manifest records 4,384,573 eligible feature rows and passed SQL assertions; the separate check found no disagreements across 7,000 sampled customer/date records.

## Run

From the repository root, with authorised `transactions.csv` and `transactions_v2.csv` in `data/raw/`:

```powershell
.\.venv\Scripts\python.exe src/build_sql.py --input-dir data/raw --output-dir data/analytics
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

Counts and window amounts use zero for no observed events; recency uses history beyond the window. No population-fitted imputation, scaling, encoding, member age or gender has been applied. Training-only preprocessing will be added with the model pipeline. Member attributes are deferred because snapshot availability at historic cutoffs is unproven.
