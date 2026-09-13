"""Familywise certification of predictive-resolution transfer ceilings.

The point predictive-resolution ladder decomposes held-out predictive utility
across ordered information levels. This module adds a simultaneous uncertainty
layer across the entire group x resolution-step family.

Within each independent group, caller-declared resampling blocks are sampled with
replacement. The same sampled block indices are used for every resolution step in
that group, preserving cross-step bootstrap covariance. Studentized deviations
are then combined across all estimable group-step cells through one global max-t
critical value. The resulting intervals therefore support a familywise statement
about the whole predictive-resolution ladder rather than a collection of
uncorrected per-step intervals.

The certified transfer ceiling advances only through consecutive resolution steps
that are simultaneously robust-positive for every independent group. A positive
total gain cannot skip over an uncertain, mixed, unavailable or robust-nonpositive
resolution increment.
"""
from __future__ import annotations

from dataclasses import asdict, dataclass
import hashlib
import math
from typing import Sequence

import numpy as np

from .predictive_resolution import (
    _validate_groups,
    _validate_levels,
    _validate_weights,
    decompose_predictive_resolution,
)


@dataclass(frozen=True)
class ResolutionCertificationCell:
    """One group x adjacent-resolution simultaneous interval."""

    group: object
    lower_level: str
    upper_level: str
    row_count: int
    block_count: int
    total_weight: float
    mean_gain: float
    bootstrap_standard_error: float | None
    lower_bound: float | None
    upper_bound: float | None
    status: str
    estimable: bool

    def as_dict(self) -> dict[str, object]:
        return asdict(self)


@dataclass(frozen=True)
class ResolutionStepCertification:
    """All-group simultaneous status for one adjacent resolution step."""

    lower_level: str
    upper_level: str
    category: str
    robust_positive_group_count: int
    robust_nonpositive_group_count: int
    uncertain_group_count: int
    unavailable_group_count: int
    groups: tuple[ResolutionCertificationCell, ...]

    def as_dict(self) -> dict[str, object]:
        payload = asdict(self)
        payload["groups"] = [row.as_dict() for row in self.groups]
        return payload


@dataclass(frozen=True)
class PredictiveResolutionCertification:
    """Familywise certification result for an ordered predictive-resolution ladder."""

    levels: tuple[str, ...]
    familywise_confidence_level: float
    bootstrap_draws: int
    seed: int
    minimum_blocks_per_group: int
    row_independence_assumed: bool
    max_t_critical_value: float | None
    cell_count: int
    estimable_cell_count: int
    all_steps_estimable: bool
    point_transfer_ceiling: str
    certified_transfer_ceiling: str
    steps: tuple[ResolutionStepCertification, ...]

    def as_dict(self) -> dict[str, object]:
        payload = asdict(self)
        payload["steps"] = [row.as_dict() for row in self.steps]
        return payload


def _stable_group_seed(seed: int, group: object) -> int:
    digest = hashlib.sha256(
        f"{seed}|predictive-resolution|max-t|{group!r}".encode("utf-8")
    ).digest()
    return int.from_bytes(digest[:8], "little", signed=False)


def _block_labels(
    blocks: Sequence[object] | None,
    n: int,
) -> tuple[np.ndarray, bool]:
    if blocks is None:
        return np.asarray([f"row-{index:09d}" for index in range(n)], dtype=object), True
    values = np.asarray(list(blocks), dtype=object)
    if values.shape != (n,):
        raise ValueError("blocks must contain one value per score row")
    for value in values.tolist():
        if value is None:
            raise ValueError("block labels may not be missing")
        try:
            hash(value)
        except TypeError as exc:
            raise ValueError("block labels must be hashable") from exc
    return values, False


def _cell_status(
    lower: float | None,
    upper: float | None,
    *,
    tolerance: float,
) -> str:
    if lower is None or upper is None:
        return "unavailable"
    if lower > tolerance:
        return "robust_positive"
    if upper <= tolerance:
        return "robust_nonpositive"
    return "uncertain"


def _step_category(statuses: Sequence[str]) -> str:
    values = tuple(statuses)
    if not values:
        raise ValueError("step certification requires at least one independent group")
    if any(value == "unavailable" for value in values):
        return "unavailable"
    if all(value == "robust_positive" for value in values):
        return "robust_generalizing"
    if all(value == "robust_nonpositive" for value in values):
        return "robust_non_generalizing"
    if any(value == "uncertain" for value in values):
        return "uncertain"
    return "mixed"


