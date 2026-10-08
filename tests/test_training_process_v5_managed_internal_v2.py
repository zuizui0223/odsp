from __future__ import annotations

import json
from pathlib import Path


VALIDATION = Path(
    "ODSP_TRAINING_PROCESS_V5_MANAGED_INTERNAL_VALIDATION_CONTRACT_V2.json"
)
PROMOTION = Path(
    "ODSP_TRAINING_PROCESS_V5_MANAGED_INTERNAL_PROMOTION_GATE_V3.json"
)


def test_managed_internal_v2_contract_closes_receipt_chronology_consistency():
    p = json.loads(VALIDATION.read_text(encoding="utf-8"))
    chronology = p["chronology_v2"]
    assert chronology["required_order"] == (
        "freeze < declared_first_access <= odsp_managed_validation_read"
    )
    assert chronology["future_dated_first_access_after_scoring_rejected"] is True
    assert chronology["historical_truth_of_declared_first_access_machine_proven"] is False
    boundary = p["claim_boundary_v2"]
    assert boundary["score_tensor_derived_by_managed_scoring"] is True
    assert boundary["semantic_use_of_model_and_validation_inputs_cryptographically_proven"] is False


def test_managed_internal_promotion_v3_requires_corrected_focused_receipts_first():
    p = json.loads(PROMOTION.read_text(encoding="utf-8"))
    assert p["schema_version"] == 3
    assert p["promotion_requirements"][-2:] == [
        "route evidence registry updated only after focused and identity receipts exist",
        "routing promotion occurs only after updated evidence content is locked",
    ]
    focused = p["focused_requirements"]
    assert focused["outcome_bearing_validation_file_absent_at_freeze"] is True
    assert focused["scoring_code_byte_tampering_rejected"] is True
    assert focused["declared_first_access_after_managed_validation_read_rejected"] is True
    assert p["external_route_boundary"]["untouched_external_primary_surface_changed"] is False
