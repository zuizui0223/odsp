from __future__ import annotations

import math
import numpy as np
import pytest

from odsp.bounded_reweighting_robustness import (
    audit_bounded_reweighting_robustness,
    extreme_bounded_weighted_mean,
)


def test_gamma_one_reduces_to_declared_weighted_mean():
    gain=np.asarray([0.3,-0.1,0.2,0.4])
    weight=np.asarray([1.0,2.0,3.0,4.0])
    expected=float(np.sum(gain*weight)/np.sum(weight))
    assert math.isclose(
        extreme_bounded_weighted_mean(gain,base_weight=weight,gamma=1.0,minimize=True),
        expected,rel_tol=0.0,abs_tol=1e-15,
    )
    assert math.isclose(
        extreme_bounded_weighted_mean(gain,base_weight=weight,gamma=1.0,minimize=False),
        expected,rel_tol=0.0,abs_tol=1e-15,
    )


def test_positive_point_can_be_gamma_sensitive():
    gain=np.r_[np.full(300,0.2),np.full(100,-0.2)]
    groups=["g"]*gain.size
    result=audit_bounded_reweighting_robustness(gain,groups,gamma=2.0)
    row=result.groups[0]
    assert result.point_transfer_category=="generalizing"
    assert result.envelope_transfer_category=="gamma_sensitive"
    assert row.point_mean_gain>0
    assert row.worst_case_mean_gain<0<row.best_case_mean_gain
    assert row.critical_gamma is not None
    assert abs(row.critical_gamma-math.sqrt(3.0))<1e-10
    assert result.automatic_bias_correction_performed is False
    assert result.aggregate_confidence_score_emitted is False


def test_invalid_gamma_and_weights_fail_closed():
    with pytest.raises(ValueError):
        audit_bounded_reweighting_robustness([0.1,0.2],["g","g"],gamma=0.9)
    with pytest.raises(ValueError):
        audit_bounded_reweighting_robustness(
            [0.1,0.2],["g","g"],base_weight=[1.0,-1.0],gamma=2.0
        )
