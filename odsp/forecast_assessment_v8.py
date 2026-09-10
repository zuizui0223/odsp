"""Forecast Assessment v8: v7 evidence gated by exact-content provenance."""
from __future__ import annotations

from dataclasses import asdict, dataclass
from typing import Mapping, Sequence

from .evaluation_content_provenance import (
    EvaluationContentProvenanceAudit,
    audit_evaluation_content_provenance,
)
from .forecast_assessment_v7 import ForecastAssessmentV7Result, assess_state_forecast_v7


@dataclass(frozen=True)
class ForecastAssessmentV8Certification:
    base_validation_status: str
    base_v7_certification_status: str
    base_v7_operational_status: str
    evaluation_content_provenance_status: str
    downstream_v7_status: str
    evaluation_access_provenance_status: str
    selection_validation_provenance_status: str
    training_validation_provenance_status: str
    heldout_row_provenance_status: str
    certification_status: str
    operational_status: str
    statistical_blocking_reasons: tuple[str, ...]
    provenance_blocking_reasons: tuple[str, ...]
    warning_reasons: tuple[str, ...]
    trace: tuple[str, ...]

    def as_dict(self) -> dict[str, object]:
        payload = asdict(self)
        payload["statistical_blocking_reasons"] = list(self.statistical_blocking_reasons)
        payload["provenance_blocking_reasons"] = list(self.provenance_blocking_reasons)
        payload["warning_reasons"] = list(self.warning_reasons)
        payload["trace"] = list(self.trace)
        return payload


@dataclass(frozen=True)
class ForecastAssessmentV8Result:
    candidate_name: str
    row_count: int
    base_v7_assessment: ForecastAssessmentV7Result
    evaluation_content_provenance: EvaluationContentProvenanceAudit | None
    downstream_v7_assessment: ForecastAssessmentV7Result | None
    v8_certification: ForecastAssessmentV8Certification
    settings: dict[str, object]
    aggregate_confidence_score_emitted: bool

    def as_dict(self) -> dict[str, object]:
        return {
            "candidate_name": self.candidate_name,
            "row_count": self.row_count,
            "base_v7_assessment": self.base_v7_assessment.as_dict(),
            "evaluation_content_provenance": (
                None
                if self.evaluation_content_provenance is None
                else self.evaluation_content_provenance.as_dict()
            ),
            "downstream_v7_assessment": (
                None
                if self.downstream_v7_assessment is None
                else self.downstream_v7_assessment.as_dict()
            ),
            "v8_certification": self.v8_certification.as_dict(),
            "settings": dict(self.settings),
            "aggregate_confidence_score_emitted": self.aggregate_confidence_score_emitted,
        }


def _base_v7(
    name: str,
    conditional_log_density: Sequence[float],
    marginal_log_density: Sequence[float],
    covered: Sequence[bool],
    groups: Sequence[object],
    blocks: Sequence[object],
    *,
    region_size: Sequence[float],
    scheme_nested_draws: int,
    scheme_seed: int | None,
    scheme_minimum_refits: int | None,
    v7_kwargs: Mapping[str, object],
) -> ForecastAssessmentV7Result:
    return assess_state_forecast_v7(
        name,
        conditional_log_density,
        marginal_log_density,
        covered,
        groups,
        blocks,
        region_size=region_size,
        final_evaluation_artifact_id=None,
        accessed_artifact_ids_by_stage=None,
        selection_row_ids_by_stage=None,
        refit_schemes=None,
        scheme_nested_draws=scheme_nested_draws,
        scheme_seed=scheme_seed,
        scheme_minimum_refits=scheme_minimum_refits,
        **dict(v7_kwargs),
    )


