from odsp.bounded_reweighting_robustness_benchmark import (
    run_bounded_reweighting_robustness_benchmark,
)


def test_frozen_bounded_reweighting_benchmark_passes():
    result=run_bounded_reweighting_robustness_benchmark(gamma=2.0)
    assert result["passed"] is True
    assert len(result["checks"])==12
    assert all(row["passed"] for row in result["checks"])
    assert result["all_positive"]["envelope_transfer_category"]=="gamma_robust_generalizing"
    assert result["mixed_sign_gamma_1"]["envelope_transfer_category"]=="gamma_robust_generalizing"
    assert result["mixed_sign_primary_gamma"]["envelope_transfer_category"]=="gamma_sensitive"
    assert result["all_negative"]["envelope_transfer_category"]=="gamma_robust_non_generalizing"
    assert result["mixed_sign_critical_gamma_error"]<=1e-10
    assert result["small_n_exhaustive_error"]<=1e-12
