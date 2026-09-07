"""Deterministic diagnostic fixtures, not empirical ecological performance."""
from __future__ import annotations

import numpy as np

from .model_refit_transfer_uncertainty import audit_model_refit_transfer_uncertainty


def _design():
    r, j, k, m = 20, 6, 20, 20
    groups = tuple(f'group-{g:02d}' for g in range(j) for _ in range(k*m))
    blocks = tuple(f'block-{b:02d}' for _ in range(j) for b in range(k) for _ in range(m))
    ids = tuple(f'refit-{a:02d}' for a in range(r))
    group_effect = np.repeat(np.linspace(-0.005, 0.005, j), k*m)
    block_effect = np.tile(np.repeat(np.linspace(-0.03, 0.03, k), m), j)
    row_effect = np.tile(np.linspace(-0.002, 0.002, m), j*k)
    variation = group_effect + block_effect + row_effect
    stable = 0.30 + np.linspace(-0.02, 0.02, r)[:, None] + variation
    fragile = np.r_[np.full(10, 0.30), np.full(10, -0.20)][:, None] + variation
    return stable, fragile, groups, blocks, ids


def _bound_error(a, b):
    left = {row.group_id: row for row in a.groups}
    right = {row.group_id: row for row in b.groups}
    errors = []
    for gid, row in left.items():
        for key in ('nested_max_t_lower_bound', 'nested_max_t_upper_bound',
                    'nested_marginal_lower_bound', 'nested_marginal_upper_bound'):
            x, y = getattr(row, key), getattr(right[gid], key)
            errors.append(0.0 if x is None and y is None else abs(float(x)-float(y)))
    errors.append(abs(float(a.nested_max_t_critical_value)-float(b.nested_max_t_critical_value)))
    return max(errors)


def run_model_refit_transfer_uncertainty_benchmark(*, seed: int = 20260906,
                                                   nested_draws: int = 4000) -> dict[str, object]:
    stable, fragile, groups, blocks, ids = _design()
    settings = dict(seed=seed, nested_draws=nested_draws, familywise_confidence_level=0.95,
                    minimum_refits=8, minimum_blocks_per_group=8)

    def audit(gain, group=groups, block=blocks, refit_ids=ids, weight=None):
        return audit_model_refit_transfer_uncertainty(
            gain, group, blocks=block, refit_ids=refit_ids, reference_refit_id=ids[0],
            sample_weight=weight, **settings,
        )

    positive = audit(stable)
    negative = audit(-stable)
    sensitive = audit(fragile)
    identical = audit(np.repeat(stable[:1], len(ids), axis=0))
    few_refits = audit(stable[:4], refit_ids=ids[:4])
    keep = np.array([group != groups[0] or block in {'block-00','block-01','block-02','block-03'}
                     for group, block in zip(groups, blocks)])
    few_blocks = audit(stable[:, keep], tuple(np.asarray(groups)[keep]), tuple(np.asarray(blocks)[keep]))
    reversed_refits = audit(stable[::-1], refit_ids=ids[::-1])
    permutation = np.random.default_rng(919).permutation(stable.shape[1])
    permuted_rows = audit(stable[:, permutation], tuple(np.asarray(groups)[permutation]),
                          tuple(np.asarray(blocks)[permutation]))
    scaled = audit(stable, weight=np.full(stable.shape[1], 100.0))
    reduction = max(
        max(abs(row.nested_max_t_lower_bound-ref.max_t_lower_bound),
            abs(row.nested_max_t_upper_bound-ref.max_t_upper_bound))
        for row, ref in zip(identical.groups, identical.reference_audit.groups)
    )
    refit_order_error = _bound_error(positive, reversed_refits)
    row_order_error = _bound_error(positive, permuted_rows)
    scaling_error = _bound_error(positive, scaled)
    checks = {
        'stable_positive_reference_fit_is_simultaneously_robust_generalizing': positive.reference_fit_category == 'robust_generalizing',
        'stable_positive_refit_aware_is_robust_generalizing': positive.refit_aware_category == 'robust_generalizing',
        'stable_negative_refit_aware_is_robust_non_generalizing': negative.refit_aware_category == 'robust_non_generalizing',
        'refit_fragile_reference_fit_is_simultaneously_robust_generalizing': sensitive.reference_fit_category == 'robust_generalizing',
        'refit_fragile_ensemble_is_refit_sensitive': sensitive.refit_sign_stability == 'refit_sensitive',
        'refit_fragile_refit_aware_is_not_robust_generalizing': sensitive.refit_aware_category == 'uncertain' and not sensitive.refit_aware_admissible,
        'identical_refits_reduce_to_existing_simultaneous_category': identical.refit_aware_category == identical.reference_fit_category,
        'identical_refits_max_t_bounds_match_existing_simultaneous_within_1e_12': reduction <= 1e-12,
        'too_few_refits_is_unavailable': few_refits.refit_aware_category == 'unavailable',
        'too_few_blocks_is_unavailable': few_blocks.refit_aware_category == 'unavailable' and few_blocks.unavailable_group_count == 1,
        'refit_order_with_ids_is_invariant': refit_order_error <= 1e-12 and positive.reference_refit_id == reversed_refits.reference_refit_id,
        'row_order_is_invariant': row_order_error <= 1e-12,
        'positive_global_weight_scaling_is_invariant': scaling_error <= 1e-12,
        'reference_fit_cannot_override_refit_aware_failure': not sensitive.reference_fit_can_override_refit_aware_failure and not sensitive.refit_aware_admissible,
        'aggregate_confidence_score_emitted': not any(a.aggregate_confidence_score_emitted for a in (positive,negative,sensitive,identical,few_refits,few_blocks)),
    }
    return {
        'seed': seed, 'nested_draws': nested_draws, 'familywise_confidence_level': 0.95,
        'stable_positive': positive.as_dict(), 'stable_negative': negative.as_dict(),
        'refit_fragile': sensitive.as_dict(), 'identical_refits': identical.as_dict(),
        'too_few_refits': few_refits.as_dict(), 'too_few_blocks': few_blocks.as_dict(),
        'identical_refits_bound_error': reduction, 'refit_order_error': refit_order_error,
        'row_order_error': row_order_error, 'positive_global_weight_scaling_error': scaling_error,
        'checks': [{'name': name, 'passed': bool(passed)} for name, passed in checks.items()],
        'passed': bool(all(checks.values())),
    }
