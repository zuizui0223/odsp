from __future__ import annotations

import json
from pathlib import Path


PLAN = Path("ODSP_TRAINING_SOURCE_PROCESS_V0_EVIDENCE_PLAN_V2.json")


def test_source_v0_evidence_plan_v2_adds_only_status_semantics_before_results():
    payload = json.loads(PLAN.read_text(encoding="utf-8"))
    correction = payload["correction"]
    assert correction["raw_numeric_status_metadata_was_corrected_after_v1_plan"] is True
    assert correction["statistical_estimator_or_threshold_changed"] is False
    assert correction["added_evidence_artifact"] == (
        "ODSP_TRAINING_SOURCE_PROCESS_V0_STATUS_SEMANTICS_CONTRACT.json"
    )
    assert payload["future_receipts_not_yet_observed_at_freeze"] == [
        "TRAINING_SOURCE_PROCESS_V0_MANAGED_FOCUSED_RECEIPT.json",
        "TRAINING_SOURCE_PROCESS_V0_QUALIFICATION_IDENTITY_RECEIPT.json",
    ]


def test_source_v0_evidence_plan_v2_keeps_managed_wrapper_as_only_primary_candidate():
    payload = json.loads(PLAN.read_text(encoding="utf-8"))
    boundary = payload["claim_boundary"]
    assert boundary["raw_numeric_method_statistically_qualified"] is True
    assert boundary["raw_numeric_surface_primary"] is False
    assert boundary["managed_wrapper_required_for_primary_route"] is True
    assert payload["registration_boundary"]["route_not_registered_by_this_plan"] is True
