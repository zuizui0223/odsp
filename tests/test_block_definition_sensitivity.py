import numpy as np
import pytest

from odsp.block_definition_sensitivity import audit_block_definition_sensitivity


def _simple_rows():
    gains=[];groups=[];fine=[];coarse=[]
    for gi in range(2):
        gid=f"g{gi}"
        for bi in range(8):
            for ri in range(4):
                gains.append(0.20+0.002*bi)
                groups.append(gid)
                fine.append(f"{gid}-b{bi}")
                coarse.append(f"{gid}-b{bi}")
    return np.asarray(gains),tuple(groups),{"fine":tuple(fine),"same_science":tuple(coarse)}


def test_block_definition_sensitivity_returns_stable_positive():
    gain,groups,defs=_simple_rows()
    result=audit_block_definition_sensitivity(
        gain,groups,defs,bootstrap_draws=200,minimum_blocks_per_group=8
    )
    assert result.sensitivity_category=="block_definition_robust_generalizing"
    assert result.robust_category_set==("robust_generalizing",)
    assert result.point_category_set==("generalizing",)
    assert result.definition_count==2
    assert result.group_status_flip_count==0
    assert result.no_automatic_block_definition_selection is True
    assert result.aggregate_confidence_score_emitted is False


def test_block_definition_sensitivity_requires_multiple_aligned_definitions():
    gain,groups,defs=_simple_rows()
    with pytest.raises(ValueError):
        audit_block_definition_sensitivity(gain,groups,{"only":defs["fine"]})
    bad=dict(defs)
    bad["fine"]=bad["fine"][:-1]
    with pytest.raises(ValueError):
        audit_block_definition_sensitivity(gain,groups,bad)
