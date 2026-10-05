from __future__ import annotations
import json
from pathlib import Path

FOCUSED=Path("TRAINING_PROCESS_V5_EXTERNAL_FOCUSED_ENDPOINT_RECEIPT.json")
IDENTITY=Path("TRAINING_PROCESS_V5_EXTERNAL_ENDPOINT_IDENTITY_RECEIPT.json")

def test_external_focused_endpoint_receipt_is_success_and_fail_closed():
    p=json.loads(FOCUSED.read_text(encoding="utf-8"))
    assert p["official_run"]["github_actions_run_id"] == 37266129747
    assert p["official_run"]["focused_test_step_conclusion"] == "success"
    assert p["official_run"]["identity_snapshot_step_conclusion"] == "success"
    assert all(p["required_failure_modes"].values())
    assert p["boundary"]["internal_v5_operating_characteristics_reused_unchanged"] is True
    assert p["boundary"]["fixed_set_results_reclassified"] is False

def test_external_identity_receipt_locks_endpoint_and_internal_route():
    p=json.loads(IDENTITY.read_text(encoding="utf-8"))
    assert p["first_snapshot_run"]["qualification_pass"] is True
    assert p["first_snapshot_run"]["github_actions_run_id"] == 37266129747
    assert p["canonical_surface"] == (
        "odsp.training_process_untouched_external_v5."
        "run_untouched_external_training_process_v5"
    )
    paths=[row["path"] for row in p["implementation_source_snapshot"]]
    assert "odsp/training_process_untouched_external_v5.py" in paths
    assert "odsp/training_process_managed_external_scoring.py" in paths
    assert "odsp/training_process_external_freeze_v1.py" in paths
    assert len(paths) == len(set(paths)) == 24
    route=p["internal_v5_route_snapshot"]
    assert route["role"] == "primary_confirmatory"
    assert route["qualification_registry_id"] == "odsp-confirmatory-route-evidence-v4"
    assert len(route["qualification_evidence_artifacts"]) == 10
    assert p["runtime_environment_snapshot"]["distributions"] == [
        {"name":"numpy","version":"2.5.3"}
    ]
    assert p["summary"]["external_contract_content_frozen"] is True
