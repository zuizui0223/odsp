"""Forecast Assessment v5: v4 evidence gated by refit training provenance."""
from __future__ import annotations

from dataclasses import asdict, dataclass
from typing import Mapping, Sequence

from .forecast_assessment_v4 import ForecastAssessmentV4Result, assess_state_forecast_v4
from .refit_training_validation_provenance import (
    RefitTrainingValidationProvenanceAudit,
    audit_refit_training_validation_provenance,
)


@dataclass(frozen=True)
class ForecastAssessmentV5Certification:
    base_validation_status: str
    base_v4_certification_status: str
    base_v4_operational_status: str
    training_validation_provenance_status: str
    downstream_v4_scheme_status: str
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
class ForecastAssessmentV5Result:
    candidate_name: str
    row_count: int
    base_v4_assessment: ForecastAssessmentV4Result
    training_validation_provenance: RefitTrainingValidationProvenanceAudit | None
    provenance_qualified_v4_assessment: ForecastAssessmentV4Result | None
    v5_certification: ForecastAssessmentV5Certification
    settings: dict[str, object]
    aggregate_confidence_score_emitted: bool

    def as_dict(self) -> dict[str, object]:
        return {
            "candidate_name": self.candidate_name,
            "row_count": self.row_count,
            "base_v4_assessment": self.base_v4_assessment.as_dict(),
            "training_validation_provenance": (
                None
                if self.training_validation_provenance is None
                else self.training_validation_provenance.as_dict()
            ),
            "provenance_qualified_v4_assessment": (
                None
                if self.provenance_qualified_v4_assessment is None
                else self.provenance_qualified_v4_assessment.as_dict()
            ),
            "v5_certification": self.v5_certification.as_dict(),
            "settings": dict(self.settings),
            "aggregate_confidence_score_emitted": self.aggregate_confidence_score_emitted,
        }


def _canonical_scheme_names(mapping: Mapping[object, object], *, label: str) -> tuple[str, ...]:
    names = tuple(str(value).strip() for value in mapping)
    if any(not value for value in names):
        raise ValueError(f"{label} scheme names must be non-empty")
    if len(set(names)) != len(names):
        raise ValueError(f"{label} scheme names must be unique after canonicalization")
    return tuple(sorted(names))


def _copy_summary(
    base: ForecastAssessmentV4Result,
    qualified: ForecastAssessmentV4Result,
    provenance: RefitTrainingValidationProvenanceAudit,
) -> ForecastAssessmentV5Certification:
    summary = qualified.v4_certification
    trace = tuple(base.v4_certification.trace) + (
        f"training_validation_provenance:{provenance.separation_category}",
        f"downstream_v4_scheme:{summary.aligned_scheme_audit_status}",
        f"heldout_row_provenance:{summary.row_provenance_status}",
        f"v5_certification:{summary.certification_status}",
        f"v5_operational:{summary.operational_status}",
    )
    return ForecastAssessmentV5Certification(
        base_validation_status=summary.base_validation_status,
        base_v4_certification_status=base.v4_certification.certification_status,
        base_v4_operational_status=base.v4_certification.operational_status,
        training_validation_provenance_status=provenance.separation_category,
        downstream_v4_scheme_status=summary.aligned_scheme_audit_status,
        heldout_row_provenance_status=summary.row_provenance_status,
        certification_status=summary.certification_status,
        operational_status=summary.operational_status,
        statistical_blocking_reasons=tuple(summary.statistical_blocking_reasons),
        provenance_blocking_reasons=tuple(summary.provenance_blocking_reasons),
        warning_reasons=tuple(summary.warning_reasons),
        trace=trace,
    )


def _omitted_summary(base: ForecastAssessmentV4Result) -> ForecastAssessmentV5Certification:
    summary = base.v4_certification
    trace = tuple(summary.trace) + (
        "training_validation_provenance:not_audited",
        "downstream_v4_scheme:not_audited",
        f"v5_certification:{summary.certification_status}",
        f"v5_operational:{summary.operational_status}",
    )
    return ForecastAssessmentV5Certification(
        base_validation_status=summary.base_validation_status,
        base_v4_certification_status=summary.certification_status,
        base_v4_operational_status=summary.operational_status,
        training_validation_provenance_status="not_audited",
        downstream_v4_scheme_status="not_audited",
        heldout_row_provenance_status=summary.row_provenance_status,
        certification_status=summary.certification_status,
        operational_status=summary.operational_status,
        statistical_blocking_reasons=tuple(summary.statistical_blocking_reasons),
        provenance_blocking_reasons=tuple(summary.provenance_blocking_reasons),
        warning_reasons=tuple(summary.warning_reasons),
        trace=trace,
    )


