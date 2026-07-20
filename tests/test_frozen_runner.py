import json
import tempfile
import unittest
from pathlib import Path

import pandas as pd

from odsp import ACSPExportLayout, BenchmarkConfig, CandidatePatchConfig, OccurrenceConnectivityConfig
from validation.run_frozen_benchmark import parse_layout, run_benchmark


class FrozenBenchmarkRunnerTests(unittest.TestCase):
    def _write_manifest(self, root: Path) -> Path:
        path = root / "manifest.csv"
        pd.DataFrame([
            {
                "cohort": "test", "pair_id": 1, "status": "predeclared",
                "taxon_group": "plant", "region_name": "Izu",
                "west": 138.8, "south": 34.0, "east": 139.8, "north": 35.0,
                "species_key": 1, "scientific_name": "Example species",
            }
        ]).to_csv(path, index=False)
        return path

    def test_parse_layout(self):
        layout = parse_layout("cohort=/tmp/exports")
        self.assertEqual(layout.cohort, "cohort")
        self.assertEqual(layout.root, Path("/tmp/exports"))

    def test_complete_export_writes_metrics_and_summary(self):
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            exports = root / "exports"
            output = root / "results"
            exports.mkdir()
            manifest = self._write_manifest(root)
            pd.DataFrame({
                "repeat": [0, 0, 0, 0],
                "latitude": [34.004, 34.0042, 34.02, 34.0202],
                "longitude": [139.0] * 4,
                "integrated_support_score": [0.8] * 4,
            }).to_csv(exports / "pair_001_candidates.csv", index=False)
            pd.DataFrame({
                "repeat": [0, 0],
                "training_latitude": [34.0, 34.0],
                "training_longitude": [139.0, 139.0],
                "heldout_latitude": [34.0041, 34.0201],
                "heldout_longitude": [139.0, 139.0],
            }).to_csv(exports / "pair_001_folds.csv", index=False)
            config = BenchmarkConfig(
                candidate_patch=CandidatePatchConfig(
                    support_thresholds=(0.5,),
                    link_distance_m=500,
                    min_patch_members=2,
                ),
                connectivity=OccurrenceConnectivityConfig(500, 750, 5000),
                holdout_cluster_radius_m=100,
                recovery_radii_km=(1.0,),
            )
            report = run_benchmark(
                manifest,
                [ACSPExportLayout(exports, "test")],
                output,
                config=config,
            )
            self.assertEqual(report["ready_units"], 1)
            self.assertEqual(report["evaluated_units"], 1)
            self.assertTrue(report["intention_to_evaluate_complete"])
            self.assertTrue((output / "unit_metrics.csv").exists())
            self.assertTrue((output / "cohort_summary.csv").exists())
            saved = json.loads((output / "run_manifest.json").read_text())
            self.assertEqual(saved["metric_rows"], 1)

    def test_incomplete_export_is_retained_in_audit(self):
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            exports = root / "exports"
            output = root / "results"
            exports.mkdir()
            manifest = self._write_manifest(root)
            pd.DataFrame({
                "repeat": [0], "latitude": [34.0], "longitude": [139.0],
                "integrated_support_score": [0.8],
            }).to_csv(exports / "pair_001_candidates.csv", index=False)
            pd.DataFrame({"repeat": [0], "all_heldout_ids": ["a;b"]}).to_csv(
                exports / "pair_001_folds.csv", index=False
            )
            report = run_benchmark(
                manifest,
                [ACSPExportLayout(exports, "test")],
                output,
            )
            self.assertEqual(report["ready_units"], 0)
            self.assertEqual(report["blocked_or_missing_units"], 1)
            self.assertFalse(report["intention_to_evaluate_complete"])
            audit = pd.read_csv(output / "adapter_audit.csv")
            self.assertEqual(audit.iloc[0].status, "blocked_incomplete_legacy_export")
            self.assertFalse((output / "unit_metrics.csv").exists())


if __name__ == "__main__":
    unittest.main()
