"""Build the local retrospective transaction foundation, with aggregate run evidence."""
import argparse
import hashlib
import json
import tempfile
from pathlib import Path

import duckdb

ROOT = Path(__file__).resolve().parents[1]
CALENDAR = [('2016-05-01','train'),('2016-06-01','train'),('2016-07-01','train'),
            ('2016-08-01','train'),('2016-10-01','selection'),
            ('2016-12-01','calibration'),('2017-02-01','holdout')]


def execute_sql(con, filename):
    con.execute((ROOT / 'sql' / filename).read_text(encoding='utf-8'))


def configure(con, calendar=None, observed_until='2017-03-31'):
    con.execute('CREATE OR REPLACE TABLE scoring_calendar(scoring_date DATE, split VARCHAR)')
    con.executemany('INSERT INTO scoring_calendar VALUES (?,?)', calendar or CALENDAR)
    con.execute('CREATE OR REPLACE TABLE run_config AS SELECT CAST(? AS DATE) observed_until',
                [observed_until])


def build(con):
    # A rebuilt upstream cohort invalidates every dependent feature/preprocessing table.
    for table in ('model_features','preprocessing_parameters','customer_features',
                  'listening_features','feature_quality_summary','renewal_by_engagement',
                  'log_source_calendar'):
        con.execute('DROP TABLE IF EXISTS '+table)
    for filename in ('001_stage_transactions.sql','002_cohorts.sql',
                     '003_transaction_features.sql','004_assertions.sql'):
        print('Running ' + filename, flush=True)
        execute_sql(con, filename)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--input-dir', type=Path, required=True)
    parser.add_argument('--output-dir', type=Path, required=True)
    args = parser.parse_args()
    args.output_dir.mkdir(parents=True, exist_ok=True)
    # A failed rerun must not leave a stale success report.
    summary_path = args.output_dir / 'sql_build_summary.json'
    for stale_report in (summary_path,args.output_dir/'listening_build_summary.json'):
        if stale_report.exists():
            stale_report.unlink()
    paths = {name: args.input_dir / filename for name, filename in
             [('raw_original','transactions.csv'),('raw_refresh','transactions_v2.csv')]}
    manifest = []
    for table, path in paths.items():
        with path.open('rb') as stream:
            checksum = hashlib.file_digest(stream,'sha256').hexdigest()
        manifest.append({'filename':path.name,'bytes':path.stat().st_size,'sha256':checksum})
    con = duckdb.connect(str(args.output_dir / 'analytics.duckdb'))
    spill = tempfile.TemporaryDirectory(prefix='kkbox-sql-spill-')
    con.execute('SET temp_directory = ?', [spill.name])
    con.execute("SET threads=4")
    con.execute("SET memory_limit='4GB'")
    con.execute('BEGIN TRANSACTION')
    try:
        for table,path in paths.items():
            con.execute(f'CREATE OR REPLACE TEMP TABLE {table} AS SELECT * FROM '
                        'read_csv(?, header=true, all_varchar=true)', [str(path)])
        configure(con)
        build(con)
        cur = con.execute('SELECT * FROM cohort_summary ORDER BY scoring_date')
        summaries = [dict(zip([d[0] for d in cur.description],row)) for row in cur.fetchall()]
        # Every earlier stage must finish maturing before the following stage scores.
        for before, after in [('train','selection'),('selection','calibration'),('calibration','holdout')]:
            maturity = max(r['latest_maturity'] for r in summaries if r['split']==before)
            next_score = min(r['scoring_date'] for r in summaries if r['split']==after)
            if maturity >= next_score:
                raise ValueError(f'Unmatured labels at transition {before} -> {after}')
        feature_rows = con.execute('SELECT count(*) FROM transaction_features').fetchone()[0]
        staged = con.execute('SELECT source_release,count(*) FROM stg_transactions GROUP BY 1 ORDER BY 1').fetchall()
        print('Committing validated tables',flush=True)
        con.execute('COMMIT')
        print('Commit complete',flush=True)
    except Exception:
        con.execute('ROLLBACK')
        raise
    finally:
        print('Closing database',flush=True)
        con.close()
        spill.cleanup()
        print('Database closed',flush=True)
    report = {'status':'transaction foundation built; not model approval',
              'source_policy':'original history + March-only refresh; exact duplicate analytical rows collapsed',
              'time_basis':'retrospective event dates; operational ingestion dates unavailable',
              'sources':manifest,'staged_rows':dict(staged),'feature_rows':feature_rows,
              'assertions':'passed','cohorts':summaries,
              'sql_sha256':{p.name:hashlib.sha256(p.read_bytes()).hexdigest()
                            for p in sorted((ROOT/'sql').glob('*.sql'))}}
    summary_path.write_text(json.dumps(report,indent=2,default=str)+'\n',encoding='utf-8')
    print(json.dumps(report,indent=2,default=str),flush=True)


if __name__=='__main__':
    main()
