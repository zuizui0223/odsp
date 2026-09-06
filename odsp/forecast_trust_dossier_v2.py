"""Forecast trust dossier v2 with explicit robustness and deployment traceability.

This module composes existing ODSP evidence without creating new statistical
information.  Validation admission is inherited from ``BiasRobustCandidateScore``.
Sampling-weight sensitivity, deterministic bounded reweighting, environmental
novelty, and selection status are retained as separate evidence layers so that a
warning cannot silently rewrite validation history and a pass cannot rescue a
failed gate.
"""
from __future__ import annotations

from dataclasses import asdict, dataclass
from typing import Sequence

from .bias_robust_model_selection import (
    BiasRobustCandidateScore,
    BiasRobustSelectionResult,
)
from .bounded_reweighting_robustness import BoundedReweightingAudit
from .prediction_novelty import NoveltySummary
from .sampling_weight_sensitivity import SamplingWeightSensitivityAudit


@dataclass(frozen=True)
class BiasRobustValidationSummary:
    point_transfer_gate: str
    point_transfer_category: str
    groupwise_coverage_gate: str
    groupwise_coverage_category: str
    joint_robustness_gate: str
    joint_robustness_category: str
    validation_gamma: float
    validation_status: str
    mean_log_density_gain: float
    minimum_worst_case_lower_bound: float | None
    maximum_best_case_upper_bound: float | None
    worst_group_coverage_error: float
    blocking_reasons: tuple[str, ...]

    def as_dict(self) -> dict[str, object]:
        payload = asdict(self)
        payload["blocking_reasons"] = list(self.blocking_reasons)
        return payload


@dataclass(frozen=True)
class RobustnessProfileSummary:
    sampling_weight_gate: str
    sampling_weight_status: str
    sampling_scenario_count: int
    minimum_scenario_mean_gain: float | None
    maximum_scenario_mean_gain: float | None
    sampling_group_status_flip_count: int
    bounded_reweighting_gate: str
    bounded_reweighting_status: str
    bounded_gamma: float | None
    minimum_worst_case_group_gain: float | None
    maximum_best_case_group_gain: float | None
    minimum_critical_gamma: float | None
    critical_gamma_group_count: int
    warnings: tuple[str, ...]

    def as_dict(self) -> dict[str, object]:
        payload = asdict(self)
        payload["warnings"] = list(self.warnings)
        return payload


@dataclass(frozen=True)
class DeploymentTrustSummaryV2:
    row_count: int
    status: str
    in_domain_count: int
    novel_count: int
    strict_extrapolation_count: int
    in_domain_fraction: float
    novel_fraction: float
    strict_extrapolation_fraction: float
    maximum_novelty_ratio: float | None
    warnings: tuple[str, ...]

    def as_dict(self) -> dict[str, object]:
        payload = asdict(self)
        payload["warnings"] = list(self.warnings)
        return payload


@dataclass(frozen=True)
class BiasRobustSelectionSummary:
    status: str
    compared: bool
    bias_robust_trusted: bool
    pareto_member: bool
    recommended: bool

    def as_dict(self) -> dict[str, object]:
        return asdict(self)


@dataclass(frozen=True)
class DecisionTraceSummary:
    operational_status: str
    validation_status: str
    selection_status: str
    blocking_reasons: tuple[str, ...]
    warning_reasons: tuple[str, ...]
    trace: tuple[str, ...]

    def as_dict(self) -> dict[str, object]:
        payload = asdict(self)
        payload["blocking_reasons"] = list(self.blocking_reasons)
        payload["warning_reasons"] = list(self.warning_reasons)
        payload["trace"] = list(self.trace)
        return payload


