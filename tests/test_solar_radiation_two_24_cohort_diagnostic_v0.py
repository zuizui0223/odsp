"""Original-source all-48 nonreplication interpretation, no post hoc recovery claims."""
import json
import unittest
from scripts.analyze_original_solar_radiation_two_cohorts_diagnostic_v0 import (
    diagnose,mean_ci,two_source_set_comparison,source_biological_class,
    sign_pattern,EARLIER,EXTERNAL,EARLIER_CONTEXTS,EXTERNAL_CONTEXTS,CONTRACT
)


class SolarRadiationTwoOriginalSamples(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.first=[json.loads(x.read_text(encoding="utf-8")) for x in
                   (EARLIER,EXTERNAL,EARLIER_CONTEXTS,EXTERNAL_CONTEXTS)]

    def test_full48_unaltered_earlier_and_external_source_denominators(self):
        x=diagnose(*self.first)
        self.assertEqual(x["all_48_previously_frozen_source_studies_included"],48)
        self.assertEqual(x["first_24_and_external_24_original_source_weather_observation_coverages"]
                         ["earlier"]["source_studies_with_shortwave_slope"],10)
        self.assertEqual(x["first_24_and_external_24_original_source_weather_observation_coverages"]
                         ["external"]["source_studies_with_shortwave_slope"],10)
        self.assertEqual(x["prior_frozen_external_replication_decision_UNCHANGED"],
                         "NEGATIVE_DIRECTION_NOT_REPLICATED_IN_HELDOUT_SOURCE_SAMPLE")
        self.assertEqual(len({x["source_package_uuid"] for x in
                              x["all_original_studies_anonymized_source_descriptions"]}),48)

    def test_previous_known_frozen_group_means_and_study_difference(self):
        x=diagnose(*self.first)["study_equal_original_shortwave_slope_two_cohort_difference"]
        self.assertAlmostEqual(x["equal_source_earlier_mean"],-.019658718057344777,places=12)
        self.assertAlmostEqual(x["equal_source_external_mean"],-.0033607359100145946,places=12)
        self.assertAlmostEqual(x["earlier_minus_external_observed_mean_difference"],
                               -.016297982147330183,places=12)
        self.assertLess(x["source_within_sample_bootstrap95_difference"][0],
                        x["source_within_sample_bootstrap95_difference"][1])

    def test_source_bootstraps_and_permutation_are_deterministic(self):
        self.assertEqual(mean_ci([.02]*7,nboot=120),[.02,.02])
        r=two_source_set_comparison([-.02]*6,[.02]*6,nboot=120,nperm=240)
        self.assertAlmostEqual(r["earlier_minus_external_observed_mean_difference"],-.04)
        self.assertEqual(r["source_within_sample_bootstrap95_difference"],[-.04,-.04])
        self.assertTrue(r["Monte_Carlo_two_sided_permutation_reference"]
                        ["NOT_a_valid_randomized_world_source_design_p_value"])

    def test_unsupported_is_never_ecological_zero_and_no_locomotion_reassignment(self):
        x=diagnose(*self.first)
        zero=[p for p in x["all_original_studies_anonymized_source_descriptions"]
              if p["radiation_slope_per_100Wm2"] is None]
        self.assertEqual(len(zero),28)
        self.assertTrue(all(p["ecological_locomotion_class"] is None for p in zero))
        cl=json.loads(CONTRACT.read_text(encoding="utf-8"))
        defs=cl["ecological_interpretation"]["frozen_taxa_groups"]
        self.assertEqual(source_biological_class(["Anser albifrons","Branta leucopsis"],defs),"birds")
        with self.assertRaisesRegex(ValueError,"Unknown"):
            source_biological_class(["A made-up bird"],defs)

    def test_original_within_source_context_signs_never_counted_as_independent_studies(self):
        p=[
            {"within_animal_clock_month_weather_associations":
                 {"shortwave_Wm2":{"mean":-.01}},
             "geographic_latitude_band_not_coordinate":{
                 "hemisphere":"N","absolute_latitude_band_degrees":[30,45]}},
            {"within_animal_clock_month_weather_associations":
                 {"shortwave_Wm2":{"mean":+.01}},
             "geographic_latitude_band_not_coordinate":{
                 "hemisphere":"N","absolute_latitude_band_degrees":[30,45]}}
        ]
        z=sign_pattern(p)
        self.assertEqual(z["within_original_source_study_context_sign_consistency"],
                         "OPPOSITE_SIGN_ACROSS_SELECTED_SOURCE_CONTEXTS")
        self.assertEqual(z["source_observed_hemisphere"],"N")
        self.assertEqual(z["original_source_siteyear_taxon_contexts_with_supported_shortwave_slopes"],2)


if __name__=="__main__":
    unittest.main()
