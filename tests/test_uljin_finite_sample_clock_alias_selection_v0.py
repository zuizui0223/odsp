"""No real wildlife or operation source: frozen finite-sample diagnostic tests."""
import json
from pathlib import Path

import numpy as np
import pytest

from odsp.uljin_finite_sample_clock_alias_selection_v0 import (
    PROFILES,SCALES,PAIRS,SITES,TRAIN_IDX,TEST_IDX,
    phase_intensity,inverse_cdf_table,phase_to_civil_numpy,
    event_count_frames,geometry_for_pairs,_fit_sufficient,
    heldout_site_equal_gain,run_frozen_finite_sample_panel,
)
from odsp.uljin_conditional_branch_shape_v0 import (
    MirrorCountCell,fit_conditional_branch_model,score_heldout_station_frame,
)
from odsp.uljin_photoperiod_mirror_design_v0 import (
    generate_preoutcome_2022_mirror_calendar,
)

ROOT=Path(__file__).resolve().parents[1]
PLAN=json.loads((ROOT/"ULJIN_FINITE_SAMPLE_CLOCK_ALIAS_SELECTION_V0_CONTRACT.json").read_text())
CAL=json.loads((ROOT/"ULJIN_PHOTOPERIOD_MIRROR_2022_V0_DESIGN_CONTRACT.json").read_text())


def _geometry():
    dates=generate_preoutcome_2022_mirror_calendar(CAL)["matched_dates"]
    assert len(dates)==41
    return geometry_for_pairs(dates)


def test_full_pair_and_physical_site_frame_kept_and_same_latent_events():
    rng=np.random.default_rng(722)
    cdf,grid=inverse_cdf_table(PROFILES[1])
    civil,solar,n=event_count_frames(rng,4623,_geometry(),cdf,grid)
    assert civil.shape==solar.shape==(SITES,2,6)
    assert civil.sum()==solar.sum()==n
    assert np.array_equal(civil.sum(axis=2),solar.sum(axis=2))
    assert len(TRAIN_IDX)==40 and len(TEST_IDX)==42
    assert not (set(TRAIN_IDX)&set(TEST_IDX))
    assert set(TRAIN_IDX)|set(TEST_IDX)==set(range(SITES))


def test_exact_mapping_phase_inverse_and_night_modulo():
    from odsp.uljin_solar_phase_device_exposure_v0 import clock_to_phase
    from datetime import date
    day=date(2022,8,13)
    geo=_geometry()
    sr,ss=geo[0,0]
    for phi in np.linspace(0,24,240,endpoint=False):
        # A full-year calendar geometry is used, but inversion is local to pair 0.
        clock=phase_to_civil_numpy(np.array([phi]),
            np.array([sr]),np.array([ss]))[0]
        from odsp.uljin_solar_phase_device_exposure_v0 import phase_to_clock
        assert clock==pytest.approx(phase_to_clock(float(phi),
            date.fromisoformat(
              generate_preoutcome_2022_mirror_calendar(CAL)["matched_dates"][0]["ascending_date"]
            )),abs=1e-9)


def test_frozen_previously_qualified_fitter_equal_to_collapsed_statistics():
    # All original comparisons have equal 4h branch exposure here, so six
    # sums over station×pair cells are sufficient for the identical fitter.
    train=[]
    for s in ("UJ1_TRAIN_A","UJ2_TRAIN_B"):
        reg=s[:3]
        for pair in ("p1","p2"):
            for k in range(6):
                train.append(MirrorCountCell(
                    station=s,region=reg,taxon="synthetic",pair_id=pair,
                    clock_bin=k,rising_count=6+k+(s=="UJ2_TRAIN_B"),
                    falling_count=9+2*k+(pair=="p2"),
                    rising_active_hours=4.,falling_active_hours=4.))
    aggregate=np.zeros((2,6),dtype=int)
    for r in train:
        aggregate[0,r.clock_bin]+=r.rising_count
        aggregate[1,r.clock_bin]+=r.falling_count
    for allow_shape in (False,True):
        expected=fit_conditional_branch_model(
            train,allow_branch_shape=allow_shape).six_branch_log_rate_ratios
        collapsed=_fit_sufficient(aggregate,allow_shape)
        assert collapsed==pytest.approx(expected,abs=1e-9)

    heldout=[MirrorCountCell(
        station="UJ1_TEST_C",region="UJ1",taxon="synthetic",pair_id="p1",
        clock_bin=k,rising_count=4+k,falling_count=8+k,
        rising_active_hours=4.,falling_active_hours=4.)
        for k in range(6)]
    direct=score_heldout_station_frame(train,heldout)[
        "test_site_equal_mean_conditional_gain"]
    beta0=np.array(_fit_sufficient(aggregate,False))
    beta1=np.array(_fit_sufficient(aggregate,True))
    a=np.array([r.rising_count for r in heldout])
    d=np.array([r.falling_count for r in heldout])
    derived=np.sum(d*(beta1-beta0)-(a+d)*(
        np.logaddexp(0,beta1)-np.logaddexp(0,beta0)))/len(heldout)
    assert direct==pytest.approx(derived,abs=1e-9)


def test_full_site_equal_denominator_and_no_event_selected_roster():
    rng=np.random.default_rng(72)
    cdf,grid=inverse_cdf_table(PROFILES[2])
    civil,solar,n=event_count_frames(rng,4623,_geometry(),cdf,grid)
    gain_c=heldout_site_equal_gain(civil)
    gain_s=heldout_site_equal_gain(solar)
    assert np.isfinite(gain_c) and np.isfinite(gain_s)
    assert np.array_equal(civil[TEST_IDX].sum(axis=2),
                          solar[TEST_IDX].sum(axis=2))
    with pytest.raises(ValueError):
        heldout_site_equal_gain(civil[TEST_IDX])


def test_small_preflight_shape_and_seed_repeatability_no_full_panel():
    out=run_frozen_finite_sample_panel(CAL,PLAN,_test_world_count=2)
    second=run_frozen_finite_sample_panel(CAL,PLAN,_test_world_count=2)
    assert out==second
    assert out["case_count"]==9
    assert out["worlds_per_case_executed"]==2
    assert len(out["cases"])==len(PROFILES)*len(SCALES)
    assert all(0<=x["clock_only_selection_frequency"]<=1 for x in out["cases"])
    assert not out["real_animal_events_accessed"]


def test_tampered_precommitted_scenarios_fail_closed():
    altered=json.loads(json.dumps(PLAN))
    altered["profiles"][2]["peak"]=20
    with pytest.raises(ValueError,match="contract"):
        run_frozen_finite_sample_panel(CAL,altered,_test_world_count=1)
