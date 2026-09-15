from __future__ import annotations

import json
from pathlib import Path

from odsp.shared_block_positive_multicontrast_calibration import (
    GENERATOR_VERSION,
    run_paired_directional_family_calibration,
)


def test_small_paired_multicontrast_panel_is_deterministic():
    first = run_paired_directional_family_calibration(
        simulations_per_scenario=100,
        bootstrap_draws=500,
    )
    second = run_paired_directional_family_calibration(
        simulations_per_scenario=100,
        bootstrap_draws=500,
    )
    assert first.as_dict() == second.as_dict()
    assert first.generator_version == GENERATOR_VERSION
    assert {row.contrast_count for row in first.scenarios} == {4, 12}
    assert len(first.scenarios) == 6


def test_lattice_family_contract_maps_two_and_three_blocks_to_edge_counts():
    contract = json.loads(
        Path("ODSP_PAIRED_DIRECTIONAL_LATTICE_FAMILY_CALIBRATION_CONTRACT.json").read_text()
    )
    mapping = contract["family_mapping"]
    assert mapping["two_information_blocks"] == 4
    assert mapping["three_information_blocks"] == 12
    assert mapping["four_information_blocks"] == 32
    assert contract["acceptance_rule"]["maximum_accepted_rate_at_1000_simulations"] == 0.06378404875209022
    assert contract["acceptance_rule"]["frozen_before_first_1000_simulation_result"] is True
    boundary = contract["scientific_boundaries"]
    assert boundary["two_information_block_complete_lattice_targeted"] is True
    assert boundary["three_information_block_complete_lattice_targeted"] is True
    assert boundary["four_or_more_information_block_complete_lattice_qualified"] is False
