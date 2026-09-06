"""High-level, non-collapsing trust dossier for ecological-state forecasts.

The dossier composes existing ODSP validation and deployment diagnostics.  It does
not create a new confidence score or allow deployment novelty to rewrite validation
history.  Validation blockers and deployment warnings remain separate.
"""
from __future__ import annotations

from dataclasses import asdict, dataclass
from typing import Sequence

from .prediction_novelty import NoveltySummary
from .robust_trust_aware_model_selection import (
    RobustTrustAwareCandidateScore,
    RobustTrustAwareSelectionResult,
)


@dataclass(frozen=True)
class ValidationGateSummary:
    point_transfer_gate: str
    point_transfer_category: str
    groupwise_coverage_gate: str
    groupwise_coverage_category: str
    transfer_uncertainty_gate: str
    robust_transfer_category: str
    robust_validation_status: str
    mean_log_density_gain: float
    minimum_group_lower_bound: float | None
    worst_group_coverage_error: float
    blocking_reasons: tuple[str, ...]

    def as_dict(self) -> dict[str, object]:
        payload = asdict(self)
        payload["blocking_reasons"] = list(self.blocking_reasons)
        return payload


@dataclass(frozen=True)
class DeploymentTrustSummary:
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
class SelectionTrustSummary:
    status: str
    compared: bool
    robust_trusted: bool
    pareto_member: bool
    recommended: bool

    def as_dict(self) -> dict[str, object]:
        return asdict(self)


@dataclass(frozen=True)
class ForecastTrustDossier:
    candidate_name: str
    validation: ValidationGateSummary
    deployment: DeploymentTrustSummary
    selection: SelectionTrustSummary
    aggregate_confidence_score_emitted: bool

    def as_dict(self) -> dict[str, object]:
        return {
            "candidate_name": self.candidate_name,
            "validation": self.validation.as_dict(),
            "deployment": self.deployment.as_dict(),
            "selection": self.selection.as_dict(),
            "aggregate_confidence_score_emitted": self.aggregate_confidence_score_emitted,
        }


def _validation_summary(candidate: RobustTrustAwareCandidateScore) -> ValidationGateSummary:
    point = candidate.point_and_coverage
    forecast = point.forecast_score
    coverage = point.groupwise_trust
    uncertainty = candidate.transfer_uncertainty

    point_gate = "pass" if forecast.transfer_admissible else "fail"
    coverage_gate = "pass" if coverage.coverage_category == "calibrated" else "fail"

    robust_category = uncertainty.robust_transfer_category
    if robust_category == "robust_generalizing":
        uncertainty_gate = "pass"
    elif robust_category == "unavailable":
        uncertainty_gate = "unavailable"
    elif robust_category == "uncertain":
        uncertainty_gate = "uncertain"
    else:
        uncertainty_gate = "fail"

    blockers: list[str] = []
    if point_gate != "pass":
        blockers.append("point_transfer_failure")
    if coverage_gate != "pass":
        blockers.append("groupwise_coverage_failure")
    if uncertainty_gate == "uncertain":
        blockers.append("transfer_uncertain")
    elif uncertainty_gate == "unavailable":
        blockers.append("transfer_unavailable")
    elif uncertainty_gate == "fail":
        blockers.append("transfer_nonpositive")

    if uncertainty_gate == "unavailable":
        validation_status = "unavailable"
    elif candidate.robust_trusted_admissible:
        validation_status = "admitted"
    else:
        validation_status = "blocked"

    return ValidationGateSummary(
        point_transfer_gate=point_gate,
        point_transfer_category=forecast.transfer_category,
        groupwise_coverage_gate=coverage_gate,
        groupwise_coverage_category=coverage.coverage_category,
        transfer_uncertainty_gate=uncertainty_gate,
        robust_transfer_category=robust_category,
        robust_validation_status=validation_status,
        mean_log_density_gain=float(forecast.mean_log_density_gain),
        minimum_group_lower_bound=candidate.minimum_group_lower_bound,
        worst_group_coverage_error=float(point.worst_group_coverage_error),
        blocking_reasons=tuple(blockers),
    )


def _deployment_summary(
    novelty_rows: Sequence[NoveltySummary] | None,
) -> DeploymentTrustSummary:
    if novelty_rows is None:
        return DeploymentTrustSummary(
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

    return DeploymentTrustSummary(
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
    selection: RobustTrustAwareSelectionResult | None,
) -> SelectionTrustSummary:
    if selection is None:
        return SelectionTrustSummary(
            status="not_compared",
            compared=False,
            robust_trusted=False,
            pareto_member=False,
            recommended=False,
        )

    candidate_names = {row.name for row in selection.candidates}
    if candidate_name not in candidate_names:
        raise ValueError("candidate is not present in the supplied selection result")
    robust = candidate_name in selection.robust_trusted_names
    pareto = candidate_name in selection.pareto_front_names
    recommended = candidate_name == selection.recommended_by_log_score
    if recommended:
        status = "recommended"
    elif pareto:
        status = "pareto_member"
    elif robust:
        status = "robust_trusted_not_pareto"
    else:
        status = "not_robust_trusted"
    return SelectionTrustSummary(
        status=status,
        compared=True,
        robust_trusted=robust,
        pareto_member=pareto,
        recommended=recommended,
    )


def build_forecast_trust_dossier(
    candidate: RobustTrustAwareCandidateScore,
    *,
    deployment_novelty_rows: Sequence[NoveltySummary] | None = None,
    selection: RobustTrustAwareSelectionResult | None = None,
) -> ForecastTrustDossier:
    """Compose validated evidence and deployment warnings without collapsing them."""

    return ForecastTrustDossier(
        candidate_name=candidate.name,
        validation=_validation_summary(candidate),
        deployment=_deployment_summary(deployment_novelty_rows),
        selection=_selection_summary(candidate.name, selection),
        aggregate_confidence_score_emitted=False,
    )
