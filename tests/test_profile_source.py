"""Synthetic boundary checks; no KKBox source data is used."""
import gzip
import hashlib
import tempfile
import unittest
from pathlib import Path
from src.profile_source import profile_file


class ProfileTests(unittest.TestCase):
    def test_dates_missing_labels_and_malformed_rows(self):
        payload = ("msno,date,is_churn\nsynthetic-a,20170228,0\n"
                   "synthetic-b,20170230,1\nsynthetic-c,,2\nshort,20170301\n").encode()
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "fixture.csv"
            path.write_bytes(payload)
            result = profile_file(path)
        self.assertEqual(result["sha256"], hashlib.sha256(payload).hexdigest())
        self.assertEqual(result["rows_scanned"], 4)
        self.assertEqual(result["malformed_rows"], 1)
        self.assertEqual(result["dates"]["date"], {"min": "2017-02-28", "max": "2017-02-28", "invalid": 1})
        self.assertEqual(result["missing_counts"]["date"], 1)
        self.assertEqual(result["label_counts"], {"0": 1, "1": 1, "invalid": 1})
        self.assertNotIn("synthetic-a", str(result))

    def test_gzip_and_scan_limit_are_explicit(self):
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "fixture.csv.gz"
            with gzip.open(path, "wt", encoding="utf-8") as file:
                file.write("msno,is_churn\na,0\nb,1\n")
            partial = profile_file(path, 1)
            full = profile_file(path, 2)
        self.assertFalse(partial["complete_scan"])
        self.assertEqual(partial["rows_scanned"], 1)
        self.assertTrue(full["complete_scan"])

    def test_duplicate_header_rejected(self):
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "fixture.csv"
            path.write_text("msno,msno\na,b\n", encoding="utf-8")
            with self.assertRaises(ValueError):
                profile_file(path)


if __name__ == "__main__":
    unittest.main()
