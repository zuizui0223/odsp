"""Known-truth benchmark for Forecast Assessment v10 access-log chain gating."""
from __future__ import annotations

from copy import deepcopy

import numpy as np

from .evaluation_access_log_chain_benchmark import _build_chain
from .forecast_assessment_v3_benchmark import _base_design, _common_kwargs, _region
from .forecast_assessment_v4_benchmark import _provenance_ids, _scheme_inputs
from .forecast_assessment_v5_benchmark import _training_memberships
from .forecast_assessment_v6_benchmark import _selection_rows
from .forecast_assessment_v7_benchmark import FINAL_ARTIFACT_ID, _clean_access
from .forecast_assessment_v8_benchmark import FINAL_CONTENT_DIGEST, _clean_content, _digest
from .forecast_assessment_v9 import assess_state_forecast_v9
from .forecast_assessment_v9_benchmark import _manifest
from .forecast_assessment_v10 import assess_state_forecast_v10


EXPECTED_ACCESS_STAGES = ("candidate_screening", "model_review", "threshold_review")
EXPECTED_SELECTION_STAGES = (
    "candidate_ranking",
    "early_stopping",
    "hyperparameter_tuning",
)


def _chain_from_ledgers(
    id_ledger: dict[str, tuple[str, ...]],
    digest_ledger: dict[str, tuple[str, ...]],
) -> list[dict[str, object]]:
    specs: list[tuple[str, str, str]] = []
    for stage in EXPECTED_ACCESS_STAGES:
        for artifact_id, digest in zip(id_ledger[stage], digest_ledger[stage], strict=True):
            specs.append((stage, artifact_id, digest))
    return _build_chain(tuple(specs))


def _log_args(
    events: list[dict[str, object]],
) -> dict[str, object]:
    return {
        "evaluation_access_log_events": events,
        "committed_access_event_count": len(events),
        "committed_terminal_access_event_hash": events[-1]["event_hash"],
    }


