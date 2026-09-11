import json
from pathlib import Path


CONTRACT = Path(__file__).resolve().parents[1] / "EVALUATION_ACCESS_CHECKPOINT_CONTRACT.json"


def test_evaluation_access_checkpoint_contract_is_frozen():
    contract = json.loads(CONTRACT.read_text())
    assert contract["contract_id"] == "odsp-evaluation-access-checkpoint-provenance"
    assert contract["frozen_date"] == "2026-09-11"
    assert contract["checkpoint_schema"]["at_least_two_checkpoints_are_required"] is True
    assert contract["checkpoint_schema"]["terminal_event_checkpoint_is_required"] is True
    assert contract["decision_rule"]["all_checkpoint_hashes_match_and_order_is_increasing_and_terminal_checkpoint_present_gives"] == "evaluation_access_checkpoints_consistent"
    assert contract["decision_rule"]["any_checkpoint_hash_mismatch_or_order_mismatch_or_missing_terminal_checkpoint_gives"] == "evaluation_access_checkpoint_mismatch"
    obligations = contract["known_truth_benchmark"]["frozen_obligations"]
    assert len(obligations) == 16
    assert all(obligations.values())
    assert contract["claim_boundary"]["consistent_checkpoints_prove_external_timestamping"] is False
    assert contract["claim_boundary"]["consistent_checkpoints_prove_no_whole_chain_and_checkpoint_cofabrication"] is False
    assert contract["decision_rule"]["aggregate_confidence_score_emitted"] is False
