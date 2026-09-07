"""Known-truth benchmark for simultaneous group transfer certification."""
from __future__ import annotations

import numpy as np

from .simultaneous_group_certification import audit_simultaneous_group_certification


def _rows_from_block_means(block_means_by_group, rows_per_block: int):
    gains=[];groups=[];blocks=[]
    for gi,block_means in enumerate(block_means_by_group):
        gid=f"group-{gi+1:02d}"
        for bi,value in enumerate(block_means):
            bid=f"{gid}-block-{bi+1:02d}"
            gains.extend([float(value)]*rows_per_block)
            groups.extend([gid]*rows_per_block)
            blocks.extend([bid]*rows_per_block)
    return np.asarray(gains,dtype=float),tuple(groups),tuple(blocks)


def _max_abs_bound_error(a,b,field: str) -> float:
    left={row.group_id:getattr(row,field) for row in a.groups}
    right={row.group_id:getattr(row,field) for row in b.groups}
    values=[]
    for gid in left:
        x=left[gid];y=right[gid]
        if x is None or y is None:
            values.append(0.0 if x is None and y is None else float("inf"))
        else:
            values.append(abs(float(x)-float(y)))
    return float(max(values,default=0.0))


def run_simultaneous_group_certification_benchmark(
    *,seed: int=20260906,bootstrap_draws: int=4000
) -> dict[str,object]:
    if seed!=20260906:
        raise ValueError("the frozen simultaneous-certification benchmark uses seed 20260906")
    group_count=20;blocks_per_group=20;rows_per_block=25
    base=np.asarray([
        -0.15,-0.10,-0.08,-0.05,-0.03,-0.01,0.01,0.03,0.05,0.07,
        0.09,0.11,0.13,0.15,0.17,0.19,0.21,0.23,0.25,0.27,
    ])

    strong_pattern=base+0.20
    strong_gain,strong_groups,strong_blocks=_rows_from_block_means(
        [strong_pattern for _ in range(group_count)],rows_per_block
    )
    strong=audit_simultaneous_group_certification(
        strong_gain,strong_groups,blocks=strong_blocks,
        familywise_confidence_level=0.95,bootstrap_draws=bootstrap_draws,
        seed=seed,minimum_blocks_per_group=8,
    )

    negative_pattern=-(base+0.20)
    negative_gain,negative_groups,negative_blocks=_rows_from_block_means(
        [negative_pattern for _ in range(group_count)],rows_per_block
    )
    negative=audit_simultaneous_group_certification(
        negative_gain,negative_groups,blocks=negative_blocks,
        familywise_confidence_level=0.95,bootstrap_draws=bootstrap_draws,
        seed=seed,minimum_blocks_per_group=8,
    )

    trap_gain,trap_groups,trap_blocks=_rows_from_block_means(
        [base for _ in range(group_count)],rows_per_block
    )
    trap=audit_simultaneous_group_certification(
        trap_gain,trap_groups,blocks=trap_blocks,
        familywise_confidence_level=0.95,bootstrap_draws=bootstrap_draws,
        seed=seed,minimum_blocks_per_group=8,
    )

    one_negative_patterns=[strong_pattern for _ in range(group_count)]
    one_negative_patterns[-1]=negative_pattern
    mixed_gain,mixed_groups,mixed_blocks=_rows_from_block_means(
        one_negative_patterns,rows_per_block
    )
    mixed=audit_simultaneous_group_certification(
        mixed_gain,mixed_groups,blocks=mixed_blocks,
        familywise_confidence_level=0.95,bootstrap_draws=bootstrap_draws,
        seed=seed,minimum_blocks_per_group=8,
    )

    few_patterns=[strong_pattern[:4] for _ in range(group_count)]
    few_gain,few_groups,few_blocks=_rows_from_block_means(few_patterns,rows_per_block)
    few=audit_simultaneous_group_certification(
        few_gain,few_groups,blocks=few_blocks,
        familywise_confidence_level=0.95,bootstrap_draws=bootstrap_draws,
        seed=seed,minimum_blocks_per_group=8,
    )

    scaled=audit_simultaneous_group_certification(
        trap_gain,trap_groups,blocks=trap_blocks,
        sample_weight=np.full(trap_gain.size,100.0),
        familywise_confidence_level=0.95,bootstrap_draws=bootstrap_draws,
        seed=seed,minimum_blocks_per_group=8,
    )

    rng=np.random.default_rng(99117)
    permutation=rng.permutation(trap_gain.size)
    row_reordered=audit_simultaneous_group_certification(
        trap_gain[permutation],
        tuple(np.asarray(trap_groups,dtype=object)[permutation]),
        blocks=tuple(np.asarray(trap_blocks,dtype=object)[permutation]),
        familywise_confidence_level=0.95,bootstrap_draws=bootstrap_draws,
        seed=seed,minimum_blocks_per_group=8,
    )

    group_reverse=np.argsort(np.asarray(trap_groups,dtype=object),kind="stable")[::-1]
    group_reordered=audit_simultaneous_group_certification(
        trap_gain[group_reverse],
        tuple(np.asarray(trap_groups,dtype=object)[group_reverse]),
        blocks=tuple(np.asarray(trap_blocks,dtype=object)[group_reverse]),
        familywise_confidence_level=0.95,bootstrap_draws=bootstrap_draws,
        seed=seed,minimum_blocks_per_group=8,
    )

    single_gain,single_groups,single_blocks=_rows_from_block_means([strong_pattern],rows_per_block)
    single=audit_simultaneous_group_certification(
        single_gain,single_groups,blocks=single_blocks,
        familywise_confidence_level=0.95,bootstrap_draws=bootstrap_draws,
        seed=seed,minimum_blocks_per_group=8,
    )

    trap_marginal_min=min(float(row.marginal_lower_bound) for row in trap.groups if row.marginal_lower_bound is not None)
    trap_max_t_min=min(float(row.max_t_lower_bound) for row in trap.groups if row.max_t_lower_bound is not None)
    trap_bonf_min=min(float(row.bonferroni_lower_bound) for row in trap.groups if row.bonferroni_lower_bound is not None)
    scaling_error=max(
        abs(float(trap.max_t_critical_value)-float(scaled.max_t_critical_value)),
        _max_abs_bound_error(trap,scaled,"max_t_lower_bound"),
        _max_abs_bound_error(trap,scaled,"bonferroni_lower_bound"),
    )
    row_order_error=max(
        abs(float(trap.max_t_critical_value)-float(row_reordered.max_t_critical_value)),
        _max_abs_bound_error(trap,row_reordered,"max_t_lower_bound"),
        _max_abs_bound_error(trap,row_reordered,"bonferroni_lower_bound"),
    )
    group_order_error=max(
        abs(float(trap.max_t_critical_value)-float(group_reordered.max_t_critical_value)),
        _max_abs_bound_error(trap,group_reordered,"max_t_lower_bound"),
        _max_abs_bound_error(trap,group_reordered,"bonferroni_lower_bound"),
    )

    checks={
        "strong_positive_is_simultaneously_robust_generalizing": strong.max_t_transfer_category=="robust_generalizing" and strong.simultaneous_admissible,
        "strong_negative_is_simultaneously_robust_non_generalizing": negative.max_t_transfer_category=="robust_non_generalizing" and not negative.simultaneous_admissible,
        "multiplicity_trap_all_marginal_intervals_positive": trap.marginal_interval_category=="robust_generalizing" and trap_marginal_min>0.0,
        "multiplicity_trap_max_t_not_simultaneously_generalizing": trap.max_t_transfer_category=="uncertain" and trap_max_t_min<=0.0,
        "multiplicity_trap_bonferroni_not_simultaneously_generalizing": trap.bonferroni_transfer_category=="uncertain" and trap_bonf_min<=0.0,
        "max_t_critical_exceeds_single_group_normal_scale": trap.max_t_critical_value is not None and trap.max_t_critical_value>1.96,
        "one_negative_group_is_not_rescued_by_positive_groups": mixed.point_transfer_category=="mixed" and mixed.max_t_transfer_category=="mixed" and not mixed.simultaneous_admissible,
        "too_few_blocks_is_unavailable": few.max_t_transfer_category=="unavailable" and few.unavailable_group_count==group_count,
        "positive_global_weight_scaling_invariant": scaling_error<=1e-12,
        "row_order_invariant": row_order_error<=1e-12,
        "group_order_invariant": group_order_error<=1e-12,
        "single_group_max_t_category_matches_marginal_category": single.max_t_transfer_category==single.marginal_interval_category=="robust_generalizing",
        "pooled_gain_cannot_override_group_failure": mixed.pooled_mean_can_override_group_failure is False and mixed.max_t_transfer_category!="robust_generalizing",
        "marginal_interval_cannot_override_simultaneous_failure": trap.marginal_interval_can_override_simultaneous_failure is False and trap.marginal_interval_category=="robust_generalizing" and trap.max_t_transfer_category!="robust_generalizing",
        "aggregate_confidence_score_emitted": trap.aggregate_confidence_score_emitted is False and strong.aggregate_confidence_score_emitted is False,
    }

    return {
        "seed":seed,
        "bootstrap_draws":bootstrap_draws,
        "familywise_confidence_level":0.95,
        "strong_positive":strong.as_dict(),
        "strong_negative":negative.as_dict(),
        "multiplicity_trap":trap.as_dict(),
        "one_negative_group":mixed.as_dict(),
        "too_few_blocks":few.as_dict(),
        "single_group":single.as_dict(),
        "multiplicity_trap_marginal_minimum_lower_bound":trap_marginal_min,
        "multiplicity_trap_max_t_minimum_lower_bound":trap_max_t_min,
        "multiplicity_trap_bonferroni_minimum_lower_bound":trap_bonf_min,
        "max_t_critical_value":trap.max_t_critical_value,
        "positive_global_weight_scaling_error":scaling_error,
        "row_order_error":row_order_error,
        "group_order_error":group_order_error,
        "checks":[{"name":name,"passed":bool(value)} for name,value in checks.items()],
        "passed":bool(all(checks.values())),
    }
