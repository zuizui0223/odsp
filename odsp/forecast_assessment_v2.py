"""Extended one-call forecast assessment over the current ODSP trust stack.

V2 preserves the complete v1 assessment as immutable evidence and optionally adds
three later audits on the same held-out target: simultaneous familywise group
certification, model-refit transfer uncertainty, and block-definition sensitivity.
The added evidence forms an explicit extended-certification trace; it never
retroactively rewrites the original validation/dossier history.
"""
from __future__ import annotations

from dataclasses import asdict, dataclass
from typing import Mapping, Sequence

import numpy as np

from .block_definition_sensitivity import (
    BlockDefinitionSensitivityAudit,
    audit_block_definition_sensitivity,
)
from .forecast_assessment import ForecastAssessmentResult, assess_state_forecast
from .model_refit_transfer_uncertainty import (
    ModelRefitTransferAudit,
    audit_model_refit_transfer_uncertainty,
)
from .simultaneous_group_certification import (
    SimultaneousGroupCertificationAudit,
    audit_simultaneous_group_certification,
)


@dataclass(frozen=True)
class ExtendedCertificationSummary:
    base_validation_status: str
    base_operational_status: str
    simultaneous_status: str
    simultaneous_category: str
    model_refit_status: str
    model_refit_category: str
    block_definition_status: str
    block_definition_category: str
    certification_status: str
    operational_status: str
    extended_blocking_reasons: tuple[str, ...]
    warning_reasons: tuple[str, ...]
    trace: tuple[str, ...]

    def as_dict(self) -> dict[str, object]:
        payload = asdict(self)
        payload["extended_blocking_reasons"] = list(self.extended_blocking_reasons)
        payload["warning_reasons"] = list(self.warning_reasons)
        payload["trace"] = list(self.trace)
        return payload


@dataclass(frozen=True)
class ForecastAssessmentV2Result:
    candidate_name: str
    row_count: int
    base_assessment: ForecastAssessmentResult
    simultaneous_group_audit: SimultaneousGroupCertificationAudit | None
    model_refit_audit: ModelRefitTransferAudit | None
    block_definition_audit: BlockDefinitionSensitivityAudit | None
    extended_certification: ExtendedCertificationSummary
    refit_reference_match_error: float | None
    settings: dict[str, object]
    aggregate_confidence_score_emitted: bool

    def as_dict(self) -> dict[str, object]:
        return {
            "candidate_name": self.candidate_name,
            "row_count": self.row_count,
            "base_assessment": self.base_assessment.as_dict(),
            "simultaneous_group_audit": (
                None if self.simultaneous_group_audit is None
                else self.simultaneous_group_audit.as_dict()
            ),
            "model_refit_audit": (
                None if self.model_refit_audit is None else self.model_refit_audit.as_dict()
            ),
            "block_definition_audit": (
                None if self.block_definition_audit is None
                else self.block_definition_audit.as_dict()
            ),
            "extended_certification": self.extended_certification.as_dict(),
            "refit_reference_match_error": self.refit_reference_match_error,
            "settings": dict(self.settings),
            "aggregate_confidence_score_emitted": self.aggregate_confidence_score_emitted,
        }


def _formal_layer_status(category: str | None, *, audited: bool) -> str:
    if not audited:
        return "not_audited"
    if category == "robust_generalizing":
        return "pass"
    if category == "unavailable":
        return "unavailable"
    if category == "uncertain":
        return "uncertain"
    if category in {"robust_non_generalizing", "mixed"}:
        return "fail"
    return "fail"


def _block_definition_status(category: str | None, *, audited: bool) -> str:
    if not audited:
        return "not_audited"
    if category == "block_definition_robust_generalizing":
        return "pass"
    if category == "stable_unavailable":
        return "unavailable"
    if category == "block_definition_sensitive":
        return "sensitive"
    if category == "block_definition_robust_non_generalizing":
        return "non_generalizing"
    return "warning"


def _reference_row_index(
    refit_count: int,
    refit_ids: Sequence[object] | None,
    reference_refit_id: object | None,
) -> tuple[int, str]:
    if refit_ids is None:
        ids = tuple(f"refit-{index:09d}" for index in range(refit_count))
    else:
        if len(refit_ids) != refit_count:
            raise ValueError("refit_ids must contain one identifier per refit")
        ids = tuple(str(value).strip() for value in refit_ids)
        if any(not value for value in ids) or len(set(ids)) != len(ids):
            raise ValueError("refit_ids must be non-empty and unique")
    if reference_refit_id is None:
        reference = min(ids)
    else:
        reference = str(reference_refit_id).strip()
        if reference not in ids:
            raise ValueError("reference_refit_id must identify one supplied refit")
    return ids.index(reference), reference


