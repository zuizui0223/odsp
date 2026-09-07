"""Known-truth benchmark for Forecast Assessment v2 composition."""
from __future__ import annotations

import numpy as np

from .forecast_assessment import assess_state_forecast
from .forecast_assessment_v2 import assess_state_forecast_v2


def _coverage(groups, fraction: float = 0.90):
    labels=np.asarray(groups,dtype=object)
    covered=np.zeros(len(groups),dtype=bool)
    for gid in tuple(dict.fromkeys(groups)):
        idx=np.flatnonzero(labels==gid)
        covered[idx[:int(round(fraction*idx.size))]]=True
    return covered


def _strong_rows(group_count=6, blocks_per_group=20, rows_per_block=20):
    gain=[];groups=[];blocks=[];paired=[];row_iid=[]
    row_index=0
    for gi in range(group_count):
        gid=f"group-{gi+1:02d}"
        for bi in range(blocks_per_group):
            center=0.30+0.002*(gi-2.5)+0.001*(bi-9.5)
            values=center+np.linspace(-0.01,0.01,rows_per_block)
            for value in values:
                gain.append(float(value));groups.append(gid)
                blocks.append(f"{gid}-block-{bi+1:02d}")
                paired.append(f"{gid}-pair-{bi//2+1:02d}")
                row_iid.append(f"{gid}-row-{row_index:05d}")
                row_index+=1
    return np.asarray(gain),tuple(groups),tuple(blocks),tuple(paired),tuple(row_iid)


def _multiplicity_trap(group_count=20, rows_per_block=25):
    block_means=np.asarray([
        -0.15,-0.10,-0.08,-0.05,-0.03,-0.01,0.01,0.03,0.05,0.07,
        0.09,0.11,0.13,0.15,0.17,0.19,0.21,0.23,0.25,0.27,
    ])
    gain=[];groups=[];blocks=[]
    for gi in range(group_count):
        gid=f"group-{gi+1:02d}"
        for bi,mean in enumerate(block_means):
            gain.extend([float(mean)]*rows_per_block)
            groups.extend([gid]*rows_per_block)
            blocks.extend([f"{gid}-block-{bi+1:02d}"]*rows_per_block)
    return np.asarray(gain),tuple(groups),tuple(blocks)


