"""Independent known-truth source/math gates. No live animal or satellite fetch."""
import json
import math
from pathlib import Path
import tempfile
import unittest

from scripts.run_serengeti_modis_relative_greenness_photo_v0 import (
    COVARIATES,OUTCOMES,YEARS,FOCAL,OLD_NDVI_CAMERA_PHOTO_SHA,
    prior_source_receipt,camera_relative_rank_change,
    rho_leave_one_out,REQUIRED_FIRST_SUPPORTED
)

ROOT=Path(__file__).resolve().parents[1]

class TestSeasonalAbsoluteGreennessVsRelativeRank(unittest.TestCase):
    def test_constant_greenup_for_all_sites_preserves_site_rank(self):
        sample={
            (f"s{i}",2011):{"rising":i*.02,"falling":i*.02+.12}
            for i in range(20)
        }
        n=camera_relative_rank_change(sample,2011)
        self.assertEqual(n,20)
        self.assertTrue(all(x["relative_rank_shift"]==0 for x in sample.values()))
        self.assertTrue(all(x["falling"]>x["rising"] for x in sample.values()))

    def test_all_positive_greening_can_still_change_relative_rank(self):
        sample={
            ("s0",2011):{"rising":.20,"falling":.31},
            ("s1",2011):{"rising":.23,"falling":.28},
            ("s2",2011):{"rising":.26,"falling":.40}
        }
        self.assertEqual(camera_relative_rank_change(sample,2011),3)
        self.assertAlmostEqual(sample[("s1",2011)]["relative_rank_shift"],-.5)
        self.assertAlmostEqual(sample[("s0",2011)]["relative_rank_shift"],+.5)
        self.assertAlmostEqual(sum(v["relative_rank_shift"] for v in sample.values()),0)
        self.assertTrue(all(v["falling"]-v["rising"]>0 for v in sample.values()))

    def test_rho_identifies_perfect_agreement_but_no_inferential_p_value(self):
        n=20
        a=list(range(n))
        self.assertAlmostEqual(rho_leave_one_out(a,a)["rho"],1)
        self.assertAlmostEqual(rho_leave_one_out(a,a[::-1])["rho"],-1)
        self.assertIsNone(rho_leave_one_out(a,[1]*n)["rho"])
        self.assertIsNone(rho_leave_one_out(a[:8],a[:8])["rho"])

    def test_only_original_three_taxon_years_admitted_and_all_six_outcome_cells_returned(self):
        self.assertEqual(len(COVARIATES),3)
        self.assertEqual(len(OUTCOMES),2)
        self.assertEqual(len(FOCAL)*len(YEARS),15)
        self.assertEqual(REQUIRED_FIRST_SUPPORTED,
                         {("zebra",2011):53,("zebra",2012):31,
                          ("wildebeest",2011):27})
        c=json.loads((ROOT/"research/SERENGETI_MODIS_RELATIVE_GREENNESS_V0_CONTRACT.json").read_text())
        self.assertEqual(len(c["fixed_covariates"]),3)
        self.assertEqual(len(c["fixed_observed_outcomes"]),2)
        self.assertIn("after",c["epistemic_status"].lower())
        self.assertEqual(c["frozen_sample"]["years"],list(YEARS))
        self.assertTrue(c["fixed_statistics"]["no_causal_interpretation"])

    def test_previous_source_camera_artifact_checksum_rejects_modified_result(self):
        self.assertEqual(OLD_NDVI_CAMERA_PHOTO_SHA,
                         "b6ed0294d6e4c6277f07ef9327f536c564c33c79265570bf7b37197eb951c25f")
        with tempfile.TemporaryDirectory() as tmp:
            p=Path(tmp)/"mutated.json"
            p.write_text('{"all_original_match_photo_records":38792}')
            with self.assertRaisesRegex(ValueError,"HOLD_20261015_FIRST_CAMERA_NDVI_PHOTO_RECEIPT_CHANGED"):
                prior_source_receipt(p)

if __name__=="__main__":unittest.main()
