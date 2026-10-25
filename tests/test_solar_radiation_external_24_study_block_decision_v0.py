"""Frozen 24-source heldout solar/radiation sign-decision safeguards."""
import unittest
from scripts.evaluate_external_solar_radiation_24_source_study_blocks_v0 import (
    analyze_external_heldout
)
from scripts.run_solar_radiation_external_24_sources_v0 import verify_external_frozen_frame


def synthetic_external(values):
    _,sources=verify_external_frozen_frame()
    result=[]
    for i,x in enumerate(sources):
        val=values[i] if i<len(values) else None
        if val is None:
            contexts=[]
        else:
            a={k:{"mean":val} for k in (
                "wind_sun_cos","windspeed_ms","shortwave_Wm2","temperature_C")}
            contexts=[{
                "within_animal_clock_month_weather_associations":a,
                "weather_environmental_effect_status":"SOURCE_GROUP_OBSERVED_ENVIRONMENT_DESCRIPTION"
            }]
        result.append({
            "source_package_uuid":x["original_source_package_uuid"],
            "source_study_ids":x["original_repository_study_ids"],
            "original_taxon":x["original_taxon"],
            "source_status":"ORIGINAL_SOURCE_FIRST_GPS_AND_ERA5_OBSERVATIONS_COMPLETED",
            "source_original_GPS_first_directional_result":{
                "supported_individuals":6,
                "results":{"raw_toward_sun_mean_cos":{"mean":.05}}
            },
            "provider_original_source_checksum_receipt":{"provider_checksum_verified":True},
            "source_taxa":[{"taxon":x["original_taxon"],
                            "source_gridyear_weather_contexts":contexts}]
        })
    return {"version":"external-24-original-GPS-solar-radiation-validation-v0",
            "all_external_first_source_results":result}


class ExternalSourceHeldoutRadiation(unittest.TestCase):

    def test_24_unique_original_source_ids_and_predeclared_negative_slope(self):
        c,source=verify_external_frozen_frame()
        self.assertEqual(len(source),24)
        self.assertEqual(c["sample_n_archives"],24)
        self.assertEqual(c["primary_effect_units"].split(" per +100")[1][:4]," W/m")
        self.assertEqual(c["primary_test"].split("only if at least ")[1][:1],"6")

    def test_all_negative_six_source_studies_replicates_by_predeclared_rule(self):
        p=synthetic_external([-.01]*6)
        r=analyze_external_heldout(p)
        assert r["first_external_original_source_study_frame"]==24
        self.assertEqual(r["source_primary_radiation_per_100Wm2"]["supported_original_source_study_IDs"],6)
        self.assertEqual(r["source_primary_radiation_per_100Wm2"]["predeclared_external_replication_decision"],
                         "NEGATIVE_DIRECTION_REPLICATED_IN_HELDOUT_SOURCE_SAMPLE")

    def test_support_below_six_does_not_claim_replication(self):
        p=synthetic_external([-.01]*5)
        r=analyze_external_heldout(p)
        self.assertEqual(r["source_primary_radiation_per_100Wm2"]["predeclared_external_replication_decision"],
                         "INSUFFICIENT_HELDOUT_STUDY_SUPPORT")

    def test_nonnegative_heldout_studies_fail_signed_replication(self):
        p=synthetic_external([+.01]*8)
        r=analyze_external_heldout(p)
        self.assertEqual(r["source_primary_radiation_per_100Wm2"]["predeclared_external_replication_decision"],
                         "NEGATIVE_DIRECTION_NOT_REPLICATED_IN_HELDOUT_SOURCE_SAMPLE")

    def test_no_source_substitution_or_dropped_undefined_studies(self):
        p=synthetic_external([-.01]*9)
        p["all_external_first_source_results"].pop()
        with self.assertRaisesRegex(ValueError,"24"):
            analyze_external_heldout(p)


if __name__=="__main__":
    unittest.main()
