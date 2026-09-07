"""Known-truth benchmark for Forecast Assessment v4 provenance composition."""
from __future__ import annotations

import numpy as np

from .forecast_assessment_v3 import assess_state_forecast_v3
from .forecast_assessment_v3_benchmark import _base_design, _common_kwargs, _region
from .forecast_assessment_v4 import assess_state_forecast_v4


def _scheme_inputs(ids, *, sensitive=False):
    gain, groups, blocks, covered, bootstrap, fold, seed, fragile, _ = _base_design()
    schemes = {"bootstrap": bootstrap, "fold": fold, "seed": fragile if sensitive else seed}
    scheme_ids = {name: ids[name] for name in schemes}
    refs = {name: scheme_ids[name][0] for name in schemes}
    return schemes, scheme_ids, refs


def _scheme_kwargs(ids, *, sensitive=False):
    schemes, scheme_ids, refs = _scheme_inputs(ids, sensitive=sensitive)
    return dict(
        refit_schemes=schemes,
        refit_ids_by_scheme=scheme_ids,
        reference_refit_ids_by_scheme=refs,
        scheme_nested_draws=1200,
        scheme_seed=20260907,
        scheme_minimum_refits=8,
    )


def _provenance_ids(base_ids, schemes):
    return {name: base_ids for name in schemes}