def _leakage_summary(
    base: ForecastAssessmentV4Result,
    provenance: RefitTrainingValidationProvenanceAudit,
) -> ForecastAssessmentV5Certification:
    summary = base.v4_certification
    base_validation = summary.base_validation_status
    base_certification = summary.certification_status

    if base_validation == "unavailable":
        certification = "unavailable"
    elif base_validation == "blocked":
        certification = "not_certified"
    elif base_certification == "not_certified":
        certification = "not_certified"
    elif base_certification == "unavailable":
        certification = "unavailable"
    else:
        certification = "unavailable"

    if base_validation == "unavailable":
        operational = "unavailable"
    elif base_validation == "blocked":
        operational = "blocked"
    elif certification == "not_certified":
        operational = "admitted_extended_not_certified"
    else:
        operational = "admitted_extended_unavailable"

    provenance_reasons = tuple(
        dict.fromkeys(tuple(summary.provenance_blocking_reasons) + ("training_validation_leakage",))
    )
    trace = tuple(summary.trace) + (
        f"training_validation_provenance:{provenance.separation_category}",
        "downstream_v4_scheme:not_run_training_validation_leakage",
        "heldout_row_provenance:not_run_training_validation_leakage",
        f"v5_certification:{certification}",
        f"v5_operational:{operational}",
    )
    return ForecastAssessmentV5Certification(
        base_validation_status=base_validation,
        base_v4_certification_status=base_certification,
        base_v4_operational_status=summary.operational_status,
        training_validation_provenance_status=provenance.separation_category,
        downstream_v4_scheme_status="not_run_training_validation_leakage",
        heldout_row_provenance_status="not_run_training_validation_leakage",
        certification_status=certification,
        operational_status=operational,
        statistical_blocking_reasons=tuple(summary.statistical_blocking_reasons),
        provenance_blocking_reasons=provenance_reasons,
        warning_reasons=tuple(summary.warning_reasons),
        trace=trace,
    )


def assess_state_forecast_v5(
    name: str,
    conditional_log_density: Sequence[float],
    marginal_log_density: Sequence[float],
    covered: Sequence[bool],
    groups: Sequence[object],
    blocks: Sequence[object],
    *,
    region_size: Sequence[float],
    validation_row_ids: Sequence[object] | None = None,
    refit_schemes: Mapping[str, Sequence[Sequence[float]]] | None = None,
    validation_row_ids_by_scheme: Mapping[str, Sequence[object]] | None = None,
    refit_ids_by_scheme: Mapping[str, Sequence[object]] | None = None,
    reference_refit_ids_by_scheme: Mapping[str, object] | None = None,
    training_row_ids_by_scheme: Mapping[str, Mapping[object, Sequence[object]]] | None = None,
    scheme_nested_draws: int = 1200,
    scheme_seed: int | None = None,
    scheme_minimum_refits: int | None = None,
    **v4_kwargs,
) -> ForecastAssessmentV5Result:
    """Run v4 base evidence, then gate any scheme statistics by training provenance."""

    base = assess_state_forecast_v4(
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
        **v4_kwargs,
    )

    provenance = None
    qualified = None
    if refit_schemes is None:
        if any(
            value is not None
            for value in (
                training_row_ids_by_scheme,
                validation_row_ids_by_scheme,
                refit_ids_by_scheme,
                reference_refit_ids_by_scheme,
            )
        ):
            raise ValueError("scheme provenance metadata must not be supplied without refit_schemes")
        summary = _omitted_summary(base)
    else:
        if validation_row_ids is None:
            raise ValueError("validation_row_ids are required when refit_schemes are supplied")
        if validation_row_ids_by_scheme is None:
            raise ValueError("validation_row_ids_by_scheme is required when refit_schemes are supplied")
        if refit_ids_by_scheme is None:
            raise ValueError("explicit refit_ids_by_scheme are required for training provenance")
        if training_row_ids_by_scheme is None:
            raise ValueError("training_row_ids_by_scheme is required when refit_schemes are supplied")

        scheme_names = _canonical_scheme_names(refit_schemes, label="refit_schemes")
        refit_scheme_names = _canonical_scheme_names(refit_ids_by_scheme, label="refit_ids_by_scheme")
        if scheme_names != refit_scheme_names:
            raise ValueError("refit_ids_by_scheme must cover every and only declared refit scheme")

        provenance = audit_refit_training_validation_provenance(
            validation_row_ids,
            training_row_ids_by_scheme,
            expected_refit_ids_by_scheme=refit_ids_by_scheme,
        )
        if provenance.training_validation_separated:
            qualified = assess_state_forecast_v4(
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
                scheme_nested_draws=scheme_nested_draws,
                scheme_seed=scheme_seed,
                scheme_minimum_refits=scheme_minimum_refits,
                **v4_kwargs,
            )
            summary = _copy_summary(base, qualified, provenance)
        else:
            summary = _leakage_summary(base, provenance)

    settings = {
        "base_v4_scheme_layer_omitted": True,
        "training_validation_provenance_audited": provenance is not None,
        "downstream_v4_scheme_assessment_run": qualified is not None,
        "scheme_nested_draws": int(scheme_nested_draws),
        "scheme_seed": (
            int(v4_kwargs.get("seed", 20260906)) if scheme_seed is None else int(scheme_seed)
        ),
        "scheme_minimum_refits": (
            int(v4_kwargs.get("minimum_refits", 8))
            if scheme_minimum_refits is None
            else int(scheme_minimum_refits)
        ),
    }
    return ForecastAssessmentV5Result(
        candidate_name=base.candidate_name,
        row_count=base.row_count,
        base_v4_assessment=base,
        training_validation_provenance=provenance,
        provenance_qualified_v4_assessment=qualified,
        v5_certification=summary,
        settings=settings,
        aggregate_confidence_score_emitted=False,
    )
