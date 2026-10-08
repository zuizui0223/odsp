from __future__ import annotations

import json
from pathlib import Path


GATE = Path("ODSP_TRAINING_PROCESS_V5_MANAGED_INTERNAL_PROMOTION_GATE_V2.json")


def test_managed_internal_promotion_v2_freezes_order_before_registry_change():
    p = json.loads(GATE.read_text(encoding="utf-8"))
    assert p["schema_version"] == 2
    assert p["required_order"][-2:] == [
        "route evidence registry updated only after both receipts exist",
        "confirmatory method routing switched only after updated evidence chain is content-locked",
    ]
    failure = p["focused_failure_modes_required"]
    assert failure["happy_path_freezes_validation_design_before_outcome_file_creation"] is True
    assert failure["generated_model_byte_tampering_rejected"] is True
    assert failure["scoring_code_byte_tampering_rejected"] is True
    assert failure["managed_scoring_receipt_tampering_rejected"] is True
    assert failure["equal_or_earlier_declared_first_validation_access_rejected"] is True


def test_managed_internal_promotion_v2_does_not_overclaim_semantics():
    p = json.loads(GATE.read_text(encoding="utf-8"))
    semantics = p["promotion_semantics"]
    assert semantics["statistical_method_changes"] is False
    assert semantics["process_mean_estimand_changes"] is False
    assert semantics["caller_supplied_score_tensor_is_not_primary_input_after_promotion"] is True
    assert semantics["semantic_use_of_model_and_validation_inputs_cryptographically_proven"] is False
    external = p["external_route_boundary"]
    assert external["untouched_external_primary_surface_changed"] is False
    assert external["external_route_evidence_chain_rewritten"] is False
