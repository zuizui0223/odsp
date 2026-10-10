"""Sharp common detector-q envelope on IDENTICAL civil response bins."""
from __future__ import annotations
from itertools import product
import json
from pathlib import Path
import numpy as np
import pytest

from odsp.uljin_common_96bin_detector_envelope_v0 import (
    BINS,DELTAS,BOXES,PAIRS,TRUTH_IDS,ratio_extrema,
    normalize_q_groups,site_equal_pair_bound,
    frozen_full_96bin_panel
)

ROOT=Path(__file__).resolve().parents[1]
PLAN=json.loads((ROOT/"ULJIN_COMMON_96BIN_DETECTOR_ENVELOPE_V0_CONTRACT.json").read_text())
PARENT=json.loads((ROOT/"ULJIN_Q_W_VARIANCE_BUDGET_V0_FIRST_RESULT_LEDGER.json").read_text())
CAL=json.loads((ROOT/"ULJIN_PHOTOPERIOD_MIRROR_2022_V0_DESIGN_CONTRACT.json").read_text())


def test_sharp_fractional_linear_bounds_against_ALL_16_vertex_values():
    a=np.array([.15,.35,.25,.25])
    b=np.array([.3,.1,.4,.2])
    lo=np.array([.35,.6,.5,.45])
    hi=np.array([.8,.9,.65,.95])
    all_ratios=[]
    for bits in product((0,1),repeat=4):
        q=np.where(bits,hi,lo)
        all_ratios.append(float(np.dot(a,q)/np.dot(b,q)))
    left,right=ratio_extrema(a,b,lo,hi)
    assert left==pytest.approx(min(all_ratios),abs=1e-11)
    assert right==pytest.approx(max(all_ratios),abs=1e-11)
    assert left<right
    assert ratio_extrema(a,a,lo,hi)==pytest.approx((1.,1.))
    with pytest.raises(ValueError):
        ratio_extrema(a,b,lo,np.ones(3))
    with pytest.raises(ValueError):
        ratio_extrema(a,b,np.zeros(4),hi)


def test_six_civil_four_hour_groups_preserve_the_common_96bin_axis():
    a=np.arange(1,97,dtype=float)
    a/=a.sum()
    b=np.arange(96,0,-1,dtype=float)
    b/=b.sum()
    a6,b6=normalize_q_groups(a,b,"fixed_civil_6blocks")
    assert len(a6)==len(b6)==6
    assert a6[0]==pytest.approx(sum(a[:16]))
    assert a6[-1]==pytest.approx(sum(a[-16:]))
    a96,b96=normalize_q_groups(a,b,"independent_civil_96bins")
    assert np.array_equal(a96,a) and np.array_equal(b96,b)
    with pytest.raises(ValueError):
        normalize_q_groups(a,b,"solar_phase_bins_cannot_replace_civil")


def test_shared_q_event_term_cancels_and_baseline_is_always_inside():
    rng=np.random.default_rng(78)
    a=rng.uniform(.01,1,size=(2,96))
    b=rng.uniform(.01,1,size=(2,96))
    a/=a.sum(axis=1,keepdims=True)
    b/=b.sum(axis=1,keepdims=True)
    y=np.zeros((16,2,96),dtype=int)
    y[:,:,28]=20
    y[:,:,66]=15
    nominal=float(np.sum((y/y.sum(axis=(1,2))[:,None,None]/16).sum(axis=0)*
                         np.log(a/b)))
    d0=site_equal_pair_bound(y,a,b,0.,"independent_civil_96bins")
    assert d0["exact_shared_q_lower_logscore_gap_nats_per_event"]==pytest.approx(
        nominal,abs=1e-10)
    assert d0["exact_shared_q_upper_logscore_gap_nats_per_event"]==pytest.approx(
        nominal,abs=1e-10)
    wide=site_equal_pair_bound(y,a,b,.2,"independent_civil_96bins")
    narrow=site_equal_pair_bound(y,a,b,.2,"fixed_civil_6blocks")
    assert wide["exact_shared_q_lower_logscore_gap_nats_per_event"]<=(
        narrow["exact_shared_q_lower_logscore_gap_nats_per_event"]+1e-10)
    assert wide["exact_shared_q_upper_logscore_gap_nats_per_event"]>=(
        narrow["exact_shared_q_upper_logscore_gap_nats_per_event"]-1e-10)
    assert (wide["exact_shared_q_lower_logscore_gap_nats_per_event"]<=
            nominal<=wide["exact_shared_q_upper_logscore_gap_nats_per_event"])


def test_reject_missing_96clock_bins_or_zero_response_site():
    a=np.full((2,96),1/96)
    data=np.zeros((16,2,96),dtype=int)
    with pytest.raises(ValueError):
        site_equal_pair_bound(data,a,a,0.,"independent_civil_96bins")
    data[:,:,8]=10
    with pytest.raises(ValueError):
        site_equal_pair_bound(data[:,:,:95],a,a,0.,"independent_civil_96bins")
    with pytest.raises(ValueError):
        site_equal_pair_bound(data,a,a,.3,"independent_civil_96bins")


def test_full_240_frozen_sharp_q_envelopes_and_training_result_replay():
    out=frozen_full_96bin_panel(PLAN,PARENT,CAL)
    assert out["status"]=="SOURCE_FREE_SHARP_COMMON_96_CLOCK_BIN_Q_SCORE_ENVELOPES"
    assert out["matched_astronomical_calendar_pairs"]==41
    assert out["original_clock_bins"]==96
    assert out["physical_heldout_sites"]==16
    assert out["scored_pairwise_model_cases"]==3*2*4
    assert out["total_frozen_reported_q_envelopes"]==240
    assert out["q_bounds_depend_on_unmeasured_external_target_distance_mix"]
    assert out["sharp_linear_fractional_bounds_not_statistical_CI"]
    assert out["training_models_frozen_not_refit_for_uncertain_q"]
    assert out["same_q_for_competing_models_and_same_clock_outcomes"]
    assert not out["no_original_species_events_operation_logs_or_calibration_q_used"] is False
    for pair in out["every_fixed_model_pair_case"]:
        assert pair["true_model"] in TRUTH_IDS
        assert [pair["comparator_A"],pair["comparator_B"]] in [list(x) for x in PAIRS]
        assert len(pair["all_10_q_envelopes"])==len(DELTAS)*len(BOXES)
        for record in pair["all_10_q_envelopes"]:
            original=pair["nominal_original_clock_scoring_A_minus_B"]
            assert record["exact_shared_q_lower_logscore_gap_nats_per_event"]<=original+1e-10
            assert record["exact_shared_q_upper_logscore_gap_nats_per_event"]>=original-1e-10
    json.dumps(out,allow_nan=False)


def test_original_contract_and_parent_immutable_and_not_a_confidence_interval():
    modified=json.loads(json.dumps(PLAN))
    modified["physical_detector_model"]["delta_grid"][2]=.04
    with pytest.raises(ValueError,match="frozen"):
        frozen_full_96bin_panel(modified,PARENT,CAL)
    changed=json.loads(json.dumps(PARENT))
    changed["first_ci_run"]=0
    with pytest.raises(ValueError,match="frozen"):
        frozen_full_96bin_panel(PLAN,changed,CAL)
