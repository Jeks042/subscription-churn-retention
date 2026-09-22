"""Compare candidate source windows; do not infer validity from accuracy alone."""
import calendar
import json
from collections import defaultdict
from datetime import date, timedelta
from pathlib import Path
import duckdb
from audit_transactions import reconcile


def main():
    con=duckdb.connect("data/validation/validation.duckdb",read_only=True)
    output=[]
    for label_table in ("train","train_v2"):
        labels=con.execute(f"SELECT msno,is_churn FROM {label_table} ORDER BY md5(msno) LIMIT 2000").fetchall()
        for source in ("transactions","all_tx"):
            cursor=con.execute(f"SELECT t.* FROM {source} t JOIN (SELECT msno FROM {label_table} ORDER BY md5(msno) LIMIT 2000) l USING(msno)")
            columns=[d[0] for d in cursor.description]
            histories=defaultdict(list)
            for record in cursor.fetchall():
                row=dict(zip(columns,record)); histories[row["msno"]].append(row)
            last_observed=con.execute(f"SELECT max(transaction_date) FROM {source}").fetchone()[0]
            for month in (1,2,3):
                start=date(2017,month,1)
                cutoff=(start-timedelta(days=1)).strftime("%Y%m%d")
                previous_month=(start-timedelta(days=1)).replace(day=1).strftime("%Y%m%d")
                end=start.replace(day=calendar.monthrange(2017,month)[1]).strftime("%Y%m%d")
                for window in ("all_history","previous_month_only"):
                    counts=defaultdict(int)
                    for key,label in labels:
                        history=histories[key]
                        if window=="previous_month_only":
                            history=[r for r in history if r["transaction_date"]>=previous_month]
                        status,predicted=reconcile(history,cutoff,start.strftime("%Y%m%d"),end,last_observed)
                        counts[status]+=1
                        if status=="reconciled":
                            counts[f"supplied_{label}_reconstructed_{predicted}"]+=1
                    output.append({"labels":label_table,"source":source,"expiry_month":start.strftime("%Y-%m"),"history_window":window,"sample_size":len(labels),"counts":dict(counts)})
    Path("data/validation/window_diagnostics.json").write_text(json.dumps(output,indent=2)+"\n",encoding="utf-8")
    for record in output:
        if record["source"]=="all_tx" and record["history_window"]=="previous_month_only":
            print(json.dumps(record))


if __name__=="__main__":
    main()
