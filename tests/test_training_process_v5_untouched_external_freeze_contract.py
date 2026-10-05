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

def test_process_external_route_remains_closed_until_internal_chain_passes():
    p=json.loads(CONTRACT.read_text(encoding="utf-8"))
    assert p["route_state"]["external_process_route_primary_now"] is False
    assert p["route_state"]["may_not_be_registered_until_all_prerequisites_pass"] is True
    assert p["prerequisites"]["internal_v5_primary_qualification_required"] is True
    assert p["prerequisites"]["managed_generation_receipt_required"] is True

def test_external_freeze_does_not_borrow_fixed_set_target():
    p=json.loads(CONTRACT.read_text(encoding="utf-8"))
    assert p["claim_boundary"]["fixed_set_refit_results_reclassified"] is False
    assert p["claim_boundary"]["process_mean_estimand_changed"] is False
