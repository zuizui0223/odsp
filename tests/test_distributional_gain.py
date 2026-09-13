from __future__ import annotations

import math

import numpy as np
import pytest

from odsp.distributional_gain import (
    score_distributional_gain,
    score_distributional_groups,
)


def test_distributional_gain_is_weighted_log_score_difference() -> None:
    conditional = np.log(np.asarray([0.8, 0.6, 0.9]))
    baseline = np.log(np.asarray([0.5, 0.5, 0.5]))
    weights = np.asarray([1.0, 2.0, 3.0])
    result = score_distributional_gain(
        conditional,
        baseline,
        sample_weight=weights,
    )
    expected = float(np.sum(weights * (conditional - baseline)) / weights.sum())
    assert math.isclose(result.mean_log_score_gain, expected, abs_tol=1e-12)
    assert result.row_count == 3
    assert result.positive_weight_row_count == 3
    assert result.total_weight == 6.0


def test_common_rowwise_reference_measure_shift_cancels_exactly() -> None:
    conditional = np.asarray([-0.4, -0.8, -1.2, -0.3])
    baseline = np.asarray([-0.7, -0.7, -1.0, -0.5])
    weights = np.asarray([1.0, 2.0, 1.5, 0.5])
    shift = np.asarray([2.1, -3.4, 0.8, 5.2])
    original = score_distributional_gain(
        conditional, baseline, sample_weight=weights
    )
    shifted = score_distributional_gain(
        conditional + shift,
        baseline + shift,
        sample_weight=weights,
    )
    assert math.isclose(
        original.mean_log_score_gain,
        shifted.mean_log_score_gain,
        rel_tol=0.0,
        abs_tol=1e-12,
    )


def test_zero_conditional_mass_is_predictive_failure_not_unavailable() -> None:
    result = score_distributional_gain(
        [-0.2, float("-inf")],
        [-0.4, -0.5],
    )
    assert result.mean_log_score_gain == float("-inf")


def test_baseline_must_cover_every_positive_weight_realized_state() -> None:
    with pytest.raises(ValueError, match="baseline log score must be finite"):
        score_distributional_gain(
            [-0.2, -0.3],
            [-0.4, float("-inf")],
        )


def test_zero_weight_rows_do_not_force_finite_baseline() -> None:
    result = score_distributional_gain(
        [-0.2, -0.3],
        [-0.4, float("-inf")],
        sample_weight=[1.0, 0.0],
    )
    assert math.isclose(result.mean_log_score_gain, 0.2, abs_tol=1e-12)


def test_independent_group_rule_does_not_pool_conflicting_groups() -> None:
    grouped = score_distributional_groups(
        [
            ("large-positive", [-0.1] * 100, [-0.3] * 100),
            ("small-negative", [-0.5], [-0.4]),
        ]
    )
    assert grouped.gain_category == "mixed"
    assert grouped.groups[0].score.mean_log_score_gain > 0
    assert grouped.groups[1].score.mean_log_score_gain < 0


def test_group_weights_are_matched_by_group_name() -> None:
    grouped = score_distributional_groups(
        {
            "a": ([-0.2, -0.4], [-0.4, -0.5]),
            "b": ([-0.1, -0.2], [-0.3, -0.4]),
        },
        sample_weights={"a": [2.0, 1.0], "b": [1.0, 3.0]},
    )
    assert grouped.gain_category == "generalizing"
    with pytest.raises(ValueError, match="unknown groups"):
        score_distributional_groups(
            {"a": ([-0.2], [-0.3])},
            sample_weights={"a": [1.0], "ghost": [1.0]},
        )
