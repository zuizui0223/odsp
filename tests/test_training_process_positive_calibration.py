from __future__ import annotations

import json
from pathlib import Path

import numpy as np
import pytest

from odsp.training_process_positive_calibration import (
    GENERATOR_VERSION,
    SCENARIOS,
    _crossed_null_world,
    _flatten_world,
    run_training_process_positive_null_calibration,
)


ROOT = Path(__file__).resolve().parents[1]
CONTRACT = ROOT / "ODSP_TRAINING_PROCESS_POSITIVE_NULL_CALIBRATION_CONTRACT.json"


def test_known_null_generator_is_reproducible_and_crossed():
    first_rng = np.random.default_rng(123)
    second_rng = np.random.default_rng(123)
    first = _crossed_null_world(
        first_rng,
        refit_count=8,
        blocks_per_group=8,
        group_count=3,
        contrast_count=2,
        training_sd=0.5,
        validation_sd=0.5,
        interaction_sd=0.5,
        training_cross_cell_correlation=0.35,
        contrast_correlation=0.5,
        distribution="normal",
    )
    second = _crossed_null_world(
        second_rng,
        refit_count=8,
        blocks_per_group=8,
        group_count=3,
        contrast_count=2,
        training_sd=0.5,
        validation_sd=0.5,
        interaction_sd=0.5,
        training_cross_cell_correlation=0.35,
        contrast_correlation=0.5,
        distribution="normal",
    )
    assert first.shape == (8, 3, 8, 2)
    assert np.array_equal(first, second)

    gains, groups, blocks = _flatten_world(first)
    assert gains.shape == (8, 24, 2)
    assert len(groups) == len(blocks) == 24
    assert len(set(groups)) == 3
    assert len(set(blocks)) == 24


def test_calibration_contract_matches_generator_scenarios():
    payload = json.loads(CONTRACT.read_text(encoding="utf-8"))
    assert payload["generator"]["generator_version"] == GENERATOR_VERSION
    assert payload["generator"]["contrast_count"] == 2
    assert len(payload["scenarios"]) == len(SCENARIOS) == 6
    assert [row["scenario_id"] for row in payload["scenarios"]] == [
        row[0] for row in SCENARIOS
    ]
    assert payload["qualification_run"]["simulations_per_scenario"] == 1000
    assert payload["qualification_run"]["bootstrap_draws_per_interval"] == 500
    assert payload["acceptance_rule"]["every_scenario_must_pass"] is True


def test_calibration_freeze_is_honest_about_prequalification_exploration():
    payload = json.loads(CONTRACT.read_text(encoding="utf-8"))
    history = payload["prequalification_history"]
    assert history["small_exploratory_diagnostic_simulations_occurred_before_this_freeze"] is True
    assert history["exploratory_results_are_qualification_evidence"] is False
    assert history["acceptance_threshold_was_tuned_to_exploratory_results"] is False
    assert history["first_1000_simulation_qualification_run_must_occur_after_this_contract"] is True


def test_calibration_rejects_out_of_scope_or_underpowered_settings_before_simulation():
    with pytest.raises(ValueError, match="simulations_per_scenario"):
        run_training_process_positive_null_calibration(
            simulations_per_scenario=99
        )
    with pytest.raises(ValueError, match="bootstrap_draws"):
        run_training_process_positive_null_calibration(
            bootstrap_draws=499
        )
    with pytest.raises(ValueError, match="contrast_count"):
        run_training_process_positive_null_calibration(
            contrast_count=4
        )
    with pytest.raises(ValueError, match="group_count"):
        run_training_process_positive_null_calibration(
            group_count=1
        )
