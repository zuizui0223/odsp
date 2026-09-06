"""Known-truth benchmark for ForecastTrustDossier v3 radius integration."""
from __future__ import annotations

import math
import numpy as np

from .bias_robust_model_selection import compare_bias_robust_candidates, evaluate_bias_robust_candidate
from .forecast_trust_dossier_v3 import build_forecast_trust_dossier_v3
from .joint_robustness_radius import audit_joint_robustness_radius
from .prediction_novelty import NoveltySummary


def _rows_from_blocks(block_values_by_group, rows_per_block: int):
    gains=[];groups=[];blocks=[]
    for gi,block_values in enumerate(block_values_by_group):
        gid=f"group-{gi+1:02d}"
        for bi,value in enumerate(block_values):
            bid=f"{gid}-block-{bi+1:02d}"
            values=np.asarray(value,dtype=float)
            if values.ndim==0:
                values=np.full(rows_per_block,float(values))
            if values.shape!=(rows_per_block,):
                raise ValueError("unexpected block shape")
            gains.extend(values.tolist());groups.extend([gid]*rows_per_block);blocks.extend([bid]*rows_per_block)
    return np.asarray(gains,dtype=float),tuple(groups),tuple(blocks)


def _coverage(groups):
    labels=np.asarray(groups,dtype=object)
    covered=np.zeros(len(groups),dtype=bool)
    for gid in tuple(dict.fromkeys(groups)):
        idx=np.flatnonzero(labels==gid)
        covered[idx[:int(round(0.90*idx.size))]]=True
    return covered


def _candidate(name,gain,groups,blocks,*,gamma,region_size,bootstrap_draws):
    return evaluate_bias_robust_candidate(
        name,gain,np.zeros_like(gain),_coverage(groups),groups,blocks,
        region_size=np.full(gain.size,region_size),gamma=gamma,
        confidence_level=0.95,bootstrap_draws=bootstrap_draws,seed=20260906,
        minimum_blocks_per_group=8,
    )


def _novelty(categories):
    rows=[]
    for i,category in enumerate(categories):
        ratio=3.5 if category=="strict_extrapolation" else 0.5
        outside=(1,) if category=="strict_extrapolation" else ()
        rows.append(NoveltySummary(
            row_index=i,nearest_scaled_distance=ratio,reference_distance=1.0,
            novelty_ratio=ratio,outside_feature_count=len(outside),
            outside_feature_indices=outside,category=category,
        ))
    return tuple(rows)


