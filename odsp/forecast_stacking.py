"""Group-safe probabilistic forecast stacking for ecological-state densities.

Stacking weights are learned on a dedicated tuning split only.  Final validation
rows are never used to update the weights.  Member-model calibration or conformal
coverage is not inherited by the stacked density: a stacked forecast must be
recalibrated on a separate calibration split before any coverage claim is made.
"""
from __future__ import annotations

from dataclasses import asdict, dataclass
import math
from typing import Sequence

import numpy as np

from .transferability import classify_independent_gains


@dataclass(frozen=True)
class ForecastStackingFit:
    candidate_names: tuple[str, ...]
    weights: tuple[float, ...]
    tuning_row_count: int
    tuning_total_weight: float
    iterations: int
    converged: bool
    mean_stacked_log_density: float
    mean_equal_weight_log_density: float
    objective_improvement: float
    validation_used_for_fit: bool
    coverage_inherited_from_members: bool
    requires_independent_recalibration: bool

    def as_dict(self) -> dict[str, object]:
        return asdict(self)


@dataclass(frozen=True)
class ForecastStackingGroupScore:
    group_id: str
    row_count: int
    total_weight: float
    mean_log_density_gain: float

    def as_dict(self) -> dict[str, object]:
        return asdict(self)


@dataclass(frozen=True)
class ForecastStackingValidation:
    row_count: int
    group_count: int
    mean_stacked_log_density: float
    mean_marginal_log_density: float
    mean_log_density_gain: float
    equal_group_mean_gain: float
    minimum_group_gain: float
    maximum_group_gain: float
    positive_group_count: int
    nonpositive_group_count: int
    transfer_category: str
    transfer_admissible: bool
    coverage_inherited_from_members: bool
    requires_independent_recalibration: bool
    aggregate_confidence_score_emitted: bool
    groups: tuple[ForecastStackingGroupScore, ...]

    def as_dict(self) -> dict[str, object]:
        payload = asdict(self)
        payload["groups"] = [row.as_dict() for row in self.groups]
        return payload


def _validate_matrix(values: Sequence[Sequence[float]], name: str) -> np.ndarray:
    array = np.asarray(values, dtype=float)
    if array.ndim != 2 or array.shape[0] == 0 or array.shape[1] < 2:
        raise ValueError(f"{name} must be a non-empty two-dimensional matrix with at least two candidates")
    if not np.isfinite(array).all():
        raise ValueError(f"{name} must contain only finite values")
    return array


def _validate_vector(values: Sequence[float], name: str, *, expected: int) -> np.ndarray:
    array = np.asarray(values, dtype=float)
    if array.shape != (expected,):
        raise ValueError(f"{name} must contain one value per row")
    if not np.isfinite(array).all():
        raise ValueError(f"{name} must contain only finite values")
    return array


def _validate_weights(values: Sequence[float] | None, n: int) -> np.ndarray:
    if values is None:
        return np.ones(n, dtype=float)
    weight = np.asarray(values, dtype=float)
    if weight.shape != (n,):
        raise ValueError("sample_weight must contain one value per row")
    if not np.isfinite(weight).all() or np.any(weight < 0) or not np.any(weight > 0):
        raise ValueError("sample_weight must be finite, non-negative and positive in total")
    return weight


def _candidate_names(values: Sequence[object] | None, k: int) -> tuple[str, ...]:
    if values is None:
        return tuple(f"candidate_{index + 1}" for index in range(k))
    if len(values) != k:
        raise ValueError("candidate_names must contain one name per candidate column")
    names = tuple(str(value).strip() for value in values)
    if any(not value for value in names) or len(set(names)) != len(names):
        raise ValueError("candidate_names must be non-empty and unique")
    return names


def _logsumexp_rows(log_values: np.ndarray) -> np.ndarray:
    maximum = np.max(log_values, axis=1, keepdims=True)
    return (maximum[:, 0] + np.log(np.sum(np.exp(log_values - maximum), axis=1)))


def _mixture_log_density(log_density: np.ndarray, weights: np.ndarray) -> np.ndarray:
    if weights.ndim != 1 or weights.size != log_density.shape[1]:
        raise ValueError("weights do not match candidate columns")
    if np.any(weights < 0) or not np.isfinite(weights).all() or not np.sum(weights) > 0:
        raise ValueError("weights must be finite, non-negative and positive in total")
    normalized = weights / np.sum(weights)
    safe = np.maximum(normalized, np.finfo(float).tiny)
    return _logsumexp_rows(log_density + np.log(safe)[None, :])


def _weighted_mean(values: np.ndarray, weight: np.ndarray) -> float:
    total = float(np.sum(weight))
    if not total > 0:
        raise ValueError("weights must have positive total mass")
    return float(np.sum(values * weight) / total)


