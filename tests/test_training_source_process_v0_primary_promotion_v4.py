from __future__ import annotations

import json
from pathlib import Path


GATE = Path("ODSP_TRAINING_SOURCE_PROCESS_V0_PRIMARY_PROMOTION_GATE_V4.json")


def test_source_v0_promotion_v4_requires_corrected_scoring_contract():
    payload = json.loads(GATE.read_text(encoding="utf-8"))
    required = payload["required_validation_provenance"]
    assert "ODSP_TRAINING_SOURCE_PROCESS_V0_MANAGED_INTERNAL_VALIDATION_CONTRACT_V3.json" in required
    assert (
        "canonical scoring surface is "
        "odsp.training_source_process_managed_scoring."
        "run_managed_training_source_process_scoring_v0"
    ) in required
    assert payload["registration"]["managed_wrapper_primary_now"] is False
    assert payload["registration"]["raw_numeric_surface_primary"] is False


def test_source_v0_promotion_v4_preserves_order_and_narrow_claim():
    payload = json.loads(GATE.read_text(encoding="utf-8"))
    assert payload["promotion_order"] == {
        "statistical_base_and_support_receipts_exist_first": True,
        "process_and_managed_generation_provenance_exist_before_validation_scoring": True,
        "corrected_validation_contract_v3_exists_before_focused_tests": True,
        "focused_tests_pass_before_identity_receipt": True,
        "identity_and_evidence_receipts_exist_before_route_registration": True,
        "routing_promotion_occurs_last": True,
    }
    assert payload["registration"]["requires_distinct_upstream_mode"] == (
        "predeclared_training_source_process"
    )
    boundary = payload["claim_boundary"]
    assert boundary["outer_source_process_is_conditional_on_frozen_original_source_roster"] is True
    assert boundary["unknown_ecological_source_superpopulation_generalization_claimed"] is False
    assert boundary["qualified_training_process_v5_reclassified"] is False
