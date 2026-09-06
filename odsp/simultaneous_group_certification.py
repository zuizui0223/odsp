"""Simultaneous familywise uncertainty certification across validation groups.

This module strengthens ODSP's block-aware transfer audit when the scientific
claim is simultaneous across many independent validation groups.  Separate
per-group 95% intervals are retained as a marginal reference, but they are not
interpreted as a 95% familywise statement.  The primary familywise interval is a
two-sided studentized bootstrap max-t interval.  A Bonferroni-adjusted percentile
interval is returned as a conservative sensitivity reference.

The procedure is still an empirical bootstrap audit.  It depends on defensible
validation-group independence and caller-declared resampling blocks, and it does
not include uncertainty from refitting an upstream predictive learner.
"""
from __future__ import annotations

from dataclasses import asdict, dataclass
import hashlib
import math
from typing import Sequence

import numpy as np

from .transferability import classify_independent_gains


@dataclass(frozen=True)
class SimultaneousGroupCertificationRow:
    group_id: str
    row_count: int
    block_count: int
    total_weight: float
    mean_gain: float
    bootstrap_standard_error: float | None
    marginal_lower_bound: float | None
    marginal_upper_bound: float | None
    bonferroni_lower_bound: float | None
    bonferroni_upper_bound: float | None
    max_t_lower_bound: float | None
    max_t_upper_bound: float | None
    marginal_status: str
    bonferroni_status: str
    max_t_status: str
    estimable: bool

    def as_dict(self) -> dict[str, object]:
        return asdict(self)


@dataclass(frozen=True)
class SimultaneousGroupCertificationAudit:
    row_count: int
    group_count: int
    familywise_confidence_level: float
    bootstrap_draws: int
    seed: int
    minimum_blocks_per_group: int
    row_independence_assumed: bool
    mean_gain: float
    point_transfer_category: str
    marginal_interval_category: str
    bonferroni_transfer_category: str
    max_t_transfer_category: str
    simultaneous_admissible: bool
    max_t_critical_value: float | None
    bonferroni_per_tail_alpha: float
    unavailable_group_count: int
    max_t_uncertain_group_count: int
    max_t_robust_positive_group_count: int
    max_t_robust_nonpositive_group_count: int
    pooled_mean_can_override_group_failure: bool
    marginal_interval_can_override_simultaneous_failure: bool
    bonferroni_is_primary: bool
    aggregate_confidence_score_emitted: bool
    groups: tuple[SimultaneousGroupCertificationRow, ...]

    def as_dict(self) -> dict[str, object]:
        payload = asdict(self)
        payload["groups"] = [row.as_dict() for row in self.groups]
        return payload


def _weights(values: Sequence[float] | None, n: int) -> np.ndarray:
    if values is None:
        return np.ones(n, dtype=float)
    weight = np.asarray(values, dtype=float)
    if weight.shape != (n,):
        raise ValueError("sample_weight must contain one value per row")
    if not np.isfinite(weight).all() or np.any(weight < 0) or not np.any(weight > 0):
        raise ValueError("sample_weight must be finite, non-negative and positive in total")
    return weight


def _labels(values: Sequence[object], n: int, name: str) -> tuple[str, ...]:
    if len(values) != n:
        raise ValueError(f"{name} must contain one value per row")
    labels = tuple(str(value).strip() for value in values)
    if any(not value for value in labels):
        raise ValueError(f"{name} labels must be non-empty")
    return labels


def _weighted_mean(values: np.ndarray, weight: np.ndarray) -> float:
    total = float(np.sum(weight))
    if total <= 0.0:
        raise ValueError("weights must have positive total mass")
    return float(np.sum(values * weight) / total)


def _stable_seed(seed: int, group_id: str) -> int:
    digest = hashlib.sha256(f"{seed}|simultaneous|max-t|{group_id}".encode("utf-8")).digest()
    return int.from_bytes(digest[:8], "little", signed=False)


def _bootstrap_group_mean_sorted_blocks(
    gain: np.ndarray,
    weight: np.ndarray,
    block_labels: tuple[str, ...],
    *,
    draws: int,
    seed: int,
) -> np.ndarray:
    ordered_blocks = tuple(sorted(set(block_labels)))
    block_weight = np.empty(len(ordered_blocks), dtype=float)
    block_weighted_gain = np.empty(len(ordered_blocks), dtype=float)
    label_array = np.asarray(block_labels, dtype=object)
    for index, block_id in enumerate(ordered_blocks):
        mask = label_array == block_id
        local_weight = weight[mask]
        block_weight[index] = np.sum(local_weight)
        block_weighted_gain[index] = np.sum(gain[mask] * local_weight)

    rng = np.random.default_rng(seed)
    sampled = rng.integers(0, len(ordered_blocks), size=(draws, len(ordered_blocks)))
    denominator = np.sum(block_weight[sampled], axis=1)
    numerator = np.sum(block_weighted_gain[sampled], axis=1)
    return numerator / denominator


