"""Forecast Assessment v9: v8 evidence gated by evaluation-ledger binding."""
from __future__ import annotations

from dataclasses import asdict, dataclass
from typing import Mapping, Sequence

from .evaluation_ledger_binding import (
    EvaluationLedgerBindingAudit,
    audit_evaluation_ledger_binding,
)
from .forecast_assessment_v8 import ForecastAssessmentV8Result, assess_state_forecast_v8


@dataclass(frozen=True)
class ForecastAssessmentV9Certification:
    base_validation_status: str
    base_v8_certification_status: str
    base_v8_operational_status: str
    evaluation_ledger_binding_status: str
    downstream_v8_status: str
    evaluation_content_provenance_status: str
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
class ForecastAssessmentV9Result:
    candidate_name: str
    row_count: int
    base_v8_assessment: ForecastAssessmentV8Result
    evaluation_ledger_binding: EvaluationLedgerBindingAudit | None
    downstream_v8_assessment: ForecastAssessmentV8Result | None
    v9_certification: ForecastAssessmentV9Certification
    settings: dict[str, object]
    aggregate_confidence_score_emitted: bool

    def as_dict(self) -> dict[str, object]:
        return {
            "candidate_name": self.candidate_name,
            "row_count": self.row_count,
            "base_v8_assessment": self.base_v8_assessment.as_dict(),
            "evaluation_ledger_binding": (
                None
                if self.evaluation_ledger_binding is None
                else self.evaluation_ledger_binding.as_dict()
            ),
            "downstream_v8_assessment": (
                None
                if self.downstream_v8_assessment is None
                else self.downstream_v8_assessment.as_dict()
            ),
            "v9_certification": self.v9_certification.as_dict(),
            "settings": dict(self.settings),
            "aggregate_confidence_score_emitted": self.aggregate_confidence_score_emitted,
        }


def _base_v8(
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
    v8_kwargs: Mapping[str, object],
) -> ForecastAssessmentV8Result:
    return assess_state_forecast_v8(
        name,
        conditional_log_density,
        marginal_log_density,
        covered,
        groups,
        blocks,
        region_size=region_size,
        final_evaluation_digest=None,
        accessed_artifact_digests_by_stage=None,
        final_evaluation_artifact_id=None,
        accessed_artifact_ids_by_stage=None,
        selection_row_ids_by_stage=None,
        refit_schemes=None,
        scheme_nested_draws=scheme_nested_draws,
        scheme_seed=scheme_seed,
        scheme_minimum_refits=scheme_minimum_refits,
        **dict(v8_kwargs),
    )


def _full_v8(
    name: str,
    conditional_log_density: Sequence[float],
    marginal_log_density: Sequence[float],
    covered: Sequence[bool],
    groups: Sequence[object],
    blocks: Sequence[object],
    *,
    region_size: Sequence[float],
    final_evaluation_digest: object | None,
    accessed_artifact_digests_by_stage: Mapping[object, Sequence[object]] | None,
    expected_evaluation_content_stage_names: Sequence[object] | None,
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
    v8_kwargs: Mapping[str, object],
) -> ForecastAssessmentV8Result:
    return assess_state_forecast_v8(
        name,
        conditional_log_density,
        marginal_log_density,
        covered,
        groups,
        blocks,
        region_size=region_size,
        final_evaluation_digest=final_evaluation_digest,
        accessed_artifact_digests_by_stage=accessed_artifact_digests_by_stage,
        expected_evaluation_content_stage_names=expected_evaluation_content_stage_names,
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
        **dict(v8_kwargs),
    )


