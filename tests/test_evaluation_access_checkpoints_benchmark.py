from odsp.evaluation_access_checkpoints_benchmark import run_evaluation_access_checkpoints_benchmark


def test_evaluation_access_checkpoint_benchmark_passes():
    result = run_evaluation_access_checkpoints_benchmark(seed=20260911)
    assert result["passed"] is True
    assert len(result["checks"]) == 16
    assert all(row["passed"] for row in result["checks"])
    assert result["clean"]["separation_category"] == "evaluation_access_checkpoints_consistent"
    assert result["middle_mismatch"]["mismatched_checkpoint_count"] == 1
    assert result["order_mismatch"]["checkpoint_order_strictly_increasing"] is False
    assert result["missing_terminal"]["terminal_checkpoint_present"] is False
