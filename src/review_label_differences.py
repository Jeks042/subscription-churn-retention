"""Aggregate label differences without exporting identifiers or customer histories."""
import argparse
import json
from collections import Counter, defaultdict
from pathlib import Path

import duckdb

from audit_transactions import reconcile


def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--database',type=Path,required=True)
    parser.add_argument('--output',type=Path,required=True)
    args=parser.parse_args()
    con=duckdb.connect(str(args.database),read_only=True)
    con.execute('CREATE TEMP TABLE ids AS SELECT msno,is_churn FROM train ORDER BY md5(msno) LIMIT 2000')
    labels=dict(con.execute('SELECT * FROM ids').fetchall())
    cursor=con.execute('''SELECT t.*, 'original' source_release FROM transactions t JOIN ids USING(msno)
        UNION ALL SELECT t.*, 'refresh' source_release FROM transactions_v2 t JOIN ids USING(msno)''')
    columns=[d[0] for d in cursor.description]
    histories=defaultdict(list)
    for row in cursor.fetchall():
        record=dict(zip(columns,row))
        histories[record['msno']].append(record)
    counts=Counter()
    changes=Counter()
    for key,label in labels.items():
        all_rows=histories[key]
        baseline=[r for r in all_rows if r['source_release']=='original' or r['transaction_date']>='20170301']
        params=('20170131','20170201','20170228','20170331')
        status,predicted=reconcile(baseline,*params)
        union_status,union_predicted=reconcile(all_rows,*params)
        month_status,month_predicted=reconcile([r for r in baseline if r['transaction_date']>='20170101'],*params)
        counts[status]+=1
        if status=='reconciled':
            counts['supplied_match' if predicted==int(label) else 'supplied_mismatch']+=1
            counts[f'supplied_{label}_baseline_{predicted}']+=1
            if predicted!=int(label):
                if union_status=='reconciled' and union_predicted==int(label):
                    changes['mismatch_matches_after_including_backdated_refresh']+=1
                elif month_status=='reconciled' and month_predicted==int(label):
                    changes['mismatch_matches_with_january_only_history']+=1
                else:
                    changes['mismatch_not_explained_by_these_two_changes']+=1
        if (status,predicted)!=(union_status,union_predicted):
            changes['union_changes_status_or_label']+=1
        if (status,predicted)!=(month_status,month_predicted):
            changes['january_filter_changes_status_or_label']+=1
    report={'sample_size':len(labels),'sample':'original labels ordered by MD5 identifier',
            'expiry_month':'2017-02','baseline':'original + March-only refresh; all pre-scoring history',
            'counts':dict(counts),'sensitivity':dict(changes),
            'conclusion':'These comparisons diagnose disagreement, not definitive causes. Supplied labels are not ground truth for the separately defined historical cohorts.'}
    args.output.parent.mkdir(parents=True,exist_ok=True)
    args.output.write_text(json.dumps(report,indent=2)+'\n',encoding='utf-8')
    print(json.dumps(report,indent=2))
    con.close()


if __name__=='__main__':
    main()
