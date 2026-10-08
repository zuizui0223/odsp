"""Exhaustive exact positive integer completion tests, not ecological data."""
import json
from pathlib import Path
from fractions import Fraction
import numpy as np
import pytest

from odsp.uljin_threeway_margin_identifiability_v0 import (
    WORLD_A,WORLD_B,two_way_margins,
)
from odsp.uljin_threeway_margin_fiber_bounds_v1 import (
    reconstruct_from_early_rise, early_log_odds_ratio,
    exhaustive_fiber_bounds,
)
ROOT=Path(__file__).resolve().parents[1]
PLAN=json.loads((ROOT/"ULJIN_THREEWAY_MARGIN_FIBER_BOUNDS_V1_CONTRACT.json").read_text())
LEDGER=json.loads((ROOT/"ULJIN_THREEWAY_MARGIN_IDENTIFIABILITY_V0_FIRST_RESULT_LEDGER.json").read_text())


def test_parent_positive_integer_witnesses_and_both_directions():
    margins=two_way_margins(WORLD_A)
    for x in (WORLD_A,WORLD_B):
        a=reconstruct_from_early_rise(
            tuple(int(v) for v in x[0,0].tolist()),margins)
        assert np.array_equal(a,x)
    assert early_log_odds_ratio(WORLD_A)[0]==Fraction(1)
    assert early_log_odds_ratio(WORLD_B)[0]<1

    # Construct a third valid completion with the opposing sign.
    x=list(WORLD_A[0,0].tolist())
    x[0]-=1
    x[5]+=1
    reverse=reconstruct_from_early_rise(tuple(x),margins)
    assert early_log_odds_ratio(reverse)[0]>1


def test_exact_fiber_has_both_directions_plus_zero_under_same_margins():
    out=exhaustive_fiber_bounds(PLAN,LEDGER)
    assert out["status"]=="EXHAUSTIVE_INTEGER_FIBER_SIGN_NOT_IDENTIFIED_SOURCE_FREE"
    assert out["original_world_A_inside_fiber"]
    assert out["original_world_B_inside_fiber"]
    assert out["both_signs_and_null_possible_for_same_pairwise_margins"]
    assert out["admissible_positive_integer_complete_table_count"]>3
    rows=out["by_direction"]["autumn_relative_early_minus_late"]
    assert min(rows.values())>0
    assert sum(rows.values())==out["admissible_positive_integer_complete_table_count"]
    lower=out["min_early_site_first_vs_last_branch_odds_ratio"]
    upper=out["max_early_site_first_vs_last_branch_odds_ratio"]
    assert lower["odds_ratio"]<1<upper["odds_ratio"]
    assert lower["log_odds_ratio"]<0<upper["log_odds_ratio"]
    m=two_way_margins(WORLD_A)
    for source in (lower,upper):
        arr=np.asarray(source["complete_site_branch_phase_table"])
        assert np.min(arr)>=1
        assert all(np.array_equal(g,m[k]) for k,g in two_way_margins(arr).items())
    assert not out["statistical_confidence_interval_computed"]
    assert not out["real_camera_events_or_uptime_read"]
    json.dumps(out,allow_nan=False)


def test_exact_fiber_repeatability_and_prior_receipt_provenance():
    a=exhaustive_fiber_bounds(PLAN,LEDGER)
    b=exhaustive_fiber_bounds(PLAN,LEDGER)
    assert a==b
    other=json.loads(json.dumps(LEDGER))
    other["first_ci_run"]=0
    with pytest.raises(ValueError,match="frozen"):
        exhaustive_fiber_bounds(PLAN,other)
    tampered=json.loads(json.dumps(PLAN))
    tampered["fiber_constraints"]["strictly_positive_cell_minimum"]=0
    with pytest.raises(ValueError,match="frozen"):
        exhaustive_fiber_bounds(tampered,LEDGER)


def test_reconstructor_fail_closed_on_missing_or_nonpositive_cell():
    m=two_way_margins(WORLD_A)
    with pytest.raises(ValueError):
        reconstruct_from_early_rise((0,6,6,6,6,6),m)
    with pytest.raises(ValueError):
        reconstruct_from_early_rise((50,6,6,6,6),m)
    with pytest.raises(ValueError):
        reconstruct_from_early_rise((48,50,6,6,6,6),m)
