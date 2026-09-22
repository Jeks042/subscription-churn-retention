"""Stream local CSV/CSV.GZ files into an aggregate inventory; never export rows."""
import argparse
import csv
import gzip
import hashlib
import json
from datetime import datetime, timezone
from pathlib import Path

DATE_COLUMNS = {"date", "transaction_date", "membership_expire_date", "registration_init_time"}
MISSING = {"", "null", "nan", "na", "n/a"}


def profile_file(path, max_rows=None):
    path = Path(path)
    digest = hashlib.sha256()
    with path.open("rb") as source:
        for chunk in iter(lambda: source.read(1024 * 1024), b""):
            digest.update(chunk)
    result = {"filename": path.name, "size_bytes": path.stat().st_size,
              "sha256": digest.hexdigest(), "rows_scanned": 0,
              "complete_scan": True, "malformed_rows": 0}
    opener = gzip.open if path.name.lower().endswith(".gz") else open
    with opener(path, "rt", encoding="utf-8-sig", newline="") as source:
        reader = csv.reader(source)
        columns = next(reader, None)
        if not columns or len(set(columns)) != len(columns) or any(not c.strip() for c in columns):
            raise ValueError("CSV must have a nonempty, unique header")
        result["columns"] = columns
        result["missing_counts"] = {c: 0 for c in columns}
        dates = {c: {"min": None, "max": None, "invalid": 0} for c in columns if c in DATE_COLUMNS}
        labels = {"0": 0, "1": 0, "invalid": 0} if "is_churn" in columns else None
        for row in reader:
            if max_rows is not None and result["rows_scanned"] >= max_rows:
                result["complete_scan"] = False
                break
            result["rows_scanned"] += 1
            if len(row) != len(columns):
                result["malformed_rows"] += 1
                continue
            for col, value in zip(columns, row):
                value = value.strip()
                if value.lower() in MISSING:
                    result["missing_counts"][col] += 1
                    continue
                if col in dates:
                    try:
                        if len(value) != 8 or not value.isascii() or not value.isdigit():
                            raise ValueError("Expected YYYYMMDD")
                        parsed = datetime.strptime(value, "%Y%m%d").date().isoformat()
                        stat = dates[col]
                        stat["min"] = min(stat["min"], parsed) if stat["min"] else parsed
                        stat["max"] = max(stat["max"], parsed) if stat["max"] else parsed
                    except ValueError:
                        dates[col]["invalid"] += 1
                if col == "is_churn":
                    labels[value if value in ("0", "1") else "invalid"] += 1
        result["dates"] = dates
        if labels is not None:
            result["label_counts"] = labels
    return result


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--input-dir", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("--max-rows", type=int, help="Optional smoke scan; not a full validation")
    args = parser.parse_args()
    if args.max_rows is not None and args.max_rows < 1:
        parser.error("--max-rows must be positive")
    paths = sorted(p for p in args.input_dir.iterdir() if p.is_file() and
                   (p.name.lower().endswith(".csv") or p.name.lower().endswith(".csv.gz")))
    if not paths:
        parser.error("No CSV or CSV.GZ files found; extract authorised archives first")
    if args.output.resolve() in [p.resolve() for p in paths]:
        parser.error("Output must not overwrite an input")
    records = []
    for path in paths:
        print(f"Profiling {path.name}", flush=True)
        records.append(profile_file(path, args.max_rows))
    report = {"generated_utc": datetime.now(timezone.utc).isoformat(),
              "scope": "file inventory only; not label reconciliation or temporal approval",
              "files": records}
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(report, indent=2) + "\n", encoding="utf-8")
    print(f"Inventory written for {len(records)} file(s).")


if __name__ == "__main__":
    main()
