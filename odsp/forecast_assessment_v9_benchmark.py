"""Known-truth benchmark for Forecast Assessment v9 ledger binding."""
from __future__ import annotations

from copy import deepcopy

import numpy as np

from .forecast_assessment_v3_benchmark import _base_design, _common_kwargs, _region
from .forecast_assessment_v4_benchmark import _provenance_ids, _scheme_inputs
from .forecast_assessment_v5_benchmark import _training_memberships
from .forecast_assessment_v6_benchmark import _selection_rows
from .forecast_assessment_v7_benchmark import FINAL_ARTIFACT_ID, _clean_access
from .forecast_assessment_v8 import assess_state_forecast_v8
from .forecast_assessment_v8_benchmark import FINAL_CONTENT_DIGEST, _clean_content, _digest
from .forecast_assessment_v9 import assess_state_forecast_v9


def _manifest(
    id_ledger: dict[str, tuple[str, ...]],
    digest_ledger: dict[str, tuple[str, ...]],
) -> dict[str, str]:
    result = {FINAL_ARTIFACT_ID: FINAL_CONTENT_DIGEST, "final-content-alias": FINAL_CONTENT_DIGEST}
    for stage in id_ledger:
        for artifact_id, digest in zip(id_ledger[stage], digest_ledger[stage], strict=True):
            result[artifact_id] = digest
    return result


