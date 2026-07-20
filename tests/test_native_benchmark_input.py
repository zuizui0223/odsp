import json
import tempfile
import unittest
from pathlib import Path

import pandas as pd

from odsp.benchmark_input import discover_native_benchmark_units, load_native_benchmark_unit


class NativeBenchmarkInputTests(unittest.TestCase):
    def _write_unit(self, root: Path, *, frozen: bool = True) -> Path:
        unit = root / "unit-a"
        unit.mkdir()
        (unit / "unit.json").write_text(json.dumps({
            "taxon": "Example species",
            "region": "Izu",
            "fold_id": "1",
            "support_method": "independent_kernel_support",
            "support_frozen_before_holdout": frozen,
        }))
        pd.DataFrame({"latitude": [34.0], "longitude": [139.0]}).to_csv(unit / "training_occurrences.csv", index=False)
        pd.DataFrame({"latitude": [34.01, 34.011], "longitude": [139.0, 139.0], "candidate_support": [0.8, 0.7]}).to_csv(unit / "candidate_support.csv", index=False)
        pd.DataFrame({"latitude": [34.01], "longitude": [139.0]}).to_csv(unit / "held_out_occurrences.csv", index=False)
        return unit

    def test_loads_without_producer_specific_fields(self):
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            unit = self._write_unit(root)
            loaded = load_native_benchmark_unit(unit)
            self.assertEqual(loaded.provenance["support_method"], "independent_kernel_support")
            self.assertNotIn("acsp", loaded.provenance)
            self.assertEqual(discover_native_benchmark_units(root), [unit])

    def test_rejects_support_not_frozen_before_holdout(self):
        with tempfile.TemporaryDirectory() as temp:
            unit = self._write_unit(Path(temp), frozen=False)
            with self.assertRaisesRegex(ValueError, "frozen before"):
                load_native_benchmark_unit(unit)


if __name__ == "__main__":
    unittest.main()
