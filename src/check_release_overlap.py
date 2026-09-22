"""Diagnose transaction-release overlap before combining histories."""
import json
from pathlib import Path
import duckdb


def main():
    con = duckdb.connect("data/validation/validation.duckdb", read_only=True)
    result = {}
    result["v2_pre_march_rows"] = con.execute("SELECT count(*) FROM transactions_v2 WHERE transaction_date < '20170301'").fetchone()[0]
    result["exact_rows_present_in_both_releases"] = con.execute("SELECT count(*) FROM (SELECT * FROM transactions INTERSECT SELECT * FROM transactions_v2)").fetchone()[0]
    result["v2_pre_march_not_in_original"] = con.execute("SELECT count(*) FROM (SELECT * FROM transactions_v2 WHERE transaction_date < '20170301' EXCEPT SELECT * FROM transactions)").fetchone()[0]
    result["v2_pre_march_matching_original_except_expiry"] = con.execute("""SELECT count(*) FROM transactions_v2 v
        WHERE v.transaction_date < '20170301' AND EXISTS (SELECT 1 FROM transactions o
        WHERE o.msno=v.msno AND o.payment_method_id=v.payment_method_id
        AND o.payment_plan_days=v.payment_plan_days AND o.plan_list_price=v.plan_list_price
        AND o.actual_amount_paid=v.actual_amount_paid AND o.is_auto_renew=v.is_auto_renew
        AND o.transaction_date=v.transaction_date AND o.is_cancel=v.is_cancel)""").fetchone()[0]
    result["expiry_before_transaction_by_cancel"] = con.execute("SELECT is_cancel,count(*) FROM all_tx WHERE membership_expire_date < transaction_date GROUP BY 1 ORDER BY 1").fetchall()
    Path("data/validation/release_overlap.json").write_text(json.dumps(result,indent=2)+"\n",encoding="utf-8")
    print(json.dumps(result,indent=2))


if __name__ == "__main__":
    main()
