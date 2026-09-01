import math

import numpy as np
import pytest

from odsp.niche_geometry import (
    axis_thickness_map,
    conditional_information,
    effective_conditional_states,
    niche_thickness_profile,
)


def test_single_vertical_layer_has_unit_thickness():
    support = np.ones((3, 4, 1), dtype=float)
    profile = niche_thickness_profile(
        support,
        horizontal_axes=(0, 1),
        vertical_axis=2,
    )
    assert profile.vertical_information_nats == pytest.approx(0.0)
    assert profile.effective_vertical_states == pytest.approx(1.0)
    assert profile.added_axis_information_nats == pytest.approx(0.0)


def test_even_four_layer_forest_has_effective_vertical_thickness_four():
    support = np.ones((2, 3, 4), dtype=float)
    profile = niche_thickness_profile(
        support,
        horizontal_axes=(0, 1),
        vertical_axis=2,
    )
    assert profile.vertical_information_nats == pytest.approx(math.log(4.0))
    assert profile.effective_vertical_states == pytest.approx(4.0)
    assert profile.effective_added_states == pytest.approx(4.0)


def test_local_thickness_map_separates_thin_and_layered_horizontal_cells():
    support = np.zeros((1, 2, 4), dtype=float)
    support[0, 0, 0] = 1.0
    support[0, 1, :] = 1.0

    result = axis_thickness_map(
        support,
        horizontal_axes=(0, 1),
        added_axes=(2,),
    )

    assert result.effective_states.shape == (1, 2)
    assert result.effective_states[0, 0] == pytest.approx(1.0)
    assert result.effective_states[0, 1] == pytest.approx(4.0)
    assert result.information_nats[0, 0] == pytest.approx(0.0)
    assert result.information_nats[0, 1] == pytest.approx(math.log(4.0))


def test_zero_support_horizontal_cells_are_unknown_not_unit_thickness():
    support = np.zeros((1, 2, 2), dtype=float)
    support[0, 0, :] = 1.0

    result = axis_thickness_map(
        support,
        horizontal_axes=(0, 1),
        added_axes=(2,),
    )

    assert result.effective_states[0, 0] == pytest.approx(2.0)
    assert np.isnan(result.effective_states[0, 1])
    assert result.horizontal_mass[0, 1] == pytest.approx(0.0)


def test_temporal_thickness_is_conditional_on_horizontal_location():
    support = np.zeros((2, 1, 2), dtype=float)
    support[0, 0, 0] = 1.0
    support[1, 0, 1] = 1.0

    profile = niche_thickness_profile(
        support,
        horizontal_axes=(0, 1),
        temporal_axis=2,
    )

    # Time is perfectly determined by x-y, so it adds no uncertainty after
    # location is known even though two time states occur globally.
    assert profile.temporal_information_nats == pytest.approx(0.0)
    assert profile.effective_temporal_states == pytest.approx(1.0)


def test_two_time_states_within_every_cell_have_thickness_two():
    support = np.ones((2, 2, 2), dtype=float)
    profile = niche_thickness_profile(
        support,
        horizontal_axes=(0, 1),
        temporal_axis=2,
    )
    assert profile.temporal_information_nats == pytest.approx(math.log(2.0))
    assert profile.effective_temporal_states == pytest.approx(2.0)


def test_joint_vertical_temporal_state_space_can_be_four():
    support = np.ones((1, 2, 2, 2), dtype=float)
    profile = niche_thickness_profile(
        support,
        horizontal_axes=(0, 1),
        vertical_axis=2,
        temporal_axis=3,
    )
    assert profile.effective_vertical_states == pytest.approx(2.0)
    assert profile.effective_temporal_states == pytest.approx(2.0)
    assert profile.effective_joint_vertical_temporal_states == pytest.approx(4.0)
    assert profile.vertical_temporal_conditional_mutual_information_nats == pytest.approx(
        0.0
    )


def test_z_time_conditional_dependence_reduces_joint_effective_states():
    support = np.zeros((1, 1, 2, 2), dtype=float)
    support[0, 0, 0, 0] = 1.0
    support[0, 0, 1, 1] = 1.0
    profile = niche_thickness_profile(
        support,
        horizontal_axes=(0, 1),
        vertical_axis=2,
        temporal_axis=3,
    )
    assert profile.effective_vertical_states == pytest.approx(2.0)
    assert profile.effective_temporal_states == pytest.approx(2.0)
    assert profile.effective_joint_vertical_temporal_states == pytest.approx(2.0)
    assert profile.vertical_temporal_conditional_mutual_information_nats == pytest.approx(
        math.log(2.0)
    )


def test_conditional_information_ignores_unlisted_axes_by_marginalizing():
    support = np.ones((2, 2, 3, 5), dtype=float)
    value = conditional_information(
        support,
        base_axes=(0, 1),
        added_axes=(2,),
    )
    assert value == pytest.approx(math.log(3.0))
    assert effective_conditional_states(
        support,
        base_axes=(0, 1),
        added_axes=(2,),
    ) == pytest.approx(3.0)


def test_local_map_preserves_requested_horizontal_axis_order():
    support = np.ones((2, 3, 4), dtype=float)
    result = axis_thickness_map(
        support,
        horizontal_axes=(1, 0),
        added_axes=(2,),
    )
    assert result.effective_states.shape == (3, 2)
    assert np.allclose(result.effective_states, 4.0)


def test_unavailable_states_are_removed_before_normalization():
    support = np.ones((1, 1, 3), dtype=float)
    unavailable = np.zeros_like(support, dtype=bool)
    unavailable[..., 2] = True
    profile = niche_thickness_profile(
        support,
        horizontal_axes=(0, 1),
        vertical_axis=2,
        unavailable_mask=unavailable,
    )
    assert profile.effective_vertical_states == pytest.approx(2.0)


def test_invalid_support_fails_closed():
    with pytest.raises(ValueError, match="non-negative"):
        niche_thickness_profile(
            np.array([[[1.0, -1.0]]]),
            horizontal_axes=(0, 1),
            temporal_axis=2,
        )
    with pytest.raises(ValueError, match="distinct"):
        niche_thickness_profile(
            np.ones((1, 1, 2)),
            horizontal_axes=(0, 1),
            vertical_axis=1,
        )
    with pytest.raises(ValueError, match="disjoint"):
        axis_thickness_map(
            np.ones((1, 1, 2)),
            horizontal_axes=(0, 1),
            added_axes=(1,),
        )
