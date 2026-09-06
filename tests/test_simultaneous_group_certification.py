import numpy as np
import pytest

from odsp.simultaneous_group_certification import audit_simultaneous_group_certification


def _simple_rows(group_count=3, blocks_per_group=10, rows_per_block=4, value=0.25):
    gain=[];groups=[];blocks=[]
    for gi in range(group_count):
        gid=f"g{gi}"
        for bi in range(blocks_per_group):
            gain.extend([value+0.001*bi]*rows_per_block)
            groups.extend([gid]*rows_per_block)
            blocks.extend([f"{gid}-b{bi}"]*rows_per_block)
    return np.asarray(gain,dtype=float),tuple(groups),tuple(blocks)


def test_simultaneous_group_certification_strong_positive():
    gain,groups,blocks=_simple_rows()
    audit=audit_simultaneous_group_certification(
        gain,groups,blocks=blocks,bootstrap_draws=1000,minimum_blocks_per_group=8
    )
    assert audit.max_t_transfer_category=="robust_generalizing"
    assert audit.simultaneous_admissible is True
    assert audit.max_t_critical_value is not None
    assert audit.bonferroni_is_primary is False
    assert audit.aggregate_confidence_score_emitted is False
    assert all(row.max_t_lower_bound>0 for row in audit.groups)


def test_simultaneous_group_certification_unavailable_blocks_global_claim():
    gain,groups,blocks=_simple_rows(blocks_per_group=4)
    audit=audit_simultaneous_group_certification(
        gain,groups,blocks=blocks,bootstrap_draws=1000,minimum_blocks_per_group=8
    )
    assert audit.max_t_transfer_category=="unavailable"
    assert audit.unavailable_group_count==3
    assert audit.simultaneous_admissible is False


def test_simultaneous_group_certification_rejects_bad_shapes():
    gain,groups,blocks=_simple_rows()
    with pytest.raises(ValueError):
        audit_simultaneous_group_certification(gain,groups[:-1],blocks=blocks)
    with pytest.raises(ValueError):
        audit_simultaneous_group_certification(gain,groups,blocks=blocks[:-1])
    with pytest.raises(ValueError):
        audit_simultaneous_group_certification(gain,groups,blocks=blocks,bootstrap_draws=100)
    with pytest.raises(ValueError):
        audit_simultaneous_group_certification(gain,groups,blocks=blocks,familywise_confidence_level=1.0)
