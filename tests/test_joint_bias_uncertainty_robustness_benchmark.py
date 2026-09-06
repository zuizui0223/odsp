from odsp.joint_bias_uncertainty_robustness_benchmark import (
    run_joint_bias_uncertainty_robustness_benchmark,
)


def test_frozen_joint_bias_uncertainty_benchmark_passes():
    result=run_joint_bias_uncertainty_robustness_benchmark(
        seed=20260906,bootstrap_draws=1000
    )
    assert result["passed"] is True
    assert len(result["checks"])==10
    assert all(row["passed"] for row in result["checks"])
    assert result["strong_positive"]["joint_robust_category"]=="joint_robust_generalizing"
    assert result["mixed_sign"]["joint_robust_category"]=="envelope_sensitive"
    assert result["negative"]["joint_robust_category"]=="joint_robust_non_generalizing"
    assert result["weak_positive_gamma_1"]["joint_robust_category"]=="uncertain"
    assert result["too_few_blocks"]["joint_robust_category"]=="unavailable"
    assert result["gamma_1_existing_bound_error"]<=1e-12
