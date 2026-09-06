from __future__ import annotations

import numpy as np

from odsp.bias_robust_model_selection import (
    compare_bias_robust_candidates,
    evaluate_bias_robust_candidate,
)


def _candidate(name: str, gain: np.ndarray, covered: np.ndarray, region_size: float):
    groups=[];blocks=[]
    group_count=2;blocks_per_group=10;rows_per_block=20
    for gi in range(group_count):
        gid=f"g{gi+1}"
        for bi in range(blocks_per_group):
            bid=f"{gid}-b{bi+1}"
            groups.extend([gid]*rows_per_block);blocks.extend([bid]*rows_per_block)
    marginal=np.full(gain.size,-2.0)
    return evaluate_bias_robust_candidate(
        name,marginal+gain,marginal,covered,groups,blocks,
        region_size=np.full(gain.size,region_size),gamma=2.0,
        bootstrap_draws=500,seed=20260906,minimum_blocks_per_group=8,
    )


def test_gamma_fragile_candidate_is_rejected_after_point_trust():
    pattern=np.r_[np.full(15,0.2),np.full(5,-0.2)]
    gain=np.tile(pattern,20)
    covered=np.tile(np.r_[np.ones(180,dtype=bool),np.zeros(20,dtype=bool)],2)
    fragile=_candidate("fragile",gain,covered,2.5)
    assert fragile.point_and_coverage.trusted_admissible is True
    assert fragile.joint_robustness.joint_robust_category=="envelope_sensitive"
    assert fragile.bias_robust_trusted_admissible is False


def test_joint_robust_candidate_reaches_selection():
    gain=np.full(400,0.25)
    covered=np.tile(np.r_[np.ones(180,dtype=bool),np.zeros(20,dtype=bool)],2)
    good=_candidate("good",gain,covered,4.0)
    broad=_candidate("broad",np.full(400,0.15),covered,7.0)
    result=compare_bias_robust_candidates([good,broad],bootstrap_draws=500)
    assert set(result.bias_robust_trusted_names)=={"good","broad"}
    assert result.pareto_front_names==("good",)
    assert result.recommended_by_log_score=="good"
    assert result.aggregate_confidence_score_emitted is False