def _extended_summary(
    base: ForecastAssessmentResult,
    simultaneous: SimultaneousGroupCertificationAudit | None,
    refit: ModelRefitTransferAudit | None,
    block_definition: BlockDefinitionSensitivityAudit | None,
) -> ExtendedCertificationSummary:
    base_validation = base.dossier.validation.validation_status
    base_operational = base.dossier.decision_trace.operational_status

    simultaneous_category = (
        "not_audited" if simultaneous is None else simultaneous.max_t_transfer_category
    )
    refit_category = "not_audited" if refit is None else refit.refit_aware_category
    block_category = (
        "not_audited" if block_definition is None else block_definition.sensitivity_category
    )
    simultaneous_status = _formal_layer_status(
        None if simultaneous is None else simultaneous.max_t_transfer_category,
        audited=simultaneous is not None,
    )
    refit_status = _formal_layer_status(
        None if refit is None else refit.refit_aware_category,
        audited=refit is not None,
    )
    block_status = _block_definition_status(
        None if block_definition is None else block_definition.sensitivity_category,
        audited=block_definition is not None,
    )

    formal_statuses = [
        status
        for status in (simultaneous_status, refit_status)
        if status != "not_audited"
    ]
    if not formal_statuses:
        certification = "not_audited"
    elif any(status in {"fail", "uncertain"} for status in formal_statuses):
        certification = "not_certified"
    elif any(status == "unavailable" for status in formal_statuses):
        certification = "unavailable"
    elif all(status == "pass" for status in formal_statuses):
        certification = "certified"
    else:
        certification = "not_certified"

    blockers: list[str] = []
    if simultaneous_status == "uncertain":
        blockers.append("simultaneous_group_uncertain")
    elif simultaneous_status == "unavailable":
        blockers.append("simultaneous_group_unavailable")
    elif simultaneous_status == "fail":
        blockers.append("simultaneous_group_nonpositive_or_mixed")
    if refit_status == "uncertain":
        blockers.append("model_refit_uncertain")
    elif refit_status == "unavailable":
        blockers.append("model_refit_unavailable")
    elif refit_status == "fail":
        blockers.append("model_refit_nonpositive_or_mixed")

    warnings = list(base.dossier.decision_trace.warning_reasons)
    if block_status == "sensitive":
        warnings.append("block_definition_sensitive")
    elif block_status == "unavailable":
        warnings.append("block_definition_unavailable")
    elif block_status == "non_generalizing":
        warnings.append("block_definition_non_generalizing")
    elif block_status == "warning":
        warnings.append("block_definition_warning")

    if base_validation == "unavailable":
        operational = "unavailable"
    elif base_validation == "blocked":
        operational = "blocked"
    elif certification == "not_certified":
        operational = "admitted_extended_not_certified"
    elif certification == "unavailable":
        operational = "admitted_extended_unavailable"
    elif certification == "certified":
        operational = "admitted_with_warnings" if warnings else "admitted"
    else:
        operational = base_operational

    trace = (
        f"base_validation:{base_validation}",
        f"simultaneous:{simultaneous_category}",
        f"model_refit:{refit_category}",
        f"block_definition:{block_category}",
        f"extended_certification:{certification}",
        f"operational:{operational}",
    )
    return ExtendedCertificationSummary(
        base_validation_status=base_validation,
        base_operational_status=base_operational,
        simultaneous_status=simultaneous_status,
        simultaneous_category=simultaneous_category,
        model_refit_status=refit_status,
        model_refit_category=refit_category,
        block_definition_status=block_status,
        block_definition_category=block_category,
        certification_status=certification,
        operational_status=operational,
        extended_blocking_reasons=tuple(blockers),
        warning_reasons=tuple(dict.fromkeys(warnings)),
        trace=trace,
    )


