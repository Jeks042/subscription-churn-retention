import unittest

import duckdb

from src.build_sql import build, configure, execute_sql


class SqlBuildTests(unittest.TestCase):
    def setUp(self):
        self.con=duckdb.connect()
        schema='''(msno VARCHAR,payment_method_id VARCHAR,payment_plan_days VARCHAR,
            plan_list_price VARCHAR,actual_amount_paid VARCHAR,is_auto_renew VARCHAR,
            transaction_date VARCHAR,membership_expire_date VARCHAR,is_cancel VARCHAR)'''
        for name in ('raw_original','raw_refresh'):
            self.con.execute('CREATE TABLE '+name+schema)

    def tearDown(self):
        self.con.close()

    def add(self,customer,day,expiry='20170215',cancel='0',amount='100',table='raw_original'):
        self.con.execute(f'INSERT INTO {table} VALUES (?,?,?,?,?,?,?,?,?)',
                         [customer,'1','30','100',amount,'1',day,expiry,cancel])

    def test_deduplication_cutoffs_windows_and_future_invariance(self):
        for day in ('20161102','20161103','20170101','20170102','20170125','20170131'):
            self.add('a',day)
        self.add('a','20170131')  # Exact duplicate cannot inflate payments or counts.
        self.add('a','20170201','20170301',amount='999999')
        self.add('a','20170130',amount='888888',table='raw_refresh') # Correction excluded.
        self.add('future_only','20170201')
        configure(self.con,[('2017-02-01','test')])
        build(self.con)
        self.assertEqual(self.con.execute('SELECT count(*) FROM cohort_labels').fetchone()[0],1)
        actual=self.con.execute('''SELECT transaction_count_7d,transaction_count_30d,
            transaction_count_90d,subscription_recorded_amount_90d FROM transaction_features''').fetchone()
        self.assertEqual(actual,(2,3,5,500))
        before=self.con.execute('SELECT * FROM transaction_features').fetchall()
        self.con.execute('CREATE TABLE model_features AS SELECT * FROM transaction_features')
        self.con.execute("UPDATE raw_original SET actual_amount_paid='7',membership_expire_date='20300101' WHERE transaction_date>='20170201'")
        build(self.con)
        self.assertNotIn(('model_features',),self.con.execute('SHOW TABLES').fetchall())
        self.assertEqual(before,self.con.execute('SELECT * FROM transaction_features').fetchall())
        self.con.execute('INSERT INTO transaction_features SELECT * FROM transaction_features')
        with self.assertRaisesRegex(duckdb.Error,'Duplicate feature key'):
            execute_sql(self.con,'004_assertions.sql')

    def test_label_boundary_censoring_lead_time_and_cancellation(self):
        for customer in ('day29','day30','cancel','late','same_day'):
            self.add(customer,'20170131','20170208')
        self.add('too_soon','20170131','20170207')
        self.add('censored','20170131','20170228')
        self.add('day29','20170309','20170409',table='raw_refresh')
        self.add('day30','20170310','20170410',table='raw_refresh')
        self.add('cancel','20170209','20170201',cancel='1')
        self.add('cancel','20170303','20170403',table='raw_refresh')
        self.add('late','20170311','20170101',cancel='1',table='raw_refresh')
        # Same-day subscription is ordered before cancellation for the same plan.
        self.add('same_day','20170210','20170310')
        self.add('same_day','20170210','20170101',cancel='1')
        configure(self.con,[('2017-02-01','test')],observed_until='2017-03-20')
        build(self.con)
        rows=dict(self.con.execute('SELECT msno,is_churn FROM cohort_labels').fetchall())
        self.assertEqual(rows,{'day29':0,'day30':1,'cancel':1,'late':1,
                              'same_day':0,'too_soon':1,'censored':None})
        self.assertEqual(self.con.execute("SELECT count(*) FROM transaction_features WHERE msno='too_soon'").fetchone()[0],0)


if __name__=='__main__':
    unittest.main()
