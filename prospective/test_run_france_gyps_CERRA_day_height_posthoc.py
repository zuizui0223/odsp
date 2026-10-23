"""France 5km postoutcome climate extension: synchronized CERRA whole-date null."""
import numpy as np
import pytest
from prospective.run_france_gyps_CERRA_day_height_posthoc import (
    shuffle_full_calendar_days,date_label_map_to_sessions,verify_external_weather
)
from prospective.france_gyps_CERRA_day_height_kernel import (
    pack_profiles,score,MIN_DAY
)

def source_weather(solar_birds=12):
    return {
      "analysis":"FRANCE_GYPS_2019_2021_CERRA_DAY_CONTEXT_XY_NO_HEIGHT_V1",
      "source_original_GPS_zip_md5":"b18cc8004d311d19ff24060f655178bf",
      "prior_5km_biological_roster_hash":"031d6226418cc0291a48d7d4eb44f1cae003df3a411ef3767a5229dbd45b1928",
      "numeric_GPS_height_read":False,
      "numeric_baro_height_read":False,
      "source_support":{"solar":{"n_eligible_birds":solar_birds}},
      "location_WGS84":[44.2,3.25]
    }

def test_altitude_target_scoring_uses_old_50fix_day_min():
    assert MIN_DAY==50

def test_site_date_permutation_is_one_day_label_shared_by_all_birds():
    states={
       "2019-05-11":"low","2019-05-12":"low",
       "2019-05-13":"high","2019-05-14":"high",
       "2019-06-11":"low","2019-06-12":"high"
    }
    shuffled=shuffle_full_calendar_days(states,np.random.default_rng(20261023))
    for month in ("2019-05","2019-06"):
        assert sorted(v for d,v in shuffled.items() if d.startswith(month))==sorted(
            v for d,v in states.items() if d.startswith(month)
        )
    data=[]
    for i in range(10):
        bird=f"b{i}"
        for d,v in sorted(states.items()):
            h=np.zeros(10,np.int64)
            h[2 if v=="low" else 7]=60
            data.append({"bird":bird,"day":d,"hists":{(1,2):h}})
    labels={(r["bird"],r["day"]):0 if states[r["day"]]=="low" else 1 for r in data}
    p=pack_profiles(data,labels)
    new=date_label_map_to_sessions(p,shuffled)
    for day in states:
        ix=[i for i,(_,d) in enumerate(p["bird_days"]) if d==day]
        assert len({int(new[i]) for i in ix})==1

def test_preheight_weather_roster_drift_disallowed():
    assert verify_external_weather(source_weather(12)) is True
    with pytest.raises(ValueError,match="minimum ten"):
        verify_external_weather(source_weather(9))
    tampered=source_weather()
    tampered["numeric_GPS_height_read"]=True
    with pytest.raises(ValueError,match="original outcome-blind"):
        verify_external_weather(tampered)

def test_identical_shape_weather_has_no_synthetic_response():
    states={}
    sessions=[]
    for i in range(10):
        for d,v in [("2019-05-11",0),("2019-05-12",0),
                    ("2019-05-13",1),("2019-05-14",1)]:
            b=f"bird{i}"
            h=np.zeros(10,dtype=np.int64)
            h[5]=60
            sessions.append({"bird":b,"day":d,"hists":{(1,1):h}})
            states[b,d]=v
    out=score(pack_profiles(sessions,states))
    assert out["eligible_birds"]==10
    assert abs(out["mean_gain"])<1e-10
