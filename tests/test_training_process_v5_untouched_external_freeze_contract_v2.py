from __future__ import annotations
import json
from pathlib import Path

CONTRACT=Path("ODSP_TRAINING_PROCESS_V5_UNTOUCHED_EXTERNAL_FREEZE_CONTRACT_V2.json")

def test_v2_external_contract_requires_managed_score_derivation():
    p=json.loads(CONTRACT.read_text(encoding="utf-8"))
    assert p["schema_version"] == 2
    assert p["managed_scoring"]["caller_supplied_score_matrix_allowed_for_primary_external_route"] is False
    assert p["managed_scoring"]["generated_model_artifact_bytes_reverified_before_scoring"] is True
    assert p["managed_scoring"]["canonical_score_tensor_sha256_required"] is True
    assert p["claim_boundary"]["operational_model_to_score_derivation_verified"] is True
    assert p["route_state"]["external_process_route_primary_now"] is False

def test_v2_external_contract_preserves_process_mean_scope():
    b=json.loads(CONTRACT.read_text(encoding="utf-8"))["claim_boundary"]
    assert b["process_mean_conditional_on_frozen_training_source"] is True
    assert b["individual_future_refit_success_probability_claimed"] is False
    assert b["original_training_source_population_generalization_claimed"] is False
    assert b["fixed_set_intersection_reclassified"] is False
