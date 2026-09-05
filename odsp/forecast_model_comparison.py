"""Model-agnostic comparison of probabilistic ecological-state forecasts.

Candidates are compared only on genuinely held-out evidence.  Transferability,
coverage and sharpness remain separate dimensions; no aggregate confidence score
is formed.  A pooled positive mean cannot rescue an independent group with a
non-positive gain.
"""
from __future__ import annotations

from dataclasses import asdict, dataclass
import math
from typing import Sequence

import numpy as np

from .transferability import classify_independent_gains


@dataclass(frozen=True)
class ForecastGroupScore:
    group_id: str
    row_count: int
    total_weight: float
    mean_log_density_gain: float

    def as_dict(self) -> dict[str, object]:
        return asdict(self)


@dataclass(frozen=True)
class ForecastCandidateScore:
    name: str
    row_count: int
    group_count: int
    mean_conditional_log_density: float
    mean_marginal_log_density: float
    mean_log_density_gain: float
    equal_group_mean_gain: float
    minimum_group_gain: float
    maximum_group_gain: float
    positive_group_count: int
    nonpositive_group_count: int
    transfer_category: str
    transfer_admissible: bool
    coverage_audited: bool
    target_coverage: float | None
    empirical_coverage: float | None
    absolute_coverage_error: float | None
    coverage_tolerance: float | None
    coverage_ok: bool | None
    mean_region_size: float | None
    median_region_size: float | None
    trusted_admissible: bool
    groups: tuple[ForecastGroupScore, ...]

    def as_dict(self) -> dict[str, object]:
        payload = asdict(self)
        payload["groups"] = [row.as_dict() for row in self.groups]
        return payload


@dataclass(frozen=True)
class ForecastComparisonResult:
    coverage_tolerance: float
    candidates: tuple[ForecastCandidateScore, ...]
    transfer_admissible_names: tuple[str, ...]
    trusted_admissible_names: tuple[str, ...]
    pareto_front_names: tuple[str, ...]
    recommended_by_log_score: str | None
    aggregate_confidence_score_emitted: bool

    def as_dict(self) -> dict[str, object]:
        return {
            "coverage_tolerance": self.coverage_tolerance,
            "candidates": [row.as_dict() for row in self.candidates],
            "transfer_admissible_names": list(self.transfer_admissible_names),
            "trusted_admissible_names": list(self.trusted_admissible_names),
            "pareto_front_names": list(self.pareto_front_names),
            "recommended_by_log_score": self.recommended_by_log_score,
            "aggregate_confidence_score_emitted": self.aggregate_confidence_score_emitted,
        }


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
        raise ValueError("sample_weight must contain one value per row")
    if not np.isfinite(weight).all() or np.any(weight < 0) or not np.any(weight > 0):
        raise ValueError("sample_weight must be finite, non-negative and positive in total")
    return weight


def _weighted_mean(values: np.ndarray, weight: np.ndarray) -> float:
    total = float(np.sum(weight))
    if not total > 0:
        raise ValueError("weights must have positive total mass")
    return float(np.sum(values * weight) / total)


def _group_labels(values: Sequence[object], n: int) -> tuple[str, ...]:
    if len(values) != n:
        raise ValueError("groups must contain one value per row")
    result: list[str] = []
    for value in values:
        text = str(value).strip()
        if not text:
            raise ValueError("group labels must be non-empty")
        result.append(text)
    return tuple(result)


