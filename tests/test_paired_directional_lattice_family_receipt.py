from __future__ import annotations

import json
from pathlib import Path

from odsp.shared_block_positive_multicontrast_calibration import GENERATOR_VERSION


def test_paired_lattice_family_receipt_matches_contract():
    contract = json.loads(
        Path("ODSP_PAIRED_DIRECTIONAL_LATTICE_FAMILY_CALIBRATION_CONTRACT.json").read_text()
    )
    receipt = json.loads(
        Path("PAIRED_DIRECTIONAL_LATTICE_FAMILY_CALIBRATION_RECEIPT.json").read_text()
    )
    assert receipt["generator_version"] == GENERATOR_VERSION
    run = receipt["first_1000_simulation_run"]
    design = contract["fixed_null_calibration_design"]
    for field in (
        "seed", "simulations_per_scenario", "bootstrap_draws_per_interval",
        "group_count", "group_correlation", "contrast_correlation",
        "familywise_lower_confidence_level",
    ):
        assert run[field] == design[field]
    limit = contract["acceptance_rule"]["maximum_accepted_rate_at_1000_simulations"]
    assert receipt["acceptance_rule"]["maximum_accepted_rate_at_1000_simulations"] == limit
    assert receipt["summary"]["qualification_pass"] is True
    assert receipt["summary"]["two_information_block_complete_lattice_qualified"] is True
    assert receipt["summary"]["three_information_block_complete_lattice_qualified"] is True
    assert receipt["summary"]["four_or_more_information_block_complete_lattice_qualified"] is False
    assert set(receipt["scientific_boundary"]["qualified_edge_family_sizes"]) == {4, 12}
    assert receipt["scientific_boundary"]["unqualified_next_edge_family_size"] == 32
    assert all(row["one_sided_familywise_false_positive_rate"] <= limit for row in receipt["scenarios"])
