"""Forecast Assessment v7: v6 evidence gated by evaluation-access provenance."""
from __future__ import annotations

from dataclasses import asdict, dataclass
from typing import Mapping, Sequence

from .evaluation_access_provenance import (
    EvaluationAccessProvenanceAudit,
    audit_evaluation_access_provenance,
)
from .forecast_assessment_v6 import ForecastAssessmentV6Result, assess_state_forecast_v6


@dataclass(frozen=True)
class ForecastAssessmentV7Certification:
    base_validation_status: str
    base_v6_certification_status: str
    base_v6_operational_status: str
    evaluation_access_provenance_status: str
    downstream_v6_status: str
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
class ForecastAssessmentV7Result:
    candidate_name: str
    row_count: int
    base_v6_assessment: ForecastAssessmentV6Result
    evaluation_access_provenance: EvaluationAccessProvenanceAudit | None
    downstream_v6_assessment: ForecastAssessmentV6Result | None
    v7_certification: ForecastAssessmentV7Certification
    settings: dict[str, object]
    aggregate_confidence_score_emitted: bool

    def as_dict(self) -> dict[str, object]:
        return {
            "candidate_name": self.candidate_name,
            "row_count": self.row_count,
            "base_v6_assessment": self.base_v6_assessment.as_dict(),
            "evaluation_access_provenance": (
                None
                if self.evaluation_access_provenance is None
                else self.evaluation_access_provenance.as_dict()
            ),
            "downstream_v6_assessment": (
                None
                if self.downstream_v6_assessment is None
                else self.downstream_v6_assessment.as_dict()
            ),
            "v7_certification": self.v7_certification.as_dict(),
            "settings": dict(self.settings),
            "aggregate_confidence_score_emitted": self.aggregate_confidence_score_emitted,
        }


def _base_v6(
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
    v6_kwargs: Mapping[str, object],
) -> ForecastAssessmentV6Result:
    return assess_state_forecast_v6(
        name,
        conditional_log_density,
        marginal_log_density,
        covered,
        groups,
        blocks,
        region_size=region_size,
        selection_row_ids_by_stage=None,
        refit_schemes=None,
        scheme_nested_draws=scheme_nested_draws,
        scheme_seed=scheme_seed,
        scheme_minimum_refits=scheme_minimum_refits,
        **dict(v6_kwargs),
    )


def _full_v6(
    name: str,
    conditional_log_density: Sequence[float],
    marginal_log_density: Sequence[float],
    covered: Sequence[bool],
    groups: Sequence[object],
    blocks: Sequence[object],
    *,
    region_size: Sequence[float],
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
    v6_kwargs: Mapping[str, object],
) -> ForecastAssessmentV6Result:
    return assess_state_forecast_v6(
        name,
        conditional_log_density,
        marginal_log_density,
        covered,
        groups,
        blocks,
        region_size=region_size,
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
        **dict(v6_kwargs),
    )