def _bootstrap_group_steps(
    row_gains: np.ndarray,
    weight: np.ndarray,
    block: np.ndarray,
    *,
    draws: int,
    seed: int,
) -> tuple[np.ndarray, np.ndarray, int]:
    """Return point means and aligned block-bootstrap means for all steps."""

    positive = weight > 0
    gain = np.asarray(row_gains[positive], dtype=float)
    local_weight = np.asarray(weight[positive], dtype=float)
    local_block = np.asarray(block[positive], dtype=object)
    ordered_blocks = tuple(dict.fromkeys(local_block.tolist()))
    block_count = len(ordered_blocks)
    step_count = gain.shape[1]

    block_weight = np.empty(block_count, dtype=float)
    block_weighted_gain = np.empty((block_count, step_count), dtype=float)
    for index, block_id in enumerate(ordered_blocks):
        mask = local_block == block_id
        local = local_weight[mask]
        block_weight[index] = float(np.sum(local))
        block_weighted_gain[index, :] = np.sum(gain[mask] * local[:, None], axis=0)

    total_weight = float(np.sum(block_weight))
    point = np.sum(block_weighted_gain, axis=0) / total_weight
    rng = np.random.default_rng(seed)
    sampled = rng.integers(0, block_count, size=(draws, block_count))
    denominator = np.sum(block_weight[sampled], axis=1)
    numerator = np.sum(block_weighted_gain[sampled, :], axis=1)
    samples = numerator / denominator[:, None]
    return point, samples, block_count


