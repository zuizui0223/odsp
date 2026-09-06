"""Trust-aware comparison of probabilistic ecological-state forecasts.

A candidate is admitted only when every declared independent group has both a
positive conditional-minus-marginal log-density gain and empirical coverage within
the declared tolerance.  Pooled summaries cannot rescue group failures.  Among
admitted candidates, ODSP reports a Pareto front over gain, worst-group coverage
error and prediction-region size rather than constructing an aggregate confidence
score.
"""
from __future__ import annotations

from dataclasses import asdict, dataclass
import math
from typing import Sequence

from .forecast_model_comparison import ForecastCandidateScore, evaluate_forecast_candidate
from .groupwise_coverage_audit import GroupwiseForecastTrustAudit, audit_groupwise_forecast_trust


@dataclass(frozen=True)
class TrustAwareCandidateScore:
    name: str
    forecast_score: ForecastCandidateScore
    groupwise_trust: GroupwiseForecastTrustAudit
    worst_group_coverage_error: float
    trusted_admissible: bool

    def as_dict(self) -> dict[str, object]:
        return {
            "name": self.name,
            "forecast_score": self.forecast_score.as_dict(),
            "groupwise_trust": self.groupwise_trust.as_dict(),
            "worst_group_coverage_error": self.worst_group_coverage_error,
            "trusted_admissible": self.trusted_admissible,
        }


@dataclass(frozen=True)
class TrustAwareModelSelectionResult:
    target_coverage: float
    coverage_tolerance: float
    gain_tolerance: float
    candidates: tuple[TrustAwareCandidateScore, ...]
    trusted_admissible_names: tuple[str, ...]
    pareto_front_names: tuple[str, ...]
    recommended_by_log_score: str | None
    aggregate_confidence_score_emitted: bool

    def as_dict(self) -> dict[str, object]:
        return {
            "target_coverage": self.target_coverage,
            "coverage_tolerance": self.coverage_tolerance,
            "gain_tolerance": self.gain_tolerance,
            "candidates": [row.as_dict() for row in self.candidates],
            "trusted_admissible_names": list(self.trusted_admissible_names),
            "pareto_front_names": list(self.pareto_front_names),
            "recommended_by_log_score": self.recommended_by_log_score,
            "aggregate_confidence_score_emitted": self.aggregate_confidence_score_emitted,
        }


def evaluate_trust_aware_candidate(
    name: str,
    conditional_log_density: Sequence[float],
    marginal_log_density: Sequence[float],
    covered: Sequence[bool],
    groups: Sequence[object],
    *,
    region_size: Sequence[float],
    target_coverage: float = 0.90,
    coverage_tolerance: float = 0.03,
    gain_tolerance: float = 1e-12,
    sample_weight: Sequence[float] | None = None,
) -> TrustAwareCandidateScore:
    """Evaluate one candidate using pooled summaries plus fail-closed group audits."""

    base = evaluate_forecast_candidate(
        name,
        conditional_log_density,
        marginal_log_density,
        groups,
        covered=covered,
        target_coverage=target_coverage,
        region_size=region_size,
        sample_weight=sample_weight,
        coverage_tolerance=coverage_tolerance,
        gain_tolerance=gain_tolerance,
    )
    audit = audit_groupwise_forecast_trust(
        conditional_log_density,
        marginal_log_density,
        covered,
        groups,
        target_coverage=target_coverage,
        tolerance=coverage_tolerance,
        gain_tolerance=gain_tolerance,
        sample_weight=sample_weight,
    )
    worst = max(row.absolute_coverage_error for row in audit.groups)
    trusted = bool(base.transfer_admissible and audit.trusted_admissible)
    return TrustAwareCandidateScore(
        name=base.name,
        forecast_score=base,
        groupwise_trust=audit,
        worst_group_coverage_error=float(worst),
        trusted_admissible=trusted,
    )


def _dominates(a: TrustAwareCandidateScore, b: TrustAwareCandidateScore) -> bool:
    if not (a.trusted_admissible and b.trusted_admissible):
        return False
    a_size = a.forecast_score.mean_region_size
    b_size = b.forecast_score.mean_region_size
    if a_size is None or b_size is None:
        return False
    a_gain = a.forecast_score.mean_log_density_gain
    b_gain = b.forecast_score.mean_log_density_gain
    no_worse = (
        a_gain >= b_gain
        and a.worst_group_coverage_error <= b.worst_group_coverage_error
        and a_size <= b_size
    )
    strictly_better = (
        a_gain > b_gain
        or a.worst_group_coverage_error < b.worst_group_coverage_error
        or a_size < b_size
    )
    return bool(no_worse and strictly_better)


def compare_trust_aware_candidates(
    candidates: Sequence[TrustAwareCandidateScore],
    *,
    target_coverage: float = 0.90,
    coverage_tolerance: float = 0.03,
    gain_tolerance: float = 1e-12,
) -> TrustAwareModelSelectionResult:
    rows = tuple(candidates)
    if not rows:
        raise ValueError("candidates must contain at least one score")
    names = [row.name for row in rows]
    if len(set(names)) != len(names):
        raise ValueError("candidate names must be unique")
    if not math.isfinite(target_coverage) or not 0.0 < target_coverage < 1.0:
        raise ValueError("target_coverage must lie strictly between zero and one")
    if not math.isfinite(coverage_tolerance) or coverage_tolerance < 0:
        raise ValueError("coverage_tolerance must be finite and non-negative")
    if not math.isfinite(gain_tolerance) or gain_tolerance < 0:
        raise ValueError("gain_tolerance must be finite and non-negative")

    for row in rows:
        base = row.forecast_score
        if base.target_coverage is None or not math.isclose(base.target_coverage, target_coverage, rel_tol=0.0, abs_tol=1e-15):
            raise ValueError("candidate target coverage disagrees with comparison target")
        if base.coverage_tolerance is None or not math.isclose(base.coverage_tolerance, coverage_tolerance, rel_tol=0.0, abs_tol=1e-15):
            raise ValueError("candidate coverage tolerance disagrees with comparison tolerance")

    trusted = tuple(row for row in rows if row.trusted_admissible)
    pareto: list[str] = []
    for candidate in trusted:
        if not any(
            _dominates(other, candidate)
            for other in trusted
            if other.name != candidate.name
        ):
            pareto.append(candidate.name)

    recommended = None
    if trusted:
        recommended = max(
            trusted,
            key=lambda row: row.forecast_score.mean_log_density_gain,
        ).name

    return TrustAwareModelSelectionResult(
        target_coverage=float(target_coverage),
        coverage_tolerance=float(coverage_tolerance),
        gain_tolerance=float(gain_tolerance),
        candidates=rows,
        trusted_admissible_names=tuple(row.name for row in trusted),
        pareto_front_names=tuple(pareto),
        recommended_by_log_score=recommended,
        aggregate_confidence_score_emitted=False,
    )
