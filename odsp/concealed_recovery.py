"""Concealed known-truth recovery for ODSP Chapter 2.

The generating support tensor is used only by the data generator and final truth
scoring.  The estimator receives sampled state counts only.  This separates the
question "is the metric analytically correct?" from "can it be recovered from
finite observations without reading the generating tensor?".

This benchmark is synthetic development evidence.  It does not establish that
opportunistic GBIF/iNaturalist counts are unbiased use probabilities.
"""
from __future__ import annotations

from dataclasses import asdict, dataclass
from typing import Sequence

import numpy as np

from .niche_geometry import NicheThicknessProfile, niche_thickness_profile
from .projection_loss import ProjectionOverlapProfile, projection_overlap_profile
from .synthetic_benchmark import (
    coupled_vertical_temporal,
    habitat_capacity_pair,
    independent_vertical_temporal,
    joint_only_partition_pair,
    planar_sufficiency,
    pure_temporal_thickness,
    pure_vertical_thickness,
    temporal_partition_pair,
    vertical_partition_pair,
)


DEFAULT_SAMPLE_SIZE = 100_000
DEFAULT_RANDOM_SEED = 2026090102
THICKNESS_ABSOLUTE_TOLERANCE = 0.08
OVERLAP_ABSOLUTE_TOLERANCE = 0.03


@dataclass(frozen=True)
class ConcealedRecoveryCheck:
    family: str
    metric: str
    truth: float
    estimate: float
    absolute_error: float
    tolerance: float
    passed: bool

    def as_dict(self) -> dict[str, object]:
        return asdict(self)


@dataclass(frozen=True)
class ConcealedRecoveryBenchmark:
    sample_size: int
    random_seed: int
    checks: tuple[ConcealedRecoveryCheck, ...]

    @property
    def passed(self) -> bool:
        return bool(self.checks) and all(check.passed for check in self.checks)

    def as_dict(self) -> dict[str, object]:
        return {
            "sample_size": self.sample_size,
            "random_seed": self.random_seed,
            "passed": self.passed,
            "checks": [check.as_dict() for check in self.checks],
        }


def sample_state_counts(
    hidden_support: np.ndarray,
    *,
    n_observations: int,
    random_state: int,
) -> np.ndarray:
    """Sample a finite observation-count tensor from a hidden support field."""

    support = np.asarray(hidden_support, dtype=float)
    if support.size == 0 or support.ndim < 2:
        raise ValueError("hidden_support must be a non-empty array with at least two axes")
    if not np.isfinite(support).all() or np.any(support < 0):
        raise ValueError("hidden_support must be finite and non-negative")
    total = float(support.sum())
    if not total > 0:
        raise ValueError("hidden_support must have positive mass")
    n = int(n_observations)
    if n < 1:
        raise ValueError("n_observations must be >= 1")
    seed = int(random_state)
    probability = (support / total).reshape(-1)
    rng = np.random.default_rng(seed)
    counts = rng.multinomial(n, probability).reshape(support.shape)
    return counts.astype(float, copy=False)


def estimate_thickness_from_counts(
    sampled_counts: np.ndarray,
    *,
    horizontal_axes: Sequence[int] = (0, 1),
    vertical_axis: int | None = None,
    temporal_axis: int | None = None,
) -> NicheThicknessProfile:
    """Estimate niche thickness using sampled counts only, with no truth access."""

    return niche_thickness_profile(
        sampled_counts,
        horizontal_axes=horizontal_axes,
        vertical_axis=vertical_axis,
        temporal_axis=temporal_axis,
    )


def estimate_projection_overlap_from_counts(
    sampled_counts_a: np.ndarray,
    sampled_counts_b: np.ndarray,
    *,
    horizontal_axes: Sequence[int] = (0, 1),
    vertical_axis: int | None = None,
    temporal_axis: int | None = None,
) -> ProjectionOverlapProfile:
    """Estimate projection overlap using two sampled count tensors only."""

    return projection_overlap_profile(
        sampled_counts_a,
        sampled_counts_b,
        horizontal_axes=horizontal_axes,
        vertical_axis=vertical_axis,
        temporal_axis=temporal_axis,
    )


def _check(
    family: str,
    metric: str,
    truth: float,
    estimate: float,
    tolerance: float,
) -> ConcealedRecoveryCheck:
    error = abs(float(estimate) - float(truth))
    return ConcealedRecoveryCheck(
        family=family,
        metric=metric,
        truth=float(truth),
        estimate=float(estimate),
        absolute_error=error,
        tolerance=float(tolerance),
        passed=bool(np.isfinite(error) and error <= tolerance),
    )


