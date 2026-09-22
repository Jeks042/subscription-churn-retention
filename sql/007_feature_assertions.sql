SELECT CASE WHEN count(*)>0 THEN error('Duplicate listening feature key') END
FROM (SELECT scoring_date,msno FROM listening_features GROUP BY ALL HAVING count(*)<>1);
SELECT CASE WHEN count(*)>0 THEN error('Duplicate combined feature key') END
FROM (SELECT scoring_date,msno FROM customer_features GROUP BY ALL HAVING count(*)<>1);
SELECT CASE WHEN count(*)<>(SELECT count(*) FROM transaction_features)
    THEN error('Combined join changed population') END FROM customer_features;
SELECT CASE WHEN count(*)>0 THEN error('Eligible key lost in combined join') END
FROM transaction_features t WHERE NOT EXISTS (
    SELECT 1 FROM customer_features f WHERE f.scoring_date=t.scoring_date AND f.msno=t.msno);
SELECT CASE WHEN count(*)>0 THEN error('Listening date leakage') END
FROM customer_features WHERE max_listening_event_date>=scoring_date;
SELECT CASE WHEN count(*)>0 THEN error('Listening window count error') END
FROM customer_features WHERE listening_log_days_7d>7 OR listening_log_days_30d>30
 OR listening_log_days_90d>90 OR listening_log_days_7d>listening_log_days_30d
 OR listening_log_days_30d>listening_log_days_90d
 OR listening_log_days_90d>log_source_days_90d;
SELECT CASE WHEN count(*)>0 THEN error('Duration bounds error') END
FROM customer_features WHERE listening_bounded_seconds_7d<0
 OR listening_bounded_seconds_30d<0 OR listening_bounded_seconds_90d<0
 OR listening_bounded_seconds_7d>86400*listening_usable_duration_days_7d
 OR listening_bounded_seconds_30d>86400*listening_usable_duration_days_30d
 OR listening_bounded_seconds_90d>86400*listening_usable_duration_days_90d;
SELECT CASE WHEN count(*)>0 THEN error('Outcome column found in combined features') END
FROM information_schema.columns WHERE table_name='customer_features'
 AND column_name IN ('is_churn','first_renewal_date','effective_expiry','mature','maturity_date','split');
SELECT CASE WHEN sum(eligible_customers)<>(SELECT count(*) FROM customer_features
    WHERE scoring_date IN (SELECT scoring_date FROM scoring_calendar WHERE split<>'holdout'))
    THEN error('Engagement summary denominator mismatch') END FROM renewal_by_engagement;
SELECT CASE WHEN count(*)>0 THEN error('Holdout outcomes exposed in engagement analysis') END
FROM renewal_by_engagement r JOIN scoring_calendar c USING(scoring_date) WHERE c.split='holdout';
