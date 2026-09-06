"""Known-truth benchmark for the joint robustness gamma radius."""
from __future__ import annotations

import math
import numpy as np

from .block_aware_transfer_uncertainty import audit_block_aware_transfer_uncertainty
from .joint_bias_uncertainty_robustness import audit_joint_bias_uncertainty_robustness
from .joint_robustness_radius import audit_joint_robustness_radius


def _rows_from_blocks(block_values_by_group, rows_per_block):
    gains=[];groups=[];blocks=[]
    for gi,block_values in enumerate(block_values_by_group):
        gid=f"group-{gi+1:02d}"
        for bi,value in enumerate(block_values):
            bid=f"{gid}-block-{bi+1:02d}"
            values=np.asarray(value,dtype=float)
            if values.ndim==0:
                values=np.full(rows_per_block,float(values))
            gains.extend(values.tolist());groups.extend([gid]*rows_per_block);blocks.extend([bid]*rows_per_block)
    return np.asarray(gains,dtype=float),tuple(groups),tuple(blocks)


def run_joint_robustness_radius_benchmark(
    *,seed: int=20260906,bootstrap_draws: int=500
) -> dict[str,object]:
    group_count=6;blocks_per_group=20;rows_per_block=20

    positive_blocks=[]
    negative_blocks=[]
    for gi in range(group_count):
        pos=[];neg=[]
        for bi in range(blocks_per_group):
            pos_center=0.25+0.002*(gi-2.5)+0.001*(bi-9.5)
            neg_center=-0.25+0.002*(gi-2.5)-0.001*(bi-9.5)
            pos.append(pos_center+np.linspace(-0.01,0.01,rows_per_block))
            neg.append(neg_center+np.linspace(-0.01,0.01,rows_per_block))
        positive_blocks.append(pos);negative_blocks.append(neg)
    positive_gain,positive_groups,positive_block_ids=_rows_from_blocks(positive_blocks,rows_per_block)
    negative_gain,negative_groups,negative_block_ids=_rows_from_blocks(negative_blocks,rows_per_block)

    positive=audit_joint_robustness_radius(
        positive_gain,positive_groups,positive_block_ids,
        confidence_level=0.95,bootstrap_draws=bootstrap_draws,seed=seed,
        minimum_blocks_per_group=8,search_upper_gamma=10.0,binary_iterations=50,
    )
    negative=audit_joint_robustness_radius(
        negative_gain,negative_groups,negative_block_ids,
        confidence_level=0.95,bootstrap_draws=bootstrap_draws,seed=seed,
        minimum_blocks_per_group=8,search_upper_gamma=10.0,binary_iterations=50,
    )

    mixed_pattern=np.r_[np.full(15,0.20),np.full(5,-0.20)]
    mixed_blocks=[[mixed_pattern.copy() for _ in range(blocks_per_group)] for _ in range(group_count)]
    mixed_gain,mixed_groups,mixed_block_ids=_rows_from_blocks(mixed_blocks,rows_per_block)
    mixed=audit_joint_robustness_radius(
        mixed_gain,mixed_groups,mixed_block_ids,
        confidence_level=0.95,bootstrap_draws=bootstrap_draws,seed=seed,
        minimum_blocks_per_group=8,search_upper_gamma=10.0,binary_iterations=50,
    )
    mixed_scaled=audit_joint_robustness_radius(
        mixed_gain,mixed_groups,mixed_block_ids,base_weight=np.full(mixed_gain.size,100.0),
        confidence_level=0.95,bootstrap_draws=bootstrap_draws,seed=seed,
        minimum_blocks_per_group=8,search_upper_gamma=10.0,binary_iterations=50,
    )

    weak_pattern=np.asarray([
        -0.25,-0.20,-0.15,-0.10,-0.08,-0.06,-0.04,-0.02,0.00,0.02,
        0.04,0.06,0.08,0.10,0.12,0.14,0.16,0.18,0.20,0.22,
    ])
    weak_blocks=[weak_pattern+0.001*gi for gi in range(group_count)]
    weak_gain,weak_groups,weak_block_ids=_rows_from_blocks(weak_blocks,rows_per_block)
    weak=audit_joint_robustness_radius(
        weak_gain,weak_groups,weak_block_ids,
        confidence_level=0.95,bootstrap_draws=bootstrap_draws,seed=seed,
        minimum_blocks_per_group=8,search_upper_gamma=10.0,binary_iterations=50,
    )

    few_blocks=[[np.full(rows_per_block,0.25) for _ in range(4)] for _ in range(group_count)]
    few_gain,few_groups,few_block_ids=_rows_from_blocks(few_blocks,rows_per_block)
    few=audit_joint_robustness_radius(
        few_gain,few_groups,few_block_ids,
        confidence_level=0.95,bootstrap_draws=bootstrap_draws,seed=seed,
        minimum_blocks_per_group=8,search_upper_gamma=10.0,binary_iterations=50,
    )

    gamma_path=[]
    failed=False;regained=False
    for gamma in (1.0,1.25,1.5,2.0,4.0):
        audit=audit_joint_bias_uncertainty_robustness(
            mixed_gain,mixed_groups,mixed_block_ids,gamma=gamma,
            confidence_level=0.95,bootstrap_draws=bootstrap_draws,seed=seed,
            minimum_blocks_per_group=8,
        )
        passed=audit.joint_robust_category=="joint_robust_generalizing"
        if failed and passed:
            regained=True
        if not passed:
            failed=True
        gamma_path.append({"gamma":gamma,"category":audit.joint_robust_category,"passed_target":passed})

    block_existing=audit_block_aware_transfer_uncertainty(
        positive_gain,positive_groups,blocks=positive_block_ids,
        confidence_level=0.95,bootstrap_draws=bootstrap_draws,seed=seed,
        minimum_blocks_per_group=8,
    )
    expected_joint=(
        "joint_robust_generalizing"
        if block_existing.robust_transfer_category=="robust_generalizing"
        else "joint_robust_non_generalizing"
        if block_existing.robust_transfer_category=="robust_non_generalizing"
        else block_existing.robust_transfer_category
    )

    sqrt3=math.sqrt(3.0)
    break_error=(None if mixed.break_gamma is None else abs(mixed.break_gamma-sqrt3))
    scaling_error=max(
        abs((mixed.certified_gamma or 0.0)-(mixed_scaled.certified_gamma or 0.0)),
        abs((mixed.break_gamma or 0.0)-(mixed_scaled.break_gamma or 0.0)),
    )
    checks={
        "strong_positive_robust_through_search_upper": positive.radius_status=="robust_through_search_upper" and positive.certified_gamma==10.0,
        "strong_negative_robust_through_search_upper": negative.radius_status=="robust_through_search_upper" and negative.certified_gamma==10.0,
        "mixed_positive_has_finite_radius": mixed.radius_status=="finite_radius" and mixed.target_joint_category=="joint_robust_generalizing",
        "mixed_positive_break_gamma_matches_sqrt3": break_error is not None and break_error<=1e-10,
        "mixed_positive_boundary_interval_width_le_1e_10": mixed.boundary_interval_width is not None and mixed.boundary_interval_width<=1e-10,
        "weak_positive_not_certified_at_baseline": weak.radius_status=="not_certified_at_baseline" and weak.certified_gamma is None,
        "too_few_blocks_unavailable": few.radius_status=="unavailable" and few.certified_gamma is None,
        "global_base_weight_scaling_invariant": scaling_error<=1e-12 and mixed.radius_status==mixed_scaled.radius_status,
        "gamma_path_never_regains_baseline_category_after_failure": not regained,
        "gamma_1_matches_existing_block_aware_category": positive.baseline_joint_category==expected_joint,
        "automatic_bias_correction_performed": all(not row.automatic_bias_correction_performed for row in (positive,negative,mixed,mixed_scaled,weak,few)),
        "aggregate_confidence_score_emitted": all(not row.aggregate_confidence_score_emitted for row in (positive,negative,mixed,mixed_scaled,weak,few)),
    }
    return {
        "seed":seed,"bootstrap_draws":bootstrap_draws,
        "strong_positive":positive.as_dict(),
        "strong_negative":negative.as_dict(),
        "mixed_positive":mixed.as_dict(),
        "mixed_positive_scaled_weights":mixed_scaled.as_dict(),
        "weak_positive":weak.as_dict(),
        "too_few_blocks":few.as_dict(),
        "gamma_path":gamma_path,
        "sqrt3":sqrt3,
        "break_gamma_error":break_error,
        "base_weight_scaling_error":scaling_error,
        "checks":[{"name":name,"passed":bool(value)} for name,value in checks.items()],
        "passed":bool(all(checks.values())),
    }
