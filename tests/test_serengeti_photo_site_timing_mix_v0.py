"""No animal events: algebra and epistemic controls for photo-time/site composition."""
import json
import unittest
from collections import Counter
from pathlib import Path
from scripts.run_serengeti_photo_site_timing_mix_v0 import (
    compute_common_support_decomposition, FOCAL, YEARS
)

ROOT=Path(__file__).resolve().parents[1]

def c(night,day):
    return Counter(night=night,core=day,edge=0)

class TestPhotoTimingVersusStationMix(unittest.TestCase):
    def test_within_only_stable_site_weights(self):
        src={
            "A":{"rising":c(2,8),"falling":c(7,3)},
            "B":{"rising":c(2,8),"falling":c(7,3)},
        }
        r=compute_common_support_decomposition(src)
        self.assertAlmostEqual(r["within_station_photo_schedule_term"],.5)
        self.assertAlmostEqual(r["among_station_photo_weight_term"],0.0)
        self.assertAlmostEqual(r["common_photo_night_fraction_change"],.5)
        self.assertAlmostEqual(r["photo_station_total_variation"],0)
        self.assertAlmostEqual(r["decomposition_identity_error"],0)

    def test_station_reweighting_only_invariant_within_site_timing(self):
        src={
            "A":{"rising":c(8,2),"falling":c(72,18)},
            "B":{"rising":c(18,72),"falling":c(2,8)},
        }
        r=compute_common_support_decomposition(src)
        self.assertAlmostEqual(r["within_station_photo_schedule_term"],0)
        self.assertAlmostEqual(r["among_station_photo_weight_term"],.48)
        self.assertAlmostEqual(r["common_photo_night_fraction_change"],.48)
        self.assertAlmostEqual(r["photo_station_total_variation"],.8)

    def test_detection_selected_roster_and_all_site_delta_are_distinct(self):
        src={
            "A":{"rising":c(8,2),"falling":c(8,2)},
            "B":{"rising":c(0,0),"falling":c(10,0)},
        }
        r=compute_common_support_decomposition(src)
        self.assertEqual(r["source_sites_with_either_branch_photo"],2)
        self.assertEqual(r["common_photo_positive_camera_count"],1)
        self.assertAlmostEqual(r["common_photo_night_fraction_change"],0)
        self.assertAlmostEqual(r["all_site_photo_night_fraction_change"],.1)
        self.assertAlmostEqual(r["common_photo_fraction_of_all_records"]["falling"],.5)
        self.assertFalse(r["support_display_eligible"])

    def test_no_common_photographed_site_reports_undefined_not_pseudocount(self):
        src={
            "A":{"rising":c(8,2)},
            "B":{"falling":c(3,7)},
        }
        r=compute_common_support_decomposition(src)
        self.assertEqual(r["common_photo_positive_camera_count"],0)
        self.assertIsNone(r["within_station_photo_schedule_term"])
        self.assertIsNone(r["among_station_photo_weight_term"])
        self.assertIsNone(r["common_photo_night_fraction_change"])
        self.assertAlmostEqual(r["all_site_photo_night_fraction_change"],-.5)

    def test_components_can_have_opposite_signs_and_still_sum_exactly(self):
        src={
            "A":{"rising":c(8,2),"falling":c(54,36)},
            "B":{"rising":c(18,72),"falling":c(1,9)},
        }
        r=compute_common_support_decomposition(src)
        self.assertLess(r["within_station_photo_schedule_term"],0)
        self.assertGreater(r["among_station_photo_weight_term"],0)
        self.assertAlmostEqual(
            r["common_photo_night_fraction_change"],
            r["within_station_photo_schedule_term"]+
            r["among_station_photo_weight_term"],places=13)

    def test_registration_all_43_taxa_and_site_vs_region_claims(self):
        contract=json.loads(
            (ROOT/"research/SERENGETI_WITHIN_STATION_VERSUS_SPATIAL_MIX_V0_CONTRACT.json").read_text())
        self.assertEqual(contract["source"]["original_taxon_labels"],43)
        self.assertEqual(len(YEARS),3)
        self.assertEqual(len(FOCAL),7)
        self.assertTrue(contract["outputs"]["no_zero_pseudocount"])
        self.assertTrue(any("photo" in s.lower() for s in contract["null_limits"]))
        self.assertFalse("p_value" in contract["outputs"])

if __name__=="__main__": unittest.main()
