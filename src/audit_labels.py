"""Check label keys and release overlap without exporting customer identifiers."""
import argparse
import csv
import json
from pathlib import Path


def read_labels(path):
    labels = {}
    counts = {"rows": 0, "missing_ids": 0, "invalid_labels": 0,
              "duplicate_key_rows": 0, "conflicting_duplicate_rows": 0}
    with Path(path).open(encoding="utf-8-sig", newline="") as file:
        reader = csv.DictReader(file)
        if reader.fieldnames != ["msno", "is_churn"]:
            raise ValueError("Unexpected label schema")
        for row in reader:
            counts["rows"] += 1
            key = (row.get("msno") or "").strip()
            value = row.get("is_churn")
            if not key:
                counts["missing_ids"] += 1
                continue
            if value not in ("0", "1") or None in row:
                counts["invalid_labels"] += 1
                continue
            if key in labels:
                counts["duplicate_key_rows"] += 1
                if labels[key] != value:
                    counts["conflicting_duplicate_rows"] += 1
            else:
                labels[key] = value
    counts["unique_valid_ids"] = len(labels)
    counts["churned_unique_ids"] = sum(v == "1" for v in labels.values())
    counts["churn_rate"] = counts["churned_unique_ids"] / len(labels) if labels else None
    return counts, labels


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--input-dir", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    first, a = read_labels(args.input_dir / "train.csv")
    second, b = read_labels(args.input_dir / "train_v2.csv")
    overlap = a.keys() & b.keys()
    result = {"train.csv": first, "train_v2.csv": second,
              "overlapping_ids": len(overlap),
              "changed_label_among_overlap": sum(a[k] != b[k] for k in overlap),
              "interpretation": "Releases describe different periods; changed labels are not automatically errors. Do not concatenate as one cohort."}
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(result, indent=2) + "\n", encoding="utf-8")
    print(json.dumps(result, indent=2))


if __name__ == "__main__":
    main()
