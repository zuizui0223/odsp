"""No-source fixed civil-target astronomical model comparison invariants."""
from datetime import date
import json
from pathlib import Path
import numpy as np
import pytest

from odsp.uljin_common_clock_mechanistic_comparison_v0 import (
    KINDS,PEAKS,BINS,TRUTHS,TRAIN_SITES,TOTAL_SITES,
    original_days,geometry,average_anchors,coordinate_jacobian,
    civil_bin_probabilities,precompute_profiles,_fit_and_score,
    run_frozen_common_clock_panel,
)

ROOT=Path(__file__).resolve().parents[1]
CAL=json.loads((ROOT/"ULJIN_PHOTOPERIOD_MIRROR_2022_V0_DESIGN_CONTRACT.json").read_text())
PLAN=json.loads((ROOT/"ULJIN_COMMON_CLOCK_MECHANISTIC_COMPARISON_V0_CONTRACT.json").read_text())


def test_all_models_predict_the_identical_civil_15min_response_support():
    days,branch=original_days(CAL)
    assert len(days)==82 and int(np.sum(branch==1))==41
    assert BINS==96 and len(PEAKS)==48
    tables=precompute_profiles(days)
    assert set(tables)==set(KINDS)
    for name,table in tables.items():
        assert table.shape==(82,96,48)
        assert np.all(table>0)
        assert np.all(np.isfinite(table))
        assert np.max(np.abs(table.sum(axis=1)-1))<1e-10
    # The extra-parameter model has EXACTLY the same phase mapping;
    # its distinction is learned rising/falling parameters, not bin edges.
    assert np.array_equal(tables["solar_phase_plus_branch"],tables["solar_phase"])


def test_solar_noon_and_sunrise_sunset_map_with_exact_derivatives():
    day=date(2022,5,1)
    days,_=original_days(CAL)
    avg=average_anchors(days)
    sr,ss,noon=geometry(day)
    t=np.array([sr,ss,0.0,23.9999,noon])
    phi,jac=coordinate_jacobian(t,day,"solar_phase",avg)
    assert phi[0]==pytest.approx(6.,abs=1e-10)
    assert phi[1]==pytest.approx(18.,abs=1e-10)
    assert phi[4]==pytest.approx(12.,abs=1e-10)
    assert np.all(jac>0)
    avgcoord,avgjac=coordinate_jacobian(t,day,"average_anchor",avg)
    assert avgcoord[0]==pytest.approx(avg[0],abs=1e-10)
    assert avgcoord[1]==pytest.approx(avg[1],abs=1e-10)
    nooncoord,noonjac=coordinate_jacobian(
        np.array([noon]),day,"solar_noon",avg)
    assert nooncoord[0]==pytest.approx(12.,abs=1e-10)
    assert noonjac[0]==pytest.approx(1)
    clock,cj=coordinate_jacobian(t,day,"civil_clock",avg)
    assert np.allclose(clock,t)
    assert np.all(cj==1)


def test_jacobian_full_day_and_partial_operation_geometry():
    day=date(2022,8,13)
    avg=average_anchors(original_days(CAL)[0])
    # Probability in bin of unknown camera operation must not be fabricated.
    for kind in KINDS:
        full=civil_bin_probabilities(day,kind,avg,[(0.,24.)])
        part=civil_bin_probabilities(day,kind,avg,[(0.,8.)])
        assert np.allclose(full.sum(axis=0),1,atol=1e-10)
        assert np.allclose(part.sum(axis=0),1,atol=1e-10)
        assert np.all(part[33:]==0)
        assert np.all(part[:32]>0)
        union=civil_bin_probabilities(day,kind,avg,[(0.,5.),(4.,8.)])
        assert np.allclose(union,part,atol=1e-12)
    with pytest.raises(ValueError,match="HOLD_NO_POSITIVE_EXPOSURE"):
        civil_bin_probabilities(day,"solar_phase",avg,[])
    with pytest.raises(ValueError):
        civil_bin_probabilities(day,"solar_phase",avg,[(8.,3.)])
    with pytest.raises(ValueError):
        civil_bin_probabilities(day,"solar_phase",avg,[(0.,25.)])


def test_heldout_site_split_score_and_same_observation_frame():
    days,branch=original_days(CAL)
    x=precompute_profiles(days)
    counts=np.zeros((TOTAL_SITES,len(days),BINS),dtype=int)
    for s in range(TOTAL_SITES):
        for d in range(len(days)):
            counts[s,d,(7*4+s%3+d%4)%BINS]=10
    scored=_fit_and_score(x,counts,branch)
    assert set(scored)==set(KINDS)|{"uniform_device_time"}
    assert len(scored["solar_phase_plus_branch"]["training_only_peak_parameters"])==2
    assert all(np.isfinite(z["heldout_equal_site_logscore_nats_per_event"])
               for z in scored.values())
    with pytest.raises(ValueError):
        _fit_and_score(x,counts[:TRAIN_SITES],branch)


def test_frozen_five_biological_truth_worlds_and_two_sample_sizes():
    result=run_frozen_common_clock_panel(CAL,PLAN)
    assert result["status"]=="SOURCE_FREE_COMMON_CLOCK_MECHANISTIC_COMPARISON_ONLY"
    assert result["original_calendar_pairs"]==41
    assert result["common_civil_clock_bin_count"]==96
    assert len(result["scenarios"])==5*2*3
    assert {r["truth"] for r in result["scenarios"]}=={r[0] for r in TRUTHS}
    assert result["all_scenarios_kept"]
    for row in result["scenarios"]:
        assert row["trained_on_sites"]==TRAIN_SITES
        assert row["untouched_heldout_sites"]==TOTAL_SITES-TRAIN_SITES
        assert row["all_date_pair_events_binned_in_same_civil_cells"]
        scores=row["all_common_clock_heldout_scores"]
        assert scores["civil_clock"]["improvement_over_civil_clock_nats_per_event"]==0
        assert scores["solar_phase"]["improvement_over_solar_phase_nats_per_event"]==0
    assert not result["causal_zeitgeber_or_hysteresis_identified"]
    assert not result["original_animal_events_or_camera_log_opened"]
    json.dumps(result,allow_nan=False)


def test_source_free_contract_mutations_fail_closed():
    changed=json.loads(json.dumps(PLAN))
    changed["training_testing"]["training_sites"]=20
    with pytest.raises(ValueError,match="contract"):
        run_frozen_common_clock_panel(CAL,changed)
    original=json.loads(json.dumps(CAL))
    original["preoutcome_structural_pairing"][
        "pair_absolute_daylength_difference_max_hours"]=.9
    with pytest.raises(ValueError):
        run_frozen_common_clock_panel(original,PLAN)
