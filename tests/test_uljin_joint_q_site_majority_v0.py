"""Simultaneous detector-q calibration + exact 16 independent-site majority tests."""
from __future__ import annotations
import json
from pathlib import Path
from math import comb
import numpy as np
import pytest

pytest.importorskip("scipy", reason="optional original PR257 exact q reference calibration")
from odsp.uljin_joint_q_site_majority_v0 import (
    N_SITE,ALPHA_Q,ALPHA_SITES,ALPHA_PER_PAIR,SITE_TAIL_THRESHOLD,
    exact_site_majority_right_tail,sitewise_shared_q_score_bounds,
    frozen_site_majority_full_panel,
)

ROOT=Path(__file__).resolve().parents[1]
PLAN=json.loads((ROOT/"ULJIN_JOINT_Q_SITE_MAJORITY_V0_CONTRACT.json").read_text())
PARENT=json.loads((ROOT/"ULJIN_96BIN_SIMULTANEOUS_Q_CALIBRATION_V0_FIRST_RESULT_LEDGER.json").read_text())
CAL=json.loads((ROOT/"ULJIN_PHOTOPERIOD_MIRROR_2022_V0_DESIGN_CONTRACT.json").read_text())


def test_exact_16_physical_site_binomial_threshold_and_four_way_error_budget():
    assert N_SITE==16 and SITE_TAIL_THRESHOLD==14
    assert ALPHA_Q==ALPHA_SITES==.025
    assert 4*ALPHA_PER_PAIR==ALPHA_SITES
    assert ALPHA_Q+ALPHA_SITES==.05
    assert exact_site_majority_right_tail(16)==pytest.approx(1/65536)
    assert exact_site_majority_right_tail(14)==pytest.approx(137/65536)
    assert exact_site_majority_right_tail(13)==pytest.approx(697/65536)
    assert exact_site_majority_right_tail(14)<ALPHA_PER_PAIR
    assert exact_site_majority_right_tail(13)>ALPHA_PER_PAIR
    with pytest.raises(ValueError):
        exact_site_majority_right_tail(14,n=82)
    with pytest.raises(ValueError):
        exact_site_majority_right_tail(17)


def test_model_ranking_and_sign_are_INDEPENDENT_of_oracle_cp_coverage_flag():
    a=np.full((82,96),1/96,dtype=float)
    b=np.full((82,96),1/96,dtype=float)
    # Both original 96-bin predictions are positive, normalized.
    a[:,5]*=3
    a/=a.sum(axis=1,keepdims=True)
    data=np.zeros((16,82,96),dtype=int)
    data[:,:,5]=20
    true_q=np.full((82,96),.6)
    base={
        "method":"individual_96_civil_15min_bins",
        "q_lower":np.full((82,96),.6),
        "q_upper":np.full((82,96),.6),
        "calibration_groups_may_not_reflect_quarterhour_q":False,
        "HOLD_some_reference_q_lower_is_zero":False,
        "simultaneous_source_q_confidence_coverage":True,
        "simultaneous_TRUE_96_CLOCK_BIN_q_coverage":True,
    }
    positive=sitewise_shared_q_score_bounds(data,a,b,true_q,base)
    assert positive["robust_site_positive_count"]==16
    assert positive["exact_site_majority_p_value"]==pytest.approx(1/65536)
    assert positive["inferential_site_majority_decision"]==(
        "A_BETTER_AT_MAJORITY_OF_NEW_SITES_CERTIFIED"
    )
    assert positive["q_interval_contained_true_q_site_scores_ORACLE_ONLY"]
    # A SOURCE calibration can miss true q with ≤.025 frequency. The
    # statistical decision must still run, not be selected on hidden truth!
    notcovered={**base,
        "simultaneous_source_q_confidence_coverage":False,
        "simultaneous_TRUE_96_CLOCK_BIN_q_coverage":False}
    independent=sitewise_shared_q_score_bounds(data,a,b,true_q,notcovered)
    assert independent["inferential_site_majority_decision"]==positive[
        "inferential_site_majority_decision"]
    assert independent["robust_site_positive_count"]==16
    assert independent["exact_site_majority_p_value"]==positive[
        "exact_site_majority_p_value"]
    # If actual clock granularity is WRONG, statistical ranking is HOLD
    # independent of the observed positive count.
    coarse={**base,
        "method":"six_clock_4hour_blocks",
        "q_lower":np.full((82,6),.6),
        "q_upper":np.full((82,6),.6),
        "calibration_groups_may_not_reflect_quarterhour_q":True}
    hold=sitewise_shared_q_score_bounds(data,a,b,true_q,coarse)
    assert hold["admission_status"]=="HOLD_TIME_RESOLUTION_NOT_ADMISSIBLE"
    assert hold["inferential_site_majority_decision"] is None


