from __future__ import annotations

import pytest

from odsp.bootstrap_t_operating_characteristics import (
    run_null_calibration_scenario,
)


def test_null_calibration_benchmark_is_deterministic_and_non_empirical():
    kwargs = dict(
        scenario_id="smoke-normal-b20",
        distribution="normal",
        group_count=4,
        blocks_per_group=20,
        simulations=50,
        bootstrap_draws=500,
        seed=20260914,
    )
    first = run_null_calibration_scenario(**kwargs)
    second = run_null_calibration_scenario(**kwargs)
    assert first == second
    assert first.simulations == 50
    assert first.group_count == 4
    assert first.blocks_per_group == 20
    for value in (
        first.v1_two_sided_familywise_noncoverage_rate,
        first.v2_two_sided_familywise_noncoverage_rate,
        first.v1_any_false_positive_cell_rate,
        first.v2_any_false_positive_cell_rate,
        first.v1_any_false_negative_cell_rate,
        first.v2_any_false_negative_cell_rate,
        first.v1_terminal_false_generalizing_rate,
        first.v2_terminal_false_generalizing_rate,
        first.v1_infinite_critical_rate,
        first.v2_infinite_critical_rate,
    ):
        assert 0.0 <= value <= 1.0
    assert first.v2_monte_carlo_standard_error >= 0.0


def test_calibration_input_guards_fail_closed():
    with pytest.raises(ValueError, match="blocks_per_group"):
        run_null_calibration_scenario(
            scenario_id="bad",
            distribution="normal",
            group_count=4,
            blocks_per_group=7,
            simulations=50,
            bootstrap_draws=500,
            seed=1,
        )
    with pytest.raises(ValueError, match="simulations"):
        run_null_calibration_scenario(
            scenario_id="bad",
            distribution="normal",
            group_count=4,
            blocks_per_group=20,
            simulations=49,
            bootstrap_draws=500,
            seed=1,
        )
