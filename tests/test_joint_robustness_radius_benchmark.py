from odsp.joint_robustness_radius_benchmark import run_joint_robustness_radius_benchmark


def test_frozen_joint_robustness_radius_benchmark_passes():
    result=run_joint_robustness_radius_benchmark(seed=20260906,bootstrap_draws=500)
    assert result["passed"] is True
    assert len(result["checks"])==12
    assert all(row["passed"] for row in result["checks"])
    assert result["strong_positive"]["radius_status"]=="robust_through_search_upper"
    assert result["strong_negative"]["radius_status"]=="robust_through_search_upper"
    assert result["mixed_positive"]["radius_status"]=="finite_radius"
    assert result["weak_positive"]["radius_status"]=="not_certified_at_baseline"
    assert result["too_few_blocks"]["radius_status"]=="unavailable"
