import unittest

import pandas as pd

from odsp.continuity import (
    EnvironmentalContinuityConfig,
    environmental_continuity,
    summarize_continuity,
)


class EnvironmentalContinuityTests(unittest.TestCase):
    def setUp(self):
        self.config = EnvironmentalContinuityConfig(
            link_distance_m=150,
            occurrence_anchor_distance_m=100,
            strong_continuity_threshold=0.65,
            weak_continuity_threshold=0.35,
        )

    def test_widest_path_detects_weak_neck(self):
        field = pd.DataFrame({
            "latitude": [34.0000, 34.0010, 34.0020, 34.0030],
            "longitude": [139.0] * 4,
            "candidate_support": [0.9, 0.8, 0.4, 0.9],
        })
        known = pd.DataFrame({"latitude": [34.0], "longitude": [139.0]})
        result = environmental_continuity(field, known, config=self.config)
        self.assertAlmostEqual(float(result.iloc[3].occurrence_continuity), 0.4)
        self.assertEqual(result.iloc[3].environmental_continuity_class, "weak_neck_extension")
        self.assertAlmostEqual(float(result.iloc[3].environmental_bottleneck_depth), 0.5)

    def test_detached_high_support_component_is_not_continuous(self):
        field = pd.DataFrame({
            "latitude": [34.0000, 34.0010, 34.0100, 34.0110],
            "longitude": [139.0] * 4,
            "candidate_support": [0.9, 0.8, 0.9, 0.85],
        })
        known = pd.DataFrame({"latitude": [34.0], "longitude": [139.0]})
        result = environmental_continuity(field, known, config=self.config)
        self.assertEqual(result.iloc[0].environmental_continuity_class, "continuous_environmental_extension")
        self.assertEqual(result.iloc[2].environmental_continuity_class, "detached_environmental_analogue")
        self.assertEqual(float(result.iloc[2].occurrence_continuity), 0.0)

    def test_support_value_alone_does_not_determine_class(self):
        field = pd.DataFrame({
            "latitude": [34.0000, 34.0010, 34.0020, 34.0100],
            "longitude": [139.0] * 4,
            "candidate_support": [0.9, 0.9, 0.9, 0.9],
        })
        known = pd.DataFrame({"latitude": [34.0], "longitude": [139.0]})
        result = environmental_continuity(field, known, config=self.config)
        self.assertEqual(result.iloc[2].environmental_continuity_class, "continuous_environmental_extension")
        self.assertEqual(result.iloc[3].environmental_continuity_class, "detached_environmental_analogue")

    def test_summary_and_validation(self):
        field = pd.DataFrame({
            "latitude": [34.0000, 34.0010],
            "longitude": [139.0, 139.0],
            "candidate_support": [0.9, 0.8],
        })
        known = pd.DataFrame({"latitude": [34.0], "longitude": [139.0]})
        result = environmental_continuity(field, known, config=self.config)
        summary = summarize_continuity(result)
        self.assertEqual(int(summary.node_count.sum()), 2)
        with self.assertRaises(ValueError):
            EnvironmentalContinuityConfig(weak_continuity_threshold=0.8, strong_continuity_threshold=0.5).validate()


if __name__ == "__main__":
    unittest.main()
