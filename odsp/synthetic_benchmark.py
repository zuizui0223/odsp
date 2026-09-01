"""Frozen known-truth synthetic benchmark families for Chapter 2."""
from __future__ import annotations

from dataclasses import dataclass
import math

import numpy as np

from .niche_geometry import niche_thickness_profile
from .projection_loss import projection_overlap_profile


@dataclass(frozen=True)
class SyntheticCheck:
    family: str
    metric: str
    observed: float
    expected: float
    passed: bool


def _check(
    family: str,
    metric: str,
    observed: float | None,
    expected: float,
    *,
    atol: float = 1e-10,
) -> SyntheticCheck:
    value = float("nan") if observed is None else float(observed)
    return SyntheticCheck(
        family=family,
        metric=metric,
        observed=value,
        expected=float(expected),
        passed=bool(np.isfinite(value) and abs(value - expected) <= atol),
    )


def planar_sufficiency(*, shape: tuple[int, int] = (3, 4)) -> np.ndarray:
    support = np.ones((*shape, 1, 1), dtype=float)
    return support


def pure_vertical_thickness(
    *, vertical_states: int = 4, shape: tuple[int, int] = (2, 3)
) -> np.ndarray:
    return np.ones((*shape, int(vertical_states), 1), dtype=float)


def pure_temporal_thickness(
    *, temporal_states: int = 3, shape: tuple[int, int] = (2, 3)
) -> np.ndarray:
    return np.ones((*shape, 1, int(temporal_states)), dtype=float)


def independent_vertical_temporal(
    *,
    vertical_states: int = 2,
    temporal_states: int = 3,
    shape: tuple[int, int] = (2, 2),
) -> np.ndarray:
    return np.ones(
        (*shape, int(vertical_states), int(temporal_states)), dtype=float
    )


def coupled_vertical_temporal(
    *, shape: tuple[int, int] = (2, 2)
) -> np.ndarray:
    support = np.zeros((*shape, 2, 2), dtype=float)
    support[:, :, 0, 0] = 1.0
    support[:, :, 1, 1] = 1.0
    return support


def vertical_partition_pair(
    *, shape: tuple[int, int] = (2, 2)
) -> tuple[np.ndarray, np.ndarray]:
    a = np.zeros((*shape, 2, 1), dtype=float)
    b = np.zeros_like(a)
    a[:, :, 0, 0] = 1.0
    b[:, :, 1, 0] = 1.0
    return a, b


def temporal_partition_pair(
    *, shape: tuple[int, int] = (2, 2)
) -> tuple[np.ndarray, np.ndarray]:
    a = np.zeros((*shape, 1, 2), dtype=float)
    b = np.zeros_like(a)
    a[:, :, 0, 0] = 1.0
    b[:, :, 0, 1] = 1.0
    return a, b


def joint_only_partition_pair(
    *, shape: tuple[int, int] = (2, 2)
) -> tuple[np.ndarray, np.ndarray]:
    a = np.zeros((*shape, 2, 2), dtype=float)
    b = np.zeros_like(a)
    a[:, :, 0, 0] = 1.0
    a[:, :, 1, 1] = 1.0
    b[:, :, 0, 1] = 1.0
    b[:, :, 1, 0] = 1.0
    return a, b


def simple_layered_habitat_pair(
    *, shape: tuple[int, int] = (2, 2), layered_states: int = 4
) -> tuple[np.ndarray, np.ndarray]:
    simple = np.ones((*shape, 1), dtype=float)
    layered = np.ones((*shape, int(layered_states)), dtype=float)
    return simple, layered


