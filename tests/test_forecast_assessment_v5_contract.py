import json
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]


def test_forecast_assessment_v5_contract_is_frozen():
    contract = json.loads(
        (ROOT / "FORECAST_ASSESSMENT_V5_TRAINING_PROVENANCE_CONTRACT.json").read_text(
            encoding="utf-8"
        )
    )
    assert contract["contract_id"] == "odsp-forecast-assessment-v5-training-provenance-gate"

    composition = contract["composition_rule"]
    assert composition["complete_v4_result_without_scheme_layer_is_preserved_as_base_evidence"] is True
    assert composition["forecast_assessment_v4_code_or_contract_is_not_modified"] is True
    assert composition["requested_scheme_layer_requires_explicit_stable_refit_ids"] is True
    assert composition["requested_scheme_layer_requires_training_membership_for_every_scheme_and_refit"] is True
    assert composition["training_provenance_runs_before_row_alignment_and_scheme_statistics"] is True
    assert composition["training_validation_disjoint_allows_existing_v4_scheme_path"] is True
    assert composition["training_validation_leakage_prevents_existing_v4_scheme_path"] is True
    assert composition["qualified_v4_assessment_is_absent_on_training_leakage"] is True
    assert composition["row_alignment_and_scheme_statistics_are_not_run_on_training_leakage"] is True
    assert composition["training_leakage_is_provenance_failure_not_statistical_uncertainty"] is True
    assert composition["aggregate_confidence_score_emitted"] is False

    rule = contract["decision_rule"]
    assert rule["clean_training_provenance_inherits_qualified_v4_certification"] is True
    assert rule["training_leakage_on_otherwise_certifiable_base_gives_unavailable"] is True
    assert rule["training_leakage_adds_provenance_reason"] == "training_validation_leakage"
    assert rule["training_leakage_does_not_add_refit_scheme_statistical_reason"] is True
    assert rule["clean_training_provenance_plus_row_mismatch_inherits_v4_provenance_unavailable"] is True
    assert rule["clean_training_provenance_plus_scheme_sensitive_inherits_v4_not_certified"] is True
    assert rule["aggregate_confidence_score_emitted"] is False

    obligations = contract["known_truth_benchmark"]["frozen_obligations"]
    assert len(obligations) == 15
    assert all(
        value is True
        for key, value in obligations.items()
        if key != "aggregate_confidence_score_emitted"
    )
    assert obligations["aggregate_confidence_score_emitted"] is False

    assert all(value is False for value in contract["claim_boundary"].values())
    assert all(value is False for value in contract["frozen_v4_submission_boundary"].values())
