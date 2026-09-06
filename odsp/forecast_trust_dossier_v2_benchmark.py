"""Known-truth benchmark for the forecast trust dossier v2."""
from __future__ import annotations

import math
import numpy as np

from .bias_robust_model_selection import (
    BiasRobustCandidateScore,
    compare_bias_robust_candidates,
    evaluate_bias_robust_candidate,
)
from .bounded_reweighting_robustness import audit_bounded_reweighting_robustness
from .forecast_trust_dossier_v2 import build_forecast_trust_dossier_v2
from .prediction_novelty import NoveltySummary
from .sampling_weight_sensitivity import audit_sampling_weight_sensitivity


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


def _candidate(
    name: str,
    gain: np.ndarray,
    groups,
    blocks,
    *,
    gamma: float,
    region_size: float,
    bootstrap_draws: int,
    failed_coverage_group: str | None=None,
) -> BiasRobustCandidateScore:
    return evaluate_bias_robust_candidate(
        name,
        gain,
        np.zeros_like(gain),
        _coverage(groups,failed_group=failed_coverage_group),
        groups,
        blocks,
        region_size=np.full(gain.size,region_size),
        gamma=gamma,
        confidence_level=0.95,
        bootstrap_draws=bootstrap_draws,
        seed=20260906,
        minimum_blocks_per_group=8,
    )


def _novelty(categories):
    rows=[]
    for i,category in enumerate(categories):
        if category=="strict_extrapolation":
            ratio=3.5;outside=(1,)
        elif category=="novel":
            ratio=1.4;outside=()
        else:
            ratio=0.5;outside=()
        rows.append(NoveltySummary(
            row_index=i,
            nearest_scaled_distance=ratio,
            reference_distance=1.0,
            novelty_ratio=ratio,
            outside_feature_count=len(outside),
            outside_feature_indices=outside,
            category=category,
        ))
    return tuple(rows)


