"""Synthetic Simpson composition: nuisance assumptions and null permutation tests."""
import json
from pathlib import Path
import numpy as np
import pytest

from odsp.uljin_stratum_composition_simpson_v0 import (
    SITES, PAIR_COUNT, PERMS, EARLY, LATE, SCENARIOS, SCALES, SEED,
    two_type_population_oracle, synthetic_world, partially_pooled_training_fit,
    conditional_permutation_test, evaluate_world, run_panel,
)
from odsp.uljin_finite_sample_clock_alias_selection_v0 import TRAIN_IDX, TEST_IDX

ROOT=Path(__file__).resolve().parents[1]
PLAN=json.loads((ROOT/"ULJIN_STRATUM_COMPOSITION_SIMPSON_V0_CONTRACT.json").read_text())


def test_simpson_oracle_true_within_type_shape_invariant_and_aggregate_changes():
    oracle=two_type_population_oracle()
    assert not oracle["true_branch_by_bin_interaction_within_each_type"]
    assert oracle["pooled_first_bin_ratio"]>2.7
    assert oracle["pooled_last_bin_ratio"]<0.7
    assert oracle["pooled_log_rate_ratio_first_minus_last"]>1
    for name,ratio_a,ratio_b,shape in SCENARIOS[:2]:
        assert np.allclose(shape,0)
    assert EARLY.sum()==LATE.sum()
    assert PAIR_COUNT==41 and SITES==82
    assert len(TRAIN_IDX)==40 and len(TEST_IDX)==42


def test_same_full_physical_site_support_and_frozen_rng():
    a=synthetic_world(1,1,11)
    b=synthetic_world(1,1,11)
    assert np.array_equal(a,b)
    assert a.shape==(82,2,6)
    assert a.dtype.kind in "iu"
    assert (a>=0).all()
    assert (a[TEST_IDX].sum()>0)


def test_partial_pooling_fitted_on_train_only_not_an_alpha_test():
    counts=synthetic_world(1,1,1)
    weak=partially_pooled_training_fit(counts[TRAIN_IDX],0.2)
    strong=partially_pooled_training_fit(counts[TRAIN_IDX],10.)
    assert len(weak)==len(strong)==6
    assert all(np.isfinite(weak)) and all(np.isfinite(strong))
    assert max(weak)-min(weak)>=0
    assert max(strong)-min(strong)>=0
    with pytest.raises(ValueError):
        partially_pooled_training_fit(counts[TEST_IDX],0.2)
    with pytest.raises(ValueError):
        partially_pooled_training_fit(counts[TRAIN_IDX],-1)


def test_strict_conditional_permutation_preserves_low_information_roster():
    # All-zero sites retained; per-pair branch and bin totals have no
    # exchangeable assignments in a completely empty sample.
    arr=np.zeros((42,2,6),dtype=np.int64)
    out=conditional_permutation_test(arr,np.random.default_rng(1))
    assert out["pvalue"]==1 and not out["rejected"]
    assert out["informative_strata"]==0
    # Two cross-bin single detections within one site have conditional support.
    arr[0,0,0]=1
    arr[0,1,5]=1
    out=conditional_permutation_test(arr,np.random.default_rng(1))
    assert out["informative_strata"]==1
    assert out["permutation_variance_bins"]==2
    assert 0.01<=out["pvalue"]<=1
    assert not out["rejected"]  # only two possible assignments, no 5% rejection


def test_all_six_frozen_scenarios_preflight_reproducible_no_source():
    first=run_panel(PLAN,_test_worlds=2)
    second=run_panel(PLAN,_test_worlds=2)
    assert first==second
    assert len(first["scenarios"])==6
    assert first["worlds_per_scenario"]==2
    assert first["conditional_test_nominal_alpha"]==.05
    assert first["pooled_rule_not_a_formal_alpha_test"]
    assert first["partial_pool_fit_not_a_formal_alpha_test"]
    assert first["no_real_observations_or_uptime_opened"]
    json.dumps(first,allow_nan=False)


def test_frozen_parameters_cannot_be_posthoc_adjusted():
    edited=json.loads(json.dumps(PLAN))
    edited["scenarios"][1]["early_branch_multiplier"]=2
    with pytest.raises(ValueError,match="frozen"):
        run_panel(edited,_test_worlds=1)
