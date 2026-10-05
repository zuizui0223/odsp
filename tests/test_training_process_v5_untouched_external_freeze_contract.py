from __future__ import annotations
import json
from pathlib import Path

CONTRACT=Path("ODSP_TRAINING_PROCESS_V5_UNTOUCHED_EXTERNAL_FREEZE_CONTRACT.json")

def test_process_external_freeze_locks_full_validation_design():
    p=json.loads(CONTRACT.read_text(encoding="utf-8"))
    assert p["pre_outcome_external_design"]["roster_columns_exactly"] == [
        "row_id","group_id","block_id","sample_weight"
    ]
    assert p["pre_outcome_external_design"]["outcome_column_allowed"] is False
    assert p["pre_outcome_external_design"]["group_block_weight_metadata_frozen_before_outcome_access"] is True

def test_external_freeze_targets_provenance_verifying_v5_wrapper():
    p=json.loads(CONTRACT.read_text(encoding="utf-8"))
    assert p["method_identity"]["canonical_surface"] == (
        "odsp.training_process_confirmatory_v5."
        "certify_predeclared_training_process_positive_information_v5"
    )
    assert p["method_identity"]["qualification_registry"] == (
        "odsp-confirmatory-route-evidence-v4"
    )

def test_process_external_route_remains_closed_until_endpoint_is_verified():
    p=json.loads(CONTRACT.read_text(encoding="utf-8"))
    assert p["route_state"]["internal_process_route_primary"] is True
    assert p["route_state"]["external_process_route_primary_now"] is False
    assert p["route_state"]["may_not_be_registered_until_endpoint_and_freeze_semantics_pass"] is True

def test_external_freeze_does_not_borrow_fixed_set_or_expand_estimand():
    p=json.loads(CONTRACT.read_text(encoding="utf-8"))
    b=p["claim_boundary"]
    assert b["fixed_set_refit_results_reclassified"] is False
    assert b["process_mean_estimand_changed"] is False
    assert b["process_mean_conditional_on_frozen_training_source"] is True
    assert b["individual_future_refit_success_probability_claimed"] is False