@dataclass(frozen=True)
class ForecastTrustDossierV2:
    candidate_name: str
    validation: BiasRobustValidationSummary
    robustness_profile: RobustnessProfileSummary
    deployment: DeploymentTrustSummaryV2
    selection: BiasRobustSelectionSummary
    decision_trace: DecisionTraceSummary
    aggregate_confidence_score_emitted: bool

    def as_dict(self) -> dict[str, object]:
        return {
            "candidate_name": self.candidate_name,
            "validation": self.validation.as_dict(),
            "robustness_profile": self.robustness_profile.as_dict(),
            "deployment": self.deployment.as_dict(),
            "selection": self.selection.as_dict(),
            "decision_trace": self.decision_trace.as_dict(),
            "aggregate_confidence_score_emitted": self.aggregate_confidence_score_emitted,
        }


def _validation_summary(candidate: BiasRobustCandidateScore) -> BiasRobustValidationSummary:
    point = candidate.point_and_coverage
    forecast = point.forecast_score
    coverage = point.groupwise_trust
    joint = candidate.joint_robustness

    point_gate = "pass" if forecast.transfer_admissible else "fail"
    coverage_gate = "pass" if coverage.coverage_category == "calibrated" else "fail"
    category = joint.joint_robust_category
    if category == "joint_robust_generalizing":
        joint_gate = "pass"
    elif category == "unavailable":
        joint_gate = "unavailable"
    elif category == "envelope_sensitive":
        joint_gate = "sensitive"
    elif category == "uncertain":
        joint_gate = "uncertain"
    else:
        joint_gate = "fail"

    blockers: list[str] = []
    if point_gate != "pass":
        blockers.append("point_transfer_failure")
    if coverage_gate != "pass":
        blockers.append("groupwise_coverage_failure")
    if joint_gate == "sensitive":
        blockers.append("joint_reweighting_sensitive")
    elif joint_gate == "uncertain":
        blockers.append("joint_transfer_uncertain")
    elif joint_gate == "unavailable":
        blockers.append("joint_transfer_unavailable")
    elif joint_gate == "fail":
        blockers.append("joint_transfer_nonpositive")

    if joint_gate == "unavailable":
        validation_status = "unavailable"
    elif candidate.bias_robust_trusted_admissible:
        validation_status = "admitted"
    else:
        validation_status = "blocked"

    return BiasRobustValidationSummary(
        point_transfer_gate=point_gate,
        point_transfer_category=forecast.transfer_category,
        groupwise_coverage_gate=coverage_gate,
        groupwise_coverage_category=coverage.coverage_category,
        joint_robustness_gate=joint_gate,
        joint_robustness_category=category,
        validation_gamma=float(joint.gamma),
        validation_status=validation_status,
        mean_log_density_gain=float(forecast.mean_log_density_gain),
        minimum_worst_case_lower_bound=candidate.minimum_worst_case_lower_bound,
        maximum_best_case_upper_bound=joint.maximum_best_case_upper_bound,
        worst_group_coverage_error=float(point.worst_group_coverage_error),
        blocking_reasons=tuple(blockers),
    )


def _sampling_gate(category: str) -> str:
    if category == "weight_robust_generalizing":
        return "pass"
    if category == "weight_robust_non_generalizing":
        return "fail"
    if category == "stable_unavailable":
        return "unavailable"
    return "warning"


def _bounded_gate(category: str) -> str:
    if category == "gamma_robust_generalizing":
        return "pass"
    if category == "gamma_robust_non_generalizing":
        return "fail"
    return "warning"


