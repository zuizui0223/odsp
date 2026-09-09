"""Known-truth benchmark for Forecast Assessment v6 selection provenance."""
from __future__ import annotations

from copy import deepcopy

import numpy as np

from .forecast_assessment_v3_benchmark import _base_design, _common_kwargs, _region
from .forecast_assessment_v4_benchmark import _provenance_ids, _scheme_inputs
from .forecast_assessment_v5 import assess_state_forecast_v5
from .forecast_assessment_v5_benchmark import _training_memberships
from .forecast_assessment_v6 import assess_state_forecast_v6


def _selection_rows(prefix: str = "selection") -> dict[str, tuple[str, ...]]:
    return {
        "candidate_ranking": tuple(f"{prefix}::rank::{i:02d}" for i in range(8)),
        "early_stopping": tuple(f"{prefix}::stop::{i:02d}" for i in range(6)),
        "hyperparameter_tuning": tuple(f"{prefix}::tune::{i:02d}" for i in range(10)),
    }


def run_forecast_assessment_v6_benchmark(*, seed: int = 20260907) -> dict[str, object]:
    if seed != 20260907:
        raise ValueError("the frozen Forecast Assessment v6 benchmark uses seed 20260907")

    gain, groups, blocks, covered, bootstrap, _fold, _seed, fragile, ids = _base_design()
    n = gain.size
    base_ids = tuple(f"validation-{idx:04d}" for idx in range(n))
    conditional = gain.copy()
    marginal = np.zeros(n)
    expected_stages = ("candidate_ranking", "early_stopping", "hyperparameter_tuning")
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

    clean = assess_state_forecast_v6(
        "strong",
        conditional,
        marginal,
        covered,
        groups,
        blocks,
        selection_row_ids_by_stage=clean_selection,
        expected_selection_stage_names=expected_stages,
        **common_scheme,
        **v2_formal_kwargs,
    )
    direct_full_v5 = assess_state_forecast_v5(
        "strong",
        conditional,
        marginal,
        covered,
        groups,
        blocks,
        **common_scheme,
        **v2_formal_kwargs,
    )
    direct_base_v5 = assess_state_forecast_v5(
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

    leaking_selection = _selection_rows("leaking-selection")
    rank_rows = list(leaking_selection["candidate_ranking"])
    rank_rows[3] = base_ids[23]
    leaking_selection["candidate_ranking"] = tuple(rank_rows)
    selection_leakage = assess_state_forecast_v6(
        "selection-leakage",
        conditional,
        marginal,
        covered,
        groups,
        blocks,
        selection_row_ids_by_stage=leaking_selection,
        expected_selection_stage_names=expected_stages,
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
    prior_failure = assess_state_forecast_v6(
        "prior-failure",
        conditional,
        marginal,
        covered,
        groups,
        blocks,
        selection_row_ids_by_stage=leaking_selection,
        expected_selection_stage_names=expected_stages,
        **common_scheme,
        **v2_fragile_kwargs,
    )

    leaking_training = deepcopy(clean_training)
    leaking_refit = ids["seed"][5]
    training_rows = list(leaking_training["seed"][leaking_refit])
    training_rows[2] = base_ids[17]
    leaking_training["seed"][leaking_refit] = tuple(training_rows)
    clean_selection_training_leak = assess_state_forecast_v6(
        "training-leakage",
        conditional,
        marginal,
        covered,
        groups,
        blocks,
        selection_row_ids_by_stage=clean_selection,
        expected_selection_stage_names=expected_stages,
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
    clean_selection_row_mismatch = assess_state_forecast_v6(
        "row-mismatch",
        conditional,
        marginal,
        covered,
        groups,
        blocks,
        selection_row_ids_by_stage=clean_selection,
        expected_selection_stage_names=expected_stages,
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

    clean_selection_sensitive = assess_state_forecast_v6(
        "scheme-sensitive",
        conditional,
        marginal,
        covered,
        groups,
        blocks,
        selection_row_ids_by_stage=clean_selection,
        expected_selection_stage_names=expected_stages,
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

    leak_without_scheme = assess_state_forecast_v6(
        "selection-leak-no-scheme",
        conditional,
        marginal,
        covered,
        groups,
        blocks,
        validation_row_ids=base_ids,
        selection_row_ids_by_stage=leaking_selection,
        expected_selection_stage_names=expected_stages,
        scheme_nested_draws=1200,
        scheme_seed=20260907,
        scheme_minimum_refits=8,
        **v2_formal_kwargs,
    )

    train_x = np.column_stack([np.linspace(-1, 1, 60), np.sin(np.linspace(-2, 2, 60))])
    query_x = np.asarray([[0.0, 0.0], [0.5, 0.2], [3.0, 0.0]])
    strict = assess_state_forecast_v6(
        "strict",
        conditional,
        marginal,
        covered,
        groups,
        blocks,
        selection_row_ids_by_stage=clean_selection,
        expected_selection_stage_names=expected_stages,
        novelty_train_X=train_x,
        novelty_query_X=query_x,
        **common_scheme,
        **v2_formal_kwargs,
    )

    omitted_selection = assess_state_forecast_v6(
        "omitted-selection",
        conditional,
        marginal,
        covered,
        groups,
        blocks,
        **common_scheme,
        **v2_formal_kwargs,
    )
    omitted_direct_v5 = assess_state_forecast_v5(
        "omitted-selection",
        conditional,
        marginal,
        covered,
        groups,
        blocks,
        **common_scheme,
        **v2_formal_kwargs,
    )

    cluster_means = np.asarray([-0.20, -0.10, 0.0, 0.05, 0.10, 0.15, 0.20, 0.25])
    cluster_rows = 40
    pseudo_group, pseudo_blocks, pseudo_alt, pseudo_gain = [], [], [], []
    for g in range(6):
        gid = f"group-{g:02d}"
        for c, mean in enumerate(cluster_means):
            for r in range(cluster_rows):
                pseudo_group.append(gid)
                pseudo_blocks.append(f"{gid}-row-{c * cluster_rows + r:04d}")
                pseudo_alt.append(f"{gid}-cluster-{c:02d}")
                pseudo_gain.append(float(mean))
    pseudo_gain = np.asarray(pseudo_gain)
    pseudo_group = tuple(pseudo_group)
    pseudo_blocks = tuple(pseudo_blocks)
    pseudo_alt = tuple(pseudo_alt)
    pseudo_covered = np.zeros(pseudo_gain.size, dtype=bool)
    labels = np.asarray(pseudo_group, dtype=object)
    for gid in tuple(dict.fromkeys(pseudo_group)):
        idx = np.flatnonzero(labels == gid)
        pseudo_covered[idx[: int(0.9 * idx.size)]] = True
    pseudo_refits = np.repeat(pseudo_gain[None, :], 12, axis=0)
    pseudo_refit_ids = {
        name: tuple(f"{name}-refit-{i:02d}" for i in range(12))
        for name in ("bootstrap", "fold", "seed")
    }
    pseudo_schemes = {name: pseudo_refits.copy() for name in pseudo_refit_ids}
    pseudo_ids = tuple(f"pseudo-{i:04d}" for i in range(pseudo_gain.size))
    pseudo_training = _training_memberships(pseudo_refit_ids)
    block_warning = assess_state_forecast_v6(
        "block-warning",
        pseudo_gain,
        np.zeros_like(pseudo_gain),
        pseudo_covered,
        pseudo_group,
        pseudo_blocks,
        region_size=_region(pseudo_gain.size),
        validation_gamma=1.0,
        bootstrap_draws=800,
        seed=20260907,
        minimum_blocks_per_group=8,
        alternative_block_definitions={"eight_cluster": pseudo_alt},
        validation_row_ids=pseudo_ids,
        selection_row_ids_by_stage=_selection_rows("pseudo-selection"),
        expected_selection_stage_names=expected_stages,
        refit_schemes=pseudo_schemes,
        validation_row_ids_by_scheme={name: pseudo_ids for name in pseudo_schemes},
        refit_ids_by_scheme=pseudo_refit_ids,
        reference_refit_ids_by_scheme={name: values[0] for name, values in pseudo_refit_ids.items()},
        training_row_ids_by_scheme=pseudo_training,
        scheme_nested_draws=1200,
        scheme_seed=20260907,
        scheme_minimum_refits=8,
    )

    checks = {
        "clean_selection_case_is_certified": clean.selection_validation_provenance is not None and clean.selection_validation_provenance.selection_validation_separated and clean.downstream_v5_assessment is not None and clean.v6_certification.certification_status == "certified",
        "scheme_omitted_base_v5_result_is_preserved_exactly": clean.base_v5_assessment.as_dict() == direct_base_v5.as_dict(),
        "clean_selection_case_matches_direct_full_v5_result": clean.downstream_v5_assessment is not None and clean.downstream_v5_assessment.as_dict() == direct_full_v5.as_dict(),
        "selection_leakage_makes_otherwise_certifiable_case_unavailable": selection_leakage.base_v5_assessment.v5_certification.certification_status == "certified" and selection_leakage.v6_certification.certification_status == "unavailable" and selection_leakage.v6_certification.operational_status == "admitted_extended_unavailable",
        "selection_leakage_prevents_downstream_v5_assessment": selection_leakage.selection_validation_provenance is not None and selection_leakage.selection_validation_provenance.separation_category == "selection_validation_leakage" and selection_leakage.downstream_v5_assessment is None and not selection_leakage.settings["downstream_v5_assessment_run"],
        "selection_leakage_is_only_new_provenance_blocker": selection_leakage.v6_certification.provenance_blocking_reasons == ("selection_validation_leakage",) and selection_leakage.v6_certification.training_validation_provenance_status == "not_run_selection_validation_leakage" and not any(reason.startswith("refit_scheme") or reason.startswith("training_validation") for reason in selection_leakage.v6_certification.statistical_blocking_reasons),
        "prior_base_v5_not_certified_is_not_rescued_by_selection_leakage": prior_failure.base_v5_assessment.v5_certification.certification_status == "not_certified" and prior_failure.v6_certification.certification_status == "not_certified" and prior_failure.downstream_v5_assessment is None,
        "clean_selection_plus_training_leakage_inherits_v5_unavailable": clean_selection_training_leak.downstream_v5_assessment is not None and clean_selection_training_leak.downstream_v5_assessment.v5_certification.certification_status == "unavailable" and clean_selection_training_leak.v6_certification.certification_status == "unavailable" and "training_validation_leakage" in clean_selection_training_leak.v6_certification.provenance_blocking_reasons,
        "clean_selection_plus_row_mismatch_inherits_v5_unavailable": clean_selection_row_mismatch.downstream_v5_assessment is not None and clean_selection_row_mismatch.downstream_v5_assessment.v5_certification.certification_status == "unavailable" and clean_selection_row_mismatch.v6_certification.certification_status == "unavailable" and "heldout_row_mismatch" in clean_selection_row_mismatch.v6_certification.provenance_blocking_reasons,
        "clean_selection_plus_scheme_sensitive_inherits_v5_not_certified": clean_selection_sensitive.downstream_v5_assessment is not None and clean_selection_sensitive.downstream_v5_assessment.v5_certification.certification_status == "not_certified" and clean_selection_sensitive.v6_certification.certification_status == "not_certified",
        "selection_leakage_without_scheme_layer_is_still_unavailable": leak_without_scheme.base_v5_assessment.v5_certification.certification_status == "certified" and leak_without_scheme.downstream_v5_assessment is None and leak_without_scheme.v6_certification.certification_status == "unavailable",
        "strict_extrapolation_remains_warning_under_clean_selection_provenance": strict.downstream_v5_assessment is not None and strict.v6_certification.certification_status == "certified" and strict.v6_certification.operational_status == "admitted_with_warnings" and "strict_extrapolation" in strict.v6_certification.warning_reasons,
        "omitted_selection_layer_preserves_direct_full_v5_result_and_certification": omitted_selection.selection_validation_provenance is None and omitted_selection.downstream_v5_assessment is not None and omitted_selection.downstream_v5_assessment.as_dict() == omitted_direct_v5.as_dict() and omitted_selection.v6_certification.certification_status == omitted_direct_v5.v5_certification.certification_status,
        "block_definition_warning_remains_warning_under_clean_selection_provenance": block_warning.selection_validation_provenance is not None and block_warning.selection_validation_provenance.selection_validation_separated and block_warning.downstream_v5_assessment is not None and block_warning.v6_certification.certification_status == "certified" and "block_definition_sensitive" in block_warning.v6_certification.warning_reasons,
        "aggregate_confidence_score_emitted": all(not row.aggregate_confidence_score_emitted for row in (clean, selection_leakage, prior_failure, clean_selection_training_leak, clean_selection_row_mismatch, clean_selection_sensitive, leak_without_scheme, strict, omitted_selection, block_warning)),
    }

    return {
        "seed": seed,
        "clean_selection": clean.as_dict(),
        "selection_leakage": selection_leakage.as_dict(),
        "prior_v5_failure_with_selection_leakage": prior_failure.as_dict(),
        "clean_selection_training_leakage": clean_selection_training_leak.as_dict(),
        "clean_selection_row_mismatch": clean_selection_row_mismatch.as_dict(),
        "clean_selection_scheme_sensitive": clean_selection_sensitive.as_dict(),
        "selection_leakage_without_scheme": leak_without_scheme.as_dict(),
        "strict_extrapolation": strict.as_dict(),
        "omitted_selection": omitted_selection.as_dict(),
        "block_definition_warning": block_warning.as_dict(),
        "checks": [{"name": name, "passed": bool(value)} for name, value in checks.items()],
        "passed": bool(all(checks.values())),
    }
