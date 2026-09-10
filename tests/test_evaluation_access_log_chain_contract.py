import json
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]


def test_evaluation_access_log_chain_contract_is_frozen():
    contract = json.loads((ROOT / "EVALUATION_ACCESS_LOG_CHAIN_CONTRACT.json").read_text())
    assert contract["contract_id"] == "odsp-evaluation-access-log-chain-provenance"
    assert all(contract["event_schema"].values())
    commitments = contract["commitment_rule"]
    assert commitments["committed_event_count_is_required_and_must_equal_supplied_event_count"] is True
    assert commitments["committed_terminal_event_hash_is_required_and_must_equal_last_event_hash"] is True
    assert commitments["each_previous_hash_must_equal_prior_event_hash"] is True
    assert commitments["each_event_hash_is_recomputed"] is True
    assert commitments["stage_id_ledger_must_equal_event_derived_ledger"] is True
    assert commitments["stage_digest_ledger_must_equal_event_derived_ledger"] is True
    assert commitments["automatic_external_anchor_verification"] is False
    assert commitments["automatic_access_history_inference"] is False
    assert commitments["real_world_log_completeness_assumed"] is False
    assert commitments["aggregate_confidence_score_emitted"] is False

    obligations = contract["known_truth_benchmark"]["frozen_obligations"]
    assert len(obligations) == 17
    assert all(value is True for key, value in obligations.items() if key != "aggregate_confidence_score_emitted")
    assert obligations["aggregate_confidence_score_emitted"] is False
    assert all(value is False for value in contract["claim_boundary"].values())
    assert all(value is False for value in contract["frozen_submission_boundary"].values())
