import json
from pathlib import Path

ROOT=Path(__file__).resolve().parents[1]


def test_forecast_assessment_v3_contract_is_frozen_and_fail_closed():
    contract=json.loads((ROOT/"FORECAST_ASSESSMENT_V3_CONTRACT.json").read_text(encoding="utf-8"))
    assert contract["contract_id"]=="odsp-forecast-assessment-v3-refit-scheme-certification"
    composition=contract["composition_rule"]
    assert composition["complete_v2_result_is_preserved"] is True
    assert composition["v2_result_is_not_recomputed_from_scheme_result"] is True
    assert composition["scheme_layer_uses_existing_refit_scheme_sensitivity_api"] is True
    rule=contract["decision_rule"]
    assert rule["v2_not_certified_cannot_be_rescued_by_scheme_layer"] is True
    assert rule["one_robust_scheme_cannot_override_scheme_sensitive_result"] is True
    obligations=contract["known_truth_benchmark"]["frozen_obligations"]
    assert len(obligations)==12
    for name,value in obligations.items():
        if name=="aggregate_confidence_score_emitted":
            assert value is False
        else:
            assert value is True
    assert all(value is False for value in contract["claim_boundary"].values())
    assert all(value is False for value in contract["frozen_v4_boundary"].values())
