from odsp.robust_trust_aware_model_selection_benchmark import (
    run_robust_trust_aware_model_selection_benchmark,
)


def test_frozen_robust_selection_benchmark_passes():
    result=run_robust_trust_aware_model_selection_benchmark(seed=20260906,bootstrap_draws=2000)
    assert result["passed"] is True
    assert all(row["passed"] for row in result["checks"])
    comparison=result["comparison"]
    assert comparison["recommended_by_log_score"]=="robust_balanced"
    assert comparison["pareto_front_names"]==["robust_balanced"]
    assert "fragile_point_positive" in comparison["legacy_trusted_but_robust_rejected_names"]
    assert result["candidates"]["fragile_point_positive"]["transfer_uncertainty"]["robust_transfer_category"]=="uncertain"
    assert result["candidates"]["too_few_blocks"]["transfer_uncertainty"]["robust_transfer_category"]=="unavailable"
