"""Known-truth ecological mechanisms, not posthoc camera trap outcome search."""
from __future__ import annotations

from datetime import date
import json
import math

import numpy as np
import pytest

from odsp.ri_solar_clock_transfer_v0 import (
    VERSION, DielEvent, cached_solar_times,
    equinoctial_solar_phase, fit_species_profiles,
    score_new_site_future_year, site_is_sealed,
    solar_phase_to_civil_bin_matrix, sunrise_sunset_local,
    summarize_site_level_transfer, _phase_to_unwrapped_civil,
)


def _sites(count, sealed):
    chosen=[]
    for i in range(20000):
        site=f"synthetic-ri-site-{i:05d}"
        if site_is_sealed(site)==sealed:
            chosen.append(site)
            if len(chosen)==count:
                return chosen
    raise AssertionError("test fixture not enough deterministic sites")


def _events(site_list, years, mechanism, *, per_unit=24):
    events=[]
    for site_index,site in enumerate(site_list):
        lat=41.3+.003*(site_index%5)
        lon=-71.5-.004*(site_index%5)
        for yr in years:
            for season,month,daynum in (
                ("winter",1,12),
                ("summer",7,15),
            ):
                day=date(yr,month,daynum)
                sr,ss=sunrise_sunset_local(day,lat,lon)
                for j in range(per_unit):
                    phase_fraction=(j//2+0.5)/(per_unit//2)
                    if mechanism=="sun":
                        # Uniform SOLAR phase within two dawn/dusk bins.
                        # This known-truth distribution matches the histogram
                        # density family, not sharp within-bin point masses.
                        phase=(4. if j%2==0 else 16.)+4.*phase_fraction
                        clock=_phase_to_unwrapped_civil(phase,sr,ss)%24
                    elif mechanism=="civil":
                        # Uniform HUMAN CLOCK times within two fixed bins.
                        clock=(4. if j%2==0 else 16.)+4.*phase_fraction
                    else:
                        raise AssertionError("unknown simulation mechanism")
                    events.append(DielEvent(
                        site_id=site,species="synthetic fox",season=season,
                        season_year=yr,day=day,clock_hour=clock,
                        latitude=lat,longitude=lon,
                    ))
    return events


def test_geometry_matches_approximate_ri_solar_days_and_dst():
    winter=sunrise_sunset_local(date(2022,12,21),41.5,-71.5)
    summer=sunrise_sunset_local(date(2022,6,21),41.5,-71.5)
    assert 6.5 < winter[0] < 7.6
    assert 15.5 < winter[1] < 17.1
    assert 4.6 < summer[0] < 5.6
    assert 19.5 < summer[1] < 21.0
    assert summer[1]-summer[0] > winter[1]-winter[0]+5


def test_equinoctial_solar_identity_at_6_and_18():
    sr,ss=6.,18.
    for h in np.linspace(0,23.9,100):
        assert equinoctial_solar_phase(float(h),sr,ss)==pytest.approx(
            h,abs=1e-11
        )
    assert np.allclose(solar_phase_to_civil_bin_matrix(sr,ss),np.eye(6),
                       atol=1e-12)


@pytest.mark.parametrize("sr,ss",[
    (5.,20.),(7.,17.),(6.8,16.4),(4.5,20.5),(6.,18.),(5.,18.),
])
def test_probability_transport_is_exact_stochastic_and_never_leaks_mass(sr,ss):
    M=solar_phase_to_civil_bin_matrix(sr,ss)
    assert M.shape==(6,6)
    assert np.all(M>=-1e-13)
    assert np.allclose(M.sum(axis=1),1.,atol=1e-12)
    for k in range(6):
        pred=np.eye(6)[k]@M
        assert pred.sum()==pytest.approx(1.,abs=1e-12)
    phase=np.array([.03,.11,.23,.35,.20,.08])
    assert float((phase@M).sum())==pytest.approx(1.,abs=1e-12)


def test_solar_phase_to_clock_transport_matches_numeric_change_of_variables():
    sr,ss=5.,20.
    M=solar_phase_to_civil_bin_matrix(sr,ss)
    # Independently approximate exactly uniform-within-bin solar phases.
    for k in range(6):
        P=np.zeros(6)
        for frac in (np.arange(10000)+0.5)/10000.:
            phase=4*(k+frac)
            t=_phase_to_unwrapped_civil(float(phase),sr,ss)%24.
            P[int(t//4)]+=1/10000.
        assert np.allclose(P,M[k],atol=.0003)


def test_physical_site_holdout_never_changes_with_season_or_year():
    for site in ("a","b","c","D"):
        assert site_is_sealed(site)==site_is_sealed(site)
    with pytest.raises(ValueError,match="frozen site fold"):
        site_is_sealed("a",heldout_fold=1)
    with pytest.raises(ValueError,match="site_id"):
        site_is_sealed("")


def test_known_truth_solar_tracked_activity_predicts_unseen_sites_future_years():
    train=_events(_sites(14,False),(2018,2019,2020,2021),"sun")
    test=_events(_sites(12,True),(2022,2023),"sun")
    models,admission=fit_species_profiles(train)
    assert sorted(models)==["synthetic fox"]
    assert admission["training_physical_sites"]==14
    assert len(admission["excluded_species"])==0
    scores=[(e,score_new_site_future_year(e,models[e.species])) for e in test]
    summary=summarize_site_level_transfer(scores)
    assert summary["method_version"]==VERSION
    assert summary["all_season_site_floor_met"]
    assert summary["solar_transfer_both_seasons_positive"]
    assert summary["physical_negative_control_both_seasons_positive"]
    assert summary["scientific_status"]=="EXPLORATORY_SOLAR_TRANSPORT_SIGNAL"
    for season in ("winter","summer"):
        assert summary["season_groups"][season]["unique_physical_site_count"]==12
        assert (summary["season_groups"][season]["metrics"]
                ["solar_over_clock"]["mean"]>0)
    assert summary["bootstrap_site_iid_sampling_proven"] is False
    json.dumps(summary,allow_nan=False)


def test_known_truth_fixed_clock_can_defeat_solar_for_future_site_predictions():
    train=_events(_sites(14,False),(2018,2019,2020,2021),"civil")
    test=_events(_sites(12,True),(2022,2023),"civil")
    models,_=fit_species_profiles(train)
    scored=[(e,score_new_site_future_year(e,models[e.species])) for e in test]
    result=summarize_site_level_transfer(scored)
    assert result["scientific_status"]=="EXPLORATORY_NOT_SUPPORTED_OR_UNAVAILABLE"
    assert not result["solar_transfer_both_seasons_positive"]
    for s in ("winter","summer"):
        assert result["season_groups"][s]["metrics"]["solar_over_clock"]["mean"]<0


def test_process_coverage_and_refit_probability_never_claimed():
    train=_events(_sites(14,False),(2018,),"sun")
    models,_=fit_species_profiles(train)
    assert "synthetic fox" in models
    assert all(model.training_event_count>=120 for model in models.values())
    assert all(model.training_site_count>=8 for model in models.values())


def test_training_rejects_future_year_and_sealed_source_site():
    train=_events(_sites(10,False),(2018,),"sun")
    future=_events(_sites(1,True),(2022,),"sun")
    with pytest.raises(ValueError,match="future year or sealed site"):
        fit_species_profiles(train+future)


def test_holdout_rejects_nonsealed_or_old_year_and_mismatched_species():
    train=_events(_sites(14,False),(2018,),"sun")
    models,_=fit_species_profiles(train)
    model=models["synthetic fox"]
    invalid=_events(_sites(1,False),(2022,),"sun")[0]
    with pytest.raises(ValueError,match="not from sealed site"):
        score_new_site_future_year(invalid,model)
    good=_events(_sites(1,True),(2022,),"sun")[0]
    wrong=DielEvent(
        good.site_id,"other species",good.season,good.season_year,
        good.day,good.clock_hour,good.latitude,good.longitude
    )
    with pytest.raises(ValueError,match="species model mismatch"):
        score_new_site_future_year(wrong,model)


def test_biologically_unreasonable_sun_geometry_fails_closed():
    with pytest.raises(ValueError,match="polar"):
        sunrise_sunset_local(date(2022,6,21),90.,0.)
    with pytest.raises(ValueError,match="invalid geographic"):
        sunrise_sunset_local(date(2022,6,21),41.,math.nan)
    with pytest.raises(ValueError,match="invalid sunrise"):
        solar_phase_to_civil_bin_matrix(19.,5.)
    with pytest.raises(ValueError,match="civil_hour"):
        equinoctial_solar_phase(24.,6.,18.)
