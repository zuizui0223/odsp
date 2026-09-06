import json
from pathlib import Path


ROOT=Path(__file__).resolve().parents[1]


def test_simultaneous_group_certification_contract_is_frozen_and_fail_closed():
    contract=json.loads((ROOT/"SIMULTANEOUS_GROUP_CERTIFICATION_CONTRACT.json").read_text(encoding="utf-8"))
    assert contract["contract_id"]=="odsp-simultaneous-group-certification-v1"
    definition=contract["definition"]
    assert definition["primary_simultaneous_method"]=="two-sided studentized bootstrap max-t interval"
    assert definition["unestimable_group_blocks_global_certification"] is True
    assert definition["pooled_gain_can_override_group_failure"] is False
    assert definition["marginal_interval_can_override_simultaneous_failure"] is False
    assert definition["aggregate_confidence_score_emitted"] is False
    obligations=contract["known_truth_benchmark"]["frozen_obligations"]
    positive={k:v for k,v in obligations.items() if k!="aggregate_confidence_score_emitted"}
    assert len(obligations)==15
    assert all(value is True for value in positive.values())
    assert obligations["aggregate_confidence_score_emitted"] is False
    boundary=contract["claim_boundary"]
    assert all(value is False for value in boundary.values())
    frozen=contract["frozen_v4_boundary"]
    assert all(value is False for value in frozen.values())
