import tempfile
import unittest
from pathlib import Path

import pandas as pd

from odsp.acsp_adapter import ACSPExportLayout, inputs_from_acsp_export, load_frozen_manifest


class ACSPAdapterTests(unittest.TestCase):
    def test_repository_manifest_is_frozen_and_unique(self):
        manifest = load_frozen_manifest("validation/frozen_taxon_region_manifest.csv")
        self.assertEqual(len(manifest), 48)
        self.assertEqual(manifest[["cohort", "pair_id"]].drop_duplicates().shape[0], 48)
        self.assertEqual(set(manifest.taxon_group), {"plant", "animal"})

    def test_complete_export_becomes_ready_input(self):
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            pd.DataFrame({
                "repeat": [0, 0], "latitude": [34.0, 34.01],
                "longitude": [139.0, 139.01], "integrated_support_score": [0.8, 0.7],
            }).to_csv(root / "pair_001_candidates.csv", index=False)
            pd.DataFrame({
                "repeat": [0, 0], "training_latitude": [34.0, 34.001],
                "training_longitude": [139.0, 139.001],
                "heldout_latitude": [34.02, 34.021],
                "heldout_longitude": [139.0, 139.001],
            }).to_csv(root / "pair_001_folds.csv", index=False)
            manifest = pd.DataFrame([{
                "cohort": "test", "pair_id": 1, "status": "predeclared",
                "taxon_group": "plant", "region_name": "Izu",
                "west": 138.8, "south": 34.0, "east": 139.8, "north": 35.0,
                "species_key": 1, "scientific_name": "Example species",
            }])
            adapted = inputs_from_acsp_export(manifest, [ACSPExportLayout(root, "test")])
            self.assertEqual(len(adapted), 1)
            self.assertEqual(adapted[0].audit["status"], "ready")
            self.assertEqual(len(adapted[0].training_occurrences), 2)
            self.assertEqual(len(adapted[0].held_out_occurrences), 2)

    def test_legacy_export_without_coordinates_is_blocked(self):
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            pd.DataFrame({
                "repeat": [0], "latitude": [34.0], "longitude": [139.0],
                "integrated_support_score": [0.8],
            }).to_csv(root / "pair_001_candidates.csv", index=False)
            pd.DataFrame({"repeat": [0], "all_heldout_ids": ["a;b"]}).to_csv(
                root / "pair_001_folds.csv", index=False
            )
            manifest = pd.DataFrame([{
                "cohort": "test", "pair_id": 1, "status": "predeclared",
                "taxon_group": "plant", "region_name": "Izu",
                "west": 138.8, "south": 34.0, "east": 139.8, "north": 35.0,
                "species_key": 1, "scientific_name": "Example species",
            }])
            adapted = inputs_from_acsp_export(manifest, [ACSPExportLayout(root, "test")])
            self.assertEqual(adapted[0].audit["status"], "blocked_incomplete_legacy_export")
            self.assertFalse(adapted[0].audit["coordinate_complete"])


if __name__ == "__main__":
    unittest.main()
