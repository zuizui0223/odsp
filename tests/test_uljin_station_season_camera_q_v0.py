"""Same physical camera's rising/falling detector q and new-site majority."""
import json
from pathlib import Path
import numpy as np
import pytest

pytest.importorskip("scipy",reason="independent binomial CP quantiles are optional")
from odsp.uljin_station_season_camera_q_v0 import (
    PATTERNS,METHODS,BUDGETS,PAIRS,
    physical_site_q,exact_joint_cp,calibrate_site_q,
    vectorized_source_ratio_bounds,outer_site_score_bounds,
    run_frozen_station_branch_panel
)
from odsp.uljin_common_clock_mechanistic_comparison_v0 import original_days

ROOT=Path(__file__).resolve().parents[1]
PLAN=json.loads((ROOT/"ULJIN_STATION_SEASON_CAMERA_Q_V0_CONTRACT.json").read_text())
PARENT=json.loads((ROOT/"ULJIN_SITE_SPECIFIC_CAMERA_Q_V0_FIRST_RESULT_LEDGER.json").read_text())
CAL=json.loads((ROOT/"ULJIN_PHOTOPERIOD_MIRROR_2022_V0_DESIGN_CONTRACT.json").read_text())


def test_original_41_mirror_dates_and_32_iid_physical_station_types():
    days,branch=original_days(CAL)
    assert len(days)==82 and np.sum(branch==0)==np.sum(branch==1)==41
    for pi,world in enumerate(PATTERNS):
        types,q=physical_site_q(pi)
        assert q.shape==(32,2,6)
        assert types.shape==(32,)
        assert np.array_equal(types,physical_site_q(pi)[0])
        assert np.all((types==0)|(types==1))
        if pi==0:
            assert np.array_equal(q[:,0,:],q[:,1,:])
        else:
            assert np.max(abs(q[:,0,:]-q[:,1,:]))>.45


def test_proper_iid_50_50_source_branch_mean_but_not_branch_specific_q():
    _,q=physical_site_q(1)
    means=q[16:].mean(axis=1)
    assert means.shape==(16,6)
    assert np.max(abs(means[:,None,:]-q[16:]))>.2
    # Perfect source-population branch-mean q still does not cover
    # actual source TARGET q_{physical_site,photoperiod_branch}.
    assert np.allclose(means,(q[16:,0,:]+q[16:,1,:])/2)
    for budget_i,(T,n0,n1) in enumerate(BUDGETS):
        assert 16*6*n0==16*2*6*n1==T
        pooled=calibrate_site_q(1,budget_i,0,q)
        separate=calibrate_site_q(1,budget_i,1,q)
        assert pooled["q_source_groups"]==96
        assert separate["q_source_groups"]==192
        assert pooled["source_binomial_iid_correct"]
        assert separate["source_binomial_iid_correct"]
        assert not pooled["actual_ref_target_q_branch_specific"]
        assert separate["actual_ref_target_q_branch_specific"]
        assert pooled["total_true_passage_reference_opportunities"]==T
        assert separate["total_true_passage_reference_opportunities"]==T


def test_correct_source_q_temporal_scope_and_zero_lower_HOLD():
    _,q=physical_site_q(0)
    pooled=calibrate_site_q(0,0,0,q)
    separate=calibrate_site_q(0,0,1,q)
    assert pooled["actual_ref_target_q_branch_specific"]
    assert separate["actual_ref_target_q_branch_specific"]
    assert pooled["lower"].shape==(16,2,6)
    assert separate["upper"].shape==(16,2,6)
    assert np.allclose(pooled["lower"][:,0,:],pooled["lower"][:,1,:])
    sample=np.zeros((16,2,6),dtype=int)
    lo,hi=exact_joint_cp(sample,200)
    assert np.all(lo==0) and np.all(hi>0)
    with pytest.raises(ValueError):
        exact_joint_cp(np.full((16,2,6),201),200)


