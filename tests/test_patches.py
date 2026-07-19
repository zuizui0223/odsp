import unittest
import pandas as pd

from odsp import (
    CandidatePatchConfig,
    OccurrenceConnectivityConfig,
    annotate_occurrence_connectivity,
    build_candidate_patches,
    build_occurrence_patches,
)


class PatchTests(unittest.TestCase):
    def test_occurrence_components(self):
        points = pd.DataFrame({"latitude": [34.0, 34.001, 34.05], "longitude": [139.0, 139.0, 139.0]})
        result = build_occurrence_patches(points, link_distance_m=500)
        self.assertEqual(result.occurrence_patch_id.nunique(), 2)

    def test_connectivity_classes(self):
        known = pd.DataFrame({"latitude": [34.0], "longitude": [139.0]})
        candidates = pd.DataFrame({
            "latitude": [34.004, 34.0042, 34.02, 34.0202, 34.10, 34.1002],
            "longitude": [139.0] * 6,
            "candidate_support": [0.8] * 6,
        })
        patches = build_candidate_patches(
            candidates,
            config=CandidatePatchConfig(support_thresholds=(0.5,), link_distance_m=500, min_patch_members=2),
        )
        annotated = annotate_occurrence_connectivity(
            patches,
            known,
            config=OccurrenceConnectivityConfig(
                occurrence_link_distance_m=500,
                candidate_occurrence_link_distance_m=750,
                near_disconnected_max_distance_m=5000,
            ),
        )
        labels = set(annotated.occurrence_patch_connectivity_class)
        self.assertIn("occurrence_patch_extension", labels)
        self.assertIn("near_disconnected_occurrence_patch", labels)
        self.assertIn("remote_candidate_patch", labels)


if __name__ == "__main__":
    unittest.main()