def _fragile_refits(refit_count=20, group_count=6, blocks_per_group=20, rows_per_block=20):
    gain=[];groups=[];blocks=[]
    for gi in range(group_count):
        gid=f"group-{gi+1:02d}"
        for bi in range(blocks_per_group):
            variation=0.002*(gi-2.5)+0.001*(bi-9.5)+np.linspace(-0.002,0.002,rows_per_block)
            gain.extend((0.30+variation).tolist())
            groups.extend([gid]*rows_per_block)
            blocks.extend([f"{gid}-block-{bi+1:02d}"]*rows_per_block)
    reference=np.asarray(gain,dtype=float)
    variation=reference-0.30
    matrix=np.empty((refit_count,reference.size),dtype=float)
    matrix[:refit_count//2]=0.30+variation
    matrix[refit_count//2:]=-0.20+variation
    ids=tuple(f"refit-{index:02d}" for index in range(refit_count))
    return reference,matrix,tuple(groups),tuple(blocks),ids


def _pseudoreplication(group_count=6, rows_per_block=50):
    block_means=np.asarray([-0.20,-0.10,0.00,0.05,0.10,0.15,0.20,0.25])
    gain=[];groups=[];row_iid=[];clusters=[]
    row_index=0
    for gi in range(group_count):
        gid=f"group-{gi+1:02d}"
        for bi,mean in enumerate(block_means):
            for _ in range(rows_per_block):
                gain.append(float(mean));groups.append(gid)
                row_iid.append(f"{gid}-row-{row_index:05d}")
                clusters.append(f"{gid}-cluster-{bi+1:02d}")
                row_index+=1
    return np.asarray(gain),tuple(groups),tuple(row_iid),tuple(clusters)


def _base_kwargs(gain,groups,blocks):
    n=gain.size
    return dict(
        name="candidate",
        conditional_log_density=gain,
        marginal_log_density=np.zeros(n),
        covered=_coverage(groups),
        groups=groups,
        blocks=blocks,
        region_size=np.full(n,4.0),
        confidence_level=0.95,
        bootstrap_draws=1000,
        seed=20260907,
        minimum_blocks_per_group=8,
    )


def run_forecast_assessment_v2_benchmark(*,seed: int=20260907) -> dict[str,object]:
    if seed!=20260907:
        raise ValueError("the frozen Forecast Assessment v2 benchmark uses seed 20260907")

    strong_gain,strong_groups,strong_blocks,strong_pairs,strong_rows=_strong_rows()
    strong_kwargs=_base_kwargs(strong_gain,strong_groups,strong_blocks)
    stable_offsets=np.r_[0.0,np.linspace(-0.01,0.01,19)]
    stable_refits=strong_gain[None,:]+stable_offsets[:,None]
    stable_ids=tuple(f"refit-{index:02d}" for index in range(20))
    strong=assess_state_forecast_v2(
        **strong_kwargs,
        validation_gamma=1.0,
        run_simultaneous_group_certification=True,
        simultaneous_draws=2000,
        refit_row_gain=stable_refits,
        refit_ids=stable_ids,
        reference_refit_id="refit-00",
        refit_nested_draws=2000,
        minimum_refits=8,
        alternative_block_definitions={"paired_blocks":strong_pairs,"row_iid":strong_rows},
    )
    direct_strong=assess_state_forecast(**strong_kwargs,validation_gamma=1.0)

    trap_gain,trap_groups,trap_blocks=_multiplicity_trap()
    trap=assess_state_forecast_v2(
        **_base_kwargs(trap_gain,trap_groups,trap_blocks),
        validation_gamma=1.0,
        run_simultaneous_group_certification=True,
        simultaneous_draws=2000,
    )

    fragile_gain,fragile_matrix,fragile_groups,fragile_blocks,fragile_ids=_fragile_refits()
    fragile=assess_state_forecast_v2(
        **_base_kwargs(fragile_gain,fragile_groups,fragile_blocks),
        validation_gamma=1.0,
        refit_row_gain=fragile_matrix,
        refit_ids=fragile_ids,
        reference_refit_id="refit-00",
        refit_nested_draws=2000,
        minimum_refits=8,
    )

    pseudo_gain,pseudo_groups,pseudo_rows,pseudo_clusters=_pseudoreplication()
    pseudo=assess_state_forecast_v2(
        **_base_kwargs(pseudo_gain,pseudo_groups,pseudo_rows),
        validation_gamma=1.0,
        alternative_block_definitions={"eight_clusters":pseudo_clusters},
    )

    few_refits=assess_state_forecast_v2(
        **strong_kwargs,
        validation_gamma=1.0,
        refit_row_gain=stable_refits[:4],
        refit_ids=stable_ids[:4],
        reference_refit_id="refit-00",
        refit_nested_draws=2000,
        minimum_refits=8,
    )

    optional=assess_state_forecast_v2(**strong_kwargs,validation_gamma=1.0)

    novelty_train=np.asarray([
        [-1.0,-1.0],[-1.0,0.0],[-1.0,1.0],[0.0,-1.0],[0.0,0.0],
        [0.0,1.0],[1.0,-1.0],[1.0,0.0],[1.0,1.0],[0.5,0.5],
    ])
    novelty_query=np.asarray([[0.0,0.0],[3.0,0.0]])
    strict=assess_state_forecast_v2(
        **strong_kwargs,
        validation_gamma=1.0,
        run_simultaneous_group_certification=True,
        simultaneous_draws=2000,
        novelty_train_X=novelty_train,
        novelty_query_X=novelty_query,
    )

    mismatch_rejected=False
    bad=stable_refits.copy();bad[0]=bad[0]+1e-4
    try:
        assess_state_forecast_v2(
            **strong_kwargs,validation_gamma=1.0,
            refit_row_gain=bad,refit_ids=stable_ids,reference_refit_id="refit-00",
            refit_nested_draws=2000,minimum_refits=8,
        )
    except ValueError as exc:
        mismatch_rejected="does not match" in str(exc)

    checks={
        "strong_case_base_validation_admitted": strong.base_assessment.dossier.validation.validation_status=="admitted",
        "strong_case_simultaneous_certification_passes": strong.simultaneous_group_audit is not None and strong.simultaneous_group_audit.max_t_transfer_category=="robust_generalizing",
        "strong_case_model_refit_certification_passes": strong.model_refit_audit is not None and strong.model_refit_audit.refit_aware_category=="robust_generalizing",
        "strong_case_block_definitions_are_robust": strong.block_definition_audit is not None and strong.block_definition_audit.sensitivity_category=="block_definition_robust_generalizing",
        "strong_case_extended_certification_is_certified": strong.extended_certification.certification_status=="certified" and strong.extended_certification.operational_status=="admitted",
        "multiplicity_trap_base_admitted_but_simultaneous_not_certified": trap.base_assessment.dossier.validation.validation_status=="admitted" and trap.simultaneous_group_audit.max_t_transfer_category=="uncertain" and trap.extended_certification.certification_status=="not_certified",
        "refit_fragile_base_admitted_but_model_refit_not_certified": fragile.base_assessment.dossier.validation.validation_status=="admitted" and fragile.model_refit_audit.reference_fit_category=="robust_generalizing" and fragile.model_refit_audit.refit_aware_category=="uncertain" and fragile.extended_certification.certification_status=="not_certified",
        "block_definition_sensitive_case_keeps_base_admitted_with_design_warning": pseudo.base_assessment.dossier.validation.validation_status=="admitted" and pseudo.block_definition_audit.sensitivity_category=="block_definition_sensitive" and "block_definition_sensitive" in pseudo.extended_certification.warning_reasons,
        "too_few_refits_gives_extended_unavailable_without_rewriting_base": few_refits.base_assessment.dossier.validation.validation_status=="admitted" and few_refits.model_refit_audit.refit_aware_category=="unavailable" and few_refits.extended_certification.certification_status=="unavailable",
        "optional_extended_layers_can_be_omitted": optional.extended_certification.certification_status=="not_audited" and optional.simultaneous_group_audit is None and optional.model_refit_audit is None and optional.block_definition_audit is None,
        "refit_reference_mismatch_is_rejected": mismatch_rejected,
        "strict_extrapolation_warning_remains_distinct_from_extended_certification": strict.base_assessment.dossier.validation.validation_status=="admitted" and strict.extended_certification.certification_status=="certified" and "strict_extrapolation" in strict.extended_certification.warning_reasons and strict.extended_certification.operational_status=="admitted_with_warnings",
        "base_validation_history_is_unchanged_by_extended_layers": strong.base_assessment.as_dict()==direct_strong.as_dict(),
        "aggregate_confidence_score_emitted": not any(row.aggregate_confidence_score_emitted for row in (strong,trap,fragile,pseudo,few_refits,optional,strict)),
    }
    return {
        "seed":seed,
        "strong":strong.as_dict(),
        "multiplicity_trap":trap.as_dict(),
        "refit_fragile":fragile.as_dict(),
        "block_definition_sensitive":pseudo.as_dict(),
        "too_few_refits":few_refits.as_dict(),
        "optional_layers_omitted":optional.as_dict(),
        "strict_extrapolation":strict.as_dict(),
        "refit_reference_mismatch_rejected":mismatch_rejected,
        "checks":[{"name":name,"passed":bool(value)} for name,value in checks.items()],
        "passed":bool(all(checks.values())),
    }
