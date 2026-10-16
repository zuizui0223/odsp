"""Synthetic only: NDVI time-lag, site selection and photo-source limits."""
from collections import Counter
from datetime import date
import json
from pathlib import Path
import unittest

from scripts.run_serengeti_camera_ndvi_photo_assoc_v0 import (
    FIRST_SATELLITE_SHA,REQUIRED_ORIGINAL_PHOTOS,
    last_completed_site_NDVI,spearman,correlations_by_taxon_year,FOCAL
)
ROOT=Path(__file__).resolve().parents[1]

class TestCameraRemoteSensingEcology(unittest.TestCase):
    def test_frozen_satellite_and_first_photo_contract(self):
        self.assertEqual(FIRST_SATELLITE_SHA,
            "e0e3c57de8d6a3ab9996412886e9733ea572cf9989f88a68b5c3ac5fb5557f11")
        self.assertEqual(REQUIRED_ORIGINAL_PHOTOS,38792)
        self.assertEqual(len(FOCAL),5)

    def test_only_last_completed_qa_good_satellite_is_used(self):
        ends=[date(2012,1,16),date(2012,2,1)]
        maps=[{"A":.2,"B":.5},{"A":None,"B":.4}]
        self.assertEqual(last_completed_site_NDVI(ends,maps,"A",date(2012,1,30)),.2)
        self.assertIsNone(last_completed_site_NDVI(ends,maps,"A",date(2012,2,3)))
        self.assertAlmostEqual(last_completed_site_NDVI(ends,maps,"B",date(2012,2,3)),.4)
        self.assertIsNone(last_completed_site_NDVI(ends,maps,"B",date(2012,3,12)))

    def test_spearman_monotone_positive_and_negative(self):
        self.assertAlmostEqual(spearman(list(range(15)),list(range(15))),1)
        self.assertAlmostEqual(spearman(list(range(15)),list(range(14,-1,-1))),-1)
        self.assertIsNone(spearman([1]*15,list(range(15))))
        self.assertIsNone(spearman(list(range(10)),list(range(10))))

    def test_insufficient_photo_source_yields_undefined_correlation_not_pseudocount(self):
        site_ndvi={(f"site{i}",2011):i/100 for i in range(20)}
        cells={}
        source_totals=Counter()
        for i in range(20):
            site=f"site{i}"
            # Note: these synthetic camera photos have only one per branch,
            # below the prospectively frozen >=5 each-branch threshold.
            cells[(site,2011,"zebra","rising")]=Counter(core=1)
            cells[(site,2011,"zebra","falling")]=Counter(night=1)
        source_totals[("zebra",2011,"rising")]=100
        source_totals[("zebra",2011,"falling")]=100
        rows=correlations_by_taxon_year(cells,site_ndvi,source_totals)
        z=next(x for x in rows if x["source_taxon"]=="zebra" and x["solstice_cycle_year"]==2011)
        self.assertEqual(z["focal_photo_sites_both_branches_with_at_least_5_events"],0)
        self.assertFalse(z["supported_descriptive_association"])
        self.assertIsNone(z["ndvi_vs_camera_photo_count_log_falling_rising"]["spearman"])

    def test_contract_frozen_before_first_camera_pixels_and_prohibits_causal(self):
        p=ROOT/"research/SERENGETI_SITE_MODIS_NDVI_PHOTO_REWEIGHT_V0_CONTRACT.json"
        c=json.loads(p.read_text())
        self.assertEqual(c["spatial"]["pixel"][:7],"At each")
        self.assertEqual(c["date_calendar"]["site_taxon_admission"].split(" ")[0],"For")
        self.assertEqual(c["date_calendar"]["species"],list(FOCAL))
        self.assertEqual(c["estimands"]["descriptive_correlations"].split(" ")[0],"Spearman")
        self.assertIn("one savanna landscape",c["claim_ceiling"])
        self.assertTrue(c["estimands"]["no_output_per_camera_NDVI"])

if __name__=="__main__": unittest.main()
