"""Forecast Assessment v6: v5 evidence gated by selection provenance."""
from __future__ import annotations

from dataclasses import asdict, dataclass
from typing import Mapping, Sequence

from .forecast_assessment_v5 import ForecastAssessmentV5Result, assess_state_forecast_v5
from .selection_validation_provenance import (
    SelectionValidationProvenanceAudit,
    audit_selection_validation_provenance,
)


@dataclass(frozen=True)
class ForecastAssessmentV6Certification:
    base_validation_status: str
    base_v5_certification_status: str
    base_v5_operational_status: str
    selection_validation_provenance_status: str
    downstream_v5_status: str
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
class ForecastAssessmentV6Result:
    candidate_name: str
    row_count: int
    base_v5_assessment: ForecastAssessmentV5Result
    selection_validation_provenance: SelectionValidationProvenanceAudit | None
    downstream_v5_assessment: ForecastAssessmentV5Result | None
    v6_certification: ForecastAssessmentV6Certification
    settings: dict[str, object]
    aggregate_confidence_score_emitted: bool

    def as_dict(self) -> dict[str, object]:
        return {
            "candidate_name": self.candidate_name,
            "row_count": self.row_count,
            "base_v5_assessment": self.base_v5_assessment.as_dict(),
            "selection_validation_provenance": (
                None
                if self.selection_validation_provenance is None
                else self.selection_validation_provenance.as_dict()
            ),
            "downstream_v5_assessment": (
                None
                if self.downstream_v5_assessment is None
                else self.downstream_v5_assessment.as_dict()
            ),
            "v6_certification": self.v6_certification.as_dict(),
            "settings": dict(self.settings),
            "aggregate_confidence_score_emitted": self.aggregate_confidence_score_emitted,
        }


def _full_v5(
    name: str,
    conditional_log_density: Sequence[float],
    marginal_log_density: Sequence[float],
    covered: Sequence[bool],
    groups: Sequence[object],
    blocks: Sequence[object],
    *,
    region_size: Sequence[float],
    validation_row_ids: Sequence[object] | None,
    refit_schemes: Mapping[str, Sequence[Sequence[float]]] | None,
    validation_row_ids_by_scheme: Mapping[str, Sequence[object]] | None,
    refit_ids_by_scheme: Mapping[str, Sequence[object]] | None,
    reference_refit_ids_by_scheme: Mapping[str, object] | None,
    training_row_ids_by_scheme: Mapping[str, Mapping[object, Sequence[object]]] | None,
    scheme_nested_draws: int,
    scheme_seed: int | None,
    scheme_minimum_refits: int | None,
    v5_kwargs: Mapping[str, object],
) -> ForecastAssessmentV5Result:
    return assess_state_forecast_v5(
        name,
        conditional_log_density,
        marginal_log_density,
        covered,
        groups,
        blocks,
        region_size=region_size,
        validation_row_ids=validation_row_ids,
        refit_schemes=refit_schemes,
        validation_row_ids_by_scheme=validation_row_ids_by_scheme,
        refit_ids_by_scheme=refit_ids_by_scheme,
        reference_refit_ids_by_scheme=reference_refit_ids_by_scheme,
        training_row_ids_by_scheme=training_row_ids_by_scheme,
        scheme_nested_draws=scheme_nested_draws,
        scheme_seed=scheme_seed,
        scheme_minimum_refits=scheme_minimum_refits,
        **dict(v5_kwargs),
    )


def _inherit_summary(
    base: ForecastAssessmentV5Result,
    downstream: ForecastAssessmentV5Result,
    *,
    selection_status: str,
) -> ForecastAssessmentV6Certification:
    summary = downstream.v5_certification
    trace = tuple(base.v5_certification.trace) + (
        f"selection_validation_provenance:{selection_status}",
        "downstream_v5:run",
        f"training_validation_provenance:{summary.training_validation_provenance_status}",
        f"heldout_row_provenance:{summary.heldout_row_provenance_status}",
        f"v6_certification:{summary.certification_status}",
        f"v6_operational:{summary.operational_status}",
    )
    return ForecastAssessmentV6Certification(
        base_validation_status=summary.base_validation_status,
        base_v5_certification_status=base.v5_certification.certification_status,
        base_v5_operational_status=base.v5_certification.operational_status,
        selection_validation_provenance_status=selection_status,
        downstream_v5_status="run",
        training_validation_provenance_status=summary.training_validation_provenance_status,
        heldout_row_provenance_status=summary.heldout_row_provenance_status,
        certification_status=summary.certification_status,
        operational_status=summary.operational_status,
        statistical_blocking_reasons=tuple(summary.statistical_blocking_reasons),
        provenance_blocking_reasons=tuple(summary.provenance_blocking_reasons),
        warning_reasons=tuple(summary.warning_reasons),
        trace=trace,
    )


