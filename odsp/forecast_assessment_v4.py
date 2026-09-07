"""Forecast Assessment v4: v3 certification with machine-checked row provenance."""
from __future__ import annotations

from dataclasses import asdict, dataclass
from typing import Mapping, Sequence

from .aligned_refit_scheme_sensitivity import (
    AlignedRefitSchemeSensitivityAudit,
    audit_aligned_refit_scheme_sensitivity,
)
from .forecast_assessment_v2 import ForecastAssessmentV2Result, assess_state_forecast_v2
from .forecast_assessment_v3 import (
    ForecastAssessmentV3Result,
    _v3_summary,
)


@dataclass(frozen=True)
class ForecastAssessmentV4Certification:
    base_validation_status: str
    v2_certification_status: str
    row_provenance_status: str
    v3_assessment_status: str
    v3_certification_status: str
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
class ForecastAssessmentV4Result:
    candidate_name: str
    row_count: int
    base_v2_assessment: ForecastAssessmentV2Result
    aligned_refit_scheme_audit: AlignedRefitSchemeSensitivityAudit | None
    v3_assessment: ForecastAssessmentV3Result | None
    v4_certification: ForecastAssessmentV4Certification
    settings: dict[str, object]
    aggregate_confidence_score_emitted: bool

    def as_dict(self) -> dict[str, object]:
        return {
            "candidate_name": self.candidate_name,
            "row_count": self.row_count,
            "base_v2_assessment": self.base_v2_assessment.as_dict(),
            "aligned_refit_scheme_audit": (
                None
                if self.aligned_refit_scheme_audit is None
                else self.aligned_refit_scheme_audit.as_dict()
            ),
            "v3_assessment": None if self.v3_assessment is None else self.v3_assessment.as_dict(),
            "v4_certification": self.v4_certification.as_dict(),
            "settings": dict(self.settings),
            "aggregate_confidence_score_emitted": self.aggregate_confidence_score_emitted,
        }


def _v3_settings(
    v2_kwargs: Mapping[str, object],
    *,
    scheme_nested_draws: int,
    scheme_seed: int | None,
    scheme_minimum_refits: int | None,
    audited: bool,
) -> dict[str, object]:
    resolved_seed = (
        int(v2_kwargs.get("seed", 20260906)) if scheme_seed is None else int(scheme_seed)
    )
    resolved_minimum_refits = (
        int(v2_kwargs.get("minimum_refits", 8))
        if scheme_minimum_refits is None
        else int(scheme_minimum_refits)
    )
    return {
        "refit_scheme_sensitivity_audited": audited,
        "scheme_nested_draws": int(scheme_nested_draws),
        "scheme_seed": resolved_seed,
        "scheme_minimum_refits": resolved_minimum_refits,
    }


def _compose_v3(
    base: ForecastAssessmentV2Result,
    scheme_audit,
    *,
    settings: dict[str, object],
) -> ForecastAssessmentV3Result:
    return ForecastAssessmentV3Result(
        candidate_name=base.candidate_name,
        row_count=base.row_count,
        base_v2_assessment=base,
        refit_scheme_audit=scheme_audit,
        v3_certification=_v3_summary(base, scheme_audit),
        settings=settings,
        aggregate_confidence_score_emitted=False,
    )


