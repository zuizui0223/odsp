"""Source-only tracking schema diagnosis; synthetic fixtures and no GPS movement."""
from pathlib import Path
from tempfile import TemporaryDirectory
import json
import unittest

from scripts.movebank_wolf_florida_original_source_diagnosis_20261025 import (
    LABELS,columns,timestamp_structure,inspect_failure_modes
)

class GPSOriginalSourceRootCauseTests(unittest.TestCase):
    def test_original_same_taxon_source_is_only_two_held_archives(self):
        self.assertEqual(LABELS,("wolves_yellowstone","white_tail_florida"))
    def test_canonical_schema_recognized_and_no_position_output(self):
        s=["timestamp","individual-local-identifier","location-lat","location-long",
           "individual-taxon-canonical-name"]
        x=columns(s)
        self.assertEqual(x["ind"],"individual-local-identifier")
        self.assertEqual(x["time"],"timestamp")
        self.assertEqual(x["lat"],"location-lat")
    def test_source_timestamp_format_summary_has_no_original_date_numbers(self):
        x=timestamp_structure("2019-02-17 12:34:56.0")
        self.assertEqual(x,"9999-99-99 99:99:99.9")
        self.assertNotIn("2019",x)
    def test_invalid_source_rows_accounted_without_artificial_zero_movement(self):
        with TemporaryDirectory() as tmp:
            f=Path(tmp)/"synthetic.csv"
            f.write_text("timestamp,individual-local-identifier,location-lat,location-long\n"
                         "2020-04-20T10:00:00,SECRET_ANIMAL_A,45,-112\n"
                         "invalid_timestamp,SECRET_ANIMAL_B,45,-112\n"
                         "2020-04-21T10:00:00,SECRET_ANIMAL_C,,\n",encoding="utf-8")
            out=inspect_failure_modes(f)
        c=out["source_row_reason_counts"]
        self.assertEqual(c["rows"],3)
        self.assertEqual(c["fully_valid_source_rows"],1)
        self.assertEqual(c["invalid_or_missing_timestamp"],1)
        self.assertEqual(c["invalid_or_missing_original_WGS84_position"],1)
        self.assertFalse(out["original_speed_or_movement_intervals_inspected"])
        self.assertFalse(out["original_GPS_ID_coordinates_timestamps_exported"])
        self.assertNotIn("SECRET_ANIMAL",json.dumps(out))
    def test_no_canonical_fields_is_hold_not_negative_ecology(self):
        with TemporaryDirectory() as tmp:
            f=Path(tmp)/"synthetic.csv"
            f.write_text("somethingelse\n123\n")
            out=inspect_failure_modes(f)
        self.assertEqual(out["status"],"HOLD_REQUIRED_GPS_CANONICAL_COLUMNS_MISSING")
        self.assertEqual(out["original_source_data_rows_scanned"],0)

if __name__=="__main__":
    unittest.main()
