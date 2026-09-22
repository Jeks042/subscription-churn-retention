# Data access and handling

Verified source: [KKBox/WSDM competition data](https://www.kaggle.com/competitions/kkbox-churn-prediction-challenge/data).

Access and use are subject to the [competition rules](https://www.kaggle.com/c/kkbox-churn-prediction-challenge/rules). Download only through an authorised account after the account holder has accepted applicable terms. Access was confirmed and the agreement accepted with explicit user authorisation on 22 September 2026. See the validation findings for source audits and analytical limitations.

Do not commit source files, customer-level extracts, identifiers, credentials, fitted artifacts containing restricted information or data-bearing Power BI files. Public aggregate outputs require a disclosure and rules review.

For each downloaded file, record original name, source URL, acquisition date, release/version, byte size, SHA-256, row count, grain, keys, date coverage and null/duplicate checks. Confirm actual schemas before implementing ingestion.

Keep raw, interim and processed data in ignored directories or approved external storage. The source data is not covered by any future code licence for this repository.

The complete original listening CSV is under `data/raw/original_logs_complete/user_logs.csv`; it must be 30,514,081,415 bytes. The first interrupted extraction and its hardlink are quarantined under `data/quarantine/` with .incomplete extensions. Do not use them. Refreshed logs retain the nested archive path `data/raw/data/churn_comp_refresh/user_logs_v2.csv`.

Aggregate findings are in reports/validation_findings.md. Calendar v1 and the transaction SQL contract are implemented for retrospective reconstruction; ingestion availability is unproven and no model results are claimed. Local `data/analytics/analytics.duckdb` contains private features and labels. Only its aggregate run manifest is published.
