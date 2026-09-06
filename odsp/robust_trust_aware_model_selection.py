"""Robust trust-aware selection of probabilistic ecological-state forecasts.

This layer composes three distinct audits on the same untouched validation rows:
point transferability, group-wise empirical coverage, and block-bootstrap transfer
uncertainty.  A candidate reaches the Pareto comparison only when every declared
independent group is calibrated and has an uncertainty-supported positive gain.
"""
from __future__ import annotations

from dataclasses import dataclass
import math
from typing import Sequence

import numpy as np

from .block_aware_transfer_uncertainty import (
    BlockAwareTransferAudit,
    audit_block_aware_transfer_uncertainty,
)
from .trust_aware_model_selection import (
    TrustAwareCandidateScore,
    evaluate_trust_aware_candidate,
)


@dataclass(frozen=True)
class RobustTrustAwareCandidateScore:
    name: str
    point_and_coverage: TrustAwareCandidateScore
    transfer_uncertainty: BlockAwareTransferAudit
    minimum_group_lower_bound: float | None
    robust_trusted_admissible: bool

    def as_dict(self) -> dict[str, object]:
        return {
            "name": self.name,
            "point_and_coverage": self.point_and_coverage.as_dict(),
            "transfer_uncertainty": self.transfer_uncertainty.as_dict(),
            "minimum_group_lower_bound": self.minimum_group_lower_bound,
            "robust_trusted_admissible": self.robust_trusted_admissible,
        }


@dataclass(frozen=True)
class RobustTrustAwareSelectionResult:
    target_coverage: float
    coverage_tolerance: float
    confidence_level: float
    bootstrap_draws: int
    minimum_blocks_per_group: int
    candidates: tuple[RobustTrustAwareCandidateScore, ...]
    point_trusted_names: tuple[str, ...]
    robust_trusted_names: tuple[str, ...]
    legacy_trusted_but_robust_rejected_names: tuple[str, ...]
    pareto_front_names: tuple[str, ...]
    recommended_by_log_score: str | None
    aggregate_confidence_score_emitted: bool

    def as_dict(self) -> dict[str, object]:
        return {
            "target_coverage": self.target_coverage,
            "coverage_tolerance": self.coverage_tolerance,
            "confidence_level": self.confidence_level,
            "bootstrap_draws": self.bootstrap_draws,
            "minimum_blocks_per_group": self.minimum_blocks_per_group,
            "candidates": [row.as_dict() for row in self.candidates],
            "point_trusted_names": list(self.point_trusted_names),
            "robust_trusted_names": list(self.robust_trusted_names),
            "legacy_trusted_but_robust_rejected_names": list(
                self.legacy_trusted_but_robust_rejected_names
            ),
            "pareto_front_names": list(self.pareto_front_names),
            "recommended_by_log_score": self.recommended_by_log_score,
            "aggregate_confidence_score_emitted": self.aggregate_confidence_score_emitted,
        }


def evaluate_robust_trust_candidate(
    name: str,
    conditional_log_density: Sequence[float],
    marginal_log_density: Sequence[float],
    covered: Sequence[bool],
    groups: Sequence[object],
    blocks: Sequence[object],
    *,
    region_size: Sequence[float],
    target_coverage: float = 0.90,
    coverage_tolerance: float = 0.03,
    gain_tolerance: float = 0.0,
    confidence_level: float = 0.95,
    bootstrap_draws: int = 2000,
    seed: int = 20260906,
    minimum_blocks_per_group: int = 8,
    sample_weight: Sequence[float] | None = None,
) -> RobustTrustAwareCandidateScore:
    conditional = np.asarray(conditional_log_density, dtype=float)
    marginal = np.asarray(marginal_log_density, dtype=float)
    if conditional.ndim != 1 or conditional.size == 0:
        raise ValueError("conditional_log_density must be a non-empty vector")
    if marginal.shape != conditional.shape:
        raise ValueError("marginal_log_density must match conditional_log_density")

    point = evaluate_trust_aware_candidate(
        name,
        conditional,
        marginal,
        covered,
        groups,
        region_size=region_size,
        target_coverage=target_coverage,
        coverage_tolerance=coverage_tolerance,
        gain_tolerance=gain_tolerance,
        sample_weight=sample_weight,
    )
    uncertainty = audit_block_aware_transfer_uncertainty(
        conditional - marginal,
        groups,
        blocks=blocks,
        sample_weight=sample_weight,
        confidence_level=confidence_level,
        bootstrap_draws=bootstrap_draws,
        seed=seed,
        minimum_blocks_per_group=minimum_blocks_per_group,
        gain_tolerance=gain_tolerance,
    )
    lower_bounds = [
        row.lower_bound for row in uncertainty.groups if row.lower_bound is not None
    ]
    minimum_lower = min(lower_bounds) if len(lower_bounds) == len(uncertainty.groups) else None
    robust_trusted = bool(
        point.trusted_admissible and uncertainty.robust_admissible
    )
    return RobustTrustAwareCandidateScore(
        name=point.name,
        point_and_coverage=point,
        transfer_uncertainty=uncertainty,
        minimum_group_lower_bound=(None if minimum_lower is None else float(minimum_lower)),
        robust_trusted_admissible=robust_trusted,
    )