def _selection_leakage_summary(
    base: ForecastAssessmentV5Result,
    provenance: SelectionValidationProvenanceAudit,
) -> ForecastAssessmentV6Certification:
    summary = base.v5_certification
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
            + ("selection_validation_leakage",)
        )
    )
    trace = tuple(summary.trace) + (
        f"selection_validation_provenance:{provenance.separation_category}",
        "downstream_v5:not_run_selection_validation_leakage",
        "training_validation_provenance:not_run_selection_validation_leakage",
        "heldout_row_provenance:not_run_selection_validation_leakage",
        f"v6_certification:{certification}",
        f"v6_operational:{operational}",
    )
    return ForecastAssessmentV6Certification(
        base_validation_status=base_validation,
        base_v5_certification_status=base_certification,
        base_v5_operational_status=summary.operational_status,
        selection_validation_provenance_status=provenance.separation_category,
        downstream_v5_status="not_run_selection_validation_leakage",
        training_validation_provenance_status="not_run_selection_validation_leakage",
        heldout_row_provenance_status="not_run_selection_validation_leakage",
        certification_status=certification,
        operational_status=operational,
        statistical_blocking_reasons=tuple(summary.statistical_blocking_reasons),
        provenance_blocking_reasons=provenance_reasons,
        warning_reasons=tuple(summary.warning_reasons),
        trace=trace,
    )


def assess_state_forecast_v6(
    name: str,
    conditional_log_density: Sequence[float],
    marginal_log_density: Sequence[float],
    covered: Sequence[bool],
    groups: Sequence[object],
    blocks: Sequence[object],
    *,
    region_size: Sequence[float],
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
    **v5_kwargs,
) -> ForecastAssessmentV6Result:
    """Gate ordinary v5 assessment by direct selection/final-validation provenance.

    One scheme-omitted v5 result is always preserved as base evidence.  When a
    selection ledger is supplied, it is audited before any full v5 training or
    refit-scheme path is allowed to run.  Direct selection/final-validation
    overlap therefore cannot be converted into a weaker statistical result.
    """

    base = assess_state_forecast_v5(
        name,
        conditional_log_density,
        marginal_log_density,
        covered,
        groups,
        blocks,
        region_size=region_size,
        refit_schemes=None,
        scheme_nested_draws=scheme_nested_draws,
        scheme_seed=scheme_seed,
        scheme_minimum_refits=scheme_minimum_refits,
        **v5_kwargs,
    )

    provenance = None
    downstream = None
    if selection_row_ids_by_stage is None:
        if expected_selection_stage_names is not None:
            raise ValueError(
                "expected_selection_stage_names must not be supplied without selection_row_ids_by_stage"
            )
        downstream = _full_v5(
            name,
            conditional_log_density,
            marginal_log_density,
            covered,
            groups,
            blocks,
            region_size=region_size,
            validation_row_ids=validation_row_ids,
            refit_schemes=refit_schemes,
            validation_row_ids_by_scheme=validation_row_ids_by_scheme,
            refit_ids_by_scheme=refit_ids_by_scheme,
            reference_refit_ids_by_scheme=reference_refit_ids_by_scheme,
            training_row_ids_by_scheme=training_row_ids_by_scheme,
            scheme_nested_draws=scheme_nested_draws,
            scheme_seed=scheme_seed,
            scheme_minimum_refits=scheme_minimum_refits,
            v5_kwargs=v5_kwargs,
        )
        summary = _inherit_summary(base, downstream, selection_status="not_audited")
    else:
        if validation_row_ids is None:
            raise ValueError(
                "validation_row_ids are required when selection provenance is supplied"
            )
        provenance = audit_selection_validation_provenance(
            validation_row_ids,
            selection_row_ids_by_stage,
            expected_stage_names=expected_selection_stage_names,
        )
        if provenance.selection_validation_separated:
            downstream = _full_v5(
                name,
                conditional_log_density,
                marginal_log_density,
                covered,
                groups,
                blocks,
                region_size=region_size,
                validation_row_ids=validation_row_ids,
                refit_schemes=refit_schemes,
                validation_row_ids_by_scheme=validation_row_ids_by_scheme,
                refit_ids_by_scheme=refit_ids_by_scheme,
                reference_refit_ids_by_scheme=reference_refit_ids_by_scheme,
                training_row_ids_by_scheme=training_row_ids_by_scheme,
                scheme_nested_draws=scheme_nested_draws,
                scheme_seed=scheme_seed,
                scheme_minimum_refits=scheme_minimum_refits,
                v5_kwargs=v5_kwargs,
            )
            summary = _inherit_summary(
                base,
                downstream,
                selection_status=provenance.separation_category,
            )
        else:
            summary = _selection_leakage_summary(base, provenance)

    settings = {
        "base_v5_scheme_layer_omitted": True,
        "selection_validation_provenance_audited": provenance is not None,
        "selection_expected_stage_coverage_checked": (
            False if provenance is None else provenance.expected_stage_coverage_checked
        ),
        "downstream_v5_assessment_run": downstream is not None,
        "scheme_nested_draws": int(scheme_nested_draws),
        "scheme_seed": (
            int(v5_kwargs.get("seed", 20260906)) if scheme_seed is None else int(scheme_seed)
        ),
        "scheme_minimum_refits": (
            int(v5_kwargs.get("minimum_refits", 8))
            if scheme_minimum_refits is None
            else int(scheme_minimum_refits)
        ),
    }
    return ForecastAssessmentV6Result(
        candidate_name=base.candidate_name,
        row_count=base.row_count,
        base_v5_assessment=base,
        selection_validation_provenance=provenance,
        downstream_v5_assessment=downstream,
        v6_certification=summary,
        settings=settings,
        aggregate_confidence_score_emitted=False,
    )
