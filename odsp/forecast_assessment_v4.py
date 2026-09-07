"""Forecast Assessment v4: v3 evidence plus machine-checked row provenance."""
from __future__ import annotations

from dataclasses import asdict, dataclass
from typing import Mapping, Sequence

from .aligned_refit_scheme_sensitivity import (
    AlignedRefitSchemeSensitivityAudit,
    audit_aligned_refit_scheme_sensitivity,
)
from .forecast_assessment_v3 import (
    ForecastAssessmentV3Certification,
    ForecastAssessmentV3Result,
    _v3_summary,
    assess_state_forecast_v3,
)


@dataclass(frozen=True)
class ForecastAssessmentV4Certification:
    base_validation_status: str
    base_v3_certification_status: str
    base_v3_operational_status: str
    row_provenance_status: str
    aligned_scheme_audit_status: str
    aligned_scheme_category: str
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
class ForecastAssessmentV4Result:
    candidate_name: str
    row_count: int
    base_v3_assessment: ForecastAssessmentV3Result
    aligned_refit_scheme_audit: AlignedRefitSchemeSensitivityAudit | None
    aligned_v3_certification: ForecastAssessmentV3Certification | None
    v4_certification: ForecastAssessmentV4Certification
    settings: dict[str, object]
    aggregate_confidence_score_emitted: bool

    def as_dict(self) -> dict[str, object]:
        return {
            "candidate_name": self.candidate_name,
            "row_count": self.row_count,
            "base_v3_assessment": self.base_v3_assessment.as_dict(),
            "aligned_refit_scheme_audit": (
                None
                if self.aligned_refit_scheme_audit is None
                else self.aligned_refit_scheme_audit.as_dict()
            ),
            "aligned_v3_certification": (
                None
                if self.aligned_v3_certification is None
                else self.aligned_v3_certification.as_dict()
            ),
            "v4_certification": self.v4_certification.as_dict(),
            "settings": dict(self.settings),
            "aggregate_confidence_score_emitted": self.aggregate_confidence_score_emitted,
        }


def _copy_v3_summary(
    base: ForecastAssessmentV3Result,
    summary: ForecastAssessmentV3Certification,
    *,
    row_provenance_status: str,
    aligned_scheme_audit_status: str,
    aligned_scheme_category: str,
) -> ForecastAssessmentV4Certification:
    trace = tuple(summary.trace) + (
        f"row_provenance:{row_provenance_status}",
        f"aligned_scheme_audit:{aligned_scheme_audit_status}",
        f"v4_certification:{summary.certification_status}",
        f"v4_operational:{summary.operational_status}",
    )
    return ForecastAssessmentV4Certification(
        base_validation_status=summary.base_validation_status,
        base_v3_certification_status=base.v3_certification.certification_status,
        base_v3_operational_status=base.v3_certification.operational_status,
        row_provenance_status=row_provenance_status,
        aligned_scheme_audit_status=aligned_scheme_audit_status,
        aligned_scheme_category=aligned_scheme_category,
        certification_status=summary.certification_status,
        operational_status=summary.operational_status,
        statistical_blocking_reasons=tuple(summary.extended_blocking_reasons),
        provenance_blocking_reasons=(),
        warning_reasons=tuple(summary.warning_reasons),
        trace=trace,
    )


def _mismatch_summary(
    base: ForecastAssessmentV3Result,
    aligned: AlignedRefitSchemeSensitivityAudit,
) -> ForecastAssessmentV4Certification:
    base_summary = base.v3_certification
    base_validation = base_summary.base_validation_status
    base_certification = base_summary.certification_status

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

    trace = tuple(base_summary.trace) + (
        "row_provenance:row_mismatch",
        f"aligned_scheme_audit:{aligned.status}",
        f"v4_certification:{certification}",
        f"v4_operational:{operational}",
    )
    return ForecastAssessmentV4Certification(
        base_validation_status=base_validation,
        base_v3_certification_status=base_certification,
        base_v3_operational_status=base_summary.operational_status,
        row_provenance_status="row_mismatch",
        aligned_scheme_audit_status=aligned.status,
        aligned_scheme_category=aligned.scheme_sensitivity_category,
        certification_status=certification,
        operational_status=operational,
        statistical_blocking_reasons=tuple(base_summary.extended_blocking_reasons),
        provenance_blocking_reasons=("heldout_row_mismatch",),
        warning_reasons=tuple(base_summary.warning_reasons),
        trace=trace,
    )