def test_zero_lower_q_hold_does_not_fabricate_detector_model_majority():
    aa=np.full((82,96),1/96,dtype=float)
    data=np.ones((16,82,96),dtype=int)
    cal={
        "method":"six_clock_4hour_blocks",
        "q_lower":np.zeros((82,6),dtype=float),
        "q_upper":np.ones((82,6),dtype=float),
        "calibration_groups_may_not_reflect_quarterhour_q":False,
        "HOLD_some_reference_q_lower_is_zero":True,
        "simultaneous_source_q_confidence_coverage":False,
        "simultaneous_TRUE_96_CLOCK_BIN_q_coverage":False
    }
    hold=sitewise_shared_q_score_bounds(data,aa,aa,
                                        np.full((82,96),.7),cal)
    assert hold["admission_status"]=="HOLD_Q_REFERENCE_LOWER_ZERO"
    assert hold["exact_site_majority_p_value"] is None
    assert hold["inferential_site_majority_decision"] is None


def test_full_frozen_192_source_free_site_majority_and_q_calibration_worlds():
    result=frozen_site_majority_full_panel(PLAN,PARENT,CAL)
    assert result["status"]=="SOURCE_FREE_JOINT_Q_AND_INDEPENDENT_SITE_MAJORITY_TEST_ONLY"
    assert result["original_astronomical_matched_date_pairs"]==41
    assert result["same_civil_15min_time_bins"]==96
    assert result["training_physical_sites"]==16
    assert result["independent_heldout_physical_sites"]==16
    assert result["total_predeclared_cases"]==192
    assert len(result["all_eight_first_source_calibration_audits"])==8
    assert result["combined_per_scenario_false_certification_alpha_bound"]==.05
    assert result["source_q_oracle_coverage_not_an_operational_admission_condition"]
    assert result["new_site_majority_probability_not_mean_expected_site_score"]
    assert result["per_design_not_simultaneously_over_all_192_truth_worlds"]
    assert result["real_original_EcoBank_wildlife_camera_or_external_reference_NOT_opened"]
    rows=result["all_192_predefined_source_free_q_and_site_cases"]
    assert sum(x["admission_status"]=="HOLD_TIME_RESOLUTION_NOT_ADMISSIBLE"
               for x in rows)==48
    for row in rows:
        assert row["oracle_coverage_never_used_as_decision_gate"]
        if row["admission_status"]=="SOURCE_TEMPORAL_SCOPE_VALID_Q_CI_FOR_SITE_TEST":
            assert row["robust_site_positive_count"] in range(17)
            assert row["exact_site_majority_p_value"]==pytest.approx(
                exact_site_majority_right_tail(row["robust_site_positive_count"]))
            assert len(row["sitewise_robust_lower"])==16
            assert len(row["sitewise_robust_upper"])==16
            if row["inferential_site_majority_decision"]==(
                "A_BETTER_AT_MAJORITY_OF_NEW_SITES_CERTIFIED"):
                assert row["robust_site_positive_count"]>=14
        else:
            assert row["inferential_site_majority_decision"] is None
    json.dumps(result,allow_nan=False)


def test_precommitment_and_first_parent_result_guard_fail_closed():
    edited=json.loads(json.dumps(PLAN))
    edited["error_allocation"]["site_majority_each_of_four_pairwise_one_sided_alpha"]=.05
    with pytest.raises(ValueError,match="frozen"):
        frozen_site_majority_full_panel(edited,PARENT,CAL)
    edited_parent=json.loads(json.dumps(PARENT))
    edited_parent["first_complete_ci_run"]=0
    with pytest.raises(ValueError,match="frozen"):
        frozen_site_majority_full_panel(PLAN,edited_parent,CAL)
