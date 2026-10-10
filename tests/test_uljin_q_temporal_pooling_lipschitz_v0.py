"""Independent true-passage source-time pooling with per-day external drift q bands."""
from pathlib import Path
import json
import numpy as np
import pytest

pytest.importorskip("scipy",reason="optional exact detector q Clopper Pearson intervals")
from odsp.uljin_q_temporal_pooling_lipschitz_v0 import (
    LENGTHS,PATTERNS,DAILY_COUNTS,TOTALS,groups_for_41_days,
    pooled_source_reference,full_frozen_temporal_pooling_panel,
)
from odsp.uljin_station_season_camera_q_v0 import physical_site_q
from odsp.uljin_within_branch_daily_q_drift_v0 import true_daily_q
from odsp.uljin_common_clock_mechanistic_comparison_v0 import original_days

ROOT=Path(__file__).resolve().parents[1]
PLAN=json.loads((ROOT/"ULJIN_Q_TEMPORAL_POOLING_LIPSCHITZ_V0_CONTRACT.json").read_text())
PARENT=json.loads((ROOT/"ULJIN_WITHIN_BRANCH_DAILY_Q_DRIFT_V0_FIRST_RESULT_LEDGER.json").read_text())
CAL=json.loads((ROOT/"ULJIN_PHOTOPERIOD_MIRROR_2022_V0_DESIGN_CONTRACT.json").read_text())


def test_frozen_uniform_reference_date_partitions_cover_every_original_day():
    assert LENGTHS==(1,3,7,41)
    assert [len(groups_for_41_days(m)) for m in LENGTHS]==[41,14,6,1]
    for m in LENGTHS:
        groups=groups_for_41_days(m)
        assert [x for g in groups for x in g]==list(range(41))
        assert sum(len(g) for g in groups)==41
        assert all(0<len(g)<=m for g in groups)
        assert all(g==tuple(range(g[0],g[-1]+1)) for g in groups)
    with pytest.raises(ValueError):
        groups_for_41_days(6)


def test_external_absolute_lipschitz_guarantees_group_means_enclose_daily_q():
    dates,branch=original_days(CAL)
    types,qbar=physical_site_q(1)
    for wi,(name,amp,L) in enumerate(PATTERNS):
        actual=true_daily_q(branch,qbar,types,amp)
        for b in (0,1):
            assert np.max(np.abs(np.diff(actual[:,b::2,:],axis=1)))<=L+1e-12
        for budget_i,(n_day,T) in enumerate(zip(DAILY_COUNTS,TOTALS)):
            for length in LENGTHS:
                cal=pooled_source_reference(actual,wi,budget_i,length)
                assert cal["total_reference_opportunities"]==T
                assert T==16*2*6*41*n_day
                assert cal["n_source_groups_simultaneous"]==16*2*6*len(
                    groups_for_41_days(length))
                assert cal["daily_lower"].shape==cal["daily_upper"].shape==(16,82,6)
                assert np.all((cal["daily_lower"]>=0)&(
                    cal["daily_lower"]<=cal["daily_upper"])&(
                    cal["daily_upper"]<=1))
                if cal["q_group_means_CP_joint_coverage_ORACLE_ONLY"]:
                    assert cal["individual_day_q_joint_coverage_ORACLE_ONLY"]
                    assert np.all(cal["daily_lower"]<=actual[16:]+1e-12)
                    assert np.all(cal["daily_upper"]>=actual[16:]-1e-12)
                assert cal["source_date_iid_uniform_for_every_passage"]
                assert cal["all_original_41_dates_retained"]


def test_finite_sample_group_q_error_budget_and_no_source_observation_leak():
    assert PARENT["first_scored_workflow_run"]==38035769887
    assert PLAN["statistical_procedure"]["q_joint_alpha"]==.025
    assert PLAN["statistical_procedure"][
        "site_majority_alpha_each_fixed_model_pair"]==.00625
    assert 4*.00625+.025==.05
    assert PLAN["uniform_reference_opportunities"]["reference_seed"]==2026101029
    _,branch=original_days(CAL)
    labels,base=physical_site_q(1)
    actual=true_daily_q(branch,base,labels,.35)
    a=pooled_source_reference(actual,1,0,7)
    b=pooled_source_reference(actual,1,0,7)
    assert np.array_equal(a["daily_lower"],b["daily_lower"])
    assert np.array_equal(a["daily_upper"],b["daily_upper"])
    assert a["external_abs_adjacent_day_L_assumed"]==.03
    assert a["group_count_per_branch"]==6


def test_frozen_384_cases_each_method_calibrates_same_96_clock_bins():
    out=full_frozen_temporal_pooling_panel(PLAN,PARENT,CAL)
    assert out["status"]=="SOURCE_FREE_SOURCE_Q_TEMPORAL_POOLING_LIPSCHITZ_FULL_V0"
    assert out["matched_original_mirror_date_pairs"]==41
    assert out["same_civil_15min_clock_bins"]==96
    assert out["independent_heldout_physical_sites"]==16
    assert len(out["all_first_96_model_cases_x_four_q_temporal_scales"])==96
    assert len(out["all_16_external_q_reference_calibration_receipts"])==16
    assert out["total_predeclared_time_pooling_results"]==384
    assert out["per_original_selected_design_false_certification_alpha_with_external_L"]==.05
    assert out["source_true_q_oracle_coverage_not_used_for_model_inference"]
    for r in out["all_first_96_model_cases_x_four_q_temporal_scales"]:
        arms=r["four_predeclared_grouped_q_calibration_results"]
        assert set(arms)==set(str(v) for v in LENGTHS)
        for a in arms.values():
            assert a["oracle_coverage_not_a_decision_gate"]
            if a["status"]=="VALID_SYNTHETIC_EXTERNAL_L_GROUP_Q_BOUNDS":
                assert a["physical_robust_positive_site_count"] in range(17)
                if a["site_majority_certified"]:
                    assert a["physical_robust_positive_site_count"]>=14
            else:
                assert a["site_majority_certified"] is None
    json.dumps(out,allow_nan=False)


def test_synthetic_contract_and_parent_first_result_frozen():
    changed=json.loads(json.dumps(PLAN))
    changed["uniform_reference_opportunities"]["time_pooling_lengths"]=[1,4,7,41]
    with pytest.raises(ValueError,match="frozen"):
        full_frozen_temporal_pooling_panel(changed,PARENT,CAL)
    prev=json.loads(json.dumps(PARENT))
    prev["first_scored_workflow_run"]=0
    with pytest.raises(ValueError,match="frozen"):
        full_frozen_temporal_pooling_panel(PLAN,prev,CAL)
