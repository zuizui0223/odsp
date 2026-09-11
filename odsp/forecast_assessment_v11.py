"""Forecast Assessment v11: v10 evidence gated by access-checkpoint provenance."""
from __future__ import annotations

from dataclasses import asdict, dataclass
from typing import Mapping, Sequence

from .evaluation_access_checkpoints import (
    EvaluationAccessCheckpointAudit,
    audit_evaluation_access_checkpoints,
)
from .forecast_assessment_v10 import ForecastAssessmentV10Result, assess_state_forecast_v10


@dataclass(frozen=True)
class ForecastAssessmentV11Certification:
    base_validation_status: str
    base_v10_certification_status: str
    base_v10_operational_status: str
    evaluation_access_checkpoint_status: str
    downstream_v10_status: str
    evaluation_access_log_chain_status: str
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
class ForecastAssessmentV11Result:
    candidate_name: str
    row_count: int
    base_v10_assessment: ForecastAssessmentV10Result
    evaluation_access_checkpoints: EvaluationAccessCheckpointAudit | None
    downstream_v10_assessment: ForecastAssessmentV10Result | None
    v11_certification: ForecastAssessmentV11Certification
    settings: dict[str, object]
    aggregate_confidence_score_emitted: bool

    def as_dict(self) -> dict[str, object]:
        return {
            "candidate_name": self.candidate_name,
            "row_count": self.row_count,
            "base_v10_assessment": self.base_v10_assessment.as_dict(),
            "evaluation_access_checkpoints": (
                None
                if self.evaluation_access_checkpoints is None
                else self.evaluation_access_checkpoints.as_dict()
            ),
            "downstream_v10_assessment": (
                None
                if self.downstream_v10_assessment is None
                else self.downstream_v10_assessment.as_dict()
            ),
            "v11_certification": self.v11_certification.as_dict(),
            "settings": dict(self.settings),
            "aggregate_confidence_score_emitted": self.aggregate_confidence_score_emitted,
        }


def _base_v10(
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
    v10_kwargs: Mapping[str, object],
) -> ForecastAssessmentV10Result:
    return assess_state_forecast_v10(
        name,
        conditional_log_density,
        marginal_log_density,
        covered,
        groups,
        blocks,
        region_size=region_size,
        evaluation_access_log_events=None,
        committed_access_event_count=None,
        committed_terminal_access_event_hash=None,
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
        **dict(v10_kwargs),
    )


def _full_v10(
    name: str,
    conditional_log_density: Sequence[float],
    marginal_log_density: Sequence[float],
    covered: Sequence[bool],
    groups: Sequence[object],
    blocks: Sequence[object],
    *,
    region_size: Sequence[float],
    evaluation_access_log_events: Sequence[Mapping[str, object]] | None,
    committed_access_event_count: int | None,
    committed_terminal_access_event_hash: object | None,
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
    v10_kwargs: Mapping[str, object],
) -> ForecastAssessmentV10Result:
    return assess_state_forecast_v10(
        name,
        conditional_log_density,
        marginal_log_density,
        covered,
        groups,
        blocks,
        region_size=region_size,
        evaluation_access_log_events=evaluation_access_log_events,
        committed_access_event_count=committed_access_event_count,
        committed_terminal_access_event_hash=committed_terminal_access_event_hash,
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
        **dict(v10_kwargs),
    )


