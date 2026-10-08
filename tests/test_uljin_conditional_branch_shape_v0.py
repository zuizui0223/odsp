"""Known-truth conditional-rate ecological branch-shape tests, synthetic only.

No EcoBank event or camera-operation record is read in these tests.
The original 41 source-free calendar pair identities are untouched.
"""
from __future__ import annotations

import json
import math
import numpy as np
import pytest

from odsp.uljin_conditional_branch_shape_v0 import (
    MirrorCountCell,
    fit_conditional_branch_model,
    expected_falling_probability,
    conditional_logprob,
    score_heldout_station_frame,
)


def _row(site="UJ1-S01", pair="pair-01", bin_no=0, rising=0, falling=0,
         rising_hours=4., falling_hours=4., taxon="synthetic-species"):
    return MirrorCountCell(
        site,site.split("-")[0],taxon,pair,bin_no,
        rising,falling,rising_hours,falling_hours
    )


def _panel(branch_by_bin:bool):
    """Counts generated from fixed, KNOWN conditional probabilities.

    Large cell totals limit deterministic integer rounding noise:
    there is no statistical chance to cherry-pick an outcome.
    """
    train=[]
    test=[]
    betas=([-1.3,-.9,-.4,.4,.9,1.3]
           if branch_by_bin else [.25]*6)
    for s in range(26):
        site=f"{'UJ1' if s%2==0 else 'UJ2'}-site-{s:03d}"
        rows=train if s<16 else test
        for daypair in range(5):
            for k in range(6):
                ea,eb=(4.,2.) if (k+daypair)%2==0 else (3.,4.)
                n=100
                p=expected_falling_probability(ea,eb,betas[k])
                falling=round(n*p)
                rows.append(_row(
                    site,f"p{daypair:02d}",k,n-falling,falling,ea,eb
                ))
    return train,test


def test_known_shape_change_predicts_future_stations_better_than_common_rate():
    train,test=_panel(True)
    out=score_heldout_station_frame(train,test)
    assert out["train_physical_sites"]==16
    assert out["test_physical_sites"]==10
    assert out["test_site_equal_mean_conditional_gain"]>.15
    assert all(out["site_region_support"][g]["station_count"]==5 for g in ("UJ1","UJ2"))
    assert out["training_null"]["model"]=="common_branch_rate"
    assert out["training_branch_shape"]["model"]=="branch_by_clock_bin"
    assert out["posterior_or_pvalue_computed"] is False
    assert out["causal_photoperiod_memory_claimed"] is False
    assert out["test_source_is_original_EcoBank"] is False
    assert out["model_exposure_values_are_independently_verified_in_real_EcoBank"] is False
    encoded=json.dumps(out,allow_nan=False)
    assert "UJ1-site-" not in encoded
    assert "UJ2-site-" not in encoded


def test_correct_common_branch_rate_has_no_spurious_improvement_from_shape():
    train,test=_panel(False)
    out=score_heldout_station_frame(train,test)
    assert abs(out["test_site_equal_mean_conditional_gain"])<.0005
    betas=out["training_branch_shape"]["six_branch_log_rate_ratios"]
    assert max(betas)-min(betas)<.03


def test_single_day_detections_are_informative_and_zero_zero_are_retained():
    a=_row(rising=0,falling=4)
    b=_row(rising=3,falling=0,pair="pair-02")
    empty=_row(rising=0,falling=0,pair="pair-03")
    off=_row(rising=0,falling=0,rising_hours=0.,falling_hours=0.,
             pair="pair-04")
    one_sided_exposure=_row(
        rising=0,falling=2,rising_hours=0.,falling_hours=4.,
        pair="pair-05"
    )
    assert a.is_informative and b.is_informative
    assert not empty.is_informative
    assert not off.is_informative
    assert not one_sided_exposure.is_informative
    assert expected_falling_probability(0.,0.,0.) is None
    assert expected_falling_probability(0.,4.,0.)==1.
    assert expected_falling_probability(4.,0.,0.)==0.


def test_nonzero_count_at_zero_operating_hours_is_invalid():
    with pytest.raises(ValueError,match="zero independently logged exposure"):
        _row(rising=1,falling=0,rising_hours=0.,falling_hours=4.)
    with pytest.raises(ValueError,match="hourly camera exposure"):
        _row(rising=0,falling=0,rising_hours=4.1)
    with pytest.raises(ValueError,match="nonnegative"):
        _row(rising=-1,falling=0)


def test_conditioning_eliminates_unknown_baseline_poisson_intensity():
    # p is unaffected by arbitrary nuisance intensity lambda;
    # uneven camera effort needs the explicitly predeclared offset.
    p_equal=expected_falling_probability(4.,4.,0.)
    p_unequal=expected_falling_probability(4.,2.,0.)
    assert p_equal==pytest.approx(.5)
    assert p_unequal==pytest.approx(1/3)
    p_effect=expected_falling_probability(4.,2.,math.log(2.))
    assert p_effect==pytest.approx(.5)


def test_realistic_sparse_all_zero_site_cells_are_kept_in_original_frame():
    train,test=_panel(True)
    station=test[0].station
    # Keep the station in the heldout roster with all count pairs zero.
    modified=[
        _row(site=x.station,pair=x.pair_id,bin_no=x.clock_bin,
             rising=0,falling=0,rising_hours=x.rising_active_hours,
             falling_hours=x.falling_active_hours)
        if x.station==station else x
        for x in test
    ]
    result=score_heldout_station_frame(train,modified)
    assert result["test_physical_sites"]==10
    assert result["site_region_support"]["UJ1"]["station_count"]==5
    assert result["zero_zero_cells_retained_but_conditionally_noninformative"] is True


def test_duplicate_cell_and_train_test_site_leakage_blocked():
    train,test=_panel(True)
    with pytest.raises(ValueError,match="duplicated physical station"):
        score_heldout_station_frame(train+[train[0]],test)
    with pytest.raises(ValueError,match="disjoint"):
        score_heldout_station_frame(train,test+[train[0]])


def test_model_does_not_fit_without_any_informative_conditional_events():
    rows=[_row(pair=f"p{i:03d}") for i in range(30)]
    with pytest.raises(ValueError,match="insufficient informative"):
        fit_conditional_branch_model(rows,allow_branch_shape=True)


def test_postoutcome_penalty_cannot_be_tuned():
    train,_=_panel(True)
    with pytest.raises(ValueError,match="frozen ridge penalty"):
        fit_conditional_branch_model(train,allow_branch_shape=True,
                                     lambda_penalty=0.)