def certify_predictive_resolution(
    levels: Sequence[tuple[str, Sequence[float]]],
    groups: Sequence[object],
    *,
    blocks: Sequence[object] | None = None,
    sample_weight: Sequence[float] | None = None,
    familywise_confidence_level: float = 0.95,
    bootstrap_draws: int = 4000,
    seed: int = 20260913,
    minimum_blocks_per_group: int = 8,
    gain_tolerance: float = 0.0,
) -> PredictiveResolutionCertification:
    """Certify a predictive transfer ceiling jointly over groups and resolution steps.

    Every predictive level must be evaluated on the same held-out rows using the
    same score orientation. Adjacent row-wise score differences define the
    resolution increments. Comparator levels must be finite on all positive-weight
    rows; the richest level may contain ``-inf`` as a valid predictive failure.

    Cells with non-finite row gains or too few positive-weight resampling blocks
    are marked ``unavailable`` and cannot be crossed by the certified ceiling.
    When ``blocks`` is omitted each positive-weight row is treated as its own
    resampling block, which is recorded as ``row_independence_assumed=True``.

    This procedure quantifies held-out scoring uncertainty conditional on the
    supplied predictive scores. It does not add upstream learner-refit uncertainty.
    """

    if not math.isfinite(familywise_confidence_level) or not (
        0.0 < familywise_confidence_level < 1.0
    ):
        raise ValueError(
            "familywise_confidence_level must lie strictly between zero and one"
        )
    if not isinstance(bootstrap_draws, int) or bootstrap_draws < 500:
        raise ValueError("bootstrap_draws must be an integer >= 500")
    if not isinstance(seed, int):
        raise ValueError("seed must be an integer")
    if not isinstance(minimum_blocks_per_group, int) or minimum_blocks_per_group < 2:
        raise ValueError("minimum_blocks_per_group must be an integer >= 2")
    if not math.isfinite(gain_tolerance) or gain_tolerance < 0:
        raise ValueError("gain_tolerance must be finite and non-negative")

    names, score_arrays = _validate_levels(levels)
    n = int(score_arrays[0].size)
    group_array = _validate_groups(groups, n)
    weight = _validate_weights(sample_weight, n)
    block_array, row_independence_assumed = _block_labels(blocks, n)

    # Reuse the point decomposition as the single source of truth for point
    # transfer categories and the point transfer ceiling. It also enforces the
    # fail-closed support rule for intermediate comparators.
    point_result = decompose_predictive_resolution(
        levels,
        groups,
        sample_weight=weight,
        gain_tolerance=gain_tolerance,
    )

    step_count = len(names) - 1
    row_gains = np.column_stack(
        [score_arrays[index + 1] - score_arrays[index] for index in range(step_count)]
    )
    ordered_groups = tuple(dict.fromkeys(group_array.tolist()))

    # Build aligned bootstrap arrays separately by group. Each group's resampled
    # block indices are shared across all resolution steps, preserving their
    # within-group covariance. Only finite, sufficiently blocked cells enter the
    # global max-t family.
    records: dict[tuple[int, int], dict[str, object]] = {}
    bootstrap_columns: list[np.ndarray] = []
    bootstrap_points: list[float] = []
    bootstrap_ses: list[float] = []
    bootstrap_keys: list[tuple[int, int]] = []

    for group_index, group in enumerate(ordered_groups):
        group_mask = group_array == group
        local_weight = weight[group_mask]
        local_blocks = block_array[group_mask]
        positive = local_weight > 0
        if not np.any(positive):
            raise ValueError(f"group {group!r} has zero total score weight")
        positive_block_count = len(set(local_blocks[positive].tolist()))
        local_gain = row_gains[group_mask]
        finite_step = np.all(np.isfinite(local_gain[positive]), axis=0)

        point_means: np.ndarray | None = None
        samples: np.ndarray | None = None
        if positive_block_count >= minimum_blocks_per_group and np.any(finite_step):
            # Replace unavailable step columns by zero only for the shared block
            # resampling operation. They never enter the max-t family or output
            # intervals; finite step columns are unchanged.
            safe_gain = local_gain.copy()
            safe_gain[:, ~finite_step] = 0.0
            point_means, samples, _ = _bootstrap_group_steps(
                safe_gain,
                local_weight,
                local_blocks,
                draws=bootstrap_draws,
                seed=_stable_group_seed(seed, group),
            )

        for step_index in range(step_count):
            key = (group_index, step_index)
            point_gain = point_result.groups[group_index].increments[step_index].mean_gain
            estimable = bool(
                positive_block_count >= minimum_blocks_per_group
                and finite_step[step_index]
                and math.isfinite(point_gain)
                and samples is not None
                and point_means is not None
            )
            records[key] = {
                "group": group,
                "lower_level": names[step_index],
                "upper_level": names[step_index + 1],
                "row_count": int(np.count_nonzero(group_mask)),
                "block_count": int(positive_block_count),
                "total_weight": float(np.sum(local_weight)),
                "mean_gain": float(point_gain),
                "bootstrap_standard_error": None,
                "lower_bound": None,
                "upper_bound": None,
                "status": "unavailable",
                "estimable": estimable,
            }
            if estimable:
                column = samples[:, step_index]
                standard_error = float(np.std(column, ddof=1))
                records[key]["bootstrap_standard_error"] = standard_error
                bootstrap_columns.append(column)
                bootstrap_points.append(float(point_means[step_index]))
                bootstrap_ses.append(standard_error)
                bootstrap_keys.append(key)

    critical: float | None = None
    if bootstrap_columns:
        matrix = np.column_stack(bootstrap_columns)
        point_vector = np.asarray(bootstrap_points, dtype=float)
        se_vector = np.asarray(bootstrap_ses, dtype=float)
        standardized = np.zeros_like(matrix)
        nonzero = se_vector > 1e-15
        if np.any(nonzero):
            standardized[:, nonzero] = (
                np.abs(matrix[:, nonzero] - point_vector[nonzero])
                / se_vector[nonzero]
            )
        max_statistic = np.max(standardized, axis=1)
        critical = float(np.quantile(max_statistic, familywise_confidence_level))
        for column_index, key in enumerate(bootstrap_keys):
            point = float(records[key]["mean_gain"])
            se = se_vector[column_index]
            lower = float(point - critical * se)
            upper = float(point + critical * se)
            records[key]["lower_bound"] = lower
            records[key]["upper_bound"] = upper
            records[key]["status"] = _cell_status(
                lower,
                upper,
                tolerance=gain_tolerance,
            )

    steps: list[ResolutionStepCertification] = []
    for step_index in range(step_count):
        cells = tuple(
            ResolutionCertificationCell(**records[(group_index, step_index)])
            for group_index in range(len(ordered_groups))
        )
        statuses = [cell.status for cell in cells]
        category = _step_category(statuses)
        steps.append(
            ResolutionStepCertification(
                lower_level=names[step_index],
                upper_level=names[step_index + 1],
                category=category,
                robust_positive_group_count=statuses.count("robust_positive"),
                robust_nonpositive_group_count=statuses.count("robust_nonpositive"),
                uncertain_group_count=statuses.count("uncertain"),
                unavailable_group_count=statuses.count("unavailable"),
                groups=cells,
            )
        )

    certified_ceiling = names[0]
    for step_index, step in enumerate(steps):
        if step.category == "robust_generalizing":
            certified_ceiling = names[step_index + 1]
        else:
            break

    estimable_count = sum(
        cell.estimable for step in steps for cell in step.groups
    )
    return PredictiveResolutionCertification(
        levels=names,
        familywise_confidence_level=float(familywise_confidence_level),
        bootstrap_draws=int(bootstrap_draws),
        seed=int(seed),
        minimum_blocks_per_group=int(minimum_blocks_per_group),
        row_independence_assumed=bool(row_independence_assumed),
        max_t_critical_value=critical,
        cell_count=int(len(ordered_groups) * step_count),
        estimable_cell_count=int(estimable_count),
        all_steps_estimable=bool(estimable_count == len(ordered_groups) * step_count),
        point_transfer_ceiling=point_result.all_group_point_transfer_ceiling,
        certified_transfer_ceiling=certified_ceiling,
        steps=tuple(steps),
    )