def _dominates(
    a: RobustTrustAwareCandidateScore,
    b: RobustTrustAwareCandidateScore,
) -> bool:
    if not (a.robust_trusted_admissible and b.robust_trusted_admissible):
        return False
    a_lower = a.minimum_group_lower_bound
    b_lower = b.minimum_group_lower_bound
    a_size = a.point_and_coverage.forecast_score.mean_region_size
    b_size = b.point_and_coverage.forecast_score.mean_region_size
    if a_lower is None or b_lower is None or a_size is None or b_size is None:
        return False
    a_gain = a.point_and_coverage.forecast_score.mean_log_density_gain
    b_gain = b.point_and_coverage.forecast_score.mean_log_density_gain
    a_cov = a.point_and_coverage.worst_group_coverage_error
    b_cov = b.point_and_coverage.worst_group_coverage_error
    no_worse = (
        a_gain >= b_gain
        and a_lower >= b_lower
        and a_cov <= b_cov
        and a_size <= b_size
    )
    strict = (
        a_gain > b_gain
        or a_lower > b_lower
        or a_cov < b_cov
        or a_size < b_size
    )
    return bool(no_worse and strict)


def compare_robust_trust_candidates(
    candidates: Sequence[RobustTrustAwareCandidateScore],
    *,
    target_coverage: float = 0.90,
    coverage_tolerance: float = 0.03,
    confidence_level: float = 0.95,
    bootstrap_draws: int = 2000,
    minimum_blocks_per_group: int = 8,
) -> RobustTrustAwareSelectionResult:
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
    if not math.isfinite(confidence_level) or not 0.0 < confidence_level < 1.0:
        raise ValueError("confidence_level must lie strictly between zero and one")

    point_trusted = tuple(
        row.name for row in rows if row.point_and_coverage.trusted_admissible
    )
    robust = tuple(row for row in rows if row.robust_trusted_admissible)
    robust_names = tuple(row.name for row in robust)
    rejected_after_uncertainty = tuple(
        row.name
        for row in rows
        if row.point_and_coverage.trusted_admissible
        and not row.robust_trusted_admissible
    )

    pareto: list[str] = []
    for candidate in robust:
        if not any(
            _dominates(other, candidate)
            for other in robust
            if other.name != candidate.name
        ):
            pareto.append(candidate.name)

    recommended = None
    if robust:
        recommended = max(
            robust,
            key=lambda row: row.point_and_coverage.forecast_score.mean_log_density_gain,
        ).name

    return RobustTrustAwareSelectionResult(
        target_coverage=float(target_coverage),
        coverage_tolerance=float(coverage_tolerance),
        confidence_level=float(confidence_level),
        bootstrap_draws=int(bootstrap_draws),
        minimum_blocks_per_group=int(minimum_blocks_per_group),
        candidates=rows,
        point_trusted_names=point_trusted,
        robust_trusted_names=robust_names,
        legacy_trusted_but_robust_rejected_names=rejected_after_uncertainty,
        pareto_front_names=tuple(pareto),
        recommended_by_log_score=recommended,
        aggregate_confidence_score_emitted=False,
    )
