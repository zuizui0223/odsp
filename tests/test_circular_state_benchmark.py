from __future__ import annotations

from odsp.circular_state_benchmark import run_circular_state_benchmark


def test_frozen_circular_state_benchmark_passes_all_obligations():
    result = run_circular_state_benchmark(
        seed=20260905,
        replicates=128,
        training_rows=800,
        heldout_rows=1600,
        period=24.0,
    )
    assert result.passed is True
    assert result.stable_all_positive is True
    assert result.shifted_all_negative is True
    assert result.null_mean_gain_near_zero is True
    assert result.phase_origin_gain_invariance_error <= 1e-10
    assert result.period_unit_gain_invariance_error <= 1e-10
    assert 0.87 <= result.interval_empirical_coverage <= 0.93

    by_name = {row.family: row for row in result.families}
    assert by_name["stable_generalizing"].positive_gain_fraction == 1.0
    assert by_name["shifted_non_generalizing"].negative_gain_fraction == 1.0
    assert abs(by_name["unorganized"].mean_log_density_gain) < 0.02