def _v4_summary(
    base: ForecastAssessmentV2Result,
    aligned: AlignedRefitSchemeSensitivityAudit | None,
    v3: ForecastAssessmentV3Result | None,
    *,
    scheme_declared: bool,
) -> ForecastAssessmentV4Certification:
    v2 = base.extended_certification

    if v3 is not None:
        v3_cert = v3.v3_certification
        provenance = (
            "not_required"
            if not scheme_declared
            else aligned.row_alignment.alignment_category
        )
        trace = tuple(v3_cert.trace) + (
            f"row_provenance:{provenance}",
            f"v4_certification:{v3_cert.certification_status}",
            f"v4_operational:{v3_cert.operational_status}",
        )
        return ForecastAssessmentV4Certification(
            base_validation_status=v3_cert.base_validation_status,
            v2_certification_status=v3_cert.v2_certification_status,
            row_provenance_status=provenance,
            v3_assessment_status="completed",
            v3_certification_status=v3_cert.certification_status,
            certification_status=v3_cert.certification_status,
            operational_status=v3_cert.operational_status,
            extended_blocking_reasons=v3_cert.extended_blocking_reasons,
            warning_reasons=v3_cert.warning_reasons,
            trace=trace,
        )

    if aligned is None or aligned.row_alignment.alignment_passed:
        raise RuntimeError("missing v3 assessment is only valid after a row provenance mismatch")

    blockers = list(v2.extended_blocking_reasons)
    blockers.append("heldout_row_mismatch")
    base_validation = v2.base_validation_status
    v2_certification = v2.certification_status

    if base_validation == "unavailable":
        certification = "unavailable"
        operational = "unavailable"
    elif base_validation == "blocked":
        certification = "not_certified"
        operational = "blocked"
    elif v2_certification == "not_certified":
        certification = "not_certified"
        operational = "admitted_extended_not_certified"
    elif v2_certification == "unavailable":
        certification = "unavailable"
        operational = "admitted_extended_unavailable"
    else:
        certification = "unavailable"
        operational = "admitted_extended_unavailable"

    warnings = tuple(v2.warning_reasons)
    trace = tuple(v2.trace) + (
        "row_provenance:row_mismatch",
        "v3_assessment:withheld_row_mismatch",
        f"v4_certification:{certification}",
        f"v4_operational:{operational}",
    )
    return ForecastAssessmentV4Certification(
        base_validation_status=base_validation,
        v2_certification_status=v2_certification,
        row_provenance_status="row_mismatch",
        v3_assessment_status="withheld_row_mismatch",
        v3_certification_status="not_run_row_mismatch",
        certification_status=certification,
        operational_status=operational,
        extended_blocking_reasons=tuple(dict.fromkeys(blockers)),
        warning_reasons=warnings,
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
    refit_schemes: Mapping[str, Sequence[Sequence[float]]] | None = None,
    validation_row_ids: Sequence[object] | None = None,
    validation_row_ids_by_scheme: Mapping[str, Sequence[object]] | None = None,
    refit_ids_by_scheme: Mapping[str, Sequence[object]] | None = None,
    reference_refit_ids_by_scheme: Mapping[str, object] | None = None,
    scheme_nested_draws: int = 1200,
    scheme_seed: int | None = None,
    scheme_minimum_refits: int | None = None,
    **v2_kwargs,
) -> ForecastAssessmentV4Result:
    """Run one-call Forecast Assessment with optional row-provenance scheme gating."""

    scheme_declared = refit_schemes is not None
    if not scheme_declared:
        if validation_row_ids_by_scheme is not None:
            raise ValueError("validation_row_ids_by_scheme requires refit_schemes")
    else:
        if not refit_schemes:
            raise ValueError("refit_schemes must contain at least two named schemes when supplied")
        if validation_row_ids is None or validation_row_ids_by_scheme is None:
            raise ValueError(
                "declared refit_schemes require validation_row_ids and validation_row_ids_by_scheme"
            )

    base = assess_state_forecast_v2(
        name,
        conditional_log_density,
        marginal_log_density,
        covered,
        groups,
        blocks,
        region_size=region_size,
        **v2_kwargs,
    )

    resolved_settings = _v3_settings(
        v2_kwargs,
        scheme_nested_draws=scheme_nested_draws,
        scheme_seed=scheme_seed,
        scheme_minimum_refits=scheme_minimum_refits,
        audited=scheme_declared,
    )

    aligned = None
    v3 = None
    if not scheme_declared:
        v3 = _compose_v3(base, None, settings=resolved_settings)
    else:
        confidence_level = float(v2_kwargs.get("confidence_level", 0.95))
        minimum_blocks = int(v2_kwargs.get("minimum_blocks_per_group", 8))
        gain_tolerance = float(v2_kwargs.get("gain_tolerance", 0.0))
        resolved_seed = int(resolved_settings["scheme_seed"])
        resolved_minimum_refits = int(resolved_settings["scheme_minimum_refits"])
        aligned = audit_aligned_refit_scheme_sensitivity(
            refit_schemes,
            groups,
            blocks=blocks,
            validation_row_ids=validation_row_ids,
            validation_row_ids_by_scheme=validation_row_ids_by_scheme,
            sample_weight=v2_kwargs.get("base_weight"),
            refit_ids_by_scheme=refit_ids_by_scheme,
            reference_refit_ids_by_scheme=reference_refit_ids_by_scheme,
            familywise_confidence_level=confidence_level,
            nested_draws=scheme_nested_draws,
            seed=resolved_seed,
            minimum_refits=resolved_minimum_refits,
            minimum_blocks_per_group=minimum_blocks,
            gain_tolerance=gain_tolerance,
        )
        if aligned.statistical_audit_run:
            v3 = _compose_v3(base, aligned.scheme_audit, settings=resolved_settings)

    summary = _v4_summary(base, aligned, v3, scheme_declared=scheme_declared)
    settings = dict(resolved_settings)
    settings.update(
        {
            "row_provenance_required": bool(scheme_declared),
            "row_provenance_status": summary.row_provenance_status,
            "scheme_aware_v3_assessment_completed": v3 is not None,
        }
    )
    return ForecastAssessmentV4Result(
        candidate_name=base.candidate_name,
        row_count=base.row_count,
        base_v2_assessment=base,
        aligned_refit_scheme_audit=aligned,
        v3_assessment=v3,
        v4_certification=summary,
        settings=settings,
        aggregate_confidence_score_emitted=False,
    )
