from __future__ import annotations

from odsp.trusted_joint_forecast_benchmark import run_trusted_joint_forecast_benchmark


def test_trusted_joint_forecast_benchmark_passes():
    result = run_trusted_joint_forecast_benchmark(
        seed=20260905,
        training_rows=1200,
        calibration_rows=1200,
        test_rows=3000,
    )
    assert result.passed is True
    assert result.training_split_preserved is True
    assert result.joint_log_density_gain > 0
    assert result.coupling_log_density_gain > 0
    assert 0.88 <= result.empirical_joint_coverage <= 0.93
    assert result.same_domain_non_strict_fraction >= 0.90
    assert result.shifted_strict_extrapolation_fraction == 1.0
    assert result.forecast_exposes_aggregate_confidence is False
