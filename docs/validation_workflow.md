# Source validation workflow

## 1. Authorised acquisition

Sign in to the official KKBox competition page and confirm access. The account holder must review and accept any required competition agreement. Record file versions, acquisition date and source URLs. Do not obtain restricted files from unauthorised mirrors.

## 2. File inventory

Place authorised CSV or CSV.GZ files under ignored `data/raw/`. Extract other archive formats locally first. From the project directory, run:

```powershell
python src/profile_source.py --input-dir data/raw --output data/validation/source_inventory.json
```

The standard-library script streams records without loading the dataset into memory. It hashes each complete file, then counts rows, missing fields, malformed records, valid date ranges and binary label values. It exports no customer rows or identifier values. A full scan can take considerable time on listening logs.

For an initial format check add `--max-rows 10000`. That still hashes the whole file but only profiles the initial records. Such output is explicitly marked incomplete and must not be reported as full-file statistics.

Null counts, date ranges and label counts exclude malformed-width rows; malformed rows are counted separately. Missing date/label values are reported in missing_counts, not invalid counts. ZIP/7z archives are not directly supported. Schema roles must be reviewed manually; sample-submission labels must never be treated as observed outcomes.

## 3. Relational validation

The following commands implement label-key checks, transaction duplicates and join coverage, deterministic sampled renewal reconstruction and release diagnostics. The initial inventory script alone does not perform these checks.

```powershell
python -m venv .venv
.\.venv\Scripts\python.exe -m pip install -r requirements.txt
.\.venv\Scripts\python.exe src/audit_labels.py --input-dir data/raw --output data/validation/label_audit.json
.\.venv\Scripts\python.exe src/audit_transactions.py --input-dir data/raw --output-dir data/validation
.\.venv\Scripts\python.exe src/check_release_overlap.py
.\.venv\Scripts\python.exe src/diagnose_label_windows.py
.\.venv\Scripts\python.exe src/audit_auxiliary.py --members data/raw/members_v3.csv --logs data/raw/data/churn_comp_refresh/user_logs_v2.csv --output-dir data/validation
.\.venv\Scripts\python.exe src/audit_cohorts.py --database data/validation/validation.duckdb --output data/validation/cohort_audit.json
.\.venv\Scripts\python.exe src/review_label_differences.py --database data/validation/validation.duckdb --output data/validation/label_differences.json
```

Run from the project root. The v2 archives contain nested paths; copy train_v2.csv and transactions_v2.csv to data/raw/ after extraction, or preserve the documented arrangement. Audit outputs and DuckDB databases remain in ignored data/validation/. The auxiliary command deliberately scans the refreshed log file only. It does not stand in for an audit of the original logs.

Transaction source union is diagnostic. It is not yet an approved production merge or deduplication policy. Sample reconciliation deliberately uses all pre-cutoff history; diagnose_label_windows.py separately checks the source example's previous-month filter. Neither script silently treats censored outcomes as non-churn.

For the original listening log, verify the archive listing and wait for extraction to exit successfully. File presence alone is insufficient. The first interrupted extraction was only 8 GB of a 30.5 GB CSV and is now quarantined. Audit the complete path explicitly:

```powershell
tar -tvf "$env:USERPROFILE/Downloads/user_logs.csv.7z"
.\.venv\Scripts\python.exe src/audit_auxiliary.py --members data/raw/members_v3.csv --logs data/raw/original_logs_complete/user_logs.csv --expected-log-bytes 30514081415 --output-dir data/validation/original_complete
```

The SQL audit strictly parses every record, hashes the complete source, checks keys/dates/seconds, scans duplicates per month to bound memory, and reports member-join coverage. It can take tens of minutes on the full original release. No permissive row skipping is enabled. DuckDB spill files use an isolated system temporary directory outside the synced workspace.

The [transaction SQL workflow](sql_workflow.md) implements the documented baseline convention and has its own assertions. Verify its labels against the separate Python implementation with:

```powershell
.\.venv\Scripts\python.exe src/verify_sql_reconstruction.py --database data/analytics/analytics.duckdb --output data/validation/sql_reconstruction_check.json
```

## 4. Temporal feasibility

Use observed coverage to choose scoring dates and feature windows. A training label must be mature before the evaluation scoring date. Confirm follow-up completeness and intervention lead time. Document any departure from the competition's prediction setup.

## 5. Decision record

Only after the preceding checks, publish permitted aggregate findings and a GO/NO-GO decision in reports/validation_findings.md. Keep Issue #1 open until every acceptance criterion is met.

## Tool verification

```powershell
.\.venv\Scripts\python.exe -m unittest discover -s tests -v
```

Synthetic tests cover inventory, incomplete-extraction guards, label keys, the 30-day boundary, censoring, same-day ordering, cancellation handling, SQL duplicate inflation and post-cutoff leakage. Full source scans and the 7,000-record SQL/Python comparison are separate evidence from these tests.
