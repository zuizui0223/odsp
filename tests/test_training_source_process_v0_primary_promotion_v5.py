from __future__ import annotations

import json
from pathlib import Path


GATE = Path("ODSP_TRAINING_SOURCE_PROCESS_V0_PRIMARY_PROMOTION_GATE_V5.json")
IDENTITY = Path(
    "ODSP_TRAINING_SOURCE_PROCESS_V0_QUALIFICATION_IDENTITY_CONTRACT_V2.json"
)


def test_source_v0_promotion_v5_requires_final_validation_v4_surface():
    payload = json.loads(GATE.read_text(encoding="utf-8"))
    correction = payload["correction"]
    assert correction["v4_required_superseded_validation_v3_and_old_scoring_surface"] is True
    assert correction["v4_rewritten"] is False
    assert correction["final_validation_contract"].endswith(
        "MANAGED_INTERNAL_VALIDATION_CONTRACT_V4.json"
    )
    assert correction["final_canonical_scoring_surface"] == (
        "odsp.training_source_process_managed_internal_scoring."
        "run_managed_training_source_process_scoring_v0"
    )
    assert payload["registration"]["managed_wrapper_primary_now"] is False


def test_source_v0_identity_v2_is_after_final_correction_and_before_routing():
    payload = json.loads(IDENTITY.read_text(encoding="utf-8"))
    order = payload["workflow_order"]
    assert order["final_validation_and_promotion_contracts_exist_before_focused_tests"] is True
    assert order["focused_provenance_tests_before_identity_snapshot"] is True
    assert order["identity_snapshot_before_evidence_content_lock"] is True
    assert order["evidence_content_lock_before_route_registration"] is True
    assert payload["final_promotion_gate"].endswith(
        "PRIMARY_PROMOTION_GATE_V5.json"
    )
