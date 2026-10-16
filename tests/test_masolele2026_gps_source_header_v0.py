"""Synthetic-only original wildebeest GPS source admission controls."""
import json
from pathlib import Path
import unittest
from scripts.preflight_masolele2026_wildebeest_gps_header_v0 import (
    _normalized,REQUIRED_COLUMNS,EXPECTED_SIZE,EXACT_SOURCE_SHA256,
    public_header_only_receipt
)

ROOT=Path(__file__).resolve().parents[1]

class TestOriginal2026WildebeestGPSHeaderOnly(unittest.TestCase):
    def test_source_metadata_unchanged(self):
        c=json.loads((ROOT/"research/MASOLELE_2026_WILDEBEEST_GPS_SOURCE_GATE_V0.json").read_text())
        self.assertEqual(c["sha256"],EXACT_SOURCE_SHA256)
        self.assertEqual(c["expected_size_bytes"],EXPECTED_SIZE)
        self.assertEqual(c["published_individuals"],57)
        self.assertEqual(c["published_paper_eligible_observations"],143168)
        self.assertEqual(len(REQUIRED_COLUMNS),5)
        self.assertIn("no protected animal gps rows",c["nature"].lower())

    def test_source_never_promoted_on_changed_or_fabricated_bytes(self):
        junk=b"AID,Date,Step_length,SPECIES,COLLAR_ID\nsecretlion,2020-01-01,1,WB,tag42\n"
        with self.assertRaisesRegex(ValueError,"HOLD_ORIGINAL_DRYAD_BYTES_OR_SHA256_MISMATCH"):
            public_header_only_receipt(junk)

    def test_csv_columns_normalization(self):
        self.assertEqual(_normalized("Step_length"),"steplength")
        self.assertEqual(_normalized("COLLAR_ID"),"collarid")

    def test_no_gps_fix_hours_biological_claims_from_original_header(self):
        c=json.loads((ROOT/"research/MASOLELE_2026_WILDEBEEST_GPS_SOURCE_GATE_V0.json").read_text())
        self.assertIn("1h",c["published_fix_interval_distribution"])
        self.assertIn("4h",c["published_fix_interval_distribution"])
        self.assertTrue(any("GPS fixes" in t for t in c["observation_ceiling"]))

if __name__=="__main__":unittest.main()
