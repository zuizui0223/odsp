from __future__ import annotations

import json
from pathlib import Path


GATE = Path("ODSP_TRAINING_SOURCE_PROCESS_V0_PRIMARY_PROMOTION_GATE_V3.json")


def test_source_v0_promotion_v3_normalizes_order_without_relaxing_gate():
    payload = json.loads(GATE.read_text(encoding="utf-8"))
    order = payload["promotion_order"]
    assert order == {
        "statistical_base_and_support_receipts_exist_first": True,
        "managed_nested_generation_provenance_exists_before_validation_scoring": True,
        "validation_freeze_exists_before_outcome_access": True,
        "managed_scoring_and_focused_tests_exist_before_identity_receipt": True,
        "identity_and_evidence_receipts_exist_before_route_registration": True,
        "routing_promotion_occurs_last": True,
    }
    assert payload["registration"]["primary_confirmatory_now"] is False
    assert payload["registration"]["requires_distinct_upstream_mode"] == (
        "predeclared_training_source_process"
    )


def test_source_v0_promotion_v3_keeps_outer_process_claim_narrow():
    payload = json.loads(GATE.read_text(encoding="utf-8"))
    boundary = payload["claim_boundary"]
    assert boundary["outer_source_process_is_conditional_on_frozen_original_source_roster"] is True
    assert boundary["unknown_ecological_source_superpopulation_generalization_claimed"] is False
    assert boundary["individual_future_source_sample_success_probability_claimed"] is False
    assert boundary["qualified_training_process_v5_reclassified"] is False
    assert payload["scope"]["untouched_external"] is False