def _robustness_summary(
    sampling_weight: SamplingWeightSensitivityAudit | None,
    bounded_reweighting: BoundedReweightingAudit | None,
) -> RobustnessProfileSummary:
    warnings: list[str] = []

    if sampling_weight is None:
        sampling_gate = "not_audited"
        sampling_status = "not_audited"
        scenario_count = 0
        min_scenario_gain = None
        max_scenario_gain = None
        flip_count = 0
    else:
        if sampling_weight.aggregate_confidence_score_emitted:
            raise ValueError("sampling-weight audit unexpectedly emits an aggregate confidence score")
        sampling_status = sampling_weight.sensitivity_category
        sampling_gate = _sampling_gate(sampling_status)
        scenario_count = int(sampling_weight.scenario_count)
        min_scenario_gain = float(sampling_weight.minimum_scenario_mean_gain)
        max_scenario_gain = float(sampling_weight.maximum_scenario_mean_gain)
        flip_count = int(sampling_weight.group_status_flip_count)
        if sampling_status == "weight_sensitive":
            warnings.append("sampling_weight_sensitive")
        elif sampling_status == "weight_robust_non_generalizing":
            warnings.append("sampling_weight_non_generalizing")
        elif sampling_status == "stable_unavailable":
            warnings.append("sampling_weight_unavailable")
        elif sampling_gate == "warning":
            warnings.append("sampling_weight_uncertain")

    if bounded_reweighting is None:
        bounded_gate = "not_audited"
        bounded_status = "not_audited"
        bounded_gamma = None
        min_worst = None
        max_best = None
        min_critical = None
        critical_count = 0
    else:
        if bounded_reweighting.aggregate_confidence_score_emitted:
            raise ValueError("bounded-reweighting audit unexpectedly emits an aggregate confidence score")
        bounded_status = bounded_reweighting.envelope_transfer_category
        bounded_gate = _bounded_gate(bounded_status)
        bounded_gamma = float(bounded_reweighting.gamma)
        min_worst = float(bounded_reweighting.minimum_worst_case_group_gain)
        max_best = float(bounded_reweighting.maximum_best_case_group_gain)
        finite = [row.critical_gamma for row in bounded_reweighting.groups if row.critical_gamma is not None]
        min_critical = float(min(finite)) if finite else None
        critical_count = len(finite)
        if bounded_status == "gamma_sensitive":
            warnings.append("bounded_reweighting_sensitive")
        elif bounded_status == "gamma_robust_non_generalizing":
            warnings.append("bounded_reweighting_non_generalizing")
        elif bounded_status == "gamma_mixed":
            warnings.append("bounded_reweighting_mixed")

    return RobustnessProfileSummary(
        sampling_weight_gate=sampling_gate,
        sampling_weight_status=sampling_status,
        sampling_scenario_count=scenario_count,
        minimum_scenario_mean_gain=min_scenario_gain,
        maximum_scenario_mean_gain=max_scenario_gain,
        sampling_group_status_flip_count=flip_count,
        bounded_reweighting_gate=bounded_gate,
        bounded_reweighting_status=bounded_status,
        bounded_gamma=bounded_gamma,
        minimum_worst_case_group_gain=min_worst,
        maximum_best_case_group_gain=max_best,
        minimum_critical_gamma=min_critical,
        critical_gamma_group_count=critical_count,
        warnings=tuple(warnings),
    )


def _deployment_summary(
    novelty_rows: Sequence[NoveltySummary] | None,
) -> DeploymentTrustSummaryV2:
    if novelty_rows is None:
        return DeploymentTrustSummaryV2(
            row_count=0,
            status="not_audited",
            in_domain_count=0,
            novel_count=0,
            strict_extrapolation_count=0,
            in_domain_fraction=0.0,
            novel_fraction=0.0,
            strict_extrapolation_fraction=0.0,
            maximum_novelty_ratio=None,
            warnings=(),
        )

    rows = tuple(novelty_rows)
    if not rows:
        raise ValueError("novelty_rows must be non-empty when supplied")
    categories = [row.category for row in rows]
    allowed = {"in_domain", "novel", "strict_extrapolation"}
    if any(category not in allowed for category in categories):
        raise ValueError("novelty_rows contain an unsupported category")

    in_domain = categories.count("in_domain")
    novel = categories.count("novel")
    strict = categories.count("strict_extrapolation")
    n = len(rows)
    warnings: list[str] = []
    if strict:
        status = "strict_extrapolation_warning"
        warnings.append("strict_extrapolation")
        if novel:
            warnings.append("environmental_novelty")
    elif novel:
        status = "novel_warning"
        warnings.append("environmental_novelty")
    else:
        status = "in_domain"

    return DeploymentTrustSummaryV2(
        row_count=n,
        status=status,
        in_domain_count=in_domain,
        novel_count=novel,
        strict_extrapolation_count=strict,
        in_domain_fraction=float(in_domain / n),
        novel_fraction=float(novel / n),
        strict_extrapolation_fraction=float(strict / n),
        maximum_novelty_ratio=float(max(row.novelty_ratio for row in rows)),
        warnings=tuple(warnings),
    )