def _inherit_summary(
    base: ForecastAssessmentV8Result,
    downstream: ForecastAssessmentV8Result,
    *,
    binding_status: str,
) -> ForecastAssessmentV9Certification:
    summary = downstream.v8_certification
    trace = tuple(base.v8_certification.trace) + (
        f"evaluation_ledger_binding:{binding_status}",
        "downstream_v8:run",
        f"evaluation_content_provenance:{summary.evaluation_content_provenance_status}",
        f"evaluation_access_provenance:{summary.evaluation_access_provenance_status}",
        f"selection_validation_provenance:{summary.selection_validation_provenance_status}",
        f"training_validation_provenance:{summary.training_validation_provenance_status}",
        f"heldout_row_provenance:{summary.heldout_row_provenance_status}",
        f"v9_certification:{summary.certification_status}",
        f"v9_operational:{summary.operational_status}",
    )
    return ForecastAssessmentV9Certification(
        base_validation_status=summary.base_validation_status,
        base_v8_certification_status=base.v8_certification.certification_status,
        base_v8_operational_status=base.v8_certification.operational_status,
        evaluation_ledger_binding_status=binding_status,
        downstream_v8_status="run",
        evaluation_content_provenance_status=summary.evaluation_content_provenance_status,
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


def _binding_mismatch_summary(
    base: ForecastAssessmentV8Result,
    binding: EvaluationLedgerBindingAudit,
) -> ForecastAssessmentV9Certification:
    summary = base.v8_certification
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
            + ("evaluation_ledger_binding_mismatch",)
        )
    )
    sentinel = "not_run_evaluation_ledger_binding_mismatch"
    trace = tuple(summary.trace) + (
        f"evaluation_ledger_binding:{binding.separation_category}",
        f"downstream_v8:{sentinel}",
        f"evaluation_content_provenance:{sentinel}",
        f"evaluation_access_provenance:{sentinel}",
        f"selection_validation_provenance:{sentinel}",
        f"training_validation_provenance:{sentinel}",
        f"heldout_row_provenance:{sentinel}",
        f"v9_certification:{certification}",
        f"v9_operational:{operational}",
    )
    return ForecastAssessmentV9Certification(
        base_validation_status=base_validation,
        base_v8_certification_status=base_certification,
        base_v8_operational_status=summary.operational_status,
        evaluation_ledger_binding_status=binding.separation_category,
        downstream_v8_status=sentinel,
        evaluation_content_provenance_status=sentinel,
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


def assess_state_forecast_v9(
    name: str,
    conditional_log_density: Sequence[float],
    marginal_log_density: Sequence[float],
    covered: Sequence[bool],
    groups: Sequence[object],
    blocks: Sequence[object],
    *,
    region_size: Sequence[float],
    artifact_digest_by_id: Mapping[object, object] | None = None,
    expected_evaluation_ledger_binding_stage_names: Sequence[object] | None = None,
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
    **v8_kwargs,
) -> ForecastAssessmentV9Result:
    """Gate ordinary v8 assessment by ID↔digest evaluation-ledger binding.

    When a caller supplies an artifact manifest, the same artifact-ID and digest
    ledgers that would be forwarded to v8 are first checked for internal binding.
    Binding mismatch suppresses the full v8 path before content, artifact-access,
    selection, training, held-out alignment or refit-scheme evidence can run.
    """

    binding = None
    if artifact_digest_by_id is None:
        if expected_evaluation_ledger_binding_stage_names is not None:
            raise ValueError(
                "expected_evaluation_ledger_binding_stage_names must not be supplied without artifact_digest_by_id"
            )
    else:
        missing = []
        if final_evaluation_artifact_id is None:
            missing.append("final_evaluation_artifact_id")
        if final_evaluation_digest is None:
            missing.append("final_evaluation_digest")
        if accessed_artifact_ids_by_stage is None:
            missing.append("accessed_artifact_ids_by_stage")
        if accessed_artifact_digests_by_stage is None:
            missing.append("accessed_artifact_digests_by_stage")
        if missing:
            raise ValueError(
                "evaluation-ledger binding requires artifact_digest_by_id together with "
                + ", ".join(missing)
            )
        binding = audit_evaluation_ledger_binding(
            final_evaluation_artifact_id,
            final_evaluation_digest,
            artifact_digest_by_id,
            accessed_artifact_ids_by_stage,
            accessed_artifact_digests_by_stage,
            expected_stage_names=expected_evaluation_ledger_binding_stage_names,
        )

    base = _base_v8(
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
        v8_kwargs=v8_kwargs,
    )

    downstream = None
    if binding is None or binding.ledger_binding_consistent:
        downstream = _full_v8(
            name,
            conditional_log_density,
            marginal_log_density,
            covered,
            groups,
            blocks,
            region_size=region_size,
            final_evaluation_digest=final_evaluation_digest,
            accessed_artifact_digests_by_stage=accessed_artifact_digests_by_stage,
            expected_evaluation_content_stage_names=expected_evaluation_content_stage_names,
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
            v8_kwargs=v8_kwargs,
        )
        summary = _inherit_summary(
            base,
            downstream,
            binding_status=(
                "not_audited" if binding is None else binding.separation_category
            ),
        )
    else:
        summary = _binding_mismatch_summary(base, binding)

    settings = {
        "base_v8_content_artifact_access_selection_and_scheme_layers_omitted": True,
        "evaluation_ledger_binding_audited": binding is not None,
        "evaluation_ledger_binding_expected_stage_coverage_checked": (
            False if binding is None else binding.expected_stage_coverage_checked
        ),
        "downstream_v8_assessment_run": downstream is not None,
        "scheme_nested_draws": int(scheme_nested_draws),
        "scheme_seed": (
            int(v8_kwargs.get("seed", 20260906)) if scheme_seed is None else int(scheme_seed)
        ),
        "scheme_minimum_refits": (
            int(v8_kwargs.get("minimum_refits", 8))
            if scheme_minimum_refits is None
            else int(scheme_minimum_refits)
        ),
    }
    return ForecastAssessmentV9Result(
        candidate_name=base.candidate_name,
        row_count=base.row_count,
        base_v8_assessment=base,
        evaluation_ledger_binding=binding,
        downstream_v8_assessment=downstream,
        v9_certification=summary,
        settings=settings,
        aggregate_confidence_score_emitted=False,
    )
