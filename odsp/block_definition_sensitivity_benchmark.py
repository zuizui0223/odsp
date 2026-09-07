"""Known-truth benchmark for block-definition sensitivity."""
from __future__ import annotations

from collections import OrderedDict
import numpy as np

from .block_definition_sensitivity import audit_block_definition_sensitivity


def _strong_rows(*, sign: float, group_count: int = 6, blocks_per_group: int = 20, rows_per_block: int = 20):
    gain=[];groups=[];true_blocks=[];paired_blocks=[];row_blocks=[]
    row_index=0
    for gi in range(group_count):
        gid=f"group-{gi+1:02d}"
        for bi in range(blocks_per_group):
            center=sign*(0.25+0.002*(gi-2.5)+0.001*(bi-9.5))
            values=center+sign*np.linspace(-0.01,0.01,rows_per_block)
            for value in values:
                gain.append(float(value));groups.append(gid)
                true_blocks.append(f"{gid}-block-{bi+1:02d}")
                paired_blocks.append(f"{gid}-pair-{bi//2+1:02d}")
                row_blocks.append(f"{gid}-row-{row_index:05d}")
                row_index+=1
    return (
        np.asarray(gain,dtype=float),
        tuple(groups),
        OrderedDict([
            ("row_iid",tuple(row_blocks)),
            ("twenty_blocks",tuple(true_blocks)),
            ("ten_paired_blocks",tuple(paired_blocks)),
        ]),
    )


def _pseudoreplication_rows(*, group_count: int = 6, rows_per_block: int = 50):
    block_means=np.asarray([-0.20,-0.10,0.00,0.05,0.10,0.15,0.20,0.25],dtype=float)
    gain=[];groups=[];row_blocks=[];cluster_blocks=[]
    row_index=0
    for gi in range(group_count):
        gid=f"group-{gi+1:02d}"
        for bi,mean in enumerate(block_means):
            for _ in range(rows_per_block):
                gain.append(float(mean));groups.append(gid)
                row_blocks.append(f"{gid}-row-{row_index:05d}")
                cluster_blocks.append(f"{gid}-cluster-{bi+1:02d}")
                row_index+=1
    return (
        np.asarray(gain,dtype=float),
        tuple(groups),
        OrderedDict([
            ("row_iid",tuple(row_blocks)),
            ("eight_clusters",tuple(cluster_blocks)),
        ]),
    )


def _too_coarse_rows(*, group_count: int = 6, rows_per_group: int = 120):
    gain=[];groups=[];four=[];six=[]
    for gi in range(group_count):
        gid=f"group-{gi+1:02d}"
        for ri in range(rows_per_group):
            gain.append(0.25);groups.append(gid)
            four.append(f"{gid}-four-{ri%4}")
            six.append(f"{gid}-six-{ri%6}")
    return np.asarray(gain,dtype=float),tuple(groups),OrderedDict([
        ("four_blocks",tuple(four)),
        ("six_blocks",tuple(six)),
    ])


