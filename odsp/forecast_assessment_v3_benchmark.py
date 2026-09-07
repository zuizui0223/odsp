"""Known-truth benchmark for Forecast Assessment v3."""
from __future__ import annotations

import numpy as np

from .forecast_assessment_v2 import assess_state_forecast_v2
from .forecast_assessment_v3 import assess_state_forecast_v3


def _base_design():
    j,k,m,r=6,16,20,12
    groups=tuple(f"group-{g:02d}" for g in range(j) for _ in range(k*m))
    blocks=tuple(f"block-{b:02d}" for _ in range(j) for b in range(k) for _ in range(m))
    group_effect=np.repeat(np.linspace(-0.004,0.004,j),k*m)
    block_effect=np.tile(np.repeat(np.linspace(-0.025,0.025,k),m),j)
    row_effect=np.tile(np.linspace(-0.002,0.002,m),j*k)
    variation=group_effect+block_effect+row_effect
    gain=0.30+variation
    offsets=np.r_[0.0,np.linspace(-0.018,0.018,r-1)]
    bootstrap=gain[None,:]+offsets[:,None]
    fold=gain[None,:]+np.r_[0.0,np.linspace(-0.032,-0.008,r-1)][:,None]
    seed=gain[None,:]+np.r_[0.0,np.linspace(0.008,0.032,r-1)][:,None]
    fragile=np.empty_like(bootstrap)
    fragile[0]=gain
    fragile[1:6]=gain[None,:]+np.linspace(-0.01,0.01,5)[:,None]
    fragile[6:]=(-0.15+variation)[None,:]
    ids={
        "bootstrap":tuple(f"bootstrap-refit-{i:02d}" for i in range(r)),
        "fold":tuple(f"fold-refit-{i:02d}" for i in range(r)),
        "seed":tuple(f"seed-refit-{i:02d}" for i in range(r)),
    }
    covered=np.zeros(len(groups),dtype=bool)
    labels=np.asarray(groups,dtype=object)
    for gid in tuple(dict.fromkeys(groups)):
        idx=np.flatnonzero(labels==gid)
        covered[idx[:int(round(0.90*idx.size))]]=True
    return gain,groups,blocks,covered,bootstrap,fold,seed,fragile,ids


def _common_kwargs(*, bootstrap_draws=800):
    return dict(
        region_size=None,
        target_coverage=0.90,
        coverage_tolerance=0.03,
        validation_gamma=1.5,
        confidence_level=0.95,
        bootstrap_draws=bootstrap_draws,
        seed=20260907,
        minimum_blocks_per_group=8,
        gain_tolerance=0.0,
    )


def _region(n, value=4.0):
    return np.full(n,value,dtype=float)


def _scheme_kwargs(ids, *, sensitive=False, unavailable=False):
    gain,groups,blocks,covered,bootstrap,fold,seed,fragile,_ = _base_design()
    schemes={"bootstrap":bootstrap,"fold":fold,"seed":fragile if sensitive else seed}
    scheme_ids=dict(ids)
    if unavailable:
        schemes["fold"]=fold[:4]
        scheme_ids["fold"]=ids["fold"][:4]
    refs={name:scheme_ids[name][0] for name in schemes}
    return dict(
        refit_schemes=schemes,
        refit_ids_by_scheme=scheme_ids,
        reference_refit_ids_by_scheme=refs,
        scheme_nested_draws=1200,
        scheme_seed=20260907,
        scheme_minimum_refits=8,
    )


