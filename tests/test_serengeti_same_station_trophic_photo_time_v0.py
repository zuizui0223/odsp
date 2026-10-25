"""Synthetic original-source support and ecological claim ceiling tests (NO animal observations)."""
import json
import math
import unittest
from collections import Counter, defaultdict
from pathlib import Path
from scripts.run_serengeti_same_station_trophic_photo_time_v0 import (
    PAIRS,sitecycle_difference,strict_log_three_way,pair_summary,stats
)
ROOT=Path(__file__).resolve().parents[1]

class TestTrophicCoRecordedPhotoTime(unittest.TestCase):
    def test_parallel_photo_night_shift_has_zero_between_taxon_difference(self):
        af=Counter(night=8,core=2)
        bf=Counter(night=6,core=4)
        ar=Counter(night=4,core=6)
        br=Counter(night=2,core=8)
        self.assertAlmostEqual(sitecycle_difference(af,bf,ar,br),0.0)
        self.assertAlmostEqual(strict_log_three_way(af,bf,ar,br),0.0)

    def test_site_difference_positive_when_predator_night_fraction_changes_more(self):
        af=Counter(night=8,edge=2)
        bf=Counter(night=2,core=8)
        ar=Counter(night=3,core=7)
        br=Counter(night=3,core=7)
        self.assertAlmostEqual(sitecycle_difference(af,bf,ar,br),.6)
        self.assertGreater(strict_log_three_way(af,bf,ar,br),0)

    def test_missing_a_species_branch_does_not_create_a_pseudocount(self):
        af=Counter(night=1)
        bf=Counter(core=2)
        ar=Counter(core=1)
        br=Counter()
        self.assertIsNone(sitecycle_difference(af,bf,ar,br))
        self.assertIsNone(strict_log_three_way(af,bf,ar,br))
        self.assertIsNone(strict_log_three_way(
            Counter(night=1),Counter(night=1,core=1),
            Counter(night=1,core=1),Counter(night=1,core=1)
        ))

    def test_camera_roster_and_leave_one_site_out(self):
        structural={("s1",2010),("s2",2010),("s2",2011),("s3",2011)}
        counts={
            "hyenaSpotted":{
                ("s1",2010,"rising"):Counter(night=4,core=6),
                ("s1",2010,"falling"):Counter(night=9,core=1),
                ("s2",2010,"rising"):Counter(night=2,core=8),
                ("s2",2010,"falling"):Counter(night=5,core=5),
                ("s3",2011,"falling"):Counter(night=8),
            },
            "zebra":{
                ("s1",2010,"rising"):Counter(night=2,core=8),
                ("s1",2010,"falling"):Counter(night=3,core=7),
                ("s2",2010,"rising"):Counter(night=4,core=6),
                ("s2",2010,"falling"):Counter(night=4,core=6),
                ("s2",2011,"rising"):Counter(core=2),
                ("s2",2011,"falling"):Counter(core=3),
                ("s3",2011,"rising"):Counter(night=2),
            }
        }
        res=pair_summary("hyenaSpotted","zebra","predator",counts,structural)
        self.assertEqual(res["structurally_eligible_camera_sitecycles"],4)
        self.assertEqual(res["sitecycles_with_both_taxa_recorded_in_both_season_branches"],2)
        self.assertEqual(res["distinct_physical_cameras_supporting_pair"],2)
        self.assertEqual(res["strict_eight_nonzero_record_cells_sitecycles"],2)
        self.assertEqual(res["per_solstice_cycle"][0]["eligible_codetected_sitecycles"],2)
        self.assertEqual(res["per_solstice_cycle"][1]["eligible_codetected_sitecycles"],0)
        self.assertEqual(res["physical_camera_equal_D"]["n"],2)
        lo,hi=res["physical_camera_leave_one_out_D_min_max"]
        self.assertLessEqual(lo,hi)

    def test_frozen_four_pairs_and_claim_guards(self):
        p=ROOT/"research/SERENGETI_SAME_STATION_TROPHIC_PHOTO_TIME_V0_CONTRACT.json"
        c=json.loads(p.read_text())
        self.assertEqual(len(PAIRS),4)
        self.assertEqual(
            [(x["focal"],x["comparison"]) for x in c["pair_order_fixed"]],
            [(a,b) for a,b,_ in PAIRS]
        )
        self.assertIn("NOT",c["prior_outcome_exposure"])
        self.assertTrue(any("hourly uptime" in t.lower() for t in c["null_and_limits"]))
        self.assertEqual(stats([])["n"],0)

if __name__=="__main__":
    unittest.main()