def _full_v7(
    name: str,
    conditional_log_density: Sequence[float],
    marginal_log_density: Sequence[float],
    covered: Sequence[bool],
    groups: Sequence[object],
    blocks: Sequence[object],
    *,
    region_size: Sequence[float],
    final_evaluation_artifact_id: object | None,
    accessed_artifact_ids_by_stage: Mapping[object, Sequence[object]] | None,
    expected_evaluation_access_stage_names: Sequence[object] | None,
    validation_row_ids: Sequence[object] | None,
    selection_row_ids_by_stage: Mapping[object, Sequence[object]] | None,
    expected_selection_stage_names: Sequence[object] | None,
    refit_schemes: Mapping[str, Sequence[Sequence[float]]] | None,
    validation_row_ids_by_scheme: Mapping[str, Sequence[object]] | None,
    refit_ids_by_scheme: Mapping[str, Sequence[object]] | None,
    reference_refit_ids_by_scheme: Mapping[str, object] | None,
    training_row_ids_by_scheme: Mapping[str, Mapping[object, Sequence[object]]] | None,
    scheme_nested_draws: int,
    scheme_seed: int | None,
    scheme_minimum_refits: int | None,
    v7_kwargs: Mapping[str, object],
) -> ForecastAssessmentV7Result:
    return assess_state_forecast_v7(
        name,
        conditional_log_density,
        marginal_log_density,
        covered,
        groups,
        blocks,
        region_size=region_size,
        final_evaluation_artifact_id=final_evaluation_artifact_id,
        accessed_artifact_ids_by_stage=accessed_artifact_ids_by_stage,
        expected_evaluation_access_stage_names=expected_evaluation_access_stage_names,
        validation_row_ids=validation_row_ids,
        selection_row_ids_by_stage=selection_row_ids_by_stage,
        expected_selection_stage_names=expected_selection_stage_names,
        refit_schemes=refit_schemes,
        validation_row_ids_by_scheme=validation_row_ids_by_scheme,
        refit_ids_by_scheme=refit_ids_by_scheme,
        reference_refit_ids_by_scheme=reference_refit_ids_by_scheme,
        training_row_ids_by_scheme=training_row_ids_by_scheme,
        scheme_nested_draws=scheme_nested_draws,
        scheme_seed=scheme_seed,
        scheme_minimum_refits=scheme_minimum_refits,
        **dict(v7_kwargs),
    )


def _inherit_summary(
    base: ForecastAssessmentV7Result,
    downstream: ForecastAssessmentV7Result,
    *,
    content_status: str,
) -> ForecastAssessmentV8Certification:
    summary = downstream.v7_certification
    trace = tuple(base.v7_certification.trace) + (
        f"evaluation_content_provenance:{content_status}",
        "downstream_v7:run",
        f"evaluation_access_provenance:{summary.evaluation_access_provenance_status}",
        f"selection_validation_provenance:{summary.selection_validation_provenance_status}",
        f"training_validation_provenance:{summary.training_validation_provenance_status}",
        f"heldout_row_provenance:{summary.heldout_row_provenance_status}",
        f"v8_certification:{summary.certification_status}",
        f"v8_operational:{summary.operational_status}",
    )
    return ForecastAssessmentV8Certification(
        base_validation_status=summary.base_validation_status,
        base_v7_certification_status=base.v7_certification.certification_status,
        base_v7_operational_status=base.v7_certification.operational_status,
        evaluation_content_provenance_status=content_status,
        downstream_v7_status="run",
        evaluation_access_provenance_status=summary.evaluation_access_provenance_status,
        selection_validation_provenance_status=summary.selection_validation_provenance_status,
        training_validation_provenance_status=summary.training_validation_provenance_status,
        heldout_row_provenance_status=summary.heldout_row_provenance_status,
        certification_status=summary.certification_status,
        operational_status=summary.operational_status,
        statistical_blocking_reasons=tuple(summary.statistical_blocking_reasons),
        provenance_blocking_reasons=tuple(summary.provenance_blocking_reasons),
        warning_reasons=tuple(summary.warning_reasons),
        trace=trace,
    )


