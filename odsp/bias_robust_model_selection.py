"""Bias-robust trust-aware model selection for ecological-state forecasts.

This layer composes two existing validation audits on the same untouched rows:
(1) point transfer plus group-wise empirical coverage and (2) joint block-bootstrap
plus bounded-reweighting transfer robustness.  Only candidates passing both enter
Pareto comparison.  The component evidence remains separate and no aggregate
confidence score is formed.
"""
from __future__ import annotations

from dataclasses import dataclass
import math
from typing import Sequence

import numpy as np

from .joint_bias_uncertainty_robustness import (
    JointBiasUncertaintyAudit,
    audit_joint_bias_uncertainty_robustness,
)
from .trust_aware_model_selection import (
    TrustAwareCandidateScore,
    evaluate_trust_aware_candidate,
)


@dataclass(frozen=True)
class BiasRobustCandidateScore:
    name: str
    point_and_coverage: TrustAwareCandidateScore
    joint_robustness: JointBiasUncertaintyAudit
    minimum_worst_case_lower_bound: float | None
    bias_robust_trusted_admissible: bool

    def as_dict(self) -> dict[str, object]:
        return {
            "name": self.name,
            "point_and_coverage": self.point_and_coverage.as_dict(),
            "joint_robustness": self.joint_robustness.as_dict(),
            "minimum_worst_case_lower_bound": self.minimum_worst_case_lower_bound,
            "bias_robust_trusted_admissible": self.bias_robust_trusted_admissible,
        }


@dataclass(frozen=True)
class BiasRobustSelectionResult:
    target_coverage: float
    coverage_tolerance: float
    gamma: float
    confidence_level: float
    bootstrap_draws: int
    minimum_blocks_per_group: int
    candidates: tuple[BiasRobustCandidateScore, ...]
    point_trusted_names: tuple[str, ...]
    bias_robust_trusted_names: tuple[str, ...]
    point_trusted_but_bias_robust_rejected_names: tuple[str, ...]
    pareto_front_names: tuple[str, ...]
    recommended_by_log_score: str | None
    aggregate_confidence_score_emitted: bool

    def as_dict(self) -> dict[str, object]:
        return {
            "target_coverage": self.target_coverage,
            "coverage_tolerance": self.coverage_tolerance,
            "gamma": self.gamma,
            "confidence_level": self.confidence_level,
            "bootstrap_draws": self.bootstrap_draws,
            "minimum_blocks_per_group": self.minimum_blocks_per_group,
            "candidates": [row.as_dict() for row in self.candidates],
            "point_trusted_names": list(self.point_trusted_names),
            "bias_robust_trusted_names": list(self.bias_robust_trusted_names),
            "point_trusted_but_bias_robust_rejected_names": list(
                self.point_trusted_but_bias_robust_rejected_names
            ),
            "pareto_front_names": list(self.pareto_front_names),
            "recommended_by_log_score": self.recommended_by_log_score,
            "aggregate_confidence_score_emitted": self.aggregate_confidence_score_emitted,
        }


def evaluate_bias_robust_candidate(
    name: str,
    conditional_log_density: Sequence[float],
    marginal_log_density: Sequence[float],
    covered: Sequence[bool],
    groups: Sequence[object],
    blocks: Sequence[object],
    *,
    region_size: Sequence[float],
    base_weight: Sequence[float] | None = None,
    target_coverage: float = 0.90,
    coverage_tolerance: float = 0.03,
    gamma: float = 2.0,
    confidence_level: float = 0.95,
    bootstrap_draws: int = 1000,
    seed: int = 20260906,
    minimum_blocks_per_group: int = 8,
    gain_tolerance: float = 0.0,
) -> BiasRobustCandidateScore:
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
        sample_weight=base_weight,
    )
    joint = audit_joint_bias_uncertainty_robustness(
        conditional - marginal,
        groups,
        blocks,
        base_weight=base_weight,
        gamma=gamma,
        confidence_level=confidence_level,
        bootstrap_draws=bootstrap_draws,
        seed=seed,
        minimum_blocks_per_group=minimum_blocks_per_group,
        gain_tolerance=gain_tolerance,
    )
    trusted = bool(point.trusted_admissible and joint.joint_robust_admissible)
    return BiasRobustCandidateScore(
        name=point.name,
        point_and_coverage=point,
        joint_robustness=joint,
        minimum_worst_case_lower_bound=joint.minimum_worst_case_lower_bound,
        bias_robust_trusted_admissible=trusted,
    )


def _dominates(a: BiasRobustCandidateScore, b: BiasRobustCandidateScore) -> bool:
    if not (a.bias_robust_trusted_admissible and b.bias_robust_trusted_admissible):
        return False
    a_lower = a.minimum_worst_case_lower_bound
    b_lower = b.minimum_worst_case_lower_bound
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


def compare_bias_robust_candidates(
    candidates: Sequence[BiasRobustCandidateScore],
    *,
    target_coverage: float = 0.90,
    coverage_tolerance: float = 0.03,
    gamma: float = 2.0,
    confidence_level: float = 0.95,
    bootstrap_draws: int = 1000,
    minimum_blocks_per_group: int = 8,
) -> BiasRobustSelectionResult:
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
    if not math.isfinite(gamma) or gamma < 1.0:
        raise ValueError("gamma must be finite and >= 1")
    if not math.isfinite(confidence_level) or not 0.0 < confidence_level < 1.0:
        raise ValueError("confidence_level must lie strictly between zero and one")

    point_trusted = tuple(
        row.name for row in rows if row.point_and_coverage.trusted_admissible
    )
    robust = tuple(row for row in rows if row.bias_robust_trusted_admissible)
    robust_names = tuple(row.name for row in robust)
    rejected = tuple(
        row.name
        for row in rows
        if row.point_and_coverage.trusted_admissible
        and not row.bias_robust_trusted_admissible
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

    return BiasRobustSelectionResult(
        target_coverage=float(target_coverage),
        coverage_tolerance=float(coverage_tolerance),
        gamma=float(gamma),
        confidence_level=float(confidence_level),
        bootstrap_draws=int(bootstrap_draws),
        minimum_blocks_per_group=int(minimum_blocks_per_group),
        candidates=rows,
        point_trusted_names=point_trusted,
        bias_robust_trusted_names=robust_names,
        point_trusted_but_bias_robust_rejected_names=rejected,
        pareto_front_names=tuple(pareto),
        recommended_by_log_score=recommended,
        aggregate_confidence_score_emitted=False,
    )
