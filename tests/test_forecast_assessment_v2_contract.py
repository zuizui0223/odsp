import json
from pathlib import Path


ROOT=Path(__file__).resolve().parents[1]


def test_forecast_assessment_v2_contract_is_frozen_and_fail_closed():
    contract=json.loads((ROOT/'FORECAST_ASSESSMENT_V2_CONTRACT.json').read_text(encoding='utf-8'))
    assert contract['contract_id']=='odsp-forecast-assessment-v2'
    composition=contract['composition_rule']
    assert composition['base_assessment_uses_existing_assess_state_forecast_v1'] is True
    assert composition['base_validation_history_is_never_recomputed_from_extended_layers'] is True
    assert composition['model_refit_reference_row_must_match_base_row_gain_within_tolerance'] is True
    assert composition['aggregate_confidence_score_emitted'] is False
    rule=contract['decision_rule']
    assert rule['block_definition_sensitivity_is_design_warning_not_retroactive_validation_override'] is True
    assert rule['single_scalar_confidence_score_is_forbidden'] is True
    obligations=contract['known_truth_benchmark']['frozen_obligations']
    assert len(obligations)==14
    for name,value in obligations.items():
        assert value is (name!='aggregate_confidence_score_emitted')
    assert all(value is False for value in contract['claim_boundary'].values())
    assert all(value is False for value in contract['frozen_v4_boundary'].values())
