from __future__ import annotations

from odsp.state_space_generality_benchmark import (
    run_state_space_generality_benchmark,
)


def test_state_space_generality_benchmark_passes_all_obligations() -> None:
    result = run_state_space_generality_benchmark()
    assert result.passed
    assert result.failed_count == 0
    assert result.check_count == 10
    assert result.passed_count == 10
    assert result.maximum_absolute_error <= 2e-10
    assert result.state_spaces == (
        "finite_discrete",
        "continuous_scalar",
        "circular_scalar",
        "continuous_x_circular_joint",
    )
    assert "log q_train(A|X) - log q0_train(A)" in result.common_estimand


def test_each_state_space_has_native_equivalence_and_reference_shift_checks() -> None:
    result = run_state_space_generality_benchmark()
    by_space: dict[str, set[str]] = {}
    for check in result.checks:
        by_space.setdefault(check.state_space, set()).add(check.property_name)
    for state_space in result.state_spaces:
        assert by_space[state_space] == {
            "native_and_generic_gain_agree",
            "common_reference_measure_shift_invariant",
        }
    assert by_space["independent_group_rule"] == {
        "conflicting_groups_remain_mixed",
        "all_positive_groups_are_generalizing",
    }