def test_one_site_score_bounds_must_not_use_oracle_q_coverage_for_decisions():
    dates,branch=original_days(CAL)
    aa=np.full((82,96),1/96.)
    bb=aa.copy()
    aa[:,7]*=5
    aa/=aa.sum(axis=1,keepdims=True)
    data=np.zeros((16,82,96),dtype=int)
    data[:,:,7]=20
    true_q=np.full((16,2,6),.65)
    base={
        "lower":np.full((16,2,6),.65),
        "upper":np.full((16,2,6),.65),
        "actual_ref_target_q_branch_specific":True,
        "HOLD_zero_q_interval_lower":False,
        "source_CP_joint_coverage_ORACLE_ONLY":True,
        "station_by_branch_target_CP_joint_coverage_ORACLE_ONLY":True
    }
    good=outer_site_score_bounds(data,aa,bb,true_q,branch,base)
    assert good["scope"]=="SOURCE_STATION_X_BRANCH_Q_TARGET_VALID"
    assert good["majority_new_site_certified"]
    assert good["independent_site_positive_robust_count"]==16
    changed={**base,
        "source_CP_joint_coverage_ORACLE_ONLY":False,
        "station_by_branch_target_CP_joint_coverage_ORACLE_ONLY":False}
    not_peeking=outer_site_score_bounds(data,aa,bb,true_q,branch,changed)
    assert not_peeking["majority_new_site_certified"]==good["majority_new_site_certified"]
    assert not_peeking["exact_site_majority_p"]==good["exact_site_majority_p"]
    pooled={**base,"actual_ref_target_q_branch_specific":False}
    hold=outer_site_score_bounds(data,aa,bb,true_q,branch,pooled)
    assert hold["scope"]=="HOLD_SITE_ONLY_Q_NOT_PORTABLE_TO_BRANCH"
    assert hold["majority_new_site_certified"] is None


def test_per_date_fractional_extrema_contains_uniform_q_and_is_outer():
    _,branch=original_days(CAL)
    a=np.tile(np.array([.24,.16,.18,.14,.13,.15]),(82,1))
    b=np.tile(np.array([.18,.23,.12,.20,.11,.16]),(82,1))
    a/=a.sum(axis=1,keepdims=True)
    b/=b.sum(axis=1,keepdims=True)
    lower=np.full((16,2,6),.45)[:,branch,:]
    upper=np.full((16,2,6),.9)[:,branch,:]
    lo,hi=vectorized_source_ratio_bounds(a,b,lower,upper)
    true=np.full((16,82,6),.65)
    ratios=np.sum(a[None,:,:]*true,axis=2)/np.sum(b[None,:,:]*true,axis=2)
    assert lo.shape==hi.shape==(16,82)
    assert np.all(lo<=ratios+1e-12) and np.all(hi>=ratios-1e-12)


def test_frozen_complete_96_pairs_have_both_equal_cost_calibration_arms():
    out=run_frozen_station_branch_panel(PLAN,PARENT,CAL)
    assert out["status"]=="SOURCE_FREE_STATION_X_PHOTOPERIOD_BRANCH_CAMERA_Q_ONLY"
    assert out["total_original_paired_cases"]==96
    assert len(out["frozen_external_reference_calibration_receipts"])==8
    assert out["original_daylength_mirror_pairs"]==41
    assert out["same_original_civil_15min_response_bins"]==96
    assert out["branch_heterogeneity_pooled_q_HOLD_case_count"]==48
    assert out["per_preselected_design_total_error_bound_under_assumptions"]==.05
    for case in out["frozen_paired_comparisons"]:
        assert [case["ordered_model_A"],case["ordered_model_B"]] in [
            list(x) for x in PAIRS]
        arms=case["two_equal_cost_calibration_arms"]
        assert set(arms)==set(METHODS)
        for sub in arms.values():
            assert sub["oracle_coverage_not_in_decision"]
            if sub["scope"]=="SOURCE_STATION_X_BRANCH_Q_TARGET_VALID":
                assert sub["independent_site_positive_robust_count"] in range(17)
                if sub["majority_new_site_certified"]:
                    assert sub["independent_site_positive_robust_count"]>=14
            else:
                assert sub["majority_new_site_certified"] is None
    assert out["real_EcoBank_species_events_original_camera_operation_or_q_refs_NOT_read"]
    json.dumps(out,allow_nan=False)


def test_frozen_contract_and_parent_ci_no_unregistered_route_changes():
    modified=json.loads(json.dumps(PLAN))
    modified["site_and_detector_truth"]["two_q_worlds"][1][
        "q_type_A_falling"][0]=.6
    with pytest.raises(ValueError,match="frozen"):
        run_frozen_station_branch_panel(modified,PARENT,CAL)
    parent=json.loads(json.dumps(PARENT))
    parent["first_complete_ci_run"]=0
    with pytest.raises(ValueError,match="frozen"):
        run_frozen_station_branch_panel(PLAN,parent,CAL)