def _inherit_summary(
    base: ForecastAssessmentV10Result,
    downstream: ForecastAssessmentV10Result,
    *,
    checkpoint_status: str,
) -> ForecastAssessmentV11Certification:
    summary = downstream.v10_certification
    trace = tuple(base.v10_certification.trace) + (
        f"evaluation_access_checkpoints:{checkpoint_status}",
        "downstream_v10:run",
        f"evaluation_access_log_chain:{summary.evaluation_access_log_chain_status}",
        f"evaluation_ledger_binding:{summary.evaluation_ledger_binding_status}",
        f"evaluation_content_provenance:{summary.evaluation_content_provenance_status}",
        f"evaluation_access_provenance:{summary.evaluation_access_provenance_status}",
        f"selection_validation_provenance:{summary.selection_validation_provenance_status}",
        f"training_validation_provenance:{summary.training_validation_provenance_status}",
        f"heldout_row_provenance:{summary.heldout_row_provenance_status}",
        f"v11_certification:{summary.certification_status}",
        f"v11_operational:{summary.operational_status}",
    )
    return ForecastAssessmentV11Certification(
        base_validation_status=summary.base_validation_status,
        base_v10_certification_status=base.v10_certification.certification_status,
        base_v10_operational_status=base.v10_certification.operational_status,
        evaluation_access_checkpoint_status=checkpoint_status,
        downstream_v10_status="run",
        evaluation_access_log_chain_status=summary.evaluation_access_log_chain_status,
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


def _checkpoint_mismatch_summary(
    base: ForecastAssessmentV10Result,
    audit: EvaluationAccessCheckpointAudit,
) -> ForecastAssessmentV11Certification:
    summary = base.v10_certification
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
            + ("evaluation_access_checkpoint_mismatch",)
        )
    )
    sentinel = "not_run_evaluation_access_checkpoint_mismatch"
    trace = tuple(summary.trace) + (
        f"evaluation_access_checkpoints:{audit.separation_category}",
        f"downstream_v10:{sentinel}",
        f"evaluation_access_log_chain:{sentinel}",
        f"evaluation_ledger_binding:{sentinel}",
        f"evaluation_content_provenance:{sentinel}",
        f"evaluation_access_provenance:{sentinel}",
        f"selection_validation_provenance:{sentinel}",
        f"training_validation_provenance:{sentinel}",
        f"heldout_row_provenance:{sentinel}",
        f"v11_certification:{certification}",
        f"v11_operational:{operational}",
    )
    return ForecastAssessmentV11Certification(
        base_validation_status=base_validation,
        base_v10_certification_status=base_certification,
        base_v10_operational_status=summary.operational_status,
        evaluation_access_checkpoint_status=audit.separation_category,
        downstream_v10_status=sentinel,
        evaluation_access_log_chain_status=sentinel,
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


def _event_hashes(events: Sequence[Mapping[str, object]]) -> tuple[object, ...]:
    hashes: list[object] = []
    for row in events:
        if not isinstance(row, Mapping):
            raise ValueError("each evaluation access-log event must be a mapping")
        if "event_hash" not in row:
            raise ValueError("each evaluation access-log event must contain event_hash for checkpoint gating")
        hashes.append(row["event_hash"])
    if not hashes:
        raise ValueError("evaluation_access_log_events must contain at least one event when checkpoints are supplied")
    return tuple(hashes)


def assess_state_forecast_v11(
    name: str,
    conditional_log_density: Sequence[float],
    marginal_log_density: Sequence[float],
    covered: Sequence[bool],
    groups: Sequence[object],
    blocks: Sequence[object],
    *,
    region_size: Sequence[float],
    evaluation_access_checkpoints: Sequence[Mapping[str, object]] | None = None,
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
    **v10_kwargs,
) -> ForecastAssessmentV11Result:
    """Gate Forecast Assessment v10 by evaluation-access checkpoint provenance."""

    checkpoint_audit = None
    if evaluation_access_checkpoints is not None:
        if evaluation_access_log_events is None:
            raise ValueError(
                "evaluation_access_log_events are required when evaluation_access_checkpoints are supplied"
            )
        checkpoint_audit = audit_evaluation_access_checkpoints(
            _event_hashes(evaluation_access_log_events),
            evaluation_access_checkpoints,
        )

    base = _base_v10(
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
        v10_kwargs=v10_kwargs,
    )

    downstream = None
    if checkpoint_audit is None or checkpoint_audit.checkpoints_consistent:
        downstream = _full_v10(
            name,
            conditional_log_density,
            marginal_log_density,
            covered,
            groups,
            blocks,
            region_size=region_size,
            evaluation_access_log_events=evaluation_access_log_events,
            committed_access_event_count=committed_access_event_count,
            committed_terminal_access_event_hash=committed_terminal_access_event_hash,
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
            v10_kwargs=v10_kwargs,
        )
        summary = _inherit_summary(
            base,
            downstream,
            checkpoint_status=(
                "not_audited"
                if checkpoint_audit is None
                else checkpoint_audit.separation_category
            ),
        )
    else:
        summary = _checkpoint_mismatch_summary(base, checkpoint_audit)

    settings = {
        "base_v10_provenance_and_scheme_layers_omitted": True,
        "evaluation_access_checkpoints_audited": checkpoint_audit is not None,
        "downstream_v10_assessment_run": downstream is not None,
        "scheme_nested_draws": int(scheme_nested_draws),
        "scheme_seed": (
            int(v10_kwargs.get("seed", 20260906)) if scheme_seed is None else int(scheme_seed)
        ),
        "scheme_minimum_refits": (
            int(v10_kwargs.get("minimum_refits", 8))
            if scheme_minimum_refits is None
            else int(scheme_minimum_refits)
        ),
    }
    return ForecastAssessmentV11Result(
        candidate_name=base.candidate_name,
        row_count=base.row_count,
        base_v10_assessment=base,
        evaluation_access_checkpoints=checkpoint_audit,
        downstream_v10_assessment=downstream,
        v11_certification=summary,
        settings=settings,
        aggregate_confidence_score_emitted=False,
    )
