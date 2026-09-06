from __future__ import annotations

import numpy as np

from odsp.joint_robustness_radius import audit_joint_robustness_radius


def _simple_rows(value: float):
    gains=[];groups=[];blocks=[]
    for gi in range(2):
        gid=f"g{gi+1}"
        for bi in range(8):
            bid=f"{gid}-b{bi+1}"
            gains.extend([value]*4);groups.extend([gid]*4);blocks.extend([bid]*4)
    return np.asarray(gains,dtype=float),groups,blocks


def test_positive_signal_is_certified_through_search_upper():
    gain,groups,blocks=_simple_rows(0.25)
    result=audit_joint_robustness_radius(
        gain,groups,blocks,bootstrap_draws=200,seed=20260906,
        minimum_blocks_per_group=8,search_upper_gamma=4.0,binary_iterations=25,
    )
    assert result.radius_status=="robust_through_search_upper"
    assert result.certified_gamma==4.0
    assert result.break_gamma is None
    assert result.radius_is_lower_bound_only is True
    assert result.aggregate_confidence_score_emitted is False


def test_bad_search_upper_is_rejected():
    gain,groups,blocks=_simple_rows(0.25)
    try:
        audit_joint_robustness_radius(gain,groups,blocks,search_upper_gamma=1.0)
    except ValueError:
        return
    raise AssertionError("expected ValueError")
