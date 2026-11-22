import hashlib
import unittest
from unittest.mock import patch
from scripts import gomes_zenodo_structure_v2 as v2

def mock_source():
    return (",".join(v2.KNOWN_HEADER)+"\n"
            +",1,20,Site1,blue,high,A,SEALED,2020-01-01,20:00,0,0,0,0,0,0,0,0,0\n"
            +",1,20,Site1,blue,low,B,SEALED,2020-01-01,20:00,0,0,0,0,0,0,0,0,0\n").encode()

class StructureTests(unittest.TestCase):
    def test_only_context_opened_and_paired_groups(self):
        raw=mock_source()
        with patch.object(v2,"EXPECTED_MD5",hashlib.md5(raw).hexdigest()):
            r=v2.metadata_scan(raw)
        self.assertFalse(r["response_number_opened"])
        self.assertEqual(r["context_day_hour_x_with_two_or_more_pos"],1)
        self.assertEqual(r["bat_label_count"],2)
    def test_reject_header_change(self):
        raw=mock_source().replace(b"Number",b"Activity",1)
        with patch.object(v2,"EXPECTED_MD5",hashlib.md5(raw).hexdigest()):
            with self.assertRaisesRegex(RuntimeError,"header"):
                v2.metadata_scan(raw)

if __name__=="__main__":
    unittest.main()