def assess_state_forecast_v2(
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
    selection=None,
    run_simultaneous_group_certification: bool = False,
    simultaneous_draws: int = 2000,
    refit_row_gain: Sequence[Sequence[float]] | None = None,
    refit_ids: Sequence[object] | None = None,
    reference_refit_id: object | None = None,
    refit_nested_draws: int = 2000,
    minimum_refits: int = 8,
    refit_reference_match_tolerance: float = 1e-12,
    alternative_block_definitions: Mapping[str, Sequence[object]] | None = None,
) -> ForecastAssessmentV2Result:
    """Run v1 assessment plus optional current-generation certification layers."""

    base = assess_state_forecast(
        name,
        conditional_log_density,
        marginal_log_density,
        covered,
        groups,
        blocks,
        region_size=region_size,
        base_weight=base_weight,
        target_coverage=target_coverage,
        coverage_tolerance=coverage_tolerance,
        validation_gamma=validation_gamma,
        confidence_level=confidence_level,
        bootstrap_draws=bootstrap_draws,
        seed=seed,
        minimum_blocks_per_group=minimum_blocks_per_group,
        gain_tolerance=gain_tolerance,
        weight_scenarios=weight_scenarios,
        bounded_gamma=bounded_gamma,
        critical_gamma_search_upper_bound=critical_gamma_search_upper_bound,
        radius_search_upper_gamma=radius_search_upper_gamma,
        radius_binary_iterations=radius_binary_iterations,
        novelty_train_X=novelty_train_X,
        novelty_query_X=novelty_query_X,
        novelty_reference_quantile=novelty_reference_quantile,
        selection=selection,
    )

    conditional = np.asarray(conditional_log_density, dtype=float)
    marginal = np.asarray(marginal_log_density, dtype=float)
    row_gain = conditional - marginal

    simultaneous = None
    if run_simultaneous_group_certification:
        simultaneous = audit_simultaneous_group_certification(
            row_gain,
            groups,
            blocks=blocks,
            sample_weight=base_weight,
            familywise_confidence_level=confidence_level,
            bootstrap_draws=simultaneous_draws,
            seed=seed,
            minimum_blocks_per_group=minimum_blocks_per_group,
            gain_tolerance=gain_tolerance,
        )

    refit = None
    match_error = None
    if refit_row_gain is not None:
        matrix = np.asarray(refit_row_gain, dtype=float)
        if matrix.ndim != 2 or matrix.shape[1] != row_gain.size or not np.isfinite(matrix).all():
            raise ValueError("refit_row_gain must be a finite refits x validation_rows matrix aligned to the base assessment")
        reference_index, reference_label = _reference_row_index(
            matrix.shape[0], refit_ids, reference_refit_id
        )
        match_error = float(np.max(np.abs(matrix[reference_index] - row_gain)))
        if not np.isfinite(refit_reference_match_tolerance) or refit_reference_match_tolerance < 0.0:
            raise ValueError("refit_reference_match_tolerance must be finite and non-negative")
        if match_error > refit_reference_match_tolerance:
            raise ValueError(
                "declared model-refit reference row does not match the base assessment row_gain"
            )
        refit = audit_model_refit_transfer_uncertainty(
            matrix,
            groups,
            blocks=blocks,
            refit_ids=refit_ids,
            reference_refit_id=reference_label,
            sample_weight=base_weight,
            familywise_confidence_level=confidence_level,
            nested_draws=refit_nested_draws,
            seed=seed,
            minimum_refits=minimum_refits,
            minimum_blocks_per_group=minimum_blocks_per_group,
            gain_tolerance=gain_tolerance,
        )

    block_definition = None
    if alternative_block_definitions is not None:
        if not alternative_block_definitions:
            raise ValueError("alternative_block_definitions must contain at least one alternative")
        if "primary" in alternative_block_definitions:
            raise ValueError("alternative block definitions may not use the reserved name 'primary'")
        definitions: dict[str, Sequence[object]] = {"primary": blocks}
        definitions.update(alternative_block_definitions)
        block_definition = audit_block_definition_sensitivity(
            row_gain,
            groups,
            definitions,
            sample_weight=base_weight,
            confidence_level=confidence_level,
            bootstrap_draws=bootstrap_draws,
            seed=seed,
            minimum_blocks_per_group=minimum_blocks_per_group,
            gain_tolerance=gain_tolerance,
        )

    extended = _extended_summary(base, simultaneous, refit, block_definition)
    settings = {
        "simultaneous_group_certification_audited": simultaneous is not None,
        "simultaneous_draws": int(simultaneous_draws),
        "model_refit_uncertainty_audited": refit is not None,
        "refit_nested_draws": int(refit_nested_draws),
        "minimum_refits": int(minimum_refits),
        "refit_reference_match_tolerance": float(refit_reference_match_tolerance),
        "block_definition_sensitivity_audited": block_definition is not None,
    }
    return ForecastAssessmentV2Result(
        candidate_name=base.candidate_name,
        row_count=base.row_count,
        base_assessment=base,
        simultaneous_group_audit=simultaneous,
        model_refit_audit=refit,
        block_definition_audit=block_definition,
        extended_certification=extended,
        refit_reference_match_error=match_error,
        settings=settings,
        aggregate_confidence_score_emitted=False,
    )
