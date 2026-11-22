"""Known-truth proof checks for detector-q identified-set arithmetic.

No real biological response values required.
"""
import math
import unittest

from odsp.detector_partial_identification_v5 import (
    bound_at_gamma, curve, gamma_min_for_common_vertical_profile,
    interval_above_fraction, unavoidable_pair_difference,
)


class IdentificationV5Tests(unittest.TestCase):
    def test_original_two_world_observation_table_requires_gamma_nine(self):
        y={"Species_A":{"above":9.0,"below":1.0},
           "Species_B":{"above":1.0,"below":9.0}}
        self.assertAlmostEqual(gamma_min_for_common_vertical_profile(y, alpha=0),9)
        gamma1=bound_at_gamma(y,1,alpha=0)
        self.assertEqual(gamma1["pairs_with_necessarily_different_latent_above_fractions"],1)
        self.assertAlmostEqual(gamma1["max_necessary_pair_absolute_stratum_fraction_difference"],.8)
        self.assertAlmostEqual(gamma1["lower_bound_true_label_layer_mutual_info_nats_conditional_on_model"],.32)
        gamma9=bound_at_gamma(y,9,alpha=0)
        self.assertTrue(gamma9["all_equal_latent_vertical_profiles_possible_given_gamma"])
        self.assertAlmostEqual(gamma9["lower_bound_true_label_layer_mutual_info_nats_conditional_on_model"],0)

    def test_identical_recorded_class_distributions_have_zero_lower_bound(self):
        counts={"a":{"above":2,"below":8},"b":{"above":200,"below":800}}
        self.assertAlmostEqual(gamma_min_for_common_vertical_profile(counts,alpha=0),1)
        for gamma in (1,2,10):
            r=bound_at_gamma(counts,gamma,alpha=0)
            self.assertEqual(r["pairs_with_necessarily_different_latent_above_fractions"],0)
            self.assertAlmostEqual(r["lower_bound_true_label_layer_mutual_info_nats_conditional_on_model"],0)

    def test_unequal_counts_scale_invariant_without_prior(self):
        orig={"a":{"above":1,"below":9},"b":{"above":9,"below":1}}
        scaled={s:{z:20*n for z,n in c.items()} for s,c in orig.items()}
        a=curve(orig,alpha=0,gamma_values=(1,2,5,9,20))
        b=curve(scaled,alpha=0,gamma_values=(1,2,5,9,20))
        self.assertAlmostEqual(a["gamma_min_erase_all_label_profiles_plugin"],
                               b["gamma_min_erase_all_label_profiles_plugin"])
        for av,bv in zip(a["scenario_rows"],b["scenario_rows"]):
            self.assertAlmostEqual(av["lower_bound_true_label_layer_mutual_info_nats_conditional_on_model"],
                                   bv["lower_bound_true_label_layer_mutual_info_nats_conditional_on_model"])

    def test_pair_bound_is_sharp_and_symmetry(self):
        one=interval_above_fraction(9,1,2)
        two=interval_above_fraction(1,9,2)
        self.assertAlmostEqual(unavoidable_pair_difference(one,two),one[0]-two[1])
        self.assertAlmostEqual(unavoidable_pair_difference(two,one),
                               unavoidable_pair_difference(one,two))
        self.assertTrue(0 <= one[0] <= one[1] <= 1)

    def test_zero_count_with_zero_smoothing_fails(self):
        counts={"a":{"above":0,"below":5},"b":{"above":8,"below":2}}
        with self.assertRaisesRegex(ValueError,"positive"):
            bound_at_gamma(counts,2,alpha=0)
        self.assertGreater(gamma_min_for_common_vertical_profile(counts,alpha=.5),1)

    def test_invalid_detector_bounds_rejected(self):
        counts={"a":{"above":9,"below":1},"b":{"above":1,"below":9}}
        with self.assertRaises(ValueError):
            bound_at_gamma(counts,.999)
        with self.assertRaises(ValueError):
            bound_at_gamma(counts,float("nan"))
        with self.assertRaises(ValueError):
            bound_at_gamma(counts,2,alpha=-.5)

    def test_pairwise_overlap_implies_common_intersection(self):
        counts={"a":{"above":9,"below":1},
                "b":{"above":3,"below":7},
                "c":{"above":1,"below":9}}
        threshold=gamma_min_for_common_vertical_profile(counts,alpha=0)
        self.assertGreater(bound_at_gamma(counts,threshold*.99,alpha=0)["pairs_with_necessarily_different_latent_above_fractions"],0)
        self.assertTrue(bound_at_gamma(counts,threshold*1.000001,alpha=0)["all_equal_latent_vertical_profiles_possible_given_gamma"])

if __name__=="__main__":
    unittest.main()