def evaluate_forecast_candidate(
    name: str,
    conditional_log_density: Sequence[float],
    marginal_log_density: Sequence[float],
    groups: Sequence[object],
    *,
    covered: Sequence[bool] | None = None,
    target_coverage: float | None = None,
    region_size: Sequence[float] | None = None,
    sample_weight: Sequence[float] | None = None,
    coverage_tolerance: float = 0.03,
    gain_tolerance: float = 0.0,
) -> ForecastCandidateScore:
    """Score one candidate on the same held-out rows used by all candidates."""

    candidate_name = str(name).strip()
    if not candidate_name:
        raise ValueError("name must be non-empty")
    if not math.isfinite(coverage_tolerance) or coverage_tolerance < 0:
        raise ValueError("coverage_tolerance must be finite and non-negative")
    if not math.isfinite(gain_tolerance) or gain_tolerance < 0:
        raise ValueError("gain_tolerance must be finite and non-negative")

    conditional = _validate_vector(conditional_log_density, "conditional_log_density")
    marginal = _validate_vector(
        marginal_log_density, "marginal_log_density", expected=conditional.size
    )
    weight = _validate_weights(sample_weight, conditional.size)
    labels = _group_labels(groups, conditional.size)
    gain = conditional - marginal

    ordered_groups = tuple(dict.fromkeys(labels))
    group_scores: list[ForecastGroupScore] = []
    group_gains: list[float] = []
    for group_id in ordered_groups:
        mask = np.asarray([value == group_id for value in labels], dtype=bool)
        group_weight = weight[mask]
        group_gain = _weighted_mean(gain[mask], group_weight)
        group_gains.append(group_gain)
        group_scores.append(
            ForecastGroupScore(
                group_id=group_id,
                row_count=int(np.count_nonzero(mask)),
                total_weight=float(np.sum(group_weight)),
                mean_log_density_gain=float(group_gain),
            )
        )

    transfer_category = classify_independent_gains(
        group_gains, tolerance=gain_tolerance
    )
    transfer_admissible = bool(
        transfer_category == "generalizing"
        and _weighted_mean(gain, weight) > gain_tolerance
    )

    coverage_audited = covered is not None or target_coverage is not None
    if coverage_audited and (covered is None or target_coverage is None):
        raise ValueError("covered and target_coverage must be supplied together")
    empirical_coverage: float | None = None
    coverage_error: float | None = None
    coverage_ok: bool | None = None
    if covered is not None and target_coverage is not None:
        target = float(target_coverage)
        if not math.isfinite(target) or not 0.0 < target < 1.0:
            raise ValueError("target_coverage must lie strictly between zero and one")
        covered_array = np.asarray(covered, dtype=bool)
        if covered_array.shape != (conditional.size,):
            raise ValueError("covered must contain one value per row")
        empirical_coverage = _weighted_mean(covered_array.astype(float), weight)
        coverage_error = float(abs(empirical_coverage - target))
        coverage_ok = bool(coverage_error <= coverage_tolerance)
    else:
        target = None

    mean_region_size: float | None = None
    median_region_size: float | None = None
    if region_size is not None:
        size = _validate_vector(region_size, "region_size", expected=conditional.size)
        if np.any(size < 0):
            raise ValueError("region_size must be non-negative")
        mean_region_size = _weighted_mean(size, weight)
        median_region_size = float(np.median(size))

    trusted_admissible = bool(
        transfer_admissible
        and coverage_audited
        and coverage_ok is True
    )
    return ForecastCandidateScore(
        name=candidate_name,
        row_count=int(conditional.size),
        group_count=len(group_scores),
        mean_conditional_log_density=_weighted_mean(conditional, weight),
        mean_marginal_log_density=_weighted_mean(marginal, weight),
        mean_log_density_gain=_weighted_mean(gain, weight),
        equal_group_mean_gain=float(np.mean(group_gains)),
        minimum_group_gain=float(np.min(group_gains)),
        maximum_group_gain=float(np.max(group_gains)),
        positive_group_count=int(np.sum(np.asarray(group_gains) > gain_tolerance)),
        nonpositive_group_count=int(np.sum(np.asarray(group_gains) <= gain_tolerance)),
        transfer_category=transfer_category,
        transfer_admissible=transfer_admissible,
        coverage_audited=coverage_audited,
        target_coverage=target,
        empirical_coverage=empirical_coverage,
        absolute_coverage_error=coverage_error,
        coverage_tolerance=float(coverage_tolerance) if coverage_audited else None,
        coverage_ok=coverage_ok,
        mean_region_size=mean_region_size,
        median_region_size=median_region_size,
        trusted_admissible=trusted_admissible,
        groups=tuple(group_scores),
    )


def _dominates(a: ForecastCandidateScore, b: ForecastCandidateScore) -> bool:
    if not (a.trusted_admissible and b.trusted_admissible):
        return False
    if a.absolute_coverage_error is None or b.absolute_coverage_error is None:
        return False
    if a.mean_region_size is None or b.mean_region_size is None:
        return False
    no_worse = (
        a.mean_log_density_gain >= b.mean_log_density_gain
        and a.absolute_coverage_error <= b.absolute_coverage_error
        and a.mean_region_size <= b.mean_region_size
    )
    strictly_better = (
        a.mean_log_density_gain > b.mean_log_density_gain
        or a.absolute_coverage_error < b.absolute_coverage_error
        or a.mean_region_size < b.mean_region_size
    )
    return bool(no_worse and strictly_better)


def compare_forecast_candidates(
    candidates: Sequence[ForecastCandidateScore],
    *,
    coverage_tolerance: float = 0.03,
) -> ForecastComparisonResult:
    """Compare already scored candidates without constructing an aggregate score."""

    rows = tuple(candidates)
    if not rows:
        raise ValueError("candidates must contain at least one score")
    names = [row.name for row in rows]
    if len(set(names)) != len(names):
        raise ValueError("candidate names must be unique")
    if not math.isfinite(coverage_tolerance) or coverage_tolerance < 0:
        raise ValueError("coverage_tolerance must be finite and non-negative")
    for row in rows:
        if row.coverage_audited and row.coverage_tolerance is not None:
            if not math.isclose(row.coverage_tolerance, coverage_tolerance, rel_tol=0.0, abs_tol=1e-15):
                raise ValueError("candidate coverage tolerance disagrees with comparison tolerance")

    transfer_names = tuple(row.name for row in rows if row.transfer_admissible)
    trusted = tuple(row for row in rows if row.trusted_admissible)
    trusted_names = tuple(row.name for row in trusted)

    pareto: list[str] = []
    for candidate in trusted:
        if not any(
            _dominates(other, candidate)
            for other in trusted
            if other.name != candidate.name
        ):
            pareto.append(candidate.name)

    recommended: str | None = None
    if trusted:
        recommended = max(
            trusted,
            key=lambda row: row.mean_log_density_gain,
        ).name

    return ForecastComparisonResult(
        coverage_tolerance=float(coverage_tolerance),
        candidates=rows,
        transfer_admissible_names=transfer_names,
        trusted_admissible_names=trusted_names,
        pareto_front_names=tuple(pareto),
        recommended_by_log_score=recommended,
        aggregate_confidence_score_emitted=False,
    )
