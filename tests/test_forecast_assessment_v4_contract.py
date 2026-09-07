import json
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]


def test_forecast_assessment_v4_provenance_contract_is_frozen():
    contract = json.loads(
        (ROOT / "FORECAST_ASSESSMENT_V4_PROVENANCE_CONTRACT.json").read_text(encoding="utf-8")
    )
    assert contract["contract_id"] == "odsp-forecast-assessment-v4-provenance-aware-scheme-certification"

    composition = contract["composition_rule"]
    assert composition["complete_v3_result_without_scheme_layer_is_preserved_as_base_evidence"] is True
    assert composition["forecast_assessment_v3_code_or_contract_is_not_modified"] is True
    assert composition["aligned_scheme_layer_uses_existing_aligned_refit_scheme_api"] is True
    assert composition["existing_v3_scheme_decision_rule_is_reused_after_successful_alignment"] is True
    assert composition["row_mismatch_prevents_statistical_scheme_audit"] is True
    assert composition["row_mismatch_is_provenance_unavailable_not_refit_scheme_uncertainty"] is True
    assert composition["aggregate_confidence_score_emitted"] is False

    decision = contract["decision_rule"]
    assert decision["base_v3_not_certified_cannot_be_rescued"] is True
    assert decision["provenance_row_mismatch_on_otherwise_admitted_base_gives_unavailable"] is True
    assert decision["provenance_row_mismatch_adds_provenance_reason_not_statistical_scheme_reason"] is True
    assert decision["scheme_only_formal_layer_can_certify_when_base_v3_is_not_audited"] is True
    assert decision["aggregate_confidence_score_emitted"] is False

    obligations = contract["known_truth_benchmark"]["frozen_obligations"]
    assert len(obligations) == 13
    assert all(value is True for key, value in obligations.items() if key != "aggregate_confidence_score_emitted")
    assert obligations["aggregate_confidence_score_emitted"] is False

    assert all(value is False for value in contract["claim_boundary"].values())
    assert all(value is False for value in contract["frozen_v4_submission_boundary"].values())
