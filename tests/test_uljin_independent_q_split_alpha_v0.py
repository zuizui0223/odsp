"""Source-free joint calibration coverage and exact site-bin null guards."""
import json
import math
from pathlib import Path
import numpy as np
import pytest

from odsp.uljin_independent_q_split_alpha_v0 import (
    ALPHA_CAL,ALPHA_TEST,ALPHA_ALL,N_REF,REPS,TRUTHS,
    independent_hoeffding_bounds,true_detector_crossproduct,
    _noncentral_exact_pmf,_tail_from_margins,
    _draw_site_four_count_table,_draw_one,
    frozen_joint_calibration_panel,
)

ROOT=Path(__file__).resolve().parents[1]
PLAN=json.loads((ROOT/"ULJIN_INDEPENDENT_Q_SPLIT_ALPHA_V0_CONTRACT.json").read_text())


def test_simultaneous_four_detector_bands_have_finite_sample_union_guarantee():
    for n in N_REF:
        e=math.sqrt(math.log(8/ALPHA_CAL)/(2*n))
        assert 8*math.exp(-2*n*e*e)==pytest.approx(ALPHA_CAL,rel=1e-12)
        b=independent_hoeffding_bounds(tuple(round(.85*n) for _ in range(4)),n)
        assert all(0<=lo<=hi<=1 for lo,hi in zip(b.lower,b.upper))
        assert b.covers((.85,.85,.85,.85))
    assert ALPHA_CAL+ALPHA_TEST==ALPHA_ALL==.05
    assert ALPHA_TEST<.05


def test_zero_detector_lower_bound_holds_not_fake_inferred_animal_shift():
    b=independent_hoeffding_bounds((0,40,45,0),50)
    assert math.isinf(b.detector_gamma_upper)
    # Do NOT divide through a zero efficiency lower bound.
    with pytest.raises(ValueError):
        independent_hoeffding_bounds((51,20,30,10),50)
    with pytest.raises(ValueError):
        independent_hoeffding_bounds((0,0,0,0),50,alpha_cal=.05)


def test_detector_only_and_effort_only_truths_are_distinct():
    names={w[0]:w for w in TRUTHS}
    q=names["null_detector_only"][1]
    assert true_detector_crossproduct(q)==pytest.approx(2)
    e=names["null_effort_only"][2]
    assert e[2]*e[1]/(e[0]*e[3])==pytest.approx(2)
    assert true_detector_crossproduct(names["null_effort_only"][1])==pytest.approx(1)
    assert names["alternative_strong_encounter"][-1]==2
    assert all(w[-1]==1 for w in TRUTHS[:3])


def test_conditional_animal_counts_preserve_original_site_margins():
    for i,(_,q,e,source,latent) in enumerate(TRUTHS):
        effort=e[2]*e[1]/(e[0]*e[3])
        offset,p=_noncentral_exact_pmf(source,effort*true_detector_crossproduct(q)*latent)
        assert 0<=offset<=source[2]
        assert abs(p.sum()-1)<1e-12
        generated=_draw_site_four_count_table(
            np.random.default_rng(100+i),source,
            effort*true_detector_crossproduct(q)*latent)
        a,b,c,d=source
        aa,bb,cc,dd=generated
        assert sum(generated)==sum(source)
        assert aa+cc==a+c and cc+dd==c+d
        p1=_tail_from_margins(source,cc,1.)
        p2=_tail_from_margins(source,cc,2.)
        assert 0<=p1<=p2<=1


def test_independent_reference_sampling_and_robust_alpha_accounting_preflight():
    result=frozen_joint_calibration_panel(PLAN,_test_replicates=3)
    assert result["status"]=="SOURCE_FREE_Q_CALIBRATION_PREFLIGHT_ONLY"
    assert result["case_count"]==len(TRUTHS)*len(N_REF)==16
    assert result["worlds_per_case"]==3
    assert result["guaranteed_total_false_certification_upper_bound"]==.05
    assert result["guarantee_conditional_on_independence_and_model"]
    assert result["empirical_monte_carlo_fraction_not_formal_size_proof"]
    assert not result["original_animal_events_or_reference_sensor_calibration_not_opened"] is False
    for entry in result["all_precommitted_cases"]:
        assert entry["replicates"]==3
        assert entry["unconditional_false_certification_alpha_bound"]==.05
        assert 0<=entry["fraction_robustly_rejecting_latent_OR_le_1"]<=1
        assert 0<=entry["empirical_joint_q_band_coverage"]<=1
    assert result==frozen_joint_calibration_panel(PLAN,_test_replicates=3)
    json.dumps(result,allow_nan=False)


def test_precommitted_source_and_alpha_cannot_change_after_first_outcome():
    changed=json.loads(json.dumps(PLAN))
    changed["combined_inference"]["animal_count_exact_conditional_test_budget"]=.05
    with pytest.raises(ValueError,match="contract"):
        frozen_joint_calibration_panel(changed,_test_replicates=1)
    changed=json.loads(json.dumps(PLAN))
    changed["synthetic_truth_worlds"][2]["reference_q"]=[1,1,1,1]
    with pytest.raises(ValueError,match="contract"):
        frozen_joint_calibration_panel(changed,_test_replicates=1)
    with pytest.raises(ValueError):
        frozen_joint_calibration_panel(PLAN,_test_replicates=0)
