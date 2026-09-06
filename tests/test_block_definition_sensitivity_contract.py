import json
from pathlib import Path


ROOT=Path(__file__).resolve().parents[1]


def test_block_definition_sensitivity_contract_is_frozen_and_fail_closed():
    contract=json.loads((ROOT/"BLOCK_DEFINITION_SENSITIVITY_CONTRACT.json").read_text(encoding="utf-8"))
    assert contract["contract_id"]=="odsp-block-definition-sensitivity-v1"
    composition=contract["composition_rule"]
    assert composition["same_row_gain_required_across_block_definitions"] is True
    assert composition["same_group_labels_required_across_block_definitions"] is True
    assert composition["no_automatic_block_definition_selection"] is True
    assert composition["aggregate_confidence_score_emitted"] is False
    rule=contract["decision_rule"]
    assert rule["pooled_mean_can_override_definition_failure"] is False
    assert rule["row_count_can_override_block_count_failure"] is False
    assert rule["correct_block_definition_is_not_inferred"] is True
    obligations=contract["known_truth_benchmark"]["frozen_obligations"]
    assert len(obligations)==12
    for key,value in obligations.items():
        if key in {"no_automatic_block_definition_selection","aggregate_confidence_score_emitted"}:
            assert value is False
        else:
            assert value is True
    boundary=contract["claim_boundary"]
    assert all(value is False for value in boundary.values())
    frozen=contract["frozen_v4_boundary"]
    assert all(value is False for value in frozen.values())
