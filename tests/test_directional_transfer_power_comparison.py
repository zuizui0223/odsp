from __future__ import annotations

import json
from pathlib import Path

import pytest

from odsp.directional_transfer_power_comparison import (
    COMPARISON_VERSION,
    _scenario_definitions,
    run_directional_transfer_power_comparison,
)
from odsp.transfer_ceiling_operating_characteristics import GENERATOR_VERSION


ROOT = Path(__file__).resolve().parents[1]


def test_predeclared_directional_power_contract_is_frozen_before_result():
    contract = json.loads(
        (ROOT / "ODSP_DIRECTIONAL_TRANSFER_POWER_COMPARISON_CONTRACT.json").read_text(
            encoding="utf-8"
        )
    )
    assert contract["comparison"]["same_simulated_world_per_method"] is True
    assert contract["comparison"]["same_bootstrap_seed_per_method"] is True
    assert contract["fixed_design"]["simulations_per_scenario"] == 1000
    assert contract["fixed_design"]["bootstrap_draws_per_interval"] == 500
    assert contract["fixed_design"]["reference_generator_version"] == GENERATOR_VERSION
    assert contract["qualification_rules"]["candidate_ceiling_regression_count_across_paired_datasets"] == 0
    assert contract["qualification_rules"]["coarse_truth_overreach_maximum_rate"] < 0.064
    assert contract["qualification_rules"]["weak_positive_power_gain_used_for_qualification"] is False
    assert len(contract["predeclared_scenarios"]) == 6


def test_code_scenarios_match_predeclared_contract():
    contract = json.loads(
        (ROOT / "ODSP_DIRECTIONAL_TRANSFER_POWER_COMPARISON_CONTRACT.json").read_text(
            encoding="utf-8"
        )
    )
    code_ids = [row[0] for row in _scenario_definitions()]
    contract_ids = [row["scenario_id"] for row in contract["predeclared_scenarios"]]
    assert code_ids == contract_ids
    assert COMPARISON_VERSION == "paired_two_sided_vs_one_sided_same_world_v1"


def test_comparison_rejects_underpowered_monte_carlo_panel():
    with pytest.raises(ValueError, match="simulations_per_scenario"):
        run_directional_transfer_power_comparison(simulations_per_scenario=99)


def test_comparison_rejects_too_few_bootstrap_draws():
    with pytest.raises(ValueError, match="bootstrap_draws"):
        run_directional_transfer_power_comparison(bootstrap_draws=499)
