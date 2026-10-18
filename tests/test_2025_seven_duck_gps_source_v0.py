"""Known-truth, source-only UTC solstice and coarse location GPS support."""
import json
from datetime import date,datetime
from pathlib import Path
import unittest
from scripts.audit_2025_seven_duck_gps_daylength_source_v0 import (
    PINNED_MD5,REQUIRED_FIELDS,MIN_DATE_EACH_BRANCH,
    solstice_branch,date_support,interval_bin,parse_original_time,
    schema_key
)
ROOT=Path(__file__).resolve().parents[1]

class TestPublicSevenSpeciesDuckGPSPreflight(unittest.TestCase):
    def test_original_source_md5_and_schema_gate(self):
        self.assertEqual(PINNED_MD5,"1972d0ef08b83c2b88a169ba07bb48b3")
        self.assertIn("ground.speed",REQUIRED_FIELDS)
        self.assertIn("individual.id",REQUIRED_FIELDS)
        self.assertEqual(schema_key("ground.speed"),"groundspeed")
        c=json.loads((ROOT/"research/DUCK_GPS_2025_SOURCE_DAYLENGTH_PREFLIGHT_V0_CONTRACT.json").read_text())
        self.assertEqual(c["source"]["md5"],PINNED_MD5)
        self.assertFalse(c["fields_and_q"]["read_GPS_speed_value_for_outcome"])
        self.assertEqual(MIN_DATE_EACH_BRANCH,7)

    def test_hemisphere_correct_astronomical_branch(self):
        self.assertEqual(solstice_branch(date(2020,11,21),+50),(2020,"falling"))
        self.assertEqual(solstice_branch(date(2021,1,21),+50),(2020,"rising"))
        self.assertEqual(solstice_branch(date(2020,11,21),-35),(2020,"rising"))
        self.assertEqual(solstice_branch(date(2021,1,21),-35),(2020,"falling"))
        self.assertIsNone(solstice_branch(date(2020,11,21),.3))

    def test_same_individual_location_bucket_consistent_near_solstice(self):
        a=date_support("study","indiv","species",datetime(2020,11,21,3),50.51,8.01)
        b=date_support("study","indiv","species",datetime(2021,1,21,4),50.53,8.04)
        self.assertEqual(a[0],b[0])
        self.assertEqual(a[1],"falling")
        self.assertEqual(b[1],"rising")
        c=date_support("study","indiv","species",datetime(2021,1,21,4),51.07,8.04)
        self.assertNotEqual(a[0],c[0])
        self.assertIsNone(date_support("study","indiv","species",datetime(2020,12,21),50.53,8.04))

    def test_fix_interval_bins_preserve_nonzero_schedules(self):
        self.assertEqual(interval_bin(1),"0-1.5")
        self.assertEqual(interval_bin(2),"1.5-3")
        self.assertEqual(interval_bin(4),"3-6")
        self.assertEqual(interval_bin(8),"6-12")
        self.assertEqual(interval_bin(0),"duplicate_or_nonincreasing")
        self.assertEqual(interval_bin(24),">12")

    def test_clock_UTC_timestamp_parser_and_anonymity_protocol(self):
        self.assertEqual(parse_original_time("2019-12-31 23:15:00"),datetime(2019,12,31,23,15))
        with self.assertRaisesRegex(ValueError,"HOLD_TIMEZONE_AWARE_RAW_SOURCE"):
            parse_original_time("2019-12-31 23:15:00+02:00")
        c=json.loads((ROOT/"research/DUCK_GPS_2025_SOURCE_DAYLENGTH_PREFLIGHT_V0_CONTRACT.json").read_text())
        self.assertIn("No source animal",c["source_safety"])

if __name__=="__main__": unittest.main()