def run_forecast_assessment_v9_benchmark(*, seed: int = 20260910) -> dict[str, object]:
    if seed != 20260910:
        raise ValueError("the frozen Forecast Assessment v9 benchmark uses seed 20260910")

    gain, groups, blocks, covered, bootstrap, _fold, _seed, fragile, ids = _base_design()
    n = gain.size
    base_ids = tuple(f"validation-{idx:04d}" for idx in range(n))
    conditional = gain.copy()
    marginal = np.zeros(n)

    expected_access_stages = ("candidate_screening", "model_review", "threshold_review")
    clean_access = _clean_access()
    clean_content = _clean_content()
    manifest = _manifest(clean_access, clean_content)
    expected_selection_stages = (
        "candidate_ranking",
        "early_stopping",
        "hyperparameter_tuning",
    )
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
        final_evaluation_digest=FINAL_CONTENT_DIGEST,
        accessed_artifact_digests_by_stage=clean_content,
        expected_evaluation_content_stage_names=expected_access_stages,
        final_evaluation_artifact_id=FINAL_ARTIFACT_ID,
        accessed_artifact_ids_by_stage=clean_access,
        expected_evaluation_access_stage_names=expected_access_stages,
        selection_row_ids_by_stage=clean_selection,
        expected_selection_stage_names=expected_selection_stages,
    )
    binding_args = dict(
        artifact_digest_by_id=manifest,
        expected_evaluation_ledger_binding_stage_names=expected_access_stages,
    )

    clean = assess_state_forecast_v9(
        "strong",
        conditional,
        marginal,
        covered,
        groups,
        blocks,
        **binding_args,
        **full_provenance,
        **common_scheme,
        **v2_formal_kwargs,
    )
    direct_full_v8 = assess_state_forecast_v8(
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
    direct_base_v8 = assess_state_forecast_v8(
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

    mismatched_content = deepcopy(clean_content)
    rows = list(mismatched_content["candidate_screening"])
    rows[-1] = _digest("binding-substitution")
    mismatched_content["candidate_screening"] = tuple(rows)
    binding_mismatch = assess_state_forecast_v9(
        "binding-mismatch",
        conditional,
        marginal,
        covered,
        groups,
        blocks,
        artifact_digest_by_id=manifest,
        expected_evaluation_ledger_binding_stage_names=expected_access_stages,
        final_evaluation_digest=FINAL_CONTENT_DIGEST,
        accessed_artifact_digests_by_stage=mismatched_content,
        expected_evaluation_content_stage_names=expected_access_stages,
        final_evaluation_artifact_id=FINAL_ARTIFACT_ID,
        accessed_artifact_ids_by_stage=clean_access,
        expected_evaluation_access_stage_names=expected_access_stages,
        selection_row_ids_by_stage=clean_selection,
        expected_selection_stage_names=expected_selection_stages,
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
    prior_failure = assess_state_forecast_v9(
        "prior-failure",
        conditional,
        marginal,
        covered,
        groups,
        blocks,
        artifact_digest_by_id=manifest,
        expected_evaluation_ledger_binding_stage_names=expected_access_stages,
        final_evaluation_digest=FINAL_CONTENT_DIGEST,
        accessed_artifact_digests_by_stage=mismatched_content,
        expected_evaluation_content_stage_names=expected_access_stages,
        final_evaluation_artifact_id=FINAL_ARTIFACT_ID,
        accessed_artifact_ids_by_stage=clean_access,
        expected_evaluation_access_stage_names=expected_access_stages,
        selection_row_ids_by_stage=clean_selection,
        expected_selection_stage_names=expected_selection_stages,
        **common_scheme,
        **v2_fragile_kwargs,
    )

    content_leak_ids = deepcopy(clean_access)
    content_leak_digests = deepcopy(clean_content)
    alias_id = "byte-identical-final-copy"
    manifest_with_copy = dict(manifest)
    manifest_with_copy[alias_id] = FINAL_CONTENT_DIGEST
    ids_rows = list(content_leak_ids["candidate_screening"])
    digest_rows = list(content_leak_digests["candidate_screening"])
    ids_rows[-1] = alias_id
    digest_rows[-1] = FINAL_CONTENT_DIGEST
    content_leak_ids["candidate_screening"] = tuple(ids_rows)
    content_leak_digests["candidate_screening"] = tuple(digest_rows)
    clean_binding_content_leak = assess_state_forecast_v9(
        "content-leakage",
        conditional,
        marginal,
        covered,
        groups,
        blocks,
        artifact_digest_by_id=manifest_with_copy,
        expected_evaluation_ledger_binding_stage_names=expected_access_stages,
        final_evaluation_digest=FINAL_CONTENT_DIGEST,
        accessed_artifact_digests_by_stage=content_leak_digests,
        expected_evaluation_content_stage_names=expected_access_stages,
        final_evaluation_artifact_id=FINAL_ARTIFACT_ID,
        accessed_artifact_ids_by_stage=content_leak_ids,
        expected_evaluation_access_stage_names=expected_access_stages,
        selection_row_ids_by_stage=clean_selection,
        expected_selection_stage_names=expected_selection_stages,
        **common_scheme,
        **v2_formal_kwargs,
    )

    direct_id_leak_ids = deepcopy(clean_access)
    direct_id_leak_digests = deepcopy(clean_content)
    id_rows = list(direct_id_leak_ids["model_review"])
    digest_rows = list(direct_id_leak_digests["model_review"])
    id_rows[-1] = FINAL_ARTIFACT_ID
    digest_rows[-1] = FINAL_CONTENT_DIGEST
    direct_id_leak_ids["model_review"] = tuple(id_rows)
    direct_id_leak_digests["model_review"] = tuple(digest_rows)
    clean_binding_direct_id_leak = assess_state_forecast_v9(
        "direct-id-leakage",
        conditional,
        marginal,
        covered,
        groups,
        blocks,
        artifact_digest_by_id=manifest,
        expected_evaluation_ledger_binding_stage_names=expected_access_stages,
        final_evaluation_digest=FINAL_CONTENT_DIGEST,
        accessed_artifact_digests_by_stage=direct_id_leak_digests,
        expected_evaluation_content_stage_names=expected_access_stages,
        final_evaluation_artifact_id=FINAL_ARTIFACT_ID,
        accessed_artifact_ids_by_stage=direct_id_leak_ids,
        expected_evaluation_access_stage_names=expected_access_stages,
        selection_row_ids_by_stage=clean_selection,
        expected_selection_stage_names=expected_selection_stages,
        **common_scheme,
        **v2_formal_kwargs,
    )

    leaking_selection = _selection_rows("leaking-selection")
    ranking = list(leaking_selection["candidate_ranking"])
    ranking[3] = base_ids[23]
    leaking_selection["candidate_ranking"] = tuple(ranking)
    clean_binding_selection_leak = assess_state_forecast_v9(
        "selection-leakage",
        conditional,
        marginal,
        covered,
        groups,
        blocks,
        **binding_args,
        final_evaluation_digest=FINAL_CONTENT_DIGEST,
        accessed_artifact_digests_by_stage=clean_content,
        expected_evaluation_content_stage_names=expected_access_stages,
        final_evaluation_artifact_id=FINAL_ARTIFACT_ID,
        accessed_artifact_ids_by_stage=clean_access,
        expected_evaluation_access_stage_names=expected_access_stages,
        selection_row_ids_by_stage=leaking_selection,
        expected_selection_stage_names=expected_selection_stages,
        **common_scheme,
        **v2_formal_kwargs,
    )

    leaking_training = deepcopy(clean_training)
    leaking_refit = ids["seed"][5]
    training_rows = list(leaking_training["seed"][leaking_refit])
    training_rows[2] = base_ids[17]
    leaking_training["seed"][leaking_refit] = tuple(training_rows)
    clean_binding_training_leak = assess_state_forecast_v9(
        "training-leakage",
        conditional,
        marginal,
        covered,
        groups,
        blocks,
        **binding_args,
        **full_provenance,
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
    clean_binding_row_mismatch = assess_state_forecast_v9(
        "row-mismatch",
        conditional,
        marginal,
        covered,
        groups,
        blocks,
        **binding_args,
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

    clean_binding_sensitive = assess_state_forecast_v9(
        "scheme-sensitive",
        conditional,
        marginal,
        covered,
        groups,
        blocks,
        **binding_args,
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

    mismatch_without_downstream = assess_state_forecast_v9(
        "binding-mismatch-no-lower-layers",
        conditional,
        marginal,
        covered,
        groups,
        blocks,
        artifact_digest_by_id=manifest,
        expected_evaluation_ledger_binding_stage_names=expected_access_stages,
        final_evaluation_digest=FINAL_CONTENT_DIGEST,
        accessed_artifact_digests_by_stage=mismatched_content,
        final_evaluation_artifact_id=FINAL_ARTIFACT_ID,
        accessed_artifact_ids_by_stage=clean_access,
        scheme_nested_draws=1200,
        scheme_seed=20260907,
        scheme_minimum_refits=8,
        **v2_formal_kwargs,
    )

    train_x = np.column_stack([np.linspace(-1, 1, 60), np.sin(np.linspace(-2, 2, 60))])
    query_x = np.asarray([[0.0, 0.0], [0.5, 0.2], [3.0, 0.0]])
    strict = assess_state_forecast_v9(
        "strict",
        conditional,
        marginal,
        covered,
        groups,
        blocks,
        **binding_args,
        **full_provenance,
        novelty_train_X=train_x,
        novelty_query_X=query_x,
        **common_scheme,
        **v2_formal_kwargs,
    )

    omitted_binding = assess_state_forecast_v9(
        "omitted-binding",
        conditional,
        marginal,
        covered,
        groups,
        blocks,
        **full_provenance,
        **common_scheme,
        **v2_formal_kwargs,
    )
    omitted_direct_v8 = assess_state_forecast_v8(
        "omitted-binding",
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
        "clean_binding_case_is_certified": clean.evaluation_ledger_binding is not None and clean.evaluation_ledger_binding.ledger_binding_consistent and clean.downstream_v8_assessment is not None and clean.v9_certification.certification_status == "certified",
        "content_access_selection_and_scheme_omitted_base_v8_result_is_preserved_exactly": clean.base_v8_assessment.as_dict() == direct_base_v8.as_dict(),
        "clean_binding_case_matches_direct_full_v8_result": clean.downstream_v8_assessment is not None and clean.downstream_v8_assessment.as_dict() == direct_full_v8.as_dict(),
        "ledger_binding_mismatch_makes_otherwise_certifiable_case_unavailable": binding_mismatch.base_v8_assessment.v8_certification.certification_status == "certified" and binding_mismatch.v9_certification.certification_status == "unavailable" and binding_mismatch.v9_certification.operational_status == "admitted_extended_unavailable",
        "ledger_binding_mismatch_prevents_downstream_v8_assessment": binding_mismatch.evaluation_ledger_binding is not None and binding_mismatch.evaluation_ledger_binding.separation_category == "evaluation_ledger_binding_mismatch" and binding_mismatch.downstream_v8_assessment is None and not binding_mismatch.settings["downstream_v8_assessment_run"],
        "ledger_binding_mismatch_is_only_new_provenance_blocker": binding_mismatch.v9_certification.provenance_blocking_reasons == ("evaluation_ledger_binding_mismatch",) and binding_mismatch.v9_certification.evaluation_content_provenance_status == "not_run_evaluation_ledger_binding_mismatch" and binding_mismatch.v9_certification.evaluation_access_provenance_status == "not_run_evaluation_ledger_binding_mismatch",
        "prior_base_v8_not_certified_is_not_rescued_by_binding_mismatch": prior_failure.base_v8_assessment.v8_certification.certification_status == "not_certified" and prior_failure.v9_certification.certification_status == "not_certified" and prior_failure.downstream_v8_assessment is None,
        "clean_binding_plus_content_leakage_inherits_v8_unavailable": clean_binding_content_leak.downstream_v8_assessment is not None and clean_binding_content_leak.downstream_v8_assessment.v8_certification.certification_status == "unavailable" and "final_evaluation_content_leakage" in clean_binding_content_leak.v9_certification.provenance_blocking_reasons,
        "clean_binding_plus_artifact_access_leakage_inherits_v8_unavailable": clean_binding_direct_id_leak.downstream_v8_assessment is not None and clean_binding_direct_id_leak.downstream_v8_assessment.v8_certification.certification_status == "unavailable" and "final_evaluation_content_leakage" in clean_binding_direct_id_leak.v9_certification.provenance_blocking_reasons,
        "clean_binding_plus_selection_leakage_inherits_v8_unavailable": clean_binding_selection_leak.downstream_v8_assessment is not None and clean_binding_selection_leak.downstream_v8_assessment.v8_certification.certification_status == "unavailable" and "selection_validation_leakage" in clean_binding_selection_leak.v9_certification.provenance_blocking_reasons,
        "clean_binding_plus_training_leakage_inherits_v8_unavailable": clean_binding_training_leak.downstream_v8_assessment is not None and clean_binding_training_leak.downstream_v8_assessment.v8_certification.certification_status == "unavailable" and "training_validation_leakage" in clean_binding_training_leak.v9_certification.provenance_blocking_reasons,
        "clean_binding_plus_row_mismatch_inherits_v8_unavailable": clean_binding_row_mismatch.downstream_v8_assessment is not None and clean_binding_row_mismatch.downstream_v8_assessment.v8_certification.certification_status == "unavailable" and "heldout_row_mismatch" in clean_binding_row_mismatch.v9_certification.provenance_blocking_reasons,
        "clean_binding_plus_scheme_sensitive_inherits_v8_not_certified": clean_binding_sensitive.downstream_v8_assessment is not None and clean_binding_sensitive.downstream_v8_assessment.v8_certification.certification_status == "not_certified" and "refit_scheme_sensitive" in clean_binding_sensitive.v9_certification.statistical_blocking_reasons,
        "binding_mismatch_without_downstream_layers_is_still_unavailable": mismatch_without_downstream.downstream_v8_assessment is None and mismatch_without_downstream.v9_certification.certification_status == "unavailable",
        "strict_extrapolation_remains_warning_under_clean_binding": strict.downstream_v8_assessment is not None and strict.v9_certification.certification_status == "certified" and strict.v9_certification.operational_status == "admitted_with_warnings" and "strict_extrapolation" in strict.v9_certification.warning_reasons and "environmental_novelty" in strict.v9_certification.warning_reasons,
        "omitted_binding_layer_preserves_direct_full_v8_result_and_certification": omitted_binding.evaluation_ledger_binding is None and omitted_binding.downstream_v8_assessment is not None and omitted_binding.downstream_v8_assessment.as_dict() == omitted_direct_v8.as_dict() and omitted_binding.v9_certification.certification_status == omitted_direct_v8.v8_certification.certification_status,
        "aggregate_confidence_score_emitted": all(not row.aggregate_confidence_score_emitted for row in (clean, binding_mismatch, prior_failure, clean_binding_content_leak, clean_binding_direct_id_leak, clean_binding_selection_leak, clean_binding_training_leak, clean_binding_row_mismatch, clean_binding_sensitive, mismatch_without_downstream, strict, omitted_binding)),
    }

    return {
        "seed": seed,
        "clean_binding": clean.as_dict(),
        "ledger_binding_mismatch": binding_mismatch.as_dict(),
        "prior_v8_failure_with_binding_mismatch": prior_failure.as_dict(),
        "clean_binding_content_leakage": clean_binding_content_leak.as_dict(),
        "clean_binding_direct_artifact_id_leakage": clean_binding_direct_id_leak.as_dict(),
        "clean_binding_selection_leakage": clean_binding_selection_leak.as_dict(),
        "clean_binding_training_leakage": clean_binding_training_leak.as_dict(),
        "clean_binding_row_mismatch": clean_binding_row_mismatch.as_dict(),
        "clean_binding_scheme_sensitive": clean_binding_sensitive.as_dict(),
        "binding_mismatch_without_downstream_layers": mismatch_without_downstream.as_dict(),
        "strict_extrapolation": strict.as_dict(),
        "omitted_binding": omitted_binding.as_dict(),
        "checks": [{"name": name, "passed": bool(value)} for name, value in checks.items()],
        "passed": bool(all(checks.values())),
    }
