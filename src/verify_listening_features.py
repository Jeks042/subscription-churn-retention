"""Independently recompute sampled listening features from audited daily records."""
import argparse
import json
import math
from collections import defaultdict
from datetime import datetime, timedelta
from functools import lru_cache
from pathlib import Path

import duckdb

try:
    from feature_contract import IMPUTED_FEATURES, RAW_PREDICTORS
except ImportError:
    from src.feature_contract import IMPUTED_FEATURES, RAW_PREDICTORS


@lru_cache(maxsize=2048)
def day(text):
    return datetime.strptime(text,'%Y%m%d').date()


def expected_features(history,scoring,calendar):
    result={}
    scoped=[(d,v) for d,v in history if scoring-timedelta(days=90)<=d<scoring]
    for days in (7,30,90):
        window=[(d,v) for d,v in scoped if d>=scoring-timedelta(days=days)]
        usable=[v for _,v in window if v is not None and math.isfinite(v) and v>=0]
        result[f'listening_log_days_{days}d']=len(window)
        result[f'listening_bounded_seconds_{days}d']=(math.fsum(min(v,86400) for v in usable)
            if usable else (0 if not window else None))
        result[f'listening_usable_duration_days_{days}d']=len(usable)
        result[f'listening_negative_seconds_days_{days}d']=sum(v is not None and math.isfinite(v) and v<0 for _,v in window)
        result[f'listening_over_24h_days_{days}d']=sum(v is not None and math.isfinite(v) and v>86400 for _,v in window)
        result[f'listening_missing_seconds_days_{days}d']=sum(v is None or not math.isfinite(v) for _,v in window)
        result[f'log_source_days_{days}d']=sum(scoring-timedelta(days=days)<=d<scoring for d in calendar)
    result['listening_recency_90d']=(scoring-max(d for d,_ in scoped)).days if scoped else None
    result['no_listening_logs_90d']=int(not scoped)
    return result


def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--database',type=Path,required=True)
    parser.add_argument('--log-database',type=Path,required=True)
    parser.add_argument('--output',type=Path,required=True)
    args=parser.parse_args()
    con=duckdb.connect(str(args.database),read_only=True)
    con.execute('SET threads=4')
    con.execute('SET enable_progress_bar=false')
    escaped=str(args.log_database.resolve()).replace("'","''")
    con.execute("ATTACH '"+escaped+"' AS audited_logs (READ_ONLY)")
    con.execute('''CREATE TEMP TABLE sample AS SELECT * FROM customer_features
        QUALIFY row_number() OVER(PARTITION BY scoring_date ORDER BY md5(msno||CAST(scoring_date AS VARCHAR)))<=100''')
    cur=con.execute('SELECT * FROM sample')
    snapshots=[dict(zip([d[0] for d in cur.description],r)) for r in cur.fetchall()]
    history=defaultdict(list)
    for customer,date,seconds in con.execute('''SELECT msno,date,total_secs FROM audited_logs.logs
        WHERE msno IN (SELECT msno FROM sample)''').fetchall():
        try:
            value=float(seconds)
        except (TypeError,ValueError):
            value=None
        history[customer].append((day(date),value))
    calendar={day(r[0]) for r in con.execute('SELECT DISTINCT date FROM audited_logs.logs').fetchall()}
    errors=defaultdict(int)
    checked=0
    for snapshot in snapshots:
        expected=expected_features(history[snapshot['msno']],snapshot['scoring_date'],calendar)
        for name,value in expected.items():
            actual=snapshot[name]
            checked+=1
            match=(value is None and actual is None) or (value is not None and actual is not None
                and math.isclose(value,actual,rel_tol=1e-10,abs_tol=1e-4))
            if not match:
                errors[name]+=1
    missing_sql=','.join(f'count(*) FILTER(WHERE {name} IS NULL) AS {name}_missing' for name in IMPUTED_FEATURES)
    cur=con.execute('SELECT scoring_date,count(*) feature_rows,'+missing_sql+
                    ' FROM customer_features GROUP BY scoring_date ORDER BY scoring_date')
    missingness=[dict(zip([d[0] for d in cur.description],r)) for r in cur.fetchall()]
    other_nulls=' OR '.join(name+' IS NULL' for name in RAW_PREDICTORS if name not in IMPUTED_FEATURES)
    other_missing=con.execute('SELECT count(*) FROM customer_features WHERE '+other_nulls).fetchone()[0]
    report={'sample_rows':len(snapshots),'sample_per_scoring_date':100,
            'feature_values_checked':checked,'mismatches_by_feature':dict(errors),
            'raw_missingness_by_date':missingness,'rows_with_other_missing_predictors':other_missing,
            'comparison':'Independent Python aggregation vs SQL; not validation of operational availability'}
    args.output.parent.mkdir(parents=True,exist_ok=True)
    args.output.write_text(json.dumps(report,indent=2,default=str)+'\n',encoding='utf-8')
    con.close()
    print(json.dumps(report,indent=2,default=str))
    if errors or other_missing:
        raise ValueError('Listening feature reconstruction mismatch')


if __name__=='__main__':
    main()
