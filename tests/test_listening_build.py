import unittest

import duckdb

from src.build_listening import build
from src.feature_contract import TRANSACTION_FEATURES, MODEL_PREDICTORS


class ListeningBuildTests(unittest.TestCase):
    def setUp(self):
        self.con=duckdb.connect()
        self.con.execute('CREATE TABLE scoring_calendar(scoring_date DATE,split VARCHAR)')
        self.con.execute("INSERT INTO scoring_calendar VALUES ('2016-05-01','train'),('2016-06-01','train'),('2016-10-01','holdout')")
        self.con.execute('CREATE TABLE transaction_features(scoring_date DATE,msno VARCHAR,'+
                         ','.join(name+' DOUBLE' for name in TRANSACTION_FEATURES)+',max_feature_event_date DATE)')
        for date in ('2016-05-01','2016-06-01','2016-10-01'):
            for customer in ('a','b','c'):
                self.con.execute('INSERT INTO transaction_features VALUES ('+','.join('?' for _ in range(len(TRANSACTION_FEATURES)+3))+')',
                                 [date,customer]+[1]*len(TRANSACTION_FEATURES)+['2016-01-01'])
        self.con.execute('CREATE TABLE cohort_labels AS SELECT scoring_date,msno,true mature,0 is_churn FROM transaction_features')
        self.con.execute('CREATE TABLE log_source(msno VARCHAR,date VARCHAR,total_secs VARCHAR)')
        self.con.executemany('INSERT INTO log_source VALUES (?,?,?)',[
            ('a','20160131','5000'),('a','20160201','10'),('a','20160401','100'),
            ('a','20160424','200'),('a','20160430','-5'),('a','20160501','999999'),
            ('b','20160425','-1'),('b','20160426','NaN'),('b','20160427',None),
            ('a','20160930','50'),('a','20161001','60')])
        self.con.execute('CREATE TABLE member_source(msno VARCHAR)')
        self.con.execute("INSERT INTO member_source VALUES ('a')")

    def tearDown(self):
        self.con.close()

    def test_boundaries_anomalies_missingness_and_population(self):
        build(self.con)
        values=self.con.execute("""SELECT listening_log_days_7d,listening_log_days_30d,
            listening_log_days_90d,listening_bounded_seconds_7d,listening_bounded_seconds_30d,
            listening_bounded_seconds_90d,listening_negative_seconds_days_90d
            FROM customer_features WHERE msno='a' AND scoring_date='2016-05-01'""").fetchone()
        self.assertEqual(values,(2,3,4,200,300,310,1))
        self.assertEqual(self.con.execute("SELECT listening_bounded_seconds_90d,listening_missing_seconds_days_90d FROM customer_features WHERE msno='b' AND scoring_date='2016-05-01'").fetchone(),(None,2))
        self.assertEqual(self.con.execute("SELECT listening_bounded_seconds_90d,listening_recency_90d,no_listening_logs_90d FROM customer_features WHERE msno='c' AND scoring_date='2016-05-01'").fetchone(),(0,None,1))
        june=self.con.execute("SELECT listening_bounded_seconds_30d,listening_over_24h_days_30d FROM customer_features WHERE msno='a' AND scoring_date='2016-06-01'").fetchone()
        self.assertEqual(june,(0,0))  # May 1 is 31 days before June 1, outside 30d.
        self.assertEqual(self.con.execute("SELECT listening_bounded_seconds_90d,listening_over_24h_days_90d FROM customer_features WHERE msno='a' AND scoring_date='2016-06-01'").fetchone(),(86700,1))
        self.assertEqual(self.con.execute('SELECT count(*) FROM model_features').fetchone()[0],9)
        self.assertEqual(self.con.execute('SELECT training_rows FROM preprocessing_parameters').fetchone()[0],6)
        self.assertEqual(self.con.execute('SELECT listening_recency_90d_median,listening_bounded_seconds_90d_median FROM preprocessing_parameters').fetchone(),(17.5,155.0))
        self.assertEqual(self.con.execute('SELECT sum(eligible_customers) FROM renewal_by_engagement').fetchone()[0],6)
        self.assertEqual(self.con.execute("SELECT count(*) FROM renewal_by_engagement WHERE scoring_date='2016-10-01'").fetchone()[0],0)
        self.assertEqual(self.con.execute('SELECT sum(without_member_record) FROM feature_quality_summary').fetchone()[0],6)
        self.assertEqual(len(self.con.execute('DESCRIBE model_features').fetchall()),len(MODEL_PREDICTORS)+2)

    def test_future_invariance_and_training_only_fit(self):
        build(self.con)
        parameters=self.con.execute('SELECT * FROM preprocessing_parameters').fetchall()
        before=self.con.execute('SELECT * FROM customer_features ORDER BY scoring_date,msno').fetchall()
        self.con.execute("UPDATE log_source SET total_secs='777777' WHERE date='20161001'")
        build(self.con)
        self.assertEqual(before,self.con.execute('SELECT * FROM customer_features ORDER BY scoring_date,msno').fetchall())
        self.con.execute("UPDATE log_source SET total_secs='500' WHERE date='20160930'")
        build(self.con)
        self.assertEqual(parameters,self.con.execute('SELECT * FROM preprocessing_parameters').fetchall())
        changed=self.con.execute("SELECT listening_bounded_seconds_7d FROM customer_features WHERE scoring_date='2016-10-01' AND msno='a'").fetchone()[0]
        self.assertEqual(changed,500)


if __name__=='__main__':
    unittest.main()
