from __future__ import annotations

import json
from pathlib import Path

from odsp.paired_directional_power_comparison import (
    COMPARISON_VERSION,
    run_paired_directional_power_comparison,
)


def test_paired_directional_power_contract_is_frozen_before_outcome():
    contract = json.loads(
        Path("ODSP_PAIRED_DIRECTIONAL_POWER_COMPARISON_CONTRACT.json").read_text()
    )
    design = contract["fixed_design"]
    rules = contract["qualification_rules"]
    assert design["simulations_per_scenario"] == 1000
    assert design["bootstrap_draws_per_interval"] == 500
    assert design["group_count"] == 6
    assert design["group_correlation"] == 0.7
    assert design["step_correlation"] == 0.4
    assert design["same_world_per_method"] is True
    assert design["same_shared_block_bootstrap_seed_per_method"] is True
    assert rules["paired_dataset_ceiling_regression_count"] == 0
    assert rules["coarse_truth_one_sided_overreach_maximum"] == 0.06378404875209022
    assert rules["power_gain_used_for_qualification"] is False
    assert rules["frozen_before_first_1000_simulation_result"] is True


def test_small_paired_directional_comparison_is_deterministic_and_no_regression():
    first = run_paired_directional_power_comparison(
        simulations_per_scenario=100,
        bootstrap_draws=500,
    )
    second = run_paired_directional_power_comparison(
        simulations_per_scenario=100,
        bootstrap_draws=500,
    )
    assert first.as_dict() == second.as_dict()
    assert first.comparison_version == COMPARISON_VERSION
    assert first.same_world_per_method is True
    assert first.same_shared_block_bootstrap_seed_per_method is True
    assert all(row.paired_dataset_ceiling_regression_count == 0 for row in first.scenarios)
