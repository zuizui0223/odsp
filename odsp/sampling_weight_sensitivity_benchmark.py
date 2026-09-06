"""Known-truth benchmark for sampling-weight sensitivity audits."""
from __future__ import annotations

from collections import OrderedDict
import numpy as np

from .sampling_weight_sensitivity import audit_sampling_weight_sensitivity


def _stable_rows(group_count: int, blocks_per_group: int, rows_per_block: int):
    gain=[]; groups=[]; blocks=[]; effort=[]
    for gi in range(group_count):
        gid=f"group-{gi+1:02d}"
        for bi in range(blocks_per_group):
            bid=f"{gid}-block-{bi+1:02d}"
            base=0.25+0.002*(gi-2.5)+0.01*((bi-(blocks_per_group-1)/2)/blocks_per_group)
            for ri in range(rows_per_block):
                gain.append(base+0.002*((ri-(rows_per_block-1)/2)/rows_per_block))
                groups.append(gid); blocks.append(bid)
                effort.append(0.75+0.5*((ri+bi)%rows_per_block)/(rows_per_block-1))
    return np.asarray(gain),tuple(groups),tuple(blocks),np.asarray(effort)


def _sensitive_rows(group_count: int, blocks_per_group: int, rows_per_block: int):
    if rows_per_block % 2:
        raise ValueError("rows_per_block must be even")
    gain=[]; groups=[]; blocks=[]; positive_mask=[]
    half=rows_per_block//2
    for gi in range(group_count):
        gid=f"group-{gi+1:02d}"
        for bi in range(blocks_per_group):
            bid=f"{gid}-block-{bi+1:02d}"
            for ri in range(rows_per_block):
                positive=ri<half
                gain.append(0.40 if positive else -0.10)
                groups.append(gid); blocks.append(bid); positive_mask.append(positive)
    return np.asarray(gain),tuple(groups),tuple(blocks),np.asarray(positive_mask,dtype=bool)


def _scenario_map_stable(effort: np.ndarray):
    return OrderedDict([
        ("uniform", np.ones(effort.size)),
        ("mild_effort", effort),
        ("inverse_effort", 1.0/effort),
    ])


def _scenario_map_sensitive(positive: np.ndarray):
    return OrderedDict([
        ("uniform", np.ones(positive.size)),
        ("downweight_positive", np.where(positive,0.25,1.0)),
        ("upweight_negative", np.where(positive,0.10,1.0)),
    ])


