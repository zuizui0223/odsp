"""Forecast Assessment v3: v2 evidence plus refit-scheme certification.

V3 preserves the complete Forecast Assessment v2 result and optionally adds the
validated refit-scheme sensitivity layer on the same held-out target.  The scheme
layer is a formal extended-certification gate but never rewrites v1/v2 validation
history, block-definition warnings, or deployment-novelty warnings.
"""
from __future__ import annotations

from dataclasses import asdict, dataclass
from typing import Mapping, Sequence

from .forecast_assessment_v2 import ForecastAssessmentV2Result, assess_state_forecast_v2
from .refit_scheme_sensitivity import (
    RefitSchemeSensitivityAudit,
    audit_refit_scheme_sensitivity,
)


@dataclass(frozen=True)
class ForecastAssessmentV3Certification:
    base_validation_status: str
    v2_certification_status: str
    v2_operational_status: str
    refit_scheme_status: str
    refit_scheme_category: str
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
class ForecastAssessmentV3Result:
    candidate_name: str
    row_count: int
    base_v2_assessment: ForecastAssessmentV2Result
    refit_scheme_audit: RefitSchemeSensitivityAudit | None
    v3_certification: ForecastAssessmentV3Certification
    settings: dict[str, object]
    aggregate_confidence_score_emitted: bool

    def as_dict(self) -> dict[str, object]:
        return {
            "candidate_name": self.candidate_name,
            "row_count": self.row_count,
            "base_v2_assessment": self.base_v2_assessment.as_dict(),
            "refit_scheme_audit": (
                None if self.refit_scheme_audit is None else self.refit_scheme_audit.as_dict()
            ),
            "v3_certification": self.v3_certification.as_dict(),
            "settings": dict(self.settings),
            "aggregate_confidence_score_emitted": self.aggregate_confidence_score_emitted,
        }


def _scheme_status(category: str | None, *, audited: bool) -> str:
    if not audited:
        return "not_audited"
    if category == "scheme_robust_generalizing":
        return "pass"
    if category == "unavailable":
        return "unavailable"
    if category == "scheme_sensitive":
        return "sensitive"
    if category in {"stable_uncertain", "uncertain"}:
        return "uncertain"
    if category in {"scheme_robust_non_generalizing", "stable_mixed", "mixed"}:
        return "fail"
    if category is not None and category.startswith("stable_"):
        return "fail"
    return "fail"


def _v3_summary(
    base: ForecastAssessmentV2Result,
    scheme: RefitSchemeSensitivityAudit | None,
) -> ForecastAssessmentV3Certification:
    v2 = base.extended_certification
    base_validation = v2.base_validation_status
    v2_certification = v2.certification_status
    v2_operational = v2.operational_status
    scheme_category = "not_audited" if scheme is None else scheme.sensitivity_category
    scheme_status = _scheme_status(
        None if scheme is None else scheme.sensitivity_category,
        audited=scheme is not None,
    )

    blockers = list(v2.extended_blocking_reasons)
    if scheme_status == "sensitive":
        blockers.append("refit_scheme_sensitive")
    elif scheme_status == "unavailable":
        blockers.append("refit_scheme_unavailable")
    elif scheme_status == "uncertain":
        blockers.append("refit_scheme_uncertain")
    elif scheme_status == "fail":
        blockers.append("refit_scheme_nonpositive_or_mixed")

    if base_validation == "unavailable":
        certification = "unavailable"
    elif base_validation == "blocked":
        certification = "not_certified"
    elif v2_certification == "not_certified":
        certification = "not_certified"
    elif v2_certification == "unavailable":
        certification = "unavailable"
    elif scheme_status in {"sensitive", "uncertain", "fail"}:
        certification = "not_certified"
    elif scheme_status == "unavailable":
        certification = "unavailable"
    elif scheme_status == "pass":
        certification = (
            "certified" if v2_certification in {"certified", "not_audited"}
            else v2_certification
        )
    else:  # scheme omitted
        certification = v2_certification

    warnings = tuple(v2.warning_reasons)
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
        operational = v2_operational

    trace = tuple(v2.trace) + (
        f"refit_scheme:{scheme_category}",
        f"v3_certification:{certification}",
        f"v3_operational:{operational}",
    )
    return ForecastAssessmentV3Certification(
        base_validation_status=base_validation,
        v2_certification_status=v2_certification,
        v2_operational_status=v2_operational,
        refit_scheme_status=scheme_status,
        refit_scheme_category=scheme_category,
        certification_status=certification,
        operational_status=operational,
        extended_blocking_reasons=tuple(dict.fromkeys(blockers)),
        warning_reasons=warnings,
        trace=trace,
    )


def assess_state_forecast_v3(
    name: str,
    conditional_log_density: Sequence[float],
    marginal_log_density: Sequence[float],
    covered: Sequence[bool],
    groups: Sequence[object],
    blocks: Sequence[object],
    *,
    region_size: Sequence[float],
    refit_schemes: Mapping[str, Sequence[Sequence[float]]] | None = None,
    refit_ids_by_scheme: Mapping[str, Sequence[object]] | None = None,
    reference_refit_ids_by_scheme: Mapping[str, object] | None = None,
    scheme_nested_draws: int = 1200,
    scheme_seed: int | None = None,
    scheme_minimum_refits: int | None = None,
    **v2_kwargs,
) -> ForecastAssessmentV3Result:
    """Run Forecast Assessment v2 and optionally add refit-scheme certification.

    All refit-scheme gain matrices must refer to the same untouched validation rows
    as the base assessment.  Numeric matrices cannot prove row identity; that
    scientific provenance remains caller-declared.  The same group labels, block
    labels and base weights are passed to every scheme audit.
    """

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

    scheme_audit = None
    if refit_schemes is not None:
        if not refit_schemes:
            raise ValueError("refit_schemes must contain at least two named schemes when supplied")
        base_weight = v2_kwargs.get("base_weight")
        confidence_level = float(v2_kwargs.get("confidence_level", 0.95))
        minimum_blocks = int(v2_kwargs.get("minimum_blocks_per_group", 8))
        gain_tolerance = float(v2_kwargs.get("gain_tolerance", 0.0))
        seed = int(v2_kwargs.get("seed", 20260906)) if scheme_seed is None else int(scheme_seed)
        minimum_refits = (
            int(v2_kwargs.get("minimum_refits", 8))
            if scheme_minimum_refits is None
            else int(scheme_minimum_refits)
        )
        scheme_audit = audit_refit_scheme_sensitivity(
            refit_schemes,
            groups,
            blocks=blocks,
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

    summary = _v3_summary(base, scheme_audit)
    settings = {
        "refit_scheme_sensitivity_audited": scheme_audit is not None,
        "scheme_nested_draws": int(scheme_nested_draws),
        "scheme_seed": (
            int(v2_kwargs.get("seed", 20260906)) if scheme_seed is None else int(scheme_seed)
        ),
        "scheme_minimum_refits": (
            int(v2_kwargs.get("minimum_refits", 8))
            if scheme_minimum_refits is None
            else int(scheme_minimum_refits)
        ),
    }
    return ForecastAssessmentV3Result(
        candidate_name=base.candidate_name,
        row_count=base.row_count,
        base_v2_assessment=base,
        refit_scheme_audit=scheme_audit,
        v3_certification=summary,
        settings=settings,
        aggregate_confidence_score_emitted=False,
    )
