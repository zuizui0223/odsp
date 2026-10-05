from __future__ import annotations
import json
from pathlib import Path

GATE=Path("ODSP_TRAINING_PROCESS_V5_PRIMARY_PROMOTION_GATE_V2.json")

def test_promotion_gate_v2_names_provenance_wrapper_not_raw_numeric_core():
    p=json.loads(GATE.read_text(encoding="utf-8"))
    assert p["schema_version"] == 2
    assert p["predecessor"]["retained_unchanged"] is True
    assert p["canonical_primary_surface"] == (
        "odsp.training_process_confirmatory_v5."
        "certify_predeclared_training_process_positive_information_v5"
    )
    assert p["promotion_rule"]["canonical_wrapper_is_primary_candidate"] is True
    assert p["promotion_rule"]["raw_numeric_surface_is_primary"] is False
    assert p["canonical_wrapper_requirements"]["entire_training_source_frame_validation_disjointness_verified"] is True

def test_promotion_gate_v2_keeps_process_mean_claim_narrow():
    b=json.loads(GATE.read_text(encoding="utf-8"))["claim_boundary"]
    assert b["process_mean_conditional_on_frozen_training_source"] is True
    assert b["fixed_set_intersection_reclassified"] is False
    assert b["individual_future_refit_success_probability_claimed"] is False
    assert b["score_table_derivation_from_generated_models_independently_proven"] is False
