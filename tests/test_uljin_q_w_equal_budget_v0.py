"""Pre-outcome source-free equal-cost q/w opportunity design and inference gates."""
from pathlib import Path
import json
import math
import pytest

pytest.importorskip("scipy",reason="optional exact binomial q/w calibration")
from odsp.uljin_q_w_equal_budget_v0 import (
    DESIGNS,WORLDS,REPS,ALPHA_Q,ALPHA_W,ALPHA_TEST,
    _simulate_one,run_allocation_panel
)
ROOT=Path(__file__).resolve().parents[1]
FROZEN=json.loads((ROOT/"ULJIN_Q_W_EQUAL_BUDGET_V0_CONTRACT.json").read_text())
PARENT=json.loads((ROOT/"ULJIN_DISTANCE_MIX_TIPPING_RADIUS_V0_FIRST_RESULT_LEDGER.json").read_text())


def test_equal_q_w_gold_standard_passage_opportunities_and_frozen_alpha():
    assert len(WORLDS)==4
    assert len(DESIGNS)==4
    assert REPS==200
    assert ALPHA_Q==ALPHA_W==.0125
    assert ALPHA_TEST==.025
    assert ALPHA_Q+ALPHA_W+ALPHA_TEST==.05
    for budget,designs in DESIGNS:
        assert len(designs)==3
        assert [x[0] for x in designs]==["equal_per_cell","q_heavy","w_heavy"]
        assert all(8*q_n+4*w_n==budget and q_n>0 and w_n>0
                   for _,q_n,w_n in designs)


def test_source_free_null_distance_mix_can_alias_season_without_true_encounter():
    equal=WORLDS[0]
    confounded=WORLDS[1]
    assert equal[1]==confounded[1]==1.
    assert equal[2]==(.5,.5,.5,.5)
    assert confounded[2]==(.2,.8,.8,.2)
    a=_simulate_one(1,2,0,23)
    b=_simulate_one(1,2,0,23)
    assert a==b
    assert a["true_detector_gamma"]==pytest.approx((.78/.42)**2)
    assert a["exact_animal_total"]==sum(confounded[3])
    assert 0<=a["B"]


def test_new_source_free_design_full_three_allocations_per_budget_fast():
    result=run_allocation_panel(FROZEN,PARENT,_test_replicates=3)
    assert result["status"]=="SOURCE_FREE_Q_W_ALLOCATION_PREFLIGHT"
    assert result["world_count"]==4*4*3*3
    assert result["truth_case_count"]==48
    assert result["original_same_cost_opportunity_accounting_verified"]
    assert result["conditional_false_certification_union_bound"]==.05
    assert result["coverage_guarantee_requires_independent_valid_reference_labels"]
    assert result["oracle_comparison_not_equal_cost"]
    assert result["real_EcoBank_events_original_device_logs_reference_passages_read"] is False
    assert run_allocation_panel(FROZEN,PARENT,_test_replicates=3)==result
    for row in result["all_predeclared_worlds"]:
        assert row["q_reference_opportunities_total"]+row[
            "w_reference_opportunities_total"]==row["reference_budget_opportunities"]
        for key in ("robust_latent_encounter_certification_fraction",
                    "eight_q_joint_coverage","four_w_joint_coverage",
                    "twelve_cell_joint_coverage","zero_detector_q_lower_HOLD_fraction"):
            assert 0<=row[key]<=1
        assert row["robust_certification_mc_standard_error"]>=0
    json.dumps(result,allow_nan=False)


def test_frozen_plans_fail_if_post_result_allocation_or_source_changed():
    altered=json.loads(json.dumps(FROZEN))
    altered["reference_budgets_and_allocations"][0]["strategies"][0]["w_n"]=250
    with pytest.raises(ValueError,match="frozen"):
        run_allocation_panel(altered,PARENT,_test_replicates=1)
    prior=json.loads(json.dumps(PARENT))
    prior["first_scored_ci_run"]=0
    with pytest.raises(ValueError,match="frozen"):
        run_allocation_panel(FROZEN,prior,_test_replicates=1)
    with pytest.raises(ValueError):
        run_allocation_panel(FROZEN,PARENT,_test_replicates=201)
    with pytest.raises(ValueError):
        _simulate_one(5,0,0,0)
