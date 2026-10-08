from __future__ import annotations
import json
from pathlib import Path

P=Path("ODSP_TRAINING_SOURCE_PROCESS_V0_PRIMARY_PROMOTION_GATE.json")

def test_source_v0_promotion_gate_requires_managed_scores_and_full_provenance():
    p=json.loads(P.read_text(encoding="utf-8"))
    assert len(p["statistical_evidence_required"]) == 2
    assert len(p["process_provenance_required"]) == 3
    assert "managed source x inner-refit x row x level score tensor" in p["score_provenance_required"]
    assert p["promotion_semantics"]["raw_caller_supplied_source_refit_score_tensor_primary"] is False
    assert p["promotion_semantics"]["managed_model_to_score_derivation_required"] is True
    assert p["promotion_semantics"]["route_registry_update_only_after_all_evidence_frozen"] is True

def test_source_v0_promotion_gate_keeps_narrow_estimand():
    p=json.loads(P.read_text(encoding="utf-8"))
    b=p["claim_boundary"]
    assert b["unknown_ecological_source_superpopulation_generalization_claimed"] is False
    assert b["individual_future_source_sample_success_probability_claimed"] is False
    assert b["all_future_source_samples_positive_claimed"] is False
    assert b["qualified_training_process_v5_reclassified"] is False
    assert p["scope"]["contrast_count"] == 2
    assert p["scope"]["balanced_inner_refit_counts_required"] is True
