from __future__ import annotations

import numpy as np
import pytest

from odsp.sampling_weight_sensitivity import audit_sampling_weight_sensitivity


def test_weight_scenarios_can_flip_transfer_conclusion():
    group_count=2; blocks_per_group=20; rows_per_block=20
    gain=[];groups=[];blocks=[];positive=[]
    for gi in range(group_count):
        gid=f"g{gi+1}"
        for bi in range(blocks_per_group):
            bid=f"{gid}-b{bi+1}"
            for ri in range(rows_per_block):
                is_pos=ri<10
                gain.append(0.4 if is_pos else -0.1)
                groups.append(gid);blocks.append(bid);positive.append(is_pos)
    gain=np.asarray(gain);positive=np.asarray(positive,dtype=bool)
    result=audit_sampling_weight_sensitivity(
        gain,groups,
        {"uniform":np.ones(gain.size),"negative_heavy":np.where(positive,0.1,1.0)},
        blocks=blocks,bootstrap_draws=1000,seed=20260906,minimum_blocks_per_group=8,
    )
    by={row.name:row for row in result.scenarios}
    assert by["uniform"].robust_transfer_category=="robust_generalizing"
    assert by["negative_heavy"].robust_transfer_category=="robust_non_generalizing"
    assert result.sensitivity_category=="weight_sensitive"
    assert result.any_robust_category_change is True
    assert result.automatic_bias_correction_performed is False
    assert result.aggregate_confidence_score_emitted is False


def test_requires_multiple_valid_weight_scenarios():
    with pytest.raises(ValueError):
        audit_sampling_weight_sensitivity([0.1,0.2],["g","g"],{"uniform":[1,1]},bootstrap_draws=500)
    with pytest.raises(ValueError):
        audit_sampling_weight_sensitivity([0.1,0.2],["g","g"],{"a":[1,1],"b":[1,-1]},bootstrap_draws=500)