def assess_state_forecast_v4(
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
    scheme_nested_draws: int = 1200,
    scheme_seed: int | None = None,
    scheme_minimum_refits: int | None = None,
    **v3_kwargs,
) -> ForecastAssessmentV4Result:
    """Run v3 base evidence, then optionally add provenance-aware scheme evidence.

    The complete base v3 assessment is always computed with its scheme layer
    omitted and preserved unchanged. If schemes are requested, unique validation
    row IDs are required for the base target and every scheme. Only a successful
    row-key alignment permits the existing refit-scheme statistical audit to run.
    """

    base = assess_state_forecast_v3(
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
        **v3_kwargs,
    )

    aligned = None
    aligned_v3 = None
    if refit_schemes is not None:
        if validation_row_ids is None:
            raise ValueError("validation_row_ids are required when refit_schemes are supplied")
        if validation_row_ids_by_scheme is None:
            raise ValueError(
                "validation_row_ids_by_scheme is required when refit_schemes are supplied"
            )
        base_weight = v3_kwargs.get("base_weight")
        confidence_level = float(v3_kwargs.get("confidence_level", 0.95))
        minimum_blocks = int(v3_kwargs.get("minimum_blocks_per_group", 8))
        gain_tolerance = float(v3_kwargs.get("gain_tolerance", 0.0))
        seed = int(v3_kwargs.get("seed", 20260906)) if scheme_seed is None else int(scheme_seed)
        minimum_refits = (
            int(v3_kwargs.get("minimum_refits", 8))
            if scheme_minimum_refits is None
            else int(scheme_minimum_refits)
        )
        aligned = audit_aligned_refit_scheme_sensitivity(
            refit_schemes,
            groups,
            blocks=blocks,
            validation_row_ids=validation_row_ids,
            validation_row_ids_by_scheme=validation_row_ids_by_scheme,
            sample_weight=base_weight,
            refit_ids_by_scheme=refit_ids_by_scheme,
            reference_refit_ids_by_scheme=reference_refit_ids_by_scheme,
            familywise_confidence_level=confidence_level,
            nested_draws=scheme_nested_draws,
            seed=seed,
            minimum_refits=minimum_refits,
            minimum_blocks_per_group=minimum_blocks,
            gain_tolerance=gain_tolerance,
        )
        if aligned.statistical_audit_run:
            if aligned.scheme_audit is None:
                raise RuntimeError("a successful aligned scheme audit must expose statistical evidence")
            aligned_v3 = _v3_summary(base.base_v2_assessment, aligned.scheme_audit)

    if aligned is None:
        v4_summary = _copy_v3_summary(
            base,
            base.v3_certification,
            row_provenance_status="not_audited",
            aligned_scheme_audit_status="not_audited",
            aligned_scheme_category="not_audited",
        )
    elif not aligned.statistical_audit_run:
        v4_summary = _mismatch_summary(base, aligned)
    else:
        if aligned_v3 is None:
            raise RuntimeError("aligned v3 certification is missing after a successful audit")
        v4_summary = _copy_v3_summary(
            base,
            aligned_v3,
            row_provenance_status=aligned.row_alignment.alignment_category,
            aligned_scheme_audit_status=aligned.status,
            aligned_scheme_category=aligned.scheme_sensitivity_category,
        )

    settings = {
        "base_v3_scheme_layer_omitted": True,
        "row_provenance_audited": aligned is not None,
        "scheme_nested_draws": int(scheme_nested_draws),
        "scheme_seed": (
            int(v3_kwargs.get("seed", 20260906)) if scheme_seed is None else int(scheme_seed)
        ),
        "scheme_minimum_refits": (
            int(v3_kwargs.get("minimum_refits", 8))
            if scheme_minimum_refits is None
            else int(scheme_minimum_refits)
        ),
    }
    return ForecastAssessmentV4Result(
        candidate_name=base.candidate_name,
        row_count=base.row_count,
        base_v3_assessment=base,
        aligned_refit_scheme_audit=aligned,
        aligned_v3_certification=aligned_v3,
        v4_certification=v4_summary,
        settings=settings,
        aggregate_confidence_score_emitted=False,
    )