def _content_leakage_summary(
    base: ForecastAssessmentV7Result,
    provenance: EvaluationContentProvenanceAudit,
) -> ForecastAssessmentV8Certification:
    summary = base.v7_certification
    base_validation = summary.base_validation_status
    base_certification = summary.certification_status

    if base_validation == "unavailable":
        certification = "unavailable"
        operational = "unavailable"
    elif base_validation == "blocked":
        certification = "not_certified"
        operational = "blocked"
    elif base_certification == "not_certified":
        certification = "not_certified"
        operational = "admitted_extended_not_certified"
    elif base_certification == "unavailable":
        certification = "unavailable"
        operational = "admitted_extended_unavailable"
    else:
        certification = "unavailable"
        operational = "admitted_extended_unavailable"

    provenance_reasons = tuple(
        dict.fromkeys(
            tuple(summary.provenance_blocking_reasons)
            + ("final_evaluation_content_leakage",)
        )
    )
    sentinel = "not_run_final_evaluation_content_leakage"
    trace = tuple(summary.trace) + (
        f"evaluation_content_provenance:{provenance.separation_category}",
        f"downstream_v7:{sentinel}",
        f"evaluation_access_provenance:{sentinel}",
        f"selection_validation_provenance:{sentinel}",
        f"training_validation_provenance:{sentinel}",
        f"heldout_row_provenance:{sentinel}",
        f"v8_certification:{certification}",
        f"v8_operational:{operational}",
    )
    return ForecastAssessmentV8Certification(
        base_validation_status=base_validation,
        base_v7_certification_status=base_certification,
        base_v7_operational_status=summary.operational_status,
        evaluation_content_provenance_status=provenance.separation_category,
        downstream_v7_status=sentinel,
        evaluation_access_provenance_status=sentinel,
        selection_validation_provenance_status=sentinel,
        training_validation_provenance_status=sentinel,
        heldout_row_provenance_status=sentinel,
        certification_status=certification,
        operational_status=operational,
        statistical_blocking_reasons=tuple(summary.statistical_blocking_reasons),
        provenance_blocking_reasons=provenance_reasons,
        warning_reasons=tuple(summary.warning_reasons),
        trace=trace,
    )


