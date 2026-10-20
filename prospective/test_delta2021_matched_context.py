"""Synthetic tests for paired tag/bird cross-context comparison (no source outcomes)."""
from pathlib import Path
import json
import numpy as np
from prospective.delta2021_matched_context import compare_matched, corrected_rho


def test_perfect_monotonic_association():
    flight={str(i):{"gain":float(i),"days":3,"bins":100} for i in range(12)}
    still={str(i):{"gain":float(i),"days":4,"bins":150} for i in range(12)}
    result, paired = compare_matched(flight,still,seed=123,draws=99,bootstrap=100)
    assert result["matched_birds"]==12
    assert abs(result["rho"]-1)<1e-10
    assert result["two_sided_permutation_p"]==0.01
    assert result["sign_concordance"]==11
    assert len(paired)==12


def test_bird_intersection_not_union():
    flight={str(i):{"gain":float(i),"days":3,"bins":100} for i in range(14)}
    still={str(i):{"gain":float(i),"days":4,"bins":150} for i in range(4,18)}
    result,paired=compare_matched(flight,still,seed=11,draws=49,bootstrap=100)
    assert result["matched_birds"]==10
    assert [row["animal_id"] for row in paired]==[str(i) for i in range(4,14)]


def test_no_false_numeric_precision_with_constant_stationary_scores():
    flight={str(i):{"gain":float(i),"days":3,"bins":100} for i in range(10)}
    still={str(i):{"gain":0.0,"days":4,"bins":150} for i in range(10)}
    result,paired=compare_matched(flight,still,seed=11,draws=99,bootstrap=100)
    assert result["rho"] is None
    assert result["two_sided_permutation_p"] is None
    assert result["permutation_valid"]==0


def test_ranks_do_not_require_equal_effect_units():
    a=np.array([1,2,4,10],float);b=np.array([200,600,800,900],float)
    assert abs(corrected_rho(a,b)-1)<1e-12
    assert abs(corrected_rho(a,10*b+99)-1)<1e-12
