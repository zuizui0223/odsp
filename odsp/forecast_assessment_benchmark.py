"""Known-truth benchmark for the one-call forecast assessment API."""
from __future__ import annotations

import math
import numpy as np

from .bias_robust_model_selection import (
    compare_bias_robust_candidates,
    evaluate_bias_robust_candidate,
)
from .forecast_assessment import assess_state_forecast


def _rows_from_blocks(block_patterns_by_group, rows_per_block: int):
    gain=[];groups=[];blocks=[]
    for gi,patterns in enumerate(block_patterns_by_group):
        gid=f"group-{gi+1:02d}"
        for bi,pattern in enumerate(patterns):
            bid=f"{gid}-block-{bi+1:02d}"
            values=np.asarray(pattern,dtype=float)
            if values.ndim==0:
                values=np.full(rows_per_block,float(values))
            if values.shape!=(rows_per_block,):
                raise ValueError("unexpected block pattern shape")
            gain.extend(values.tolist());groups.extend([gid]*rows_per_block);blocks.extend([bid]*rows_per_block)
    return np.asarray(gain,dtype=float),tuple(groups),tuple(blocks)


def _coverage(groups, *, failed_group: str | None=None):
    labels=np.asarray(groups,dtype=object)
    covered=np.zeros(len(groups),dtype=bool)
    for gid in tuple(dict.fromkeys(groups)):
        idx=np.flatnonzero(labels==gid)
        fraction=0.60 if gid==failed_group else 0.90
        covered[idx[:int(round(fraction*idx.size))]]=True
    return covered


def _selection_candidate(name,gain,groups,blocks,*,gamma,region_size,bootstrap_draws):
    return evaluate_bias_robust_candidate(
        name,gain,np.zeros_like(gain),_coverage(groups),groups,blocks,
        region_size=np.full(gain.size,region_size),gamma=gamma,
        confidence_level=0.95,bootstrap_draws=bootstrap_draws,seed=20260906,
        minimum_blocks_per_group=8,
    )


def _novelty_training_matrix():
    x=np.linspace(-2.0,2.0,25)
    return np.column_stack([x,np.sin(x)])


