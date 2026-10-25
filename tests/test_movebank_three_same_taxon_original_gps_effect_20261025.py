"""Known-truth gates, no new numerical GPS events read before source input."""
import json
from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch

from scripts.movebank_three_same_taxon_original_gps_effect_20261025 import (
    PINNED_SOURCE_SHA,old_cohort_gate,source_support_status,run
)
from scripts.movebank_same_taxon_three_source_only_20261025 import contract_sources

class NewSameTaxonMovementTests(unittest.TestCase):
    def test_prior_source_receipt_identity_frozen(self):
        self.assertEqual(PINNED_SOURCE_SHA,"f4b884a36dd109b01db04a55ea9a81ccd413d74271febd6e90f1da15b11eda4f")
        c=json.loads(Path("research/MOVEBANK_THREE_NEW_SAME_TAXON_GPS_EFFECT_V0_20261025.json").read_text())
        self.assertEqual(len(c["comparisons"]),3)
        self.assertIn("NOT inspected",c["sequencing"])
        self.assertTrue(any("No source GPS" in s for s in c["limits"]))

    def test_old_same_taxon_cohort_effects_locked_without_new_outcome(self):
        prior=old_cohort_gate()
        self.assertEqual(len(prior),3)
        self.assertEqual(prior["wolves_yellowstone"]["initial_n"],9)
        self.assertEqual(prior["white_tail_florida"]["initial_n"],33)
        self.assertEqual(prior["elk_southwest_alberta"]["initial_n"],12)
        self.assertAlmostEqual(prior["elk_southwest_alberta"]["initial_delta"],.04500073152774594)

    def test_source_invalid_is_hold_not_no_seasonal_change(self):
        self.assertEqual(source_support_status({"source_calendar_feasibility":{
            "valid_position_time_individual_rows":0,"individual_years_ge_10_pairs":0
        }}),"HOLD_ORIGINAL_GPS_LOCATION_OR_TIME_UNPARSEABLE")
        self.assertEqual(source_support_status({"source_calendar_feasibility":{
            "valid_position_time_individual_rows":40811,"individual_years_ge_10_pairs":0
        }}),"INSUFFICIENT_SOURCE_BOTH_BRANCH_CALENDAR_OBSERVATIONS")
        self.assertEqual(source_support_status({"source_calendar_feasibility":{
            "valid_position_time_individual_rows":878116,"individual_years_ge_10_pairs":235
        }}),"SOURCE_ONLY_SOLAR_CALENDAR_READY")

    def test_mocks_only_frozen_ready_source_and_retains_all_three_nulls(self):
        sources=contract_sources()
        screens=[
            {"source_calendar_feasibility":{"valid_position_time_individual_rows":0,
                "individual_years_ge_10_pairs":0},
             "original_download_integrity":{"provider_checksum_verified":True}},
            {"source_calendar_feasibility":{"valid_position_time_individual_rows":40811,
                "individual_years_ge_10_pairs":0},
             "original_download_integrity":{"provider_checksum_verified":True}},
            {"source_calendar_feasibility":{"valid_position_time_individual_rows":878116,
                "csv_rows":878116,
                "individual_years_ge_10_pairs":235,
                "distinct_individuals_with_valid_fixes":171},
             "original_download_integrity":{"provider_checksum_verified":True}},
        ]
        elk=sources[-1]
        fs=[{"bitstream_uuid":elk["data_bitstream"],
             "name":elk["filename"],"bytes":elk["file_bytes"],
             "checksum":{"checkSumAlgorithm":"MD5","value":elk["checksum_md5"]}}]
        fake={
            "gps_rows":878116,
            "source_individuals":171,
            "individual_years_ge10_matched_days":95,
            "effect_status":"exploratory_population_description",
            "effect":{
                "n_individuals":60,"n_positive":34,"n_negative":26,
                "mean_falling_minus_rising_log1p_night_over_day_kmh":.02,
                "mean_falling_minus_rising_day_log1p_kmh":.01,
                "mean_falling_minus_rising_night_log1p_kmh":.03,
                "individual_cluster_bootstrap_95_percentile":[-.01,.05],
            }
        }
        with tempfile.TemporaryDirectory() as td:
            with patch("scripts.movebank_three_same_taxon_original_gps_effect_20261025.source_gate",
                        return_value=(sources,screens)),\
                 patch("scripts.movebank_three_same_taxon_original_gps_effect_20261025.original_files",
                       return_value=fs) as original,\
                 patch("scripts.movebank_three_same_taxon_original_gps_effect_20261025.checksum_and_download",
                       return_value={"bytes":elk["file_bytes"],"provider_checksum_verified":True}),\
                 patch("scripts.movebank_three_same_taxon_original_gps_effect_20261025.inspect_csv",
                       return_value={"csv_rows":878116,"valid_position_time_individual_rows":878116,
                                     "individual_years_ge_10_pairs":235,
                                     "distinct_individuals_with_valid_fixes":171}),\
                 patch("scripts.movebank_three_same_taxon_original_gps_effect_20261025.taxonomy_source_only_summary",
                       return_value={"off_target_taxon_rows":0}),\
                 patch("scripts.movebank_three_same_taxon_original_gps_effect_20261025.analyze_file",
                       return_value=fake):
                result=run(Path(td)/"fake_prior.json",Path(td))
                self.assertEqual(original.call_count,1)
        self.assertEqual(result["new_GPS_source_admitted_count"],1)
        self.assertEqual(result["source_or_sampling_HOLD_count"],2)
        self.assertFalse(result["sources"][0]["new_GPS_movement_evaluated"])
        self.assertFalse(result["sources"][1]["new_GPS_movement_evaluated"])
        self.assertTrue(result["sources"][2]["new_GPS_movement_evaluated"])
        self.assertTrue(result["sources"][2]["same_sign_as_previous_taxon_source"])
        self.assertFalse(result["no_new_animal_lat_lon_ID_timestamp_exported"] is False)

    def test_animal_and_original_source_identifiers_not_exported_in_frozen_contract(self):
        cfg=json.loads(Path("research/MOVEBANK_THREE_NEW_SAME_TAXON_GPS_EFFECT_V0_20261025.json").read_text())
        self.assertEqual(len(cfg["response_components"]),3)
        self.assertTrue(any("animal" in s.lower() for s in cfg["limits"]))
        self.assertIn("all three files",cfg["eligibility"].lower())

if __name__=="__main__":
    unittest.main()
