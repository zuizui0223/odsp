"""Forecast Assessment v10: v9 evidence gated by access-log chain provenance."""
from __future__ import annotations

from dataclasses import asdict, dataclass
from typing import Mapping, Sequence

from .evaluation_access_log_chain import (
    EvaluationAccessLogChainAudit,
    audit_evaluation_access_log_chain,
)
from .forecast_assessment_v9 import ForecastAssessmentV9Result, assess_state_forecast_v9


@dataclass(frozen=True)
class ForecastAssessmentV10Certification:
    base_validation_status: str
    base_v9_certification_status: str
    base_v9_operational_status: str
    evaluation_access_log_chain_status: str
    downstream_v9_status: str
    evaluation_ledger_binding_status: str
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
class ForecastAssessmentV10Result:
    candidate_name: str
    row_count: int
    base_v9_assessment: ForecastAssessmentV9Result
    evaluation_access_log_chain: EvaluationAccessLogChainAudit | None
    downstream_v9_assessment: ForecastAssessmentV9Result | None
    v10_certification: ForecastAssessmentV10Certification
    settings: dict[str, object]
    aggregate_confidence_score_emitted: bool

    def as_dict(self) -> dict[str, object]:
        return {
            "candidate_name": self.candidate_name,
            "row_count": self.row_count,
            "base_v9_assessment": self.base_v9_assessment.as_dict(),
            "evaluation_access_log_chain": (
                None
                if self.evaluation_access_log_chain is None
                else self.evaluation_access_log_chain.as_dict()
            ),
            "downstream_v9_assessment": (
                None
                if self.downstream_v9_assessment is None
                else self.downstream_v9_assessment.as_dict()
            ),
            "v10_certification": self.v10_certification.as_dict(),
            "settings": dict(self.settings),
            "aggregate_confidence_score_emitted": self.aggregate_confidence_score_emitted,
        }


def _base_v9(
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
    v9_kwargs: Mapping[str, object],
) -> ForecastAssessmentV9Result:
    return assess_state_forecast_v9(
        name,
        conditional_log_density,
        marginal_log_density,
        covered,
        groups,
        blocks,
        region_size=region_size,
        artifact_digest_by_id=None,
        final_evaluation_digest=None,
        accessed_artifact_digests_by_stage=None,
        final_evaluation_artifact_id=None,
        accessed_artifact_ids_by_stage=None,
        selection_row_ids_by_stage=None,
        refit_schemes=None,
        scheme_nested_draws=scheme_nested_draws,
        scheme_seed=scheme_seed,
        scheme_minimum_refits=scheme_minimum_refits,
        **dict(v9_kwargs),
    )


def _full_v9(
    name: str,
    conditional_log_density: Sequence[float],
    marginal_log_density: Sequence[float],
    covered: Sequence[bool],
    groups: Sequence[object],
    blocks: Sequence[object],
    *,
    region_size: Sequence[float],
    artifact_digest_by_id: Mapping[object, object] | None,
    expected_evaluation_ledger_binding_stage_names: Sequence[object] | None,
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
    v9_kwargs: Mapping[str, object],
) -> ForecastAssessmentV9Result:
    return assess_state_forecast_v9(
        name,
        conditional_log_density,
        marginal_log_density,
        covered,
        groups,
        blocks,
        region_size=region_size,
        artifact_digest_by_id=artifact_digest_by_id,
        expected_evaluation_ledger_binding_stage_names=expected_evaluation_ledger_binding_stage_names,
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
        **dict(v9_kwargs),
    )


