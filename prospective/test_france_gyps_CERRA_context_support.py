from prospective.france_gyps_CERRA_context_support import source_support,regime_labels
import pytest


def sample(birds=10):
    x={}
    for i in range(birds):
        for day in ("2019-05-10","2019-05-11","2019-05-12","2019-05-13"):
            for k in range(30):
                x[f"bird{i}",day,k]=(day+" 08:00:00",3.25,44.2,1.,10.,"tag")
    return x


def test_same_bird_same_5km_cell_twice_in_low_and_high():
    labels={"2019-05-10":"low","2019-05-11":"low",
            "2019-05-12":"high","2019-05-13":"high"}
    r=source_support(sample(),{f"bird{i}" for i in range(10)},labels)
    assert r["n_eligible_birds"]==10
    assert r["eligible_bird_days"]==40
    assert r["eligible_scored_5min_fixes"]==1200
    assert r["native_altitude_read"] is False


def test_single_bird_not_independent_other_bird():
    labels={"2019-05-10":"low","2019-05-11":"low",
            "2019-05-12":"high","2019-05-13":"high"}
    r=source_support(sample(1),{"bird0"},labels)
    assert r["n_eligible_birds"]==0


def test_one_regime_insufficient():
    labels={day:"low" for b,day,k in sample()}
    r=source_support(sample(),{f"bird{i}" for i in range(10)},labels)
    assert r["n_eligible_birds"]==0


def test_source_monthly_climate_from_all_calendar_days_only():
    with pytest.raises(ValueError,match="coverage"):
        regime_labels({"2019":{"daily":{
          "2019-05-01":{"solar":1.,"wind":2.,"temperature":9.},
          "2019-05-02":{"solar":2.,"wind":3.,"temperature":10.}
        }}})
