"""Post-v0 source-access contract controls; no original NDVI/animal values computed."""
import json
import unittest
from pathlib import Path

from scripts.run_serengeti_regional_modis_container_token_v1 import (
    PREVIOUS_PROBE_GOOD_NDVI, PREVIOUS_SOURCE_TERRA_SCENES,
    PUBLIC_TOKEN_ENDPOINT, signed_public_asset, scene_with_public_container_token
)
ROOT=Path(__file__).resolve().parents[1]

class TestPublicOriginalNDVIContainerToken(unittest.TestCase):
    def test_previous_original_source_2012_pixel_receipt_fixed(self):
        self.assertEqual(PREVIOUS_PROBE_GOOD_NDVI,.5484)
        self.assertEqual(PREVIOUS_SOURCE_TERRA_SCENES,83)
        self.assertEqual(PUBLIC_TOKEN_ENDPOINT,
            "https://planetarycomputer.microsoft.com/api/sas/v1/token/"
            "modiseuwest/modis-061-cogs")

    def test_signing_limited_to_public_modis_terra_cogs(self):
        public="https://modiseuwest.blob.core.windows.net/modis-061-cogs/MOD13Q1/21/09/2012017/foo.tif"
        self.assertEqual(signed_public_asset(public,"fake-token"),public+"?fake-token")
        with self.assertRaisesRegex(ValueError,"HOLD_ASSET_OUTSIDE_PUBLIC"):
            signed_public_asset(
                "https://modiseuwest.blob.core.windows.net/private-data/foo.tif",
                "fake-token")
        with self.assertRaisesRegex(ValueError,"HOLD_ASSET_OUTSIDE_PUBLIC"):
            signed_public_asset(
                "https://modiseuwest.blob.core.windows.net/modis-061-cogs/MYD13Q1/21/09/a.tif",
                "fake-token")

    def test_old_query_protocol_not_reclassified(self):
        c=json.loads((ROOT/"research/SERENGETI_MOD13Q1_PUBLIC_TOKEN_V1_SOURCE_ACCESS_CONTRACT.json").read_text())
        self.assertFalse(c["unchanged_science"]["v0_science_modified"])
        self.assertIn("522",c["unchanged_science"]["temporal"])
        self.assertEqual(c["original_first_probe_receipt"]["good_pixels"],9)
        self.assertTrue(c["quality_transaction"].startswith("One container"))

    def test_original_frozen_qa_threshold_reused(self):
        from scripts.run_serengeti_regional_ndvi_mirror_2010_2013_v0 import (
            PAIR_COVERAGE_MIN,MAX_SCENE_AGE
        )
        self.assertEqual(PAIR_COVERAGE_MIN,.6)
        self.assertEqual(MAX_SCENE_AGE,20)

if __name__=="__main__":
    unittest.main()
