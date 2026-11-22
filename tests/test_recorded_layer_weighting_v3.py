import math
import unittest

from odsp.recorded_layer_weighting_v3 import observed_two_layer_weighting


class ReferenceWeightingTests(unittest.TestCase):
    def test_same_two_species_equal_mass_measures_match(self):
        v=observed_two_layer_weighting({"s1":(90,10),"s2":(10,90)})
        direct=v["two_layer_mass_weighted"]
        equal=v["two_layer_acoustic_label_equal_weighted"]
        expected=math.log(2)+.9*math.log(.9)+.1*math.log(.1)
        self.assertAlmostEqual(direct["information_nats"],expected,places=12)
        self.assertAlmostEqual(equal["information_nats"],expected,places=12)

    def test_dominant_weak_layer_preference_hides_uncommon_specialists(self):
        c={"ubiquitous":(50000,50000),"low_only":(50,0),"high_only":(0,50)}
        res=observed_two_layer_weighting(c)
        self.assertLess(res["two_layer_mass_weighted"]["information_nats"],.01)
        self.assertGreater(res["two_layer_acoustic_label_equal_weighted"]["information_nats"],.4)
        self.assertGreater(res["label_equal_at_least_20_recorded_events"]["information_nats"],.4)

    def test_gap_only_species_is_not_false_zero_active_layer(self):
        data={"known_high":(0,10),"known_low":(10,0),"gap_only":(0,0)}
        res=observed_two_layer_weighting(data)
        self.assertEqual(res["num_published_or_source_labels"],3)
        self.assertEqual(res["num_active_two_layer_labels"],2)
        self.assertEqual(res["num_zero_both_layer_labels"],1)
        self.assertEqual(res["two_layer_acoustic_label_equal_weighted"]["num_active_acoustic_labels"],2)

    def test_no_information_if_species_layer_conditional_profiles_identical(self):
        res=observed_two_layer_weighting({"s1":(1,3),"s2":(100,300),"s3":(7,21)})
        self.assertAlmostEqual(res["two_layer_mass_weighted"]["information_nats"],0,places=12)
        self.assertAlmostEqual(res["two_layer_acoustic_label_equal_weighted"]["information_nats"],0,places=12)

    def test_no_false_high_dominated_by_single_count_in_guard(self):
        res=observed_two_layer_weighting({"common":(70,30),"rare":(0,1),"other":(30,70)})
        self.assertEqual(res["num_active_two_layer_labels"],3)
        self.assertEqual(res["label_equal_at_least_20_recorded_events"]["num_active_acoustic_labels"],2)

    def test_invalid_source_counts_fail_closed(self):
        with self.assertRaisesRegex(ValueError,"nonnegative"):
            observed_two_layer_weighting({"a":(1,-1),"b":(2,3)})
        with self.assertRaisesRegex(ValueError,"at least two"):
            observed_two_layer_weighting({"a":(0,0),"b":(2,3)})

if __name__=="__main__":
    unittest.main()
