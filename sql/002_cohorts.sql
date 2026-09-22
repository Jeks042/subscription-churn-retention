-- One row per customer/scoring date; all eligibility uses events strictly before T.
CREATE OR REPLACE TABLE cohort_candidates AS
WITH latest AS (
    SELECT s.scoring_date, s.split, t.msno, t.expiry_date expiry,
           t.event_date latest_history_date
    FROM scoring_calendar s JOIN stg_transactions t ON t.event_date < s.scoring_date
    QUALIFY row_number() OVER (
        PARTITION BY s.scoring_date, t.msno
        ORDER BY t.event_date DESC, t.plan_signature ASC, t.is_cancel DESC,
          CASE WHEN t.is_cancel='1' THEN -CAST(t.membership_expire_date AS BIGINT)
               ELSE CAST(t.membership_expire_date AS BIGINT) END DESC
    )=1
)
SELECT *, expiry >= scoring_date + 7 lead_eligible,
    expiry + 30 maturity_date,
    expiry + 30 <= (SELECT observed_until FROM run_config) mature
FROM latest WHERE expiry BETWEEN scoring_date AND last_day(scoring_date);

CREATE OR REPLACE TEMP TABLE ordered_outcome_events AS
SELECT c.scoring_date, c.msno, t.event_date, t.expiry_date, t.is_cancel,
    row_number() OVER (
        PARTITION BY c.scoring_date, c.msno
        ORDER BY t.event_date ASC, t.plan_signature DESC, t.is_cancel ASC,
          CASE WHEN t.is_cancel='1' THEN -CAST(t.membership_expire_date AS BIGINT)
               ELSE CAST(t.membership_expire_date AS BIGINT) END ASC
    ) seq
FROM cohort_candidates c JOIN stg_transactions t USING(msno)
WHERE t.event_date >= c.scoring_date
  AND t.event_date <= least(c.maturity_date, (SELECT observed_until FROM run_config));

-- Labels are kept separate from the feature table. Full follow-up is required
-- even if a renewal arrives early; censored rows retain a NULL label.
CREATE OR REPLACE TABLE cohort_labels AS
WITH first_renewal AS (
    SELECT scoring_date, msno, min(seq) FILTER(WHERE is_cancel='0') renewal_seq
    FROM ordered_outcome_events GROUP BY ALL
), outcomes AS (
    SELECT c.scoring_date, c.msno,
        min(e.event_date) FILTER(WHERE e.seq=r.renewal_seq) first_renewal_date,
        least(c.expiry, min(e.expiry_date) FILTER(
            WHERE e.is_cancel='1' AND (r.renewal_seq IS NULL OR e.seq<r.renewal_seq))) effective_expiry
    FROM cohort_candidates c
    LEFT JOIN first_renewal r USING(scoring_date,msno)
    LEFT JOIN ordered_outcome_events e USING(scoring_date,msno)
    GROUP BY c.scoring_date,c.msno,c.expiry
)
SELECT c.*, o.first_renewal_date, o.effective_expiry,
    CASE WHEN NOT c.mature THEN NULL
         WHEN o.first_renewal_date IS NULL THEN 1
         ELSE CAST(o.first_renewal_date-o.effective_expiry >= 30 AS INTEGER)
    END is_churn
FROM cohort_candidates c JOIN outcomes o USING(scoring_date,msno);
