"""Aggregate historical cohort feasibility; no customer records leave the local DB."""
import argparse
import calendar
import json
import tempfile
from datetime import date, timedelta
from pathlib import Path

import duckdb


# Reverse of the supplied labeller's ordering, to choose the last known event.
LAST_ORDER = """transaction_date DESC,
    (plan_list_price || payment_plan_days || payment_method_id) ASC,
    is_cancel DESC,
    CASE WHEN is_cancel='1' THEN -CAST(membership_expire_date AS BIGINT)
         ELSE CAST(membership_expire_date AS BIGINT) END DESC"""


def build_cohort(con, source, scoring, observed_until, lead_days=7):
    """Materialize private candidate labels, bounded at each original expiry+30.

    Uses all pre-scoring history. This is a retrospective study definition,
    not a claim to reproduce supplied competition cohorts or availability times.
    Caller must supply a trusted internal SQL source expression.
    """
    end = scoring.replace(day=calendar.monthrange(scoring.year, scoring.month)[1])
    con.execute(f"""CREATE OR REPLACE TEMP TABLE candidates AS
        SELECT msno, CAST(strptime(membership_expire_date,'%Y%m%d') AS DATE) expiry
        FROM ({source})
        WHERE transaction_date < ?
        QUALIFY row_number() OVER(PARTITION BY msno ORDER BY {LAST_ORDER})=1""",
        [scoring.strftime('%Y%m%d')])
    con.execute("DELETE FROM candidates WHERE expiry < ? OR expiry > ?", [scoring, end])
    con.execute(f"""CREATE OR REPLACE TEMP TABLE future_events AS
        SELECT c.msno, CAST(strptime(t.transaction_date,'%Y%m%d') AS DATE) event_date,
          CAST(strptime(t.membership_expire_date,'%Y%m%d') AS DATE) event_expiry,
          t.is_cancel,
          row_number() OVER(PARTITION BY c.msno ORDER BY t.transaction_date ASC,
            (t.plan_list_price || t.payment_plan_days || t.payment_method_id) DESC,
            t.is_cancel ASC,
            CASE WHEN t.is_cancel='1' THEN -CAST(t.membership_expire_date AS BIGINT)
                 ELSE CAST(t.membership_expire_date AS BIGINT) END ASC) seq
        FROM ({source}) t JOIN candidates c USING(msno)
        WHERE t.transaction_date >= ?
          AND t.transaction_date <= strftime(least(c.expiry+30, CAST(? AS DATE)), '%Y%m%d')""",
        [scoring.strftime('%Y%m%d'), observed_until])
    con.execute("""CREATE OR REPLACE TEMP TABLE cohort AS
        WITH first_renewal AS (
          SELECT msno, min(seq) FILTER(WHERE is_cancel='0') renewal_seq
          FROM future_events GROUP BY msno
        ), outcomes AS (
          SELECT c.msno, c.expiry,
            min(f.event_date) FILTER(WHERE f.seq=r.renewal_seq) renewal_date,
            least(c.expiry, min(f.event_expiry) FILTER(
              WHERE f.is_cancel='1' AND (r.renewal_seq IS NULL OR f.seq<r.renewal_seq))) effective_expiry
          FROM candidates c LEFT JOIN first_renewal r USING(msno)
          LEFT JOIN future_events f USING(msno) GROUP BY c.msno,c.expiry
        )
        SELECT *, expiry >= CAST(? AS DATE)+CAST(? AS INTEGER) lead_eligible,
          expiry+30 <= CAST(? AS DATE) mature,
          CASE WHEN expiry+30 > CAST(? AS DATE) THEN NULL
               WHEN renewal_date IS NULL THEN 1
               ELSE CAST(renewal_date-effective_expiry >= 30 AS INTEGER) END is_churn
        FROM outcomes""", [scoring, lead_days, observed_until, observed_until])
    cur = con.execute("""SELECT count(*) candidates,
        count(*) FILTER(WHERE lead_eligible) lead_eligible,
        count(*) FILTER(WHERE lead_eligible AND mature) mature_eligible,
        count(*) FILTER(WHERE lead_eligible AND NOT mature) censored_eligible,
        count(*) FILTER(WHERE lead_eligible AND is_churn=1) churn,
        count(*) FILTER(WHERE lead_eligible AND is_churn=0) non_churn
        FROM cohort""")
    return dict(zip([d[0] for d in cur.description], cur.fetchone()))


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--database', type=Path, required=True)
    parser.add_argument('--output', type=Path, required=True)
    args = parser.parse_args()
    con = duckdb.connect(str(args.database), read_only=True)
    spill = tempfile.TemporaryDirectory(prefix='kkbox-cohort-spill-')
    con.execute('SET temp_directory = ?', [spill.name])
    con.execute("SET threads=4")
    con.execute("SET memory_limit='4GB'")
    sources = {
        'original_only': ('SELECT * FROM transactions', date(2017, 2, 28)),
        'original_plus_march': ("SELECT * FROM transactions UNION ALL SELECT * FROM transactions_v2 WHERE transaction_date >= '20170301'", date(2017, 3, 31)),
        'all_releases_diagnostic': ('SELECT * FROM all_tx', date(2017, 3, 31)),
    }
    results = []
    for year, month in [(2016,5),(2016,6),(2016,7),(2016,8),(2016,10),(2016,12),(2017,2)]:
        scoring = date(year, month, 1)
        for name, (source, observed) in sources.items():
            stats = build_cohort(con, source, scoring, observed)
            if name == 'original_only':
                con.execute('CREATE OR REPLACE TEMP TABLE reference_cohort AS SELECT * FROM cohort')
            else:
                cur = con.execute("""SELECT
                    count(*) FILTER(WHERE a.msno IS NULL) added_candidates,
                    count(*) FILTER(WHERE b.msno IS NULL) removed_candidates,
                    count(*) FILTER(WHERE a.expiry<>b.expiry) changed_expiry,
                    count(*) FILTER(WHERE a.lead_eligible IS DISTINCT FROM b.lead_eligible AND a.msno IS NOT NULL AND b.msno IS NOT NULL) changed_lead_eligibility,
                    count(*) FILTER(WHERE a.lead_eligible AND b.lead_eligible AND a.mature AND b.mature AND a.is_churn<>b.is_churn) changed_mature_labels
                    FROM reference_cohort a FULL OUTER JOIN cohort b USING(msno)""")
                stats['versus_original'] = dict(zip([d[0] for d in cur.description],cur.fetchone()))
            row = {'scoring_date':str(scoring),'source':name,**stats}
            results.append(row)
            print(json.dumps(row), flush=True)
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps({'lead_days':7,'history':'all pre-scoring events',
        'limits':'Retrospective event dates, not proven ingestion availability. Reconstructed outcomes, not supplied labels. Full follow-up required even for early renewals. No model fitting.',
        'cohorts':results},indent=2)+'\n', encoding='utf-8')
    con.close()
    spill.cleanup()


if __name__ == '__main__':
    main()
