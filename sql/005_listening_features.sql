-- Run once per scoring_context date. Source customer/date keys were audited unique.
-- No member attributes or outcomes enter this query.
CREATE OR REPLACE TEMP TABLE listening_snapshot AS
WITH eligible AS (
    SELECT scoring_date,msno FROM transaction_features
    WHERE scoring_date=(SELECT scoring_date FROM scoring_context)
), window_logs AS (
    SELECT msno, CAST(strptime(date,'%Y%m%d') AS DATE) event_date,
        try_cast(total_secs AS DOUBLE) duration_seconds,
        coalesce(isfinite(try_cast(total_secs AS DOUBLE)) AND try_cast(total_secs AS DOUBLE)>=0,false) usable_duration
    FROM log_source
    WHERE date>=strftime((SELECT scoring_date FROM scoring_context)-90,'%Y%m%d')
      AND date<strftime((SELECT scoring_date FROM scoring_context),'%Y%m%d')
)
SELECT e.scoring_date,e.msno,
    count(l.msno) FILTER(WHERE l.event_date >= e.scoring_date-7) listening_log_days_7d,
    CASE WHEN count(l.msno) FILTER(WHERE l.event_date >= e.scoring_date-7)=0 THEN 0.0
         ELSE sum(least(l.duration_seconds,86400.0)) FILTER(WHERE l.event_date >= e.scoring_date-7 AND l.usable_duration)
    END listening_bounded_seconds_7d,
    count(l.msno) FILTER(WHERE l.event_date >= e.scoring_date-7 AND l.usable_duration) listening_usable_duration_days_7d,
    count(l.msno) FILTER(WHERE l.event_date >= e.scoring_date-7 AND isfinite(l.duration_seconds) AND l.duration_seconds<0) listening_negative_seconds_days_7d,
    count(l.msno) FILTER(WHERE l.event_date >= e.scoring_date-7 AND isfinite(l.duration_seconds) AND l.duration_seconds>86400) listening_over_24h_days_7d,
    count(l.msno) FILTER(WHERE l.event_date >= e.scoring_date-7 AND (l.duration_seconds IS NULL OR NOT isfinite(l.duration_seconds))) listening_missing_seconds_days_7d,
    (SELECT count(*) FROM log_source_calendar d WHERE d.event_date>=e.scoring_date-7 AND d.event_date<e.scoring_date) log_source_days_7d,
    count(l.msno) FILTER(WHERE l.event_date >= e.scoring_date-30) listening_log_days_30d,
    CASE WHEN count(l.msno) FILTER(WHERE l.event_date >= e.scoring_date-30)=0 THEN 0.0
         ELSE sum(least(l.duration_seconds,86400.0)) FILTER(WHERE l.event_date >= e.scoring_date-30 AND l.usable_duration)
    END listening_bounded_seconds_30d,
    count(l.msno) FILTER(WHERE l.event_date >= e.scoring_date-30 AND l.usable_duration) listening_usable_duration_days_30d,
    count(l.msno) FILTER(WHERE l.event_date >= e.scoring_date-30 AND isfinite(l.duration_seconds) AND l.duration_seconds<0) listening_negative_seconds_days_30d,
    count(l.msno) FILTER(WHERE l.event_date >= e.scoring_date-30 AND isfinite(l.duration_seconds) AND l.duration_seconds>86400) listening_over_24h_days_30d,
    count(l.msno) FILTER(WHERE l.event_date >= e.scoring_date-30 AND (l.duration_seconds IS NULL OR NOT isfinite(l.duration_seconds))) listening_missing_seconds_days_30d,
    (SELECT count(*) FROM log_source_calendar d WHERE d.event_date>=e.scoring_date-30 AND d.event_date<e.scoring_date) log_source_days_30d,
    count(l.msno) FILTER(WHERE l.event_date >= e.scoring_date-90) listening_log_days_90d,
    CASE WHEN count(l.msno) FILTER(WHERE l.event_date >= e.scoring_date-90)=0 THEN 0.0
         ELSE sum(least(l.duration_seconds,86400.0)) FILTER(WHERE l.event_date >= e.scoring_date-90 AND l.usable_duration)
    END listening_bounded_seconds_90d,
    count(l.msno) FILTER(WHERE l.event_date >= e.scoring_date-90 AND l.usable_duration) listening_usable_duration_days_90d,
    count(l.msno) FILTER(WHERE l.event_date >= e.scoring_date-90 AND isfinite(l.duration_seconds) AND l.duration_seconds<0) listening_negative_seconds_days_90d,
    count(l.msno) FILTER(WHERE l.event_date >= e.scoring_date-90 AND isfinite(l.duration_seconds) AND l.duration_seconds>86400) listening_over_24h_days_90d,
    count(l.msno) FILTER(WHERE l.event_date >= e.scoring_date-90 AND (l.duration_seconds IS NULL OR NOT isfinite(l.duration_seconds))) listening_missing_seconds_days_90d,
    (SELECT count(*) FROM log_source_calendar d WHERE d.event_date>=e.scoring_date-90 AND d.event_date<e.scoring_date) log_source_days_90d,
    date_diff('day',max(l.event_date),e.scoring_date) listening_recency_90d,
    CAST(count(l.msno)=0 AS INTEGER) no_listening_logs_90d,
    max(l.event_date) max_listening_event_date
FROM eligible e LEFT JOIN window_logs l USING(msno)
GROUP BY e.scoring_date,e.msno;
