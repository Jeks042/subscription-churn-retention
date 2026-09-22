import unittest
from datetime import date

import duckdb

from src.audit_cohorts import build_cohort


class CohortTests(unittest.TestCase):
    def test_boundaries_censoring_order_and_late_history(self):
        con = duckdb.connect()
        con.execute('''CREATE TABLE events(msno VARCHAR, transaction_date VARCHAR,
            membership_expire_date VARCHAR, is_cancel VARCHAR,
            plan_list_price VARCHAR, payment_plan_days VARCHAR, payment_method_id VARCHAR)''')
        def add(customer, day, expiry, cancel='0'):
            con.execute("INSERT INTO events VALUES (?,?,?,?, '149','30','1')",
                        [customer,day,expiry,cancel])
        for customer in ('early','ontime','boundary','cancel','absent','late_cancel'):
            add(customer,'20170120','20170208')
        add('early','20170131','20170207')
        add('ontime','20170309','20170409')  # 29 days, retained
        add('boundary','20170310','20170410')  # exactly 30, churn
        add('cancel','20170209','20170201','1')
        add('cancel','20170303','20170403')  # 30 since shortened expiry
        add('late_cancel','20170311','20170101','1')  # after maturity: ignored
        add('censored','20170131','20170228')
        add('same_day','20170131','20170315')
        add('same_day','20170131','20170215','1')
        add('future_only','20170202','20170220')
        stats = build_cohort(con,'SELECT * FROM events',date(2017,2,1),date(2017,3,20))
        rows = {r[0]:r[1:] for r in con.execute('SELECT msno,lead_eligible,mature,is_churn FROM cohort').fetchall()}
        self.assertNotIn('future_only', rows)
        self.assertEqual(rows['early'],(False,True,1))
        self.assertEqual(rows['ontime'],(True,True,0))
        self.assertEqual(rows['boundary'],(True,True,1))
        self.assertEqual(rows['cancel'],(True,True,1))
        self.assertEqual(rows['late_cancel'],(True,True,1))
        self.assertEqual(rows['censored'],(True,False,None))
        self.assertEqual(rows['same_day'],(True,True,1))
        self.assertEqual(stats['mature_eligible'],6)
        con.close()


if __name__ == '__main__':
    unittest.main()
