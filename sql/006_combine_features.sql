-- Both inputs already have one row per eligible customer/date.
CREATE OR REPLACE TABLE customer_features AS
SELECT t.*, l.* EXCLUDE(scoring_date,msno)
FROM transaction_features t JOIN listening_features l USING(scoring_date,msno);

-- Member presence is a retrospective quality diagnostic only, never a predictor.
CREATE OR REPLACE TABLE feature_quality_summary AS
SELECT f.scoring_date,count(*) eligible_rows,
    count(*) FILTER(WHERE no_listening_logs_90d=1) no_logs_90d,
    count(*) FILTER(WHERE listening_log_days_30d=0) no_logs_30d,
    count(*) FILTER(WHERE listening_negative_seconds_days_90d>0) customers_with_negative_seconds,
    count(*) FILTER(WHERE listening_over_24h_days_90d>0) customers_with_capped_seconds,
    count(*) FILTER(WHERE listening_missing_seconds_days_90d>0) customers_with_missing_seconds,
    count(*) FILTER(WHERE listening_bounded_seconds_90d IS NULL) missing_duration_total_90d,
    min(log_source_days_90d) min_source_calendar_days_90d,
    avg(listening_log_days_90d) mean_observed_log_days_90d,
    count(*) FILTER(WHERE m.msno IS NULL) without_member_record
FROM customer_features f LEFT JOIN member_source m USING(msno)
GROUP BY f.scoring_date ORDER BY f.scoring_date;

-- Outcomes join only for aggregate analysis, never as a feature dependency.
CREATE OR REPLACE TABLE renewal_by_engagement AS
SELECT f.scoring_date,
    CASE WHEN listening_log_days_30d=0 THEN '0 recorded days'
         WHEN listening_log_days_30d<=7 THEN '1-7 recorded days'
         WHEN listening_log_days_30d<=20 THEN '8-20 recorded days'
         ELSE '21-30 recorded days' END engagement_band,
    count(*) eligible_customers,
    count(*) FILTER(WHERE c.mature) mature_customers,
    count(*) FILTER(WHERE NOT c.mature) censored_customers,
    sum(c.is_churn) churn,
    sum(1-c.is_churn) renewed,
    avg(1-c.is_churn) renewal_rate
FROM customer_features f JOIN cohort_labels c USING(scoring_date,msno)
WHERE f.scoring_date IN (SELECT scoring_date FROM scoring_calendar WHERE split<>'holdout')
GROUP BY f.scoring_date,engagement_band ORDER BY f.scoring_date,engagement_band;
