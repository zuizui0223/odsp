"""Group-wise empirical coverage and crossed transfer/calibration audits.

These diagnostics do not create conditional-coverage guarantees. They expose where
marginal calibration or transferability fails across caller-declared groups or
novelty strata and keep pooled summaries from overriding a local failure.
"""
from __future__ import annotations

from dataclasses import asdict, dataclass
import math
from typing import Sequence

import numpy as np

from .transferability import classify_independent_gains


@dataclass(frozen=True)
class CoverageAuditRow:
    group_id: str
    row_count: int
    total_weight: float
    empirical_coverage: float
    absolute_coverage_error: float
    coverage_ok: bool

    def as_dict(self) -> dict[str, object]:
        return asdict(self)


@dataclass(frozen=True)
class GroupwiseCoverageAudit:
    row_count: int
    group_count: int
    target_coverage: float
    tolerance: float
    pooled_coverage: float
    pooled_absolute_error: float
    pooled_coverage_ok: bool
    passed_group_count: int
    failed_group_count: int
    coverage_category: str
    all_groups_ok: bool
    conditional_coverage_guarantee_claimed: bool
    aggregate_confidence_score_emitted: bool
    groups: tuple[CoverageAuditRow, ...]

    def as_dict(self) -> dict[str, object]:
        payload = asdict(self)
        payload["groups"] = [row.as_dict() for row in self.groups]
        return payload


@dataclass(frozen=True)
class GroupTrustAuditRow:
    group_id: str
    row_count: int
    total_weight: float
    mean_log_density_gain: float
    gain_positive: bool
    empirical_coverage: float
    absolute_coverage_error: float
    coverage_ok: bool
    trusted: bool

    def as_dict(self) -> dict[str, object]:
        return asdict(self)


@dataclass(frozen=True)
class GroupwiseForecastTrustAudit:
    row_count: int
    group_count: int
    mean_log_density_gain: float
    transfer_category: str
    coverage_category: str
    trusted_group_count: int
    failed_trust_group_count: int
    trusted_admissible: bool
    pooled_gain_can_override_group_failure: bool
    pooled_coverage_can_override_group_failure: bool
    aggregate_confidence_score_emitted: bool
    groups: tuple[GroupTrustAuditRow, ...]

    def as_dict(self) -> dict[str, object]:
        payload = asdict(self)
        payload["groups"] = [row.as_dict() for row in self.groups]
        return payload


def _weights(values: Sequence[float] | None, n: int) -> np.ndarray:
    if values is None:
        return np.ones(n, dtype=float)
    w = np.asarray(values, dtype=float)
    if w.shape != (n,):
        raise ValueError("sample_weight must contain one value per row")
    if not np.isfinite(w).all() or np.any(w < 0) or not np.any(w > 0):
        raise ValueError("sample_weight must be finite, non-negative and positive in total")
    return w


def _labels(values: Sequence[object], n: int) -> tuple[str, ...]:
    if len(values) != n:
        raise ValueError("groups must contain one value per row")
    labels = tuple(str(value).strip() for value in values)
    if any(not value for value in labels):
        raise ValueError("group labels must be non-empty")
    return labels


def _weighted_mean(values: np.ndarray, weight: np.ndarray) -> float:
    total = float(np.sum(weight))
    if not total > 0:
        raise ValueError("weights must have positive total mass")
    return float(np.sum(values * weight) / total)


def _validate_target(target_coverage: float, tolerance: float) -> tuple[float, float]:
    target = float(target_coverage)
    tol = float(tolerance)
    if not math.isfinite(target) or not 0.0 < target < 1.0:
        raise ValueError("target_coverage must lie strictly between zero and one")
    if not math.isfinite(tol) or tol < 0:
        raise ValueError("tolerance must be finite and non-negative")
    return target, tol