def run_sampling_weight_sensitivity_benchmark(
    *, seed: int=20260906, bootstrap_draws: int=2000
) -> dict[str,object]:
    group_count=6; blocks_per_group=20; rows_per_block=20
    stable_gain,stable_groups,stable_blocks,effort=_stable_rows(group_count,blocks_per_group,rows_per_block)
    stable_scenarios=_scenario_map_stable(effort)
    stable=audit_sampling_weight_sensitivity(
        stable_gain,stable_groups,stable_scenarios,blocks=stable_blocks,
        confidence_level=0.95,bootstrap_draws=bootstrap_draws,seed=seed,
        minimum_blocks_per_group=8,
    )

    sensitive_gain,sensitive_groups,sensitive_blocks,positive=_sensitive_rows(group_count,blocks_per_group,rows_per_block)
    sensitive_scenarios=_scenario_map_sensitive(positive)
    sensitive=audit_sampling_weight_sensitivity(
        sensitive_gain,sensitive_groups,sensitive_scenarios,blocks=sensitive_blocks,
        confidence_level=0.95,bootstrap_draws=bootstrap_draws,seed=seed,
        minimum_blocks_per_group=8,
    )

    scaled_scenarios=OrderedDict((name,weight*100.0) for name,weight in stable_scenarios.items())
    scaled=audit_sampling_weight_sensitivity(
        stable_gain,stable_groups,scaled_scenarios,blocks=stable_blocks,
        confidence_level=0.95,bootstrap_draws=bootstrap_draws,seed=seed,
        minimum_blocks_per_group=8,
    )
    reversed_scenarios=OrderedDict(reversed(list(stable_scenarios.items())))
    reordered=audit_sampling_weight_sensitivity(
        stable_gain,stable_groups,reversed_scenarios,blocks=stable_blocks,
        confidence_level=0.95,bootstrap_draws=bootstrap_draws,seed=seed,
        minimum_blocks_per_group=8,
    )

    # Too few independent blocks despite many rows.
    few_gain=[];few_groups=[];few_blocks=[]
    for gi in range(group_count):
        gid=f"group-{gi+1:02d}"
        for bi in range(4):
            bid=f"{gid}-block-{bi+1}"
            few_gain.extend([0.25]*100);few_groups.extend([gid]*100);few_blocks.extend([bid]*100)
    few_gain=np.asarray(few_gain)
    few_scenarios=OrderedDict([
        ("uniform",np.ones(few_gain.size)),
        ("effort",np.linspace(0.5,1.5,few_gain.size)),
    ])
    few=audit_sampling_weight_sensitivity(
        few_gain,tuple(few_groups),few_scenarios,blocks=tuple(few_blocks),
        confidence_level=0.95,bootstrap_draws=bootstrap_draws,seed=seed,
        minimum_blocks_per_group=8,
    )

    stable_by={row.name:row for row in stable.scenarios}
    sensitive_by={row.name:row for row in sensitive.scenarios}
    scaled_by={row.name:row for row in scaled.scenarios}
    reordered_by={row.name:row for row in reordered.scenarios}
    scale_error=max(abs(stable_by[name].mean_gain-scaled_by[name].mean_gain) for name in stable_by)
    reorder_error=max(abs(stable_by[name].mean_gain-reordered_by[name].mean_gain) for name in stable_by)

    checks={
        "stable_all_robust_generalizing": all(row.robust_transfer_category=="robust_generalizing" for row in stable.scenarios),
        "stable_category": stable.sensitivity_category=="weight_robust_generalizing",
        "sensitive_uniform_robust_generalizing": sensitive_by["uniform"].robust_transfer_category=="robust_generalizing",
        "sensitive_downweight_positive_not_generalizing": sensitive_by["downweight_positive"].robust_transfer_category=="robust_non_generalizing",
        "sensitive_upweight_negative_robust_non_generalizing": sensitive_by["upweight_negative"].robust_transfer_category=="robust_non_generalizing",
        "sensitive_category": sensitive.sensitivity_category=="weight_sensitive",
        "global_weight_scaling_invariant": scale_error<=1e-15 and scaled.sensitivity_category==stable.sensitivity_category,
        "scenario_order_invariant": reorder_error<=1e-15 and reordered.sensitivity_category==stable.sensitivity_category,
        "too_few_blocks_stable_unavailable": few.sensitivity_category=="stable_unavailable" and all(row.robust_transfer_category=="unavailable" for row in few.scenarios),
        "no_automatic_bias_correction": all(not audit.automatic_bias_correction_performed for audit in (stable,sensitive,scaled,reordered,few)),
        "no_aggregate_confidence": all(not audit.aggregate_confidence_score_emitted for audit in (stable,sensitive,scaled,reordered,few)),
    }
    return {
        "seed":int(seed),"bootstrap_draws":int(bootstrap_draws),
        "group_count":group_count,"blocks_per_group":blocks_per_group,"rows_per_block":rows_per_block,
        "stable":stable.as_dict(),"sensitive":sensitive.as_dict(),"scaled_stable":scaled.as_dict(),
        "reordered_stable":reordered.as_dict(),"too_few_blocks":few.as_dict(),
        "global_scale_mean_gain_error":float(scale_error),"scenario_order_mean_gain_error":float(reorder_error),
        "checks":[{"name":name,"passed":bool(value)} for name,value in checks.items()],
        "passed":bool(all(checks.values())),
    }
