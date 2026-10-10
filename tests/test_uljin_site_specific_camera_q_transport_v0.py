"""Proper pooled source q calibration can fail station-specific q transport."""
import json
from itertools import product
from pathlib import Path

import numpy as np
import pytest

pytest.importorskip("scipy", reason="optional exact source q calibration for site heterogeneity")
from odsp.uljin_site_specific_camera_q_transport_v0 import (
    PATTERNS,TRUTH_IDS,BUDGETS,METHODS,PAIRS,SITE_N,
    make_32_physical_site_types,source_q_and_station_q,
    exact_joint_cp,frozen_reference_calibration,
    vectorized_date_fractional_extrema,station_site_majority,
    run_first_site_q_transport_panel
)
from odsp.uljin_common_clock_mechanistic_comparison_v0 import original_days

ROOT=Path(__file__).resolve().parents[1]
PLAN=json.loads((ROOT/"ULJIN_SITE_SPECIFIC_CAMERA_Q_V0_CONTRACT.json").read_text())
PARENT=json.loads((ROOT/"ULJIN_JOINT_Q_SITE_MAJORITY_V0_FIRST_RESULT_LEDGER.json").read_text())
CAL=json.loads((ROOT/"ULJIN_PHOTOPERIOD_MIRROR_2022_V0_DESIGN_CONTRACT.json").read_text())


def test_independent_physical_station_types_and_equal_gold_reference_cost():
    assert SITE_N==16
    dates,branch=original_days(CAL)
    assert len(dates)==82
    for pi in (0,1):
        labels=make_32_physical_site_types(pi)
        assert labels.shape==(32,)
        assert np.all((labels==0)|(labels==1))
        assert np.array_equal(labels,make_32_physical_site_types(pi))
        q,mean_q=source_q_and_station_q(pi,labels)
        assert q.shape==(32,6)
        assert mean_q==pytest.approx((np.array(PATTERNS[pi][1])+
                                      np.array(PATTERNS[pi][2]))/2)
        for budget_index,(cost,nsite,npool) in enumerate(BUDGETS):
            assert 16*6*nsite==6*npool==cost
            pooled=frozen_reference_calibration(pi,budget_index,0,q,mean_q)
            station=frozen_reference_calibration(pi,budget_index,1,q,mean_q)
            assert pooled["total_reference_passage_opportunities"]==cost
            assert station["total_reference_passage_opportunities"]==cost
            assert pooled["source_sampling_correct_iid_binomial"]
            assert station["source_sampling_correct_iid_binomial"]
            assert pooled["number_independent_calibration_groups"]==6
            assert station["number_independent_calibration_groups"]==96
            assert pooled["source_to_physical_site_transport_valid"]==(pi==0)
            assert station["source_to_physical_site_transport_valid"]


def test_station_q_gradient_is_NOT_covered_just_by_accurate_population_mean():
    a,b=np.array(PATTERNS[1][1]),np.array(PATTERNS[1][2])
    mean=(a+b)/2
    assert max(abs(a-mean))>.28
    assert max(abs(b-mean))>.28
    # Even with PERFECT source q mean, individual stations can
    # lie outside the source interval. Source q is not false.
    source_lo=mean.copy()
    source_hi=mean.copy()
    assert np.all((source_lo<=mean)&(mean<=source_hi))
    assert not np.all((source_lo<=a)&(a<=source_hi))
    assert not np.all((source_lo<=b)&(b<=source_hi))
    # Exact CP boundary / zero-q failure.
    lo,hi=exact_joint_cp(np.array([0,10,15,20,10,30]),40)
    assert lo[0]==0 and hi[0]>0
    assert np.all((lo>=0)&(lo<=hi)&(hi<=1))


def test_vectorized_outer_normalizer_extrema_include_all_six_clock_q_vertices():
    a=np.tile(np.array([.22,.14,.18,.21,.11,.14]),(82,1))
    b=np.tile(np.array([.16,.24,.18,.1,.12,.2]),(82,1))
    a/=a.sum(axis=1,keepdims=True)
    b/=b.sum(axis=1,keepdims=True)
    low=np.tile(np.array([.35,.28,.31,.45,.41,.33]),(16,1))
    high=low+.19
    minratio,maxratio=vectorized_date_fractional_extrema(a,b,low,high)
    brute=[]
    for vertex in product((0,1),repeat=6):
        q=np.where(vertex,high[0],low[0])
        brute.append(float((a[0]@q)/(b[0]@q)))
    assert minratio.shape==maxratio.shape==(16,82)
    assert np.allclose(minratio,min(brute),atol=1e-12)
    assert np.allclose(maxratio,max(brute),atol=1e-12)
    assert np.all(maxratio>=minratio)