def fit_log_score_stacking(
    candidate_log_density: Sequence[Sequence[float]],
    *,
    candidate_names: Sequence[object] | None = None,
    sample_weight: Sequence[float] | None = None,
    max_iter: int = 10000,
    tolerance: float = 1e-12,
) -> ForecastStackingFit:
    """Fit convex stacking weights by EM on a dedicated tuning split.

    The objective is the weighted mean log density of the fixed candidate-density
    mixture.  Because component densities are fixed, optimizing mixture weights is
    a concave problem.  EM provides monotone updates from strictly positive equal
    initial weights.
    """

    log_density = _validate_matrix(candidate_log_density, "candidate_log_density")
    n, k = log_density.shape
    names = _candidate_names(candidate_names, k)
    weight = _validate_weights(sample_weight, n)
    if not isinstance(max_iter, int) or max_iter < 1:
        raise ValueError("max_iter must be a positive integer")
    if not math.isfinite(tolerance) or tolerance <= 0:
        raise ValueError("tolerance must be finite and positive")

    mixture_weight = np.full(k, 1.0 / k, dtype=float)
    equal_log_density = _mixture_log_density(log_density, mixture_weight)
    equal_objective = _weighted_mean(equal_log_density, weight)
    total_weight = float(np.sum(weight))
    converged = False
    iterations = 0

    for iteration in range(1, max_iter + 1):
        safe = np.maximum(mixture_weight, np.finfo(float).tiny)
        log_joint = log_density + np.log(safe)[None, :]
        log_mix = _logsumexp_rows(log_joint)
        responsibility = np.exp(log_joint - log_mix[:, None])
        new_weight = np.sum(responsibility * weight[:, None], axis=0) / total_weight
        new_weight = np.maximum(new_weight, np.finfo(float).tiny)
        new_weight /= np.sum(new_weight)
        iterations = iteration
        if float(np.max(np.abs(new_weight - mixture_weight))) <= tolerance:
            mixture_weight = new_weight
            converged = True
            break
        mixture_weight = new_weight

    stacked = _mixture_log_density(log_density, mixture_weight)
    objective = _weighted_mean(stacked, weight)
    return ForecastStackingFit(
        candidate_names=names,
        weights=tuple(float(value) for value in mixture_weight),
        tuning_row_count=int(n),
        tuning_total_weight=total_weight,
        iterations=int(iterations),
        converged=bool(converged),
        mean_stacked_log_density=float(objective),
        mean_equal_weight_log_density=float(equal_objective),
        objective_improvement=float(objective - equal_objective),
        validation_used_for_fit=False,
        coverage_inherited_from_members=False,
        requires_independent_recalibration=True,
    )


def stacked_log_density(
    fit: ForecastStackingFit,
    candidate_log_density: Sequence[Sequence[float]],
    *,
    candidate_names: Sequence[object] | None = None,
) -> np.ndarray:
    """Evaluate a frozen stack on new rows without updating its weights."""

    log_density = _validate_matrix(candidate_log_density, "candidate_log_density")
    if log_density.shape[1] != len(fit.weights):
        raise ValueError("candidate columns do not match fitted stacking weights")
    names = _candidate_names(candidate_names, log_density.shape[1]) if candidate_names is not None else fit.candidate_names
    if tuple(names) != tuple(fit.candidate_names):
        raise ValueError("candidate_names/order must match the fitted stack")
    return _mixture_log_density(log_density, np.asarray(fit.weights, dtype=float))


def evaluate_stacked_forecast(
    fit: ForecastStackingFit,
    candidate_log_density: Sequence[Sequence[float]],
    marginal_log_density: Sequence[float],
    groups: Sequence[object],
    *,
    candidate_names: Sequence[object] | None = None,
    sample_weight: Sequence[float] | None = None,
    gain_tolerance: float = 1e-12,
) -> ForecastStackingValidation:
    """Score frozen stacking weights on untouched independent validation groups."""

    log_density = _validate_matrix(candidate_log_density, "candidate_log_density")
    n = log_density.shape[0]
    marginal = _validate_vector(marginal_log_density, "marginal_log_density", expected=n)
    weight = _validate_weights(sample_weight, n)
    if len(groups) != n:
        raise ValueError("groups must contain one value per validation row")
    labels = tuple(str(value).strip() for value in groups)
    if any(not label for label in labels):
        raise ValueError("group labels must be non-empty")
    if not math.isfinite(gain_tolerance) or gain_tolerance < 0:
        raise ValueError("gain_tolerance must be finite and non-negative")

    stacked = stacked_log_density(fit, log_density, candidate_names=candidate_names)
    gain = stacked - marginal
    ordered_groups = tuple(dict.fromkeys(labels))
    group_rows: list[ForecastStackingGroupScore] = []
    group_gains: list[float] = []
    for group_id in ordered_groups:
        mask = np.asarray([value == group_id for value in labels], dtype=bool)
        local_weight = weight[mask]
        local_gain = _weighted_mean(gain[mask], local_weight)
        group_gains.append(local_gain)
        group_rows.append(
            ForecastStackingGroupScore(
                group_id=group_id,
                row_count=int(np.count_nonzero(mask)),
                total_weight=float(np.sum(local_weight)),
                mean_log_density_gain=float(local_gain),
            )
        )

    category = classify_independent_gains(group_gains, tolerance=gain_tolerance)
    mean_gain = _weighted_mean(gain, weight)
    admissible = bool(category == "generalizing" and mean_gain > gain_tolerance)
    group_array = np.asarray(group_gains, dtype=float)
    return ForecastStackingValidation(
        row_count=int(n),
        group_count=len(group_rows),
        mean_stacked_log_density=_weighted_mean(stacked, weight),
        mean_marginal_log_density=_weighted_mean(marginal, weight),
        mean_log_density_gain=float(mean_gain),
        equal_group_mean_gain=float(np.mean(group_array)),
        minimum_group_gain=float(np.min(group_array)),
        maximum_group_gain=float(np.max(group_array)),
        positive_group_count=int(np.sum(group_array > gain_tolerance)),
        nonpositive_group_count=int(np.sum(group_array <= gain_tolerance)),
        transfer_category=category,
        transfer_admissible=admissible,
        coverage_inherited_from_members=False,
        requires_independent_recalibration=True,
        aggregate_confidence_score_emitted=False,
        groups=tuple(group_rows),
    )
