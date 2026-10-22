"""Prospective French Gyps 5km ERA5 source gate is altitude-blind."""
from prospective.france_gyps_era5_2019_5km_preheight_gate import (
  COLONY,YEARS,SOURCE_5KM_SHA,score_structural,TAG_ALIAS
)


def synthetic(n=10,only_one_wind=False):
    first={}
    state={}
    days=["2019-05-11","2019-05-12","2019-05-13","2019-05-14"]
    for index,day in enumerate(days):
        state[day]=0 if index<2 or only_one_wind else 1
        for b in range(n):
            for i in range(30):
                tag=f"T{b}"
                timestamp=f"{day} 08:{i:02d}:00"
                first[f"bird{b}",day,i]=(timestamp,3.25,44.20,2.4,10,tag)
    return first,state


def test_10_birds_have_stable_ordinary_and_low_high_and_species_common_support():
    fixed,wind=synthetic()
    s=score_structural(fixed,wind)
    assert s["ordinary_5km_bird_identity_support"]["birds"]==10
    assert s["5km_own_low_high_regional_wind_support"]["birds"]==10
    assert s["5km_shared_species_wind_reference_support"]["birds"]==10
    assert s["5km_shared_species_wind_reference_support"]["bird_days"]==40
    assert s["5km_shared_species_wind_reference_support"]["selected_GPS_fixes"]==1200
    assert s["height_values_read"] is False


def test_only_one_bird_has_no_other_bird_reference():
    first,w=synthetic(n=1)
    s=score_structural(first,w)
    assert s["ordinary_5km_bird_identity_support"]["birds"]==0
    assert s["5km_shared_species_wind_reference_support"]["admitted"] is False


def test_only_low_wind_no_wind_context_test():
    first,w=synthetic(12,only_one_wind=True)
    s=score_structural(first,w)
    assert s["ordinary_5km_bird_identity_support"]["birds"]==12
    assert s["5km_shared_species_wind_reference_support"]["birds"]==0


def test_weather_protocol_is_colony_independent_of_bird_GPS():
    assert COLONY==(44.2,3.25)
    assert YEARS==(2019,2020,2021)
    assert TAG_ALIAS=="182208"
    assert len(SOURCE_5KM_SHA)==64