def test_pooled_heterogeneous_q_HOLD_does_not_consult_oracle_coverage():
    a=np.full((82,96),1/96)
    b=a.copy()
    a[:,4:20]*=3
    a/=a.sum(axis=1,keepdims=True)
    observations=np.zeros((16,82,96),dtype=int)
    observations[:,:,5]=20
    types=make_32_physical_site_types(1)
    qs,pool=source_q_and_station_q(1,types)
    ref=frozen_reference_calibration(1,0,qs,pool,0)
    res=station_site_majority(observations,a,b,qs[16:],ref)
    assert res["scope"]=="HOLD_POOLED_Q_NOT_PORTABLE_TO_INDIVIDUAL_SITE"
    assert res["site_majority_certified"] is None
    assert res["exact_16_site_one_sided_p"] is None
    changed={**ref,
        "source_joint_q_coverage_ORACLE_AUDIT_ONLY":False,
        "heldout_site_specific_q_coverage_ORACLE_AUDIT_ONLY":False}
    assert station_site_majority(observations,a,b,qs[16:],changed)[
        "scope"]==res["scope"]
    # Independent valid SOURCE 50:50 mixture q is not q of each camera.
    station_ref=frozen_reference_calibration(1,0,1,qs,pool)
    assert station_ref["source_to_physical_site_transport_valid"]


def test_all_96_frozen_clock_comparisons_and_q_site_scope_invariants():
    res=run_first_site_q_transport_panel(PLAN,PARENT,CAL)
    assert res["status"]=="SOURCE_FREE_IID_POOLED_VERSUS_SITE_SPECIFIC_CAMERA_Q"
    assert res["total_precommitted_scenarios"]==96
    assert res["original_41_matched_astronomy_pairs"]==41
    assert res["original_same_civil_time_quarter_hour_bins"]==96
    assert res["heldout_independent_physical_sites"]==16
    assert res["calibration_q_simultaneous_alpha"]==.025
    assert res["four_site_majority_hypotheses_each_alpha"]==.00625
    assert res["per_scenario_total_false_certification_alpha_under_iid_sites_and_valid_q"]==.05
    assert len(res["all_8_independent_reference_calibration_receipts"])==8
    cases=res["all_96_precommitted_model_comparisons"]
    assert len(cases)==96
    assert sum(z["scope"]=="HOLD_POOLED_Q_NOT_PORTABLE_TO_INDIVIDUAL_SITE"
               for z in cases)==24
    for z in cases:
        assert z["no_oracle_q_coverage_decision_gate"]
        assert [z["ordered_model_A"],z["ordered_model_B"]] in [
            list(x) for x in PAIRS]
        if z["scope"]=="SOURCE_SITE_Q_CALIBRATION_TRANSPORTS_TO_TARGET":
            assert z["physical_robust_positive_site_count"] in range(17)
            if z["site_majority_certified"]:
                assert z["physical_robust_positive_site_count"]>=14
        else:
            assert z["site_majority_certified"] is None
    assert res["station_q_outer_bounds_by_independently_extremizing_dates"]
    assert res["real_original_EcoBank_species_camera_hours_or_reference_q_not_accessed"]
    json.dumps(res,allow_nan=False)


def test_strict_pre_result_contract_and_unchanged_parent_ledger():
    changed=json.loads(json.dumps(PLAN))
    changed["true_camera_site_patterns"][1]["site_type_A"][0]=.91
    with pytest.raises(ValueError,match="frozen"):
        run_first_site_q_transport_panel(changed,PARENT,CAL)
    changed=json.loads(json.dumps(PARENT))
    changed["first_complete_ci_run"]=0
    with pytest.raises(ValueError,match="frozen"):
        run_first_site_q_transport_panel(PLAN,changed,CAL)
