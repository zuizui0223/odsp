from __future__ import annotations

import json
from pathlib import Path

from odsp.paired_directional_power_comparison import COMPARISON_VERSION


def test_paired_directional_power_receipt_matches_contract():
    contract = json.loads(
        Path("ODSP_PAIRED_DIRECTIONAL_POWER_COMPARISON_CONTRACT.json").read_text()
    )
    receipt = json.loads(
        Path("PAIRED_DIRECTIONAL_POWER_COMPARISON_RECEIPT.json").read_text()
    )
    assert receipt["comparison_version"] == COMPARISON_VERSION
    run = receipt["first_1000_simulation_run"]
    design = contract["fixed_design"]
    for field in (
        "seed", "simulations_per_scenario", "bootstrap_draws_per_interval",
        "group_count", "group_correlation", "step_correlation",
        "noise_standard_deviation", "familywise_confidence_level",
        "same_world_per_method", "same_shared_block_bootstrap_seed_per_method",
    ):
        assert run[field] == design[field]
    rules = contract["qualification_rules"]
    assert receipt["qualification_rule"]["coarse_truth_one_sided_overreach_maximum"] == rules["coarse_truth_one_sided_overreach_maximum"]
    assert receipt["summary"]["qualification_pass"] is True
    assert receipt["summary"]["total_paired_dataset_ceiling_regressions"] == 0
    assert receipt["summary"]["total_paired_dataset_ceiling_advances"] == 227
    limit = rules["coarse_truth_one_sided_overreach_maximum"]
    for row in receipt["scenarios"]:
        assert row["paired_dataset_ceiling_regression_count"] == 0
        assert row["candidate_acceptance_pass"] is True
        if row["truth_ceiling"] == "coarse":
            assert row["one_sided_overreach_rate"] <= limit
