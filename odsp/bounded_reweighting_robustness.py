"""Worst-case transfer robustness under bounded row reweighting.

The caller supplies a multiplicative bound ``gamma >= 1``.  Relative to optional
base weights, every validation row may be multiplied independently by any value in
``[1/gamma, gamma]``.  ODSP then solves the minimum and maximum possible weighted
mean gain in each independent group.  This is a deterministic sensitivity envelope,
not a sampling-uncertainty interval and not an inferred bias correction.
"""
from __future__ import annotations

from dataclasses import asdict, dataclass
import math
from typing import Sequence

import numpy as np

from .transferability import classify_independent_gains


@dataclass(frozen=True)
class BoundedReweightingGroup:
    group_id: str
    row_count: int
    total_base_weight: float
    point_mean_gain: float
    worst_case_mean_gain: float
    best_case_mean_gain: float
    status: str
    critical_gamma: float | None

    def as_dict(self) -> dict[str, object]:
        return asdict(self)


@dataclass(frozen=True)
class BoundedReweightingAudit:
    row_count: int
    group_count: int
    gamma: float
    multiplier_lower: float
    multiplier_upper: float
    maximum_multiplier_ratio: float
    point_transfer_category: str
    envelope_transfer_category: str
    envelope_admissible: bool
    minimum_worst_case_group_gain: float
    maximum_best_case_group_gain: float
    pooled_mean_can_override_group_failure: bool
    automatic_bias_correction_performed: bool
    aggregate_confidence_score_emitted: bool
    groups: tuple[BoundedReweightingGroup, ...]

    def as_dict(self) -> dict[str, object]:
        payload = asdict(self)
        payload["groups"] = [row.as_dict() for row in self.groups]
        return payload


def _validate_vector(values: Sequence[float], name: str, *, expected: int | None = None) -> np.ndarray:
    array = np.asarray(values, dtype=float)
    if array.ndim != 1 or array.size == 0:
        raise ValueError(f"{name} must be a non-empty one-dimensional vector")
    if expected is not None and array.size != expected:
        raise ValueError(f"{name} has an unexpected length")
    if not np.isfinite(array).all():
        raise ValueError(f"{name} must contain only finite values")
    return array


def _validate_weights(values: Sequence[float] | None, n: int) -> np.ndarray:
    if values is None:
        return np.ones(n, dtype=float)
    weight = np.asarray(values, dtype=float)
    if weight.shape != (n,):
        raise ValueError("base_weight must contain one value per row")
    if not np.isfinite(weight).all() or np.any(weight < 0) or not np.any(weight > 0):
        raise ValueError("base_weight must be finite, non-negative and positive in total")
    return weight


def _validate_groups(values: Sequence[object], n: int) -> tuple[str, ...]:
    if len(values) != n:
        raise ValueError("groups must contain one value per row")
    labels = tuple(str(value).strip() for value in values)
    if any(not value for value in labels):
        raise ValueError("group labels must be non-empty")
    return labels


def _validate_gamma(gamma: float) -> float:
    value = float(gamma)
    if not math.isfinite(value) or value < 1.0:
        raise ValueError("gamma must be finite and >= 1")
    return value


def _weighted_mean(values: np.ndarray, weight: np.ndarray) -> float:
    return float(np.sum(values * weight) / np.sum(weight))


def extreme_bounded_weighted_mean(
    gain: Sequence[float],
    *,
    base_weight: Sequence[float] | None = None,
    gamma: float = 1.0,
    minimize: bool = True,
    iterations: int = 100,
) -> float:
    """Solve the exact linear-fractional endpoint optimum to numerical precision.

    For a trial mean ``m``, minimizing ``sum(w*r*(gain-m))`` assigns the upper
    multiplier to negative residuals and the lower multiplier to positive
    residuals.  The optimum mean is the unique zero of that monotone function.
    Maximization reverses those assignments.
    """

    values = _validate_vector(gain, "gain")
    weight = _validate_weights(base_weight, values.size)
    bound = _validate_gamma(gamma)
    if not isinstance(iterations, int) or iterations < 20:
        raise ValueError("iterations must be an integer >= 20")
    if np.all(values == values[0]):
        return float(values[0])
    if bound == 1.0:
        return _weighted_mean(values, weight)

    lower_multiplier = 1.0 / bound
    upper_multiplier = bound
    lo = float(np.min(values))
    hi = float(np.max(values))

    def objective(mean: float) -> float:
        residual = values - mean
        if minimize:
            multiplier = np.where(residual < 0.0, upper_multiplier, lower_multiplier)
        else:
            multiplier = np.where(residual > 0.0, upper_multiplier, lower_multiplier)
        return float(np.sum(weight * multiplier * residual))

    for _ in range(iterations):
        mid = (lo + hi) / 2.0
        value = objective(mid)
        if value > 0.0:
            lo = mid
        else:
            hi = mid
    return float((lo + hi) / 2.0)