def run_known_truth_synthetic_benchmark() -> tuple[SyntheticCheck, ...]:
    """Run the frozen Chapter-2 analytic benchmark families.

    Historical metric labels are retained so existing benchmark outputs remain
    comparable. The z-t quantity itself is now referenced by its exact name,
    conditional mutual information ``I(Z;T|X,Y)``.
    """

    checks: list[SyntheticCheck] = []

    planar = niche_thickness_profile(
        planar_sufficiency(), horizontal_axes=(0, 1), vertical_axis=2, temporal_axis=3
    )
    checks += [
        _check("planar_sufficiency", "effective_vertical_states", planar.effective_vertical_states, 1.0),
        _check("planar_sufficiency", "effective_temporal_states", planar.effective_temporal_states, 1.0),
        _check("planar_sufficiency", "effective_joint_states", planar.effective_joint_vertical_temporal_states, 1.0),
    ]

    vertical = niche_thickness_profile(
        pure_vertical_thickness(vertical_states=4),
        horizontal_axes=(0, 1),
        vertical_axis=2,
        temporal_axis=3,
    )
    checks += [
        _check("pure_vertical", "effective_vertical_states", vertical.effective_vertical_states, 4.0),
        _check("pure_vertical", "effective_temporal_states", vertical.effective_temporal_states, 1.0),
    ]

    temporal = niche_thickness_profile(
        pure_temporal_thickness(temporal_states=3),
        horizontal_axes=(0, 1),
        vertical_axis=2,
        temporal_axis=3,
    )
    checks += [
        _check("pure_temporal", "effective_vertical_states", temporal.effective_vertical_states, 1.0),
        _check("pure_temporal", "effective_temporal_states", temporal.effective_temporal_states, 3.0),
    ]

    independent = niche_thickness_profile(
        independent_vertical_temporal(vertical_states=2, temporal_states=3),
        horizontal_axes=(0, 1),
        vertical_axis=2,
        temporal_axis=3,
    )
    checks += [
        _check("independent_zt", "effective_vertical_states", independent.effective_vertical_states, 2.0),
        _check("independent_zt", "effective_temporal_states", independent.effective_temporal_states, 3.0),
        _check("independent_zt", "effective_joint_states", independent.effective_joint_vertical_temporal_states, 6.0),
        _check(
            "independent_zt",
            "zt_interaction_information",
            independent.vertical_temporal_conditional_mutual_information_nats,
            0.0,
        ),
    ]

    coupled = niche_thickness_profile(
        coupled_vertical_temporal(),
        horizontal_axes=(0, 1),
        vertical_axis=2,
        temporal_axis=3,
    )
    checks += [
        _check("coupled_zt", "effective_vertical_states", coupled.effective_vertical_states, 2.0),
        _check("coupled_zt", "effective_temporal_states", coupled.effective_temporal_states, 2.0),
        _check("coupled_zt", "effective_joint_states", coupled.effective_joint_vertical_temporal_states, 2.0),
        _check(
            "coupled_zt",
            "zt_interaction_information",
            coupled.vertical_temporal_conditional_mutual_information_nats,
            math.log(2.0),
        ),
    ]

    vertical_a, vertical_b = vertical_partition_pair()
    vertical_overlap = projection_overlap_profile(
        vertical_a,
        vertical_b,
        horizontal_axes=(0, 1),
        vertical_axis=2,
        temporal_axis=3,
    )
    checks += [
        _check("vertical_partition_pair", "horizontal_overlap", vertical_overlap.horizontal_overlap, 1.0),
        _check("vertical_partition_pair", "full_overlap", vertical_overlap.full_overlap, 0.0),
        _check("vertical_partition_pair", "planar_overlap_inflation", vertical_overlap.planar_overlap_inflation, 1.0),
    ]

    temporal_a, temporal_b = temporal_partition_pair()
    temporal_overlap = projection_overlap_profile(
        temporal_a,
        temporal_b,
        horizontal_axes=(0, 1),
        vertical_axis=2,
        temporal_axis=3,
    )
    checks += [
        _check("temporal_partition_pair", "horizontal_overlap", temporal_overlap.horizontal_overlap, 1.0),
        _check("temporal_partition_pair", "full_overlap", temporal_overlap.full_overlap, 0.0),
        _check("temporal_partition_pair", "planar_overlap_inflation", temporal_overlap.planar_overlap_inflation, 1.0),
    ]

    joint_a, joint_b = joint_only_partition_pair()
    joint_overlap = projection_overlap_profile(
        joint_a,
        joint_b,
        horizontal_axes=(0, 1),
        vertical_axis=2,
        temporal_axis=3,
    )
    checks += [
        _check("joint_only_partition_pair", "horizontal_overlap", joint_overlap.horizontal_overlap, 1.0),
        _check("joint_only_partition_pair", "vertical_overlap", joint_overlap.horizontal_vertical_overlap, 1.0),
        _check("joint_only_partition_pair", "temporal_overlap", joint_overlap.horizontal_temporal_overlap, 1.0),
        _check("joint_only_partition_pair", "full_overlap", joint_overlap.full_overlap, 0.0),
        _check("joint_only_partition_pair", "joint_only_overlap_inflation", joint_overlap.joint_only_overlap_inflation, 1.0),
    ]

    simple, layered = simple_layered_habitat_pair(layered_states=4)
    simple_profile = niche_thickness_profile(
        simple, horizontal_axes=(0, 1), vertical_axis=2
    )
    layered_profile = niche_thickness_profile(
        layered, horizontal_axes=(0, 1), vertical_axis=2
    )
    checks += [
        _check("simple_habitat_capacity", "effective_vertical_states", simple_profile.effective_vertical_states, 1.0),
        _check("layered_habitat_capacity", "effective_vertical_states", layered_profile.effective_vertical_states, 4.0),
    ]

    return tuple(checks)
