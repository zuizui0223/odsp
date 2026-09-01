"""Analytically known synthetic benchmarks for ODSP Chapter 2.

These fixtures validate the niche-thickness and projection-loss quantities before
an empirical habitat-complexity result is used. They are not empirical evidence
and they do not tune SDMR Product A.
"""
from __future__ import annotations

from dataclasses import asdict, dataclass
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
    tolerance: float
    passed: bool

    def as_dict(self) -> dict[str, object]:
        return asdict(self)


def planar_sufficiency(*, y: int = 2, x: int = 3) -> np.ndarray:
    return np.ones((y, x, 1, 1), dtype=float)


def pure_vertical_thickness(
    *, y: int = 2, x: int = 3, vertical_states: int = 4
) -> np.ndarray:
    if vertical_states < 1:
        raise ValueError("vertical_states must be >= 1")
    return np.ones((y, x, vertical_states, 1), dtype=float)


def pure_temporal_thickness(
    *, y: int = 2, x: int = 3, temporal_states: int = 3
) -> np.ndarray:
    if temporal_states < 1:
        raise ValueError("temporal_states must be >= 1")
    return np.ones((y, x, 1, temporal_states), dtype=float)


def independent_vertical_temporal(
    *, y: int = 2, x: int = 3, vertical_states: int = 2, temporal_states: int = 3
) -> np.ndarray:
    if vertical_states < 1 or temporal_states < 1:
        raise ValueError("state counts must be >= 1")
    return np.ones((y, x, vertical_states, temporal_states), dtype=float)


def coupled_vertical_temporal(*, y: int = 2, x: int = 3) -> np.ndarray:
    """Two z and two t states with only matched z-t combinations allowed."""

    support = np.zeros((y, x, 2, 2), dtype=float)
    support[:, :, 0, 0] = 1.0
    support[:, :, 1, 1] = 1.0
    return support


def vertical_partition_pair(*, y: int = 2, x: int = 3) -> tuple[np.ndarray, np.ndarray]:
    """Identical x-y marginals but disjoint vertical strata."""

    a = np.zeros((y, x, 2, 1), dtype=float)
    b = np.zeros_like(a)
    a[:, :, 0, 0] = 1.0
    b[:, :, 1, 0] = 1.0
    return a, b


def temporal_partition_pair(*, y: int = 2, x: int = 3) -> tuple[np.ndarray, np.ndarray]:
    """Identical x-y marginals but disjoint activity times."""

    a = np.zeros((y, x, 1, 4), dtype=float)
    b = np.zeros_like(a)
    a[:, :, 0, :2] = 1.0
    b[:, :, 0, 2:] = 1.0
    return a, b


def joint_only_partition_pair() -> tuple[np.ndarray, np.ndarray]:
    """Identical x-y, z and t marginals but disjoint z×t joint states."""

    a = np.zeros((1, 1, 2, 2), dtype=float)
    b = np.zeros_like(a)
    a[0, 0, 0, 0] = 1.0
    a[0, 0, 1, 1] = 1.0
    b[0, 0, 0, 1] = 1.0
    b[0, 0, 1, 0] = 1.0
    return a, b


def habitat_capacity_pair(
    *, y: int = 2, x: int = 3, layered_vertical_states: int = 5
) -> tuple[np.ndarray, np.ndarray]:
    """Same x-y footprint, simple one-layer versus evenly layered support."""

    if layered_vertical_states < 1:
        raise ValueError("layered_vertical_states must be >= 1")
    simple = np.ones((y, x, 1), dtype=float)
    layered = np.ones((y, x, layered_vertical_states), dtype=float)
    return simple, layered


def _check(
    family: str,
    metric: str,
    observed: float,
    expected: float,
    *,
    tolerance: float = 1e-10,
) -> SyntheticCheck:
    passed = bool(math.isfinite(observed) and abs(observed - expected) <= tolerance)
    return SyntheticCheck(
        family=family,
        metric=metric,
        observed=float(observed),
        expected=float(expected),
        tolerance=float(tolerance),
        passed=passed,
    )


def run_known_truth_synthetic_benchmark() -> tuple[SyntheticCheck, ...]:
    """Run the frozen Chapter-2 analytic benchmark families."""

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
        _check("independent_zt", "zt_interaction_information", independent.vertical_temporal_interaction_information_nats, 0.0),
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
        _check("coupled_zt", "zt_interaction_information", coupled.vertical_temporal_interaction_information_nats, math.log(2.0)),
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
        _check("joint_only_partition", "horizontal_overlap", joint_overlap.horizontal_overlap, 1.0),
        _check("joint_only_partition", "horizontal_vertical_overlap", joint_overlap.horizontal_vertical_overlap, 1.0),
        _check("joint_only_partition", "horizontal_temporal_overlap", joint_overlap.horizontal_temporal_overlap, 1.0),
        _check("joint_only_partition", "full_overlap", joint_overlap.full_overlap, 0.0),
        _check("joint_only_partition", "joint_only_projection_inflation", joint_overlap.joint_only_projection_inflation, 1.0),
    ]

    simple, layered = habitat_capacity_pair(layered_vertical_states=5)
    simple_profile = niche_thickness_profile(
        simple, horizontal_axes=(0, 1), vertical_axis=2
    )
    layered_profile = niche_thickness_profile(
        layered, horizontal_axes=(0, 1), vertical_axis=2
    )
    checks += [
        _check("habitat_capacity", "simple_effective_vertical_states", simple_profile.effective_vertical_states, 1.0),
        _check("habitat_capacity", "layered_effective_vertical_states", layered_profile.effective_vertical_states, 5.0),
    ]

    return tuple(checks)


def benchmark_passes() -> bool:
    return all(check.passed for check in run_known_truth_synthetic_benchmark())
