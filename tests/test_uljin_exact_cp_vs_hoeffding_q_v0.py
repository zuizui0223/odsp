"""Exact four-cell Clopper-Pearson/Binomial inversion and detector sensitivity."""
import json
from pathlib import Path
import math
import pytest
import numpy as np

from odsp.uljin_exact_cp_vs_hoeffding_q_v0 import (
    TAIL_ALPHA,exact_clopper_pearson,four_cell_cp_bounds,
    compare_all_fixed_reference_calibrations,
)
from odsp.uljin_independent_q_split_alpha_v0 import (
    independent_hoeffding_bounds,ALPHA_CAL,ALPHA_TEST
)

ROOT=Path(__file__).resolve().parents[1]
PLAN=json.loads((ROOT/"ULJIN_EXACT_CP_VS_HOEFFDING_Q_V0_CONTRACT.json").read_text())
PRIOR=json.loads((ROOT/"ULJIN_INDEPENDENT_Q_SPLIT_ALPHA_V0_FIRST_RESULT_LEDGER.json").read_text())


def test_CP_binomial_boundary_closed_form_and_inversion():
    for n in (10,50):
        lo,hi,rl,rh=exact_clopper_pearson(0,n)
        assert lo==0
        assert hi==pytest.approx(1-TAIL_ALPHA**(1/n),abs=1e-12)
        lo,hi,rl,rh=exact_clopper_pearson(n,n)
        assert lo==pytest.approx(TAIL_ALPHA**(1/n),abs=1e-12)
        assert hi==1
    for k,n in ((4,10),(25,50),(170,200),(850,1000)):
        lo,hi,rlo,rhi=exact_clopper_pearson(k,n)
        assert 0<lo<k/n<hi<1
        assert max(rlo,rhi)<5e-8
    with pytest.raises(ValueError):
        exact_clopper_pearson(4,2)
    with pytest.raises(ValueError):
        exact_clopper_pearson(1,5001)


def test_simultaneous_bonferroni_alpha_spending_is_same_as_parent_hoeffding():
    assert TAIL_ALPHA==ALPHA_CAL/8
    assert ALPHA_CAL==ALPHA_TEST==.025
    assert ALPHA_CAL+ALPHA_TEST==.05
    for n in (50,200,1000):
        successes=tuple(int(round(n*p)) for p in (.85,.85,.85,.85))
        exact,err=four_cell_cp_bounds(successes,n)
        hoeff=independent_hoeffding_bounds(successes,n)
        assert err<5e-8
        assert exact.covers((.85,)*4)
        assert hoeff.covers((.85,)*4)
        assert 0<exact.detector_gamma_upper
        assert 0<hoeff.detector_gamma_upper


def test_full_16_fixed_representative_calibration_comparisons_and_no_empirical_claims():
    out=compare_all_fixed_reference_calibrations(PLAN,PRIOR)
    assert out["status"]=="SOURCE_FREE_EXACT_CP_VS_HOEFFDING_JOINT_Q_DESIGN_ONLY"
    assert len(out["all_16_fixed_calibration_cases"])==16
    assert out["four_cell_joint_detector_q_coverage_guaranteed_by_union_bound"]==.975
    assert out["total_combined_false_certification_error_upper_bound"]==.05
    assert out["no_monte_carlo_power_or_sample_cost_calculated"]
    assert out["representative_rounding_not_a_stochastic_calibration_observation"]
    assert not out["real_ecobank_reference_or_wildlife_records_opened"]
    assert set(out["strong_animal_effect_first_certifying_reference_n_per_cell_on_frozen_grid"])=={
        "exact_CP","Hoeffding"}
    for case in out["all_16_fixed_calibration_cases"]:
        assert case["max_CP_tail_inversion_residual"]<5e-8
        for method in ("exact_CP","Hoeffding"):
            r=case[method]
            assert r["four_q_reference_truth_covered_in_illustrative_sample"]
            assert 0<=r["robust_one_sided_exact_animal_null_p"]<=1
            assert r["one_sided_97p5pct_lower_latent_encounter_OR"]>=0
    assert all(case["reference_binomial_opportunities_per_cell"] in (50,200,1000,5000)
               for case in out["all_16_fixed_calibration_cases"])
    json.dumps(out,allow_nan=False)


def test_preregistered_contract_and_parent_attestation_fail_closed():
    changed=json.loads(json.dumps(PLAN))
    changed["animals_exact_test_alpha"]=.05
    with pytest.raises(ValueError,match="frozen"):
        compare_all_fixed_reference_calibrations(changed,PRIOR)
    changed=json.loads(json.dumps(PRIOR))
    changed["first_complete_ci_run"]=1
    with pytest.raises(ValueError,match="frozen"):
        compare_all_fixed_reference_calibrations(PLAN,changed)