def _inherit_summary(
    base: ForecastAssessmentV9Result,
    downstream: ForecastAssessmentV9Result,
    *,
    log_status: str,
) -> ForecastAssessmentV10Certification:
    summary = downstream.v9_certification
    trace = tuple(base.v9_certification.trace) + (
        f"evaluation_access_log_chain:{log_status}",
        "downstream_v9:run",
        f"evaluation_ledger_binding:{summary.evaluation_ledger_binding_status}",
        f"evaluation_content_provenance:{summary.evaluation_content_provenance_status}",
        f"evaluation_access_provenance:{summary.evaluation_access_provenance_status}",
        f"selection_validation_provenance:{summary.selection_validation_provenance_status}",
        f"training_validation_provenance:{summary.training_validation_provenance_status}",
        f"heldout_row_provenance:{summary.heldout_row_provenance_status}",
        f"v10_certification:{summary.certification_status}",
        f"v10_operational:{summary.operational_status}",
    )
    return ForecastAssessmentV10Certification(
        base_validation_status=summary.base_validation_status,
        base_v9_certification_status=base.v9_certification.certification_status,
        base_v9_operational_status=base.v9_certification.operational_status,
        evaluation_access_log_chain_status=log_status,
        downstream_v9_status="run",
        evaluation_ledger_binding_status=summary.evaluation_ledger_binding_status,
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


def _log_chain_mismatch_summary(
    base: ForecastAssessmentV9Result,
    audit: EvaluationAccessLogChainAudit,
) -> ForecastAssessmentV10Certification:
    summary = base.v9_certification
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
            + ("evaluation_access_log_chain_mismatch",)
        )
    )
    sentinel = "not_run_evaluation_access_log_chain_mismatch"
    trace = tuple(summary.trace) + (
        f"evaluation_access_log_chain:{audit.separation_category}",
        f"downstream_v9:{sentinel}",
        f"evaluation_ledger_binding:{sentinel}",
        f"evaluation_content_provenance:{sentinel}",
        f"evaluation_access_provenance:{sentinel}",
        f"selection_validation_provenance:{sentinel}",
        f"training_validation_provenance:{sentinel}",
        f"heldout_row_provenance:{sentinel}",
        f"v10_certification:{certification}",
        f"v10_operational:{operational}",
    )
    return ForecastAssessmentV10Certification(
        base_validation_status=base_validation,
        base_v9_certification_status=base_certification,
        base_v9_operational_status=summary.operational_status,
        evaluation_access_log_chain_status=audit.separation_category,
        downstream_v9_status=sentinel,
        evaluation_ledger_binding_status=sentinel,
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


def assess_state_forecast_v10(
    name: str,
    conditional_log_density: Sequence[float],
    marginal_log_density: Sequence[float],
    covered: Sequence[bool],
    groups: Sequence[object],
    blocks: Sequence[object],
    *,
    region_size: Sequence[float],
    evaluation_access_log_events: Sequence[Mapping[str, object]] | None = None,
    committed_access_event_count: int | None = None,
    committed_terminal_access_event_hash: object | None = None,
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
    **v9_kwargs,
) -> ForecastAssessmentV10Result:
    """Gate Forecast Assessment v9 by internal evaluation-access log-chain provenance."""

    audit = None
    log_metadata = (
        committed_access_event_count,
        committed_terminal_access_event_hash,
    )
    if evaluation_access_log_events is None:
        if any(value is not None for value in log_metadata):
            raise ValueError(
                "committed access-log metadata must not be supplied without evaluation_access_log_events"
            )
    else:
        missing = []
        if committed_access_event_count is None:
            missing.append("committed_access_event_count")
        if committed_terminal_access_event_hash is None:
            missing.append("committed_terminal_access_event_hash")
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
                "evaluation-access log-chain gating requires evaluation_access_log_events together with "
                + ", ".join(missing)
            )
        audit = audit_evaluation_access_log_chain(
            evaluation_access_log_events,
            committed_access_event_count,
            committed_terminal_access_event_hash,
            accessed_artifact_ids_by_stage,
            accessed_artifact_digests_by_stage,
        )

    base = _base_v9(
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
        v9_kwargs=v9_kwargs,
    )

    downstream = None
    if audit is None or audit.log_chain_consistent:
        downstream = _full_v9(
            name,
            conditional_log_density,
            marginal_log_density,
            covered,
            groups,
            blocks,
            region_size=region_size,
            artifact_digest_by_id=artifact_digest_by_id,
            expected_evaluation_ledger_binding_stage_names=expected_evaluation_ledger_binding_stage_names,
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
            v9_kwargs=v9_kwargs,
        )
        summary = _inherit_summary(
            base,
            downstream,
            log_status=("not_audited" if audit is None else audit.separation_category),
        )
    else:
        summary = _log_chain_mismatch_summary(base, audit)

    settings = {
        "base_v9_provenance_and_scheme_layers_omitted": True,
        "evaluation_access_log_chain_audited": audit is not None,
        "downstream_v9_assessment_run": downstream is not None,
        "scheme_nested_draws": int(scheme_nested_draws),
        "scheme_seed": (
            int(v9_kwargs.get("seed", 20260906)) if scheme_seed is None else int(scheme_seed)
        ),
        "scheme_minimum_refits": (
            int(v9_kwargs.get("minimum_refits", 8))
            if scheme_minimum_refits is None
            else int(scheme_minimum_refits)
        ),
    }
    return ForecastAssessmentV10Result(
        candidate_name=base.candidate_name,
        row_count=base.row_count,
        base_v9_assessment=base,
        evaluation_access_log_chain=audit,
        downstream_v9_assessment=downstream,
        v10_certification=summary,
        settings=settings,
        aggregate_confidence_score_emitted=False,
    )
