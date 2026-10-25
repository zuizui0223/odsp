"""Known-truth original source-only screening for three new same-taxon cohorts.

No empirical GPS speed, original file bytes or species effect is accessed.
"""
import csv
from pathlib import Path
from tempfile import TemporaryDirectory
from unittest.mock import patch
import unittest

from scripts.movebank_same_taxon_three_source_only_20261025 import (
    CONTRACT,EXPECTED_LABELS,contract_sources,source_metadata_gate,
    taxonomy_source_only_summary,source_only_one
)

class SameTaxonPreflightKnownTruth(unittest.TestCase):
    def setUp(self):
        self.sources=contract_sources()
        self.source=self.sources[0]
        self.metadata={"bitstream_uuid":self.source["data_bitstream"],
                       "bytes":self.source["file_bytes"],
                       "name":self.source["filename"],
                       "checksum":{"checkSumAlgorithm":"MD5",
                                   "value":self.source["checksum_md5"]}}

    def test_frozen_three_selected_before_new_animal_outcomes(self):
        self.assertEqual(tuple(s["label"] for s in self.sources),EXPECTED_LABELS)
        self.assertEqual([s["taxon"] for s in self.sources],
                         ["Canis lupus","Odocoileus virginianus","Cervus elaphus"])
        self.assertEqual([s["file_bytes"] for s in self.sources],
                         [3854637,6809097,149867434])
        self.assertNotEqual(self.sources[0]["package_uuid"],
                            "fb867768-11eb-4b55-9460-6ada78cc34c4")
        self.assertTrue(CONTRACT.is_file())

    def test_source_provider_id_md5_and_bytes_are_required(self):
        self.assertEqual(source_metadata_gate(self.source,[self.metadata]),self.metadata)
        with self.assertRaisesRegex(ValueError,"HOLD_PROVIDER_MD5_OR_BYTE_COUNT_CHANGED"):
            source_metadata_gate(self.source,[{**self.metadata,"bytes":1}])
        with self.assertRaisesRegex(ValueError,"HOLD_PROVIDER_MD5_OR_BYTE_COUNT_CHANGED"):
            source_metadata_gate(self.source,[{**self.metadata,
                "checksum":{"checkSumAlgorithm":"MD5","value":"0"*32}}])
        with self.assertRaisesRegex(ValueError,"HOLD_ORIGINAL_BITSTREAM_MISSING_NOT_UNIQUE"):
            source_metadata_gate(self.source,[])
        with self.assertRaisesRegex(ValueError,"HOLD_PROVIDER_ORIGINAL_FILENAME_CHANGED"):
            source_metadata_gate(self.source,[{**self.metadata,"name":"other.csv"}])

    def test_original_taxonomy_label_is_checked_without_ID_export(self):
        with TemporaryDirectory() as tmp:
            p=Path(tmp)/"source.csv"
            p.write_text("individual-taxon-canonical-name,individual-local-identifier\n"
                         "Canis lupus,IDENTITY_PRIVATE_A\n"
                         "Canis lupus,IDENTITY_PRIVATE_B\n")
            o=taxonomy_source_only_summary(p,"Canis lupus")
            self.assertEqual(o["off_target_taxon_rows"],0)
            self.assertEqual(o["original_taxon_rows_checked"],2)
            self.assertNotIn("IDENTITY_PRIVATE",str(o))
            p.write_text("species\nCanis lupus\nOdocoileus virginianus\n")
            o=taxonomy_source_only_summary(p,"Canis lupus")
            self.assertEqual(o["off_target_taxon_rows"],1)

    def test_missing_taxon_column_flags_metadata_only_not_imputed(self):
        with TemporaryDirectory() as tmp:
            p=Path(tmp)/"raw.csv"
            p.write_text("timestamp,latitude,longitude\n"
                         "2020-01-01T12:00:00,42,-110\n")
            x=taxonomy_source_only_summary(p,"Canis lupus")
            self.assertEqual(x["status"],"TAXON_RESTRICTED_BY_ORIGINAL_PACKAGE_METADATA_ONLY")
            self.assertFalse(x["original_csv_taxon_column_present"])

    def test_original_source_only_success_discloses_no_gps_events(self):
        mock_feasibility={
            "status":"coverage_evaluated","csv_rows":200,
            "valid_position_time_individual_rows":200,
            "distinct_individuals_with_valid_fixes":12,
            "individual_years_ge_10_pairs":6,
            "max_conservative_matched_day_pairs":19,
        }
        with TemporaryDirectory() as tmp:
            with patch("scripts.movebank_same_taxon_three_source_only_20261025.original_files",
                       return_value=[self.metadata]), \
                 patch("scripts.movebank_same_taxon_three_source_only_20261025.checksum_and_download",
                       return_value={"bytes":self.source["file_bytes"],
                                     "provider_checksum_verified":True}), \
                 patch("scripts.movebank_same_taxon_three_source_only_20261025.inspect_csv",
                       return_value=mock_feasibility), \
                 patch("scripts.movebank_same_taxon_three_source_only_20261025.taxonomy_source_only_summary",
                       return_value={"original_csv_taxon_column_present":True,
                                     "off_target_taxon_rows":0}):
                out=source_only_one(self.source,Path(tmp))
            self.assertEqual(out["status"],"SOURCE_ONLY_CALENDAR_FEASIBILITY_VERIFIED")
            self.assertEqual(out["source_only_ge10_animal_years"],6)
            self.assertFalse(out["animal_behavior_or_ecological_season_effect_calculated"])
            self.assertFalse(out["individual_ID_source_coordinates_or_datetimes_exported"])
            self.assertNotIn("IDENTITY_PRIVATE",str(out))

    def test_metadata_integrity_failure_is_HOLD_not_zero_animal_effect(self):
        with TemporaryDirectory() as tmp:
            with patch("scripts.movebank_same_taxon_three_source_only_20261025.original_files",
                       return_value=[]):
                r=source_only_one(self.source,Path(tmp))
            self.assertTrue(r["status"].startswith("HOLD_"))
            self.assertFalse(r["original_GPS_steps_or_speed_values_inspected"])
            self.assertFalse(r["animal_behavior_or_ecological_season_effect_calculated"])

if __name__=="__main__":
    unittest.main()
