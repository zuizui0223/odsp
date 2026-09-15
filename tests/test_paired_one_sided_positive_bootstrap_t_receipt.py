from __future__ import annotations

import json
from pathlib import Path

from odsp.shared_block_positive_calibration import GENERATOR_VERSION


def test_paired_one_sided_receipt_matches_frozen_contract_boundary():
    contract = json.loads(
        Path("ODSP_PAIRED_ONE_SIDED_POSITIVE_BOOTSTRAP_T_CONTRACT.json").read_text()
    )
    receipt = json.loads(
        Path("PAIRED_ONE_SIDED_POSITIVE_BOOTSTRAP_T_NULL_CALIBRATION_RECEIPT.json").read_text()
    )
    run = receipt["first_1000_simulation_run"]
    design = contract["fixed_null_calibration_design"]
    assert receipt["generator_version"] == GENERATOR_VERSION
    assert run["seed"] == design["seed"]
    assert run["simulations_per_scenario"] == design["simulations_per_scenario"]
    assert run["bootstrap_draws_per_interval"] == design["bootstrap_draws_per_interval"]
    assert run["group_count"] == design["group_count"]
    assert run["contrast_count"] == design["contrast_count"]
    assert run["group_correlation"] == design["group_correlation"]
    assert run["contrast_correlation"] == design["contrast_correlation"]
    assert run["familywise_lower_confidence_level"] == design["familywise_lower_confidence_level"]
    frozen_limit = contract["acceptance_rule"]["maximum_accepted_rate_at_1000_simulations"]
    assert receipt["acceptance_rule"]["maximum_accepted_rate_at_1000_simulations"] == frozen_limit
    assert receipt["summary"]["qualification_pass"] is True
    assert receipt["summary"]["lattice_four_edge_family_qualified_by_this_receipt"] is False
    assert all(
        row["one_sided_familywise_false_positive_rate"] <= frozen_limit
        for row in receipt["scenarios"]
    )
