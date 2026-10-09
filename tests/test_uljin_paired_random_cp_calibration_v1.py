"""Fully paired source-free binomial q trials; no animal source access."""
import json
from pathlib import Path
import math
import numpy as np
import pytest

# SciPy is optional for ODSP's scientific core. Dedicated calibration
# CI installs it and runs all assertions; core must not fail collection.
pytest.importorskip("scipy", reason="optional exact beta-quantile calibration dependency")

from odsp.uljin_paired_random_cp_calibration_v1 import (
    TRUTHS,N_REF,ALPHA_CAL,ALPHA_TEST,ALPHA_ALL,REPS,
    exact_cp_four_cell_bounds,paired_world,paired_randomized_cp_panel,
)
from odsp.uljin_exact_cp_vs_hoeffding_q_v0 import exact_clopper_pearson
from odsp.uljin_independent_q_split_alpha_v0 import (
    _draw_one, independent_hoeffding_bounds,
)

ROOT=Path(__file__).resolve().parents[1]
PLAN=json.loads((ROOT/"ULJIN_PAIRED_RANDOM_CP_VS_HOEFFDING_V1_CONTRACT.json").read_text())
OLD=json.loads((ROOT/"ULJIN_INDEPENDENT_Q_SPLIT_ALPHA_V0_FIRST_RESULT_LEDGER.json").read_text())
CP_LEDGER=json.loads((ROOT/"ULJIN_EXACT_CP_VS_HOEFFDING_Q_V0_FIRST_RESULT_LEDGER.json").read_text())


def test_exact_CP_beta_quantiles_match_parent_exhaustive_binomial_inversion():
    for n in (50,200,1000,5000):
        for k in (0,1,n//4,int(.85*n),n-1,n):
            counts=(k,k,k,k)
            cp=exact_cp_four_cell_bounds(counts,n)
            old=exact_clopper_pearson(k,n)
            assert all(q==pytest.approx(old[0],abs=2e-9) for q in cp.lower)
            assert all(q==pytest.approx(old[1],abs=2e-9) for q in cp.upper)
            assert all(0<=lo<=hi<=1 for lo,hi in zip(cp.lower,cp.upper))
    assert ALPHA_CAL==ALPHA_TEST==.025
    assert ALPHA_ALL==ALPHA_CAL+ALPHA_TEST==.05


def test_same_rng_and_parent_hoeffding_result_is_replayed_for_individual_world():
    for ti in range(len(TRUTHS)):
        for ni in range(len(N_REF)):
            for rep in (0,7):
                paired=paired_world(ti,ni,rep)
                old=_draw_one(ti,ni,rep)
                assert paired["Hoeffding"]["joint_q_coverage"]==old[
                    "calibration_joint_q_coverage"]
                assert paired["Hoeffding"]["hold"]==old[
                    "detector_q_lower_zero_hold"]
                assert paired["Hoeffding"]["certification"]==old[
                    "robust_joint_alpha_rejects_latent_OR_le_1"]
                assert paired["Hoeffding"]["B"]==pytest.approx(
                    old["calibration_gamma_upper"])
                assert paired["naive_5pct_reject"]==old[
                    "naive_detector_ignorant_5pct_rejection"]
                assert paired["same_reference_successes_for_both_methods"]
                assert paired["same_animal_event_counts_for_both_methods"]


def test_fast_preflight_all_scenarios_and_paired_uncertainty():
    out=paired_randomized_cp_panel(PLAN,OLD,CP_LEDGER,_test_replicates=3)
    assert out["status"]=="SOURCE_FREE_CP_PAIRED_PREFLIGHT_ONLY"
    assert out["case_count"]==16
    assert out["total_worlds"]==48
    assert not out["replayed_parent_first_Hoeffding_outcomes_without_retuning"]
    for row in out["simulated_case_results"]:
        assert row["replicates"]==3
        assert all(0<=row[m]["certification_fraction"]<=1
                   for m in ("CP","Hoeffding"))
        assert row["CP_only_certification_count"]>=0
        assert row["Hoeffding_only_certification_count"]>=0
        assert -1<=row["paired_CP_minus_Hoeffding_certification_fraction"]<=1
        for m in ("CP","Hoeffding"):
            assert 0<=row[m]["empirical_four_q_simultaneous_coverage_fraction"]<=1
            assert 0<=row[m]["no_finite_q_crossproduct_HOLD_fraction"]<=1
    assert out==paired_randomized_cp_panel(PLAN,OLD,CP_LEDGER,
                                         _test_replicates=3)
    assert out["coverage_guarantee_from_mathematics_not_600_draws"]
    assert not out["real_camera_sensor_reference_and_ungulate_events_opened"]


def test_fail_closed_on_frozen_methods_lineage_and_calibration_scenarios():
    altered=json.loads(json.dumps(PLAN))
    altered["methods"]["animal_conditional_alpha"]=.05
    with pytest.raises(ValueError,match="contract"):
        paired_randomized_cp_panel(altered,OLD,CP_LEDGER,_test_replicates=1)
    prior=json.loads(json.dumps(OLD))
    prior["first_complete_ci_run"]=1
    with pytest.raises(ValueError,match="contract"):
        paired_randomized_cp_panel(PLAN,prior,CP_LEDGER,_test_replicates=1)
    with pytest.raises(ValueError):
        paired_randomized_cp_panel(PLAN,OLD,CP_LEDGER,_test_replicates=0)
    with pytest.raises(ValueError):
        exact_cp_four_cell_bounds((2,3,4,51),50)
