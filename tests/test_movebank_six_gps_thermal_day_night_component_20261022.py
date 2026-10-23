"""Synthetic known-truth guards: original paired DATE/source and βN−βD."""
from datetime import date,timedelta
import json
import math
from pathlib import Path
import unittest

from scripts.movebank_six_gps_thermal_day_night_component_20261022 import (
    LABELS, paired_source_day_night, pair_replay, archived_daily_weather,
    year_slopes, summarize_original_animals, CONTRACT
)

from scripts.movebank_six_gps_thermal_day_night_component_20261022 import (
    individual_nested_component_summary
)
from scripts.movebank_six_source_within_animal_era5_canonical_v1 import canonical_bytes
import hashlib

class TestOriginalGpsDayNightClimateSlopes(unittest.TestCase):
    def test_frozen_six_old_results_and_after_outcome_caveat(self):
        p=json.loads(CONTRACT.read_text(encoding="utf-8"))
        self.assertEqual(p["original_total_individual_animals"],197)
        self.assertEqual(tuple(p["cohorts"]),LABELS)
        self.assertEqual(sum(p["original_group_n_animals"].values()),197)
        self.assertIn("POST-RESULT",p["timing"])
        self.assertTrue(p["estimand"]["no_p_values"])
        self.assertEqual(len(p["original_group_relative_night_OLS_slope"]),6)

    def test_pair_dates_and_relative_components_cannot_drift(self):
        a,b=date(2020,4,1),date(2020,8,29)
        orig=[[[ (a,b,.2), (a+timedelta(days=1),b+timedelta(days=1),-.1) ]]]
        new=[[[ (a,b,.2,.1,.3),
                (a+timedelta(days=1),b+timedelta(days=1),-.1,.1,0) ]]]
        self.assertTrue(pair_replay(orig,new))
        wrong=[[[ (a,b,.2,.1,.4),
                 (a+timedelta(days=1),b+timedelta(days=1),-.1,.1,0) ]]]
        with self.assertRaisesRegex(ValueError,"HOLD_NIGHT_MINUS_DAY_COMPONENT_IDENTITY"):
            pair_replay(orig,wrong)
        changed=[[[ (a,b+timedelta(days=3),.2,.1,.3),
                   (a+timedelta(days=1),b+timedelta(days=1),-.1,.1,0) ]]]
        with self.assertRaisesRegex(ValueError,"HOLD_OLD_GPS_DATE_PAIR"):
            pair_replay(orig,changed)

    def test_algebra_individual_year_absolute_source_decomposition(self):
        # Same days used in relative and absolute responses.
        # Make 12 original date pairs with varying source T and water.
        rising=date(2020,1,8)
        falling=date(2020,9,8)
        points=[]
        weather={}
        for k in range(-30,40):
            weather[rising+timedelta(days=k)]=(2.0,.3,.1)
            weather[falling+timedelta(days=k)]=(2.0,.3,.1)
        for i in range(12):
            a,b=rising+timedelta(days=i),falling+timedelta(days=i)
            # delta T is i+1; N = 4 * delta T, D = delta T
            weather[b]=(2.0+i+1,.3,.1)
            points.append((a,b,float(3*(i+1)),float(i+1),float(4*(i+1))))
        r=year_slopes(points,weather)
        temp=r["temp_C"]
        self.assertIsNotNone(temp["relative"])
        self.assertAlmostEqual(temp["relative"],temp["night"]-temp["day"],places=12)
        # water contrast is zero; undefined by frozen source SD rule.
        self.assertIsNone(r["water_per_100mm"]["relative"])

    def test_empty_and_single_source_animals_are_not_bootstrap_CIs(self):
        a=summarize_original_animals([0.1,-0.1,None])
        self.assertEqual(a["original_animals"],3)
        self.assertEqual(a["admitted_animal_slope"],2)
        self.assertEqual(a["undefined_animal_slope"],1)
        self.assertEqual((a["positive"],a["negative"],a["zero"]),(1,1,0))
        self.assertEqual(a["leave_one_animal_out_mean_min_max_NOT_CI"],[-.1,.1])
        b=summarize_original_animals([None,None])
        self.assertIsNone(b["mean"])
        self.assertIsNone(b["leave_one_animal_out_mean_min_max_NOT_CI"])

    def test_archive_daily_source_science_hash_not_metadata(self):
        dates=[(date(2020,1,1)+timedelta(days=i)).isoformat() for i in range(31)]
        core={"latitude":42.5,"longitude":-110.5,"timezone":"Etc/GMT+7",
              "utc_offset_seconds":-25200,"elevation_m":1800.,
              "daily_units":{"temperature_2m_mean":"°C","precipitation_sum":"mm",
                             "et0_fao_evapotranspiration":"mm"},
              "daily":{"time":dates,"temperature_2m_mean":[3.]*31,
                       "precipitation_sum":[1.]*31,
                       "et0_fao_evapotranspiration":[.5]*31}}
        digest=hashlib.sha256(canonical_bytes(core)).hexdigest()
        frame={"status":"PUBLIC_COARSE_ERA5_ORIGINAL_SCIENTIFIC_DAILY_FIELDS_V1",
               "source_groups":[{"cohort_source_label":label,
                  "new_stable_scientific_daily_snapshots":[{
                    **core,"canonical_scientific_source_sha256":digest,
                    "source_url":"https://archive-api.open-meteo.com/v1/archive"
                  }]} for label in LABELS]}
        w,receipts=archived_daily_weather(frame,"mule_deer_wyoming",
                                          {"latitude":42.5,"longitude":-110.5})
        self.assertEqual(len(w),31)
        self.assertEqual(receipts[0]["v1_source_scientific_SHA256"],digest)
        frame["source_groups"][3]["new_stable_scientific_daily_snapshots"][0]["daily"]["temperature_2m_mean"][5]=333.
        with self.assertRaisesRegex(ValueError,"HOLD_ORIGINAL_DAILY_CLIMATE_SCIENTIFIC_SHA_CHANGED"):
            archived_daily_weather(frame,"mule_deer_wyoming",{"latitude":42.5,"longitude":-110.5})

if __name__=="__main__":unittest.main()
