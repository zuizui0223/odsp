"""Solar elevation sensitivity: retain all original sources and one source study block."""
import unittest
from scripts.summarize_solar_altitude_conditional_48_source_v0 import (
    source_study_equal_effect, full_study_source_summary,cluster_ci
)
from scripts.run_solar_altitude_conditioned_48_original_studies_v0 import (
    fixed_original_study_roster
)


def synthetic_study(item, adjusted=None):
    result={
        "source_package_uuid":item["source_uuid"],
        "cohort":item["cohort"],
        "original_study_ids":item["study_id"],
        "original_native_taxa":[item["native_eligible_taxa"][0]],
        "original_provider_MD5_verified":True,
        "all_native_original_GPS_effects_replayed_before_ERA5":True,
        "siteyear_contexts":[]
    }
    if adjusted is not None:
        result["siteyear_contexts"]=[{
            "taxon":item["native_eligible_taxa"][0],
            "source_status":"GEOMETRY_ADJUSTED_GROUP_OBSERVED",
            "source_previous_irradiance_slope_per_100Wm2":.06,
            "original_animal_shortwave_slope_replayed":True,
            "geometric_solar_adjustment_effect":{
                "mean_slope_per100_Wm2":adjusted,
                "source_animal_n":6}
        }]
    else:
        result["siteyear_contexts"]=[{
            "taxon":item["native_eligible_taxa"][0],
            "source_status":"SUN_GEOMETRY_SOURCE_ANIMAL_SUPPORT_HOLD",
            "source_previous_irradiance_slope_per_100Wm2":.06,
            "original_animal_shortwave_slope_replayed":True,
            "geometric_solar_adjustment_effect":{
                "mean_slope_per100_Wm2":None,
                "source_animal_n":1}
        }]
    return result


class FullSourceAltitudeSensitivity(unittest.TestCase):

    def test_one_original_study_not_weather_grid_or_replicate_animal(self):
        selected,_=fixed_original_study_roster()
        d=synthetic_study(selected[0][0],.05)
        d["siteyear_contexts"].append({
            "taxon":d["original_native_taxa"][0],
            "source_status":"GEOMETRY_ADJUSTED_GROUP_OBSERVED",
            "source_previous_irradiance_slope_per_100Wm2":.06,
            "original_animal_shortwave_slope_replayed":True,
            "geometric_solar_adjustment_effect":{"mean_slope_per100_Wm2":-.03,
                                                  "source_animal_n":11}
        })
        s=source_study_equal_effect(d)
        self.assertAlmostEqual(s["source_adjusted_equal_taxon_siteyear_mean_per100Wm2"],.01)
        self.assertEqual(s["original_contexts_solar_altitude_adjusted"],2)
        self.assertEqual(s["original_radiation_contexts_replayed_first_weather"],2)

    def test_weather_and_solar_unidentified_are_holds_not_effect_zero(self):
        selected,_=fixed_original_study_roster()
        s=source_study_equal_effect(synthetic_study(selected[0][0],None))
        self.assertIsNone(s["source_adjusted_equal_taxon_siteyear_mean_per100Wm2"])
        self.assertEqual(s["original_radiation_contexts_replayed_first_weather"],1)
        self.assertEqual(s["original_contexts_solar_altitude_adjusted"],0)

    def test_study_bootstrap_constant_and_source_min_n(self):
        self.assertIsNone(cluster_ci([.02]*5))
        self.assertEqual(cluster_ci([.02]*6),[.02,.02])

    def test_48_source_unavailable_preserved_and_prior_nonreplication_not_reclassified(self):
        selected,held=fixed_original_study_roster()
        data={"all_source_results":[
            synthetic_study(row,(-.01 if row["cohort"]=="earlier" else +.01))
            for row,_,_ in selected
        ]}
        out=full_study_source_summary(data)
        self.assertEqual(out["all_original_source_archives"],48)
        self.assertEqual(out["prior_radiation_identifiable_studies_selected_for_geometry"],20)
        self.assertEqual(out["previously_original_unidentifiable_studies_retained"],28)
        self.assertEqual(out["per_prior_source_cohort"]["earlier"]["geometry_adjusted_radiation_source_archives"],10)
        self.assertEqual(out["per_prior_source_cohort"]["external"]["geometry_adjusted_radiation_source_archives"],10)
        self.assertEqual(out["new_geometry_adjusted_between_original_cohort_mean_difference"],-.02)
        self.assertEqual(out["frozen_previous_signed_radiation_replication_decision_UNCHANGED"],
                         "NEGATIVE_DIRECTION_NOT_REPLICATED_IN_HELDOUT_SOURCE_SAMPLE")

    def test_missing_original_source_prevents_false_global_results(self):
        selected,held=fixed_original_study_roster()
        data={"all_source_results":[synthetic_study(row,.04) for row,_,_ in selected[:-1]]}
        with self.assertRaisesRegex(ValueError,"48"):
            full_study_source_summary(data)


if __name__=="__main__":
    unittest.main()
