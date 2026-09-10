import json
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]


def test_evaluation_ledger_binding_contract_is_frozen():
    contract = json.loads(
        (ROOT / "EVALUATION_LEDGER_BINDING_CONTRACT.json").read_text(encoding="utf-8")
    )
    assert contract["contract_id"] == "odsp-evaluation-ledger-binding-provenance"

    inputs = contract["input_rule"]
    assert inputs["artifact_digest_manifest_is_caller_supplied"] is True
    assert inputs["artifact_digest_manifest_must_contain_final_artifact_id"] is True
    assert inputs["all_accessed_artifact_ids_must_exist_in_manifest"] is True
    assert inputs["artifact_id_and_digest_ledgers_must_have_same_stage_coverage"] is True
    assert inputs["duplicate_accesses_are_legal"] is True
    assert inputs["digest_order_within_stage_is_not_semantically_relevant"] is True
    assert inputs["automatic_artifact_hashing"] is False

    decision = contract["decision_rule"]
    assert decision["final_artifact_manifest_digest_must_equal_declared_final_digest"] is True
    assert decision["each_stage_declared_digest_multiset_must_equal_manifest_implied_digest_multiset"] is True
    assert decision["all_bindings_match_category"] == "evaluation_ledgers_consistently_bound"
    assert decision["any_final_or_stage_binding_mismatch_category"] == "evaluation_ledger_binding_mismatch"
    assert decision["final_digest_alias_ids_are_reported_but_not_themselves_leakage"] is True
    assert decision["artifact_ids_emitted"] is False
    assert decision["digests_emitted"] is False
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
