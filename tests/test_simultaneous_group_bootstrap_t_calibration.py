from __future__ import annotations

from odsp.bootstrap_t_calibration_benchmark import (
    run_bootstrap_t_calibration_benchmark,
)


def test_v2_familywise_null_calibration_guardrail():
    result = run_bootstrap_t_calibration_benchmark()

    assert result.simulation_count == 160
    assert result.group_count == 3
    assert result.blocks_per_group == 20
    assert result.bootstrap_draws == 500
    assert result.v2_within_ci_guardrail is True
    assert result.v2_not_materially_worse_than_v1 is True
    assert 0.0 <= result.v2_familywise_rejection_rate <= 0.12
