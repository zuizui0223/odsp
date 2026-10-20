"""Synthetic 2017 source and wind pre-height gates; arbitrary height must not parse."""
from prospective.screen_zeebrugge_2017_cerra import (
    find_2017_events, outcome_blind_procedure
)


def row(bird="A",day="2017-05-01",i=0,height="NOT_ALTITUDE",speed="10"):
    hour=8+i//12;minute=(i%12)*5
    return {
        "individual-taxon-canonical-name":"Larus fuscus",
        "individual-local-identifier":bird,
        "tag-local-identifier":bird,
        "timestamp":f"{day} {hour:02d}:{minute:02d}:00.000",
        "location-lat":"51.35","location-long":"3.17",
        "ground-speed":speed,"height-above-msl":height,
    }


def ref(bird,year="2016"):
    return {
        "animal-id":bird,"tag-id":bird,"tag-serial-no":bird,
        "study-site":"ZEEB_KLVL",
        "deploy-on-date":year+"-05-01 00:00:00",
        "deploy-on-latitude":"51.35","deploy-on-longitude":"3.17",
    }


def test_year_fixed_and_height_not_accessed():
    q=[
       row(height="NOT-A-NUMBER"),
       row(day="2016-05-01"),
       row(day="2018-05-01"),
       row(i=1,height="A-DIFFERENT-NONNUMBER"),
    ]
    first,animal,stats=find_2017_events(q)
    assert len(first)==1
    assert "height-above-msl" not in str(first)
    assert stats["counts"]["first_flying_5min_bins"]==1


def test_2016_colony_centres_and_year_2017_weather_gate(monkeypatch):
    refs=[ref(f"bird{i}") for i in range(10)]
    originals={"reference":{"site_centers":{
       "ZEEB_KLVL":{"latitude":51.35,"longitude":3.17,"new_deployments_2016":10}
    }}}
    dates={"2017-05-11":"low","2017-05-12":"low",
           "2017-05-13":"high","2017-05-14":"high"}
    def weather(centers):
        assert centers==originals["reference"]["site_centers"]
        return ({"ZEEB_KLVL":{"response_grid_latitude":51.34,
                                "response_grid_longitude":3.17}},
                {"ZEEB_KLVL":dates})
    monkeypatch.setattr("prospective.screen_zeebrugge_2017_cerra.site_winds_2017",weather)
    rows=[row(bird=f"bird{i}",day=day,i=k,height="NO_2017_HEIGHT")
          for i in range(10) for day in dates for k in range(60)]
    out=outcome_blind_procedure(refs,rows,originals)
    assert out["crosswalk"]["accepted"]
    assert out["support"]["wind_both_regimes_birds"]==10
    assert out["support"]["wind_gate_admitted"]
    assert out["2017_native_altitude_opened"] is False
    assert out["temporal_next_year_validation_only"] is True


def test_single_bird_not_eligible(monkeypatch):
    refs=[ref(f"b{i}") for i in range(3)]
    anchored={"reference":{"site_centers":{
       "ZEEB_KLVL":{"latitude":51.35,"longitude":3.17,"new_deployments_2016":3}
    }}}
    label={"2017-05-11":"low","2017-05-12":"low",
           "2017-05-13":"high","2017-05-14":"high"}
    monkeypatch.setattr("prospective.screen_zeebrugge_2017_cerra.site_winds_2017",
                        lambda centers: ({}, {"ZEEB_KLVL":label}))
    rows=[row(bird="b0",day=day,i=k) for day in label for k in range(60)]
    out=outcome_blind_procedure(refs,rows,anchored)
    assert out["support"]["wind_gate_admitted"] is False
