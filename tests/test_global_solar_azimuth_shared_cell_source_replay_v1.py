"""Ensure technical serial recovery cannot change first outcome or expand source roster."""
import unittest
from unittest.mock import patch
from scripts.global_solar_azimuth_shared_cell_source_replay_v1 import (
    fixed_serial_recovery_sources, run_serial,
)
from tempfile import TemporaryDirectory
from pathlib import Path


class OriginalHeldSourceSerialReplayV1(unittest.TestCase):
    def test_five_failed_source_UUIDs_only(self):
        rows=fixed_serial_recovery_sources()
        self.assertEqual(len(rows),5)
        self.assertEqual(len({x["package_uuid"] for x in rows}),5)
        self.assertTrue(all(x["sample_stratum"]=="all_remaining_multitaxon_census"
                            for x in rows))

    @patch("scripts.global_solar_azimuth_shared_cell_source_replay_v1.evaluate_source")
    def test_exactly_one_serial_attempt_per_original_held_source(self,eval_one):
        eval_one.side_effect=lambda item,out: {
            "package_uuid":item["package_uuid"],
            "source_status":"SOURCE_HOLD",
            "shared_taxon_pairs":[{"taxa":["a","b"],"status":"SOURCE_HOLD"}]
        }
        with TemporaryDirectory() as tmp:
            report=run_serial(Path(tmp))
        self.assertEqual(eval_one.call_count,5)
        self.assertEqual(report["preselected_held_source_archives"],5)
        self.assertEqual(report["still_SOURCE_HOLD"],5)
        self.assertEqual(report["supported_same_grid_month_clock_taxon_pairs"],0)
        ids=[x.args[0]["package_uuid"] for x in eval_one.call_args_list]
        self.assertEqual(ids,[x["package_uuid"] for x in fixed_serial_recovery_sources()])


if __name__=="__main__":
    unittest.main()