def _thickness_checks(
    family: str,
    hidden_truth: np.ndarray,
    *,
    n_observations: int,
    random_state: int,
    vertical_axis: int = 2,
    temporal_axis: int = 3,
) -> list[ConcealedRecoveryCheck]:
    # Estimation happens from sampled counts before the truth profile is opened.
    sampled = sample_state_counts(
        hidden_truth,
        n_observations=n_observations,
        random_state=random_state,
    )
    estimated = estimate_thickness_from_counts(
        sampled,
        horizontal_axes=(0, 1),
        vertical_axis=vertical_axis,
        temporal_axis=temporal_axis,
    )
    truth = niche_thickness_profile(
        hidden_truth,
        horizontal_axes=(0, 1),
        vertical_axis=vertical_axis,
        temporal_axis=temporal_axis,
    )
    return [
        _check(
            family,
            "effective_vertical_states",
            truth.effective_vertical_states,
            estimated.effective_vertical_states,
            THICKNESS_ABSOLUTE_TOLERANCE,
        ),
        _check(
            family,
            "effective_temporal_states",
            truth.effective_temporal_states,
            estimated.effective_temporal_states,
            THICKNESS_ABSOLUTE_TOLERANCE,
        ),
        _check(
            family,
            "effective_joint_vertical_temporal_states",
            truth.effective_joint_vertical_temporal_states,
            estimated.effective_joint_vertical_temporal_states,
            THICKNESS_ABSOLUTE_TOLERANCE,
        ),
    ]


def _overlap_checks(
    family: str,
    hidden_truth_a: np.ndarray,
    hidden_truth_b: np.ndarray,
    *,
    n_observations: int,
    random_state: int,
) -> list[ConcealedRecoveryCheck]:
    sampled_a = sample_state_counts(
        hidden_truth_a,
        n_observations=n_observations,
        random_state=random_state,
    )
    sampled_b = sample_state_counts(
        hidden_truth_b,
        n_observations=n_observations,
        random_state=random_state + 1,
    )
    estimated = estimate_projection_overlap_from_counts(
        sampled_a,
        sampled_b,
        horizontal_axes=(0, 1),
        vertical_axis=2,
        temporal_axis=3,
    )
    truth = projection_overlap_profile(
        hidden_truth_a,
        hidden_truth_b,
        horizontal_axes=(0, 1),
        vertical_axis=2,
        temporal_axis=3,
    )
    checks = [
        _check(
            family,
            "horizontal_overlap",
            truth.horizontal_overlap,
            estimated.horizontal_overlap,
            OVERLAP_ABSOLUTE_TOLERANCE,
        ),
        _check(
            family,
            "full_overlap",
            truth.full_overlap,
            estimated.full_overlap,
            OVERLAP_ABSOLUTE_TOLERANCE,
        ),
        _check(
            family,
            "planar_overlap_inflation",
            truth.planar_overlap_inflation,
            estimated.planar_overlap_inflation,
            OVERLAP_ABSOLUTE_TOLERANCE,
        ),
    ]
    if truth.joint_only_projection_inflation is not None:
        checks.append(
            _check(
                family,
                "joint_only_projection_inflation",
                truth.joint_only_projection_inflation,
                estimated.joint_only_projection_inflation,
                OVERLAP_ABSOLUTE_TOLERANCE,
            )
        )
    return checks


def run_concealed_recovery_benchmark(
    *,
    n_observations: int = DEFAULT_SAMPLE_SIZE,
    random_seed: int = DEFAULT_RANDOM_SEED,
) -> ConcealedRecoveryBenchmark:
    """Run the frozen finite-observation Chapter-2 recovery benchmark."""

    n = int(n_observations)
    seed = int(random_seed)
    checks: list[ConcealedRecoveryCheck] = []

    thickness_families = (
        ("planar_sufficiency", planar_sufficiency()),
        ("pure_vertical", pure_vertical_thickness(vertical_states=4)),
        ("pure_temporal", pure_temporal_thickness(temporal_states=3)),
        (
            "independent_zt",
            independent_vertical_temporal(vertical_states=2, temporal_states=3),
        ),
        ("coupled_zt", coupled_vertical_temporal()),
    )
    for index, (family, truth) in enumerate(thickness_families):
        checks.extend(
            _thickness_checks(
                family,
                truth,
                n_observations=n,
                random_state=seed + 100 * index,
            )
        )

    pair_families = (
        ("vertical_partition_pair", *vertical_partition_pair()),
        ("temporal_partition_pair", *temporal_partition_pair()),
        ("joint_only_partition", *joint_only_partition_pair()),
    )
    for index, (family, truth_a, truth_b) in enumerate(pair_families):
        checks.extend(
            _overlap_checks(
                family,
                truth_a,
                truth_b,
                n_observations=n,
                random_state=seed + 10_000 + 100 * index,
            )
        )

    # Capacity ordering is estimated without reading the analytic truth profile.
    simple_truth, layered_truth = habitat_capacity_pair(layered_vertical_states=5)
    simple_counts = sample_state_counts(
        simple_truth, n_observations=n, random_state=seed + 20_000
    )
    layered_counts = sample_state_counts(
        layered_truth, n_observations=n, random_state=seed + 20_001
    )
    simple_estimate = niche_thickness_profile(
        simple_counts, horizontal_axes=(0, 1), vertical_axis=2
    ).effective_vertical_states
    layered_estimate = niche_thickness_profile(
        layered_counts, horizontal_axes=(0, 1), vertical_axis=2
    ).effective_vertical_states
    checks.append(
        ConcealedRecoveryCheck(
            family="habitat_capacity",
            metric="layered_minus_simple_effective_vertical_states_positive",
            truth=1.0,
            estimate=1.0 if layered_estimate > simple_estimate else 0.0,
            absolute_error=0.0 if layered_estimate > simple_estimate else 1.0,
            tolerance=0.0,
            passed=bool(layered_estimate > simple_estimate),
        )
    )

    return ConcealedRecoveryBenchmark(
        sample_size=n,
        random_seed=seed,
        checks=tuple(checks),
    )
