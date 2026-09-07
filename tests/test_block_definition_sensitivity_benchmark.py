from odsp.block_definition_sensitivity_benchmark import run_block_definition_sensitivity_benchmark


def test_frozen_block_definition_sensitivity_benchmark_passes():
    result=run_block_definition_sensitivity_benchmark(seed=20260906,bootstrap_draws=2000)
    assert result["passed"] is True
    assert len(result["checks"])==12
    assert all(row["passed"] for row in result["checks"])
    assert result["strong_positive"]["sensitivity_category"]=="block_definition_robust_generalizing"
    assert result["strong_negative"]["sensitivity_category"]=="block_definition_robust_non_generalizing"
    assert result["pseudoreplication"]["sensitivity_category"]=="block_definition_sensitive"
    assert result["too_coarse"]["sensitivity_category"]=="stable_unavailable"