def run_block_definition_sensitivity_benchmark(
    *,seed: int=20260906,bootstrap_draws: int=2000
) -> dict[str,object]:
    positive_gain,positive_groups,positive_defs=_strong_rows(sign=1.0)
    negative_gain,negative_groups,negative_defs=_strong_rows(sign=-1.0)
    pseudo_gain,pseudo_groups,pseudo_defs=_pseudoreplication_rows()
    coarse_gain,coarse_groups,coarse_defs=_too_coarse_rows()

    common=dict(
        confidence_level=0.95,
        bootstrap_draws=bootstrap_draws,
        seed=seed,
        minimum_blocks_per_group=8,
    )
    positive=audit_block_definition_sensitivity(
        positive_gain,positive_groups,positive_defs,**common
    )
    negative=audit_block_definition_sensitivity(
        negative_gain,negative_groups,negative_defs,**common
    )
    pseudo=audit_block_definition_sensitivity(
        pseudo_gain,pseudo_groups,pseudo_defs,**common
    )
    coarse=audit_block_definition_sensitivity(
        coarse_gain,coarse_groups,coarse_defs,**common
    )

    reversed_defs=OrderedDict(reversed(list(pseudo_defs.items())))
    pseudo_reordered=audit_block_definition_sensitivity(
        pseudo_gain,pseudo_groups,reversed_defs,**common
    )
    pseudo_scaled=audit_block_definition_sensitivity(
        pseudo_gain,pseudo_groups,pseudo_defs,
        sample_weight=np.full(pseudo_gain.size,100.0),**common
    )

    by_name={row.name:row for row in pseudo.definitions}
    row_iid=by_name["row_iid"]
    clustered=by_name["eight_clusters"]
    scaling_error=max(
        abs((a.minimum_group_lower_bound or 0.0)-(b.minimum_group_lower_bound or 0.0))
        for a,b in zip(pseudo.definitions,pseudo_scaled.definitions)
    )

    checks={
        "strong_positive_stable_across_plausible_block_definitions": (
            positive.sensitivity_category=="block_definition_robust_generalizing"
            and all(row.robust_transfer_category=="robust_generalizing" for row in positive.definitions)
        ),
        "strong_negative_stable_across_plausible_block_definitions": (
            negative.sensitivity_category=="block_definition_robust_non_generalizing"
            and all(row.robust_transfer_category=="robust_non_generalizing" for row in negative.definitions)
        ),
        "pseudoreplication_case_is_block_definition_sensitive": pseudo.sensitivity_category=="block_definition_sensitive",
        "pseudoreplication_row_iid_is_robust_generalizing": row_iid.robust_transfer_category=="robust_generalizing",
        "pseudoreplication_clustered_is_uncertain": clustered.robust_transfer_category=="uncertain",
        "pseudoreplication_clustered_lower_bound_below_zero": clustered.minimum_group_lower_bound is not None and clustered.minimum_group_lower_bound<0.0,
        "too_coarse_definitions_are_stable_unavailable": coarse.sensitivity_category=="stable_unavailable" and all(row.robust_transfer_category=="unavailable" for row in coarse.definitions),
        "definition_order_invariant": (
            pseudo.sensitivity_category==pseudo_reordered.sensitivity_category
            and pseudo.robust_category_set==pseudo_reordered.robust_category_set
            and pseudo.group_status_flip_count==pseudo_reordered.group_status_flip_count
        ),
        "positive_global_weight_scaling_invariant": scaling_error<=1e-12 and pseudo.sensitivity_category==pseudo_scaled.sensitivity_category,
        "point_transfer_category_is_definition_invariant": all(len(audit.point_category_set)==1 for audit in (positive,negative,pseudo,coarse)),
        "no_automatic_block_definition_selection": all(audit.no_automatic_block_definition_selection for audit in (positive,negative,pseudo,coarse,pseudo_reordered,pseudo_scaled)),
        "aggregate_confidence_score_emitted": all(not audit.aggregate_confidence_score_emitted for audit in (positive,negative,pseudo,coarse,pseudo_reordered,pseudo_scaled)),
    }
    return {
        "seed":seed,
        "bootstrap_draws":bootstrap_draws,
        "strong_positive":positive.as_dict(),
        "strong_negative":negative.as_dict(),
        "pseudoreplication":pseudo.as_dict(),
        "pseudoreplication_reordered":pseudo_reordered.as_dict(),
        "pseudoreplication_scaled_weights":pseudo_scaled.as_dict(),
        "too_coarse":coarse.as_dict(),
        "pseudoreplication_row_iid_lower_bound":row_iid.minimum_group_lower_bound,
        "pseudoreplication_clustered_lower_bound":clustered.minimum_group_lower_bound,
        "base_weight_scaling_error":float(scaling_error),
        "checks":[{"name":name,"passed":bool(value)} for name,value in checks.items()],
        "passed":bool(all(checks.values())),
    }
