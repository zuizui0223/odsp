import unittest
import pandas as pd

from odsp import (
    CandidatePatchConfig,
    OccurrenceConnectivityConfig,
    annotate_occurrence_connectivity,
    build_candidate_patches,
    build_occurrence_patches,
    cluster_detections,
    connectivity_sensitivity,
    incremental_recovery_summary,
)


class PatchTests(unittest.TestCase):
    def setUp(self):
        self.known = pd.DataFrame({"latitude": [34.0], "longitude": [139.0]})
        self.candidates = pd.DataFrame({
            "latitude": [34.004, 34.0042, 34.02, 34.0202, 34.10, 34.1002],
            "longitude": [139.0] * 6,
            "candidate_support": [0.8] * 6,
        })

    def test_occurrence_components(self):
        points = pd.DataFrame({"latitude": [34.0, 34.001, 34.05], "longitude": [139.0, 139.0, 139.0]})
        result = build_occurrence_patches(points, link_distance_m=500)
        self.assertEqual(result.occurrence_patch_id.nunique(), 2)

    def test_connectivity_classes(self):
        patches = build_candidate_patches(self.candidates, config=CandidatePatchConfig(support_thresholds=(0.5,), link_distance_m=500, min_patch_members=2))
        annotated = annotate_occurrence_connectivity(patches, self.known, OccurrenceConnectivityConfig(500, 750, 5000))
        labels = set(annotated.occurrence_patch_connectivity_class)
        self.assertEqual(labels, {"occurrence_patch_extension", "near_disconnected_occurrence_patch", "remote_candidate_patch"})

    def test_incremental_recovery(self):
        patches = build_candidate_patches(self.candidates, config=CandidatePatchConfig(support_thresholds=(0.5,), link_distance_m=500, min_patch_members=2))
        annotated = annotate_occurrence_connectivity(patches, self.known, OccurrenceConnectivityConfig(500, 750, 5000))
        detections = pd.DataFrame({"latitude": [34.0041, 34.0201], "longitude": [139.0, 139.0]})
        summary = incremental_recovery_summary(annotated, detections, radii_km=(1,))
        self.assertEqual(float(summary.iloc[0].extension_only_recall), 0.5)
        self.assertEqual(float(summary.iloc[0].extension_plus_near_disconnected_recall), 1.0)
        self.assertEqual(float(summary.iloc[0].incremental_recall), 0.5)

    def test_detection_clustering_respects_group(self):
        detections = pd.DataFrame({"island": ["a", "a", "b"], "latitude": [34.0, 34.0001, 34.0], "longitude": [139.0, 139.0, 139.0]})
        clusters = cluster_detections(detections, radius_m=500, group_col="island")
        self.assertEqual(len(clusters), 2)

    def test_sensitivity_frequencies_sum_to_one(self):
        patches = build_candidate_patches(self.candidates, config=CandidatePatchConfig(support_thresholds=(0.5,), link_distance_m=500, min_patch_members=2))
        _, stability = connectivity_sensitivity(patches, self.known, (400, 500), (600, 750), (4000, 5000))
        totals = stability.groupby("candidate_patch_id").class_frequency.sum()
        self.assertTrue((totals.round(12) == 1.0).all())

    def test_invalid_and_empty_inputs(self):
        with self.assertRaises(ValueError):
            CandidatePatchConfig(support_thresholds=()).validate()
        empty = build_occurrence_patches(pd.DataFrame(columns=["latitude", "longitude"]))
        self.assertTrue(empty.empty)


if __name__ == "__main__":
    unittest.main()