def assess_state_forecast_v8(
    name: str,
    conditional_log_density: Sequence[float],
    marginal_log_density: Sequence[float],
    covered: Sequence[bool],
    groups: Sequence[object],
    blocks: Sequence[object],
    *,
    region_size: Sequence[float],
    final_evaluation_digest: object | None = None,
    accessed_artifact_digests_by_stage: Mapping[object, Sequence[object]] | None = None,
    expected_evaluation_content_stage_names: Sequence[object] | None = None,
    final_evaluation_artifact_id: object | None = None,
    accessed_artifact_ids_by_stage: Mapping[object, Sequence[object]] | None = None,
    expected_evaluation_access_stage_names: Sequence[object] | None = None,
    validation_row_ids: Sequence[object] | None = None,
    selection_row_ids_by_stage: Mapping[object, Sequence[object]] | None = None,
    expected_selection_stage_names: Sequence[object] | None = None,
    refit_schemes: Mapping[str, Sequence[Sequence[float]]] | None = None,
    validation_row_ids_by_scheme: Mapping[str, Sequence[object]] | None = None,
    refit_ids_by_scheme: Mapping[str, Sequence[object]] | None = None,
    reference_refit_ids_by_scheme: Mapping[str, object] | None = None,
    training_row_ids_by_scheme: Mapping[str, Mapping[object, Sequence[object]]] | None = None,
    scheme_nested_draws: int = 1200,
    scheme_seed: int | None = None,
    scheme_minimum_refits: int | None = None,
    **v7_kwargs,
) -> ForecastAssessmentV8Result:
    """Gate ordinary v7 assessment by exact final-evaluation content provenance.

    The caller supplies SHA-256 digests for a declared pre-final access ledger.
    A byte-identical final-content match suppresses the full v7 path before
    artifact-ID access, selection, training, held-out alignment or refit-scheme
    evidence can run. Different-byte semantic equivalents are outside scope.
    """

    provenance = None
    if accessed_artifact_digests_by_stage is None:
        if final_evaluation_digest is not None:
            raise ValueError(
                "final_evaluation_digest must not be supplied without accessed_artifact_digests_by_stage"
            )
        if expected_evaluation_content_stage_names is not None:
            raise ValueError(
                "expected_evaluation_content_stage_names must not be supplied without accessed_artifact_digests_by_stage"
            )
    else:
        if final_evaluation_digest is None:
            raise ValueError(
                "final_evaluation_digest is required when evaluation-content provenance is supplied"
            )
        provenance = audit_evaluation_content_provenance(
            final_evaluation_digest,
            accessed_artifact_digests_by_stage,
            expected_stage_names=expected_evaluation_content_stage_names,
        )

    base = _base_v7(
        name,
        conditional_log_density,
        marginal_log_density,
        covered,
        groups,
        blocks,
        region_size=region_size,
        scheme_nested_draws=scheme_nested_draws,
        scheme_seed=scheme_seed,
        scheme_minimum_refits=scheme_minimum_refits,
        v7_kwargs=v7_kwargs,
    )

    downstream = None
    if provenance is None or not provenance.final_evaluation_content_accessed:
        downstream = _full_v7(
            name,
            conditional_log_density,
            marginal_log_density,
            covered,
            groups,
            blocks,
            region_size=region_size,
            final_evaluation_artifact_id=final_evaluation_artifact_id,
            accessed_artifact_ids_by_stage=accessed_artifact_ids_by_stage,
            expected_evaluation_access_stage_names=expected_evaluation_access_stage_names,
            validation_row_ids=validation_row_ids,
            selection_row_ids_by_stage=selection_row_ids_by_stage,
            expected_selection_stage_names=expected_selection_stage_names,
            refit_schemes=refit_schemes,
            validation_row_ids_by_scheme=validation_row_ids_by_scheme,
            refit_ids_by_scheme=refit_ids_by_scheme,
            reference_refit_ids_by_scheme=reference_refit_ids_by_scheme,
            training_row_ids_by_scheme=training_row_ids_by_scheme,
            scheme_nested_draws=scheme_nested_draws,
            scheme_seed=scheme_seed,
            scheme_minimum_refits=scheme_minimum_refits,
            v7_kwargs=v7_kwargs,
        )
        summary = _inherit_summary(
            base,
            downstream,
            content_status=(
                "not_audited" if provenance is None else provenance.separation_category
            ),
        )
    else:
        summary = _content_leakage_summary(base, provenance)

    settings = {
        "base_v7_artifact_access_selection_and_scheme_layers_omitted": True,
        "evaluation_content_provenance_audited": provenance is not None,
        "evaluation_content_expected_stage_coverage_checked": (
            False if provenance is None else provenance.expected_stage_coverage_checked
        ),
        "downstream_v7_assessment_run": downstream is not None,
        "scheme_nested_draws": int(scheme_nested_draws),
        "scheme_seed": (
            int(v7_kwargs.get("seed", 20260906)) if scheme_seed is None else int(scheme_seed)
        ),
        "scheme_minimum_refits": (
            int(v7_kwargs.get("minimum_refits", 8))
            if scheme_minimum_refits is None
            else int(scheme_minimum_refits)
        ),
    }
    return ForecastAssessmentV8Result(
        candidate_name=base.candidate_name,
        row_count=base.row_count,
        base_v7_assessment=base,
        evaluation_content_provenance=provenance,
        downstream_v7_assessment=downstream,
        v8_certification=summary,
        settings=settings,
        aggregate_confidence_score_emitted=False,
    )
