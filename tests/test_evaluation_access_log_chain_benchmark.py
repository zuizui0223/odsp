from odsp.evaluation_access_log_chain_benchmark import run_evaluation_access_log_chain_benchmark


def test_evaluation_access_log_chain_frozen_known_truth_benchmark_passes():
    result = run_evaluation_access_log_chain_benchmark(seed=20260910)
    assert result["passed"] is True
    assert len(result["checks"]) == 17
    assert all(row["passed"] for row in result["checks"])
    assert result["clean"]["separation_category"] == "evaluation_access_log_chain_consistent"
    assert result["payload_mutation"]["separation_category"] == "evaluation_access_log_chain_mismatch"
    assert result["dropped_tail"]["terminal_event_hash_match"] is False
    assert result["id_ledger_mismatch"]["stage_artifact_id_ledger_match"] is False
    assert result["digest_ledger_mismatch"]["stage_digest_ledger_match"] is False
