from __future__ import annotations

import numpy as np
import pytest

from odsp.joint_bias_uncertainty_robustness import (
    audit_joint_bias_uncertainty_robustness,
)


def _repeated_blocks(pattern, block_count=20):
    gain=[];groups=[];blocks=[]
    for bi in range(block_count):
        bid=f"g-b{bi+1}"
        gain.extend(pattern);groups.extend(["g"]*len(pattern));blocks.extend([bid]*len(pattern))
    return np.asarray(gain,dtype=float),groups,blocks


def test_envelope_sensitivity_is_retained_inside_bootstrap_audit():
    gain,groups,blocks=_repeated_blocks([0.2]*15+[-0.2]*5)
    result=audit_joint_bias_uncertainty_robustness(
        gain,groups,blocks,gamma=2.0,bootstrap_draws=500,seed=20260906
    )
    row=result.groups[0]
    assert result.point_transfer_category=="generalizing"
    assert result.deterministic_envelope_category=="gamma_sensitive"
    assert result.joint_robust_category=="envelope_sensitive"
    assert row.deterministic_worst_case_gain<0<row.deterministic_best_case_gain
    assert row.worst_case_upper_bound<0
    assert row.best_case_lower_bound>0


def test_too_few_blocks_fail_closed():
    gain,groups,blocks=_repeated_blocks([0.25]*20,block_count=4)
    result=audit_joint_bias_uncertainty_robustness(
        gain,groups,blocks,gamma=2.0,bootstrap_draws=500,minimum_blocks_per_group=8
    )
    assert result.point_transfer_category=="generalizing"
    assert result.joint_robust_category=="unavailable"
    assert result.groups[0].estimable is False


def test_invalid_inputs_fail_closed():
    with pytest.raises(ValueError):
        audit_joint_bias_uncertainty_robustness([0.1],["g"],["b"],gamma=0.5)
    with pytest.raises(ValueError):
        audit_joint_bias_uncertainty_robustness([0.1],["g"],[],gamma=1.0)