def run_forecast_assessment_v10_benchmark(*, seed: int = 20260911) -> dict[str, object]:
    if seed != 20260911:
        raise ValueError("the frozen Forecast Assessment v10 benchmark uses seed 20260911")

    gain, groups, blocks, covered, bootstrap, _fold, _seed, fragile, ids = _base_design()
    n = gain.size
    base_ids = tuple(f"validation-{idx:04d}" for idx in range(n))
    conditional = gain.copy()
    marginal = np.zeros(n)

    clean_access = _clean_access()
    clean_content = _clean_content()
    clean_manifest = _manifest(clean_access, clean_content)
    clean_events = _chain_from_ledgers(clean_access, clean_content)
    clean_log = _log_args(clean_events)
    clean_selection = _selection_rows()

    base_kwargs = _common_kwargs()
    base_kwargs["region_size"] = _region(n)
    v2_formal_kwargs = dict(base_kwargs)
    v2_formal_kwargs.update(
        run_simultaneous_group_certification=True,
        simultaneous_draws=1200,
        refit_row_gain=bootstrap,
        refit_ids=ids["bootstrap"],
        reference_refit_id=ids["bootstrap"][0],
        refit_nested_draws=1200,
        minimum_refits=8,
    )

    robust_schemes, robust_ids, robust_refs = _scheme_inputs(ids)
    sensitive_schemes, sensitive_ids, sensitive_refs = _scheme_inputs(ids, sensitive=True)
    clean_training = _training_memberships(robust_ids)
    sensitive_training = _training_memberships(sensitive_ids)

    common_scheme = dict(
        validation_row_ids=base_ids,
        refit_schemes=robust_schemes,
        validation_row_ids_by_scheme=_provenance_ids(base_ids, robust_schemes),
        refit_ids_by_scheme=robust_ids,
        reference_refit_ids_by_scheme=robust_refs,
        training_row_ids_by_scheme=clean_training,
        scheme_nested_draws=1200,
        scheme_seed=20260907,
        scheme_minimum_refits=8,
    )
    full_provenance = dict(
        artifact_digest_by_id=clean_manifest,
        expected_evaluation_ledger_binding_stage_names=EXPECTED_ACCESS_STAGES,
        final_evaluation_digest=FINAL_CONTENT_DIGEST,
        accessed_artifact_digests_by_stage=clean_content,
        expected_evaluation_content_stage_names=EXPECTED_ACCESS_STAGES,
        final_evaluation_artifact_id=FINAL_ARTIFACT_ID,
        accessed_artifact_ids_by_stage=clean_access,
        expected_evaluation_access_stage_names=EXPECTED_ACCESS_STAGES,
        selection_row_ids_by_stage=clean_selection,
        expected_selection_stage_names=EXPECTED_SELECTION_STAGES,
    )

    clean = assess_state_forecast_v10(
        "strong",
        conditional,
        marginal,
        covered,
        groups,
        blocks,
        **clean_log,
        **full_provenance,
        **common_scheme,
        **v2_formal_kwargs,
    )
    direct_full_v9 = assess_state_forecast_v9(
        "strong",
        conditional,
        marginal,
        covered,
        groups,
        blocks,
        **full_provenance,
        **common_scheme,
        **v2_formal_kwargs,
    )
    direct_base_v9 = assess_state_forecast_v9(
        "strong",
        conditional,
        marginal,
        covered,
        groups,
        blocks,
        scheme_nested_draws=1200,
        scheme_seed=20260907,
        scheme_minimum_refits=8,
        **v2_formal_kwargs,
    )

    wrong_terminal = "sha256:" + "f" * 64
    log_mismatch = assess_state_forecast_v10(
        "log-mismatch",
        conditional,
        marginal,
        covered,
        groups,
        blocks,
        evaluation_access_log_events=clean_events,
        committed_access_event_count=len(clean_events),
        committed_terminal_access_event_hash=wrong_terminal,
        **full_provenance,
        **common_scheme,
        **v2_formal_kwargs,
    )

    v2_fragile_kwargs = dict(base_kwargs)
    v2_fragile_kwargs.update(
        refit_row_gain=fragile,
        refit_ids=ids["bootstrap"],
        reference_refit_id=ids["bootstrap"][0],
        refit_nested_draws=1200,
        minimum_refits=8,
    )
    prior_failure = assess_state_forecast_v10(
        "prior-failure",
        conditional,
        marginal,
        covered,
        groups,
        blocks,
        evaluation_access_log_events=clean_events,
        committed_access_event_count=len(clean_events),
        committed_terminal_access_event_hash=wrong_terminal,
        **full_provenance,
        **common_scheme,
        **v2_fragile_kwargs,
    )

    binding_bad_content = deepcopy(clean_content)
    binding_rows = list(binding_bad_content["candidate_screening"])
    binding_rows[-1] = _digest("v10-binding-substitution")
    binding_bad_content["candidate_screening"] = tuple(binding_rows)
    binding_bad_events = _chain_from_ledgers(clean_access, binding_bad_content)
    clean_log_binding_mismatch = assess_state_forecast_v10(
        "binding-mismatch",
        conditional,
        marginal,
        covered,
        groups,
        blocks,
        **_log_args(binding_bad_events),
        artifact_digest_by_id=clean_manifest,
        expected_evaluation_ledger_binding_stage_names=EXPECTED_ACCESS_STAGES,
        final_evaluation_digest=FINAL_CONTENT_DIGEST,
        accessed_artifact_digests_by_stage=binding_bad_content,
        expected_evaluation_content_stage_names=EXPECTED_ACCESS_STAGES,
        final_evaluation_artifact_id=FINAL_ARTIFACT_ID,
        accessed_artifact_ids_by_stage=clean_access,
        expected_evaluation_access_stage_names=EXPECTED_ACCESS_STAGES,
        selection_row_ids_by_stage=clean_selection,
        expected_selection_stage_names=EXPECTED_SELECTION_STAGES,
        **common_scheme,
        **v2_formal_kwargs,
    )

    content_leak_ids = deepcopy(clean_access)
    content_leak_digests = deepcopy(clean_content)
    alias_id = "v10-byte-identical-final-copy"
    content_manifest = dict(clean_manifest)
    content_manifest[alias_id] = FINAL_CONTENT_DIGEST
    ids_rows = list(content_leak_ids["candidate_screening"])
    digest_rows = list(content_leak_digests["candidate_screening"])
    ids_rows[-1] = alias_id
    digest_rows[-1] = FINAL_CONTENT_DIGEST
    content_leak_ids["candidate_screening"] = tuple(ids_rows)
    content_leak_digests["candidate_screening"] = tuple(digest_rows)
    content_leak_events = _chain_from_ledgers(content_leak_ids, content_leak_digests)
    clean_log_content_leak = assess_state_forecast_v10(
        "content-leakage",
        conditional,
        marginal,
        covered,
        groups,
        blocks,
        **_log_args(content_leak_events),
        artifact_digest_by_id=content_manifest,
        expected_evaluation_ledger_binding_stage_names=EXPECTED_ACCESS_STAGES,
        final_evaluation_digest=FINAL_CONTENT_DIGEST,
        accessed_artifact_digests_by_stage=content_leak_digests,
        expected_evaluation_content_stage_names=EXPECTED_ACCESS_STAGES,
        final_evaluation_artifact_id=FINAL_ARTIFACT_ID,
        accessed_artifact_ids_by_stage=content_leak_ids,
        expected_evaluation_access_stage_names=EXPECTED_ACCESS_STAGES,
        selection_row_ids_by_stage=clean_selection,
        expected_selection_stage_names=EXPECTED_SELECTION_STAGES,
        **common_scheme,
        **v2_formal_kwargs,
    )

    leaking_selection = _selection_rows("v10-leaking-selection")
    ranking = list(leaking_selection["candidate_ranking"])
    ranking[3] = base_ids[23]
    leaking_selection["candidate_ranking"] = tuple(ranking)
    clean_log_selection_leak = assess_state_forecast_v10(
        "selection-leakage",
        conditional,
        marginal,
        covered,
        groups,
        blocks,
        **clean_log,
        artifact_digest_by_id=clean_manifest,
        expected_evaluation_ledger_binding_stage_names=EXPECTED_ACCESS_STAGES,
        final_evaluation_digest=FINAL_CONTENT_DIGEST,
        accessed_artifact_digests_by_stage=clean_content,
        expected_evaluation_content_stage_names=EXPECTED_ACCESS_STAGES,
        final_evaluation_artifact_id=FINAL_ARTIFACT_ID,
        accessed_artifact_ids_by_stage=clean_access,
        expected_evaluation_access_stage_names=EXPECTED_ACCESS_STAGES,
        selection_row_ids_by_stage=leaking_selection,
        expected_selection_stage_names=EXPECTED_SELECTION_STAGES,
        **common_scheme,
        **v2_formal_kwargs,
    )

    leaking_training = deepcopy(clean_training)
    leaking_refit = ids["seed"][5]
    training_rows = list(leaking_training["seed"][leaking_refit])
    training_rows[2] = base_ids[17]
    leaking_training["seed"][leaking_refit] = tuple(training_rows)
    clean_log_training_leak = assess_state_forecast_v10(
        "training-leakage",
        conditional,
        marginal,
        covered,
        groups,
        blocks,
        **clean_log,
        artifact_digest_by_id=clean_manifest,
        expected_evaluation_ledger_binding_stage_names=EXPECTED_ACCESS_STAGES,
        final_evaluation_digest=FINAL_CONTENT_DIGEST,
        accessed_artifact_digests_by_stage=clean_content,
        expected_evaluation_content_stage_names=EXPECTED_ACCESS_STAGES,
        final_evaluation_artifact_id=FINAL_ARTIFACT_ID,
        accessed_artifact_ids_by_stage=clean_access,
        expected_evaluation_access_stage_names=EXPECTED_ACCESS_STAGES,
        selection_row_ids_by_stage=clean_selection,
        expected_selection_stage_names=EXPECTED_SELECTION_STAGES,
        validation_row_ids=base_ids,
        refit_schemes=robust_schemes,
        validation_row_ids_by_scheme=_provenance_ids(base_ids, robust_schemes),
        refit_ids_by_scheme=robust_ids,
        reference_refit_ids_by_scheme=robust_refs,
        training_row_ids_by_scheme=leaking_training,
        scheme_nested_draws=1200,
        scheme_seed=20260907,
        scheme_minimum_refits=8,
        **v2_formal_kwargs,
    )

    mismatch_ids = dict(_provenance_ids(base_ids, robust_schemes))
    bad_seed = list(mismatch_ids["seed"])
    bad_seed[-1] = "validation-extra"
    mismatch_ids["seed"] = tuple(bad_seed)
    clean_log_row_mismatch = assess_state_forecast_v10(
        "row-mismatch",
        conditional,
        marginal,
        covered,
        groups,
        blocks,
        **clean_log,
        **full_provenance,
        validation_row_ids=base_ids,
        refit_schemes=robust_schemes,
        validation_row_ids_by_scheme=mismatch_ids,
        refit_ids_by_scheme=robust_ids,
        reference_refit_ids_by_scheme=robust_refs,
        training_row_ids_by_scheme=clean_training,
        scheme_nested_draws=1200,
        scheme_seed=20260907,
        scheme_minimum_refits=8,
        **v2_formal_kwargs,
    )

    clean_log_sensitive = assess_state_forecast_v10(
        "scheme-sensitive",
        conditional,
        marginal,
        covered,
        groups,
        blocks,
        **clean_log,
        **full_provenance,
        validation_row_ids=base_ids,
        refit_schemes=sensitive_schemes,
        validation_row_ids_by_scheme=_provenance_ids(base_ids, sensitive_schemes),
        refit_ids_by_scheme=sensitive_ids,
        reference_refit_ids_by_scheme=sensitive_refs,
        training_row_ids_by_scheme=sensitive_training,
        scheme_nested_draws=1200,
        scheme_seed=20260907,
        scheme_minimum_refits=8,
        **v2_formal_kwargs,
    )

    mismatch_without_lower_layers = assess_state_forecast_v10(
        "log-mismatch-no-lower-layers",
        conditional,
        marginal,
        covered,
        groups,
        blocks,
        evaluation_access_log_events=clean_events,
        committed_access_event_count=len(clean_events),
        committed_terminal_access_event_hash=wrong_terminal,
        final_evaluation_digest=FINAL_CONTENT_DIGEST,
        accessed_artifact_digests_by_stage=clean_content,
        final_evaluation_artifact_id=FINAL_ARTIFACT_ID,
        accessed_artifact_ids_by_stage=clean_access,
        scheme_nested_draws=1200,
        scheme_seed=20260907,
        scheme_minimum_refits=8,
        **v2_formal_kwargs,
    )

    train_x = np.column_stack([np.linspace(-1, 1, 60), np.sin(np.linspace(-2, 2, 60))])
    query_x = np.asarray([[0.0, 0.0], [0.5, 0.2], [3.0, 0.0]])
    strict = assess_state_forecast_v10(
        "strict",
        conditional,
        marginal,
        covered,
        groups,
        blocks,
        **clean_log,
        **full_provenance,
        novelty_train_X=train_x,
        novelty_query_X=query_x,
        **common_scheme,
        **v2_formal_kwargs,
    )

    omitted_log = assess_state_forecast_v10(
        "omitted-log",
        conditional,
        marginal,
        covered,
        groups,
        blocks,
        **full_provenance,
        **common_scheme,
        **v2_formal_kwargs,
    )
    omitted_direct_v9 = assess_state_forecast_v9(
        "omitted-log",
        conditional,
        marginal,
        covered,
        groups,
        blocks,
        **full_provenance,
        **common_scheme,
        **v2_formal_kwargs,
    )

    checks = {
        "clean_log_chain_case_is_certified": clean.evaluation_access_log_chain is not None and clean.evaluation_access_log_chain.log_chain_consistent and clean.downstream_v9_assessment is not None and clean.v10_certification.certification_status == "certified",
        "provenance_omitted_base_v9_result_is_preserved_exactly": clean.base_v9_assessment.as_dict() == direct_base_v9.as_dict(),
        "clean_log_chain_case_matches_direct_full_v9_result": clean.downstream_v9_assessment is not None and clean.downstream_v9_assessment.as_dict() == direct_full_v9.as_dict(),
        "log_chain_mismatch_makes_otherwise_certifiable_case_unavailable": log_mismatch.base_v9_assessment.v9_certification.certification_status == "certified" and log_mismatch.v10_certification.certification_status == "unavailable" and log_mismatch.v10_certification.operational_status == "admitted_extended_unavailable",
        "log_chain_mismatch_prevents_downstream_v9_assessment": log_mismatch.evaluation_access_log_chain is not None and log_mismatch.evaluation_access_log_chain.separation_category == "evaluation_access_log_chain_mismatch" and log_mismatch.downstream_v9_assessment is None and not log_mismatch.settings["downstream_v9_assessment_run"],
        "log_chain_mismatch_is_only_new_provenance_blocker": log_mismatch.v10_certification.provenance_blocking_reasons == ("evaluation_access_log_chain_mismatch",) and log_mismatch.v10_certification.evaluation_ledger_binding_status == "not_run_evaluation_access_log_chain_mismatch" and not log_mismatch.v10_certification.statistical_blocking_reasons,
        "prior_base_v9_not_certified_is_not_rescued_by_log_chain_mismatch": prior_failure.base_v9_assessment.v9_certification.certification_status == "not_certified" and prior_failure.v10_certification.certification_status == "not_certified" and prior_failure.downstream_v9_assessment is None,
        "clean_log_chain_plus_binding_mismatch_inherits_v9_unavailable": clean_log_binding_mismatch.downstream_v9_assessment is not None and clean_log_binding_mismatch.downstream_v9_assessment.v9_certification.certification_status == "unavailable" and "evaluation_ledger_binding_mismatch" in clean_log_binding_mismatch.v10_certification.provenance_blocking_reasons,
        "clean_log_chain_plus_content_leakage_inherits_v9_unavailable": clean_log_content_leak.downstream_v9_assessment is not None and clean_log_content_leak.downstream_v9_assessment.v9_certification.certification_status == "unavailable" and "final_evaluation_content_leakage" in clean_log_content_leak.v10_certification.provenance_blocking_reasons,
        "clean_log_chain_plus_selection_leakage_inherits_v9_unavailable": clean_log_selection_leak.downstream_v9_assessment is not None and clean_log_selection_leak.downstream_v9_assessment.v9_certification.certification_status == "unavailable" and "selection_validation_leakage" in clean_log_selection_leak.v10_certification.provenance_blocking_reasons,
        "clean_log_chain_plus_training_leakage_inherits_v9_unavailable": clean_log_training_leak.downstream_v9_assessment is not None and clean_log_training_leak.downstream_v9_assessment.v9_certification.certification_status == "unavailable" and "training_validation_leakage" in clean_log_training_leak.v10_certification.provenance_blocking_reasons,
        "clean_log_chain_plus_row_mismatch_inherits_v9_unavailable": clean_log_row_mismatch.downstream_v9_assessment is not None and clean_log_row_mismatch.downstream_v9_assessment.v9_certification.certification_status == "unavailable" and "heldout_row_mismatch" in clean_log_row_mismatch.v10_certification.provenance_blocking_reasons,
        "clean_log_chain_plus_scheme_sensitive_inherits_v9_not_certified": clean_log_sensitive.downstream_v9_assessment is not None and clean_log_sensitive.downstream_v9_assessment.v9_certification.certification_status == "not_certified" and "refit_scheme_sensitive" in clean_log_sensitive.v10_certification.statistical_blocking_reasons,
        "log_chain_mismatch_without_selection_or_scheme_layers_is_still_unavailable": mismatch_without_lower_layers.downstream_v9_assessment is None and mismatch_without_lower_layers.v10_certification.certification_status == "unavailable",
        "strict_extrapolation_remains_warning_under_clean_log_chain": strict.downstream_v9_assessment is not None and strict.v10_certification.certification_status == "certified" and strict.v10_certification.operational_status == "admitted_with_warnings" and "strict_extrapolation" in strict.v10_certification.warning_reasons and "environmental_novelty" in strict.v10_certification.warning_reasons,
        "omitted_log_chain_layer_preserves_direct_full_v9_result_and_certification": omitted_log.evaluation_access_log_chain is None and omitted_log.downstream_v9_assessment is not None and omitted_log.downstream_v9_assessment.as_dict() == omitted_direct_v9.as_dict() and omitted_log.v10_certification.certification_status == omitted_direct_v9.v9_certification.certification_status,
        "audited_stage_ledgers_are_forwarded_to_downstream_v9": clean.downstream_v9_assessment is not None and clean.downstream_v9_assessment.evaluation_ledger_binding is not None and clean.downstream_v9_assessment.evaluation_ledger_binding.ledger_binding_consistent and clean.downstream_v9_assessment.as_dict() == direct_full_v9.as_dict(),
        "aggregate_confidence_score_emitted": all(not row.aggregate_confidence_score_emitted for row in (clean, log_mismatch, prior_failure, clean_log_binding_mismatch, clean_log_content_leak, clean_log_selection_leak, clean_log_training_leak, clean_log_row_mismatch, clean_log_sensitive, mismatch_without_lower_layers, strict, omitted_log)),
    }

    return {
        "seed": seed,
        "clean_log_chain": clean.as_dict(),
        "log_chain_mismatch": log_mismatch.as_dict(),
        "prior_v9_failure_with_log_chain_mismatch": prior_failure.as_dict(),
        "clean_log_chain_binding_mismatch": clean_log_binding_mismatch.as_dict(),
        "clean_log_chain_content_leakage": clean_log_content_leak.as_dict(),
        "clean_log_chain_selection_leakage": clean_log_selection_leak.as_dict(),
        "clean_log_chain_training_leakage": clean_log_training_leak.as_dict(),
        "clean_log_chain_row_mismatch": clean_log_row_mismatch.as_dict(),
        "clean_log_chain_scheme_sensitive": clean_log_sensitive.as_dict(),
        "log_chain_mismatch_without_lower_layers": mismatch_without_lower_layers.as_dict(),
        "strict_extrapolation": strict.as_dict(),
        "omitted_log_chain": omitted_log.as_dict(),
        "checks": [{"name": name, "passed": bool(value)} for name, value in checks.items()],
        "passed": bool(all(checks.values())),
    }
