import csv
import json
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path


ROOT=Path(__file__).resolve().parents[1]


class AuxiliaryAuditTests(unittest.TestCase):
    def test_archive_size_guard_and_complete_relational_audit(self):
        with tempfile.TemporaryDirectory() as directory:
            root=Path(directory)
            members=root/'members.csv'
            logs=root/'logs.csv'
            members.write_text('msno,city,bd,gender,registered_via,registration_init_time\na,1,0,,3,20160101\n',encoding='utf-8')
            with logs.open('w',newline='',encoding='utf-8') as stream:
                writer=csv.writer(stream)
                writer.writerow(['msno','date','num_25','num_50','num_75','num_985','num_100','num_unq','total_secs'])
                writer.writerows([['a','20170101',0,0,0,0,1,1,90],
                                  ['a','20170101',0,0,0,0,1,1,90],
                                  ['b','20170201',0,0,0,0,1,1,90000]])
            cmd=[sys.executable,str(ROOT/'src/audit_auxiliary.py'),'--members',str(members),
                 '--logs',str(logs),'--output-dir',str(root/'out'),'--expected-log-bytes']
            failed=subprocess.run(cmd+['1'],capture_output=True,text=True)
            self.assertEqual(failed.returncode,2)
            self.assertIn('finish extraction',failed.stderr)
            self.assertFalse((root/'out').exists())
            success=subprocess.run(cmd+[str(logs.stat().st_size)],capture_output=True,text=True)
            self.assertEqual(success.returncode,0,success.stderr)
            report=json.loads((root/'out/auxiliary_audit.json').read_text())
            self.assertEqual(report['logs']['row_count'],3)
            self.assertEqual(report['logs']['duplicate_customer_day_excess'],1)
            self.assertEqual(report['logs']['customers_without_member_record'],1)
            self.assertEqual(report['logs']['over_24h_listening_seconds'],1)


if __name__=='__main__':
    unittest.main()