def run_forecast_assessment_v4_benchmark(*, seed: int = 20260907) -> dict[str, object]:
    if seed != 20260907:
        raise ValueError("the frozen Forecast Assessment v4 benchmark uses seed 20260907")

    gain, groups, blocks, covered, bootstrap, fold, seed_matrix, fragile, ids = _base_design()
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

    strong_exact = assess_state_forecast_v4(
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
    direct_v3_with_scheme = assess_state_forecast_v3(
        "strong",
        conditional,
        marginal,
        covered,
        groups,
        blocks,
        **v2_formal_kwargs,
        **_scheme_kwargs(ids),
    )
    direct_v3_omitted = assess_state_forecast_v3(
        "strong",
        conditional,
        marginal,
        covered,
        groups,
        blocks,
        **v2_formal_kwargs,
        scheme_nested_draws=1200,
        scheme_seed=20260907,
        scheme_minimum_refits=8,
    )

    orders = {
        "bootstrap": np.arange(n),
        "fold": np.roll(np.arange(n), 43),
        "seed": np.random.default_rng(81421).permutation(n),
    }
    permuted_schemes = {
        name: matrix[:, orders[name]] for name, matrix in robust_schemes.items()
    }
    permuted_row_ids = {
        name: tuple(np.asarray(base_ids, dtype=object)[orders[name]]) for name in robust_schemes
    }
    strong_permuted = assess_state_forecast_v4(
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
        scheme_nested_draws=1200,
        scheme_seed=20260907,
        scheme_minimum_refits=8,
        **v2_formal_kwargs,
    )

    mismatch_ids = dict(permuted_row_ids)
    bad_seed_ids = list(mismatch_ids["seed"])
    bad_seed_ids[-1] = "validation-extra"
    mismatch_ids["seed"] = tuple(bad_seed_ids)
    strong_mismatch = assess_state_forecast_v4(
        "strong-mismatch",
        conditional,
        marginal,
        covered,
        groups,
        blocks,
        validation_row_ids=base_ids,
        validation_row_ids_by_scheme=mismatch_ids,
        refit_schemes=permuted_schemes,
        refit_ids_by_scheme=robust_ids,
        reference_refit_ids_by_scheme=robust_refs,
        scheme_nested_draws=1200,
        scheme_seed=20260907,
        scheme_minimum_refits=8,
        **v2_formal_kwargs,
    )

    scheme_sensitive = assess_state_forecast_v4(
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
    prior_failure = assess_state_forecast_v4(
        "prior-failure",
        conditional,
        marginal,
        covered,
        groups,
        blocks,
        validation_row_ids=base_ids,
        validation_row_ids_by_scheme=mismatch_ids,
        refit_schemes=permuted_schemes,
        refit_ids_by_scheme=robust_ids,
        reference_refit_ids_by_scheme=robust_refs,
        scheme_nested_draws=1200,
        scheme_seed=20260907,
        scheme_minimum_refits=8,
        **v2_fragile_kwargs,
    )

    train_x = np.column_stack([np.linspace(-1, 1, 60), np.sin(np.linspace(-2, 2, 60))])
    query_x = np.asarray([[0.0, 0.0], [0.5, 0.2], [3.0, 0.0]])
    strict = assess_state_forecast_v4(
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
        scheme_nested_draws=1200,
        scheme_seed=20260907,
        scheme_minimum_refits=8,
        novelty_train_X=train_x,
        novelty_query_X=query_x,
        **v2_formal_kwargs,
    )

    omitted = assess_state_forecast_v4(
        "omitted",
        conditional,
        marginal,
        covered,
        groups,
        blocks,
        **v2_formal_kwargs,
        scheme_nested_draws=1200,
        scheme_seed=20260907,
        scheme_minimum_refits=8,
    )
    omitted_direct = assess_state_forecast_v3(
        "omitted",
        conditional,
        marginal,
        covered,
        groups,
        blocks,
        **v2_formal_kwargs,
        scheme_nested_draws=1200,
        scheme_seed=20260907,
        scheme_minimum_refits=8,
    )

    scheme_only = assess_state_forecast_v4(
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
        scheme_nested_draws=1200,
        scheme_seed=20260907,
        scheme_minimum_refits=8,
        **base_kwargs,
    )

    cluster_means = np.asarray([-0.20, -0.10, 0.0, 0.05, 0.10, 0.15, 0.20, 0.25])
    cluster_rows = 40
    pseudo_group = []
    pseudo_blocks = []
    pseudo_alt = []
    pseudo_gain = []
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
    block_warning = assess_state_forecast_v4(
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
        scheme_nested_draws=1200,
        scheme_seed=20260907,
        scheme_minimum_refits=8,
    )

    exact_aligned = strong_exact.aligned_refit_scheme_audit
    permuted_aligned = strong_permuted.aligned_refit_scheme_audit
    mismatch_aligned = strong_mismatch.aligned_refit_scheme_audit
    sensitive_aligned = scheme_sensitive.aligned_refit_scheme_audit

    checks = {
        "strong_exact_alignment_is_v4_certified": strong_exact.v4_certification.certification_status == "certified" and exact_aligned is not None and exact_aligned.status == "audited_exact_alignment",
        "base_v3_result_is_preserved_exactly": strong_exact.base_v3_assessment.as_dict() == direct_v3_omitted.as_dict(),
        "strong_exact_alignment_matches_direct_v3_scheme_certification": strong_exact.aligned_v3_certification is not None and strong_exact.aligned_v3_certification.as_dict() == direct_v3_with_scheme.v3_certification.as_dict(),
        "independently_permuted_schemes_are_reordered_and_match_exact_result": permuted_aligned is not None and exact_aligned is not None and permuted_aligned.reordered_scheme_count == 2 and permuted_aligned.scheme_audit is not None and exact_aligned.scheme_audit is not None and permuted_aligned.scheme_audit.as_dict() == exact_aligned.scheme_audit.as_dict() and strong_permuted.aligned_v3_certification is not None and strong_exact.aligned_v3_certification is not None and strong_permuted.aligned_v3_certification.as_dict() == strong_exact.aligned_v3_certification.as_dict(),
        "row_mismatch_makes_otherwise_certifiable_case_unavailable": strong_mismatch.v4_certification.certification_status == "unavailable" and strong_mismatch.v4_certification.operational_status == "admitted_extended_unavailable" and mismatch_aligned is not None and not mismatch_aligned.statistical_audit_run and mismatch_aligned.scheme_audit is None,
        "row_mismatch_does_not_emit_refit_scheme_uncertain_or_failure_reason": strong_mismatch.v4_certification.provenance_blocking_reasons == ("heldout_row_mismatch",) and not any(reason.startswith("refit_scheme") for reason in strong_mismatch.v4_certification.statistical_blocking_reasons),
        "aligned_scheme_sensitive_makes_v4_not_certified_without_rewriting_base_v3": scheme_sensitive.base_v3_assessment.v3_certification.certification_status == "certified" and sensitive_aligned is not None and sensitive_aligned.scheme_sensitivity_category == "scheme_sensitive" and scheme_sensitive.v4_certification.certification_status == "not_certified",
        "prior_v3_not_certified_is_not_rescued_by_row_provenance_failure": prior_failure.base_v3_assessment.v3_certification.certification_status == "not_certified" and prior_failure.v4_certification.certification_status == "not_certified" and prior_failure.v4_certification.provenance_blocking_reasons == ("heldout_row_mismatch",),
        "strict_extrapolation_remains_warning_while_v4_can_be_certified": strict.v4_certification.certification_status == "certified" and strict.v4_certification.operational_status == "admitted_with_warnings" and "strict_extrapolation" in strict.v4_certification.warning_reasons,
        "omitted_scheme_layer_preserves_base_v3_result_and_certification": omitted.aligned_refit_scheme_audit is None and omitted.base_v3_assessment.as_dict() == omitted_direct.as_dict() and omitted.v4_certification.certification_status == omitted_direct.v3_certification.certification_status,
        "scheme_only_formal_layer_can_certify": scheme_only.base_v3_assessment.v3_certification.certification_status == "not_audited" and scheme_only.v4_certification.certification_status == "certified",
        "block_definition_warning_remains_warning_not_provenance_gate": block_warning.base_v3_assessment.base_v2_assessment.block_definition_audit is not None and block_warning.base_v3_assessment.base_v2_assessment.block_definition_audit.sensitivity_category == "block_definition_sensitive" and block_warning.v4_certification.certification_status == "certified" and "block_definition_sensitive" in block_warning.v4_certification.warning_reasons,
        "aggregate_confidence_score_emitted": all(not row.aggregate_confidence_score_emitted for row in (strong_exact, strong_permuted, strong_mismatch, scheme_sensitive, prior_failure, strict, omitted, scheme_only, block_warning)),
    }

    return {
        "seed": seed,
        "strong_exact": strong_exact.as_dict(),
        "strong_permuted": strong_permuted.as_dict(),
        "row_mismatch": strong_mismatch.as_dict(),
        "scheme_sensitive": scheme_sensitive.as_dict(),
        "prior_v3_failure": prior_failure.as_dict(),
        "strict_extrapolation": strict.as_dict(),
        "omitted_scheme": omitted.as_dict(),
        "scheme_only": scheme_only.as_dict(),
        "block_definition_warning": block_warning.as_dict(),
        "checks": [{"name": name, "passed": bool(value)} for name, value in checks.items()],
        "passed": bool(all(checks.values())),
    }
