from __future__ import annotations

import json
from pathlib import Path

import pytest

from odsp.independent_positive_lattice_family_calibration import (
    GENERATOR_VERSION,
    run_independent_directional_lattice_family_calibration,
)


CONTRACT = Path("ODSP_INDEPENDENT_DIRECTIONAL_LATTICE_FAMILY_CALIBRATION_CONTRACT.json")


def test_contract_freezes_three_block_twelve_edge_panel():
    payload = json.loads(CONTRACT.read_text(encoding="utf-8"))
    assert payload["contract_id"] == "odsp-independent-directional-lattice-family-calibration-v1"
    assert payload["family_mapping"]["three_information_blocks"] == 12
    assert payload["family_mapping"]["four_information_blocks"] == 32
    fixed = payload["fixed_null_calibration_design"]
    assert fixed == {
        "seed": 20260922,
        "simulations_per_scenario": 1000,
        "bootstrap_draws_per_interval": 500,
        "group_count": 6,
        "contrast_correlation": 0.5,
        "familywise_lower_confidence_level": 0.95,
    }
    scenarios = payload["predeclared_null_scenarios"]
    assert [(row["distribution"], row["blocks_per_group"], row["contrast_count"]) for row in scenarios] == [
        ("normal", 20, 12),
        ("normal", 50, 12),
        ("student_t3", 20, 12),
    ]
    assert payload["acceptance_rule"]["maximum_accepted_rate_at_1000_simulations"] == pytest.approx(
        0.06378404875209022
    )
    assert payload["scientific_boundaries"]["four_or_more_information_block_complete_lattice_qualified"] is False


def test_small_panel_is_deterministic_and_only_targets_twelve_contrasts():
    first = run_independent_directional_lattice_family_calibration(
        seed=1234,
        simulations_per_scenario=100,
        bootstrap_draws=500,
    )
    second = run_independent_directional_lattice_family_calibration(
        seed=1234,
        simulations_per_scenario=100,
        bootstrap_draws=500,
    )
    assert first.as_dict() == second.as_dict()
    assert first.generator_version == GENERATOR_VERSION
    assert len(first.scenarios) == 3
    assert {row.contrast_count for row in first.scenarios} == {12}


def test_rejects_underpowered_simulation_settings():
    with pytest.raises(ValueError, match="simulations_per_scenario"):
        run_independent_directional_lattice_family_calibration(
            simulations_per_scenario=99,
            bootstrap_draws=500,
        )
    with pytest.raises(ValueError, match="bootstrap_draws"):
        run_independent_directional_lattice_family_calibration(
            simulations_per_scenario=100,
            bootstrap_draws=499,
        )
