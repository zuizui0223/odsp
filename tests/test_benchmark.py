import unittest

import pandas as pd

from odsp import (
    BenchmarkConfig,
    BenchmarkUnit,
    CandidatePatchConfig,
    OccurrenceConnectivityConfig,
    benchmark_status_table,
    evaluate_benchmark_unit,
    summarize_benchmark_cohort,
)


class BenchmarkTests(unittest.TestCase):
    def setUp(self):
        self.unit = BenchmarkUnit("Example taxon", "example-region", "fold-1")
        self.training = pd.DataFrame({"latitude": [34.0], "longitude": [139.0]})
        self.candidates = pd.DataFrame(
            {
                "latitude": [34.004, 34.0042, 34.02, 34.0202],
                "longitude": [139.0] * 4,
                "candidate_support": [0.8] * 4,
            }
        )
        self.held_out = pd.DataFrame(
            {"latitude": [34.0041, 34.0201], "longitude": [139.0, 139.0]}
        )
        self.config = BenchmarkConfig(
            candidate_patch=CandidatePatchConfig(
                support_thresholds=(0.5,),
                link_distance_m=500,
                min_patch_members=2,
            ),
            connectivity=OccurrenceConnectivityConfig(500, 750, 5000),
            holdout_cluster_radius_m=100,
            recovery_radii_km=(1.0,),
        )

    def test_incremental_recovery_unit(self):
        metrics, annotated, clusters = evaluate_benchmark_unit(
            self.unit,
            self.training,
            self.candidates,
            self.held_out,
            config=self.config,
        )
        self.assertEqual(metrics.iloc[0].status, "ok")
        self.assertEqual(float(metrics.iloc[0].extension_only_recall), 0.5)
        self.assertEqual(
            float(metrics.iloc[0].extension_plus_near_disconnected_recall), 1.0
        )
        self.assertEqual(float(metrics.iloc[0].incremental_recall), 0.5)
        self.assertEqual(annotated.candidate_patch_id.nunique(), 2)
        self.assertEqual(len(clusters), 2)

    def test_empty_candidates_remain_in_denominator(self):
        empty = pd.DataFrame(columns=["latitude", "longitude", "candidate_support"])
        metrics, _, _ = evaluate_benchmark_unit(
            self.unit,
            self.training,
            empty,
            self.held_out,
            config=self.config,
        )
        self.assertEqual(metrics.iloc[0].status, "no_candidate_patches")
        self.assertEqual(float(metrics.iloc[0].incremental_recall), 0.0)

    def test_failures_remain_in_denominator(self):
        invalid = pd.DataFrame({"latitude": [34.0], "longitude": [139.0]})
        metrics, _, _ = evaluate_benchmark_unit(
            self.unit,
            self.training,
            invalid,
            self.held_out,
            config=self.config,
        )
        self.assertEqual(metrics.iloc[0].status, "failed")
        self.assertEqual(metrics.iloc[0].error_type, "ValueError")

    def test_pair_first_cohort_summary(self):
        rows = []
        for fold, increment in (("a", 1.0), ("b", 0.0)):
            rows.append(
                {
                    "taxon": "t1",
                    "region": "r1",
                    "fold_id": fold,
                    "radius_km": 1.0,
                    "extension_only_recall": 0.0,
                    "extension_plus_near_disconnected_recall": increment,
                    "incremental_recall": increment,
                    "status": "ok",
                }
            )
        rows.append(
            {
                "taxon": "t2",
                "region": "r2",
                "fold_id": "a",
                "radius_km": 1.0,
                "extension_only_recall": 0.0,
                "extension_plus_near_disconnected_recall": 0.0,
                "incremental_recall": 0.0,
                "status": "failed",
            }
        )
        summary = summarize_benchmark_cohort(pd.DataFrame(rows))
        self.assertEqual(int(summary.iloc[0].n_pairs), 2)
        self.assertAlmostEqual(float(summary.iloc[0].incremental_recall_mean), 0.25)
        self.assertEqual(int(summary.iloc[0].n_pairs_positive_increment), 1)

    def test_status_table_has_one_row_per_unit(self):
        metrics, _, _ = evaluate_benchmark_unit(
            self.unit,
            self.training,
            self.candidates,
            self.held_out,
            config=self.config,
        )
        status = benchmark_status_table(metrics)
        self.assertEqual(len(status), 1)
        self.assertEqual(status.iloc[0].fold_id, "fold-1")


if __name__ == "__main__":
    unittest.main()