def run_forecast_assessment_benchmark(
    *,seed: int=20260906,bootstrap_draws: int=500
) -> dict[str,object]:
    if seed!=20260906:
        raise ValueError("the frozen assessment benchmark uses seed 20260906")
    group_count=6;blocks_per_group=20;rows_per_block=20

    strong_blocks=[]
    for gi in range(group_count):
        local=[]
        for bi in range(blocks_per_group):
            center=0.25+0.002*(gi-2.5)+0.001*(bi-9.5)
            local.append(center+np.linspace(-0.01,0.01,rows_per_block))
        strong_blocks.append(local)
    strong_gain,strong_groups,strong_block_ids=_rows_from_blocks(strong_blocks,rows_per_block)
    strong_covered=_coverage(strong_groups)
    strong_region=np.full(strong_gain.size,4.0)

    broad_blocks=[[np.full(rows_per_block,0.15) for _ in range(blocks_per_group)] for _ in range(group_count)]
    broad_gain,broad_groups,broad_block_ids=_rows_from_blocks(broad_blocks,rows_per_block)
    selection=compare_bias_robust_candidates(
        [
            _selection_candidate("strong",strong_gain,strong_groups,strong_block_ids,gamma=2.0,region_size=4.0,bootstrap_draws=bootstrap_draws),
            _selection_candidate("broad",broad_gain,broad_groups,broad_block_ids,gamma=2.0,region_size=7.0,bootstrap_draws=bootstrap_draws),
        ],
        target_coverage=0.90,coverage_tolerance=0.03,gamma=2.0,
        confidence_level=0.95,bootstrap_draws=bootstrap_draws,minimum_blocks_per_group=8,
    )

    effort=np.linspace(0.75,1.25,strong_gain.size)
    train_X=_novelty_training_matrix()
    strong_full=assess_state_forecast(
        "strong",strong_gain,np.zeros_like(strong_gain),strong_covered,strong_groups,strong_block_ids,
        region_size=strong_region,validation_gamma=2.0,confidence_level=0.95,
        bootstrap_draws=bootstrap_draws,seed=seed,minimum_blocks_per_group=8,
        weight_scenarios={"uniform":np.ones(strong_gain.size),"mild_effort":effort,"inverse_effort":1.0/effort},
        bounded_gamma=2.0,radius_search_upper_gamma=4.0,radius_binary_iterations=40,
        novelty_train_X=train_X,novelty_query_X=train_X[[5,10,15]],selection=selection,
    )
    strong_strict=assess_state_forecast(
        "strong",strong_gain,np.zeros_like(strong_gain),strong_covered,strong_groups,strong_block_ids,
        region_size=strong_region,validation_gamma=2.0,confidence_level=0.95,
        bootstrap_draws=bootstrap_draws,seed=seed,minimum_blocks_per_group=8,
        novelty_train_X=train_X,novelty_query_X=np.asarray([[20.0,20.0]]),selection=selection,
    )
    strong_minimal=assess_state_forecast(
        "strong",strong_gain,np.zeros_like(strong_gain),strong_covered,strong_groups,strong_block_ids,
        region_size=strong_region,validation_gamma=2.0,confidence_level=0.95,
        bootstrap_draws=bootstrap_draws,seed=seed,minimum_blocks_per_group=8,
    )

    weight_pattern=np.r_[np.full(16,0.20),np.full(4,-0.10)]
    weight_blocks=[[weight_pattern.copy() for _ in range(blocks_per_group)] for _ in range(group_count)]
    weight_gain,weight_groups,weight_block_ids=_rows_from_blocks(weight_blocks,rows_per_block)
    positive=weight_gain>0
    weight_sensitive=assess_state_forecast(
        "weight_sensitive",weight_gain,np.zeros_like(weight_gain),_coverage(weight_groups),weight_groups,weight_block_ids,
        region_size=np.full(weight_gain.size,4.5),validation_gamma=2.0,
        confidence_level=0.95,bootstrap_draws=bootstrap_draws,seed=seed,minimum_blocks_per_group=8,
        weight_scenarios={"uniform":np.ones(weight_gain.size),"negative_heavy":np.where(positive,0.10,1.0)},
    )

    breakpoint_pattern=np.r_[np.full(15,0.20),np.full(5,-0.20)]
    breakpoint_blocks=[[breakpoint_pattern.copy() for _ in range(blocks_per_group)] for _ in range(group_count)]
    breakpoint_gain,breakpoint_groups,breakpoint_block_ids=_rows_from_blocks(breakpoint_blocks,rows_per_block)
    breakpoint=assess_state_forecast(
        "breakpoint",breakpoint_gain,np.zeros_like(breakpoint_gain),_coverage(breakpoint_groups),breakpoint_groups,breakpoint_block_ids,
        region_size=np.full(breakpoint_gain.size,4.0),validation_gamma=1.5,
        confidence_level=0.95,bootstrap_draws=bootstrap_draws,seed=seed,minimum_blocks_per_group=8,
        bounded_gamma=2.0,radius_search_upper_gamma=4.0,radius_binary_iterations=50,
    )

    weak_pattern=np.asarray([
        -0.25,-0.20,-0.15,-0.10,-0.08,-0.06,-0.04,-0.02,0.00,0.02,
        0.04,0.06,0.08,0.10,0.12,0.14,0.16,0.18,0.20,0.22,
    ])
    weak_blocks=[weak_pattern+0.001*gi for gi in range(group_count)]
    weak_gain,weak_groups,weak_block_ids=_rows_from_blocks(weak_blocks,rows_per_block)
    weak=assess_state_forecast(
        "weak",weak_gain,np.zeros_like(weak_gain),_coverage(weak_groups),weak_groups,weak_block_ids,
        region_size=np.full(weak_gain.size,4.0),validation_gamma=1.0,
        confidence_level=0.95,bootstrap_draws=bootstrap_draws,seed=seed,minimum_blocks_per_group=8,
    )

    few_blocks=[[np.full(rows_per_block,0.25) for _ in range(4)] for _ in range(group_count)]
    few_gain,few_groups,few_block_ids=_rows_from_blocks(few_blocks,rows_per_block)
    few=assess_state_forecast(
        "few",few_gain,np.zeros_like(few_gain),_coverage(few_groups),few_groups,few_block_ids,
        region_size=np.full(few_gain.size,4.0),validation_gamma=1.0,
        confidence_level=0.95,bootstrap_draws=bootstrap_draws,seed=seed,minimum_blocks_per_group=8,
    )

    sqrt3=math.sqrt(3.0)
    checks={
        "strong_case_admitted": strong_full.dossier.validation.validation_status=="admitted",
        "strong_case_weight_robust_generalizing": (
            strong_full.sampling_weight_audit is not None
            and strong_full.sampling_weight_audit.sensitivity_category=="weight_robust_generalizing"
        ),
        "strong_case_bounded_robust_generalizing": (
            strong_full.bounded_reweighting_audit is not None
            and strong_full.bounded_reweighting_audit.envelope_transfer_category=="gamma_robust_generalizing"
        ),
        "strong_case_radius_robust_through_search_upper": (
            strong_full.joint_radius.status=="robust_through_search_upper"
            and strong_full.joint_radius.certified_gamma==4.0
        ),
        "strict_extrapolation_adds_warning_without_changing_validation_admission": (
            strong_strict.dossier.validation.validation_status=="admitted"
            and strong_strict.dossier.deployment.status=="strict_extrapolation_warning"
            and strong_strict.dossier.decision_trace.operational_status=="admitted_with_warnings"
        ),
        "weight_sensitive_case_remains_validation_admitted_with_warning": (
            weight_sensitive.dossier.validation.validation_status=="admitted"
            and weight_sensitive.sampling_weight_audit is not None
            and weight_sensitive.sampling_weight_audit.sensitivity_category=="weight_sensitive"
            and "sampling_weight_sensitive" in weight_sensitive.dossier.decision_trace.warning_reasons
        ),
        "finite_radius_case_is_validation_admitted_at_gamma_1_5": (
            breakpoint.dossier.validation.validation_status=="admitted"
            and abs(breakpoint.dossier.validation.validation_gamma-1.5)<=1e-15
        ),
        "finite_radius_case_reports_break_near_sqrt3": (
            breakpoint.joint_radius.status=="finite_radius"
            and breakpoint.joint_radius.break_gamma is not None
            and abs(breakpoint.joint_radius.break_gamma-sqrt3)<=1e-10
        ),
        "weak_positive_case_is_validation_blocked": weak.dossier.validation.validation_status=="blocked",
        "too_few_blocks_case_is_validation_unavailable": few.dossier.validation.validation_status=="unavailable",
        "selection_recommendation_is_preserved": strong_full.dossier.selection.status=="recommended",
        "optional_layers_can_be_omitted": (
            strong_minimal.sampling_weight_audit is None
            and strong_minimal.bounded_reweighting_audit is None
            and strong_minimal.joint_radius.status=="not_audited"
            and strong_minimal.dossier.robustness_profile.sampling_weight_status=="not_audited"
            and strong_minimal.dossier.robustness_profile.bounded_reweighting_status=="not_audited"
            and strong_minimal.dossier.deployment.status=="not_audited"
            and strong_minimal.dossier.selection.status=="not_compared"
        ),
        "aggregate_confidence_score_emitted": all(
            not row.aggregate_confidence_score_emitted
            for row in (strong_full,strong_strict,strong_minimal,weight_sensitive,breakpoint,weak,few)
        ),
    }
    return {
        "seed":seed,"bootstrap_draws":bootstrap_draws,
        "strong_full":strong_full.as_dict(),
        "strong_strict_extrapolation":strong_strict.as_dict(),
        "strong_optional_layers_omitted":strong_minimal.as_dict(),
        "weight_sensitive":weight_sensitive.as_dict(),
        "finite_radius":breakpoint.as_dict(),
        "weak_positive":weak.as_dict(),
        "too_few_blocks":few.as_dict(),
        "checks":[{"name":name,"passed":bool(value)} for name,value in checks.items()],
        "passed":bool(all(checks.values())),
    }
