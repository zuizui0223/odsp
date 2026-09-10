"""Known-truth benchmark for Forecast Assessment v7 evaluation-access provenance."""
from __future__ import annotations

from copy import deepcopy

import numpy as np

from .forecast_assessment_v3_benchmark import _base_design, _common_kwargs, _region
from .forecast_assessment_v4_benchmark import _provenance_ids, _scheme_inputs
from .forecast_assessment_v5_benchmark import _training_memberships
from .forecast_assessment_v6 import assess_state_forecast_v6
from .forecast_assessment_v6_benchmark import _selection_rows
from .forecast_assessment_v7 import assess_state_forecast_v7


FINAL_ARTIFACT_ID = "final-evaluation::forecast-v7::frozen"


def _clean_access(prefix: str = "access") -> dict[str, tuple[str, ...]]:
    return {
        "candidate_screening": (
            f"{prefix}::candidate-summary",
            f"{prefix}::feature-diagnostics",
        ),
        "model_review": (
            f"{prefix}::training-report",
            f"{prefix}::calibration-report",
        ),
        "threshold_review": (
            f"{prefix}::development-thresholds",
            f"{prefix}::selection-notes",
        ),
    }


def run_forecast_assessment_v7_benchmark(*, seed: int = 20260910) -> dict[str, object]:
    if seed != 20260910:
        raise ValueError("the frozen Forecast Assessment v7 benchmark uses seed 20260910")

    gain, groups, blocks, covered, bootstrap, _fold, _seed, fragile, ids = _base_design()
    n = gain.size
    base_ids = tuple(f"validation-{idx:04d}" for idx in range(n))
    conditional = gain.copy()
    marginal = np.zeros(n)

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

    clean = assess_state_forecast_v7(
        "strong",
        conditional,
        marginal,
        covered,
        groups,
        blocks,
        final_evaluation_artifact_id=FINAL_ARTIFACT_ID,
        accessed_artifact_ids_by_stage=clean_access,
        expected_evaluation_access_stage_names=expected_access_stages,
        selection_row_ids_by_stage=clean_selection,
        expected_selection_stage_names=expected_selection_stages,
        **common_scheme,
        **v2_formal_kwargs,
    )
    direct_full_v6 = assess_state_forecast_v6(
        "strong",
        conditional,
        marginal,
        covered,
        groups,
        blocks,
        selection_row_ids_by_stage=clean_selection,
        expected_selection_stage_names=expected_selection_stages,
        **common_scheme,
        **v2_formal_kwargs,
    )
    direct_base_v6 = assess_state_forecast_v6(
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

    leaking_access = _clean_access("leaking-access")
    screening = list(leaking_access["candidate_screening"])
    screening[1] = FINAL_ARTIFACT_ID
    leaking_access["candidate_screening"] = tuple(screening)
    access_leakage = assess_state_forecast_v7(
        "access-leakage",
        conditional,
        marginal,
        covered,
        groups,
        blocks,
        final_evaluation_artifact_id=FINAL_ARTIFACT_ID,
        accessed_artifact_ids_by_stage=leaking_access,
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
    prior_failure = assess_state_forecast_v7(
        "prior-failure",
        conditional,
        marginal,
        covered,
        groups,
        blocks,
        final_evaluation_artifact_id=FINAL_ARTIFACT_ID,
        accessed_artifact_ids_by_stage=leaking_access,
        expected_evaluation_access_stage_names=expected_access_stages,
        selection_row_ids_by_stage=clean_selection,
        expected_selection_stage_names=expected_selection_stages,
        **common_scheme,
        **v2_fragile_kwargs,
    )

    leaking_selection = _selection_rows("leaking-selection")
    ranking = list(leaking_selection["candidate_ranking"])
    ranking[3] = base_ids[23]
    leaking_selection["candidate_ranking"] = tuple(ranking)
    clean_access_selection_leak = assess_state_forecast_v7(
        "selection-leakage",
        conditional,
        marginal,
        covered,
        groups,
        blocks,
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
    clean_access_training_leak = assess_state_forecast_v7(
        "training-leakage",
        conditional,
        marginal,
        covered,
        groups,
        blocks,
        final_evaluation_artifact_id=FINAL_ARTIFACT_ID,
        accessed_artifact_ids_by_stage=clean_access,
        expected_evaluation_access_stage_names=expected_access_stages,
        validation_row_ids=base_ids,
        selection_row_ids_by_stage=clean_selection,
        expected_selection_stage_names=expected_selection_stages,
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
    clean_access_row_mismatch = assess_state_forecast_v7(
        "row-mismatch",
        conditional,
        marginal,
        covered,
        groups,
        blocks,
        final_evaluation_artifact_id=FINAL_ARTIFACT_ID,
        accessed_artifact_ids_by_stage=clean_access,
        expected_evaluation_access_stage_names=expected_access_stages,
        validation_row_ids=base_ids,
        selection_row_ids_by_stage=clean_selection,
        expected_selection_stage_names=expected_selection_stages,
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

    clean_access_sensitive = assess_state_forecast_v7(
        "scheme-sensitive",
        conditional,
        marginal,
        covered,
        groups,
        blocks,
        final_evaluation_artifact_id=FINAL_ARTIFACT_ID,
        accessed_artifact_ids_by_stage=clean_access,
        expected_evaluation_access_stage_names=expected_access_stages,
        validation_row_ids=base_ids,
        selection_row_ids_by_stage=clean_selection,
        expected_selection_stage_names=expected_selection_stages,
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

    leak_without_downstream_layers = assess_state_forecast_v7(
        "access-leak-no-downstream-layers",
        conditional,
        marginal,
        covered,
        groups,
        blocks,
        final_evaluation_artifact_id=FINAL_ARTIFACT_ID,
        accessed_artifact_ids_by_stage=leaking_access,
        expected_evaluation_access_stage_names=expected_access_stages,
        scheme_nested_draws=1200,
        scheme_seed=20260907,
        scheme_minimum_refits=8,
        **v2_formal_kwargs,
    )

    train_x = np.column_stack([np.linspace(-1, 1, 60), np.sin(np.linspace(-2, 2, 60))])
    query_x = np.asarray([[0.0, 0.0], [0.5, 0.2], [3.0, 0.0]])
    strict = assess_state_forecast_v7(
        "strict",
        conditional,
        marginal,
        covered,
        groups,
        blocks,
        final_evaluation_artifact_id=FINAL_ARTIFACT_ID,
        accessed_artifact_ids_by_stage=clean_access,
        expected_evaluation_access_stage_names=expected_access_stages,
        selection_row_ids_by_stage=clean_selection,
        expected_selection_stage_names=expected_selection_stages,
        novelty_train_X=train_x,
        novelty_query_X=query_x,
        **common_scheme,
        **v2_formal_kwargs,
    )

    omitted_access = assess_state_forecast_v7(
        "omitted-access",
        conditional,
        marginal,
        covered,
        groups,
        blocks,
        selection_row_ids_by_stage=clean_selection,
        expected_selection_stage_names=expected_selection_stages,
        **common_scheme,
        **v2_formal_kwargs,
    )
    omitted_direct_v6 = assess_state_forecast_v6(
        "omitted-access",
        conditional,
        marginal,
        covered,
        groups,
        blocks,
        selection_row_ids_by_stage=clean_selection,
        expected_selection_stage_names=expected_selection_stages,
        **common_scheme,
        **v2_formal_kwargs,
    )

    checks = {
        "clean_access_case_is_certified": clean.evaluation_access_provenance is not None and not clean.evaluation_access_provenance.final_evaluation_accessed and clean.downstream_v6_assessment is not None and clean.v7_certification.certification_status == "certified",
        "selection_and_scheme_omitted_base_v6_result_is_preserved_exactly": clean.base_v6_assessment.as_dict() == direct_base_v6.as_dict(),
        "clean_access_case_matches_direct_full_v6_result": clean.downstream_v6_assessment is not None and clean.downstream_v6_assessment.as_dict() == direct_full_v6.as_dict(),
        "final_evaluation_access_leakage_makes_otherwise_certifiable_case_unavailable": access_leakage.base_v6_assessment.v6_certification.certification_status == "certified" and access_leakage.v7_certification.certification_status == "unavailable" and access_leakage.v7_certification.operational_status == "admitted_extended_unavailable",
        "final_evaluation_access_leakage_prevents_downstream_v6_assessment": access_leakage.evaluation_access_provenance is not None and access_leakage.evaluation_access_provenance.separation_category == "final_evaluation_access_leakage" and access_leakage.downstream_v6_assessment is None and not access_leakage.settings["downstream_v6_assessment_run"],
        "final_evaluation_access_leakage_is_only_new_provenance_blocker": access_leakage.v7_certification.provenance_blocking_reasons == ("final_evaluation_access_leakage",) and access_leakage.v7_certification.selection_validation_provenance_status == "not_run_final_evaluation_access_leakage" and access_leakage.v7_certification.training_validation_provenance_status == "not_run_final_evaluation_access_leakage" and not any(reason.startswith("selection_validation") or reason.startswith("training_validation") or reason.startswith("refit_scheme") for reason in access_leakage.v7_certification.statistical_blocking_reasons),
        "prior_base_v6_not_certified_is_not_rescued_by_access_leakage": prior_failure.base_v6_assessment.v6_certification.certification_status == "not_certified" and prior_failure.v7_certification.certification_status == "not_certified" and prior_failure.downstream_v6_assessment is None,
        "clean_access_plus_selection_leakage_inherits_v6_unavailable": clean_access_selection_leak.downstream_v6_assessment is not None and clean_access_selection_leak.downstream_v6_assessment.v6_certification.certification_status == "unavailable" and clean_access_selection_leak.v7_certification.certification_status == "unavailable" and "selection_validation_leakage" in clean_access_selection_leak.v7_certification.provenance_blocking_reasons,
        "clean_access_plus_training_leakage_inherits_v6_unavailable": clean_access_training_leak.downstream_v6_assessment is not None and clean_access_training_leak.downstream_v6_assessment.v6_certification.certification_status == "unavailable" and clean_access_training_leak.v7_certification.certification_status == "unavailable" and "training_validation_leakage" in clean_access_training_leak.v7_certification.provenance_blocking_reasons,
        "clean_access_plus_row_mismatch_inherits_v6_unavailable": clean_access_row_mismatch.downstream_v6_assessment is not None and clean_access_row_mismatch.downstream_v6_assessment.v6_certification.certification_status == "unavailable" and clean_access_row_mismatch.v7_certification.certification_status == "unavailable" and "heldout_row_mismatch" in clean_access_row_mismatch.v7_certification.provenance_blocking_reasons,
        "clean_access_plus_scheme_sensitive_inherits_v6_not_certified": clean_access_sensitive.downstream_v6_assessment is not None and clean_access_sensitive.downstream_v6_assessment.v6_certification.certification_status == "not_certified" and clean_access_sensitive.v7_certification.certification_status == "not_certified" and "refit_scheme_sensitive" in clean_access_sensitive.v7_certification.statistical_blocking_reasons,
        "access_leakage_without_selection_or_scheme_layers_is_still_unavailable": leak_without_downstream_layers.base_v6_assessment.v6_certification.certification_status == "certified" and leak_without_downstream_layers.downstream_v6_assessment is None and leak_without_downstream_layers.v7_certification.certification_status == "unavailable",
        "strict_extrapolation_remains_warning_under_clean_evaluation_access_provenance": strict.downstream_v6_assessment is not None and strict.v7_certification.certification_status == "certified" and strict.v7_certification.operational_status == "admitted_with_warnings" and "strict_extrapolation" in strict.v7_certification.warning_reasons and "environmental_novelty" in strict.v7_certification.warning_reasons,
        "omitted_evaluation_access_layer_preserves_direct_full_v6_result_and_certification": omitted_access.evaluation_access_provenance is None and omitted_access.downstream_v6_assessment is not None and omitted_access.downstream_v6_assessment.as_dict() == omitted_direct_v6.as_dict() and omitted_access.v7_certification.certification_status == omitted_direct_v6.v6_certification.certification_status,
        "aggregate_confidence_score_emitted": all(not row.aggregate_confidence_score_emitted for row in (clean, access_leakage, prior_failure, clean_access_selection_leak, clean_access_training_leak, clean_access_row_mismatch, clean_access_sensitive, leak_without_downstream_layers, strict, omitted_access)),
    }

    return {
        "seed": seed,
        "clean_access": clean.as_dict(),
        "final_evaluation_access_leakage": access_leakage.as_dict(),
        "prior_v6_failure_with_access_leakage": prior_failure.as_dict(),
        "clean_access_selection_leakage": clean_access_selection_leak.as_dict(),
        "clean_access_training_leakage": clean_access_training_leak.as_dict(),
        "clean_access_row_mismatch": clean_access_row_mismatch.as_dict(),
        "clean_access_scheme_sensitive": clean_access_sensitive.as_dict(),
        "access_leakage_without_selection_or_scheme": leak_without_downstream_layers.as_dict(),
        "strict_extrapolation": strict.as_dict(),
        "omitted_evaluation_access": omitted_access.as_dict(),
        "checks": [{"name": name, "passed": bool(value)} for name, value in checks.items()],
        "passed": bool(all(checks.values())),
    }