def run_forecast_trust_dossier_v2_benchmark(
    *,seed: int=20260906,bootstrap_draws: int=1000
) -> dict[str,object]:
    if seed!=20260906:
        raise ValueError("the frozen dossier benchmark uses seed 20260906")
    group_count=6;blocks_per_group=20;rows_per_block=20

    strong_blocks=[]
    for gi in range(group_count):
        local=[]
        for bi in range(blocks_per_group):
            center=0.25+0.002*(gi-2.5)+0.001*(bi-9.5)
            local.append(center+np.linspace(-0.01,0.01,rows_per_block))
        strong_blocks.append(local)
    strong_gain,strong_groups,strong_block_ids=_rows_from_blocks(strong_blocks,rows_per_block)
    robust_balanced=_candidate(
        "robust_balanced",strong_gain,strong_groups,strong_block_ids,
        gamma=2.0,region_size=4.0,bootstrap_draws=bootstrap_draws,
    )

    broad_blocks=[[np.full(rows_per_block,0.15) for _ in range(blocks_per_group)] for _ in range(group_count)]
    broad_gain,broad_groups,broad_block_ids=_rows_from_blocks(broad_blocks,rows_per_block)
    robust_broad=_candidate(
        "robust_broad",broad_gain,broad_groups,broad_block_ids,
        gamma=2.0,region_size=7.0,bootstrap_draws=bootstrap_draws,
    )

    fragile_pattern=np.r_[np.full(15,0.20),np.full(5,-0.20)]
    fragile_blocks=[[fragile_pattern.copy() for _ in range(blocks_per_group)] for _ in range(group_count)]
    fragile_gain,fragile_groups,fragile_block_ids=_rows_from_blocks(fragile_blocks,rows_per_block)
    gamma_fragile=_candidate(
        "gamma_fragile",fragile_gain,fragile_groups,fragile_block_ids,
        gamma=2.0,region_size=2.5,bootstrap_draws=bootstrap_draws,
    )

    coverage_blocks=[[np.full(rows_per_block,0.40) for _ in range(blocks_per_group)] for _ in range(group_count)]
    coverage_gain,coverage_groups,coverage_block_ids=_rows_from_blocks(coverage_blocks,rows_per_block)
    coverage_failure=_candidate(
        "coverage_failure",coverage_gain,coverage_groups,coverage_block_ids,
        gamma=2.0,region_size=3.0,bootstrap_draws=bootstrap_draws,
        failed_coverage_group="group-01",
    )

    few_blocks=[[np.full(rows_per_block,0.255) for _ in range(4)] for _ in range(group_count)]
    few_gain,few_groups,few_block_ids=_rows_from_blocks(few_blocks,rows_per_block)
    too_few=_candidate(
        "too_few_blocks",few_gain,few_groups,few_block_ids,
        gamma=2.0,region_size=3.5,bootstrap_draws=bootstrap_draws,
    )

    selection=compare_bias_robust_candidates(
        [robust_balanced,gamma_fragile,robust_broad,coverage_failure,too_few],
        target_coverage=0.90,coverage_tolerance=0.03,gamma=2.0,
        confidence_level=0.95,bootstrap_draws=bootstrap_draws,
        minimum_blocks_per_group=8,
    )

    effort=np.linspace(0.75,1.25,strong_gain.size)
    stable_sampling=audit_sampling_weight_sensitivity(
        strong_gain,strong_groups,
        {"uniform":np.ones(strong_gain.size),"mild_effort":effort,"inverse_effort":1.0/effort},
        blocks=strong_block_ids,confidence_level=0.95,bootstrap_draws=bootstrap_draws,
        seed=seed,minimum_blocks_per_group=8,
    )
    strong_bounded=audit_bounded_reweighting_robustness(
        strong_gain,strong_groups,gamma=2.0,
    )
    robust_in_domain=build_forecast_trust_dossier_v2(
        robust_balanced,
        sampling_weight_audit=stable_sampling,
        bounded_reweighting_audit=strong_bounded,
        deployment_novelty_rows=_novelty(["in_domain","in_domain","in_domain"]),
        selection=selection,
    )
    robust_strict=build_forecast_trust_dossier_v2(
        robust_balanced,
        sampling_weight_audit=stable_sampling,
        bounded_reweighting_audit=strong_bounded,
        deployment_novelty_rows=_novelty(["in_domain","in_domain","strict_extrapolation"]),
        selection=selection,
    )

    weight_pattern=np.r_[np.full(16,0.20),np.full(4,-0.10)]
    weight_blocks=[[weight_pattern.copy() for _ in range(blocks_per_group)] for _ in range(group_count)]
    weight_gain,weight_groups,weight_block_ids=_rows_from_blocks(weight_blocks,rows_per_block)
    weight_candidate=_candidate(
        "weight_sensitive_candidate",weight_gain,weight_groups,weight_block_ids,
        gamma=2.0,region_size=4.5,bootstrap_draws=bootstrap_draws,
    )
    positive=weight_gain>0
    weight_sensitivity=audit_sampling_weight_sensitivity(
        weight_gain,weight_groups,
        {"uniform":np.ones(weight_gain.size),"negative_heavy":np.where(positive,0.10,1.0)},
        blocks=weight_block_ids,confidence_level=0.95,bootstrap_draws=bootstrap_draws,
        seed=seed,minimum_blocks_per_group=8,
    )
    weight_bounded=audit_bounded_reweighting_robustness(weight_gain,weight_groups,gamma=2.0)
    weight_sensitive=build_forecast_trust_dossier_v2(
        weight_candidate,
        sampling_weight_audit=weight_sensitivity,
        bounded_reweighting_audit=weight_bounded,
        deployment_novelty_rows=_novelty(["in_domain"]),
    )

    breakpoint_candidate=_candidate(
        "breakpoint_candidate",fragile_gain,fragile_groups,fragile_block_ids,
        gamma=1.5,region_size=4.0,bootstrap_draws=bootstrap_draws,
    )
    breakpoint_bounded=audit_bounded_reweighting_robustness(
        fragile_gain,fragile_groups,gamma=2.0,
    )
    breakpoint=build_forecast_trust_dossier_v2(
        breakpoint_candidate,
        bounded_reweighting_audit=breakpoint_bounded,
        deployment_novelty_rows=_novelty(["in_domain"]),
    )

    fragile_dossier=build_forecast_trust_dossier_v2(
        gamma_fragile,
        bounded_reweighting_audit=audit_bounded_reweighting_robustness(fragile_gain,fragile_groups,gamma=2.0),
        deployment_novelty_rows=_novelty(["in_domain"]),
        selection=selection,
    )
    few_dossier=build_forecast_trust_dossier_v2(
        too_few,
        deployment_novelty_rows=_novelty(["in_domain"]),
        selection=selection,
    )
    broad_dossier=build_forecast_trust_dossier_v2(
        robust_broad,
        deployment_novelty_rows=_novelty(["in_domain"]),
        selection=selection,
    )

    sqrt3=math.sqrt(3.0)
    checks={
        "robust_recommended_in_domain_has_no_blocker_or_warning": (
            robust_in_domain.validation.validation_status=="admitted"
            and robust_in_domain.decision_trace.operational_status=="admitted"
            and not robust_in_domain.decision_trace.blocking_reasons
            and not robust_in_domain.decision_trace.warning_reasons
            and robust_in_domain.selection.status=="recommended"
        ),
        "strict_extrapolation_is_deployment_warning_only": (
            robust_strict.validation.validation_status=="admitted"
            and robust_strict.decision_trace.operational_status=="admitted_with_warnings"
            and not robust_strict.decision_trace.blocking_reasons
            and robust_strict.deployment.status=="strict_extrapolation_warning"
            and robust_strict.decision_trace.warning_reasons==("strict_extrapolation",)
        ),
        "sampling_weight_sensitive_case_remains_validation_admitted": (
            weight_sensitive.validation.validation_status=="admitted"
            and weight_sensitive.validation.joint_robustness_category=="joint_robust_generalizing"
        ),
        "sampling_weight_sensitive_warning_is_retained": (
            weight_sensitive.robustness_profile.sampling_weight_status=="weight_sensitive"
            and "sampling_weight_sensitive" in weight_sensitive.decision_trace.warning_reasons
            and weight_sensitive.decision_trace.operational_status=="admitted_with_warnings"
        ),
        "breakpoint_case_validation_admitted_at_gamma_1_5": (
            breakpoint.validation.validation_status=="admitted"
            and abs(breakpoint.validation.validation_gamma-1.5)<=1e-15
        ),
        "breakpoint_case_gamma_2_is_sensitive": (
            breakpoint.robustness_profile.bounded_gamma==2.0
            and breakpoint.robustness_profile.bounded_reweighting_status=="gamma_sensitive"
            and "bounded_reweighting_sensitive" in breakpoint.decision_trace.warning_reasons
        ),
        "breakpoint_case_minimum_critical_gamma_equals_sqrt3": (
            breakpoint.robustness_profile.minimum_critical_gamma is not None
            and abs(breakpoint.robustness_profile.minimum_critical_gamma-sqrt3)<=1e-10
        ),
        "joint_envelope_sensitive_case_is_validation_blocked": (
            fragile_dossier.validation.validation_status=="blocked"
            and fragile_dossier.validation.joint_robustness_category=="envelope_sensitive"
            and "joint_reweighting_sensitive" in fragile_dossier.validation.blocking_reasons
        ),
        "too_few_blocks_case_is_validation_unavailable": (
            few_dossier.validation.validation_status=="unavailable"
            and "joint_transfer_unavailable" in few_dossier.validation.blocking_reasons
        ),
        "robust_broad_selection_status_is_not_pareto": (
            broad_dossier.selection.status=="bias_robust_trusted_not_pareto"
            and broad_dossier.selection.bias_robust_trusted
            and not broad_dossier.selection.pareto_member
        ),
        "selection_recommendation_is_preserved": selection.recommended_by_log_score=="robust_balanced",
        "aggregate_confidence_score_emitted": all(
            dossier.aggregate_confidence_score_emitted is False
            for dossier in (robust_in_domain,robust_strict,weight_sensitive,breakpoint,fragile_dossier,few_dossier,broad_dossier)
        ),
    }

    return {
        "seed":seed,"bootstrap_draws":bootstrap_draws,
        "robust_recommended_in_domain":robust_in_domain.as_dict(),
        "robust_recommended_strict_extrapolation":robust_strict.as_dict(),
        "validation_admitted_but_sampling_weight_sensitive":weight_sensitive.as_dict(),
        "validation_admitted_at_gamma_1_5_but_breaks_by_gamma_2":breakpoint.as_dict(),
        "joint_envelope_sensitive_validation_blocked":fragile_dossier.as_dict(),
        "too_few_blocks_validation_unavailable":few_dossier.as_dict(),
        "robust_broad_not_pareto":broad_dossier.as_dict(),
        "selection":selection.as_dict(),
        "checks":[{"name":name,"passed":bool(value)} for name,value in checks.items()],
        "passed":bool(all(checks.values())),
    }
