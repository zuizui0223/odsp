from odsp.block_aware_transfer_uncertainty_benchmark import (
    run_block_aware_transfer_uncertainty_benchmark,
)


def test_frozen_block_aware_benchmark_passes():
    result = run_block_aware_transfer_uncertainty_benchmark(
        seed=20260906,
        bootstrap_draws=2000,
        confidence_level=0.95,
    )
    assert result["passed"] is True
    assert len(result["checks"]) == 14
    assert all(row["passed"] for row in result["checks"])
    assert result["strong_positive"]["robust_transfer_category"] == "robust_generalizing"
    assert result["weak_positive"]["robust_transfer_category"] == "uncertain"
    assert result["negative"]["robust_transfer_category"] == "robust_non_generalizing"
    assert result["pseudoreplication_row_mode"]["groups"][0]["lower_bound"] > 0.0
    assert result["pseudoreplication_block_mode"]["groups"][0]["lower_bound"] <= 0.0
    assert result["too_few_blocks"]["robust_transfer_category"] == "unavailable"
