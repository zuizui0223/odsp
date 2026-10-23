"""Independent source wind calendar/test eligibility; never open altitude."""
from collections import Counter
from prospective.france_gyps_2019_cerra_wind_prehight import (
    source_center,fetch_cerra,wind_opportunity,original_selected_birds
)
import pytest
import datetime


def bird_xy(bird,day,bin5,lon=3.1,lat=44.12):
    return (f"{day} 09:{bin5:02d}:00",lon,lat,1.0,10,bird)


def test_per_bird_median_study_centroid_equal_weights_birds():
    first={}
    # Bird A has 20 times more records; study center should still be median
    # across 3 bird medians rather than pooled GPS fix centre.
    for i in range(20):
        first["A","2019-05-01",i]=bird_xy("A","2019-05-01",i,lon=2.,lat=42.)
    first["B","2019-05-01",0]=bird_xy("B","2019-05-01",0,lon=3.,lat=44.)
    first["C","2019-05-01",0]=bird_xy("C","2019-05-01",0,lon=4.,lat=46.)
    c=source_center(first,{"A","B","C"})
    assert c["latitude"]==44.0 and c["longitude"]==3.0
    assert c["n_equal_weighted_birds"]==3


def test_cerra_daily_100m_wind_quantiles_from_ALL_calendar_days_only():
    times=[];wind=[];solar=[]
    for d in range(1,32):
        for hour in range(24):
            times.append(f"2019-01-{d:02d}T{hour:02d}:00")
            wind.append(float(d))
            solar.append(float(hour*2))
    def provider(url):
        assert "models=cerra" in url
        assert "timezone=UTC" in url
        return {
          "utc_offset_seconds":0,"latitude":44.11,"longitude":3.2,
          "hourly_units":{"wind_speed_100m":"m/s"},
          "hourly":{"time":times,"wind_speed_100m":wind,
                    "shortwave_radiation":solar}
        }
    z=fetch_cerra(2019,{"latitude":44.1,"longitude":3.2},provider)
    assert z["valid_daily_winds"]==31
    assert z["days_low"]==8
    assert z["days_high"]==8
    assert z["days_middle"]==15
    assert z["monthly_wind_quantile_thresholds"]["2019-01"]["low_max"]==8.5
    assert z["monthly_wind_quantile_thresholds"]["2019-01"]["high_min"]==23.5


def test_wind_states_separately_recur_with_two_independent_other_bird_donors():
    first={}
    labels={}
    for d,state in [("2019-05-11","low"),("2019-05-12","low"),
                    ("2019-05-13","high"),("2019-05-14","high")]:
        labels[d]=state
        for bird in (f"bird{i}" for i in range(10)):
            for minute in range(30):
                first[bird,d,minute]=bird_xy(bird,d,minute)
    a=wind_opportunity(first,{f"bird{i}" for i in range(10)},labels)
    assert a["original_bird_own_wind_same_cell"]["n_individuals"]==10
    assert a["original_bird_own_wind_same_cell"]["scorable_bird_days"]==40
    assert a["shared_species_other_bird_same_yearmonth_wind_context"]["n_individuals"]==10
    assert a["shared_species_other_bird_same_yearmonth_wind_context"]["scorable_bird_days"]==40
    assert a["shared_species_other_bird_same_yearmonth_wind_context"]["scorable_first_5min_fixes"]==1200


def test_shared_species_reference_requires_two_other_birds_both_wind_regimes():
    first={}
    labels={"2019-05-11":"low","2019-05-12":"low",
            "2019-05-13":"high","2019-05-14":"high"}
    for d in labels:
        for bird in ("A","B"):
            for minute in range(25):
                first[bird,d,minute]=bird_xy(bird,d,minute)
    a=wind_opportunity(first,{"A","B"},labels)
    assert a["original_bird_own_wind_same_cell"]["n_individuals"]==2
    assert a["shared_species_other_bird_same_yearmonth_wind_context"]["n_individuals"]==0


def test_no_weather_or_single_state_cannot_be_an_updraft_replication():
    f={}
    for d in ("2019-05-11","2019-05-12"):
        for bird in (f"bird{i}" for i in range(10)):
            for minute in range(25):
                f[bird,d,minute]=bird_xy(bird,d,minute)
    states={"2019-05-11":"low","2019-05-12":"low"}
    z=wind_opportunity(f,{f"bird{i}" for i in range(10)},states)
    assert z["original_bird_own_wind_same_cell"]["n_individuals"]==0
    assert z["shared_species_other_bird_same_yearmonth_wind_context"]["n_individuals"]==0


def test_study_source_roster_cannot_be_inferred_from_28_count_alone():
    x={
        "numeric_native_GPS_height_values_read":False,
        "selected_native_GPS_five_minute_events":742423,
        "selected_biological_animals":30,
        "horizontal_day_eligibility_by_cell_m":{
           "5000":{
              "admitted":True,"admitted_bird_ids":[str(i) for i in range(28)],
              "source_bird_ID_sha256":"wrong"}}
    }
    with pytest.raises(ValueError,match="cohort"):
        original_selected_birds(x)
