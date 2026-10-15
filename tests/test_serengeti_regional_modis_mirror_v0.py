"""No satellite or animal results; test frozen mirror NDVI no-forward-leakage and QA gaps."""
import datetime as dt
import json
from pathlib import Path
import unittest
from scripts.run_serengeti_regional_ndvi_mirror_2010_2013_v0 import (
    COLLECTION, source_scene_from_stac, past_completed_qualified_ndvi,
    apply_frozen_522_mirror_pairs, MAX_SCENE_AGE
)
ROOT=Path(__file__).resolve().parents[1]

def fake_scene(sourceid,start,finish,ndvi):
    return {"source_item":sourceid,"start_date":start,"end_date":finish,
            "good_only_NDVI":ndvi}

def all_fake_16d(value=lambda day:.5):
    frames=[]
    day=dt.date(2010,1,1)
    end=dt.date(2013,7,17)
    count=0
    while day<end:
        finish=min(day+dt.timedelta(days=15),end)
        frames.append(fake_scene("synthetic_"+str(count),day.isoformat(),finish.isoformat(),value(day)))
        count+=1
        day+=dt.timedelta(days=16)
    return frames

class TestFullHistoricalRegionalMOD13Q1(unittest.TestCase):
    def test_platform_terra_only_and_quality_asset_scale(self):
        href="https://modiseuwest.blob.core.windows.net/modis-061-cogs/MOD13Q1/21/09/2010017/A.tif"
        stub={
            "id":"MOD13Q1.A2010017.h21v09.061.fake",
            "collection":COLLECTION,
            "properties":{"platform":"terra",
                          "start_datetime":"2010-01-17T00:00:00Z",
                          "end_datetime":"2010-02-01T23:59:59Z"},
            "assets":{
              "250m_16_days_NDVI":{"href":href,"raster:bands":[{"scale":.0001}]},
              "250m_16_days_pixel_reliability":{"href":href}
            }
        }
        item=source_scene_from_stac(stub)
        self.assertEqual(item["start_date"],"2010-01-17")
        stub["properties"]["platform"]="aqua"
        self.assertIsNone(source_scene_from_stac(stub))
        stub["properties"]["platform"]="terra"
        stub["assets"]["250m_16_days_NDVI"]["raster:bands"][0]["scale"]=1.
        with self.assertRaisesRegex(ValueError,"HOLD_NDVI_STAC_SCALE"):
            source_scene_from_stac(stub)

    def test_last_completed_not_future_composite(self):
        scenes=[
            fake_scene("A","2012-01-01","2012-01-16",.15),
            fake_scene("B","2012-01-17","2012-02-01",.88),
        ]
        self.assertEqual(past_completed_qualified_ndvi(scenes,dt.date(2012,1,16)),.15)
        self.assertEqual(past_completed_qualified_ndvi(scenes,dt.date(2012,1,31)),.15)
        self.assertEqual(past_completed_qualified_ndvi(scenes,dt.date(2012,2,1)),.88)

    def test_recent_cloud_blocks_older_good(self):
        scenes=[
            fake_scene("A","2012-01-01","2012-01-16",.15),
            fake_scene("B","2012-01-17","2012-02-01",None),
        ]
        self.assertIsNone(past_completed_qualified_ndvi(scenes,dt.date(2012,2,3)))
        self.assertIsNone(past_completed_qualified_ndvi(scenes,dt.date(2012,2,20)+dt.timedelta(days=MAX_SCENE_AGE)))

    def test_uniform_qualified_ndvi_522_pairs_zero_change(self):
        x=apply_frozen_522_mirror_pairs(all_fake_16d())
        self.assertEqual(x["full_522_calendar_pair_qualified_good_observation_count"],522)
        self.assertTrue(x["three_years_coverage_qualified"])
        for year in x["yearwise"]:
            self.assertEqual(year["paired_ndvi_good_observations"],174)
            self.assertEqual(year["delta_falling_minus_rising_good_NDVI"]["mean"],0)

    def test_cloudy_first_half_year_causes_qa_hold_with_no_rescue(self):
        frames=all_fake_16d(lambda day: None if 2011 <= day.year <= 2012 else .5)
        x=apply_frozen_522_mirror_pairs(frames)
        self.assertFalse(x["three_years_coverage_qualified"])
        self.assertIsNone(x["descriptive_all_years_available_pair_summary"])
        self.assertTrue(any(not y["qualifies_for_regional_descriptive_mean"] for y in x["yearwise"]))

    def test_contract_one_coarse_region_not_animal_site_model(self):
        c=json.loads(
            (ROOT/"research/SERENGETI_REGIONAL_MOD13Q1_NDVI_2010_2013_SEASON_MIRROR_V0_CONTRACT.json").read_text()
        )
        self.assertEqual(c["spatial"]["latitude"],-2.5)
        self.assertEqual(c["temporal"]["NDVI_temporal_alignment"].split(" ")[0],"ONLY")
        self.assertEqual(c["quality"]["good_QA_exact"],0)
        self.assertFalse(c["results"]["no_animal_data_opened"] is False)
        self.assertTrue(c["spatial"]["all_actual_cameras_not_sampled"])

if __name__=="__main__":unittest.main()
