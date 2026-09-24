from __future__ import annotations

import copy
from pathlib import Path

import numpy as np
import pytest

from odsp.n2_failure_mode_stage1 import (
    FROZEN_CONTRACT_MERGE_SHA,
    Stage1Scenario,
    _group_folds,
    _population_interval,
    bop_oracle_check,
    derive_seed,
    group_layer_indices,
    layer_scores,
    load_stage1_contract,
    oracle_information_targets,
    run_factorial_cells,
    run_world,
    scenario_grid,
)


ROOT = Path(__file__).resolve().parents[1]
CONTRACT = ROOT / "N2_STRATIFIED_CONTEXT_TRANSFER_FAILURE_MODE_STAGE1_CONTRACT.json"


def _contract() -> dict[str, object]:
    return load_stage1_contract(CONTRACT)


def test_stage1_engine_is_bound_to_merged_frozen_contract():
    assert FROZEN_CONTRACT_MERGE_SHA == "05609e5a9fe4200d9cd7a1f46c807f9f682b1c72"
    contract = _contract()
    assert contract["status"] == "pre_result_frozen"
    assert len(scenario_grid(contract)) == 864


def test_layer_scores_and_group_allocation_reproduce_bop_oracle():
    z = layer_scores(4)
    assert float(np.mean(z)) == pytest.approx(0.0, abs=1e-15)
    assert float(np.mean(z * z)) == pytest.approx(1.0, abs=1e-15)
    layer = group_layer_indices(30, 4)
    assert np.bincount(layer).tolist() == [8, 8, 7, 7]

    check = bop_oracle_check(_contract())
    assert check["passed"] is True
    assert check["observed_layer_gain"] == pytest.approx(
        0.2664659336361246, abs=1e-12
    )


def test_group_cv_fold_assignment_is_layer_stratified_and_no_group_is_split():
    layer = group_layer_indices(12, 4)
    folds = _group_folds(layer, 5)
    assert folds.shape == (12,)
    assert set(folds.tolist()) == {0, 1, 2, 3, 4}
    for layer_id in range(4):
        local = folds[layer == layer_id]
        assert len(set(local.tolist())) == 3

    smallest = group_layer_indices(5, 2)
    smallest_folds = _group_folds(smallest, 5)
    assert set(smallest_folds.tolist()) == {0, 1, 2, 3, 4}


def test_oracle_context_gain_is_zero_at_null_and_positive_when_context_matters():
    null = Stage1Scenario(2.0, 0.0, 30, 100, 4, "rho_0.7", "included")
    positive = Stage1Scenario(2.0, 0.5, 30, 100, 4, "rho_0.7", "included")
    contract = _contract()
    kwargs = {
        "intercept": contract["data_generating_process"]["intercept"],
        "rho_correlated": contract["data_generating_process"]["context_generation"][
            "rho_when_correlated"
        ],
    }
    null_target = oracle_information_targets(null, **kwargs)
    positive_target = oracle_information_targets(positive, **kwargs)
    assert null_target["context_gain"] == pytest.approx(0.0, abs=1e-14)
    assert positive_target["context_gain"] > 0.0


def test_population_interval_switches_to_student_t_below_ten_groups():
    small = _population_interval(
        [0.1, 0.2, 0.3, 0.4, 0.5],
        confidence_level=0.95,
        bootstrap_draws=500,
        seed=1,
        switch_threshold=10,
    )
    large = _population_interval(
        np.linspace(0.1, 0.5, 12),
        confidence_level=0.95,
        bootstrap_draws=500,
        seed=1,
        switch_threshold=10,
    )
    assert small.method == "student_t_df_4"
    assert large.method == "group_percentile_bootstrap_500"


def test_seed_derivation_is_deterministic_and_namespace_separated():
    a = derive_seed(20260922, "factorial:0", 0)
    b = derive_seed(20260922, "factorial:0", 0)
    c = derive_seed(20260922, "anchor:A", 0)
    assert a == b
    assert a != c


def test_one_world_preserves_additive_score_identity():
    contract = _contract()
    scenario = Stage1Scenario(1.0, 0.25, 12, 100, 4, "rho_0.7", "included")
    result = run_world(
        scenario,
        seed=123456,
        contract=contract,
        bootstrap_draws=100,
    )
    assert result["group_cv_available"] is True
    assert result["group_cv_identity_error"] <= 1e-12
    assert "group_cv_pooled_log_gain" in result
    assert "group_cv_layer_decomposed_context_gain" in result


def test_tiny_factorial_fixture_runs_without_opening_frozen_execution():
    contract = copy.deepcopy(_contract())
    contract["factorial_design"]["replicates_per_factorial_cell"] = 2
    contract["factorial_design"]["population_interval_bootstrap_draws_per_world"] = 20
    result = run_factorial_cells(contract, cell_indices=[0])
    assert result["result_role"] == "descriptive_factorial_shard"
    assert result["contract_merge_sha"] == FROZEN_CONTRACT_MERGE_SHA
    assert result["cell_count"] == 1
    assert result["cells"][0]["cell_index"] == 0
    assert result["cells"][0]["group_cv_pooled_log_gain"]["planned_replicates"] == 2
