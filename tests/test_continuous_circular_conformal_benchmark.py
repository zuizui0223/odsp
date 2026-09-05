from __future__ import annotations

from odsp.continuous_circular_conformal_benchmark import (
    run_continuous_circular_conformal_benchmark,
)


def test_frozen_continuous_circular_conformal_benchmark_passes():
    result = run_continuous_circular_conformal_benchmark(
        seed=20260905,
        replicates=128,
        calibration_rows=1000,
        test_rows=2000,
    )
    assert result.passed is True
    assert 0.885 <= result.mean_continuous_coverage <= 0.915
    assert 0.885 <= result.mean_circular_coverage <= 0.915
    assert 0.89 <= result.mean_joint_coverage <= 0.93
    assert result.mean_shifted_continuous_coverage < 0.60
    assert result.mean_shifted_circular_coverage < 0.60
    assert result.continuous_affine_quantile_error <= 1e-10
    assert result.circular_phase_quantile_error <= 1e-10
    assert result.circular_unit_relative_error <= 1e-10
