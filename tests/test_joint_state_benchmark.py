from __future__ import annotations

from odsp.joint_state_benchmark import run_joint_state_benchmark


def test_frozen_joint_state_benchmark_passes_all_obligations():
    result = run_joint_state_benchmark(
        seed=20260905,
        replicates=128,
        training_rows=800,
        heldout_rows=1600,
        period=24.0,
    )
    assert result.passed is True
    assert result.stable_joint_all_positive is True
    assert result.stable_coupling_all_positive is True
    assert result.context_null_joint_mean_near_zero is True
    assert result.uncoupled_coupling_mean_near_zero is True
    assert result.context_shift_joint_all_negative is True
    assert result.coupling_shift_coupling_all_negative is True
    assert result.phase_origin_joint_gain_error <= 1e-10
    assert result.phase_origin_coupling_gain_error <= 1e-10
    assert result.period_unit_joint_gain_error <= 1e-10
    assert result.period_unit_coupling_gain_error <= 1e-10
    assert result.height_unit_joint_gain_error <= 1e-10
    assert result.height_unit_coupling_gain_error <= 1e-10
