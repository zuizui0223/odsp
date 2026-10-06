from __future__ import annotations

import json
from pathlib import Path


CONTRACT = Path(
    "ODSP_TRAINING_PROCESS_V5_MANAGED_INTERNAL_FOCUSED_RECEIPT_CONTRACT.json"
)


def test_managed_internal_focused_receipt_schema_is_frozen_pre_result():
    p = json.loads(CONTRACT.read_text(encoding="utf-8"))
    assert p["receipt_identity"]["official_github_actions_run_id_required"] is True
    outcomes = p["required_test_outcomes"]
    assert outcomes["prospective_happy_path_pass"] is True
    assert outcomes["scoring_code_byte_tampering_rejected"] is True
    assert outcomes["declared_first_access_after_managed_validation_read_rejected"] is True
    boundaries = p["required_boundaries"]
    assert boundaries["semantic_use_of_model_and_validation_inputs_cryptographically_proven"] is False
    assert boundaries["statistical_method_changed"] is False
    assert p["promotion_boundary"]["registry_update_forbidden_before_identity_receipt"] is True
