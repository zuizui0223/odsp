from __future__ import annotations

import json
from pathlib import Path

from scripts.run_training_process_v5_external_identity import build_snapshot


FOCUSED = Path("TRAINING_PROCESS_V5_EXTERNAL_FOCUSED_ENDPOINT_RECEIPT_V2.json")
IDENTITY = Path("TRAINING_PROCESS_V5_EXTERNAL_ENDPOINT_IDENTITY_RECEIPT_V2.json")


def test_final_focused_receipt_records_post_refactor_success():
    p = json.loads(FOCUSED.read_text(encoding="utf-8"))
    assert p["official_run"]["github_actions_run_id"] == 37304922796
    assert p["official_run"]["github_actions_job_id"] == 111746184229
    assert p["official_run"]["head_sha"] == (
        "54f6c50213c540246d5ccef9a0a2af077b2c0b9a"
    )
    assert p["official_run"]["focused_test_step_conclusion"] == "success"
    assert p["final_refactors"]["live_routing_self_reference_removed"] is True
    assert p["final_refactors"]["freeze_strictly_precedes_declared_first_access"] is True
    assert p["required_failure_modes"]["nonprospective_declared_first_access_rejected"] is True
    assert p["boundary"]["historical_truth_of_first_access_declaration_machine_proven"] is False


def test_final_identity_receipt_exactly_matches_current_frozen_snapshot():
    p = json.loads(IDENTITY.read_text(encoding="utf-8"))
    current = build_snapshot()
    for field in (
        "schema_version",
        "canonical_surface",
        "implementation_lock_id",
        "implementation_source_snapshot",
        "runtime_environment_lock_id",
        "runtime_environment_snapshot",
        "internal_v5_route_snapshot",
        "external_contract_sha256",
    ):
        assert p[field] == current[field], field

    paths = [row["path"] for row in p["implementation_source_snapshot"]]
    assert "odsp/training_process_internal_qualification_v5.py" in paths
    assert "odsp/confirmatory_method_routing.py" not in paths
    assert "odsp/confirmatory_route_evidence.py" not in paths
    assert p["self_reference_boundary"][
        "future_route_registry_updates_change_this_frozen_endpoint_identity"
    ] is False
    assert p["chronology_boundary"]["declared_first_external_outcome_access_required"] is True
    assert p["first_snapshot_run"]["qualification_pass"] is True
