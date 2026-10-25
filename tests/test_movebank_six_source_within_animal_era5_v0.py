"""Source-free known-truth tests for mammal individual-year GPS/ERA5 rank association."""
from datetime import date,timedelta
import json
import unittest
from pathlib import Path

from scripts.movebank_six_source_within_animal_era5_associations_v0 import (
    CONTRACT,LABELS,midranks,spearman_paired,year_pairwise_spearman,
    individual_nested_summary,summarize_animals,
    verify_unchanged_first_effects,validate_first_regional_ERA5,source_roster
)

class TestSixSourceWithinYearClimate(unittest.TestCase):
    def test_midrank_ties_and_known_spearman_signs(self):
        self.assertEqual(midranks([2,1,2,3]),[2.5,1,2.5,4])
        self.assertAlmostEqual(spearman_paired(list(range(10)),list(range(10))),1)
        self.assertAlmostEqual(spearman_paired(list(range(10)),list(range(9,-1,-1))),-1)
        self.assertIsNone(spearman_paired(list(range(10)),[2]*10))
        self.assertIsNone(spearman_paired([1,2,3],[1,2,3]))

    def test_weather_source_original_pairs_and_negative_control(self):
        start=date(2020,1,1)
        weather={start+timedelta(days=k):(k*k/100,2+k*k/500,1.)
                 for k in range(230)}
        pairs=[]
        for k in range(12):
            a=start+timedelta(days=40+k)
            b=start+timedelta(days=140+k)
            pairs.append((a,b,k))
        r=year_pairwise_spearman(pairs,weather)
        self.assertEqual(r["original_matched_source_datepairs"],12)
        self.assertEqual(r["qualified_weather_datepairs"],12)
        self.assertTrue(r["year_pair_source_support"])
        self.assertAlmostEqual(r["spearman_source_temperature_vs_relative_night_displacement"],1)
        self.assertAlmostEqual(r["spearman_source_water_vs_relative_night_displacement"],1)
        r=year_pairwise_spearman([(a,b,-v) for a,b,v in pairs],weather)
        self.assertAlmostEqual(r["spearman_source_temperature_vs_relative_night_displacement"],-1)

    def test_source_missing_weather_not_imputed_and_low_support_not_retested(self):
        start=date(2020,1,1)
        weather={start+timedelta(days=k):(k*.05,1.,.5)
                 for k in range(180)}
        pairs=[(start+timedelta(days=45+i),
                start+timedelta(days=140+i),
                float(i)) for i in range(10)]
        # 29-day history of first rising pair partly missing -> incomplete
        for k in range(16,25):
            weather.pop(start+timedelta(days=k))
        r=year_pairwise_spearman(pairs,weather)
        self.assertGreater(r["weather_missing_datepairs"],0)
        self.assertIsNone(r["spearman_source_temperature_vs_relative_night_displacement"])
        r=year_pairwise_spearman(pairs[:7],weather)
        self.assertFalse(r["year_pair_source_support"])

    def test_individual_weighting_and_undefined_years_kept(self):
        start=date(2020,1,1)
        weather={start+timedelta(days=k):(k*k/100,2+k*k/500,1.)
                 for k in range(300)}
        group=[(start+timedelta(days=40+k),
                start+timedelta(days=140+k),float(k)) for k in range(12)]
        reverse=[(a,b,-e) for a,b,e in group]
        mixed=individual_nested_summary([[group,reverse],[group]],weather)
        self.assertEqual(mixed["admissibility"]["original_individual_years"],3)
        self.assertEqual(mixed["temperature_within_animal_year"]["individuals_with_finite_within_year_rho"],2)
        self.assertAlmostEqual(mixed["temperature_within_animal_year"]["rho_mean_over_individuals"],.5)
        self.assertFalse(mixed["temperature_within_animal_year"]["minimum_five_individuals_for_descriptive_source_mean"])

    def test_prior_GPS_and_prior_ERA5_sha_fail_closed(self):
        c=json.loads(CONTRACT.read_text())
        frozen=c["previous_source_results_and_response_raw_SHA"]["mule_deer_wyoming"]
        pairs=[[[(date(2020,3,1),date(2020,9,1),frozen["e"])]] for _ in range(frozen["n"])]
        count={"source_individuals":118,"included_calendar_pairs":118}
        self.assertTrue(verify_unchanged_first_effects(pairs,frozen["e"],count,frozen))
        with self.assertRaisesRegex(ValueError,"HOLD_FIRST_GPS_GROUP_EFFECT_DRIFT"):
            verify_unchanged_first_effects(pairs,frozen["e"]+.001,count,frozen)
        old={"status":"descriptive_coarse_region_weather_link",
             "individuals_with_complete_weather_and_displacement":frozen["n"],
             "mean_falling_minus_rising_regional_temperature_c":frozen["t"],
             "mean_falling_minus_rising_regional_p_minus_et0_30d_mm":frozen["w"],
             "mean_observed_falling_minus_rising_relative_log1p_night_day_speed":frozen["e"],
             "missing_weather_date_pairs":0}
        self.assertTrue(validate_first_regional_ERA5(old,[{"sha256":x} for x in frozen["sha"]],frozen))
        with self.assertRaisesRegex(ValueError,"HOLD_PRIOR_ERA5_SOURCE_BYTES_SHA256_DRIFT"):
            validate_first_regional_ERA5(old,[{"sha256":"invalid"}],frozen)

    def test_source_frame_exactly_six_selected_and_no_animal_p_values(self):
        c=json.loads(CONTRACT.read_text())
        self.assertEqual(c["selected_source_labels"],list(LABELS))
        self.assertEqual(len(LABELS),6)
        self.assertEqual(sum(r["n"] for r in c["previous_source_results_and_response_raw_SHA"].values()),197)
        registry=source_roster()
        self.assertTrue(all(label in registry for label in LABELS))
        self.assertIn("post",c["temporal_order"].lower())
        self.assertIn("No pairwise p-values",c["estimand"]["no_statistical_tests"])
        a=summarize_animals([.3,-.1,None,None,.2],5)
        self.assertEqual(a["individuals_with_finite_within_year_rho"],3)
        self.assertEqual(a["individuals_undefined_or_insufficient"],2)
        self.assertEqual(a["individual_rho_positive"],2)

if __name__=="__main__":
    unittest.main()
