import numpy as np
from prospective.zeebrugge_cerra_2016_wind_shape import (
    score_context,permute_wind_labels,center_into_hist
)


def fake_sessions(n=10):
    sessions=[]
    birds={f"bird{i}":"ZEEB_KLVL" for i in range(n)}
    labels={"ZEEB_KLVL":{}}
    for day,state in [
        ("2016-05-11","low"),("2016-05-12","low"),
        ("2016-05-13","high"),("2016-05-14","high")
    ]:
        labels["ZEEB_KLVL"][day]=state
        for i in range(n):
            h=np.zeros(10,int)
            h[2 if state=="low" else 7]=30
            sessions.append({"bird":f"bird{i}","day":day,
                "hists":{(300,500):h}})
    return sessions,birds,labels


def test_same_bird_distinct_wind_states_in_same_cell_predict_shape():
    sessions,birds,labels=fake_sessions()
    s=score_context(sessions,birds,labels)
    assert s["eligible_birds"]==10
    assert s["eligible_bird_days"]==40
    assert s["mean_gain"]>0
    assert s["scored_fixes"]==1200


def test_constant_shape_across_wind_has_no_context_gain():
    sessions,birds,labels=fake_sessions()
    for s in sessions:
        h=np.zeros(10,int);h[5]=30
        s["hists"]={(300,500):h}
    o=score_context(sessions,birds,labels)
    assert o["eligible_birds"]==10
    assert o["mean_gain"]<=0  # conditioned reference has fewer donors and smoothing


def test_daily_median_center_removes_additive_device_offset():
    a=center_into_hist([30.,40.,60.,100.])
    b=center_into_hist([730.,740.,760.,800.])
    assert np.array_equal(a,b)


def test_one_wind_state_cannot_be_compared_without_opposite_donors():
    sessions,birds,labels=fake_sessions()
    for site in labels:
        for day in labels[site]:labels[site][day]="low"
    r=score_context(sessions,birds,labels)
    assert r["eligible_birds"]==0


def test_day_label_exchangeability_preserves_grid_month_and_shared_site_sync():
    original={"SITE_A":{"2016-05-11":"low","2016-05-12":"high","2016-05-13":"middle","2016-05-14":"low"},
              "SITE_B":{"2016-05-11":"low","2016-05-12":"high","2016-05-13":"middle","2016-05-14":"low"}}
    weather={"SITE_A":{"response_grid_latitude":51.5,"response_grid_longitude":3.7},
             "SITE_B":{"response_grid_latitude":51.5,"response_grid_longitude":3.7}}
    shuffled=permute_wind_labels(original,weather,np.random.default_rng(42))
    assert shuffled["SITE_A"]==shuffled["SITE_B"]
    assert sorted(shuffled["SITE_A"].values())==sorted(original["SITE_A"].values())
