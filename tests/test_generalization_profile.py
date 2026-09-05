from __future__ import annotations

import numpy as np

from odsp.generalization_profile import generalization_profile_from_probability_field


def test_profile_preserves_fine_level_failure_even_when_coarse_level_is_positive():
    true_probability = np.array([0.80, 0.82, 0.75, 0.78, 0.90, 0.88, 0.45, 0.46])
    probability = np.column_stack([true_probability, 1.0 - true_probability])
    y = np.array(["used"] * probability.shape[0], dtype=object)

    profile = generalization_profile_from_probability_field(
        probability,
        y,
        classes=("used", "other"),
        marginal_probability=np.array([0.5, 0.5]),
        groupings={
            "individual": ["i1", "i1", "i2", "i2", "i3", "i3", "i4", "i4"],
            "species": ["spA", "spA", "spA", "spA", "spB", "spB", "spB", "spB"],
        },
    )

    individual, species = profile.levels
    assert individual.gain_category == "mixed"
    assert individual.positive_group_count == 3
    assert individual.nonpositive_group_count == 1
    assert species.gain_category == "generalizing"
    assert species.positive_group_count == 2
    assert profile.fine_level_failures_may_not_be_overridden is True


def test_group_mass_weighting_is_explicit_and_zero_weight_rows_do_not_dominate():
    probability = np.array(
        [
            [0.8, 0.2],
            [0.8, 0.2],
            [0.1, 0.9],
        ]
    )
    y = [0, 0, 0]
    profile = generalization_profile_from_probability_field(
        probability,
        y,
        classes=(0, 1),
        marginal_probability=np.array([0.5, 0.5]),
        groupings={"individual": ["a", "a", "a"]},
        sample_weight=[1.0, 1.0, 0.0],
    )
    level = profile.levels[0]
    assert level.gain_category == "generalizing"
    assert level.groups[0].row_count == 3
    assert level.groups[0].total_weight == 2.0
    assert level.groups[0].mean_log_score_gain > 0


def test_profile_rejects_in_sample_shaped_grouping_errors():
    probability = np.array([[0.6, 0.4], [0.7, 0.3]])
    try:
        generalization_profile_from_probability_field(
            probability,
            [0, 0],
            classes=(0, 1),
            marginal_probability=np.array([0.5, 0.5]),
            groupings={"individual": ["a"]},
        )
    except ValueError as exc:
        assert "one value per row" in str(exc)
    else:
        raise AssertionError("expected grouping length mismatch to fail")
