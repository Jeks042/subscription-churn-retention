"""Compare SQL labels with the separate Python reconstruction on a local sample."""
import argparse
import calendar
import json
from collections import defaultdict
from datetime import timedelta
from pathlib import Path

import duckdb

from audit_transactions import reconcile


def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--database',type=Path,required=True)
    parser.add_argument('--output',type=Path,required=True)
    args=parser.parse_args()
    con=duckdb.connect(str(args.database),read_only=True)
    con.execute('''CREATE TEMP TABLE sample AS SELECT * FROM cohort_labels
        WHERE lead_eligible QUALIFY row_number() OVER(
        PARTITION BY scoring_date ORDER BY md5(msno))<=1000''')
    sample=con.execute('SELECT scoring_date,msno,is_churn FROM sample').fetchall()
    cur=con.execute('''SELECT t.* FROM stg_transactions t
        WHERE msno IN (SELECT msno FROM sample)''')
    columns=[d[0] for d in cur.description]
    histories=defaultdict(list)
    for row in cur.fetchall():
        record=dict(zip(columns,row))
        histories[record['msno']].append(record)
    observed=con.execute('SELECT observed_until FROM run_config').fetchone()[0].strftime('%Y%m%d')
    per_date=defaultdict(lambda:{'checked':0,'disagreements':0})
    for scoring,key,label in sample:
        end=scoring.replace(day=calendar.monthrange(scoring.year,scoring.month)[1])
        status,predicted=reconcile(histories[key],(scoring-timedelta(days=1)).strftime('%Y%m%d'),
                                   scoring.strftime('%Y%m%d'),end.strftime('%Y%m%d'),observed)
        stats=per_date[str(scoring)]
        stats['checked']+=1
        if (status!='reconciled' and label is not None) or predicted!=label:
            stats['disagreements']+=1
    result={'comparison':'SQL vs independent Python; not supplied-label agreement',
            'sample_per_date':1000,'dates':dict(per_date),
            'checked':len(sample),'disagreements':sum(r['disagreements'] for r in per_date.values())}
    args.output.parent.mkdir(parents=True,exist_ok=True)
    args.output.write_text(json.dumps(result,indent=2)+'\n',encoding='utf-8')
    print(json.dumps(result,indent=2))
    if result['disagreements']:
        raise ValueError('SQL and Python reconstructions disagree')
    con.close()


if __name__=='__main__':
    main()
