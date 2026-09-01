import numpy as np
import pytest

from odsp.projection_loss import projection_overlap_profile, schoener_overlap


def test_vertical_partition_can_be_invisible_in_xy():
    a = np.zeros((2, 3, 2), dtype=float)
    b = np.zeros_like(a)
    a[:, :, 0] = 1.0
    b[:, :, 1] = 1.0

    profile = projection_overlap_profile(
        a,
        b,
        horizontal_axes=(0, 1),
        vertical_axis=2,
    )

    assert profile.horizontal_overlap == pytest.approx(1.0)
    assert profile.horizontal_vertical_overlap == pytest.approx(0.0)
    assert profile.full_overlap == pytest.approx(0.0)
    assert profile.planar_overlap_inflation == pytest.approx(1.0)
    assert profile.vertical_projection_inflation == pytest.approx(1.0)


def test_temporal_partition_can_be_invisible_in_xy():
    a = np.zeros((2, 2, 4), dtype=float)
    b = np.zeros_like(a)
    a[:, :, :2] = 1.0
    b[:, :, 2:] = 1.0

    profile = projection_overlap_profile(
        a,
        b,
        horizontal_axes=(0, 1),
        temporal_axis=2,
    )

    assert profile.horizontal_overlap == pytest.approx(1.0)
    assert profile.horizontal_temporal_overlap == pytest.approx(0.0)
    assert profile.temporal_projection_inflation == pytest.approx(1.0)


def test_joint_z_time_partition_can_hide_from_each_single_axis():
    a = np.zeros((1, 1, 2, 2), dtype=float)
    b = np.zeros_like(a)
    a[0, 0, 0, 0] = 1.0
    a[0, 0, 1, 1] = 1.0
    b[0, 0, 0, 1] = 1.0
    b[0, 0, 1, 0] = 1.0

    profile = projection_overlap_profile(
        a,
        b,
        horizontal_axes=(0, 1),
        vertical_axis=2,
        temporal_axis=3,
    )

    assert profile.horizontal_overlap == pytest.approx(1.0)
    assert profile.horizontal_vertical_overlap == pytest.approx(1.0)
    assert profile.horizontal_temporal_overlap == pytest.approx(1.0)
    assert profile.horizontal_vertical_temporal_overlap == pytest.approx(0.0)
    assert profile.full_overlap == pytest.approx(0.0)
    assert profile.joint_only_projection_inflation == pytest.approx(1.0)


def test_equal_support_has_full_overlap_one_at_every_projection():
    support = np.arange(1, 1 + 2 * 2 * 3 * 4, dtype=float).reshape(2, 2, 3, 4)
    profile = projection_overlap_profile(
        support,
        support * 7.0,
        horizontal_axes=(0, 1),
        vertical_axis=2,
        temporal_axis=3,
    )
    assert profile.full_overlap == pytest.approx(1.0)
    assert profile.horizontal_overlap == pytest.approx(1.0)
    assert profile.planar_overlap_inflation == pytest.approx(0.0)


def test_schoener_overlap_respects_common_unavailable_mask():
    a = np.ones((1, 2, 2), dtype=float)
    b = np.ones_like(a)
    b[0, 1, 1] = 1000.0
    unavailable = np.zeros_like(a, dtype=bool)
    unavailable[0, 1, 1] = True

    assert schoener_overlap(a, b, unavailable_mask=unavailable) == pytest.approx(1.0)
