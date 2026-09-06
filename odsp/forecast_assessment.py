"""One-call orchestration of existing ODSP forecast trust evidence.

This module deliberately creates no new statistical estimand.  It validates one
set of held-out rows once, then routes those same rows through existing ODSP
validation and optional sensitivity layers before composing ForecastTrustDossierV2.
Expensive or design-specific layers remain opt-in and are reported as not audited
when omitted.
"""
from __future__ import annotations

from dataclasses import asdict, dataclass
from typing import Mapping, Sequence

import numpy as np

from .bias_robust_model_selection import (
    BiasRobustCandidateScore,
    BiasRobustSelectionResult,
    evaluate_bias_robust_candidate,
)
from .bounded_reweighting_robustness import (
    BoundedReweightingAudit,
    audit_bounded_reweighting_robustness,
)
from .forecast_trust_dossier_v2 import ForecastTrustDossierV2, build_forecast_trust_dossier_v2
from .joint_robustness_radius import JointRobustnessRadiusAudit, audit_joint_robustness_radius
from .prediction_novelty import NoveltySummary, fit_environmental_novelty_model
from .sampling_weight_sensitivity import (
    SamplingWeightSensitivityAudit,
    audit_sampling_weight_sensitivity,
)


@dataclass(frozen=True)
class JointRadiusAssessmentSummary:
    status: str
    baseline_joint_category: str | None
    target_joint_category: str | None
    certified_gamma: float | None
    break_gamma: float | None
    boundary_interval_width: float | None
    search_upper_gamma: float | None
    radius_is_lower_bound_only: bool
    certified_maximum_multiplier_ratio: float | None

    def as_dict(self) -> dict[str, object]:
        return asdict(self)


@dataclass(frozen=True)
class ForecastAssessmentResult:
    candidate_name: str
    row_count: int
    candidate: BiasRobustCandidateScore
    sampling_weight_audit: SamplingWeightSensitivityAudit | None
    bounded_reweighting_audit: BoundedReweightingAudit | None
    joint_radius: JointRadiusAssessmentSummary
    novelty_rows: tuple[NoveltySummary, ...]
    dossier: ForecastTrustDossierV2
    settings: dict[str, object]
    aggregate_confidence_score_emitted: bool

    def as_dict(self) -> dict[str, object]:
        return {
            "candidate_name": self.candidate_name,
            "row_count": self.row_count,
            "candidate": self.candidate.as_dict(),
            "sampling_weight_audit": (
                None if self.sampling_weight_audit is None else self.sampling_weight_audit.as_dict()
            ),
            "bounded_reweighting_audit": (
                None if self.bounded_reweighting_audit is None else self.bounded_reweighting_audit.as_dict()
            ),
            "joint_radius": self.joint_radius.as_dict(),
            "novelty_rows": [row.as_dict() for row in self.novelty_rows],
            "dossier": self.dossier.as_dict(),
            "settings": dict(self.settings),
            "aggregate_confidence_score_emitted": self.aggregate_confidence_score_emitted,
        }


def _validate_validation_vectors(
    conditional_log_density: Sequence[float],
    marginal_log_density: Sequence[float],
    covered: Sequence[bool],
    groups: Sequence[object],
    blocks: Sequence[object],
    region_size: Sequence[float],
) -> tuple[np.ndarray, np.ndarray]:
    conditional = np.asarray(conditional_log_density, dtype=float)
    marginal = np.asarray(marginal_log_density, dtype=float)
    if conditional.ndim != 1 or conditional.size == 0 or not np.isfinite(conditional).all():
        raise ValueError("conditional_log_density must be a non-empty finite vector")
    if marginal.shape != conditional.shape or not np.isfinite(marginal).all():
        raise ValueError("marginal_log_density must be finite and match conditional_log_density")
    n = int(conditional.size)
    if len(covered) != n or len(groups) != n or len(blocks) != n or len(region_size) != n:
        raise ValueError("covered, groups, blocks and region_size must contain one value per validation row")
    return conditional, marginal


def _radius_summary(audit: JointRobustnessRadiusAudit | None) -> JointRadiusAssessmentSummary:
    if audit is None:
        return JointRadiusAssessmentSummary(
            status="not_audited",
            baseline_joint_category=None,
            target_joint_category=None,
            certified_gamma=None,
            break_gamma=None,
            boundary_interval_width=None,
            search_upper_gamma=None,
            radius_is_lower_bound_only=False,
            certified_maximum_multiplier_ratio=None,
        )
    return JointRadiusAssessmentSummary(
        status=audit.radius_status,
        baseline_joint_category=audit.baseline_joint_category,
        target_joint_category=audit.target_joint_category,
        certified_gamma=audit.certified_gamma,
        break_gamma=audit.break_gamma,
        boundary_interval_width=audit.boundary_interval_width,
        search_upper_gamma=float(audit.search_upper_gamma),
        radius_is_lower_bound_only=bool(audit.radius_is_lower_bound_only),
        certified_maximum_multiplier_ratio=audit.certified_maximum_multiplier_ratio,
    )