def _interval_status(lower: float | None, upper: float | None, tolerance: float) -> str:
    if lower is None or upper is None:
        return "unavailable"
    if lower > tolerance:
        return "robust_positive"
    if upper <= tolerance:
        return "robust_nonpositive"
    return "uncertain"


def _category(statuses: Sequence[str]) -> str:
    rows = tuple(statuses)
    if any(status == "unavailable" for status in rows):
        return "unavailable"
    if rows and all(status == "robust_positive" for status in rows):
        return "robust_generalizing"
    if rows and all(status == "robust_nonpositive" for status in rows):
        return "robust_non_generalizing"
    if any(status == "uncertain" for status in rows):
        return "uncertain"
    return "mixed"


def audit_simultaneous_group_certification(
    row_gain: Sequence[float],
    groups: Sequence[object],
    *,
    blocks: Sequence[object] | None = None,
    sample_weight: Sequence[float] | None = None,
    familywise_confidence_level: float = 0.95,
    bootstrap_draws: int = 4000,
    seed: int = 20260906,
    minimum_blocks_per_group: int = 8,
    gain_tolerance: float = 0.0,
) -> SimultaneousGroupCertificationAudit:
    """Audit transfer-gain signs simultaneously across independent groups.

    The same bootstrap samples are used to construct three interval families:
    ordinary marginal percentile intervals, Bonferroni-adjusted percentile
    intervals, and the primary studentized max-t simultaneous intervals.
    """

    gain = np.asarray(row_gain, dtype=float)
    if gain.ndim != 1 or gain.size == 0 or not np.isfinite(gain).all():
        raise ValueError("row_gain must be a non-empty finite one-dimensional vector")
    n = int(gain.size)
    group_labels = _labels(groups, n, "groups")
    weight = _weights(sample_weight, n)
    if not math.isfinite(familywise_confidence_level) or not 0.0 < familywise_confidence_level < 1.0:
        raise ValueError("familywise_confidence_level must lie strictly between zero and one")
    if not isinstance(bootstrap_draws, int) or bootstrap_draws < 500:
        raise ValueError("bootstrap_draws must be an integer >= 500")
    if not isinstance(minimum_blocks_per_group, int) or minimum_blocks_per_group < 2:
        raise ValueError("minimum_blocks_per_group must be an integer >= 2")
    if not isinstance(seed, int):
        raise ValueError("seed must be an integer")
    if not math.isfinite(gain_tolerance) or gain_tolerance < 0.0:
        raise ValueError("gain_tolerance must be finite and non-negative")

    row_independence_assumed = blocks is None
    if blocks is None:
        block_labels = tuple(f"row-{index:09d}" for index in range(n))
    else:
        block_labels = _labels(blocks, n, "blocks")

    ordered_groups = tuple(sorted(set(group_labels)))
    group_array = np.asarray(group_labels, dtype=object)
    block_array = np.asarray(block_labels, dtype=object)
    alpha = 1.0 - float(familywise_confidence_level)
    bonf_tail = alpha / (2.0 * len(ordered_groups))

    intermediate: list[dict[str, object]] = []
    point_gains: list[float] = []
    estimable_samples: list[np.ndarray] = []
    estimable_points: list[float] = []
    estimable_ses: list[float] = []
    estimable_indices: list[int] = []

    for group_id in ordered_groups:
        mask = group_array == group_id
        local_gain = gain[mask]
        local_weight = weight[mask]
        local_blocks = tuple(str(value) for value in block_array[mask])
        block_count = len(set(local_blocks))
        point = _weighted_mean(local_gain, local_weight)
        point_gains.append(point)
        record: dict[str, object] = {
            "group_id": group_id,
            "row_count": int(np.count_nonzero(mask)),
            "block_count": int(block_count),
            "total_weight": float(np.sum(local_weight)),
            "mean_gain": float(point),
            "estimable": bool(block_count >= minimum_blocks_per_group),
        }
        if block_count < minimum_blocks_per_group:
            record.update(
                bootstrap_standard_error=None,
                marginal_lower_bound=None,
                marginal_upper_bound=None,
                bonferroni_lower_bound=None,
                bonferroni_upper_bound=None,
                max_t_lower_bound=None,
                max_t_upper_bound=None,
                marginal_status="unavailable",
                bonferroni_status="unavailable",
                max_t_status="unavailable",
            )
            intermediate.append(record)
            continue

        samples = _bootstrap_group_mean_sorted_blocks(
            local_gain,
            local_weight,
            local_blocks,
            draws=bootstrap_draws,
            seed=_stable_seed(seed, group_id),
        )
        standard_error = float(np.std(samples, ddof=1))
        marginal_lower, marginal_upper = np.quantile(
            samples, [alpha / 2.0, 1.0 - alpha / 2.0]
        )
        bonf_lower, bonf_upper = np.quantile(
            samples, [bonf_tail, 1.0 - bonf_tail]
        )
        record.update(
            bootstrap_standard_error=standard_error,
            marginal_lower_bound=float(marginal_lower),
            marginal_upper_bound=float(marginal_upper),
            bonferroni_lower_bound=float(bonf_lower),
            bonferroni_upper_bound=float(bonf_upper),
            max_t_lower_bound=None,
            max_t_upper_bound=None,
            marginal_status=_interval_status(float(marginal_lower), float(marginal_upper), gain_tolerance),
            bonferroni_status=_interval_status(float(bonf_lower), float(bonf_upper), gain_tolerance),
            max_t_status="pending",
        )
        estimable_indices.append(len(intermediate))
        estimable_samples.append(samples)
        estimable_points.append(float(point))
        estimable_ses.append(standard_error)
        intermediate.append(record)

    max_t_critical: float | None = None
    if estimable_samples:
        sample_matrix = np.column_stack(estimable_samples)
        point_vector = np.asarray(estimable_points, dtype=float)
        se_vector = np.asarray(estimable_ses, dtype=float)
        standardized = np.zeros_like(sample_matrix)
        nonzero = se_vector > 1e-15
        if np.any(nonzero):
            standardized[:, nonzero] = (
                np.abs(sample_matrix[:, nonzero] - point_vector[nonzero])
                / se_vector[nonzero]
            )
        max_statistic = np.max(standardized, axis=1)
        max_t_critical = float(np.quantile(max_statistic, familywise_confidence_level))
        for matrix_index, record_index in enumerate(estimable_indices):
            point = point_vector[matrix_index]
            se = se_vector[matrix_index]
            lower = float(point - max_t_critical * se)
            upper = float(point + max_t_critical * se)
            intermediate[record_index]["max_t_lower_bound"] = lower
            intermediate[record_index]["max_t_upper_bound"] = upper
            intermediate[record_index]["max_t_status"] = _interval_status(lower, upper, gain_tolerance)

    rows = tuple(SimultaneousGroupCertificationRow(**record) for record in intermediate)
    marginal_category = _category([row.marginal_status for row in rows])
    bonf_category = _category([row.bonferroni_status for row in rows])
    max_t_category = _category([row.max_t_status for row in rows])
    max_t_statuses = [row.max_t_status for row in rows]

    return SimultaneousGroupCertificationAudit(
        row_count=n,
        group_count=len(rows),
        familywise_confidence_level=float(familywise_confidence_level),
        bootstrap_draws=int(bootstrap_draws),
        seed=int(seed),
        minimum_blocks_per_group=int(minimum_blocks_per_group),
        row_independence_assumed=bool(row_independence_assumed),
        mean_gain=_weighted_mean(gain, weight),
        point_transfer_category=classify_independent_gains(point_gains, tolerance=gain_tolerance),
        marginal_interval_category=marginal_category,
        bonferroni_transfer_category=bonf_category,
        max_t_transfer_category=max_t_category,
        simultaneous_admissible=bool(max_t_category == "robust_generalizing"),
        max_t_critical_value=max_t_critical,
        bonferroni_per_tail_alpha=float(bonf_tail),
        unavailable_group_count=max_t_statuses.count("unavailable"),
        max_t_uncertain_group_count=max_t_statuses.count("uncertain"),
        max_t_robust_positive_group_count=max_t_statuses.count("robust_positive"),
        max_t_robust_nonpositive_group_count=max_t_statuses.count("robust_nonpositive"),
        pooled_mean_can_override_group_failure=False,
        marginal_interval_can_override_simultaneous_failure=False,
        bonferroni_is_primary=False,
        aggregate_confidence_score_emitted=False,
        groups=rows,
    )
