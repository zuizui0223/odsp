from __future__ import annotations

import json
from pathlib import Path


PLAN = Path("ODSP_TRAINING_SOURCE_PROCESS_V0_EVIDENCE_PLAN_V3.json")


def test_source_v0_evidence_plan_v3_is_final_pre_result_plan():
    payload = json.loads(PLAN.read_text(encoding="utf-8"))
    assert payload["selection_rule"]["this_is_final_pre_result_evidence_plan"] is True
    assert payload["selection_rule"]["future_focused_or_identity_result_may_not_change_artifact_membership"] is True
    evidence = payload["ordered_evidence_artifacts"]
    assert "ODSP_TRAINING_SOURCE_PROCESS_V0_MANAGED_FOCUSED_RECEIPT_CONTRACT.json" in evidence
    assert evidence[-2:] == [
        "TRAINING_SOURCE_PROCESS_V0_MANAGED_FOCUSED_RECEIPT.json",
        "TRAINING_SOURCE_PROCESS_V0_QUALIFICATION_IDENTITY_RECEIPT.json",
    ]


def test_source_v0_evidence_plan_v3_still_fails_closed_before_registration():
    payload = json.loads(PLAN.read_text(encoding="utf-8"))
    assert payload["registration_boundary"]["route_not_registered_by_this_plan"] is True
    assert payload["registration_boundary"]["artifact_sha256_snapshot_required_before_route_registration"] is True
    assert payload["registration_boundary"]["distinct_upstream_mode_required"] == (
        "predeclared_training_source_process"
    )
