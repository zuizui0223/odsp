"""Source-free joint CP reference calibration across original 82×96 clock bins."""
from pathlib import Path
import json
import numpy as np
import pytest

pytest.importorskip("scipy",reason="optional exact independent CP detector q calibration")
from odsp.uljin_96bin_simultaneous_q_calibration_v0 import (
    SEED,TRUTH_IDS,COUNTS,PATTERNS,METHODS,BUDGETS,ALPHA,
    true_detector_q,_binomial_joint_cp,independent_detector_calibration,
    first_calibrated_96bin_panel
)
from odsp.uljin_common_clock_mechanistic_comparison_v0 import original_days

ROOT=Path(__file__).resolve().parents[1]
CAL=json.loads((ROOT/"ULJIN_PHOTOPERIOD_MIRROR_2022_V0_DESIGN_CONTRACT.json").read_text())
PLAN=json.loads((ROOT/"ULJIN_96BIN_SIMULTANEOUS_Q_CALIBRATION_V0_CONTRACT.json").read_text())
PARENT=json.loads((ROOT/"ULJIN_COMMON_96BIN_DETECTOR_ENVELOPE_V0_FIRST_RESULT_LEDGER.json").read_text())


def test_frozen_82days_and_clock_q_truth_within_4h_heterogeneity():
    dates,branch=original_days(CAL)
    assert len(dates)==82 and len(branch)==82
    qblock=true_detector_q(branch,PATTERNS[0])
    qfine=true_detector_q(branch,PATTERNS[1])
    assert qblock.shape==qfine.shape==(82,96)
    assert np.allclose(qblock.reshape(82,6,16).mean(axis=2),
                       qfine.reshape(82,6,16).mean(axis=2),atol=1e-14)
    assert np.max(np.abs(qfine-qblock))>.12
    assert np.max(np.abs(qblock-qblock.reshape(82,6,16).mean(axis=2).repeat(16,axis=1)))<1e-14


def test_equal_reference_budget_and_valid_source_not_15min_target_block_calibration():
    _,branch=original_days(CAL)
    for budget_index,(budget,n6,n96) in enumerate(BUDGETS):
        assert 82*6*n6==82*96*n96==budget
        for i,pattern in enumerate(PATTERNS):
            q=true_detector_q(branch,pattern)
            outputs=[independent_detector_calibration(q,i,budget_index,k)
                     for k in (0,1)]
            assert outputs[0]["total_external_reference_opportunities"]==budget
            assert outputs[1]["total_external_reference_opportunities"]==budget
            assert outputs[0]["number_external_calibrated_source_cells"]==82*6
            assert outputs[1]["number_external_calibrated_source_cells"]==82*96
            assert outputs[0]["calibration_q_group_law_is_exact_binomial"]
            assert outputs[1]["calibration_q_group_law_is_exact_binomial"]
            assert not outputs[0]["calibration_groups_may_not_reflect_quarterhour_q"] if i==0 else outputs[0]["calibration_groups_may_not_reflect_quarterhour_q"]
            assert not outputs[1]["calibration_groups_may_not_reflect_quarterhour_q"]
            assert outputs[0]["q_lower"].shape==(82,6)
            assert outputs[1]["q_lower"].shape==(82,96)
            if outputs[0]["simultaneous_TRUE_96_CLOCK_BIN_q_coverage"]:
                assert outputs[0]["simultaneous_source_q_confidence_coverage"]


def test_binomial_CP_4h_and_15min_joint_spending_and_nonzero_conditions():
    for G,n in ((6,512),(96,32)):
        counts=np.full((82,G),int(round(.6*n)),dtype=int)
        lower,upper=_binomial_joint_cp(counts,n,ALPHA)
        assert lower.shape==upper.shape==(82,G)
        assert np.all(lower<=.6) and np.all(upper>=.6)
        assert ALPHA/(2*82*G)>0
        assert np.all(lower>0)
    bad=np.full((82,6),0,dtype=int)
    l,u=_binomial_joint_cp(bad,512,ALPHA)
    assert np.all(l==0) and np.all(u>0)
    with pytest.raises(ValueError):
        _binomial_joint_cp(np.full((82,6),513),512,ALPHA)


def test_complete_predeclared_192_report_panel_has_source_free_CI_scope_gates():
    result=first_calibrated_96bin_panel(PLAN,PARENT,CAL)
    assert result["status"]=="SOURCE_FREE_JOINT_CP_Q_CALIBRATION_96_CIVIL_BIN_SCOPE_AUDIT"
    assert result["original_41_calendar_pairs_retained"]
    assert result["original_15min_clock_bins"]==96
    assert result["physical_heldout_sites"]==16
    assert result["total_192_precommitted_score_envelopes"]==192
    assert len(result["all_8_q_calibration_source_coverage_receipts"])==8
    assert len(result["all_192_model_score_envelope_results"])==192
    assert result["joint_CP_coverage_not_independent_site_sampling_confidence"]
    assert result["four_hour_calibration_not_portable_to_15min_heterogeneous_q"]
    assert result["real_camera_q_references_and_original_ungulate_events_unopened"]
    for row in result["all_192_model_score_envelope_results"]:
        assert row["status"] in (
            "HOLD_Q_CALIBRATION_LOWER_ZERO",
            "VALID_CALIBRATION_SCOPE_FOR_SOURCE_FREE_SAMPLE",
            "UNQUALIFIED_TIME_BIN_Q_SCOPE_OR_CALIBRATION_NONCOVERAGE")
        if row["status"]=="VALID_CALIBRATION_SCOPE_FOR_SOURCE_FREE_SAMPLE":
            assert row["contains_true_q_conditional_sample_gap"]
            assert row["calibrated_q_envelope_lower_sample_gap"]<=row[
                "conditional_true_q_gap_diagnostic_only"]+1e-10
            assert row["calibrated_q_envelope_upper_sample_gap"]>=row[
                "conditional_true_q_gap_diagnostic_only"]-1e-10
        if (row["true_camera_q_temporal_pattern"]==PATTERNS[1] and
            row["calibration_clock_granularity"]==METHODS[0]):
            assert row["status"]!="VALID_CALIBRATION_SCOPE_FOR_SOURCE_FREE_SAMPLE"
            assert row.get("certified_model_order") is None
    json.dumps(result,allow_nan=False)


def test_contract_mutations_fail_closed_and_same_41_pairs_unmodified():
    revised=json.loads(json.dumps(PLAN))
    revised["calibration_experiment"]["fixed_reference_budgets"][0][
        "per_82date_96_clock_bin"]=33
    with pytest.raises(ValueError,match="frozen"):
        first_calibrated_96bin_panel(revised,PARENT,CAL)
    changed=json.loads(json.dumps(PARENT))
    changed["first_scored_ci_run"]=1
    with pytest.raises(ValueError,match="frozen"):
        first_calibrated_96bin_panel(PLAN,changed,CAL)
