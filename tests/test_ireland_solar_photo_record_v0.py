"""Original dataset is NOT a new latent animal experiment; synthetic guards only."""
import json
import unittest
from pathlib import Path
from scripts.audit_ireland_solar_daylength_recorded_v0 import (
    BASE_ORIGINAL_INCLUDED_ROWS, BASE_ALL_ROWS, GIT_BLOB_SHA, parse_minutes,
    zone, pooled, mh,
)

ROOT=Path(__file__).resolve().parents[1]
class TestIrelandSolarPhotoTime(unittest.TestCase):
    def test_original_source_expected_9411_and_8761(self):
        self.assertEqual(BASE_ALL_ROWS,9411)
        self.assertEqual(BASE_ORIGINAL_INCLUDED_ROWS,8761)
        self.assertEqual(GIT_BLOB_SHA,"2084dfac55acb75efe6e61c1abc306aeda0904eb")

    def test_equal_daylight_core_edge_and_night_definition(self):
        rise,down=6*60,18*60
        self.assertEqual(zone(3*60,rise,down),"night")
        self.assertEqual(zone(8*60,rise,down),"edge")
        self.assertEqual(zone(11*60,rise,down),"core")
        self.assertEqual(zone(17*60,rise,down),"edge")
        self.assertEqual(zone(19*60,rise,down),"night")
        self.assertEqual(zone(15*60,rise,down),"edge")

    def test_undefined_zero_cells_preserved(self):
        self.assertIsNone(pooled(1,0,3,3))
        self.assertIsNone(mh([(1,0,3,2)]))
        self.assertAlmostEqual(mh([(3,4,5,6)]),.9)

    def test_no_misparsed_clocks_or_date_refit(self):
        self.assertEqual(parse_minutes("00:04:00"),4)
        self.assertEqual(parse_minutes("16:42"),1002)
        with self.assertRaises(ValueError):
            parse_minutes("24:00:00")
        with self.assertRaises(ValueError):
            parse_minutes("bad")
        with self.assertRaises(ValueError):
            parse_minutes("11:82")

    def test_protocol_explicit_detection_conditioned_selection(self):
        c=json.loads((ROOT/"research/IRELAND_RECORDED_SOLAR_DAYLENGTH_V0_CONTRACT.json").read_text())
        self.assertTrue(c["method"]["selection_warning"].startswith("Date presence is detection-conditioned"))
        self.assertIn("No p-value",str(c["no_claims"]))
        self.assertIn("<=10min", c["method"]["match"])


if __name__=="__main__":
    unittest.main()
