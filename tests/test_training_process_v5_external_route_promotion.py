from __future__ import annotations
import json
from pathlib import Path

P=Path("ODSP_TRAINING_PROCESS_V5_EXTERNAL_ROUTE_PROMOTION_CONTRACT.json")

def test_external_route_promotion_contract_is_narrow_and_prospective():
    p=json.loads(P.read_text(encoding="utf-8"))
    assert p["routing_semantics"]["role"] == "primary_confirmatory"
    assert p["routing_semantics"]["requires_preoutcome_freeze"] is True
    assert p["routing_semantics"]["managed_external_scoring_required"] is True
    assert p["scope"]["contrast_count"] == 2
    assert p["scope"]["contrast_count_4_primary"] is False
    assert p["scope"]["paired_process_external_primary"] is False
    assert p["scope"]["lattice_process_external_primary"] is False
    assert len(p["external_evidence_append_order"]) == 6

def test_external_route_promotion_contract_does_not_expand_process_estimand():
    b=json.loads(P.read_text(encoding="utf-8"))["claim_boundary"]
    assert b["fixed_set_results_reclassified"] is False
    assert b["individual_future_refit_success_probability_claimed"] is False
    assert b["original_training_source_population_generalization_claimed"] is False
    assert b["historical_truth_of_external_nonaccess_machine_proven"] is False