def _inherit_summary(
    base: ForecastAssessmentV6Result,
    downstream: ForecastAssessmentV6Result,
    *,
    access_status: str,
) -> ForecastAssessmentV7Certification:
    summary = downstream.v6_certification
    trace = tuple(base.v6_certification.trace) + (
        f"evaluation_access_provenance:{access_status}",
        "downstream_v6:run",
        f"selection_validation_provenance:{summary.selection_validation_provenance_status}",
        f"training_validation_provenance:{summary.training_validation_provenance_status}",
        f"heldout_row_provenance:{summary.heldout_row_provenance_status}",
        f"v7_certification:{summary.certification_status}",
        f"v7_operational:{summary.operational_status}",
    )
    return ForecastAssessmentV7Certification(
        base_validation_status=summary.base_validation_status,
        base_v6_certification_status=base.v6_certification.certification_status,
        base_v6_operational_status=base.v6_certification.operational_status,
        evaluation_access_provenance_status=access_status,
        downstream_v6_status="run",
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


def _access_leakage_summary(
    base: ForecastAssessmentV6Result,
    provenance: EvaluationAccessProvenanceAudit,
) -> ForecastAssessmentV7Certification:
    summary = base.v6_certification
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
            + ("final_evaluation_access_leakage",)
        )
    )
    sentinel = "not_run_final_evaluation_access_leakage"
    trace = tuple(summary.trace) + (
        f"evaluation_access_provenance:{provenance.separation_category}",
        f"downstream_v6:{sentinel}",
        f"selection_validation_provenance:{sentinel}",
        f"training_validation_provenance:{sentinel}",
        f"heldout_row_provenance:{sentinel}",
        f"v7_certification:{certification}",
        f"v7_operational:{operational}",
    )
    return ForecastAssessmentV7Certification(
        base_validation_status=base_validation,
        base_v6_certification_status=base_certification,
        base_v6_operational_status=summary.operational_status,
        evaluation_access_provenance_status=provenance.separation_category,
        downstream_v6_status=sentinel,
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


def assess_state_forecast_v7(
    name: str,
    conditional_log_density: Sequence[float],
    marginal_log_density: Sequence[float],
    covered: Sequence[bool],
    groups: Sequence[object],
    blocks: Sequence[object],
    *,
    region_size: Sequence[float],
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
    **v6_kwargs,
) -> ForecastAssessmentV7Result:
    """Gate ordinary v6 assessment by direct final-evaluation artifact access provenance.

    A caller-declared access ledger is checked before the full v6 path. Direct
    reuse of the declared final-evaluation artifact therefore suppresses the
    downstream selection, training-provenance, held-out-alignment and
    refit-scheme layers rather than being converted into statistical weakness.
    """

    provenance = None
    if accessed_artifact_ids_by_stage is None:
        if final_evaluation_artifact_id is not None:
            raise ValueError(
                "final_evaluation_artifact_id must not be supplied without accessed_artifact_ids_by_stage"
            )
        if expected_evaluation_access_stage_names is not None:
            raise ValueError(
                "expected_evaluation_access_stage_names must not be supplied without accessed_artifact_ids_by_stage"
            )
    else:
        if final_evaluation_artifact_id is None:
            raise ValueError(
                "final_evaluation_artifact_id is required when evaluation-access provenance is supplied"
            )
        provenance = audit_evaluation_access_provenance(
            final_evaluation_artifact_id,
            accessed_artifact_ids_by_stage,
            expected_stage_names=expected_evaluation_access_stage_names,
        )

    base = _base_v6(
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
        v6_kwargs=v6_kwargs,
    )

    downstream = None
    if provenance is None or not provenance.final_evaluation_accessed:
        downstream = _full_v6(
            name,
            conditional_log_density,
            marginal_log_density,
            covered,
            groups,
            blocks,
            region_size=region_size,
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
            v6_kwargs=v6_kwargs,
        )
        summary = _inherit_summary(
            base,
            downstream,
            access_status=(
                "not_audited" if provenance is None else provenance.separation_category
            ),
        )
    else:
        summary = _access_leakage_summary(base, provenance)

    settings = {
        "base_v6_selection_and_scheme_layers_omitted": True,
        "evaluation_access_provenance_audited": provenance is not None,
        "evaluation_access_expected_stage_coverage_checked": (
            False if provenance is None else provenance.expected_stage_coverage_checked
        ),
        "downstream_v6_assessment_run": downstream is not None,
        "scheme_nested_draws": int(scheme_nested_draws),
        "scheme_seed": (
            int(v6_kwargs.get("seed", 20260906)) if scheme_seed is None else int(scheme_seed)
        ),
        "scheme_minimum_refits": (
            int(v6_kwargs.get("minimum_refits", 8))
            if scheme_minimum_refits is None
            else int(scheme_minimum_refits)
        ),
    }
    return ForecastAssessmentV7Result(
        candidate_name=base.candidate_name,
        row_count=base.row_count,
        base_v6_assessment=base,
        evaluation_access_provenance=provenance,
        downstream_v6_assessment=downstream,
        v7_certification=summary,
        settings=settings,
        aggregate_confidence_score_emitted=False,
    )
