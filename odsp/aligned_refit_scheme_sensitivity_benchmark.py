"""Known-truth benchmark for row-aligned refit-scheme sensitivity."""
from __future__ import annotations

import numpy as np

from .aligned_refit_scheme_sensitivity import audit_aligned_refit_scheme_sensitivity
from .refit_scheme_sensitivity import audit_refit_scheme_sensitivity
from .refit_scheme_sensitivity_benchmark import _design


def run_aligned_refit_scheme_sensitivity_benchmark(
    *, seed: int = 20260907, nested_draws: int = 1200
) -> dict[str, object]:
    if seed != 20260907:
        raise ValueError("the frozen aligned benchmark uses seed 20260907")
    a, b, c, _fragile, groups, blocks, refit_ids = _design()
    schemes = {"bootstrap": a, "fold": b, "seed": c}
    references = {name: refit_ids[name][0] for name in schemes}
    n = a.shape[1]
    base_ids = tuple(f"validation-{i:04d}" for i in range(n))
    settings = dict(
        familywise_confidence_level=0.95,
        nested_draws=nested_draws,
        seed=seed,
        minimum_refits=8,
        minimum_blocks_per_group=8,
    )

    baseline = audit_refit_scheme_sensitivity(
        schemes,
        groups,
        blocks=blocks,
        refit_ids_by_scheme=refit_ids,
        reference_refit_ids_by_scheme=references,
        **settings,
    )
    exact = audit_aligned_refit_scheme_sensitivity(
        schemes,
        groups,
        blocks=blocks,
        validation_row_ids=base_ids,
        validation_row_ids_by_scheme={name: base_ids for name in schemes},
        refit_ids_by_scheme=refit_ids,
        reference_refit_ids_by_scheme=references,
        **settings,
    )

    bootstrap_order = np.arange(n)
    fold_order = np.roll(np.arange(n), 37)
    seed_order = np.random.default_rng(99017).permutation(n)
    orders = {
        "bootstrap": bootstrap_order,
        "fold": fold_order,
        "seed": seed_order,
    }
    permuted_schemes = {
        name: matrix[:, orders[name]] for name, matrix in schemes.items()
    }
    permuted_ids = {
        name: tuple(np.asarray(base_ids, dtype=object)[orders[name]]) for name in schemes
    }
    permuted = audit_aligned_refit_scheme_sensitivity(
        permuted_schemes,
        groups,
        blocks=blocks,
        validation_row_ids=base_ids,
        validation_row_ids_by_scheme=permuted_ids,
        refit_ids_by_scheme=refit_ids,
        reference_refit_ids_by_scheme=references,
        **settings,
    )

    mismatch_ids = dict(permuted_ids)
    mismatch_seed = list(mismatch_ids["seed"])
    mismatch_seed[-1] = "validation-extra"
    mismatch_ids["seed"] = tuple(mismatch_seed)
    mismatch = audit_aligned_refit_scheme_sensitivity(
        permuted_schemes,
        groups,
        blocks=blocks,
        validation_row_ids=base_ids,
        validation_row_ids_by_scheme=mismatch_ids,
        refit_ids_by_scheme=refit_ids,
        reference_refit_ids_by_scheme=references,
        **settings,
    )

    duplicate_ids = dict(permuted_ids)
    duplicate_seed = list(duplicate_ids["seed"])
    duplicate_seed[-1] = duplicate_seed[0]
    duplicate_ids["seed"] = tuple(duplicate_seed)
    duplicate = audit_aligned_refit_scheme_sensitivity(
        permuted_schemes,
        groups,
        blocks=blocks,
        validation_row_ids=base_ids,
        validation_row_ids_by_scheme=duplicate_ids,
        refit_ids_by_scheme=refit_ids,
        reference_refit_ids_by_scheme=references,
        **settings,
    )

    missing_mapping_rejected = False
    try:
        audit_aligned_refit_scheme_sensitivity(
            schemes,
            groups,
            blocks=blocks,
            validation_row_ids=base_ids,
            validation_row_ids_by_scheme={"bootstrap": base_ids, "fold": base_ids},
            refit_ids_by_scheme=refit_ids,
            reference_refit_ids_by_scheme=references,
            **settings,
        )
    except ValueError:
        missing_mapping_rejected = True

    length_mismatch_rejected = False
    try:
        audit_aligned_refit_scheme_sensitivity(
            schemes,
            groups,
            blocks=blocks,
            validation_row_ids=base_ids,
            validation_row_ids_by_scheme={
                "bootstrap": base_ids,
                "fold": base_ids[:-1],
                "seed": base_ids,
            },
            refit_ids_by_scheme=refit_ids,
            reference_refit_ids_by_scheme=references,
            **settings,
        )
    except ValueError:
        length_mismatch_rejected = True

    relabeled_base = tuple(f"case-{i:04d}" for i in range(n))
    relabeled_ids = {
        name: tuple(np.asarray(relabeled_base, dtype=object)[orders[name]]) for name in schemes
    }
    relabeled = audit_aligned_refit_scheme_sensitivity(
        permuted_schemes,
        groups,
        blocks=blocks,
        validation_row_ids=relabeled_base,
        validation_row_ids_by_scheme=relabeled_ids,
        refit_ids_by_scheme=refit_ids,
        reference_refit_ids_by_scheme=references,
        **settings,
    )

    baseline_dict = baseline.as_dict()
    exact_scheme_dict = None if exact.scheme_audit is None else exact.scheme_audit.as_dict()
    permuted_scheme_dict = None if permuted.scheme_audit is None else permuted.scheme_audit.as_dict()
    relabeled_scheme_dict = None if relabeled.scheme_audit is None else relabeled.scheme_audit.as_dict()

    checks = {
        "exact_alignment_reproduces_existing_scheme_audit": exact_scheme_dict == baseline_dict and exact.status == "audited_exact_alignment",
        "independently_permuted_schemes_are_reordered_and_reproduce_existing_audit": permuted_scheme_dict == baseline_dict and permuted.status == "audited_reordered_alignment",
        "aligned_permuted_schemes_remain_scheme_robust_generalizing": permuted.scheme_sensitivity_category == "scheme_robust_generalizing" and permuted.scheme_robust_admissible,
        "reported_reordered_scheme_count_is_correct": permuted.reordered_scheme_count == 2,
        "row_mismatch_prevents_statistical_audit": mismatch.status == "row_mismatch" and not mismatch.statistical_audit_run and mismatch.scheme_audit is None,
        "duplicate_scheme_row_id_prevents_statistical_audit": duplicate.status == "row_mismatch" and not duplicate.statistical_audit_run and duplicate.scheme_audit is None,
        "missing_scheme_row_id_mapping_is_rejected": missing_mapping_rejected,
        "scheme_row_id_length_mismatch_is_rejected": length_mismatch_rejected,
        "consistent_row_id_relabeling_preserves_statistical_result": relabeled_scheme_dict == baseline_dict,
        "row_contents_are_not_used_to_infer_alignment": not permuted.row_alignment.row_contents_used_for_identity,
        "no_automatic_imputation_or_scheme_selection": not permuted.automatic_row_imputation and not permuted.automatic_scheme_selection,
        "aggregate_confidence_score_emitted": not permuted.aggregate_confidence_score_emitted and not mismatch.aggregate_confidence_score_emitted,
    }

    stable_rows = {row.scheme_name: row for row in baseline.schemes}
    return {
        "seed": seed,
        "nested_draws": nested_draws,
        "base_row_count": n,
        "baseline_scheme_category": baseline.sensitivity_category,
        "baseline_minimum_nested_max_t_lower_bound": baseline.minimum_nested_max_t_lower_bound,
        "baseline_maximum_nested_max_t_upper_bound": baseline.maximum_nested_max_t_upper_bound,
        "baseline_scheme_mean_gains": {name: row.ensemble_mean_gain for name, row in stable_rows.items()},
        "exact": exact.as_dict(),
        "permuted": permuted.as_dict(),
        "mismatch": mismatch.as_dict(),
        "duplicate": duplicate.as_dict(),
        "missing_mapping_rejected": missing_mapping_rejected,
        "length_mismatch_rejected": length_mismatch_rejected,
        "checks": [{"name": name, "passed": bool(value)} for name, value in checks.items()],
        "passed": bool(all(checks.values())),
    }
