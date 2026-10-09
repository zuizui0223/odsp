"""Synthetic camera distance transport, exact 12-cell q/w coverage and HOLD."""
import json
import math
from pathlib import Path
import numpy as np
import pytest

pytest.importorskip("scipy", reason="optional reference-mixture calibration dependency")

from odsp.uljin_q_transport_distance_mix_v0 import (
    NEAR,FAR,WREF,WORLDS,NS,REPS,
    q_effective,detector_crossproduct,cp_one_cell,cp_band,
    mixed_detector_q_bounds,detector_gamma_upper,
    trial,run_frozen_transport_panel,
)

ROOT=Path(__file__).resolve().parents[1]
PLAN=json.loads((ROOT/"ULJIN_Q_TRANSPORT_DISTANCE_MIX_V0_CONTRACT.json").read_text())


def test_exact_population_Simpson_detector_confound_without_any_q_stratum_change():
    ref=q_effective(NEAR,FAR,WREF)
    assert np.allclose(ref,[.6]*4)
    assert detector_crossproduct(ref)==pytest.approx(1.)
    near=q_effective(NEAR,FAR,WORLDS[1][2])
    assert near==pytest.approx([.42,.78,.78,.42])
    assert detector_crossproduct(near)==pytest.approx((.78/.42)**2)
    assert detector_crossproduct(q_effective(NEAR,FAR,WORLDS[2][2]))==pytest.approx(
        (.42/.78)**2)
    # The camera is the SAME model with q-near=.9, q-far=.3
    # in ALL time/season cells; only the animal distance mix changes.
    assert len(set(NEAR))==len(set(FAR))==1


def test_exact_binomial_endpoint_and_joint_alpha_allocation():
    for n in (50,200,1000):
        alpha=.0125/16
        assert cp_one_cell(0,n,alpha)[0]==0
        assert cp_one_cell(n,n,alpha)[1]==1
        qlo,qhi=cp_band((int(round(.9*n)),)*8,n,.0125)
        wlo,whi=cp_band((int(round(.2*n)),)*4,n,.0125)
        assert qlo.shape==qhi.shape==(8,)
        assert wlo.shape==whi.shape==(4,)
        assert np.all(qlo<=.9) and np.all(.9<=qhi)
        assert np.all(wlo<=.2) and np.all(.2<=whi)
    assert .0125+.0125+.025==.05


def test_transport_bounds_optimize_true_corner_min_max_and_HOLD():
    # Near > far: minimum at low target-near mix, max at high.
    a=np.full(4,.85)
    b=np.full(4,.95)
    c=np.full(4,.25)
    d=np.full(4,.35)
    wl=np.full(4,.2)
    wh=np.full(4,.8)
    lo,hi=mixed_detector_q_bounds(a,b,c,d,wl,wh)
    assert lo==pytest.approx(np.full(4,.2*.85+.8*.25))
    assert hi==pytest.approx(np.full(4,.8*.95+.2*.35))
    assert detector_gamma_upper(lo,hi)>1
    lo[0]=0
    assert math.isinf(detector_gamma_upper(lo,hi))
    with pytest.raises(ValueError):
        mixed_detector_q_bounds(a,b,c,d,wh,wl)


def test_frozen_actual_draw_reproducible_no_source_or_posthoc_schedule_change():
    x=trial(1,1,1)
    y=trial(1,1,1)
    assert x==y
    assert x["true_target_detector_gamma"]==pytest.approx((.78/.42)**2)
    assert x["reference_mixture_detector_gamma"]==pytest.approx(1.)
    assert len(x["detected_event_counts"])==4
    short=run_frozen_transport_panel(PLAN,_test_replicates=3)
    again=run_frozen_transport_panel(PLAN,_test_replicates=3)
    assert short==again
    assert short["status"]=="SOURCE_FREE_DISTANCE_MIX_PREFLIGHT"
    assert short["world_count"]==12 and short["replicates_per_world"]==3
    assert short["corrected_joint_error_bound_if_reference_valid"]==.05
    assert short["independent_true_passage_labels_assumed_not_verified"]
    assert short["original_Uljin_animal_or_source_camera_data_read"] is False
    json.dumps(short,allow_nan=False)


def test_freeze_and_malformed_input_are_fail_closed():
    mutated=json.loads(json.dumps(PLAN))
    mutated["q_truth"]["far"]=[.4]*4
    with pytest.raises(ValueError,match="contract"):
        run_frozen_transport_panel(mutated,_test_replicates=1)
    mutated=json.loads(json.dumps(PLAN))
    mutated["synthetic_monte_carlo"]["seed"]=0
    with pytest.raises(ValueError,match="contract"):
        run_frozen_transport_panel(mutated,_test_replicates=1)
    with pytest.raises(ValueError):
        run_frozen_transport_panel(PLAN,_test_replicates=0)
    with pytest.raises(ValueError):
        cp_one_cell(5,4,.001)
