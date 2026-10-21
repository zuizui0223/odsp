"""Synthetic source-independent tests of frozen Gyps wind/uplift height shapes."""
import numpy as np

from prospective.gyps_thermal_height_kernel import (
    center_bins,pack_profiles,score,permute_day_states,calibrate
)


def ten_bird_profiles(condition_difference=True):
    sessions=[]
    labels={}
    for i in range(10):
        bird=f"b{i:02d}"
        for d,state in [("2018-05-11",0),("2018-05-12",0),
                        ("2018-05-13",1),("2018-05-14",1)]:
            hist=np.zeros(10,dtype=np.int64)
            hist[(2 if state==0 else 7) if condition_difference else 5]=60
            sessions.append({"bird":bird,"day":d,"hists":{(5,6):hist}})
            labels[bird,d]=state
    return sessions,labels


def test_fixed_bird_day_center_removes_tag_constant_offset():
    assert np.array_equal(
        center_bins([10,20,60,100]),
        center_bins([1010,1020,1060,1100])
    )


def test_wind_context_helps_predict_same_bird_heldout_day():
    profiles,labels=ten_bird_profiles()
    packed=pack_profiles(profiles,labels)
    result=score(packed)
    assert result["eligible_birds"]==10
    assert result["eligible_bird_days"]==40
    assert result["scored_fixes"]==2400
    assert result["mean_gain"]>0
    assert len(result["per_bird"])==10


def test_if_all_weather_days_have_identical_shape_context_gain_zero():
    profiles,labels=ten_bird_profiles(condition_difference=False)
    result=score(pack_profiles(profiles,labels))
    assert result["eligible_birds"]==10
    assert abs(result["mean_gain"])<1e-11


def test_day_state_randomization_preserves_each_birds_date_count_in_month():
    profiles,labels=ten_bird_profiles()
    p=pack_profiles(profiles,labels)
    state=permute_day_states(p,np.random.default_rng(23))
    for group in p["groups"]:
        assert sorted(p["labels"][group])==sorted(state[group])
    assert np.mean(state!=p["labels"])>0


def test_not_enough_donor_days_yields_unavailable():
    profiles,labels=ten_bird_profiles()
    for (bird,day),state in labels.items():
        if day=="2018-05-14":
            labels[bird,day]=-1
    result=score(pack_profiles(profiles,labels))
    assert result["eligible_birds"]==0
    assert result["mean_gain"] is None


def test_same_day_other_flocks_cannot_fake_other_date_support():
    profiles,labels=ten_bird_profiles()
    reduced=[p for p in profiles if p["day"]=="2018-05-11"]
    result=score(pack_profiles(reduced,labels))
    assert result["eligible_birds"]==0


def test_conservative_null_p_includes_unavailable_draws():
    o={"mean_gain":.1}
    draws=[{"mean_gain":0,"eligible_birds":10},
           {"mean_gain":None,"eligible_birds":5},
           {"mean_gain":.2,"eligible_birds":11}]
    c=calibrate(o,draws)
    assert c["p_lower"]==2/4
    assert c["p_upper"]==3/4
