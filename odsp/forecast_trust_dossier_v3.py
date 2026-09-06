"""Forecast trust dossier v3 with certified joint-robustness radius.

V3 preserves the validated V2 sections and adds one separate robustness-radius
layer.  The radius never rewrites validation history: a finite radius is a warning
about how far the current transfer-sign certification extends, while blocked or
unavailable validation remains blocked or unavailable regardless of the radius.
"""
from __future__ import annotations

from dataclasses import asdict, dataclass
from typing import Sequence

from .bias_robust_model_selection import BiasRobustCandidateScore, BiasRobustSelectionResult
from .bounded_reweighting_robustness import BoundedReweightingAudit
from .forecast_trust_dossier_v2 import (
    BiasRobustSelectionSummary,
    BiasRobustValidationSummary,
    DeploymentTrustSummaryV2,
    ForecastTrustDossierV2,
    RobustnessProfileSummary,
    build_forecast_trust_dossier_v2,
)
from .joint_robustness_radius import JointRobustnessRadiusAudit
from .prediction_novelty import NoveltySummary
from .sampling_weight_sensitivity import SamplingWeightSensitivityAudit


@dataclass(frozen=True)
class JointRadiusSummary:
    gate: str
    status: str
    baseline_joint_category: str | None
    target_joint_category: str | None
    certified_gamma: float | None
    break_gamma: float | None
    boundary_interval_width: float | None
    radius_is_lower_bound_only: bool
    certified_maximum_multiplier_ratio: float | None
    search_upper_gamma: float | None
    limiting_group_count: int
    limiting_group_ids: tuple[str, ...]
    warnings: tuple[str, ...]

    def as_dict(self) -> dict[str, object]:
        payload=asdict(self)
        payload["limiting_group_ids"]=list(self.limiting_group_ids)
        payload["warnings"]=list(self.warnings)
        return payload


@dataclass(frozen=True)
class DecisionTraceSummaryV3:
    operational_status: str
    validation_status: str
    selection_status: str
    blocking_reasons: tuple[str, ...]
    warning_reasons: tuple[str, ...]
    trace: tuple[str, ...]

    def as_dict(self) -> dict[str, object]:
        payload=asdict(self)
        payload["blocking_reasons"]=list(self.blocking_reasons)
        payload["warning_reasons"]=list(self.warning_reasons)
        payload["trace"]=list(self.trace)
        return payload


@dataclass(frozen=True)
class ForecastTrustDossierV3:
    candidate_name: str
    validation: BiasRobustValidationSummary
    robustness_profile: RobustnessProfileSummary
    joint_radius: JointRadiusSummary
    deployment: DeploymentTrustSummaryV2
    selection: BiasRobustSelectionSummary
    decision_trace: DecisionTraceSummaryV3
    aggregate_confidence_score_emitted: bool

    def as_dict(self) -> dict[str, object]:
        return {
            "candidate_name":self.candidate_name,
            "validation":self.validation.as_dict(),
            "robustness_profile":self.robustness_profile.as_dict(),
            "joint_radius":self.joint_radius.as_dict(),
            "deployment":self.deployment.as_dict(),
            "selection":self.selection.as_dict(),
            "decision_trace":self.decision_trace.as_dict(),
            "aggregate_confidence_score_emitted":self.aggregate_confidence_score_emitted,
        }


