import json
from pathlib import Path


ROOT=Path(__file__).resolve().parents[1]


def test_forecast_assessment_contract_is_frozen_and_fail_closed():
    contract=json.loads((ROOT/"FORECAST_ASSESSMENT_CONTRACT.json").read_text(encoding="utf-8"))
    assert contract["contract_id"]=="odsp-end-to-end-forecast-assessment-v1"
    composition=contract["composition_rule"]
    assert composition["same_validation_rows_required_for_candidate_and_robustness_audits"] is True
    assert composition["dossier_uses_existing_forecast_trust_dossier_v2"] is True
    assert composition["aggregate_confidence_score_emitted"] is False
    rule=contract["decision_rule"]
    assert rule["validation_admission_is_not_recomputed_from_optional_sensitivity_layers"] is True
    assert rule["environmental_novelty_is_deployment_warning_not_validation_failure"] is True
    assert rule["single_score_is_forbidden"] is True
    obligations=contract["known_truth_benchmark"]["frozen_obligations"]
    assert len(obligations)==13
    assert all(value is True for value in obligations.values())
    boundary=contract["claim_boundary"]
    assert boundary["assessment_infers_correct_sampling_weights"] is False
    assert boundary["joint_radius_is_probability_of_correctness"] is False
    assert boundary["aggregate_confidence_score_emitted"] is False
    frozen=contract["frozen_v4_boundary"]
    assert all(value is False for value in frozen.values())
