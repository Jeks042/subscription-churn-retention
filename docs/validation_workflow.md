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

Next implement exact key uniqueness and duplicate checks, join coverage, transaction ordering, cancellation/renewal resolution and manually reviewed label examples. The initial inventory script does not perform these checks.

## 4. Temporal feasibility

Use observed coverage to choose scoring dates and feature windows. A training label must be mature before the evaluation scoring date. Confirm follow-up completeness and intervention lead time. Document any departure from the competition's prediction setup.

## 5. Decision record

Only after the preceding checks, publish permitted aggregate findings and a GO/NO-GO decision in reports/validation_findings.md. Keep Issue #1 open until every acceptance criterion is met.

## Tool verification

```powershell
python -m unittest discover -s tests -v
```

Fixtures are synthetic and exercise impossible dates, missingness, malformed rows, invalid labels, compressed inputs, scan limits and duplicate headers. Passing these tests validates the inventory utility, not the KKBox dataset.
