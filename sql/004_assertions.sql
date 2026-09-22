SELECT CASE WHEN count(*)>0 THEN error('Duplicate cohort key') END
FROM (SELECT scoring_date,msno FROM cohort_labels GROUP BY ALL HAVING count(*)<>1);
SELECT CASE WHEN count(*)>0 THEN error('Duplicate feature key') END
FROM (SELECT scoring_date,msno FROM transaction_features GROUP BY ALL HAVING count(*)<>1);
SELECT CASE WHEN count(*)<>(SELECT count(*) FROM cohort_candidates WHERE lead_eligible)
    THEN error('Feature join changed eligible population') END FROM transaction_features;
SELECT CASE WHEN count(*)>0 THEN error('Missing eligible feature row') END
FROM cohort_candidates c WHERE lead_eligible AND NOT EXISTS (
    SELECT 1 FROM transaction_features f WHERE f.scoring_date=c.scoring_date AND f.msno=c.msno);
SELECT CASE WHEN count(*)>0 THEN error('Feature date leakage or insufficient lead time') END
FROM transaction_features WHERE max_feature_event_date>=scoring_date OR days_to_expiry<7;
SELECT CASE WHEN count(*)>0 THEN error('Invalid label/censoring state') END
FROM cohort_labels WHERE (NOT mature AND is_churn IS NOT NULL)
    OR (mature AND (is_churn IS NULL OR is_churn NOT IN (0,1)));
SELECT CASE WHEN count(*)>0 THEN error('Outcome column found in features') END
FROM information_schema.columns WHERE table_name='transaction_features'
    AND column_name IN ('is_churn','first_renewal_date','effective_expiry','mature','maturity_date');