def run_forecast_assessment_v3_benchmark(*, seed: int=20260907) -> dict[str,object]:
    if seed!=20260907:
        raise ValueError("the frozen v3 benchmark uses seed 20260907")
    gain,groups,blocks,covered,bootstrap,fold,seed_matrix,fragile,ids=_base_design()
    n=gain.size
    conditional=gain.copy();marginal=np.zeros(n)
    base_kwargs=_common_kwargs()
    base_kwargs["region_size"]=_region(n)

    v2_formal_kwargs=dict(base_kwargs)
    v2_formal_kwargs.update(
        run_simultaneous_group_certification=True,
        simultaneous_draws=1200,
        refit_row_gain=bootstrap,
        refit_ids=ids["bootstrap"],
        reference_refit_id=ids["bootstrap"][0],
        refit_nested_draws=1200,
        minimum_refits=8,
    )
    robust_scheme_kwargs=_scheme_kwargs(ids)
    sensitive_scheme_kwargs=_scheme_kwargs(ids,sensitive=True)
    unavailable_scheme_kwargs=_scheme_kwargs(ids,unavailable=True)

    strong=assess_state_forecast_v3(
        "strong",conditional,marginal,covered,groups,blocks,
        **v2_formal_kwargs,**robust_scheme_kwargs,
    )
    direct_v2=assess_state_forecast_v2(
        "strong",conditional,marginal,covered,groups,blocks,**v2_formal_kwargs
    )
    scheme_sensitive=assess_state_forecast_v3(
        "scheme-sensitive",conditional,marginal,covered,groups,blocks,
        **v2_formal_kwargs,**sensitive_scheme_kwargs,
    )
    scheme_unavailable=assess_state_forecast_v3(
        "scheme-unavailable",conditional,marginal,covered,groups,blocks,
        **v2_formal_kwargs,**unavailable_scheme_kwargs,
    )

    v2_fragile_kwargs=dict(base_kwargs)
    v2_fragile_kwargs.update(
        refit_row_gain=fragile,
        refit_ids=ids["bootstrap"],
        reference_refit_id=ids["bootstrap"][0],
        refit_nested_draws=1200,
        minimum_refits=8,
    )
    already_failed=assess_state_forecast_v3(
        "already-failed",conditional,marginal,covered,groups,blocks,
        **v2_fragile_kwargs,**robust_scheme_kwargs,
    )

    omitted=assess_state_forecast_v3(
        "omitted",conditional,marginal,covered,groups,blocks,**v2_formal_kwargs
    )
    omitted_direct=assess_state_forecast_v2(
        "omitted",conditional,marginal,covered,groups,blocks,**v2_formal_kwargs
    )

    scheme_only=assess_state_forecast_v3(
        "scheme-only",conditional,marginal,covered,groups,blocks,
        **base_kwargs,**robust_scheme_kwargs,
    )

    # Pseudoreplication fixture: row-IID primary blocks pass, eight clusters warn.
    cluster_means=np.asarray([-0.20,-0.10,0.0,0.05,0.10,0.15,0.20,0.25])
    cluster_rows=40
    pseudo_group=[];pseudo_blocks=[];pseudo_alt=[];pseudo_gain=[]
    for g in range(6):
        gid=f"group-{g:02d}"
        for c,mean in enumerate(cluster_means):
            for r in range(cluster_rows):
                pseudo_group.append(gid)
                pseudo_blocks.append(f"{gid}-row-{c*cluster_rows+r:04d}")
                pseudo_alt.append(f"{gid}-cluster-{c:02d}")
                pseudo_gain.append(float(mean))
    pseudo_gain=np.asarray(pseudo_gain)
    pseudo_group=tuple(pseudo_group);pseudo_blocks=tuple(pseudo_blocks);pseudo_alt=tuple(pseudo_alt)
    pseudo_covered=np.zeros(pseudo_gain.size,dtype=bool)
    ga=np.asarray(pseudo_group,dtype=object)
    for gid in tuple(dict.fromkeys(pseudo_group)):
        idx=np.flatnonzero(ga==gid);pseudo_covered[idx[:int(0.9*idx.size)]]=True
    pseudo_refits=np.repeat(pseudo_gain[None,:],12,axis=0)
    pseudo_ids={name:tuple(f"{name}-refit-{i:02d}" for i in range(12)) for name in ("bootstrap","fold","seed")}
    pseudo_schemes={name:pseudo_refits.copy() for name in pseudo_ids}
    block_warning=assess_state_forecast_v3(
        "block-warning",pseudo_gain,np.zeros_like(pseudo_gain),pseudo_covered,pseudo_group,pseudo_blocks,
        region_size=_region(pseudo_gain.size),validation_gamma=1.0,bootstrap_draws=800,
        seed=20260907,minimum_blocks_per_group=8,
        alternative_block_definitions={"eight_cluster":pseudo_alt},
        refit_schemes=pseudo_schemes,refit_ids_by_scheme=pseudo_ids,
        reference_refit_ids_by_scheme={name:ids_[0] for name,ids_ in pseudo_ids.items()},
        scheme_nested_draws=1200,scheme_seed=20260907,scheme_minimum_refits=8,
    )

    # Strict extrapolation is deployment warning only. Requires predict extra.
    train_x=np.column_stack([np.linspace(-1,1,60),np.sin(np.linspace(-2,2,60))])
    query_x=np.asarray([[0.0,0.0],[0.5,0.2],[3.0,0.0]])
    strict=assess_state_forecast_v3(
        "strict",conditional,marginal,covered,groups,blocks,
        **v2_formal_kwargs,**robust_scheme_kwargs,
        novelty_train_X=train_x,novelty_query_X=query_x,
    )

    strong_scheme=strong.refit_scheme_audit
    sensitive_audit=scheme_sensitive.refit_scheme_audit
    checks={
        "strong_v2_certified_plus_scheme_robust_is_v3_certified": strong.base_v2_assessment.extended_certification.certification_status=="certified" and strong_scheme is not None and strong_scheme.sensitivity_category=="scheme_robust_generalizing" and strong.v3_certification.certification_status=="certified",
        "strong_v2_base_assessment_is_preserved_exactly": strong.base_v2_assessment.as_dict()==direct_v2.as_dict(),
        "scheme_sensitive_does_not_rewrite_v2_certification": scheme_sensitive.base_v2_assessment.extended_certification.certification_status=="certified" and sensitive_audit is not None and sensitive_audit.sensitivity_category=="scheme_sensitive",
        "scheme_sensitive_makes_v3_not_certified": scheme_sensitive.v3_certification.certification_status=="not_certified" and "refit_scheme_sensitive" in scheme_sensitive.v3_certification.extended_blocking_reasons,
        "scheme_unavailable_makes_v3_unavailable": scheme_unavailable.refit_scheme_audit is not None and scheme_unavailable.refit_scheme_audit.sensitivity_category=="unavailable" and scheme_unavailable.v3_certification.certification_status=="unavailable",
        "v2_already_not_certified_is_not_rescued_by_scheme_robust": already_failed.base_v2_assessment.extended_certification.certification_status=="not_certified" and already_failed.refit_scheme_audit is not None and already_failed.refit_scheme_audit.sensitivity_category=="scheme_robust_generalizing" and already_failed.v3_certification.certification_status=="not_certified",
        "strict_extrapolation_remains_warning_while_v3_can_be_certified": strict.v3_certification.certification_status=="certified" and strict.v3_certification.operational_status=="admitted_with_warnings" and "strict_extrapolation" in strict.v3_certification.warning_reasons,
        "omitted_scheme_layer_preserves_v2_result_and_certification": omitted.refit_scheme_audit is None and omitted.base_v2_assessment.as_dict()==omitted_direct.as_dict() and omitted.v3_certification.certification_status==omitted_direct.extended_certification.certification_status,
        "scheme_only_formal_layer_can_certify_when_v2_formal_layers_omitted": scheme_only.base_v2_assessment.extended_certification.certification_status=="not_audited" and scheme_only.refit_scheme_audit is not None and scheme_only.refit_scheme_audit.sensitivity_category=="scheme_robust_generalizing" and scheme_only.v3_certification.certification_status=="certified",
        "block_definition_warning_remains_warning_not_scheme_gate": block_warning.refit_scheme_audit is not None and block_warning.refit_scheme_audit.sensitivity_category=="scheme_robust_generalizing" and block_warning.base_v2_assessment.block_definition_audit is not None and block_warning.base_v2_assessment.block_definition_audit.sensitivity_category=="block_definition_sensitive" and block_warning.v3_certification.certification_status=="certified" and "block_definition_sensitive" in block_warning.v3_certification.warning_reasons,
        "scheme_names_and_categories_are_retained": strong_scheme is not None and strong_scheme.scheme_names==("bootstrap","fold","seed") and sensitive_audit is not None and sensitive_audit.scheme_category_set==("robust_generalizing","uncertain"),
        "aggregate_confidence_score_emitted": all(not row.aggregate_confidence_score_emitted for row in (strong,scheme_sensitive,scheme_unavailable,already_failed,omitted,scheme_only,block_warning,strict)),
    }

    return {
        "seed":seed,
        "strong":strong.as_dict(),
        "scheme_sensitive":scheme_sensitive.as_dict(),
        "scheme_unavailable":scheme_unavailable.as_dict(),
        "v2_already_not_certified":already_failed.as_dict(),
        "omitted_scheme":omitted.as_dict(),
        "scheme_only":scheme_only.as_dict(),
        "block_definition_warning":block_warning.as_dict(),
        "strict_extrapolation":strict.as_dict(),
        "checks":[{"name":name,"passed":bool(value)} for name,value in checks.items()],
        "passed":bool(all(checks.values())),
    }
