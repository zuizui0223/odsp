import json
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]


def test_forecast_assessment_v8_content_provenance_contract_is_frozen():
    contract = json.loads(
        (ROOT / "FORECAST_ASSESSMENT_V8_CONTENT_PROVENANCE_CONTRACT.json").read_text(
            encoding="utf-8"
        )
    )
    assert contract["contract_id"] == "odsp-forecast-assessment-v8-content-provenance-gate"

    composition = contract["composition_rule"]
    assert composition["forecast_assessment_v7_code_or_contract_is_not_modified"] is True
    assert composition["evaluation_content_provenance_contract_is_reused_unchanged"] is True
    assert composition["content_provenance_runs_before_full_v7_path"] is True
    assert composition["final_evaluation_content_leakage_prevents_full_v7_path"] is True
    assert composition["artifact_access_selection_training_alignment_and_scheme_layers_are_not_run_on_content_leakage"] is True
    assert composition["content_leakage_is_provenance_failure_not_statistical_uncertainty"] is True
    assert composition["omitted_content_layer_preserves_ordinary_v7_behavior"] is True
    assert composition["aggregate_confidence_score_emitted"] is False

    decision = contract["decision_rule"]
    assert decision["content_leakage_on_otherwise_certifiable_base_gives_unavailable"] is True
    assert decision["content_leakage_adds_provenance_reason"] == "final_evaluation_content_leakage"
    assert decision["content_leakage_does_not_add_statistical_reason"] is True
    assert decision["clean_content_plus_artifact_access_leakage_inherits_v7_provenance_unavailable"] is True
    assert decision["clean_content_plus_selection_leakage_inherits_v7_provenance_unavailable"] is True
    assert decision["clean_content_plus_training_leakage_inherits_v7_provenance_unavailable"] is True
    assert decision["clean_content_plus_row_mismatch_inherits_v7_provenance_unavailable"] is True
    assert decision["clean_content_plus_scheme_sensitive_inherits_v7_not_certified"] is True
    assert decision["aggregate_confidence_score_emitted"] is False

    obligations = contract["known_truth_benchmark"]["frozen_obligations"]
    assert len(obligations) == 16
    assert all(
        value is True
        for key, value in obligations.items()
        if key != "aggregate_confidence_score_emitted"
    )
    assert obligations["aggregate_confidence_score_emitted"] is False

    assert all(value is False for value in contract["claim_boundary"].values())
    assert all(value is False for value in contract["frozen_submission_boundary"].values())