def assess_state_forecast(
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
    validation_gamma: float = 2.0,
    confidence_level: float = 0.95,
    bootstrap_draws: int = 1000,
    seed: int = 20260906,
    minimum_blocks_per_group: int = 8,
    gain_tolerance: float = 0.0,
    weight_scenarios: Mapping[str, Sequence[float]] | None = None,
    bounded_gamma: float | None = None,
    critical_gamma_search_upper_bound: float = 100.0,
    radius_search_upper_gamma: float | None = None,
    radius_binary_iterations: int = 50,
    novelty_train_X: np.ndarray | None = None,
    novelty_query_X: np.ndarray | None = None,
    novelty_reference_quantile: float = 0.95,
    selection: BiasRobustSelectionResult | None = None,
) -> ForecastAssessmentResult:
    """Run one coherent ODSP forecast-trust assessment on one validation target.

    Weight scenarios are interpreted as complete caller-supplied validation weights,
    not multipliers that ODSP silently combines with ``base_weight``.  Environmental
    novelty is evaluated only when both training and query matrices are supplied.
    The joint robustness radius is opt-in because repeated block-bootstrap stress
    audits can be computationally expensive.
    """

    conditional, marginal = _validate_validation_vectors(
        conditional_log_density,
        marginal_log_density,
        covered,
        groups,
        blocks,
        region_size,
    )
    row_gain = conditional - marginal
    n = int(row_gain.size)

    candidate = evaluate_bias_robust_candidate(
        name,
        conditional,
        marginal,
        covered,
        groups,
        blocks,
        region_size=region_size,
        base_weight=base_weight,
        target_coverage=target_coverage,
        coverage_tolerance=coverage_tolerance,
        gamma=validation_gamma,
        confidence_level=confidence_level,
        bootstrap_draws=bootstrap_draws,
        seed=seed,
        minimum_blocks_per_group=minimum_blocks_per_group,
        gain_tolerance=gain_tolerance,
    )

    sampling_weight_audit = None
    if weight_scenarios is not None:
        sampling_weight_audit = audit_sampling_weight_sensitivity(
            row_gain,
            groups,
            weight_scenarios,
            blocks=blocks,
            confidence_level=confidence_level,
            bootstrap_draws=bootstrap_draws,
            seed=seed,
            minimum_blocks_per_group=minimum_blocks_per_group,
            gain_tolerance=gain_tolerance,
        )

    bounded_audit = None
    if bounded_gamma is not None:
        bounded_audit = audit_bounded_reweighting_robustness(
            row_gain,
            groups,
            base_weight=base_weight,
            gamma=bounded_gamma,
            gain_tolerance=gain_tolerance,
            critical_gamma_search_upper_bound=critical_gamma_search_upper_bound,
        )

    radius_audit = None
    if radius_search_upper_gamma is not None:
        radius_audit = audit_joint_robustness_radius(
            row_gain,
            groups,
            blocks,
            base_weight=base_weight,
            confidence_level=confidence_level,
            bootstrap_draws=bootstrap_draws,
            seed=seed,
            minimum_blocks_per_group=minimum_blocks_per_group,
            gain_tolerance=gain_tolerance,
            search_upper_gamma=radius_search_upper_gamma,
            binary_iterations=radius_binary_iterations,
        )

    if (novelty_train_X is None) != (novelty_query_X is None):
        raise ValueError("novelty_train_X and novelty_query_X must be supplied together")
    novelty_rows: tuple[NoveltySummary, ...] = ()
    dossier_novelty: tuple[NoveltySummary, ...] | None = None
    if novelty_train_X is not None and novelty_query_X is not None:
        novelty_model = fit_environmental_novelty_model(
            np.asarray(novelty_train_X, dtype=float),
            reference_quantile=novelty_reference_quantile,
        )
        novelty_rows = novelty_model.summarize(np.asarray(novelty_query_X, dtype=float))
        dossier_novelty = novelty_rows

    dossier = build_forecast_trust_dossier_v2(
        candidate,
        sampling_weight_audit=sampling_weight_audit,
        bounded_reweighting_audit=bounded_audit,
        deployment_novelty_rows=dossier_novelty,
        selection=selection,
    )

    if dossier.aggregate_confidence_score_emitted:
        raise ValueError("dossier unexpectedly emits an aggregate confidence score")

    settings = {
        "target_coverage": float(target_coverage),
        "coverage_tolerance": float(coverage_tolerance),
        "validation_gamma": float(validation_gamma),
        "confidence_level": float(confidence_level),
        "bootstrap_draws": int(bootstrap_draws),
        "seed": int(seed),
        "minimum_blocks_per_group": int(minimum_blocks_per_group),
        "gain_tolerance": float(gain_tolerance),
        "sampling_weight_audited": weight_scenarios is not None,
        "bounded_reweighting_audited": bounded_gamma is not None,
        "bounded_gamma": (None if bounded_gamma is None else float(bounded_gamma)),
        "joint_radius_audited": radius_search_upper_gamma is not None,
        "radius_search_upper_gamma": (
            None if radius_search_upper_gamma is None else float(radius_search_upper_gamma)
        ),
        "novelty_audited": novelty_train_X is not None,
        "selection_compared": selection is not None,
    }

    return ForecastAssessmentResult(
        candidate_name=candidate.name,
        row_count=n,
        candidate=candidate,
        sampling_weight_audit=sampling_weight_audit,
        bounded_reweighting_audit=bounded_audit,
        joint_radius=_radius_summary(radius_audit),
        novelty_rows=novelty_rows,
        dossier=dossier,
        settings=settings,
        aggregate_confidence_score_emitted=False,
    )
