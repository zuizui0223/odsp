"""Pure fixtures: yearwise observational OR must not be relabeled as animal behavior."""
import datetime as dt
import json
from collections import Counter
from pathlib import Path
import unittest
from scripts.run_serengeti_photo_weather_cycle_alignment_v0 import (
    EXPECTED_ERA5_DAILY_SERIES_SHA256,
    EXPECTED_ORIGINAL_JSON_SHA256,
    PREDECLARED_CYCLES,
    PREDECLARED_FOCAL,
    mh_by_year,
    source_eligible_site_date_map,
    tmax_precip30_change,
)
class TestJoinedRegionalWeatherPhotoContext(unittest.TestCase):
    def test_source_fingerprints_and_no_new_species_selection(self):
        self.assertEqual(EXPECTED_ORIGINAL_JSON_SHA256,
            "0b70f7425d8ade2489a989bebc7b22fda997d82b2190e5e7d3c5d6f83ee71ef3")
        self.assertEqual(EXPECTED_ERA5_DAILY_SERIES_SHA256,
            "aaa93eec1ac0fab3315bfc712020970746d47cd1d407b8a7778243b2f627bee7")
        self.assertEqual(PREDECLARED_CYCLES,(2010,2011,2012))
        self.assertEqual(len(PREDECLARED_FOCAL),5)

    def test_site_year_mh_remains_undefined_for_zero_cells(self):
        cells={
            ("a",2011,"rising"):Counter({"core":3,"edge":0,"night":2}),
            ("a",2011,"falling"):Counter({"core":0,"edge":2,"night":4}),
            ("b",2011,"rising"):Counter({"core":4,"edge":1,"night":2}),
            ("b",2011,"falling"):Counter({"core":3,"edge":5,"night":3}),
        }
        r=mh_by_year(cells,2011)
        self.assertEqual(r["events_rising"],12)
        self.assertEqual(r["events_falling"],17)
        self.assertEqual(r["sites_with_species_detections_on_both_branches"],2)
        self.assertGreater(r["site_stratified_recorded_edge_core_OR"],1)
        self.assertIsNotNone(r["site_stratified_recorded_night_day_OR"])
        absent=mh_by_year({},2012)
        self.assertIsNone(absent["site_stratified_recorded_night_day_OR"])
        self.assertEqual(absent["events_rising"],0)

    def test_climate_lag_30_day_sum_includes_target_date(self):
        rise=dt.date(2010,12,14)
        fall=dt.date(2010,12,28)
        grid={}
        for offset in range(-29,1):
            grid[(rise+dt.timedelta(days=offset)).isoformat()]={"precipitation_sum":1.0}
            grid[(fall+dt.timedelta(days=offset)).isoformat()]={"precipitation_sum":2.0}
        # Overlapping windows are overwritten by the later synthetic series.
        grid[rise.isoformat()]["temperature_2m_max"]=20.0
        grid[fall.isoformat()]["temperature_2m_max"]=23.0
        t,r=tmax_precip30_change(grid,rise,fall)
        self.assertAlmostEqual(t,3.0)
        self.assertTrue(r>0)

    def test_contract_does_not_claim_fully_confirmatory_reanalysis(self):
        p=Path(__file__).resolve().parents[1]/"research/SERENGETI_SITE_DATE_PHOTO_ERA5_ALIGNMENT_V0_CONTRACT.json"
        c=json.loads(p.read_text())
        self.assertIn("AFTER",c["sequencing_note"])
        self.assertTrue(c["strict_join"]["original_eligible_source_photo_date_pairs_not_retuned"])
        self.assertIn("UNAVAILABLE",c["strict_join"]["q_and_true_hardware_uptime"])
        self.assertTrue(any("three" in s.lower() for s in c["hard_limits"]))

if __name__=="__main__":
    unittest.main()
