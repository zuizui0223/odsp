"""Fixed six-source GPS×ERA5 ecology: association arithmetic without empirical outcomes."""
import json
import unittest
import math
from datetime import date,timedelta
from pathlib import Path

from scripts.movebank_six_source_within_animal_era5_date_slopes_20261019 import (
    CFG,LABELS,centered_slope,matched_year_climate_original,
    describe_animal_slopes,original_effect_guard,original_cohort_source_configuration,
    MIN_ORIGINAL_PAIRS_PER_YEAR,MIN_WEATHER_COMPLETE_PAIRS
)

class TestMovebankSixWithinAnimalDateClimate(unittest.TestCase):
    def test_all_six_registered_and_unchanged_old_effects(self):
        c=json.loads(CFG.read_text(encoding="utf-8"))
        self.assertEqual(c["source_cohorts"]["labels_fixed"],list(LABELS))
        self.assertEqual(sum(c["source_cohorts"]["original_individual_counts_exact"].values()),197)
        self.assertIn("AFTER",c["epistemic_status"])
        source=original_cohort_source_configuration()
        self.assertEqual(set(source),set(LABELS))
        for k in LABELS:
            self.assertTrue(source[k]["source"]["original_csv_md5"])
            self.assertIn("latitude",source[k]["grid"])
        self.assertEqual(MIN_ORIGINAL_PAIRS_PER_YEAR,10)
        self.assertEqual(MIN_WEATHER_COMPLETE_PAIRS,10)

    def test_known_truth_temperature_slope_and_negative_slope(self):
        a=[(x*1.,x*10.,3*x+2.) for x in range(10)]
        self.assertAlmostEqual(centered_slope(a,"temp_C"),3)
        self.assertAlmostEqual(centered_slope(a,"water_per_100mm"),30)
        b=[(x*1.,x*10.,-x*.5+10.) for x in range(10)]
        self.assertAlmostEqual(centered_slope(b,"temp_C"),-.5)

    def test_low_variation_or_few_dates_prevents_false_association(self):
        data=[(1+(.02 if i%2 else 0),5.*i,float(i)) for i in range(10)]
        self.assertIsNone(centered_slope(data,"temp_C"))
        self.assertIsNotNone(centered_slope(data,"water_per_100mm"))
        self.assertIsNone(centered_slope([(float(i),float(i),float(i)) for i in range(9)],"temp_C"))
        with self.assertRaisesRegex(ValueError,"HOLD_UNREGISTERED"):
            centered_slope([(float(i),float(i),float(i)) for i in range(10)],"world")

    def test_old_GPS_source_replay_hard_stop(self):
        c=json.loads(CFG.read_text())
        expected=c["source_cohorts"]["original_source_effects_exact"]["mule_deer_wyoming"]
        self.assertTrue(original_effect_guard(expected,{"source_individuals":118,"included_calendar_pairs":20991},expected,118))
        with self.assertRaisesRegex(ValueError,"HOLD_PREVIOUS_MAMMAL_GPS_EFFECT_CHANGED"):
            original_effect_guard(expected+0.0001,{"source_individuals":118,"included_calendar_pairs":20991},expected,118)
        with self.assertRaisesRegex(ValueError,"HOLD_PREVIOUS_ANIMAL_COUNT"):
            original_effect_guard(expected,{"source_individuals":119,"included_calendar_pairs":20991},expected,118)

    def test_30day_missingness_not_silently_filled(self):
        d=date(2020,5,1);dates=[d+timedelta(days=i) for i in range(90)]
        weather={day:(float(i),2.,1.) for i,day in enumerate(dates)}
        yearpairs=[(dates[30],dates[60],0.2)]*10
        d0,n0=matched_year_climate_original(yearpairs,weather)
        self.assertEqual(len(d0),10)
        self.assertEqual(n0,0)
        self.assertAlmostEqual(d0[0][0],30)
        self.assertAlmostEqual(d0[0][1],0)
        weather.pop(dates[10])
        d1,n1=matched_year_climate_original(yearpairs,weather)
        self.assertEqual(len(d1),0)
        self.assertEqual(n1,10)

    def test_source_animals_weighted_one_each_and_no_pseudoreplicate_CI(self):
        a=describe_animal_slopes([1.,-2.,None,2.])
        self.assertEqual(a["n_original_animals"],4)
        self.assertEqual(a["n_slope_admitted_animals"],3)
        self.assertEqual((a["positive"],a["negative"],a["n_undefined_animals"]),(2,1,1))
        self.assertAlmostEqual(a["mean"],1/3)
        self.assertEqual(a["leave_one_individual_out_mean_range_NOT_CI"],[-.5,1.5])
        b=describe_animal_slopes([None,None])
        self.assertIsNone(b["mean"])
        self.assertIsNone(b["leave_one_individual_out_mean_range_NOT_CI"])

if __name__=="__main__":
    unittest.main()
