"""Known-truth benchmark for bounded reweighting robustness."""
from __future__ import annotations

import itertools
import math
import numpy as np

from .bounded_reweighting_robustness import (
    audit_bounded_reweighting_robustness,
    extreme_bounded_weighted_mean,
)


def _group_rows(pattern: np.ndarray, group_count: int):
    gains=[]; groups=[]
    for gi in range(group_count):
        gid=f"group-{gi+1:02d}"
        gains.extend(pattern.tolist())
        groups.extend([gid]*pattern.size)
    return np.asarray(gains,dtype=float),tuple(groups)


def _exhaustive_endpoint_mean(gain, weight, gamma, minimize):
    gain=np.asarray(gain,dtype=float); weight=np.asarray(weight,dtype=float)
    low=1.0/gamma; high=gamma
    values=[]
    for choices in itertools.product((low,high), repeat=gain.size):
        mult=np.asarray(choices,dtype=float)
        w=weight*mult
        values.append(float(np.sum(w*gain)/np.sum(w)))
    return min(values) if minimize else max(values)


def run_bounded_reweighting_robustness_benchmark(*, gamma: float=2.0) -> dict[str,object]:
    group_count=6; rows_per_group=400

    all_positive_pattern=np.linspace(0.20,0.30,rows_per_group)
    positive_gain,positive_groups=_group_rows(all_positive_pattern,group_count)
    positive=audit_bounded_reweighting_robustness(positive_gain,positive_groups,gamma=gamma)

    mixed_pattern=np.r_[np.full(300,0.20),np.full(100,-0.20)]
    mixed_gain,mixed_groups=_group_rows(mixed_pattern,group_count)
    mixed_at_one=audit_bounded_reweighting_robustness(mixed_gain,mixed_groups,gamma=1.0)
    mixed=audit_bounded_reweighting_robustness(mixed_gain,mixed_groups,gamma=gamma)

    negative_pattern=-np.linspace(0.20,0.30,rows_per_group)
    negative_gain,negative_groups=_group_rows(negative_pattern,group_count)
    negative=audit_bounded_reweighting_robustness(negative_gain,negative_groups,gamma=gamma)

    gammas=(1.0,1.25,1.5,2.0,4.0)
    gamma_path=[audit_bounded_reweighting_robustness(mixed_gain,mixed_groups,gamma=value) for value in gammas]
    worst_path=[row.minimum_worst_case_group_gain for row in gamma_path]
    best_path=[row.maximum_best_case_group_gain for row in gamma_path]

    base_weight=np.tile(np.linspace(0.5,1.5,rows_per_group),group_count)
    weighted=audit_bounded_reweighting_robustness(
        positive_gain,positive_groups,base_weight=base_weight,gamma=gamma
    )
    scaled=audit_bounded_reweighting_robustness(
        positive_gain,positive_groups,base_weight=base_weight*100.0,gamma=gamma
    )
    scale_error=max(
        abs(a.worst_case_mean_gain-b.worst_case_mean_gain)
        for a,b in zip(weighted.groups,scaled.groups)
    )

    reverse=np.arange(positive_gain.size-1,-1,-1)
    reordered=audit_bounded_reweighting_robustness(
        positive_gain[reverse],
        tuple(positive_groups[index] for index in reverse),
        base_weight=base_weight[reverse],gamma=gamma,
    )
    by_group={row.group_id:row for row in weighted.groups}
    reordered_by_group={row.group_id:row for row in reordered.groups}
    order_error=max(
        abs(by_group[name].worst_case_mean_gain-reordered_by_group[name].worst_case_mean_gain)
        for name in by_group
    )

    small_gain=np.asarray([-0.4,-0.1,0.05,0.2,0.3,0.6],dtype=float)
    small_weight=np.asarray([1.0,2.0,0.7,1.3,0.9,1.8],dtype=float)
    small_gamma=1.7
    solved_min=extreme_bounded_weighted_mean(
        small_gain,base_weight=small_weight,gamma=small_gamma,minimize=True
    )
    solved_max=extreme_bounded_weighted_mean(
        small_gain,base_weight=small_weight,gamma=small_gamma,minimize=False
    )
    exhaustive_min=_exhaustive_endpoint_mean(small_gain,small_weight,small_gamma,True)
    exhaustive_max=_exhaustive_endpoint_mean(small_gain,small_weight,small_gamma,False)
    exhaustive_error=max(abs(solved_min-exhaustive_min),abs(solved_max-exhaustive_max))

    critical=[row.critical_gamma for row in mixed.groups]
    critical_error=max(abs(value-math.sqrt(3.0)) for value in critical if value is not None)

    checks={
        "all_positive_gamma_robust_generalizing": positive.envelope_transfer_category=="gamma_robust_generalizing",
        "mixed_sign_point_generalizing_at_gamma_1": mixed_at_one.point_transfer_category=="generalizing" and mixed_at_one.envelope_transfer_category=="gamma_robust_generalizing",
        "mixed_sign_gamma_2_sensitive": mixed.point_transfer_category=="generalizing" and mixed.envelope_transfer_category=="gamma_sensitive",
        "mixed_sign_critical_gamma_near_sqrt_3": all(value is not None for value in critical) and critical_error<=1e-10,
        "all_negative_gamma_robust_non_generalizing": negative.envelope_transfer_category=="gamma_robust_non_generalizing",
        "worst_case_gain_nonincreasing_with_gamma": all(a>=b-1e-14 for a,b in zip(worst_path,worst_path[1:])),
        "best_case_gain_nondecreasing_with_gamma": all(a<=b+1e-14 for a,b in zip(best_path,best_path[1:])),
        "base_weight_global_scaling_invariant": scale_error<=1e-14 and scaled.envelope_transfer_category==weighted.envelope_transfer_category,
        "row_order_invariant": order_error<=1e-14 and reordered.envelope_transfer_category==weighted.envelope_transfer_category,
        "small_n_solution_matches_exhaustive_endpoint_search": exhaustive_error<=1e-12,
        "no_automatic_bias_correction": all(not audit.automatic_bias_correction_performed for audit in (positive,mixed_at_one,mixed,negative,weighted,scaled,reordered)),
        "no_aggregate_confidence": all(not audit.aggregate_confidence_score_emitted for audit in (positive,mixed_at_one,mixed,negative,weighted,scaled,reordered)),
    }

    return {
        "gamma":float(gamma),"group_count":group_count,"rows_per_group":rows_per_group,
        "all_positive":positive.as_dict(),
        "mixed_sign_gamma_1":mixed_at_one.as_dict(),
        "mixed_sign_primary_gamma":mixed.as_dict(),
        "all_negative":negative.as_dict(),
        "gamma_path":[{"gamma":g,"minimum_worst_case_group_gain":w,"maximum_best_case_group_gain":b} for g,w,b in zip(gammas,worst_path,best_path)],
        "mixed_sign_critical_gamma_error":float(critical_error),
        "base_weight_scaling_error":float(scale_error),
        "row_order_error":float(order_error),
        "small_n_exhaustive_error":float(exhaustive_error),
        "checks":[{"name":name,"passed":bool(value)} for name,value in checks.items()],
        "passed":bool(all(checks.values())),
    }
