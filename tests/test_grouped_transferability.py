import math

import numpy as np
import pytest

from odsp.grouped_benchmark import (
    grouped_transferability_benchmark_passes,
    run_grouped_transferability_benchmark,
)
from odsp.grouped_transferability import score_independent_groups


def _organized_model() -> np.ndarray:
    model = np.zeros((2, 1, 2), dtype=float)
    model[0, 0, :] = [9.0, 1.0]
    model[1, 0, :] = [1.0, 9.0]
    return model


def test_all_independent_groups_positive_is_generalizing():
    model = _organized_model()
    result = score_independent_groups(
        model,
        {"individual-a": model.copy(), "individual-b": model * 3.0},
        base_axes=(0, 1),
        added_axes=(2,),
    )

    assert result.classification == "generalizing"
    assert [group.group_id for group in result.groups] == ["individual-a", "individual-b"]
    assert all(gain > 0.0 for gain in result.gains)
    assert result.equal_group_mean_gain == pytest.approx(sum(result.gains) / 2.0)


def test_opposing_independent_groups_is_mixed_not_rescued_by_mean():
    model = _organized_model()
    stable = model.copy()
    reversed_support = model[::-1].copy()

    result = score_independent_groups(
        model,
        [("stable", stable), ("reversed", reversed_support)],
        base_axes=(0, 1),
        added_axes=(2,),
    )

    assert result.gains[0] > 0.0
    assert result.gains[1] < 0.0
    assert result.classification == "mixed"


def test_all_nonpositive_groups_is_non_generalizing():
    model = _organized_model()
    reversed_support = model[::-1].copy()

    result = score_independent_groups(
        model,
        {"a": reversed_support, "b": reversed_support * 10.0},
        base_axes=(0, 1),
        added_axes=(2,),
    )

    assert result.classification == "non_generalizing"
    assert all(gain <= 0.0 for gain in result.gains)


def test_zero_conditional_group_keeps_negative_infinity_failure():
    model = np.zeros((2, 1, 2), dtype=float)
    model[0, 0, 0] = 1.0
    model[1, 0, 1] = 1.0
    heldout = np.zeros_like(model)
    heldout[0, 0, 1] = 1.0

    result = score_independent_groups(
        model,
        {"failure-a": heldout, "failure-b": heldout.copy()},
        base_axes=(0, 1),
        added_axes=(2,),
    )

    assert result.gains == (float("-inf"), float("-inf"))
    assert result.equal_group_mean_gain == float("-inf")
    assert result.classification == "non_generalizing"


def test_group_mass_does_not_change_equal_group_decision_weighting():
    model = _organized_model()
    stable = model.copy()
    reversed_support = model[::-1].copy()

    small_large = score_independent_groups(
        model,
        {"stable": stable, "reversed": reversed_support * 1_000_000.0},
        base_axes=(0, 1),
        added_axes=(2,),
    )
    equal_mass = score_independent_groups(
        model,
        {"stable": stable, "reversed": reversed_support},
        base_axes=(0, 1),
        added_axes=(2,),
    )

    assert small_large.gains == pytest.approx(equal_mass.gains)
    assert small_large.classification == equal_mass.classification == "mixed"
    assert small_large.equal_group_mean_gain == pytest.approx(equal_mass.equal_group_mean_gain)


def test_grouped_masks_are_applied_by_group_and_unknown_masks_fail_closed():
    model = np.ones((1, 1, 2), dtype=float)
    heldout = np.ones_like(model)
    mask = np.zeros_like(model, dtype=bool)
    mask[0, 0, 1] = True

    result = score_independent_groups(
        model,
        {"masked": heldout},
        base_axes=(0, 1),
        added_axes=(2,),
        heldout_unavailable_masks={"masked": mask},
    )
    assert result.groups[0].score.heldout_total_mass == pytest.approx(1.0)

    with pytest.raises(ValueError, match="unknown groups"):
        score_independent_groups(
            model,
            {"masked": heldout},
            base_axes=(0, 1),
            added_axes=(2,),
            heldout_unavailable_masks={"other": mask},
        )


def test_empty_duplicate_and_invalid_group_ids_fail_closed():
    model = _organized_model()

    with pytest.raises(ValueError, match="at least one"):
        score_independent_groups(
            model,
            [],
            base_axes=(0, 1),
            added_axes=(2,),
        )

    with pytest.raises(ValueError, match="duplicate"):
        score_independent_groups(
            model,
            [("a", model), ("a", model)],
            base_axes=(0, 1),
            added_axes=(2,),
        )

    with pytest.raises(ValueError, match="non-empty strings"):
        score_independent_groups(
            model,
            [(" ", model)],
            base_axes=(0, 1),
            added_axes=(2,),
        )


def test_gain_tolerance_controls_group_classification_consistently():
    model = np.ones((2, 1, 2), dtype=float)
    result = score_independent_groups(
        model,
        {"a": model.copy(), "b": model.copy()},
        base_axes=(0, 1),
        added_axes=(2,),
        gain_tolerance=1e-6,
    )

    assert all(math.isclose(gain, 0.0, abs_tol=1e-12) for gain in result.gains)
    assert result.classification == "non_generalizing"


def test_known_truth_grouped_transferability_benchmark_recovers_all_categories():
    checks = run_grouped_transferability_benchmark()
    assert checks
    assert {check.family for check in checks} == {
        "all_stable",
        "stable_plus_shifted",
        "all_shifted",
    }
    assert all(check.passed for check in checks)
    assert grouped_transferability_benchmark_passes() is True
