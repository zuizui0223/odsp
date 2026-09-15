from __future__ import annotations

import json
from pathlib import Path

from odsp.shared_block_positive_calibration import (
    GENERATOR_VERSION,
    run_paired_positive_null_calibration,
)


def test_small_paired_one_sided_calibration_runs_and_is_deterministic():
    first = run_paired_positive_null_calibration(
        simulations_per_scenario=100,
        bootstrap_draws=500,
    )
    second = run_paired_positive_null_calibration(
        simulations_per_scenario=100,
        bootstrap_draws=500,
    )
    assert first.as_dict() == second.as_dict()
    assert first.generator_version == GENERATOR_VERSION
    assert len(first.scenarios) == 4
    assert all(0.0 <= row.one_sided_familywise_false_positive_rate <= 1.0 for row in first.scenarios)


def test_paired_one_sided_contract_is_frozen_before_first_full_result():
    contract = json.loads(
        Path("ODSP_PAIRED_ONE_SIDED_POSITIVE_BOOTSTRAP_T_CONTRACT.json").read_text()
    )
    design = contract["fixed_null_calibration_design"]
    assert contract["alternative"] == "greater"
    assert design["simulations_per_scenario"] == 1000
    assert design["bootstrap_draws_per_interval"] == 500
    assert design["group_count"] == 6
    assert design["contrast_count"] == 2
    assert design["group_correlation"] == 0.7
    assert design["contrast_correlation"] == 0.5
    assert contract["acceptance_rule"]["maximum_accepted_rate_at_1000_simulations"] == 0.06378404875209022
    assert contract["acceptance_rule"]["frozen_before_first_1000_simulation_result"] is True
    boundary = contract["scientific_boundaries"]
    assert boundary["validation_group_independence_assumed"] is False
    assert boundary["same_block_draw_shared_across_all_groups_and_contrasts"] is True
    assert boundary["power_advantage_may_be_assessed_only_after_null_qualification"] is True
