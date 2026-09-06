"""Known-truth benchmark for joint reweighting and block-bootstrap robustness."""
from __future__ import annotations

import numpy as np

from .block_aware_transfer_uncertainty import audit_block_aware_transfer_uncertainty
from .joint_bias_uncertainty_robustness import audit_joint_bias_uncertainty_robustness


def _rows_from_blocks(block_values_by_group, rows_per_block):
    gains=[];groups=[];blocks=[]
    for gi,block_values in enumerate(block_values_by_group):
        gid=f"group-{gi+1:02d}"
        for bi,value in enumerate(block_values):
            bid=f"{gid}-block-{bi+1:02d}"
            if np.ndim(value)==0:
                local=np.full(rows_per_block,float(value))
            else:
                local=np.asarray(value,dtype=float)
                if local.size!=rows_per_block:
                    raise ValueError("block row pattern has unexpected length")
            gains.extend(local.tolist());groups.extend([gid]*rows_per_block);blocks.extend([bid]*rows_per_block)
    return np.asarray(gains,dtype=float),tuple(groups),tuple(blocks)


def run_joint_bias_uncertainty_robustness_benchmark(
    *,seed: int=20260906,bootstrap_draws: int=1000
) -> dict[str,object]:
    group_count=6;blocks_per_group=20;rows_per_block=20

    strong_blocks=[]
    for gi in range(group_count):
        values=[]
        for bi in range(blocks_per_group):
            center=0.25+0.002*(gi-2.5)+0.001*(bi-9.5)
            values.append(center+np.linspace(-0.01,0.01,rows_per_block))
        strong_blocks.append(values)
    strong_gain,strong_groups,strong_block_ids=_rows_from_blocks(strong_blocks,rows_per_block)
    strong=audit_joint_bias_uncertainty_robustness(
        strong_gain,strong_groups,strong_block_ids,gamma=2.0,
        confidence_level=0.95,bootstrap_draws=bootstrap_draws,seed=seed,
        minimum_blocks_per_group=8,
    )

    mixed_pattern=np.r_[np.full(15,0.20),np.full(5,-0.20)]
    mixed_blocks=[[mixed_pattern.copy() for _ in range(blocks_per_group)] for _ in range(group_count)]
    mixed_gain,mixed_groups,mixed_block_ids=_rows_from_blocks(mixed_blocks,rows_per_block)
    mixed=audit_joint_bias_uncertainty_robustness(
        mixed_gain,mixed_groups,mixed_block_ids,gamma=2.0,
        confidence_level=0.95,bootstrap_draws=bootstrap_draws,seed=seed,
        minimum_blocks_per_group=8,
    )

    negative_blocks=[]
    for gi in range(group_count):
        values=[]
        for bi in range(blocks_per_group):
            center=-0.25+0.002*(gi-2.5)-0.001*(bi-9.5)
            values.append(center+np.linspace(-0.01,0.01,rows_per_block))
        negative_blocks.append(values)
    negative_gain,negative_groups,negative_block_ids=_rows_from_blocks(negative_blocks,rows_per_block)
    negative=audit_joint_bias_uncertainty_robustness(
        negative_gain,negative_groups,negative_block_ids,gamma=2.0,
        confidence_level=0.95,bootstrap_draws=bootstrap_draws,seed=seed,
        minimum_blocks_per_group=8,
    )

    weak_pattern=np.asarray([
        -0.25,-0.20,-0.15,-0.10,-0.08,-0.06,-0.04,-0.02,0.00,0.02,
        0.04,0.06,0.08,0.10,0.12,0.14,0.16,0.18,0.20,0.22,
    ])
    weak_blocks=[weak_pattern+0.001*gi for gi in range(group_count)]
    weak_gain,weak_groups,weak_block_ids=_rows_from_blocks(weak_blocks,rows_per_block)
    weak_joint=audit_joint_bias_uncertainty_robustness(
        weak_gain,weak_groups,weak_block_ids,gamma=1.0,
        confidence_level=0.95,bootstrap_draws=bootstrap_draws,seed=seed,
        minimum_blocks_per_group=8,
    )
    weak_existing=audit_block_aware_transfer_uncertainty(
        weak_gain,weak_groups,blocks=weak_block_ids,
        confidence_level=0.95,bootstrap_draws=bootstrap_draws,seed=seed,
        minimum_blocks_per_group=8,
    )
    existing_by={row.group_id:row for row in weak_existing.groups}
    weak_bound_error=max(
        max(
            abs(row.worst_case_lower_bound-existing_by[row.group_id].lower_bound),
            abs(row.best_case_upper_bound-existing_by[row.group_id].upper_bound),
        )
        for row in weak_joint.groups
    )

    few_blocks=[[np.full(rows_per_block,0.25) for _ in range(4)] for _ in range(group_count)]
    few_gain,few_groups,few_block_ids=_rows_from_blocks(few_blocks,rows_per_block)
    few=audit_joint_bias_uncertainty_robustness(
        few_gain,few_groups,few_block_ids,gamma=2.0,
        confidence_level=0.95,bootstrap_draws=bootstrap_draws,seed=seed,
        minimum_blocks_per_group=8,
    )

    base_weight=np.linspace(0.5,1.5,strong_gain.size)
    weighted=audit_joint_bias_uncertainty_robustness(
        strong_gain,strong_groups,strong_block_ids,base_weight=base_weight,gamma=2.0,
        confidence_level=0.95,bootstrap_draws=bootstrap_draws,seed=seed,
        minimum_blocks_per_group=8,
    )
    scaled=audit_joint_bias_uncertainty_robustness(
        strong_gain,strong_groups,strong_block_ids,base_weight=base_weight*100.0,gamma=2.0,
        confidence_level=0.95,bootstrap_draws=bootstrap_draws,seed=seed,
        minimum_blocks_per_group=8,
    )
    scale_error=max(
        abs(a.worst_case_lower_bound-b.worst_case_lower_bound)
        for a,b in zip(weighted.groups,scaled.groups)
    )

    mixed_gamma1=audit_joint_bias_uncertainty_robustness(
        mixed_gain,mixed_groups,mixed_block_ids,gamma=1.0,
        confidence_level=0.95,bootstrap_draws=bootstrap_draws,seed=seed,
        minimum_blocks_per_group=8,
    )
    gamma_monotone=all(
        row2.worst_case_lower_bound<=row1.worst_case_lower_bound+1e-14
        for row1,row2 in zip(mixed_gamma1.groups,mixed.groups)
    )

    checks={
        "strong_positive_gamma_2_joint_robust_generalizing": strong.joint_robust_category=="joint_robust_generalizing" and strong.minimum_worst_case_lower_bound>0,
        "mixed_sign_gamma_2_detected_envelope_sensitive": mixed.point_transfer_category=="generalizing" and mixed.deterministic_envelope_category=="gamma_sensitive" and mixed.joint_robust_category=="envelope_sensitive",
        "negative_gamma_2_joint_robust_non_generalizing": negative.joint_robust_category=="joint_robust_non_generalizing" and negative.maximum_best_case_upper_bound<=0,
        "weak_positive_gamma_1_uncertain": weak_joint.point_transfer_category=="generalizing" and weak_joint.joint_robust_category=="uncertain",
        "gamma_1_matches_existing_block_bootstrap_bounds": weak_bound_error<=1e-12,
        "too_few_blocks_unavailable": few.joint_robust_category=="unavailable" and few.unavailable_group_count==group_count,
        "global_base_weight_scaling_invariant": scale_error<=1e-12 and weighted.joint_robust_category==scaled.joint_robust_category,
        "gamma_increase_cannot_improve_worst_case_lower_bound": gamma_monotone,
        "no_automatic_bias_correction": all(not audit.automatic_bias_correction_performed for audit in (strong,mixed,negative,weak_joint,few,weighted,scaled)),
        "no_aggregate_confidence": all(not audit.aggregate_confidence_score_emitted for audit in (strong,mixed,negative,weak_joint,few,weighted,scaled)),
    }

    return {
        "seed":int(seed),"bootstrap_draws":int(bootstrap_draws),
        "group_count":group_count,"blocks_per_group":blocks_per_group,"rows_per_block":rows_per_block,
        "strong_positive":strong.as_dict(),"mixed_sign":mixed.as_dict(),"negative":negative.as_dict(),
        "weak_positive_gamma_1":weak_joint.as_dict(),"too_few_blocks":few.as_dict(),
        "base_weight_scaling_error":float(scale_error),"gamma_1_existing_bound_error":float(weak_bound_error),
        "gamma_monotonicity_passed":bool(gamma_monotone),
        "checks":[{"name":name,"passed":bool(value)} for name,value in checks.items()],
        "passed":bool(all(checks.values())),
    }
