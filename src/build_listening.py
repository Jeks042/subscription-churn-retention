"""Finish milestone 2 from a reproducibly audited original listening database."""
import argparse
import hashlib
import json
import tempfile
from pathlib import Path

import duckdb

try:
    from build_sql import execute_sql, ROOT
    from feature_contract import prepare_model_features, MODEL_PREDICTORS
except ImportError:
    from src.build_sql import execute_sql, ROOT
    from src.feature_contract import prepare_model_features, MODEL_PREDICTORS


def rows(con,query):
    cur=con.execute(query)
    return [dict(zip([d[0] for d in cur.description],r)) for r in cur.fetchall()]


def build(con):
    con.execute('''CREATE OR REPLACE TABLE log_source_calendar AS
        SELECT DISTINCT CAST(strptime(date,'%Y%m%d') AS DATE) event_date FROM log_source''')
    dates=con.execute('SELECT scoring_date FROM scoring_calendar ORDER BY scoring_date').fetchall()
    for index,(scoring,) in enumerate(dates):
        print('Aggregating listening history for '+str(scoring),flush=True)
        con.execute('CREATE OR REPLACE TEMP TABLE scoring_context AS SELECT CAST(? AS DATE) scoring_date',[scoring])
        execute_sql(con,'005_listening_features.sql')
        if index==0:
            con.execute('CREATE OR REPLACE TABLE listening_features AS SELECT * FROM listening_snapshot')
        else:
            con.execute('INSERT INTO listening_features BY NAME SELECT * FROM listening_snapshot')
    print('Combining features and validating population/time boundaries',flush=True)
    execute_sql(con,'006_combine_features.sql')
    execute_sql(con,'007_feature_assertions.sql')
    print('Fitting training-only missing-value parameters',flush=True)
    prepare_model_features(con)


def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--database',type=Path,required=True)
    parser.add_argument('--log-database',type=Path,required=True)
    parser.add_argument('--audit-report',type=Path,required=True)
    parser.add_argument('--output-dir',type=Path,required=True)
    args=parser.parse_args()
    audit=json.loads(args.audit_report.read_text(encoding='utf-8'))
    if any(audit['logs'][key]!=0 for key in ('duplicate_customer_day_excess','invalid_dates','missing_keys')):
        raise ValueError('Listening source did not pass key/date checks')
    if audit['members']['duplicate_key_excess']!=0:
        raise ValueError('Member keys must be unique for diagnostic joins')
    if args.database.resolve()==args.log_database.resolve():
        raise ValueError('Analytical output must be separate from the audited source database')
    args.output_dir.mkdir(parents=True,exist_ok=True)
    output=args.output_dir/'listening_build_summary.json'
    if output.exists():
        output.unlink()
    print('Fingerprinting the audited source cache',flush=True)
    with args.log_database.open('rb') as stream:
        cache_hash=hashlib.file_digest(stream,'sha256').hexdigest()
    spill=tempfile.TemporaryDirectory(prefix='kkbox-listening-spill-')
    con=duckdb.connect(str(args.database))
    con.execute('SET temp_directory=?',[spill.name])
    con.execute("SET threads=4")
    con.execute("SET memory_limit='4GB'")
    con.execute('SET enable_progress_bar=false')
    escaped=str(args.log_database.resolve()).replace("'","''")
    con.execute("ATTACH '"+escaped+"' AS audited_logs (READ_ONLY)")
    con.execute('CREATE TEMP VIEW log_source AS SELECT msno,date,total_secs FROM audited_logs.logs')
    con.execute('CREATE TEMP VIEW member_source AS SELECT msno FROM audited_logs.members')
    if con.execute('SELECT count(*) FROM log_source').fetchone()[0]!=audit['logs']['row_count']:
        raise ValueError('Audit/cache row-count mismatch')
    con.execute('BEGIN TRANSACTION')
    try:
        build(con)
        report={'status':'milestone 2 full feature build passed; no model fitted',
                'source':audit['logs'],'audited_cache_sha256':cache_hash,
                'audit_report_sha256':hashlib.sha256(args.audit_report.read_bytes()).hexdigest(),
                'feature_rows':con.execute('SELECT count(*) FROM customer_features').fetchone()[0],
                'model_predictor_count':len(MODEL_PREDICTORS),'model_predictors':MODEL_PREDICTORS,
                'quality_by_scoring_date':rows(con,'SELECT * FROM feature_quality_summary ORDER BY scoring_date'),
                'renewal_by_engagement':rows(con,'SELECT * FROM renewal_by_engagement ORDER BY scoring_date,engagement_band'),
                'preprocessing':rows(con,'SELECT * FROM preprocessing_parameters')[0],
                'assertions':'passed',
                'sql_sha256':{p.name:hashlib.sha256(p.read_bytes()).hexdigest() for p in sorted((ROOT/'sql').glob('*.sql'))},
                'python_sha256':{p:hashlib.sha256((ROOT/'src'/p).read_bytes()).hexdigest() for p in ('build_listening.py','feature_contract.py')},
                'limits':'Retrospective event dates, not proven ingestion availability. Observed log days do not prove customer tenure or inactivity on absent days. Member presence is diagnostic only. Labels remain separate.'}
        print('Committing complete feature tables',flush=True)
        con.execute('COMMIT')
    except Exception:
        con.execute('ROLLBACK')
        raise
    finally:
        con.close()
        spill.cleanup()
    output.write_text(json.dumps(report,indent=2,default=str)+'\n',encoding='utf-8')
    print(json.dumps({'feature_rows':report['feature_rows'],'predictors':len(MODEL_PREDICTORS),
                      'assertions':report['assertions'],'summary':str(output)},indent=2),flush=True)


if __name__=='__main__':
    main()
