from __future__ import annotations

import json
from pathlib import Path

from odsp.independent_c12_support_calibration import (
    GENERATOR_VERSION,
    run_independent_c12_support_envelope_calibration,
)


CONTRACT = Path("ODSP_INDEPENDENT_C12_ONE_SIDED_SUPPORT_ENVELOPE_CONTRACT.json")


def test_contract_freezes_c12_support_envelope_before_formal_result():
    payload = json.loads(CONTRACT.read_text(encoding="utf-8"))
    assert payload["schema_version"] == 1
    assert payload["contract_id"] == "odsp-independent-c12-one-sided-support-envelope-v1"
    assert payload["generator_version"] == GENERATOR_VERSION
    assert payload["fixed_design"]["seed"] == 20261003
    assert payload["fixed_design"]["simulations_per_scenario"] == 1000
    assert payload["fixed_design"]["bootstrap_draws_per_interval"] == 500
    assert payload["fixed_design"]["group_count"] == 6
    assert payload["fixed_design"]["contrast_count"] == 12
    assert payload["qualification_if_pass"]["support_anchor_counts"] == [8, 20, 50]
    assert payload["qualification_if_pass"]["group_count_anchor"] == 6
    assert payload["qualification_if_pass"]["arbitrary_intermediate_or_larger_block_count_proven"] is False
    assert payload["qualification_if_pass"]["arbitrary_group_count_proven"] is False
    assert payload["acceptance_rule"]["frozen_before_first_1000_simulation_result"] is True


def test_c12_support_envelope_scenarios_are_exactly_predeclared():
    result = run_independent_c12_support_envelope_calibration(
        simulations_per_scenario=100,
        bootstrap_draws=500,
    )
    observed = {
        (row.distribution, row.blocks_per_group, row.contrast_count)
        for row in result.scenarios
    }
    assert observed == {
        ("normal", 8, 12),
        ("normal", 20, 12),
        ("normal", 50, 12),
        ("student_t3", 8, 12),
        ("student_t3", 20, 12),
        ("student_t3", 50, 12),
    }


def test_c12_support_envelope_is_seed_deterministic():
    first = run_independent_c12_support_envelope_calibration(
        seed=12345,
        simulations_per_scenario=100,
        bootstrap_draws=500,
    )
    second = run_independent_c12_support_envelope_calibration(
        seed=12345,
        simulations_per_scenario=100,
        bootstrap_draws=500,
    )
    assert first.as_dict() == second.as_dict()


def test_c12_support_envelope_uses_same_familywise_gate():
    result = run_independent_c12_support_envelope_calibration(
        simulations_per_scenario=100,
        bootstrap_draws=500,
    )
    assert result.contrast_count == 12
    assert result.group_count == 6
    assert result.support_anchor_counts == (8, 20, 50)
    assert all(
        row.maximum_accepted_rate == result.maximum_accepted_rate
        for row in result.scenarios
    )
