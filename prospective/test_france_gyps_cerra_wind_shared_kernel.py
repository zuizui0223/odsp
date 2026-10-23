"""Synthetic shared site-date wind swaps and two correlated source channel family."""
import numpy as np
import pytest
from prospective.france_gyps_cerra_wind_shared_kernel import (
    source_wind_labels,sync_weather_shuffle,two_channel_holm,
    pack_profiles,build_shared_context,score_shared_vs_bird
)


def make_source(n=12):
    profiles=[];states={}
    for i in range(n):
        bird=f"bird{i:02d}"
        for d,s in [("2019-05-11","low"),("2019-05-12","low"),
                    ("2019-05-13","high"),("2019-05-14","high"),
                    ("2019-05-15","low"),("2019-05-16","high")]:
            h=np.zeros(10,int)
            h[2 if s=="low" else 7]=60
            profiles.append({"bird":bird,"day":d,"hists":{(50,50):h}})
            states[d]=s
    return profiles,states


def test_same_calendar_day_all_birds_exchange_together():
    p,state=make_source()
    packed=pack_profiles(p,{(bird,day):{"low":0,"high":1}[state[day]]
                            for bird,day in {(row["bird"],row["day"]) for row in p}})
    labels=source_wind_labels(packed,state)
    perm=sync_weather_shuffle(packed,labels,np.random.default_rng(20261023))
    a={}
    for (bird,day),v in zip(packed["bird_days"],perm):
        if day in a:assert a[day]==v
        a[day]=v
    assert sorted(a.values())==[0,0,0,1,1,1]
    assert np.any(perm!=labels)


def test_mismatching_wind_for_same_date_cannot_be_randomized():
    p,state=make_source(2)
    labels_map={(r["bird"],r["day"]):{"low":0,"high":1}[state[r["day"]]] for r in p}
    packed=pack_profiles(p,labels_map)
    labels=source_wind_labels(packed,state)
    other=list(packed["bird_days"]).index(("bird01","2019-05-11"))
    labels[other]=1
    with pytest.raises(ValueError,match="agree"):
        sync_weather_shuffle(packed,labels,np.random.default_rng(13))


def test_species_common_response_support_real_when_animal_days_overlapped():
    p,days=make_source()
    labels={(r["bird"],r["day"]):{"low":0,"high":1}[days[r["day"]]] for r in p}
    packed=pack_profiles(p,labels)
    x=score_shared_vs_bird(packed,build_shared_context(packed))
    assert x["eligible_birds"]==12
    assert x["eligible_bird_days"]==72


def test_source_unavailable_sensor_contributes_one_to_Holm():
    panels={
        "GPS":{"terminal":"tested_before_two_sensor_Holm","calibration":{"p_upper":.01,"observed_minus_null_mean":.1}},
        "BAROMETRIC":{"terminal":"unavailable","calibration":{"p_upper":.001}}
    }
    z=two_channel_holm(panels)
    assert z["GPS"]["holm_upper_p"]==.02
    assert z["BAROMETRIC"]["family_inference_p"]==1.
    assert z["BAROMETRIC"]["terminal"]=="unavailable"


def test_no_sensor_is_selected_on_its_result():
    p={"GPS":{"terminal":"tested_before_two_sensor_Holm","calibration":{"p_upper":.025,"observed_minus_null_mean":.1}},
       "BAROMETRIC":{"terminal":"tested_before_two_sensor_Holm","calibration":{"p_upper":.02,"observed_minus_null_mean":-.1}}}
    out=two_channel_holm(p)
    assert out["GPS"]["holm_upper_p"]==.04
    assert out["BAROMETRIC"]["holm_upper_p"]==.04
    assert out["GPS"]["terminal"]=="supported_exploratory_bird_specific_wind_gain"
    assert out["BAROMETRIC"]["terminal"]=="not_supported_exploratory_bird_specific_wind_gain"