def _radius_summary(
    candidate: BiasRobustCandidateScore,
    radius: JointRobustnessRadiusAudit | None,
) -> JointRadiusSummary:
    if radius is None:
        return JointRadiusSummary(
            gate="not_audited",status="not_audited",baseline_joint_category=None,
            target_joint_category=None,certified_gamma=None,break_gamma=None,
            boundary_interval_width=None,radius_is_lower_bound_only=False,
            certified_maximum_multiplier_ratio=None,search_upper_gamma=None,
            limiting_group_count=0,limiting_group_ids=(),warnings=(),
        )
    if radius.aggregate_confidence_score_emitted:
        raise ValueError("joint-radius audit unexpectedly emits an aggregate confidence score")
    joint=candidate.joint_robustness
    if radius.row_count!=joint.row_count:
        raise ValueError("joint-radius row count disagrees with candidate validation evidence")
    if radius.group_count!=joint.group_count:
        raise ValueError("joint-radius group count disagrees with candidate validation evidence")
    if radius.point_transfer_category!=joint.point_transfer_category:
        raise ValueError("joint-radius point transfer category disagrees with candidate validation evidence")

    status=radius.radius_status
    warnings: list[str]=[]
    if status=="robust_through_search_upper":
        gate="pass"
    elif status=="finite_radius":
        gate="warning"
        warnings.append("finite_joint_robustness_radius")
    elif status=="not_certified_at_baseline":
        gate="warning"
        warnings.append("joint_radius_not_certified_at_baseline")
    elif status=="unavailable":
        gate="unavailable"
        warnings.append("joint_radius_unavailable")
    else:
        gate="warning"
        warnings.append("joint_radius_unresolved")

    return JointRadiusSummary(
        gate=gate,status=status,
        baseline_joint_category=radius.baseline_joint_category,
        target_joint_category=radius.target_joint_category,
        certified_gamma=radius.certified_gamma,
        break_gamma=radius.break_gamma,
        boundary_interval_width=radius.boundary_interval_width,
        radius_is_lower_bound_only=radius.radius_is_lower_bound_only,
        certified_maximum_multiplier_ratio=radius.certified_maximum_multiplier_ratio,
        search_upper_gamma=radius.search_upper_gamma,
        limiting_group_count=len(radius.limiting_group_ids),
        limiting_group_ids=radius.limiting_group_ids,
        warnings=tuple(warnings),
    )


def _decision_trace(base: ForecastTrustDossierV2, radius: JointRadiusSummary) -> DecisionTraceSummaryV3:
    blockers=tuple(base.decision_trace.blocking_reasons)
    warnings=tuple(base.decision_trace.warning_reasons)+tuple(radius.warnings)
    validation_status=base.validation.validation_status
    if validation_status=="unavailable":
        operational="unavailable"
    elif validation_status=="blocked":
        operational="blocked"
    elif warnings:
        operational="admitted_with_warnings"
    else:
        operational="admitted"
    trace=(
        f"validation:{validation_status}",
        f"joint_robustness:{base.validation.joint_robustness_category}",
        f"joint_radius:{radius.status}",
        f"sampling_weight:{base.robustness_profile.sampling_weight_status}",
        f"bounded_reweighting:{base.robustness_profile.bounded_reweighting_status}",
        f"deployment:{base.deployment.status}",
        f"selection:{base.selection.status}",
    )
    return DecisionTraceSummaryV3(
        operational_status=operational,
        validation_status=validation_status,
        selection_status=base.selection.status,
        blocking_reasons=blockers,
        warning_reasons=warnings,
        trace=trace,
    )


def build_forecast_trust_dossier_v3(
    candidate: BiasRobustCandidateScore,
    *,
    sampling_weight_audit: SamplingWeightSensitivityAudit | None=None,
    bounded_reweighting_audit: BoundedReweightingAudit | None=None,
    joint_radius_audit: JointRobustnessRadiusAudit | None=None,
    deployment_novelty_rows: Sequence[NoveltySummary] | None=None,
    selection: BiasRobustSelectionResult | None=None,
) -> ForecastTrustDossierV3:
    """Build V3 while preserving all V2 evidence semantics."""

    base=build_forecast_trust_dossier_v2(
        candidate,
        sampling_weight_audit=sampling_weight_audit,
        bounded_reweighting_audit=bounded_reweighting_audit,
        deployment_novelty_rows=deployment_novelty_rows,
        selection=selection,
    )
    radius=_radius_summary(candidate,joint_radius_audit)
    decision=_decision_trace(base,radius)
    return ForecastTrustDossierV3(
        candidate_name=base.candidate_name,
        validation=base.validation,
        robustness_profile=base.robustness_profile,
        joint_radius=radius,
        deployment=base.deployment,
        selection=base.selection,
        decision_trace=decision,
        aggregate_confidence_score_emitted=False,
    )
