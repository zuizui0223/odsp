"""No wildlife sensor outcomes: strict one-digit UTC second normalization grammar."""
from datetime import datetime
from pathlib import Path
from tempfile import TemporaryDirectory
import json
import unittest

from scripts.movebank_wolf_original_strict_utc_second_preflight_20261025 import (
    SOURCE_EXPECTED_ROWS,PATTERN,parse_one_digit_source_UTC,calendar_only_stream
)

class YellowstoneWolfStrictOriginalTimeSource(unittest.TestCase):
    def test_one_digit_second_before_Z_is_exact_UTC_not_guess(self):
        d,s=parse_one_digit_source_UTC("2019-02-17 12:34:5Z")
        self.assertEqual(d,datetime(2019,2,17,12,34,5))
        self.assertEqual(s,"UTC_ONE_DIGIT_SECONDS_Z_REPAIRED")
        d2,s2=parse_one_digit_source_UTC("2019-02-17 12:34:05Z")
        self.assertEqual(d,d2)
        self.assertEqual(s2,"ORIGINAL_ALREADY_ISO")
    def test_no_other_suffix_climate_or_time_assumptions(self):
        for raw in ("2019-02-17 12:34:5C","2019-02-17 12:34:5U",
                    "2019-02-17 12:34:5","2019-02-17 12:34:5EST",
                    "2019/02/17 12:34:5Z"):
            d,s=parse_one_digit_source_UTC(raw)
            self.assertIsNone(d)
            self.assertEqual(s,"NOT_STRICT_ONE_DIGIT_UTC_Z")
    def test_invalid_date_and_source_timezone_not_silently_normalized(self):
        v,s=parse_one_digit_source_UTC("2019-02-31 12:34:5Z")
        self.assertIsNone(v)
        self.assertEqual(s,"INVALID_DATE_TIME_AFTER_STRICT_Z_REPAIR")
        v,s=parse_one_digit_source_UTC("2020-01-21T10:30:05+08:00")
        self.assertEqual(v,datetime(2020,1,21,2,30,5))
        self.assertEqual(s,"ORIGINAL_ALREADY_ISO")
        self.assertEqual(SOURCE_EXPECTED_ROWS,23604)
    def test_never_exports_original_animal_ids_coordinates_timestamps_or_speed(self):
        with TemporaryDirectory() as td:
            p=Path(td)/"source.csv"
            p.write_text("timestamp,individual-local-identifier,location-lat,location-long\n"
                         "2019-02-17 12:34:5Z,SECRET_TAG_42,44,-110\n"
                         "2019-02-18 22:12:9Z,SECRET_TAG_42,44,-110\n")
            rec=calendar_only_stream(p)
        self.assertEqual(rec["original_source_row_status_counts"]["UTC_ONE_DIGIT_SECONDS_Z_REPAIRED"],2)
        self.assertEqual(rec["original_source_row_status_counts"]["fully_parseable_after_only_strict_UTC_second_normalization"],2)
        self.assertEqual(rec["status"],"HOLD_NOT_ALL_ORIGINAL_SOURCE_TIME_STRICTLY_RECOVERED")
        self.assertNotIn("SECRET_TAG",json.dumps(rec))
        self.assertFalse(rec["gps_displacement_magnitudes_read"])
    def test_metadata_contract_does_not_authorize_other_time_reinterpretations(self):
        c=json.loads(Path("research/MOVEBANK_WOLF_STRICT_ONE_DIGIT_UTC_REPAIR_SOURCE_ONLY_20261025.json").read_text())
        self.assertIn("ONLY strings exactly",c["allowed_single_repair"])
        self.assertIn("suffix is not Z",c["limits"])
        self.assertIn("no original animal movement",c["scientific_scope"])

if __name__=="__main__":
    unittest.main()
