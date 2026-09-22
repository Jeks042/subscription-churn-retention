"""Reconstruct full-union labels without changing baseline features or models."""
import argparse
import json
import tempfile
from datetime import date
from pathlib import Path

import duckdb

from audit_cohorts import build_cohort


def main():
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument('--source-database', type=Path, required=True)
    p.add_argument('--output-dir', type=Path, required=True)
    args = p.parse_args()
    args.output_dir.mkdir(parents=True, exist_ok=True)
    con = duckdb.connect(str(args.output_dir/'source_sensitivity.duckdb'))
    with tempfile.TemporaryDirectory(prefix='kkbox-sensitivity-') as spill:
        con.execute('SET temp_directory=?', [spill])
        con.execute('SET threads=4')
        con.execute("SET memory_limit='3GB'")
        con.execute("ATTACH '"+str(args.source_database).replace("'", "''")+"' AS audited (READ_ONLY)")
        con.execute('CREATE OR REPLACE TABLE alternative_labels(scoring_date DATE, split VARCHAR, msno VARCHAR, is_churn INTEGER)')
        summaries = []
        for scoring, split in [(date(2016,10,1), 'selection'), (date(2016,12,1), 'calibration'), (date(2017,2,1), 'holdout')]:
            print('Reconstructing alternative source labels: '+str(scoring), flush=True)
            stats = build_cohort(con, 'SELECT * FROM audited.all_tx', scoring, date(2017,3,31))
            con.execute('INSERT INTO alternative_labels SELECT ?,?,msno,is_churn FROM cohort WHERE lead_eligible AND mature', [scoring, split])
            summaries.append({'scoring_date': str(scoring), 'split': split, **stats})
        if con.execute('SELECT count(*)-count(DISTINCT (scoring_date,msno)) FROM alternative_labels').fetchone()[0]:
            raise ValueError('Duplicate alternative labels')
        expected = json.loads((Path(__file__).resolve().parents[1]/'reports/source_version_sensitivity.json').read_text(encoding='utf-8'))
        for stats in summaries:
            previous = next(r for r in expected['cohorts'] if r['scoring_date'] == stats['scoring_date'] and r['source'] == 'all_releases_diagnostic')
            for key in ['mature_eligible', 'churn', 'non_churn']:
                if stats[key] != previous[key]:
                    raise ValueError('Alternative labels differ from earlier source audit')
        con.close()
    (args.output_dir/'source_sensitivity_build.json').write_text(json.dumps({'source': 'audited all_tx full release union', 'assertions': 'passed', 'cohorts': summaries}, indent=2)+'\n', encoding='utf-8')
    print('Alternative labels verified against prior source audit', flush=True)


if __name__ == '__main__':
    main()
