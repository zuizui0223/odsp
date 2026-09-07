"""Known-truth benchmark for Forecast Assessment v5 training provenance."""
from __future__ import annotations

from copy import deepcopy

import numpy as np

from .forecast_assessment_v3_benchmark import _base_design, _common_kwargs, _region
from .forecast_assessment_v4 import assess_state_forecast_v4
from .forecast_assessment_v4_benchmark import _provenance_ids, _scheme_inputs
from .forecast_assessment_v5 import assess_state_forecast_v5


def _training_memberships(refit_ids_by_scheme):
    return {
        scheme: {
            str(refit_id): tuple(
                f"train::{scheme}::{refit_id}::row-{j:02d}" for j in range(6)
            )
            for refit_id in refit_ids
        }
        for scheme, refit_ids in refit_ids_by_scheme.items()
    }


def run_forecast_assessment_v5_benchmark(*, seed: int = 20260907) -> dict[str, object]:
    if seed != 20260907:
        raise ValueError("the frozen Forecast Assessment v5 benchmark uses seed 20260907")

    gain, groups, blocks, covered, bootstrap, _fold, _seed, fragile, ids = _base_design()
    n = gain.size
    base_ids = tuple(f"validation-{idx:04d}" for idx in range(n))
    conditional = gain.copy()
    marginal = np.zeros(n)

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

    clean_exact = assess_state_forecast_v5(
        "strong",
        conditional,
        marginal,
        covered,
        groups,
        blocks,
        validation_row_ids=base_ids,
        validation_row_ids_by_scheme=_provenance_ids(base_ids, robust_schemes),
        refit_schemes=robust_schemes,
        refit_ids_by_scheme=robust_ids,
        reference_refit_ids_by_scheme=robust_refs,
        training_row_ids_by_scheme=clean_training,
        scheme_nested_draws=1200,
        scheme_seed=20260907,
        scheme_minimum_refits=8,
        **v2_formal_kwargs,
    )
    direct_v4_exact = assess_state_forecast_v4(
        "strong",
        conditional,
        marginal,
        covered,
        groups,
        blocks,
        validation_row_ids=base_ids,
        validation_row_ids_by_scheme=_provenance_ids(base_ids, robust_schemes),
        refit_schemes=robust_schemes,
        refit_ids_by_scheme=robust_ids,
        reference_refit_ids_by_scheme=robust_refs,
        scheme_nested_draws=1200,
        scheme_seed=20260907,
        scheme_minimum_refits=8,
        **v2_formal_kwargs,
    )
    direct_v4_omitted = assess_state_forecast_v4(
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

    orders = {
        "bootstrap": np.arange(n),
        "fold": np.roll(np.arange(n), 47),
        "seed": np.random.default_rng(91531).permutation(n),
    }
    permuted_schemes = {
        name: matrix[:, orders[name]] for name, matrix in robust_schemes.items()
    }
    permuted_row_ids = {
        name: tuple(np.asarray(base_ids, dtype=object)[orders[name]])
        for name in robust_schemes
    }
    clean_permuted = assess_state_forecast_v5(
        "strong",
        conditional,
        marginal,
        covered,
        groups,
        blocks,
        validation_row_ids=base_ids,
        validation_row_ids_by_scheme=permuted_row_ids,
        refit_schemes=permuted_schemes,
        refit_ids_by_scheme=robust_ids,
        reference_refit_ids_by_scheme=robust_refs,
        training_row_ids_by_scheme=clean_training,
        scheme_nested_draws=1200,
        scheme_seed=20260907,
        scheme_minimum_refits=8,
        **v2_formal_kwargs,
    )

    leaking_training = deepcopy(clean_training)
    leaking_refit = ids["seed"][5]
    rows = list(leaking_training["seed"][leaking_refit])
    rows[2] = base_ids[17]
    leaking_training["seed"][leaking_refit] = tuple(rows)
    training_leakage = assess_state_forecast_v5(
        "strong-leakage",
        conditional,
        marginal,
        covered,
        groups,
        blocks,
        validation_row_ids=base_ids,
        validation_row_ids_by_scheme=_provenance_ids(base_ids, robust_schemes),
        refit_schemes=robust_schemes,
        refit_ids_by_scheme=robust_ids,
        reference_refit_ids_by_scheme=robust_refs,
        training_row_ids_by_scheme=leaking_training,
        scheme_nested_draws=1200,
        scheme_seed=20260907,
        scheme_minimum_refits=8,
        **v2_formal_kwargs,
    )

    mismatch_ids = _provenance_ids(base_ids, robust_schemes)
    mismatch_ids = dict(mismatch_ids)
    bad_seed = list(mismatch_ids["seed"])
    bad_seed[-1] = "validation-extra"
    mismatch_ids["seed"] = tuple(bad_seed)
    clean_row_mismatch = assess_state_forecast_v5(
        "row-mismatch",
        conditional,
        marginal,
        covered,
        groups,
        blocks,
        validation_row_ids=base_ids,
        validation_row_ids_by_scheme=mismatch_ids,
        refit_schemes=robust_schemes,
        refit_ids_by_scheme=robust_ids,
        reference_refit_ids_by_scheme=robust_refs,
        training_row_ids_by_scheme=clean_training,
        scheme_nested_draws=1200,
        scheme_seed=20260907,
        scheme_minimum_refits=8,
        **v2_formal_kwargs,
    )

    clean_sensitive = assess_state_forecast_v5(
        "scheme-sensitive",
        conditional,
        marginal,
        covered,
        groups,
        blocks,
        validation_row_ids=base_ids,
        validation_row_ids_by_scheme=_provenance_ids(base_ids, sensitive_schemes),
        refit_schemes=sensitive_schemes,
        refit_ids_by_scheme=sensitive_ids,
        reference_refit_ids_by_scheme=sensitive_refs,
        training_row_ids_by_scheme=sensitive_training,
        scheme_nested_draws=1200,
        scheme_seed=20260907,
        scheme_minimum_refits=8,
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
    prior_failure_with_leakage = assess_state_forecast_v5(
        "prior-failure",
        conditional,
        marginal,
        covered,
        groups,
        blocks,
        validation_row_ids=base_ids,
        validation_row_ids_by_scheme=_provenance_ids(base_ids, robust_schemes),
        refit_schemes=robust_schemes,
        refit_ids_by_scheme=robust_ids,
        reference_refit_ids_by_scheme=robust_refs,
        training_row_ids_by_scheme=leaking_training,
        scheme_nested_draws=1200,
        scheme_seed=20260907,
        scheme_minimum_refits=8,
        **v2_fragile_kwargs,
    )

    train_x = np.column_stack([np.linspace(-1, 1, 60), np.sin(np.linspace(-2, 2, 60))])
    query_x = np.asarray([[0.0, 0.0], [0.5, 0.2], [3.0, 0.0]])
    strict = assess_state_forecast_v5(
        "strict",
        conditional,
        marginal,
        covered,
        groups,
        blocks,
        validation_row_ids=base_ids,
        validation_row_ids_by_scheme=_provenance_ids(base_ids, robust_schemes),
        refit_schemes=robust_schemes,
        refit_ids_by_scheme=robust_ids,
        reference_refit_ids_by_scheme=robust_refs,
        training_row_ids_by_scheme=clean_training,
        scheme_nested_draws=1200,
        scheme_seed=20260907,
        scheme_minimum_refits=8,
        novelty_train_X=train_x,
        novelty_query_X=query_x,
        **v2_formal_kwargs,
    )

    omitted = assess_state_forecast_v5(
        "omitted",
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
    omitted_direct = assess_state_forecast_v4(
        "omitted",
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

    scheme_only = assess_state_forecast_v5(
        "scheme-only",
        conditional,
        marginal,
        covered,
        groups,
        blocks,
        validation_row_ids=base_ids,
        validation_row_ids_by_scheme=_provenance_ids(base_ids, robust_schemes),
        refit_schemes=robust_schemes,
        refit_ids_by_scheme=robust_ids,
        reference_refit_ids_by_scheme=robust_refs,
        training_row_ids_by_scheme=clean_training,
        scheme_nested_draws=1200,
        scheme_seed=20260907,
        scheme_minimum_refits=8,
        **base_kwargs,
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
    pseudo_row_ids = tuple(f"pseudo-{i:04d}" for i in range(pseudo_gain.size))
    pseudo_training = _training_memberships(pseudo_refit_ids)
    block_warning = assess_state_forecast_v5(
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
        validation_row_ids=pseudo_row_ids,
        validation_row_ids_by_scheme={name: pseudo_row_ids for name in pseudo_schemes},
        refit_schemes=pseudo_schemes,
        refit_ids_by_scheme=pseudo_refit_ids,
        reference_refit_ids_by_scheme={name: values[0] for name, values in pseudo_refit_ids.items()},
        training_row_ids_by_scheme=pseudo_training,
        scheme_nested_draws=1200,
        scheme_seed=20260907,
        scheme_minimum_refits=8,
    )

    exact_qualified = clean_exact.provenance_qualified_v4_assessment
    permuted_qualified = clean_permuted.provenance_qualified_v4_assessment
    checks = {
        "clean_exact_case_is_certified": clean_exact.v5_certification.certification_status == "certified" and clean_exact.training_validation_provenance is not None and clean_exact.training_validation_provenance.training_validation_separated and exact_qualified is not None,
        "base_v4_result_is_preserved_exactly": clean_exact.base_v4_assessment.as_dict() == direct_v4_omitted.as_dict(),
        "clean_exact_case_matches_direct_v4_scheme_result": exact_qualified is not None and exact_qualified.as_dict() == direct_v4_exact.as_dict(),
        "clean_permuted_case_matches_clean_exact_result": permuted_qualified is not None and exact_qualified is not None and permuted_qualified.aligned_refit_scheme_audit is not None and exact_qualified.aligned_refit_scheme_audit is not None and permuted_qualified.aligned_refit_scheme_audit.scheme_audit is not None and exact_qualified.aligned_refit_scheme_audit.scheme_audit is not None and permuted_qualified.aligned_refit_scheme_audit.scheme_audit.as_dict() == exact_qualified.aligned_refit_scheme_audit.scheme_audit.as_dict() and clean_permuted.v5_certification.certification_status == clean_exact.v5_certification.certification_status,
        "training_leakage_makes_otherwise_certifiable_case_unavailable": training_leakage.base_v4_assessment.v4_certification.certification_status == "certified" and training_leakage.v5_certification.certification_status == "unavailable" and training_leakage.v5_certification.operational_status == "admitted_extended_unavailable",
        "training_leakage_prevents_downstream_v4_scheme_assessment": training_leakage.training_validation_provenance is not None and training_leakage.training_validation_provenance.separation_category == "leakage_detected" and training_leakage.provenance_qualified_v4_assessment is None and not training_leakage.settings["downstream_v4_scheme_assessment_run"],
        "training_leakage_is_only_provenance_blocker_not_refit_scheme_statistical_blocker": training_leakage.v5_certification.provenance_blocking_reasons == ("training_validation_leakage",) and not any(reason.startswith("refit_scheme") for reason in training_leakage.v5_certification.statistical_blocking_reasons),
        "prior_base_v4_not_certified_is_not_rescued_by_training_leakage": prior_failure_with_leakage.base_v4_assessment.v4_certification.certification_status == "not_certified" and prior_failure_with_leakage.v5_certification.certification_status == "not_certified" and prior_failure_with_leakage.provenance_qualified_v4_assessment is None,
        "clean_training_plus_row_mismatch_inherits_v4_unavailable": clean_row_mismatch.training_validation_provenance is not None and clean_row_mismatch.training_validation_provenance.training_validation_separated and clean_row_mismatch.provenance_qualified_v4_assessment is not None and clean_row_mismatch.provenance_qualified_v4_assessment.v4_certification.certification_status == "unavailable" and clean_row_mismatch.v5_certification.certification_status == "unavailable" and "heldout_row_mismatch" in clean_row_mismatch.v5_certification.provenance_blocking_reasons,
        "clean_training_plus_scheme_sensitive_inherits_v4_not_certified": clean_sensitive.training_validation_provenance is not None and clean_sensitive.training_validation_provenance.training_validation_separated and clean_sensitive.provenance_qualified_v4_assessment is not None and clean_sensitive.provenance_qualified_v4_assessment.v4_certification.certification_status == "not_certified" and clean_sensitive.v5_certification.certification_status == "not_certified",
        "strict_extrapolation_remains_warning_under_clean_training_provenance": strict.v5_certification.certification_status == "certified" and strict.v5_certification.operational_status == "admitted_with_warnings" and "strict_extrapolation" in strict.v5_certification.warning_reasons,
        "omitted_scheme_layer_preserves_base_v4_result_and_certification": omitted.training_validation_provenance is None and omitted.provenance_qualified_v4_assessment is None and omitted.base_v4_assessment.as_dict() == omitted_direct.as_dict() and omitted.v5_certification.certification_status == omitted_direct.v4_certification.certification_status,
        "scheme_only_formal_layer_can_certify_with_clean_training_provenance": scheme_only.base_v4_assessment.v4_certification.certification_status == "not_audited" and scheme_only.training_validation_provenance is not None and scheme_only.training_validation_provenance.training_validation_separated and scheme_only.v5_certification.certification_status == "certified",
        "block_definition_warning_remains_warning_under_clean_training_provenance": block_warning.base_v4_assessment.base_v3_assessment.base_v2_assessment.block_definition_audit is not None and block_warning.base_v4_assessment.base_v3_assessment.base_v2_assessment.block_definition_audit.sensitivity_category == "block_definition_sensitive" and block_warning.v5_certification.certification_status == "certified" and "block_definition_sensitive" in block_warning.v5_certification.warning_reasons,
        "aggregate_confidence_score_emitted": all(not row.aggregate_confidence_score_emitted for row in (clean_exact, clean_permuted, training_leakage, clean_row_mismatch, clean_sensitive, prior_failure_with_leakage, strict, omitted, scheme_only, block_warning)),
    }

    return {
        "seed": seed,
        "clean_exact": clean_exact.as_dict(),
        "clean_permuted": clean_permuted.as_dict(),
        "training_leakage": training_leakage.as_dict(),
        "clean_row_mismatch": clean_row_mismatch.as_dict(),
        "clean_scheme_sensitive": clean_sensitive.as_dict(),
        "prior_v4_failure_with_leakage": prior_failure_with_leakage.as_dict(),
        "strict_extrapolation": strict.as_dict(),
        "omitted_scheme": omitted.as_dict(),
        "scheme_only": scheme_only.as_dict(),
        "block_definition_warning": block_warning.as_dict(),
        "checks": [{"name": name, "passed": bool(value)} for name, value in checks.items()],
        "passed": bool(all(checks.values())),
    }
