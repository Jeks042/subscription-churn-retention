"""Exact SQL transaction checks and private deterministic label reconciliation."""
import argparse
import calendar
import json
from collections import defaultdict
from datetime import datetime, timedelta
from pathlib import Path
import duckdb


def date(value):
    try:
        return datetime.strptime(value, "%Y%m%d").date()
    except (ValueError, TypeError):
        return None


def order_key(row):
    # Preserve the source labeller's string-concatenated plan signature.
    signature = row["plan_list_price"] + row["payment_plan_days"] + row["payment_method_id"]
    # Negative codepoints reverse lexical order, including prefix behaviour.
    reverse_signature = tuple(-ord(c) for c in signature) + (1,)
    expiry = int(row["membership_expire_date"])
    cancel = row["is_cancel"]
    return (row["transaction_date"], reverse_signature, cancel, -expiry if cancel == "1" else expiry)


def reconcile(history, cutoff, month_start, month_end, observed_until):
    before = [r for r in history if r["transaction_date"] <= cutoff]
    if not before:
        return "no_history", None
    if any(date(r["transaction_date"]) is None or date(r["membership_expire_date"]) is None
           or r["is_cancel"] not in ("0", "1") for r in history):
        return "invalid_history", None
    expiry = sorted(before, key=order_key)[-1]["membership_expire_date"]
    if not month_start <= expiry <= month_end:
        return "outside_expiry_cohort", None
    last_expiry = date(expiry)
    # Conservative maturity: original expiry plus the full 30-day period.
    if last_expiry + timedelta(days=30) > date(observed_until):
        return "censored", None
    for row in sorted((r for r in history if cutoff < r["transaction_date"] <= observed_until), key=order_key):
        if row["is_cancel"] == "1":
            last_expiry = min(last_expiry, date(row["membership_expire_date"]))
        else:
            return "reconciled", int((date(row["transaction_date"]) - last_expiry).days >= 30)
    return "reconciled", 1


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--input-dir", type=Path, required=True)
    parser.add_argument("--output-dir", type=Path, required=True)
    parser.add_argument("--sample-size", type=int, default=2000)
    args = parser.parse_args()
    args.output_dir.mkdir(parents=True, exist_ok=True)
    con = duckdb.connect(str(args.output_dir / "validation.duckdb"))
    con.execute("SET threads=4")
    con.execute("SET memory_limit='4GB'")
    results = {}
    for name in ("transactions", "transactions_v2", "train", "train_v2"):
        print("Loading " + name, flush=True)
        con.execute(f"CREATE OR REPLACE TABLE {name} AS SELECT * FROM read_csv(?, header=true, all_varchar=true)", [str(args.input_dir / (name + ".csv"))])
    con.execute("CREATE OR REPLACE VIEW all_tx AS SELECT * FROM transactions UNION ALL SELECT * FROM transactions_v2")
    for name in ("transactions", "transactions_v2"):
        print("Auditing " + name, flush=True)
        q = f"""SELECT count(*) AS row_count, count(DISTINCT msno) customers,
            min(transaction_date) min_transaction_date, max(transaction_date) max_transaction_date,
            count(*) FILTER(WHERE try_strptime(transaction_date,'%Y%m%d') IS NULL) invalid_transaction_dates,
            count(*) FILTER(WHERE try_strptime(membership_expire_date,'%Y%m%d') IS NULL) invalid_expiry_dates,
            count(*) FILTER(WHERE membership_expire_date < transaction_date) expiry_before_transaction,
            count(*) FILTER(WHERE is_cancel NOT IN ('0','1') OR is_cancel IS NULL) invalid_cancel,
            count(*) FILTER(WHERE is_auto_renew NOT IN ('0','1') OR is_auto_renew IS NULL) invalid_auto_renew
            FROM {name}"""
        cursor = con.execute(q)
        stats = dict(zip([d[0] for d in cursor.description], cursor.fetchone()))
        stats["exact_duplicate_excess"] = con.execute(f"SELECT coalesce(sum(n-1),0) FROM (SELECT msno,payment_method_id,payment_plan_days,plan_list_price,actual_amount_paid,is_auto_renew,transaction_date,membership_expire_date,is_cancel,count(*) n FROM {name} GROUP BY ALL HAVING count(*)>1)").fetchone()[0]
        stats["customer_days_with_multiple_transactions"] = con.execute(f"SELECT count(*) FROM (SELECT msno,transaction_date FROM {name} GROUP BY ALL HAVING count(*)>1)").fetchone()[0]
        results[name] = stats
    results["monthly_rows"] = con.execute("SELECT substr(transaction_date,1,6),count(*) FROM all_tx GROUP BY 1 ORDER BY 1").fetchall()
    results["label_join_coverage"] = {}
    for name in ("train", "train_v2"):
        results["label_join_coverage"][name] = con.execute(f"SELECT count(*) FROM {name} l WHERE NOT EXISTS (SELECT 1 FROM all_tx t WHERE t.msno=l.msno)").fetchone()[0]
    con.execute("CREATE OR REPLACE TEMP TABLE sample_ids AS SELECT msno FROM (SELECT msno FROM train ORDER BY md5(msno) LIMIT ?) UNION SELECT msno FROM (SELECT msno FROM train_v2 ORDER BY md5(msno) LIMIT ?)", [args.sample_size, args.sample_size])
    cursor = con.execute("SELECT t.* FROM all_tx t JOIN sample_ids s USING(msno)")
    columns = [d[0] for d in cursor.description]
    histories = defaultdict(list)
    for record in cursor.fetchall():
        row = dict(zip(columns, record))
        histories[row["msno"]].append(row)
    observed_until = con.execute("SELECT max(transaction_date) FROM all_tx").fetchone()[0]
    checks = []
    for name in ("train", "train_v2"):
        labels = con.execute(f"SELECT msno,is_churn FROM {name} ORDER BY md5(msno) LIMIT ?", [args.sample_size]).fetchall()
        for year, month in ((2017,1),(2017,2)):
            start = datetime(year, month, 1).date()
            cutoff = (start - timedelta(days=1)).strftime("%Y%m%d")
            end = start.replace(day=calendar.monthrange(year,month)[1])
            counts = defaultdict(int)
            for key, label in labels:
                status, actual = reconcile(histories[key], cutoff, start.strftime("%Y%m%d"), end.strftime("%Y%m%d"), observed_until)
                counts[status] += 1
                if status == "reconciled":
                    counts["label_matches" if actual == int(label) else "label_mismatches"] += 1
            checks.append({"label_release":name,"sample_size":len(labels),"cutoff":cutoff,"expiry_month":start.strftime("%Y-%m"),"history":"all available pre-cutoff transactions","counts":dict(counts)})
    results["sample_reconciliation"] = checks
    results["limits"] = "Deterministic MD5-ordered label sample; aggregate results only. Historical window deliberately uses all available history, unlike the source demo's January-only filter. Source conformance and full population reconciliation remain separate checks."
    output = args.output_dir / "transaction_audit.json"
    output.write_text(json.dumps(results, indent=2)+"\n", encoding="utf-8")
    print(json.dumps(results,indent=2), flush=True)
    con.close()


if __name__ == "__main__":
    main()
