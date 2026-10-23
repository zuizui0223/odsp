"""Known-truth synthetic solar/marginal-vs-site-conditioned controls only."""
from collections import Counter
from datetime import datetime, date, timedelta
from pathlib import Path
import json
import math
import unittest

from scripts.run_serengeti_source_recorded_solar_season_v0 import (
    _mh, _odds, solar_boundaries, summarize_taxon, zone,
)


class TestSerengetiRecordedPhase(unittest.TestCase):
    def test_true_sunrise_boundaries_and_daylight_equal_core_edge(self):
        d=date(2012,11,20)
        sunrise,sunset,length=solar_boundaries(d,-2.3,34.8)
        self.assertTrue(300<sunrise<480)
        self.assertTrue(1000<sunset<1200)
        self.assertAlmostEqual(sunset-sunrise,length)
        self.assertEqual(zone(datetime(2012,11,20,2,0,0),-2.3,34.8),"night")
        self.assertEqual(zone(datetime(2012,11,20,12,30,0),-2.3,34.8),"core")
        self.assertEqual(zone(datetime(2012,11,20,8,10,0),-2.3,34.8),"edge")

    def test_mirrored_date_daylength_difference_less_than_one_minute_in_near_equator(self):
        solstice=date(2012,12,21)
        for k in (7,50,90,140,175):
            up=solstice-timedelta(days=k)
            down=solstice+timedelta(days=k)
            daylengths=[solar_boundaries(d,-2.3,34.8)[2] for d in (up,down)]
            self.assertLess(abs(daylengths[0]-daylengths[1]),1.0)

    def test_site_stratum_adjustment_not_automatic_pooled_odds(self):
        strata=[("a",18,2,8,12),("b",1,19,5,15)]
        conditioned=_mh(strata)
        pooled=_odds(19,21,13,27)
        self.assertIsNotNone(conditioned)
        self.assertIsNotNone(pooled)
        self.assertNotAlmostEqual(conditioned,pooled)
        self.assertIsNone(_mh([("a",0,5,0,8)]))

    def test_full_source_roster_zero_counts_and_no_pseudocount(self):
        cells={
            ("a",2011,"rising"):Counter({"core":10,"edge":2,"night":5}),
            ("a",2011,"falling"):Counter({"core":3,"edge":8,"night":9}),
            ("b",2011,"rising"):Counter({"core":2}),
            ("b",2011,"falling"):Counter(),
        }
        result=summarize_taxon("synthetic_species",cells)
        self.assertEqual(result["recorded_on_both_branches_site_cycles"],1)
        self.assertEqual(result["source_camera_events_by_branch_solar_zone"]["falling"]["night"],9)
        self.assertIsNotNone(result["site_cycle_stratified_MH_record_odds_edge_core"])
        self.assertFalse(result["eligible_descriptive_display"])
        self.assertIsNone(_odds(0,4,3,2))

    def test_frozen_protocol_claim_ceiling(self):
        p=Path(__file__).resolve().parents[1]/"research/SERENGETI_SOLAR_SEASON_RECORDED_EVENT_V0_CONTRACT.json"
        c=json.loads(p.read_text())
        self.assertEqual(c["source_roster_preflight"]["candidate_site_day_mirror_pairs"],25016)
        self.assertEqual(c["source_roster_preflight"]["sites_with_20_or_more_pairs_in_a_solstice_cycle"],186)
        self.assertEqual(c["source_roster_preflight"]["daylength_difference_tolerance_minutes"],1.0)
        self.assertIn("q",str(c["interpretational_ceiling"]))
        self.assertTrue(c["source_roster_preflight"]["eligibility_independent_of_animal_detection"])


if __name__=="__main__":
    unittest.main()
