"""Known-truth benchmark for bias-robust model selection v4."""
from __future__ import annotations

import numpy as np

from .bias_robust_model_selection import (
    compare_bias_robust_candidates,
    evaluate_bias_robust_candidate,
)


def _layout(group_count: int, blocks_per_group: int, rows_per_block: int):
    groups=[];blocks=[]
    for gi in range(group_count):
        gid=f"group-{gi+1:02d}"
        for bi in range(blocks_per_group):
            bid=f"{gid}-block-{bi+1:02d}"
            groups.extend([gid]*rows_per_block)
            blocks.extend([bid]*rows_per_block)
    return tuple(groups),tuple(blocks)


def _covered(group_count: int, rows_per_group: int, *, first_group_count: int | None=None):
    chunks=[]
    for gi in range(group_count):
        count=first_group_count if gi==0 and first_group_count is not None else int(round(0.90*rows_per_group))
        chunks.append(np.r_[np.ones(count,dtype=bool),np.zeros(rows_per_group-count,dtype=bool)])
    return np.concatenate(chunks)


def _evaluate(name,gain,covered,groups,blocks,region_size,*,gamma=2.0):
    marginal=np.full(gain.size,-2.0)
    return evaluate_bias_robust_candidate(
        name,marginal+gain,marginal,covered,groups,blocks,
        region_size=np.full(gain.size,region_size),gamma=gamma,
        target_coverage=0.90,coverage_tolerance=0.03,
        confidence_level=0.95,bootstrap_draws=1000,seed=20260906,
        minimum_blocks_per_group=8,
    )


def run_bias_robust_model_selection_benchmark() -> dict[str,object]:
    group_count=6;blocks_per_group=20;rows_per_block=20
    rows_per_group=blocks_per_group*rows_per_block
    groups,blocks=_layout(group_count,blocks_per_group,rows_per_block)
    n=group_count*rows_per_group
    calibrated=_covered(group_count,rows_per_group)

    # Strong, calibrated and jointly robust.
    strong=[]
    for gi in range(group_count):
        for bi in range(blocks_per_group):
            center=0.25+0.002*(gi-2.5)+0.001*(bi-9.5)
            strong.extend((center+np.linspace(-0.01,0.01,rows_per_block)).tolist())
    robust_balanced=_evaluate("robust_balanced",np.asarray(strong),calibrated,groups,blocks,4.0)

    # Positive point gain and perfect block repeatability, but gamma=2 can reverse it.
    mixed_pattern=np.r_[np.full(15,0.20),np.full(5,-0.20)]
    gamma_gain=np.tile(mixed_pattern,group_count*blocks_per_group)
    gamma_fragile=_evaluate("gamma_fragile",gamma_gain,calibrated,groups,blocks,2.5)

    # Lower-gain, broader but still jointly robust.
    broad_gain=np.full(n,0.15)
    robust_broad=_evaluate("robust_broad",broad_gain,calibrated,groups,blocks,7.0)

    # Jointly robust transfer but first group's coverage fails badly.
    high_gain=np.full(n,0.40)
    coverage_failed=_covered(group_count,rows_per_group,first_group_count=int(0.60*rows_per_group))
    coverage_failure=_evaluate("coverage_failure",high_gain,coverage_failed,groups,blocks,2.0)

    # Point/coverage trusted but robust inference unavailable because only 4 blocks/group.
    few_groups,few_blocks=_layout(group_count,4,100)
    few_n=group_count*400
    few_covered=_covered(group_count,400)
    too_few_blocks=_evaluate(
        "too_few_blocks",np.full(few_n,0.255),few_covered,few_groups,few_blocks,3.0
    )

    candidates=[robust_balanced,gamma_fragile,robust_broad,coverage_failure,too_few_blocks]
    result=compare_bias_robust_candidates(candidates)
    by={row.name:row for row in candidates}

    reversed_result=compare_bias_robust_candidates(list(reversed(candidates)))
    order_ok=(
        set(result.bias_robust_trusted_names)==set(reversed_result.bias_robust_trusted_names)
        and set(result.pareto_front_names)==set(reversed_result.pareto_front_names)
        and result.recommended_by_log_score==reversed_result.recommended_by_log_score
    )

    checks={
        "robust_balanced_bias_robust_trusted": by["robust_balanced"].bias_robust_trusted_admissible,
        "gamma_fragile_point_trusted": by["gamma_fragile"].point_and_coverage.trusted_admissible,
        "gamma_fragile_envelope_sensitive": by["gamma_fragile"].joint_robustness.joint_robust_category=="envelope_sensitive",
        "gamma_fragile_bias_robust_rejected": not by["gamma_fragile"].bias_robust_trusted_admissible,
        "broad_bias_robust_trusted": by["robust_broad"].bias_robust_trusted_admissible,
        "coverage_failure_joint_robust_but_rejected": by["coverage_failure"].joint_robustness.joint_robust_category=="joint_robust_generalizing" and not by["coverage_failure"].bias_robust_trusted_admissible,
        "too_few_blocks_point_trusted_but_joint_unavailable": by["too_few_blocks"].point_and_coverage.trusted_admissible and by["too_few_blocks"].joint_robustness.joint_robust_category=="unavailable" and not by["too_few_blocks"].bias_robust_trusted_admissible,
        "robust_balanced_unique_pareto": result.pareto_front_names==("robust_balanced",),
        "robust_balanced_recommended": result.recommended_by_log_score=="robust_balanced",
        "candidate_order_invariant": order_ok,
        "no_aggregate_confidence": result.aggregate_confidence_score_emitted is False,
    }
    return {
        "group_count":group_count,"blocks_per_group":blocks_per_group,"rows_per_block":rows_per_block,
        "candidates":[row.as_dict() for row in candidates],
        "selection":result.as_dict(),
        "checks":[{"name":name,"passed":bool(value)} for name,value in checks.items()],
        "passed":bool(all(checks.values())),
    }