def _selection_summary(
    candidate_name: str,
    selection: BiasRobustSelectionResult | None,
) -> BiasRobustSelectionSummary:
    if selection is None:
        return BiasRobustSelectionSummary(
            status="not_compared",
            compared=False,
            bias_robust_trusted=False,
            pareto_member=False,
            recommended=False,
        )
    if selection.aggregate_confidence_score_emitted:
        raise ValueError("selection unexpectedly emits an aggregate confidence score")
    candidate_names = {row.name for row in selection.candidates}
    if candidate_name not in candidate_names:
        raise ValueError("candidate is not present in the supplied selection result")
    trusted = candidate_name in selection.bias_robust_trusted_names
    pareto = candidate_name in selection.pareto_front_names
    recommended = candidate_name == selection.recommended_by_log_score
    if recommended:
        status = "recommended"
    elif pareto:
        status = "pareto_member"
    elif trusted:
        status = "bias_robust_trusted_not_pareto"
    else:
        status = "not_bias_robust_trusted"
    return BiasRobustSelectionSummary(
        status=status,
        compared=True,
        bias_robust_trusted=trusted,
        pareto_member=pareto,
        recommended=recommended,
    )


def _decision_trace(
    validation: BiasRobustValidationSummary,
    robustness: RobustnessProfileSummary,
    deployment: DeploymentTrustSummaryV2,
    selection: BiasRobustSelectionSummary,
) -> DecisionTraceSummary:
    blockers = validation.blocking_reasons
    warnings = tuple(robustness.warnings) + tuple(deployment.warnings)
    if validation.validation_status == "unavailable":
        operational = "unavailable"
    elif validation.validation_status == "blocked":
        operational = "blocked"
    elif warnings:
        operational = "admitted_with_warnings"
    else:
        operational = "admitted"
    trace = (
        f"validation:{validation.validation_status}",
        f"joint_robustness:{validation.joint_robustness_category}",
        f"sampling_weight:{robustness.sampling_weight_status}",
        f"bounded_reweighting:{robustness.bounded_reweighting_status}",
        f"deployment:{deployment.status}",
        f"selection:{selection.status}",
    )
    return DecisionTraceSummary(
        operational_status=operational,
        validation_status=validation.validation_status,
        selection_status=selection.status,
        blocking_reasons=blockers,
        warning_reasons=warnings,
        trace=trace,
    )


def build_forecast_trust_dossier_v2(
    candidate: BiasRobustCandidateScore,
    *,
    sampling_weight_audit: SamplingWeightSensitivityAudit | None = None,
    bounded_reweighting_audit: BoundedReweightingAudit | None = None,
    deployment_novelty_rows: Sequence[NoveltySummary] | None = None,
    selection: BiasRobustSelectionResult | None = None,
) -> ForecastTrustDossierV2:
    """Compose the latest ODSP trust evidence into one explicit decision trace.

    The caller is responsible for supplying sensitivity audits that refer to the
    same forecast/evaluation target.  The summary objects do not contain enough row
    provenance to verify that identity mechanically.
    """

    if candidate.joint_robustness.aggregate_confidence_score_emitted:
        raise ValueError("candidate joint robustness unexpectedly emits an aggregate confidence score")
    validation = _validation_summary(candidate)
    robustness = _robustness_summary(sampling_weight_audit, bounded_reweighting_audit)
    deployment = _deployment_summary(deployment_novelty_rows)
    selection_summary = _selection_summary(candidate.name, selection)
    decision = _decision_trace(validation, robustness, deployment, selection_summary)
    return ForecastTrustDossierV2(
        candidate_name=candidate.name,
        validation=validation,
        robustness_profile=robustness,
        deployment=deployment,
        selection=selection_summary,
        decision_trace=decision,
        aggregate_confidence_score_emitted=False,
    )
