"""Fixture-only QA and immutable NASA STAC science source contract tests."""
import json
import unittest
from pathlib import Path
import numpy as np

from scripts.probe_serengeti_mod13q1_ndvi_cog_v0 import (
    LAT,LON, ITEM_ID, STAC_COLLECTION,NDVI_SCALE,
    good_ndvi_window, verified_item
)
ROOT=Path(__file__).resolve().parents[1]

def item_fake():
    href="https://modiseuwest.blob.core.windows.net/modis-061-cogs/MOD13Q1/21/09/2012017/foo.tif"
    return {
        "id":ITEM_ID,"collection":STAC_COLLECTION,
        "properties":{"platform":"terra",
            "start_datetime":"2012-01-17T00:00:00Z",
            "end_datetime":"2012-02-01T23:59:59Z"},
        "assets":{
            "250m_16_days_NDVI":{"href":href,
                "raster:bands":[{"scale":0.0001}]},
            "250m_16_days_pixel_reliability":{"href":href}
        }
    }

class TestOpenModisNDVISourceProbe(unittest.TestCase):
    def test_correct_source_item_only(self):
        ndvi,qa=verified_item(item_fake())
        self.assertTrue(ndvi.startswith("https://"))
        bad=item_fake();bad["properties"]["platform"]="aqua"
        with self.assertRaisesRegex(ValueError,"HOLD_NOT_TERRA"):verified_item(bad)
        bad=item_fake();bad["assets"]["250m_16_days_NDVI"]["raster:bands"][0]["scale"]=1.
        with self.assertRaisesRegex(ValueError,"HOLD_STAC_NDVI_RASTER_SCALE_CHANGED"):verified_item(bad)

    def test_six_good_required_cloud_never_filled(self):
        n=np.full((3,3),6000,dtype=np.int16)
        qa=np.array([[0,0,0],[0,0,0],[3,2,1]],dtype=np.int8)
        result=good_ndvi_window(n,qa)
        self.assertEqual(result["qa_good_reliability0_raw_valid_pixels"],6)
        self.assertAlmostEqual(result["primary_good_only_median_NDVI"],.6)
        self.assertEqual(result["qa_cloudy3_pixel_count"],1)
        self.assertFalse(result["interpolation_or_marginal_qa_used"])
        qa[0,0]=1
        result=good_ndvi_window(n,qa)
        self.assertIsNone(result["primary_good_only_median_NDVI"])
        self.assertEqual(result["status"],"QA_HOLD_NEED_AT_LEAST_6_GOOD_PIXELS")

    def test_nodata_excluded_even_if_quality_good(self):
        n=np.array([[6000,6000,6000],
                    [6000,-3000,6000],
                    [6000,6000,7000]],dtype=np.int16)
        q=np.zeros((3,3),dtype=np.int8)
        v=good_ndvi_window(n,q)
        self.assertEqual(v["qa_good_reliability0_raw_valid_pixels"],8)
        self.assertAlmostEqual(v["primary_good_only_median_NDVI"],.6)

    def test_quality_shape_is_mandatory(self):
        with self.assertRaisesRegex(ValueError,"HOLD_SATELLITE_WINDOW"):
            good_ndvi_window(np.ones((2,2)),np.ones((2,2)))

    def test_contract_fixed_original_site_privacy_and_quality(self):
        c=json.loads((ROOT/"research/SERENGETI_MOD13Q1_QA_SOURCE_PROBE_V0_CONTRACT.json").read_text())
        self.assertEqual(c["stac_item_id"],ITEM_ID)
        self.assertEqual([c["spatial_frame"]["latitude"],c["spatial_frame"]["longitude"]],[LAT,LON])
        self.assertEqual(c["ndvi_raster"]["scale"],NDVI_SCALE)
        self.assertEqual(c["ndvi_raster"]["require_valid_good_pixels_at_least"],6)
        self.assertFalse(c["spatial_frame"]["publish_original_source_camera_GPS"])
        self.assertTrue(c["temporal_frame"]["no_animal_date_join_in_source_probe"])

if __name__=="__main__":unittest.main()
