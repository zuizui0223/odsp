from __future__ import annotations
import json
from pathlib import Path

FOCUSED=Path("TRAINING_SOURCE_PROCESS_V0_MANAGED_FOCUSED_RECEIPT.json")
IDENTITY=Path("TRAINING_SOURCE_PROCESS_V0_QUALIFICATION_IDENTITY_RECEIPT.json")

def test_source_v0_focused_receipt_freezes_official_success():
    p=json.loads(FOCUSED.read_text(encoding="utf-8"))
    assert p["official_run"]["github_actions_run_id"] == 37545025741
    assert p["official_run"]["github_actions_job_id"] == 112546858326
    assert p["official_run"]["focused_test_step_conclusion"] == "success"
    assert p["official_run"]["identity_snapshot_step_conclusion"] == "success"
    assert p["summary"]["all_predeclared_required_test_files_passed_together"] is True
    assert p["history"]["required_test_file_removed_after_failure"] is False
    assert p["history"]["statistical_method_changed_after_failure"] is False

def test_source_v0_identity_receipt_locks_managed_surface():
    p=json.loads(IDENTITY.read_text(encoding="utf-8"))
    assert p["first_snapshot_run"]["github_actions_run_id"] == 37545025741
    assert p["first_snapshot_run"]["qualification_pass"] is True
    assert p["canonical_surface"] == (
        "odsp.training_source_process_managed_internal_v0."
        "run_managed_internal_training_source_process_v0"
    )
    paths=[row["path"] for row in p["implementation_source_snapshot"]]
    assert "odsp/training_source_process_managed_internal_v0.py" in paths
    assert "odsp/training_source_process_managed_internal_scoring.py" in paths
    assert "odsp/training_source_process_v0.py" in paths
    assert len(paths) == len(set(paths)) == 25
    assert p["runtime_environment_snapshot"]["python"] == {
        "implementation":"cpython","major":3,"minor":12,"micro":14
    }
    assert p["runtime_environment_snapshot"]["distributions"] == [
        {"name":"numpy","version":"2.5.3"}
    ]
