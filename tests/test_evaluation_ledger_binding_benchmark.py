from odsp.evaluation_ledger_binding_benchmark import (
    run_evaluation_ledger_binding_benchmark,
)


def test_evaluation_ledger_binding_frozen_benchmark_passes():
    result = run_evaluation_ledger_binding_benchmark(seed=20260910)
    assert result["passed"] is True
    assert len(result["checks"]) == 16
    assert all(row["passed"] for row in result["checks"])
    assert result["clean"]["separation_category"] == "evaluation_ledgers_consistently_bound"
    assert result["wrong_declared_final_digest"]["separation_category"] == "evaluation_ledger_binding_mismatch"
    assert result["stage_digest_substitution"]["mismatched_stage_count"] == 1
