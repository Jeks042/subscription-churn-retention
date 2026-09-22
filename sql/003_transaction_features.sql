-- Aggregate first, then join: event-level tables never join directly to each other.
-- Feature windows are [T-N, T); outcome eligibility is not a predictor.
CREATE OR REPLACE TABLE transaction_features AS
SELECT c.scoring_date, c.msno,
    c.expiry-c.scoring_date days_to_expiry,
    c.scoring_date-c.latest_history_date transaction_recency_days,
    least(90, c.scoring_date-(SELECT min(event_date) FROM stg_transactions
                            WHERE source_release='original')) transaction_coverage_days_90,
    count(t.msno) FILTER(WHERE t.event_date>=c.scoring_date-7) transaction_count_7d,
    count(t.msno) FILTER(WHERE t.event_date>=c.scoring_date-30) transaction_count_30d,
    count(t.msno) transaction_count_90d,
    count(t.msno) FILTER(WHERE t.is_cancel='1') cancellation_count_90d,
    count(t.msno) FILTER(WHERE t.is_cancel='0') subscription_count_90d,
    count(t.msno) FILTER(WHERE t.is_auto_renew='1') auto_renew_flag_count_90d,
    coalesce(sum(t.recorded_amount) FILTER(WHERE t.is_cancel='0'),0) subscription_recorded_amount_90d,
    count(t.msno) FILTER(WHERE t.expiry_date<t.event_date) expiry_before_event_count_90d,
    max(t.event_date) max_feature_event_date
FROM cohort_candidates c LEFT JOIN stg_transactions t
    ON t.msno=c.msno AND t.event_date>=c.scoring_date-90 AND t.event_date<c.scoring_date
WHERE c.lead_eligible
GROUP BY c.scoring_date,c.msno,c.expiry,c.latest_history_date;

CREATE OR REPLACE TABLE cohort_summary AS
SELECT scoring_date, split, count(*) candidates,
    count(*) FILTER(WHERE lead_eligible) lead_eligible,
    count(*) FILTER(WHERE lead_eligible AND mature) mature_eligible,
    count(*) FILTER(WHERE lead_eligible AND NOT mature) censored_eligible,
    count(*) FILTER(WHERE lead_eligible AND is_churn=1) churn,
    count(*) FILTER(WHERE lead_eligible AND is_churn=0) renewed,
    avg(is_churn) FILTER(WHERE lead_eligible AND mature) churn_rate,
    1-avg(is_churn) FILTER(WHERE lead_eligible AND mature) renewal_rate,
    max(maturity_date) latest_maturity
FROM cohort_labels GROUP BY scoring_date,split ORDER BY scoring_date;
