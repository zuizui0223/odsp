from __future__ import annotations

import json
from pathlib import Path


PLAN = Path("ODSP_TRAINING_SOURCE_PROCESS_V0_EVIDENCE_PLAN.json")


def test_source_v0_evidence_plan_is_frozen_before_future_receipts():
    payload = json.loads(PLAN.read_text(encoding="utf-8"))
    assert payload["planned_route_key"].endswith(
        "upstream_refits=predeclared_training_source_process|"
        "external_validation=none|contrast_count=2"
    )
    assert payload["future_receipts_not_yet_observed_at_freeze"] == [
        "TRAINING_SOURCE_PROCESS_V0_MANAGED_FOCUSED_RECEIPT.json",
        "TRAINING_SOURCE_PROCESS_V0_QUALIFICATION_IDENTITY_RECEIPT.json",
    ]
    assert payload["registration_boundary"]["route_not_registered_by_this_plan"] is True
    assert payload["registration_boundary"]["artifact_sha256_snapshot_required_before_route_registration"] is True


def test_source_v0_evidence_plan_selects_only_final_correction_contracts():
    payload = json.loads(PLAN.read_text(encoding="utf-8"))
    evidence = payload["ordered_evidence_artifacts"]
    assert "ODSP_TRAINING_SOURCE_PROCESS_V0_MANAGED_INTERNAL_VALIDATION_CONTRACT_V4.json" in evidence
    assert "ODSP_TRAINING_SOURCE_PROCESS_V0_PRIMARY_PROMOTION_GATE_V5.json" in evidence
    assert "ODSP_TRAINING_SOURCE_PROCESS_V0_QUALIFICATION_IDENTITY_CONTRACT_V2.json" in evidence
    assert "ODSP_TRAINING_SOURCE_PROCESS_V0_MANAGED_INTERNAL_VALIDATION_CONTRACT_V3.json" not in evidence
    assert "ODSP_TRAINING_SOURCE_PROCESS_V0_PRIMARY_PROMOTION_GATE_V4.json" not in evidence
