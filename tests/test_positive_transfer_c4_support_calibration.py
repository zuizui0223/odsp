from __future__ import annotations

import json
from pathlib import Path

from odsp.positive_transfer_c4_support_calibration import (
    GENERATOR_VERSION,
    run_independent_c4_support_envelope_calibration,
)


CONTRACT = Path("ODSP_INDEPENDENT_C4_ONE_SIDED_SUPPORT_ENVELOPE_CONTRACT.json")


def test_contract_freezes_support_envelope_before_formal_result():
    payload = json.loads(CONTRACT.read_text(encoding="utf-8"))
    assert payload["schema_version"] == 1
    assert payload["contract_id"] == "odsp-independent-c4-one-sided-support-envelope-v1"
    assert payload["generator_version"] == GENERATOR_VERSION
    assert payload["fixed_design"]["simulations_per_scenario"] == 1000
    assert payload["fixed_design"]["bootstrap_draws_per_interval"] == 500
    assert payload["fixed_design"]["contrast_count"] == 4
    assert payload["qualification_if_pass"]["support_anchor_counts"] == [8, 20, 50]
    assert payload["qualification_if_pass"]["arbitrary_intermediate_or_larger_block_count_proven"] is False
    assert payload["acceptance_rule"]["frozen_before_first_1000_simulation_result"] is True


def test_support_envelope_scenarios_are_exactly_predeclared():
    result = run_independent_c4_support_envelope_calibration(
        simulations_per_scenario=100,
        bootstrap_draws=500,
    )
    observed = {
        (row.distribution, row.blocks_per_group, row.contrast_count)
        for row in result.scenarios
    }
    assert observed == {
        ("normal", 8, 4),
        ("normal", 20, 4),
        ("normal", 50, 4),
        ("student_t3", 8, 4),
        ("student_t3", 20, 4),
        ("student_t3", 50, 4),
    }


def test_support_envelope_is_seed_deterministic():
    first = run_independent_c4_support_envelope_calibration(
        seed=12345,
        simulations_per_scenario=100,
        bootstrap_draws=500,
    )
    second = run_independent_c4_support_envelope_calibration(
        seed=12345,
        simulations_per_scenario=100,
        bootstrap_draws=500,
    )
    assert first.as_dict() == second.as_dict()


def test_support_envelope_acceptance_threshold_uses_same_familywise_rule():
    result = run_independent_c4_support_envelope_calibration(
        simulations_per_scenario=100,
        bootstrap_draws=500,
    )
    assert result.contrast_count == 4
    assert result.support_anchor_counts == (8, 20, 50)
    assert all(row.maximum_accepted_rate == result.maximum_accepted_rate for row in result.scenarios)
    assert all(row.terminal_false_generalizing_rate >= 0.0 for row in result.scenarios)
