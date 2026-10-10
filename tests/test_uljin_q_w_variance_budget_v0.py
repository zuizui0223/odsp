"""Independent reference q/w delta variance, analytic cost optimum, replay boundaries."""
from pathlib import Path
import json
import math
import numpy as np
import pytest
from odsp.uljin_q_w_variance_budget_v0 import (
    WORLDS,DESIGNS,REPS,NEAR,FAR,
    detector_log_or,local_variance_coefficients,
    variance_at_budget,analytic_continuous_allocation,
    one_design,run_full_decomposition
)

ROOT=Path(__file__).resolve().parents[1]
FROZEN=json.loads((ROOT/"ULJIN_Q_W_VARIANCE_BUDGET_V0_CONTRACT.json").read_text())
PARENT=json.loads((ROOT/"ULJIN_Q_W_EQUAL_BUDGET_V0_FIRST_RESULT_LEDGER.json").read_text())


def test_exact_q_and_w_gradient_coefficients_and_science_of_mixed_distance():
    balanced=local_variance_coefficients(NEAR,FAR,(.5,.5,.5,.5))
    mixed=local_variance_coefficients(NEAR,FAR,(.2,.8,.8,.2))
    assert balanced["A_q"]==pytest.approx(5/6,rel=1e-12)
    assert balanced["C_w"]==pytest.approx(1.,rel=1e-12)
    assert balanced["true_detector_OR"]==pytest.approx(1.)
    assert mixed["true_detector_OR"]==pytest.approx((.78/.42)**2)
    assert mixed["A_q"]>balanced["A_q"]
    assert mixed["C_w"]<balanced["C_w"]
    # All four season×phase cells contribute independently; signs only
    # affect direction of log OR and disappear in first-order variance.
    assert detector_log_or(np.asarray(NEAR),np.asarray(FAR),
                          np.asarray((.5,)*4))==pytest.approx(0)


def test_continuous_cost_optimum_verified_against_alternate_designs():
    for name,mix in WORLDS:
        c=local_variance_coefficients(NEAR,FAR,mix)
        optimum=analytic_continuous_allocation(c["A_q"],c["C_w"])
        r=optimum["continuous_optimal_nq_over_nw"]
        assert 0<r<2
        assert 0<optimum["fraction_total_reference_opportunities_to_q"]<1
        assert optimum["fraction_total_reference_opportunities_to_q"]+optimum[
            "fraction_total_reference_opportunities_to_w"]==pytest.approx(1)
        best=variance_at_budget(c["A_q"],c["C_w"],24000,r)
        assert all(best<=variance_at_budget(c["A_q"],c["C_w"],24000,z)+1e-13
                   for z in (.25,.5,.75,1.,2.,3.))
        assert variance_at_budget(c["A_q"],c["C_w"],12000,r)==pytest.approx(2*best)
        assert r==pytest.approx(math.sqrt(c["A_q"]/(2*c["C_w"])))


def test_all_reference_opportunity_budgets_identical_and_no_raw_records():
    for budget,options in DESIGNS:
        assert len(options)==3
        assert all(8*nq+4*nw==budget for name,nq,nw in options)
        assert [x[0] for x in options]==[
            "equal_per_cell","q_heavy","w_heavy"]
    assert REPS==800
    a=one_design(1,0,0,3)
    b=one_design(1,0,0,3)
    assert a==b
    assert a["budget"]==2400
    assert a["q_reference_opportunities"]+a["w_reference_opportunities"]==2400
    assert a["first_order_fraction_variance_due_to_q"]+a[
        "first_order_fraction_variance_due_to_w"]==pytest.approx(1)


def test_frozen_full_48_scenario_variance_panel_matches_mc_within_20pct():
    result=run_full_decomposition(FROZEN,PARENT)
    assert result["status"]=="SOURCE_FREE_Q_W_DELTA_VARIANCE_FULL_FIRST_PANEL"
    assert result["number_of_scenarios"]==48
    assert result["total_independent_worlds"]==48*REPS==38400
    assert result["independent_gold_standard_reference_replications_per_scenario"]==800
    assert len(result["all_original_equal_budget_scenarios"])==48
    assert result["first_order_only_not_exact_variance_or_confidence_interval"]
    for row in result["all_original_equal_budget_scenarios"]:
        assert abs(row["empirical_over_first_order_relative_error_or_null"])<=.2
        assert row["sample_variance_q_only_or_null"]>0
        assert row["sample_variance_w_only_or_null"]>0
        assert row["sample_variance_full_or_null"]>0
        assert row["q_reference_opportunities"]+row["w_reference_opportunities"]==row["budget"]
        assert row["first_order_fraction_variance_due_to_q"]+row[
            "first_order_fraction_variance_due_to_w"]==pytest.approx(1)
        assert not math.isnan(row["sample_bias_log_detector_OR"])
    assert not result["real_Uljin_animal_events_reference_sensors_not_accessed"] is False
    json.dumps(result,allow_nan=False)


def test_fail_closed_contract_and_parent_and_invalid_log_rate():
    altered=json.loads(json.dumps(FROZEN))
    altered["source_unchanged"]["strategies"][0]["nq_per_8_q_cell"][0]=201
    with pytest.raises(ValueError,match="frozen"):
        run_full_decomposition(altered,PARENT,_test_replicates=2)
    altered_parent=json.loads(json.dumps(PARENT))
    altered_parent["first_artifact_id"]=0
    with pytest.raises(ValueError,match="frozen"):
        run_full_decomposition(FROZEN,altered_parent,_test_replicates=2)
    with pytest.raises(ValueError):
        run_full_decomposition(FROZEN,PARENT,_test_replicates=0)
    with pytest.raises(ValueError):
        detector_log_or(np.array([0,.9,.9,.9]),np.array(FAR),
                       np.array([.5]*4))
    with pytest.raises(ValueError):
        variance_at_budget(.8,1.,1000.,0.)
