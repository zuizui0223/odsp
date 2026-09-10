"""Known-truth benchmark for Forecast Assessment v8 exact-content provenance."""
from __future__ import annotations

from copy import deepcopy
from hashlib import sha256

import numpy as np

from .forecast_assessment_v3_benchmark import _base_design, _common_kwargs, _region
from .forecast_assessment_v4_benchmark import _provenance_ids, _scheme_inputs
from .forecast_assessment_v5_benchmark import _training_memberships
from .forecast_assessment_v6_benchmark import _selection_rows
from .forecast_assessment_v7 import assess_state_forecast_v7
from .forecast_assessment_v7_benchmark import FINAL_ARTIFACT_ID, _clean_access
from .forecast_assessment_v8 import assess_state_forecast_v8


FINAL_CONTENT_DIGEST = "sha256:" + sha256(b"final-evaluation-content-v8").hexdigest()


def _digest(label: str) -> str:
    return "sha256:" + sha256(label.encode("utf-8")).hexdigest()


def _clean_content(prefix: str = "content") -> dict[str, tuple[str, ...]]:
    return {
        "candidate_screening": (
            _digest(f"{prefix}::candidate-summary"),
            _digest(f"{prefix}::feature-diagnostics"),
        ),
        "model_review": (
            _digest(f"{prefix}::training-report"),
            _digest(f"{prefix}::calibration-report"),
        ),
        "threshold_review": (
            _digest(f"{prefix}::development-thresholds"),
            _digest(f"{prefix}::selection-notes"),
        ),
    }


