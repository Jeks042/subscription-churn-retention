import unittest
from src.audit_transactions import reconcile, order_key


def event(day, expiry, cancel="0"):
    return {"transaction_date":day,"membership_expire_date":expiry,
            "is_cancel":cancel,"plan_list_price":"149","payment_plan_days":"30","payment_method_id":"1"}


class ReconciliationTests(unittest.TestCase):
    def result(self, history, observed="20170331"):
        return reconcile(history,"20170131","20170201","20170228",observed)

    def test_thirty_day_boundary(self):
        base = event("20170101","20170201")
        self.assertEqual(self.result([base,event("20170302","20170401")]),("reconciled",0))
        self.assertEqual(self.result([base,event("20170303","20170401")]),("reconciled",1))

    def test_cancellation_moves_expiry_before_first_renewal(self):
        history = [event("20170101","20170228"),event("20170203","20170203","1"),event("20170305","20170405")]
        self.assertEqual(self.result(history), ("reconciled",1))

    def test_censoring_and_no_history(self):
        self.assertEqual(self.result([event("20170101","20170228")],"20170301"),("censored",None))
        self.assertEqual(self.result([]),("no_history",None))

    def test_same_day_subscription_before_cancellation(self):
        renew=event("20170131","20170301")
        cancel=event("20170131","20170215","1")
        self.assertEqual(sorted([cancel,renew],key=order_key),[renew,cancel])
        self.assertEqual(self.result([cancel,renew]),("reconciled",1))

    def test_repeated_renewals_extend_and_cancellations_shorten(self):
        renewals=[event("20170131","20170210"),event("20170131","20170220")]
        cancels=[event("20170131","20170210","1"),event("20170131","20170220","1")]
        self.assertEqual(sorted(renewals,key=order_key)[-1]["membership_expire_date"],"20170220")
        self.assertEqual(sorted(cancels,key=order_key)[-1]["membership_expire_date"],"20170210")


if __name__ == "__main__":
    unittest.main()
