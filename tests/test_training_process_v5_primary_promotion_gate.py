from __future__ import annotations
import json
from pathlib import Path

CONTRACT=Path("ODSP_TRAINING_PROCESS_V5_PRIMARY_PROMOTION_GATE.json")

def test_v5_promotion_gate_requires_statistics_provenance_and_locks():
    p=json.loads(CONTRACT.read_text(encoding="utf-8"))
    assert p["prospective_route"]["upstream_refits"] == "predeclared_training_process"
    assert p["prospective_route"]["contrast_count"] == 2
    assert len(p["statistical_evidence_required"]) == 3
    assert len(p["process_provenance_required"]) == 3
    assert len(p["implementation_and_environment_required"]) == 3
    assert p["promotion_rule"]["all_required_evidence_must_exist_and_pass"] is True
    assert p["promotion_rule"]["raw_numeric_v5_api_without_process_provenance_is_primary"] is False
    assert p["external_boundary"]["separate_process_specific_pre_outcome_external_freeze_required"] is True
    assert p["external_boundary"]["external_row_group_block_weight_metadata_must_be_frozen_before_outcomes"] is True

def test_promotion_gate_does_not_reclassify_fixed_set_or_expand_estimand():
    p=json.loads(CONTRACT.read_text(encoding="utf-8"))
    b=p["claim_boundary"]
    assert b["fixed_set_intersection_reclassified"] is False
    assert b["historical_empirical_endpoint_reclassified"] is False
    assert b["probability_individual_future_refit_passes_claimed"] is False
    assert b["original_training_source_population_generalization_claimed"] is False