def run_forecast_assessment_v8_benchmark(*, seed: int = 20260910) -> dict[str, object]:
    if seed != 20260910:
        raise ValueError("the frozen Forecast Assessment v8 benchmark uses seed 20260910")

    gain, groups, blocks, covered, bootstrap, _fold, _seed, fragile, ids = _base_design()
    n = gain.size
    base_ids = tuple(f"validation-{idx:04d}" for idx in range(n))
    conditional = gain.copy()
    marginal = np.zeros(n)

    expected_content_stages = ("candidate_screening", "model_review", "threshold_review")
    clean_content = _clean_content()
    expected_access_stages = ("candidate_screening", "model_review", "threshold_review")
    clean_access = _clean_access()
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
    full_v7_provenance = dict(
        final_evaluation_artifact_id=FINAL_ARTIFACT_ID,
        accessed_artifact_ids_by_stage=clean_access,
        expected_evaluation_access_stage_names=expected_access_stages,
        selection_row_ids_by_stage=clean_selection,
        expected_selection_stage_names=expected_selection_stages,
    )
    clean_content_args = dict(
        final_evaluation_digest=FINAL_CONTENT_DIGEST,
        accessed_artifact_digests_by_stage=clean_content,
        expected_evaluation_content_stage_names=expected_content_stages,
    )

    clean = assess_state_forecast_v8(
        "strong",
        conditional,
        marginal,
        covered,
        groups,
        blocks,
        **clean_content_args,
        **full_v7_provenance,
        **common_scheme,
        **v2_formal_kwargs,
    )
    direct_full_v7 = assess_state_forecast_v7(
        "strong",
        conditional,
        marginal,
        covered,
        groups,
        blocks,
        **full_v7_provenance,
        **common_scheme,
        **v2_formal_kwargs,
    )
    direct_base_v7 = assess_state_forecast_v7(
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

    leaking_content = _clean_content("leaking-content")
    screening_content = list(leaking_content["candidate_screening"])
    screening_content[1] = FINAL_CONTENT_DIGEST
    leaking_content["candidate_screening"] = tuple(screening_content)
    content_leakage = assess_state_forecast_v8(
        "content-leakage",
        conditional,
        marginal,
        covered,
        groups,
        blocks,
        final_evaluation_digest=FINAL_CONTENT_DIGEST,
        accessed_artifact_digests_by_stage=leaking_content,
        expected_evaluation_content_stage_names=expected_content_stages,
        **full_v7_provenance,
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
    prior_failure = assess_state_forecast_v8(
        "prior-failure",
        conditional,
        marginal,
        covered,
        groups,
        blocks,
        final_evaluation_digest=FINAL_CONTENT_DIGEST,
        accessed_artifact_digests_by_stage=leaking_content,
        expected_evaluation_content_stage_names=expected_content_stages,
        **full_v7_provenance,
        **common_scheme,
        **v2_fragile_kwargs,
    )

    leaking_access = _clean_access("leaking-access")
    screening_access = list(leaking_access["candidate_screening"])
    screening_access[1] = FINAL_ARTIFACT_ID
    leaking_access["candidate_screening"] = tuple(screening_access)
    clean_content_access_leak = assess_state_forecast_v8(
        "artifact-access-leakage",
        conditional,
        marginal,
        covered,
        groups,
        blocks,
        **clean_content_args,
        final_evaluation_artifact_id=FINAL_ARTIFACT_ID,
        accessed_artifact_ids_by_stage=leaking_access,
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
    clean_content_selection_leak = assess_state_forecast_v8(
        "selection-leakage",
        conditional,
        marginal,
        covered,
        groups,
        blocks,
        **clean_content_args,
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
    clean_content_training_leak = assess_state_forecast_v8(
        "training-leakage",
        conditional,
        marginal,
        covered,
        groups,
        blocks,
        **clean_content_args,
        **full_v7_provenance,
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
    clean_content_row_mismatch = assess_state_forecast_v8(
        "row-mismatch",
        conditional,
        marginal,
        covered,
        groups,
        blocks,
        **clean_content_args,
        **full_v7_provenance,
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

    clean_content_sensitive = assess_state_forecast_v8(
        "scheme-sensitive",
        conditional,
        marginal,
        covered,
        groups,
        blocks,
        **clean_content_args,
        **full_v7_provenance,
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

    leak_without_downstream_layers = assess_state_forecast_v8(
        "content-leak-no-downstream-layers",
        conditional,
        marginal,
        covered,
        groups,
        blocks,
        final_evaluation_digest=FINAL_CONTENT_DIGEST,
        accessed_artifact_digests_by_stage=leaking_content,
        expected_evaluation_content_stage_names=expected_content_stages,
        scheme_nested_draws=1200,
        scheme_seed=20260907,
        scheme_minimum_refits=8,
        **v2_formal_kwargs,
    )

    train_x = np.column_stack([np.linspace(-1, 1, 60), np.sin(np.linspace(-2, 2, 60))])
    query_x = np.asarray([[0.0, 0.0], [0.5, 0.2], [3.0, 0.0]])
    strict = assess_state_forecast_v8(
        "strict",
        conditional,
        marginal,
        covered,
        groups,
        blocks,
        **clean_content_args,
        **full_v7_provenance,
        novelty_train_X=train_x,
        novelty_query_X=query_x,
        **common_scheme,
        **v2_formal_kwargs,
    )

    omitted_content = assess_state_forecast_v8(
        "omitted-content",
        conditional,
        marginal,
        covered,
        groups,
        blocks,
        **full_v7_provenance,
        **common_scheme,
        **v2_formal_kwargs,
    )
    omitted_direct_v7 = assess_state_forecast_v7(
        "omitted-content",
        conditional,
        marginal,
        covered,
        groups,
        blocks,
        **full_v7_provenance,
        **common_scheme,
        **v2_formal_kwargs,
    )

    checks = {
        "clean_content_case_is_certified": clean.evaluation_content_provenance is not None and not clean.evaluation_content_provenance.final_evaluation_content_accessed and clean.downstream_v7_assessment is not None and clean.v8_certification.certification_status == "certified",
        "base_v7_result_is_preserved_exactly": clean.base_v7_assessment.as_dict() == direct_base_v7.as_dict(),
        "clean_content_case_matches_direct_full_v7_result": clean.downstream_v7_assessment is not None and clean.downstream_v7_assessment.as_dict() == direct_full_v7.as_dict(),
        "content_leakage_makes_otherwise_certifiable_case_unavailable": content_leakage.base_v7_assessment.v7_certification.certification_status == "certified" and content_leakage.v8_certification.certification_status == "unavailable" and content_leakage.v8_certification.operational_status == "admitted_extended_unavailable",
        "content_leakage_prevents_downstream_v7_assessment": content_leakage.evaluation_content_provenance is not None and content_leakage.evaluation_content_provenance.separation_category == "final_evaluation_content_leakage" and content_leakage.downstream_v7_assessment is None and not content_leakage.settings["downstream_v7_assessment_run"],
        "content_leakage_is_only_new_provenance_blocker": content_leakage.v8_certification.provenance_blocking_reasons == ("final_evaluation_content_leakage",) and content_leakage.v8_certification.evaluation_access_provenance_status == "not_run_final_evaluation_content_leakage" and content_leakage.v8_certification.selection_validation_provenance_status == "not_run_final_evaluation_content_leakage" and not content_leakage.v8_certification.statistical_blocking_reasons,
        "prior_base_v7_not_certified_is_not_rescued_by_content_leakage": prior_failure.base_v7_assessment.v7_certification.certification_status == "not_certified" and prior_failure.v8_certification.certification_status == "not_certified" and prior_failure.downstream_v7_assessment is None,
        "clean_content_plus_artifact_access_leakage_inherits_v7_unavailable": clean_content_access_leak.downstream_v7_assessment is not None and clean_content_access_leak.downstream_v7_assessment.v7_certification.certification_status == "unavailable" and clean_content_access_leak.v8_certification.certification_status == "unavailable" and "final_evaluation_access_leakage" in clean_content_access_leak.v8_certification.provenance_blocking_reasons,
        "clean_content_plus_selection_leakage_inherits_v7_unavailable": clean_content_selection_leak.downstream_v7_assessment is not None and clean_content_selection_leak.downstream_v7_assessment.v7_certification.certification_status == "unavailable" and clean_content_selection_leak.v8_certification.certification_status == "unavailable" and "selection_validation_leakage" in clean_content_selection_leak.v8_certification.provenance_blocking_reasons,
        "clean_content_plus_training_leakage_inherits_v7_unavailable": clean_content_training_leak.downstream_v7_assessment is not None and clean_content_training_leak.downstream_v7_assessment.v7_certification.certification_status == "unavailable" and clean_content_training_leak.v8_certification.certification_status == "unavailable" and "training_validation_leakage" in clean_content_training_leak.v8_certification.provenance_blocking_reasons,
        "clean_content_plus_row_mismatch_inherits_v7_unavailable": clean_content_row_mismatch.downstream_v7_assessment is not None and clean_content_row_mismatch.downstream_v7_assessment.v7_certification.certification_status == "unavailable" and clean_content_row_mismatch.v8_certification.certification_status == "unavailable" and "heldout_row_mismatch" in clean_content_row_mismatch.v8_certification.provenance_blocking_reasons,
        "clean_content_plus_scheme_sensitive_inherits_v7_not_certified": clean_content_sensitive.downstream_v7_assessment is not None and clean_content_sensitive.downstream_v7_assessment.v7_certification.certification_status == "not_certified" and clean_content_sensitive.v8_certification.certification_status == "not_certified" and "refit_scheme_sensitive" in clean_content_sensitive.v8_certification.statistical_blocking_reasons,
        "content_leakage_without_downstream_layers_is_still_unavailable": leak_without_downstream_layers.base_v7_assessment.v7_certification.certification_status == "certified" and leak_without_downstream_layers.downstream_v7_assessment is None and leak_without_downstream_layers.v8_certification.certification_status == "unavailable",
        "strict_extrapolation_remains_warning_under_clean_content_provenance": strict.downstream_v7_assessment is not None and strict.v8_certification.certification_status == "certified" and strict.v8_certification.operational_status == "admitted_with_warnings" and "strict_extrapolation" in strict.v8_certification.warning_reasons and "environmental_novelty" in strict.v8_certification.warning_reasons,
        "omitted_content_layer_preserves_direct_full_v7_result_and_certification": omitted_content.evaluation_content_provenance is None and omitted_content.downstream_v7_assessment is not None and omitted_content.downstream_v7_assessment.as_dict() == omitted_direct_v7.as_dict() and omitted_content.v8_certification.certification_status == omitted_direct_v7.v7_certification.certification_status,
        "aggregate_confidence_score_emitted": all(not row.aggregate_confidence_score_emitted for row in (clean, content_leakage, prior_failure, clean_content_access_leak, clean_content_selection_leak, clean_content_training_leak, clean_content_row_mismatch, clean_content_sensitive, leak_without_downstream_layers, strict, omitted_content)),
    }

    return {
        "seed": seed,
        "clean_content": clean.as_dict(),
        "final_evaluation_content_leakage": content_leakage.as_dict(),
        "prior_v7_failure_with_content_leakage": prior_failure.as_dict(),
        "clean_content_artifact_access_leakage": clean_content_access_leak.as_dict(),
        "clean_content_selection_leakage": clean_content_selection_leak.as_dict(),
        "clean_content_training_leakage": clean_content_training_leak.as_dict(),
        "clean_content_row_mismatch": clean_content_row_mismatch.as_dict(),
        "clean_content_scheme_sensitive": clean_content_sensitive.as_dict(),
        "content_leakage_without_downstream_layers": leak_without_downstream_layers.as_dict(),
        "strict_extrapolation": strict.as_dict(),
        "omitted_content": omitted_content.as_dict(),
        "checks": [{"name": name, "passed": bool(value)} for name, value in checks.items()],
        "passed": bool(all(checks.values())),
    }
