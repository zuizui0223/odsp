"""Synthetic-only tests: future-year source/meteorology are checked before z."""
import json
import hashlib
import pytest
from prospective import screen_zeebrugge_2017_cerra as src17
from prospective import screen_zeebrugge_cerra_2016 as src16
from prospective.run_zeebrugge_2017_temporal_wind import check_previous_2017_support


def make_source():
    refs=[]
    for i in range(10):
        refs.append({"animal-id":f"bird{i}","tag-id":f"bird{i}",
          "tag-serial-no":f"bird{i}","study-site":"ZEEB_KLVL",
          "deploy-on-date":"2016-05-03 00:00:00",
          "deploy-on-latitude":"51.35","deploy-on-longitude":"3.17"})
    first={}
    tags={}
    regimes={"ZEEB_KLVL":{}}
    for date,state in [("2017-05-11","low"),("2017-05-12","low"),
                       ("2017-05-13","high"),("2017-05-14","high")]:
        regimes["ZEEB_KLVL"][date]=state
        for i in range(10):
            bird=f"bird{i}"
            tags[bird]={(bird,bird)}
            for b in range(60):
                first[bird,date,b]=(date+" 08:00:00.000",3.17,51.35)
    meta=src16.reference_meta(refs)
    info={"response_grid_latitude":51.34,"response_grid_longitude":3.17,
          "complete_weather_days":4,"thresholds_by_month":{
             "2017-05":{"n_calendar_days":4,"q25":3.0,"q75":9.0}
          }}
    weather={"ZEEB_KLVL":info}
    support=src16.xysupport(first,{b:"ZEEB_KLVL" for b in tags},regimes)
    prior={
        "2017_native_altitude_opened":False,
        "GPS_md5":src17.SOURCE_MD5,
        "anchor_2016_site_centers":meta["site_centers"],
        "CERRA_wind":weather,
        "CERRA_site_calendar_state_sha256":hashlib.sha256(
            json.dumps(regimes,sort_keys=True).encode()).hexdigest(),
        "support":support,
    }
    return refs,first,tags,regimes,weather,prior


def test_2017_guard_validates_anchored_wind_and_same_bird_support(monkeypatch):
    refs,first,tags,regimes,weather,prior=make_source()
    monkeypatch.setattr(src17,"site_winds_2017",lambda centers:(weather,regimes))
    mapped,w,l,s=check_previous_2017_support(prior,first,refs,tags)
    assert len(mapped)==10
    assert s["wind_both_regimes_birds"]==10
    assert l==regimes


def test_2017_guard_rejects_climate_relabel_without_reading_height(monkeypatch):
    refs,first,tags,regimes,weather,prior=make_source()
    monkeypatch.setattr(src17,"site_winds_2017",lambda centers:(weather,regimes))
    wrong=dict(prior)
    wrong["CERRA_site_calendar_state_sha256"]="0"*64
    with pytest.raises(ValueError,match="per-site date labels"):
        check_previous_2017_support(wrong,first,refs,tags)


def test_2017_guard_rejects_inspected_source_receipt(monkeypatch):
    refs,first,tags,regimes,weather,prior=make_source()
    wrong=dict(prior)
    wrong["2017_native_altitude_opened"]=True
    with pytest.raises(ValueError,match="already used native height"):
        check_previous_2017_support(wrong,first,refs,tags)
