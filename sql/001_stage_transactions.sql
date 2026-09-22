-- Fixed retrospective release policy: original history plus March-only v2.
-- Pre-March v2 corrections are reserved for a separate sensitivity analysis.
-- Keep source rows unchanged; collapse only identical nine-field analytical rows.
CREATE OR REPLACE TABLE stg_transactions AS
WITH original AS (SELECT DISTINCT * FROM raw_original),
march AS (SELECT DISTINCT * FROM raw_refresh WHERE transaction_date >= '20170301'
                                               AND transaction_date <= '20170331'),
combined AS (
    SELECT *, 'original' source_release FROM original
    UNION ALL SELECT *, 'refresh_march' source_release FROM march
)
SELECT *, CAST(strptime(transaction_date, '%Y%m%d') AS DATE) event_date,
    CAST(strptime(membership_expire_date, '%Y%m%d') AS DATE) expiry_date,
    CAST(actual_amount_paid AS BIGINT) recorded_amount,
    plan_list_price || payment_plan_days || payment_method_id plan_signature
FROM combined;

-- Read-time validation must fail on unknown flags, missing keys and source overlap.
SELECT CASE WHEN count(*) > 0 THEN error('Invalid transaction staging input') END
FROM stg_transactions
WHERE msno IS NULL OR msno='' OR event_date IS NULL OR expiry_date IS NULL
   OR is_cancel IS NULL OR is_cancel NOT IN ('0','1')
   OR is_auto_renew IS NULL OR is_auto_renew NOT IN ('0','1')
   OR recorded_amount IS NULL OR plan_signature IS NULL
   OR (source_release='original' AND event_date > DATE '2017-02-28');
