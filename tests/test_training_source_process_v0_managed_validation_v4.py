from __future__ import annotations
import json
from pathlib import Path

P=Path("ODSP_TRAINING_SOURCE_PROCESS_V0_MANAGED_INTERNAL_VALIDATION_CONTRACT_V4.json")

def test_source_v0_v4_records_parallel_scoring_correction():
    p=json.loads(P.read_text(encoding="utf-8"))
    c=p["correction"]
    assert c["parallel_cleanup_restore_race_recorded"] is True
    assert c["v3_assumption_that_managed_internal_scoring_remained_deleted_was_false"] is True
    assert c["v3_rewritten"] is False
    assert c["final_canonical_scoring_surface"] == (
        "odsp.training_source_process_managed_internal_scoring."
        "run_managed_training_source_process_scoring_v0"
    )
    assert c["duplicate_training_source_process_managed_scoring_removed"] is True

def test_source_v0_v4_keeps_calibration_unchanged():
    s=json.loads(P.read_text(encoding="utf-8"))["statistical_boundary"]
    assert all(value is False for value in s.values())
