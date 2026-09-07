"""Deterministic known-truth benchmark for refit-scheme sensitivity."""
from __future__ import annotations

import numpy as np

from .refit_scheme_sensitivity import audit_refit_scheme_sensitivity


def _design():
    r, j, k, m = 12, 6, 16, 20
    groups = tuple(f"group-{g:02d}" for g in range(j) for _ in range(k*m))
    blocks = tuple(f"block-{b:02d}" for _ in range(j) for b in range(k) for _ in range(m))
    group_effect = np.repeat(np.linspace(-0.004, 0.004, j), k*m)
    block_effect = np.tile(np.repeat(np.linspace(-0.025, 0.025, k), m), j)
    row_effect = np.tile(np.linspace(-0.002, 0.002, m), j*k)
    variation = group_effect + block_effect + row_effect
    a = 0.30 + np.linspace(-0.018, 0.018, r)[:, None] + variation
    b = 0.28 + np.linspace(-0.014, 0.014, r)[:, None] + 0.9*variation
    c = 0.32 + np.linspace(-0.022, 0.022, r)[:, None] + 1.1*variation
    fragile = np.r_[np.full(r//2, 0.30), np.full(r-r//2, -0.15)][:, None] + variation
    ids = {name: tuple(f"{name}-refit-{idx:02d}" for idx in range(r)) for name in ("bootstrap", "fold", "seed")}
    return a, b, c, fragile, groups, blocks, ids


def _scheme_summary_error(audit_a, audit_b) -> float:
    left = {row.scheme_name: row for row in audit_a.schemes}
    right = {row.scheme_name: row for row in audit_b.schemes}
    errors = []
    for name, row in left.items():
        other = right[name]
        for field in (
            "ensemble_mean_gain",
            "minimum_nested_max_t_lower_bound",
            "maximum_nested_max_t_upper_bound",
        ):
            x, y = getattr(row, field), getattr(other, field)
            if x is None or y is None:
                errors.append(0.0 if x is None and y is None else float("inf"))
            else:
                errors.append(abs(float(x)-float(y)))
    return float(max(errors, default=0.0))


def run_refit_scheme_sensitivity_benchmark(*, seed: int=20260907, nested_draws: int=2500) -> dict[str, object]:
    a, b, c, fragile, groups, blocks, ids = _design()
    stable_schemes = {"bootstrap": a, "fold": b, "seed": c}
    sensitive_schemes = {"bootstrap": a, "fold": b, "seed": fragile}
    negative_schemes = {name: -matrix for name, matrix in stable_schemes.items()}
    settings = dict(
        familywise_confidence_level=0.95,
        nested_draws=nested_draws,
        seed=seed,
        minimum_refits=8,
        minimum_blocks_per_group=8,
    )
    refs = {name: ids[name][0] for name in ids}

    def audit(schemes, *, group=groups, block=blocks, weight=None, scheme_ids=ids):
        local_refs = {name: scheme_ids[name][0] for name in schemes if name in scheme_ids}
        return audit_refit_scheme_sensitivity(
            schemes,
            group,
            blocks=block,
            sample_weight=weight,
            refit_ids_by_scheme={name: scheme_ids[name] for name in schemes if name in scheme_ids},
            reference_refit_ids_by_scheme=local_refs,
            **settings,
        )

    stable = audit(stable_schemes)
    negative = audit(negative_schemes)
    sensitive = audit(sensitive_schemes)

    unavailable_schemes = {"bootstrap": a, "fold": b[:4], "seed": c}
    unavailable_ids = dict(ids)
    unavailable_ids["fold"] = ids["fold"][:4]
    unavailable = audit(unavailable_schemes, scheme_ids=unavailable_ids)

    reordered = audit({"seed": c, "bootstrap": a, "fold": b})
    permutation = np.random.default_rng(7719).permutation(a.shape[1])
    permuted_schemes = {name: matrix[:, permutation] for name, matrix in stable_schemes.items()}
    permuted = audit(
        permuted_schemes,
        group=tuple(np.asarray(groups, dtype=object)[permutation]),
        block=tuple(np.asarray(blocks, dtype=object)[permutation]),
    )
    scaled = audit(stable_schemes, weight=np.full(a.shape[1], 100.0))

    scheme_order_error = _scheme_summary_error(stable, reordered)
    row_order_error = _scheme_summary_error(stable, permuted)
    scaling_error = _scheme_summary_error(stable, scaled)
    sensitive_categories = {row.refit_aware_category for row in sensitive.schemes}
    sensitive_reference_categories = {row.reference_fit_category for row in sensitive.schemes}

    checks = {
        "stable_positive_is_scheme_robust_generalizing": stable.sensitivity_category == "scheme_robust_generalizing" and stable.scheme_robust_admissible,
        "stable_negative_is_scheme_robust_non_generalizing": negative.sensitivity_category == "scheme_robust_non_generalizing" and not negative.scheme_robust_admissible,
        "scheme_sensitive_case_contains_robust_and_uncertain_schemes": sensitive.sensitivity_category == "scheme_sensitive" and sensitive_categories == {"robust_generalizing", "uncertain"},
        "scheme_sensitive_case_is_not_admissible": not sensitive.scheme_robust_admissible,
        "one_unavailable_scheme_makes_global_category_unavailable": unavailable.sensitivity_category == "unavailable" and unavailable.unavailable_scheme_count == 1,
        "scheme_order_invariant": scheme_order_error <= 1e-12 and stable.scheme_names == reordered.scheme_names,
        "row_order_invariant": row_order_error <= 1e-12,
        "positive_global_weight_scaling_invariant": scaling_error <= 1e-12,
        "scheme_names_preserved": stable.scheme_names == ("bootstrap", "fold", "seed"),
        "reference_fit_categories_retained_per_scheme": sensitive_reference_categories == {"robust_generalizing"},
        "no_automatic_scheme_selection": not stable.automatic_scheme_selection and not sensitive.automatic_scheme_selection,
        "aggregate_confidence_score_emitted": not stable.aggregate_confidence_score_emitted and not sensitive.aggregate_confidence_score_emitted,
    }

    return {
        "seed": seed,
        "nested_draws": nested_draws,
        "familywise_confidence_level": 0.95,
        "stable_positive": stable.as_dict(),
        "stable_negative": negative.as_dict(),
        "scheme_sensitive": sensitive.as_dict(),
        "one_unavailable_scheme": unavailable.as_dict(),
        "scheme_order_error": scheme_order_error,
        "row_order_error": row_order_error,
        "positive_global_weight_scaling_error": scaling_error,
        "checks": [{"name": name, "passed": bool(value)} for name, value in checks.items()],
        "passed": bool(all(checks.values())),
    }