def _critical_gamma(
    gain: np.ndarray,
    weight: np.ndarray,
    *,
    point_mean: float,
    gain_tolerance: float,
    search_upper_bound: float,
    iterations: int = 80,
) -> float | None:
    if search_upper_bound <= 1.0:
        raise ValueError("critical gamma search upper bound must exceed one")
    point_positive = point_mean > gain_tolerance

    def destroyed(gamma: float) -> bool:
        if point_positive:
            return extreme_bounded_weighted_mean(
                gain, base_weight=weight, gamma=gamma, minimize=True
            ) <= gain_tolerance
        return extreme_bounded_weighted_mean(
            gain, base_weight=weight, gamma=gamma, minimize=False
        ) > gain_tolerance

    if not destroyed(search_upper_bound):
        return None
    lo = 1.0
    hi = float(search_upper_bound)
    for _ in range(iterations):
        mid = (lo + hi) / 2.0
        if destroyed(mid):
            hi = mid
        else:
            lo = mid
    return float(hi)


def audit_bounded_reweighting_robustness(
    row_gain: Sequence[float],
    groups: Sequence[object],
    *,
    base_weight: Sequence[float] | None = None,
    gamma: float = 2.0,
    gain_tolerance: float = 0.0,
    critical_gamma_search_upper_bound: float = 100.0,
) -> BoundedReweightingAudit:
    gain = _validate_vector(row_gain, "row_gain")
    n = int(gain.size)
    labels = _validate_groups(groups, n)
    weight = _validate_weights(base_weight, n)
    bound = _validate_gamma(gamma)
    if not math.isfinite(gain_tolerance) or gain_tolerance < 0:
        raise ValueError("gain_tolerance must be finite and non-negative")
    if not math.isfinite(critical_gamma_search_upper_bound) or critical_gamma_search_upper_bound <= 1.0:
        raise ValueError("critical_gamma_search_upper_bound must be finite and > 1")

    group_array = np.asarray(labels, dtype=object)
    ordered_groups = tuple(dict.fromkeys(labels))
    rows: list[BoundedReweightingGroup] = []
    point_gains: list[float] = []

    for group_id in ordered_groups:
        mask = group_array == group_id
        local_gain = gain[mask]
        local_weight = weight[mask]
        point = _weighted_mean(local_gain, local_weight)
        worst = extreme_bounded_weighted_mean(
            local_gain, base_weight=local_weight, gamma=bound, minimize=True
        )
        best = extreme_bounded_weighted_mean(
            local_gain, base_weight=local_weight, gamma=bound, minimize=False
        )
        if worst > gain_tolerance:
            status = "robust_positive"
        elif best <= gain_tolerance:
            status = "robust_nonpositive"
        else:
            status = "bound_sensitive"
        critical = _critical_gamma(
            local_gain,
            local_weight,
            point_mean=point,
            gain_tolerance=gain_tolerance,
            search_upper_bound=critical_gamma_search_upper_bound,
        )
        point_gains.append(point)
        rows.append(
            BoundedReweightingGroup(
                group_id=group_id,
                row_count=int(np.count_nonzero(mask)),
                total_base_weight=float(np.sum(local_weight)),
                point_mean_gain=float(point),
                worst_case_mean_gain=float(worst),
                best_case_mean_gain=float(best),
                status=status,
                critical_gamma=critical,
            )
        )

    statuses = [row.status for row in rows]
    if all(status == "robust_positive" for status in statuses):
        category = "gamma_robust_generalizing"
    elif all(status == "robust_nonpositive" for status in statuses):
        category = "gamma_robust_non_generalizing"
    elif any(status == "bound_sensitive" for status in statuses):
        category = "gamma_sensitive"
    else:
        category = "gamma_mixed"

    return BoundedReweightingAudit(
        row_count=n,
        group_count=len(rows),
        gamma=float(bound),
        multiplier_lower=float(1.0 / bound),
        multiplier_upper=float(bound),
        maximum_multiplier_ratio=float(bound * bound),
        point_transfer_category=classify_independent_gains(point_gains, tolerance=gain_tolerance),
        envelope_transfer_category=category,
        envelope_admissible=bool(category == "gamma_robust_generalizing"),
        minimum_worst_case_group_gain=float(min(row.worst_case_mean_gain for row in rows)),
        maximum_best_case_group_gain=float(max(row.best_case_mean_gain for row in rows)),
        pooled_mean_can_override_group_failure=False,
        automatic_bias_correction_performed=False,
        aggregate_confidence_score_emitted=False,
        groups=tuple(rows),
    )
