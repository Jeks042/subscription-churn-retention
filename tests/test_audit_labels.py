import tempfile
import unittest
from pathlib import Path
from src.audit_labels import read_labels


class LabelTests(unittest.TestCase):
    def test_duplicate_conflicts_missing_and_invalid(self):
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "labels.csv"
            path.write_text("msno,is_churn\na,0\na,1\n,0\nb,2\nc,1\n", encoding="utf-8")
            stats, labels = read_labels(path)
        self.assertEqual(stats["duplicate_key_rows"], 1)
        self.assertEqual(stats["conflicting_duplicate_rows"], 1)
        self.assertEqual(stats["missing_ids"], 1)
        self.assertEqual(stats["invalid_labels"], 1)
        self.assertEqual(stats["unique_valid_ids"], 2)
        self.assertEqual(stats["churn_rate"], 0.5)


if __name__ == "__main__":
    unittest.main()
