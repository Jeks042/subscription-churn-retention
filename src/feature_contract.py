"""Explicit predictor allowlist; keys, audit fields, members and labels stay out."""
TRANSACTION_FEATURES = [
    'days_to_expiry','transaction_recency_days','transaction_coverage_days_90',
    'transaction_count_7d','transaction_count_30d','transaction_count_90d',
    'cancellation_count_90d','subscription_count_90d','auto_renew_flag_count_90d',
    'subscription_recorded_amount_90d','expiry_before_event_count_90d',
]
LISTENING_FEATURES = [f'{stem}_{days}d' for days in (7,30,90) for stem in (
    'listening_log_days','listening_bounded_seconds','listening_usable_duration_days',
    'listening_negative_seconds_days','listening_over_24h_days','listening_missing_seconds_days')]
LISTENING_FEATURES += [f'log_source_days_{days}d' for days in (7,30,90)]
LISTENING_FEATURES += ['listening_recency_90d','no_listening_logs_90d']
RAW_PREDICTORS = TRANSACTION_FEATURES + LISTENING_FEATURES
IMPUTED_FEATURES = [f'listening_bounded_seconds_{days}d' for days in (7,30,90)] + ['listening_recency_90d']
MODEL_PREDICTORS = RAW_PREDICTORS + [f'{name}_missing' for name in IMPUTED_FEATURES]


def prepare_model_features(con):
    """Fit medians on training months only, preserving missingness indicators."""
    fits=[]
    for name in IMPUTED_FEATURES:
        fits.extend([f'coalesce(median(f.{name}),0) AS {name}_median',
                     f'count(f.{name}) AS {name}_observed_training_rows'])
    con.execute('''CREATE OR REPLACE TABLE preprocessing_parameters AS
        SELECT count(*) training_rows,max(f.scoring_date) latest_fit_scoring_date,'''+','.join(fits)+'''
        FROM customer_features f JOIN scoring_calendar c USING(scoring_date)
        WHERE c.split='train' ''')
    if con.execute('SELECT training_rows FROM preprocessing_parameters').fetchone()[0]==0:
        raise ValueError('Cannot fit preprocessing without training rows')
    selections=[]
    for name in RAW_PREDICTORS:
        value=f'coalesce(f.{name},p.{name}_median)' if name in IMPUTED_FEATURES else f'f.{name}'
        selections.append(f'CAST({value} AS DOUBLE) AS {name}')
    selections.extend(f'CAST(f.{name} IS NULL AS INTEGER) AS {name}_missing' for name in IMPUTED_FEATURES)
    con.execute('CREATE OR REPLACE TABLE model_features AS SELECT f.scoring_date,f.msno,'+
                ','.join(selections)+' FROM customer_features f CROSS JOIN preprocessing_parameters p')
    bad=' OR '.join(f'{name} IS NULL OR NOT isfinite({name})' for name in MODEL_PREDICTORS)
    if con.execute('SELECT count(*) FROM model_features WHERE '+bad).fetchone()[0]:
        raise ValueError('Null or nonfinite model predictor')
    actual=[r[0] for r in con.execute('DESCRIBE model_features').fetchall()]
    if set(actual)!=set(['scoring_date','msno']+MODEL_PREDICTORS):
        raise ValueError('Unexpected predictor or outcome leakage')
    if con.execute('SELECT count(*) FROM model_features').fetchone()[0]!=con.execute('SELECT count(*) FROM customer_features').fetchone()[0]:
        raise ValueError('Preprocessing changed the feature population')
