import hashlib
import unittest
from unittest.mock import patch
from scripts import gomes_zenodo_vertical_source_preflight_v1 as gate

class GomesSourceTests(unittest.TestCase):
    def test_header_and_rows_without_ecological_values(self):
        raw=b"Species,Canopy,Time,No.\nAA,U,20,DO_NOT_PARSE\nBB,C,22,DO_NOT_PARSE\n"
        with patch.object(gate,"EXPECTED_MD5",hashlib.md5(raw).hexdigest()):
            r=gate.inspect_source(raw)
        self.assertEqual(r["status"],"source_metadata_pass")
        self.assertEqual(r["row_count"],2)
        self.assertFalse(r["ecological_outcome_values_accessed"])
        self.assertEqual(r["header_fields"],["Species","Canopy","Time","No."])
    def test_invalid_hash_rejected(self):
        with self.assertRaisesRegex(RuntimeError,"MD5"):
            gate.inspect_source(b"Bad,Source,CSV\n1,2,3\n")
    def test_ragged_source_fails(self):
        raw=b"Species,Canopy,Time\nAA,U,20\nBB,C\n"
        with patch.object(gate,"EXPECTED_MD5",hashlib.md5(raw).hexdigest()):
            r=gate.inspect_source(raw)
        self.assertEqual(r["status"],"source_metadata_stop")

if __name__=="__main__":
    unittest.main()
