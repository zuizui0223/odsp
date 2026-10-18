"""Synthetic-only GPS solar/night movement-score and source duty-cycle controls."""
from collections import Counter
from datetime import datetime,date,timedelta
import json
import math
from pathlib import Path
import unittest

from scripts.run_2025_seven_duck_gps_solar_matched_speed_v0 import (
    SUN_APPARENT_ZENITH_DEGREES,
    is_daylight_at_GPS_UTC,modeled_photoperiod_minutes,
    one_to_one_source_datepairs,balanced_pair,
    night_minus_day_median_log1p,species_summary,
    MIN_MATCHED_DATES_PER_GROUP
)
ROOT=Path(__file__).resolve().parents[1]

class TestMatchedSolarSourceMovement(unittest.TestCase):
    def test_solar_zenith_classification_at_greenwich(self):
        self.assertTrue(is_daylight_at_GPS_UTC(datetime(2020,3,20,12),0,0))
        self.assertFalse(is_daylight_at_GPS_UTC(datetime(2020,3,20,0),0,0))
        self.assertTrue(is_daylight_at_GPS_UTC(datetime(2021,1,15,12),50,0))
        self.assertFalse(is_daylight_at_GPS_UTC(datetime(2021,1,15,23),50,0))
        self.assertEqual(SUN_APPARENT_ZENITH_DEGREES,90.833)

    def test_daylength_summer_winter_and_cross_solstice(self):
        dec=modeled_photoperiod_minutes(date(2020,12,21),45)
        june=modeled_photoperiod_minutes(date(2021,6,21),45)
        self.assertTrue(480<dec<550)
        self.assertTrue(850<june<1000)
        self.assertLess(dec,june)

    def test_fixed_matched_dates_once_each_and_source_duty_balance(self):
        sol=date(2020,12,21)
        payload={}
        for k in range(7,12):
            f=sol-timedelta(days=k)
            r=sol+timedelta(days=k)
            payload[("falling",f)]={"day":[math.log1p(1)]*6,"night":[math.log1p(7)]*6}
            payload[("rising",r)]={"day":[math.log1p(1)]*6,"night":[math.log1p(1)]*6}
        pairs,_=one_to_one_source_datepairs(payload,45)
        self.assertEqual(len(pairs),MIN_MATCHED_DATES_PER_GROUP)
        self.assertEqual(len({f for f,r,d in pairs}),len(pairs))
        self.assertEqual(len({r for f,r,d in pairs}),len(pairs))
        effects=[
            night_minus_day_median_log1p(payload[("falling",f)])
            -night_minus_day_median_log1p(payload[("rising",r)])
            for f,r,d in pairs
        ]
        self.assertTrue(all(abs(v-math.log(4))<1e-8 for v in effects))

    def test_night_or_day_gps_speed_sample_gap_must_not_fake_an_effect(self):
        a={"day":[0]*3,"night":[0]*10}
        b={"day":[0]*10,"night":[0]*10}
        self.assertFalse(balanced_pair(a,b))
        a={"day":[0]*6,"night":[0]*6}
        self.assertTrue(balanced_pair(a,b))

    def test_distinct_individual_not_photo_event_weight(self):
        r=species_summary({"animal1":-.3,"animal2":-.1,"animal3":.2,"animal4":.1,"animal5":.3})
        self.assertEqual(r["n_distinct_independent_individuals"],5)
        self.assertEqual(r["individuals_positive_delta"],3)
        self.assertEqual(r["individuals_negative_delta"],2)
        self.assertTrue(r["species_descriptive_support_qualified"])
        self.assertIsNotNone(r["leave_one_animal_out_species_mean_range_NOT_confidence_interval"])

    def test_registered_external_source_not_camera_outcome(self):
        c=json.loads((ROOT/"research/DUCK_GPS_2025_SOLAR_MATCHED_SPEED_V0_CONTRACT.json").read_text())
        self.assertIn("294,683",c["status"])
        self.assertEqual(c["source"]["source_fix_rows"] if "source_fix_rows" in c["source"] else c["source"]["source_GPS_fix_rows"],294683)
        self.assertIn("5 minutes",c["unit"]["daylength"])
        self.assertTrue(any("Different observation modality" in s for s in c["sensitivity_and_limit"]))

if __name__=="__main__":unittest.main()