def run_forecast_trust_dossier_v3_benchmark(*,seed: int=20260906,bootstrap_draws: int=500) -> dict[str,object]:
    if seed!=20260906:
        raise ValueError("the frozen dossier v3 benchmark uses seed 20260906")
    group_count=6;blocks_per_group=20;rows_per_block=20

    strong_blocks=[]
    for gi in range(group_count):
        local=[]
        for bi in range(blocks_per_group):
            center=0.25+0.002*(gi-2.5)+0.001*(bi-9.5)
            local.append(center+np.linspace(-0.01,0.01,rows_per_block))
        strong_blocks.append(local)
    strong_gain,strong_groups,strong_block_ids=_rows_from_blocks(strong_blocks,rows_per_block)
    balanced=_candidate("robust_balanced",strong_gain,strong_groups,strong_block_ids,gamma=2.0,region_size=4.0,bootstrap_draws=bootstrap_draws)
    strong_radius=audit_joint_robustness_radius(
        strong_gain,strong_groups,strong_block_ids,confidence_level=0.95,
        bootstrap_draws=bootstrap_draws,seed=seed,minimum_blocks_per_group=8,
        search_upper_gamma=10.0,binary_iterations=50,
    )

    broad_blocks=[[np.full(rows_per_block,0.15) for _ in range(blocks_per_group)] for _ in range(group_count)]
    broad_gain,broad_groups,broad_block_ids=_rows_from_blocks(broad_blocks,rows_per_block)
    broad=_candidate("robust_broad",broad_gain,broad_groups,broad_block_ids,gamma=2.0,region_size=7.0,bootstrap_draws=bootstrap_draws)
    broad_radius=audit_joint_robustness_radius(
        broad_gain,broad_groups,broad_block_ids,confidence_level=0.95,
        bootstrap_draws=bootstrap_draws,seed=seed,minimum_blocks_per_group=8,
        search_upper_gamma=10.0,binary_iterations=50,
    )
    selection=compare_bias_robust_candidates(
        [balanced,broad],target_coverage=0.90,coverage_tolerance=0.03,gamma=2.0,
        confidence_level=0.95,bootstrap_draws=bootstrap_draws,minimum_blocks_per_group=8,
    )

    robust=build_forecast_trust_dossier_v3(
        balanced,joint_radius_audit=strong_radius,
        deployment_novelty_rows=_novelty(["in_domain","in_domain"]),selection=selection,
    )
    broad_dossier=build_forecast_trust_dossier_v3(
        broad,joint_radius_audit=broad_radius,
        deployment_novelty_rows=_novelty(["in_domain"]),selection=selection,
    )

    mixed_pattern=np.r_[np.full(15,0.20),np.full(5,-0.20)]
    mixed_blocks=[[mixed_pattern.copy() for _ in range(blocks_per_group)] for _ in range(group_count)]
    mixed_gain,mixed_groups,mixed_block_ids=_rows_from_blocks(mixed_blocks,rows_per_block)
    breakpoint_candidate=_candidate(
        "breakpoint_candidate",mixed_gain,mixed_groups,mixed_block_ids,
        gamma=1.5,region_size=4.0,bootstrap_draws=bootstrap_draws,
    )
    finite_radius=audit_joint_robustness_radius(
        mixed_gain,mixed_groups,mixed_block_ids,confidence_level=0.95,
        bootstrap_draws=bootstrap_draws,seed=seed,minimum_blocks_per_group=8,
        search_upper_gamma=10.0,binary_iterations=50,
    )
    breakpoint=build_forecast_trust_dossier_v3(
        breakpoint_candidate,joint_radius_audit=finite_radius,
        deployment_novelty_rows=_novelty(["in_domain"]),
    )
    breakpoint_strict=build_forecast_trust_dossier_v3(
        breakpoint_candidate,joint_radius_audit=finite_radius,
        deployment_novelty_rows=_novelty(["in_domain","strict_extrapolation"]),
    )

    weak_pattern=np.asarray([
        -0.25,-0.20,-0.15,-0.10,-0.08,-0.06,-0.04,-0.02,0.00,0.02,
        0.04,0.06,0.08,0.10,0.12,0.14,0.16,0.18,0.20,0.22,
    ])
    weak_blocks=[weak_pattern+0.001*gi for gi in range(group_count)]
    weak_gain,weak_groups,weak_block_ids=_rows_from_blocks(weak_blocks,rows_per_block)
    weak_candidate=_candidate(
        "weak_positive",weak_gain,weak_groups,weak_block_ids,
        gamma=1.0,region_size=4.0,bootstrap_draws=bootstrap_draws,
    )
    weak_radius=audit_joint_robustness_radius(
        weak_gain,weak_groups,weak_block_ids,confidence_level=0.95,
        bootstrap_draws=bootstrap_draws,seed=seed,minimum_blocks_per_group=8,
        search_upper_gamma=10.0,binary_iterations=50,
    )
    weak_dossier=build_forecast_trust_dossier_v3(
        weak_candidate,joint_radius_audit=weak_radius,
        deployment_novelty_rows=_novelty(["in_domain"]),
    )

    few_blocks=[[np.full(rows_per_block,0.25) for _ in range(4)] for _ in range(group_count)]
    few_gain,few_groups,few_block_ids=_rows_from_blocks(few_blocks,rows_per_block)
    few_candidate=_candidate(
        "too_few_blocks",few_gain,few_groups,few_block_ids,
        gamma=1.0,region_size=4.0,bootstrap_draws=bootstrap_draws,
    )
    few_radius=audit_joint_robustness_radius(
        few_gain,few_groups,few_block_ids,confidence_level=0.95,
        bootstrap_draws=bootstrap_draws,seed=seed,minimum_blocks_per_group=8,
        search_upper_gamma=10.0,binary_iterations=50,
    )
    few_dossier=build_forecast_trust_dossier_v3(
        few_candidate,joint_radius_audit=few_radius,
        deployment_novelty_rows=_novelty(["in_domain"]),
    )

    sqrt3=math.sqrt(3.0)
    checks={
        "strong_radius_through_upper_adds_no_warning": (
            robust.validation.validation_status=="admitted"
            and robust.joint_radius.status=="robust_through_search_upper"
            and robust.joint_radius.certified_gamma==10.0
            and not robust.joint_radius.warnings
            and robust.decision_trace.operational_status=="admitted"
        ),
        "finite_radius_does_not_rewrite_admitted_validation": (
            breakpoint.validation.validation_status=="admitted"
            and breakpoint.decision_trace.operational_status=="admitted_with_warnings"
        ),
        "finite_radius_warning_is_retained": breakpoint.joint_radius.warnings==("finite_joint_robustness_radius",),
        "finite_radius_break_matches_sqrt3": breakpoint.joint_radius.break_gamma is not None and abs(breakpoint.joint_radius.break_gamma-sqrt3)<=1e-10,
        "finite_radius_boundary_width_le_1e_10": breakpoint.joint_radius.boundary_interval_width is not None and breakpoint.joint_radius.boundary_interval_width<=1e-10,
        "radius_and_strict_extrapolation_warnings_remain_distinct": (
            breakpoint_strict.decision_trace.warning_reasons==("finite_joint_robustness_radius","strict_extrapolation")
            and breakpoint_strict.validation.validation_status=="admitted"
        ),
        "weak_positive_remains_validation_blocked": weak_dossier.validation.validation_status=="blocked",
        "weak_positive_radius_not_certified_warning_retained": (
            weak_dossier.joint_radius.status=="not_certified_at_baseline"
            and "joint_radius_not_certified_at_baseline" in weak_dossier.decision_trace.warning_reasons
        ),
        "too_few_blocks_remains_validation_unavailable": few_dossier.validation.validation_status=="unavailable",
        "too_few_blocks_radius_unavailable_retained": (
            few_dossier.joint_radius.status=="unavailable"
            and "joint_radius_unavailable" in few_dossier.decision_trace.warning_reasons
        ),
        "selection_recommendation_preserved": robust.selection.status=="recommended" and selection.recommended_by_log_score=="robust_balanced",
        "robust_broad_remains_not_pareto": broad_dossier.selection.status=="bias_robust_trusted_not_pareto",
        "aggregate_confidence_score_emitted": all(
            row.aggregate_confidence_score_emitted is False
            for row in (robust,broad_dossier,breakpoint,breakpoint_strict,weak_dossier,few_dossier)
        ),
    }
    return {
        "seed":seed,"bootstrap_draws":bootstrap_draws,
        "robust_recommended_radius_through_upper":robust.as_dict(),
        "validation_admitted_at_gamma_1_5_with_finite_radius":breakpoint.as_dict(),
        "finite_radius_plus_strict_extrapolation":breakpoint_strict.as_dict(),
        "weak_positive_validation_blocked_and_radius_not_certified":weak_dossier.as_dict(),
        "too_few_blocks_validation_and_radius_unavailable":few_dossier.as_dict(),
        "robust_broad_not_pareto_with_radius":broad_dossier.as_dict(),
        "selection":selection.as_dict(),
        "sqrt3":sqrt3,
        "checks":[{"name":name,"passed":bool(value)} for name,value in checks.items()],
        "passed":bool(all(checks.values())),
    }
