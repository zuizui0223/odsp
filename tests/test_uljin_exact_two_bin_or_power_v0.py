"""Exact balanced two-bin Fisher conditional size and sample-size gates."""
import json
from pathlib import Path

import numpy as np
import pytest

from odsp.uljin_exact_two_bin_or_power_v0 import (
    exact_noncentral_pmf,
    first_exact_upper_tail_rejection_threshold,
    conditional_power_at_n,
    frozen_two_bin_exact_power_panel,
)

ROOT=Path(__file__).resolve().parents[1]
PLAN=json.loads((ROOT/"ULJIN_EXACT_TWO_BIN_OR_POWER_V0_CONTRACT.json").read_text())


def test_small_exact_fisher_null_probabilities_by_enumeration():
    # n=2 -> weights C(2,x)^2 = [1,4,1], sum 6.
    p=exact_noncentral_pmf(2,1.)
    assert p==pytest.approx(np.array([1/6,4/6,1/6]))
    c,size=first_exact_upper_tail_rejection_threshold(p)
    assert c==3 and size==0.
    # Under OR=2, weights [1,8,4], sum 13.
    p2=exact_noncentral_pmf(2,2.)
    assert p2==pytest.approx(np.array([1/13,8/13,4/13]))


def test_exact_one_sided_fisher_size_power_and_conditional_n_units():
    for n in (10,20,40,80,160):
        null=conditional_power_at_n(n,1.)
        assert 0<=null["exact_conditional_null_rejection_size"]<=.05+1e-12
        assert null["exact_conditional_power"]==pytest.approx(
            null["exact_conditional_null_rejection_size"])
        assert null["total_two_bin_detected_events"]==2*n
        p2=conditional_power_at_n(n,2.)
        p3=conditional_power_at_n(n,3.)
        assert p3["exact_conditional_power"]>=p2["exact_conditional_power"]
        assert p2["exact_conditional_power"]>=null["exact_conditional_power"]


def test_frozen_all_n_sample_size_exact_calibration():
    r=frozen_two_bin_exact_power_panel(PLAN)
    assert r["status"]=="SOURCE_FREE_EXACT_CONDITIONAL_SAMPLE_SIZE_ONLY"
    assert r["all_n_null_size_at_most_alpha"]
    assert r["largest_exact_null_rejection_size"]<=0.05+1e-12
    assert r["target_conditional_power"]==.8
    assert r["scanned_n_per_season"]==[5,640]
    assert len(r["grid"])==7*4
    first=r["minimum_n_per_season_at_first_80_percent_power"]
    sustained=r["minimum_n_per_season_sustained_80_percent_through_640"]
    assert set(first)==set(sustained)=={"1.5","2.0","3.0"}
    assert first["3.0"]<=first["2.0"]<=first["1.5"]
    for k in first:
        assert 5<=first[k]<=sustained[k]<=640
    assert not r["real_event_or_device_operation_rows_read"]
    assert not r["ecological_activity_rate_identified"]
    json.dumps(r,allow_nan=False)


def test_prohibited_effect_tuning_and_numerical_inputs_rejected():
    altered=json.loads(json.dumps(PLAN))
    altered["test"]["alpha"]=.1
    with pytest.raises(ValueError,match="frozen"):
        frozen_two_bin_exact_power_panel(altered)
    with pytest.raises(ValueError):
        exact_noncentral_pmf(2,-1)
    with pytest.raises(ValueError):
        exact_noncentral_pmf(0,1)
    with pytest.raises(ValueError):
        first_exact_upper_tail_rejection_threshold(np.array([-.1,1.1]))
