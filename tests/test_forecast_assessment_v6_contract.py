import json
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]


def test_forecast_assessment_v6_selection_provenance_contract_is_frozen():
    contract = json.loads(
        (ROOT / "FORECAST_ASSESSMENT_V6_SELECTION_PROVENANCE_CONTRACT.json").read_text(
            encoding="utf-8"
        )
    )
    assert contract["contract_id"] == "odsp-forecast-assessment-v6-selection-provenance-gate"

    composition = contract["composition_rule"]
    assert composition["forecast_assessment_v5_code_or_contract_is_not_modified"] is True
    assert composition["selection_validation_provenance_contract_is_reused_unchanged"] is True
    assert composition["scheme_omitted_v5_is_preserved_as_base_evidence"] is True
    assert composition["selection_provenance_runs_before_full_v5_training_and_scheme_path"] is True
    assert composition["selection_validation_leakage_prevents_full_v5_training_and_scheme_path"] is True
    assert composition["selection_leakage_is_provenance_failure_not_statistical_uncertainty"] is True
    assert composition["selection_leakage_applies_even_when_refit_scheme_layer_is_omitted"] is True
    assert composition["omitted_selection_layer_preserves_ordinary_v5_behavior"] is True
    assert composition["aggregate_confidence_score_emitted"] is False

    decision = contract["decision_rule"]
    assert decision["selection_leakage_on_otherwise_certifiable_base_gives_unavailable"] is True
    assert decision["selection_leakage_adds_provenance_reason"] == "selection_validation_leakage"
    assert decision["selection_leakage_does_not_add_training_or_refit_scheme_statistical_reason"] is True
    assert decision["clean_selection_plus_training_leakage_inherits_v5_provenance_unavailable"] is True
    assert decision["clean_selection_plus_row_mismatch_inherits_v5_provenance_unavailable"] is True
    assert decision["clean_selection_plus_scheme_sensitive_inherits_v5_not_certified"] is True
    assert decision["aggregate_confidence_score_emitted"] is False

    obligations = contract["known_truth_benchmark"]["frozen_obligations"]
    assert len(obligations) == 15
    assert all(value is True for key, value in obligations.items() if key != "aggregate_confidence_score_emitted")
    assert obligations["aggregate_confidence_score_emitted"] is False

    assert all(value is False for value in contract["claim_boundary"].values())
    assert all(value is False for value in contract["frozen_submission_boundary"].values())