def audit_groupwise_coverage(
    covered: Sequence[bool],
    groups: Sequence[object],
    *,
    target_coverage: float = 0.90,
    tolerance: float = 0.03,
    sample_weight: Sequence[float] | None = None,
) -> GroupwiseCoverageAudit:
    covered_array = np.asarray(covered, dtype=bool)
    if covered_array.ndim != 1 or covered_array.size == 0:
        raise ValueError("covered must be a non-empty one-dimensional vector")
    n = int(covered_array.size)
    labels = _labels(groups, n)
    weight = _weights(sample_weight, n)
    target, tol = _validate_target(target_coverage, tolerance)
    ordered = tuple(dict.fromkeys(labels))
    rows: list[CoverageAuditRow] = []
    for group_id in ordered:
        mask = np.asarray([label == group_id for label in labels], dtype=bool)
        local_weight = weight[mask]
        empirical = _weighted_mean(covered_array[mask].astype(float), local_weight)
        error = abs(empirical - target)
        rows.append(CoverageAuditRow(
            group_id=group_id,
            row_count=int(np.count_nonzero(mask)),
            total_weight=float(np.sum(local_weight)),
            empirical_coverage=float(empirical),
            absolute_coverage_error=float(error),
            coverage_ok=bool(error <= tol),
        ))
    passed = sum(row.coverage_ok for row in rows)
    if passed == len(rows):
        category = "calibrated"
    elif passed == 0:
        category = "non_calibrated"
    else:
        category = "mixed"
    pooled = _weighted_mean(covered_array.astype(float), weight)
    pooled_error = abs(pooled - target)
    return GroupwiseCoverageAudit(
        row_count=n,
        group_count=len(rows),
        target_coverage=target,
        tolerance=tol,
        pooled_coverage=float(pooled),
        pooled_absolute_error=float(pooled_error),
        pooled_coverage_ok=bool(pooled_error <= tol),
        passed_group_count=int(passed),
        failed_group_count=int(len(rows) - passed),
        coverage_category=category,
        all_groups_ok=bool(passed == len(rows)),
        conditional_coverage_guarantee_claimed=False,
        aggregate_confidence_score_emitted=False,
        groups=tuple(rows),
    )


def audit_groupwise_forecast_trust(
    conditional_log_density: Sequence[float],
    marginal_log_density: Sequence[float],
    covered: Sequence[bool],
    groups: Sequence[object],
    *,
    target_coverage: float = 0.90,
    tolerance: float = 0.03,
    gain_tolerance: float = 1e-12,
    sample_weight: Sequence[float] | None = None,
) -> GroupwiseForecastTrustAudit:
    conditional = np.asarray(conditional_log_density, dtype=float)
    marginal = np.asarray(marginal_log_density, dtype=float)
    if conditional.ndim != 1 or conditional.size == 0 or marginal.shape != conditional.shape:
        raise ValueError("conditional and marginal log densities must be equal-length non-empty vectors")
    if not np.isfinite(conditional).all() or not np.isfinite(marginal).all():
        raise ValueError("log densities must be finite")
    n = int(conditional.size)
    covered_array = np.asarray(covered, dtype=bool)
    if covered_array.shape != (n,):
        raise ValueError("covered must contain one value per row")
    labels = _labels(groups, n)
    weight = _weights(sample_weight, n)
    target, tol = _validate_target(target_coverage, tolerance)
    if not math.isfinite(gain_tolerance) or gain_tolerance < 0:
        raise ValueError("gain_tolerance must be finite and non-negative")
    gain = conditional - marginal
    ordered = tuple(dict.fromkeys(labels))
    rows: list[GroupTrustAuditRow] = []
    group_gains: list[float] = []
    coverage_ok_values: list[bool] = []
    for group_id in ordered:
        mask = np.asarray([label == group_id for label in labels], dtype=bool)
        local_weight = weight[mask]
        local_gain = _weighted_mean(gain[mask], local_weight)
        empirical = _weighted_mean(covered_array[mask].astype(float), local_weight)
        error = abs(empirical - target)
        gain_positive = bool(local_gain > gain_tolerance)
        coverage_ok = bool(error <= tol)
        rows.append(GroupTrustAuditRow(
            group_id=group_id,
            row_count=int(np.count_nonzero(mask)),
            total_weight=float(np.sum(local_weight)),
            mean_log_density_gain=float(local_gain),
            gain_positive=gain_positive,
            empirical_coverage=float(empirical),
            absolute_coverage_error=float(error),
            coverage_ok=coverage_ok,
            trusted=bool(gain_positive and coverage_ok),
        ))
        group_gains.append(local_gain)
        coverage_ok_values.append(coverage_ok)
    transfer_category = classify_independent_gains(group_gains, tolerance=gain_tolerance)
    passed_coverage = sum(coverage_ok_values)
    if passed_coverage == len(rows):
        coverage_category = "calibrated"
    elif passed_coverage == 0:
        coverage_category = "non_calibrated"
    else:
        coverage_category = "mixed"
    trusted_count = sum(row.trusted for row in rows)
    return GroupwiseForecastTrustAudit(
        row_count=n,
        group_count=len(rows),
        mean_log_density_gain=_weighted_mean(gain, weight),
        transfer_category=transfer_category,
        coverage_category=coverage_category,
        trusted_group_count=int(trusted_count),
        failed_trust_group_count=int(len(rows) - trusted_count),
        trusted_admissible=bool(trusted_count == len(rows)),
        pooled_gain_can_override_group_failure=False,
        pooled_coverage_can_override_group_failure=False,
        aggregate_confidence_score_emitted=False,
        groups=tuple(rows),
    )
