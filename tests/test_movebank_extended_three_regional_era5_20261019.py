"""Independent known-truth gates for extending original GPS + same-date ERA5 to three sources."""
import json
import unittest
from datetime import date,timedelta
from pathlib import Path

from scripts.movebank_extended_three_regional_era5_20261019 import (
    CONTRACT,LABELS,admission,strict_movement_replication,summary_for_source
)
from scripts.movebank_regional_climate_link_20261019 import fixed_timezone,weather_rolling_30

def prior():
    return {
        "label":"mule_deer_wyoming",
        "taxon":"Odocoileus hemionus",
        "doi":"10.5441/001/1.708",
        "status":"exploratory_population_description",
        "eligible_individuals":118,
        "relative_effect":0.03114824366094135,
        "day_component":-0.016573549520154343,
        "night_component":0.014574694140787008
    }

class ExtendedThreeClimateTests(unittest.TestCase):
    def setUp(self):
        self.cfg=json.loads(CONTRACT.read_text(encoding="utf-8"))
        self.src={
            "label":"mule_deer_wyoming","taxon":"Odocoileus hemionus",
            "doi":"10.5441/001/1.708",
            "original_csv_bitstream_uuid":"de7b956a-f5b6-4727-a2cc-a119a1217a68",
            "original_csv_md5":"a8563f71fa6213919812dc0f2da30c26"
        }
        self.prev=prior()
        self.exp=self.cfg["frozen_expected_results"]["mule_deer_wyoming"]
        self.fs={"bitstream_uuid":self.src["original_csv_bitstream_uuid"],
                 "checksum":{"checkSumAlgorithm":"MD5","value":self.src["original_csv_md5"]}}
    def test_cohort_labels_and_prior_effect_exactly_frozen(self):
        self.assertEqual(len(LABELS),3)
        self.assertEqual(LABELS,("mule_deer_wyoming","white_tail_virginia","wolves_alberta"))
        self.assertEqual(self.exp["individuals"],118)
        self.assertEqual(self.cfg["frozen_expected_results"]["white_tail_virginia"]["individuals"],33)
        self.assertEqual(self.cfg["frozen_expected_results"]["wolves_alberta"]["individuals"],9)
        self.assertIn("POST-OUTCOME",self.cfg["timing"])
        self.assertIn("not confirmed",self.cfg["geographic_exposure"]["mule_deer_wyoming"]["description"])
        self.assertTrue(admission(self.src,self.exp,self.prev,self.fs)["original_source_md5_checked"])

    def test_wrong_original_fingerprint_never_admitted(self):
        wrong={**self.fs,"checksum":{"checkSumAlgorithm":"MD5","value":"0"*32}}
        with self.assertRaisesRegex(ValueError,"HOLD_ORIGINAL_PROVIDER_MD5_CHANGED"):
            admission(self.src,self.exp,self.prev,wrong)
        wrong={**self.src,"original_csv_bitstream_uuid":"random"}
        with self.assertRaisesRegex(ValueError,"HOLD_SOURCE_BITSTREAM_ID_CHANGED"):
            admission(wrong,self.exp,self.prev,self.fs)

    def test_prior_outcome_must_match_before_weather(self):
        wrong={**self.prev,"relative_effect":0.02}
        with self.assertRaisesRegex(ValueError,"HOLD_PRIOR_MOVEMENT_OUTCOME_DRIFT"):
            admission(self.src,self.exp,wrong,self.fs)
        good={"source_individuals":118,"included_calendar_pairs":30}
        self.assertTrue(strict_movement_replication(self.exp["relative_log_speed"],good,self.exp))
        with self.assertRaisesRegex(ValueError,"HOLD_ORIGINAL_GPS_EFFECT_RECOMPUTATION_MISMATCH"):
            strict_movement_replication(-.5,good,self.exp)
        with self.assertRaisesRegex(ValueError,"HOLD_ORIGINAL_INDIVIDUAL_SOURCE_COHORT_MISMATCH"):
            strict_movement_replication(self.exp["relative_log_speed"],{"source_individuals":117,"included_calendar_pairs":30},self.exp)

    def test_original_fixed_local_standard_timezone_and_water_30_days(self):
        self.assertEqual(fixed_timezone(-110.5),"Etc/GMT+7")
        self.assertEqual(fixed_timezone(-80.5),"Etc/GMT+5")
        self.assertEqual(fixed_timezone(-116),"Etc/GMT+8")
        base=date(2019,5,1)
        values={base+timedelta(days=i):(float(i),2.,1.) for i in range(66)}
        date0,date1=base+timedelta(days=30),base+timedelta(days=60)
        self.assertEqual(weather_rolling_30(values,date0),(30.,30.))
        result=summary_for_source(
            {"label":"test","status":"HOLD","weather_biological_causality_estimated":False},
            [[[(date0,date1,.4)]]],.4,
            {"source_individuals":1,"included_calendar_pairs":1},
            {"latitude":37.5,"longitude":-80.5,"description":"test public reference"},
            values,[{"source_url":"fake ERA5 source","sha256":"abcd"}])
        self.assertEqual(result["status"],"EXPLORATORY_ORIGINAL_SOURCE_MATCHED_ERA5_CONTEXT")
        self.assertEqual(result["individuals_with_complete_weather_and_displacement"],1)
        self.assertAlmostEqual(result["mean_observed_falling_minus_rising_relative_log1p_night_day_speed"],.4)
        self.assertAlmostEqual(result["mean_falling_minus_rising_regional_temperature_c"],30)
        self.assertEqual(result["mean_falling_minus_rising_regional_p_minus_et0_30d_mm"],0)

    def test_no_location_reconstruction_or_species_level_causal_claim(self):
        c=self.cfg
        self.assertEqual(c["weather"]["model"],"era5")
        self.assertEqual(len(c["frozen_expected_results"]),3)
        self.assertTrue(any("no animal ids" in v.lower() for v in c["source_safety"]))
        self.assertTrue(any("taxon" in v.lower() for v in c["source_safety"]))
        self.assertIn("not soil moisture",c["weather"]["antecedent_water_proxy"])

if __name__=="__main__":
    unittest.main()
