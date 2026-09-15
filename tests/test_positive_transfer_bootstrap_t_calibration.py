from __future__ import annotations

import json
from pathlib import Path

import pytest

from odsp.positive_transfer_bootstrap_t_calibration import (
    GENERATOR_VERSION,
    run_positive_transfer_null_calibration,
)


ROOT = Path(__file__).resolve().parents[1]


def test_small_null_calibration_is_reproducible_and_spans_family_sizes():
    first = run_positive_transfer_null_calibration(
        simulations_per_scenario=100,
        bootstrap_draws=500,
        group_count=3,
    )
    second = run_positive_transfer_null_calibration(
        simulations_per_scenario=100,
        bootstrap_draws=500,
        group_count=3,
    )
    assert first.as_dict() == second.as_dict()
    assert first.generator_version == GENERATOR_VERSION
    assert len(first.scenarios) == 5
    assert {row.contrast_count for row in first.scenarios} == {2, 4}
    assert {row.blocks_per_group for row in first.scenarios} == {8, 20, 50}
    assert all(
        0.0 <= row.one_sided_familywise_false_positive_rate <= 1.0
        for row in first.scenarios
    )


def test_contract_freezes_null_gate_before_power_comparison():
    contract = json.loads(
        (ROOT / "ODSP_ONE_SIDED_POSITIVE_BOOTSTRAP_T_CONTRACT.json").read_text(
            encoding="utf-8"
        )
    )
    assert contract["alternative"] == "greater"
    assert contract["acceptance_rule"]["frozen_before_first_1000_simulation_result"] is True
    assert contract["acceptance_rule"]["maximum_accepted_rate_at_1000_simulations"] < 0.064
    assert contract["version_boundary"]["replaces_two_sided_v2"] is False
    assert contract["version_boundary"]["valid_only_for_predeclared_directional_positive_claim"] is True
    assert contract["scientific_boundaries"]["power_advantage_may_be_assessed_only_after_null_qualification"] is True


def test_null_calibration_rejects_invalid_arguments():
    with pytest.raises(ValueError, match="simulations_per_scenario"):
        run_positive_transfer_null_calibration(simulations_per_scenario=99)
    with pytest.raises(ValueError, match="bootstrap_draws"):
        run_positive_transfer_null_calibration(bootstrap_draws=499)
    with pytest.raises(ValueError, match="group_count"):
        run_positive_transfer_null_calibration(group_count=1)
    with pytest.raises(ValueError, match="contrast_correlation"):
        run_positive_transfer_null_calibration(contrast_correlation=1.0)
