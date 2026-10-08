from __future__ import annotations

import json
from pathlib import Path

import numpy as np
import pytest

from odsp.training_process_future_refit_success_probability_calibration import (
    COVERAGE_SCENARIOS,
    GENERATOR_VERSION,
    POWER_SCENARIOS,
    _known_probability_world,
    run_future_refit_success_probability_v1_calibration,
)


ROOT = Path(__file__).resolve().parents[1]
CONTRACT = (
    ROOT
    / "ODSP_TRAINING_PROCESS_FUTURE_REFIT_SUCCESS_PROBABILITY_V1_CALIBRATION_CONTRACT.json"
)


def test_frozen_calibration_contract_matches_generator_before_results():
    payload = json.loads(CONTRACT.read_text(encoding="utf-8"))
    assert payload["generator_version"] == GENERATOR_VERSION
    assert payload["seed"] == 20261016
    assert payload["simulations_per_scenario"] == 1000
    assert payload["bootstrap_draws_per_interval"] == 500
    assert payload["group_count"] == 6
    assert payload["contrast_count"] == 2
    assert payload["confidence_budget"] == {
        "overall_alpha": 0.05,
        "validation_alpha": 0.025,
        "process_alpha": 0.025,
    }
    assert [
        (
            row["scenario_id"],
            row["distribution"],
            row["refit_count"],
            row["blocks_per_group"],
            row["p_success"],
        )
        for row in payload["coverage_scenarios"]
    ] == list(COVERAGE_SCENARIOS)
    assert [
        (
            row["scenario_id"],
            row["distribution"],
            row["refit_count"],
            row["blocks_per_group"],
        )
        for row in payload["strong_signal_power_scenarios"]
    ] == list(POWER_SCENARIOS)
    assert payload["coverage_acceptance"]["maximum_accepted_rate"] == pytest.approx(
        0.06378404875209022
    )
    assert payload["validation_stage_acceptance"][
        "maximum_accepted_rate"
    ] == pytest.approx(0.03487420882906575)
    assert payload["power_acceptance"]["minimum_accepted_rate"] == 0.80
    assert payload["prequalification_history"]["results_observed_before_this_freeze"] is False
    assert payload["prequalification_history"]["thresholds_tuned_to_results"] is False


def test_known_probability_world_has_exact_boundary_failure_definition():
    rng = np.random.default_rng(991)
    world, success, true_mean = _known_probability_world(
        rng,
        refit_count=20,
        blocks_per_group=8,
        group_count=6,
        contrast_count=2,
        p_success=0.0,
        positive_shift_oracle_se=6.0,
        training_cross_refit_validation_noise_correlation=0.35,
        contrast_correlation=0.5,
        distribution="normal",
    )
    assert world.shape == (20, 6, 8, 2)
    assert success.shape == (20,)
    assert not np.any(success)
    assert np.isfinite(world).all()
    assert true_mean.shape == (20, 6, 2)
    assert np.all(np.sum(true_mean == 0.0, axis=(1, 2)) == 1)
    assert np.all(np.sum(true_mean > 0.0, axis=(1, 2)) == 11)


def test_known_probability_world_p_one_has_all_true_success_indicators():
    world, success, true_mean = _known_probability_world(
        np.random.default_rng(17),
        refit_count=8,
        blocks_per_group=20,
        group_count=6,
        contrast_count=2,
        p_success=1.0,
        positive_shift_oracle_se=8.0,
        training_cross_refit_validation_noise_correlation=0.35,
        contrast_correlation=0.5,
        distribution="student_t3",
    )
    assert world.shape == (8, 6, 20, 2)
    assert np.all(success)
    assert np.isfinite(world).all()
    assert np.all(true_mean > 0.0)


def test_generator_is_reproducible_for_same_rng_seed():
    kwargs = dict(
        refit_count=8,
        blocks_per_group=8,
        group_count=6,
        contrast_count=2,
        p_success=0.8,
        positive_shift_oracle_se=6.0,
        training_cross_refit_validation_noise_correlation=0.35,
        contrast_correlation=0.5,
        distribution="normal",
    )
    first_world, first_success, first_mean = _known_probability_world(
        np.random.default_rng(44), **kwargs
    )
    second_world, second_success, second_mean = _known_probability_world(
        np.random.default_rng(44), **kwargs
    )
    assert np.array_equal(first_world, second_world)
    assert np.array_equal(first_success, second_success)
    assert np.array_equal(first_mean, second_mean)


def test_calibration_runner_rejects_postfreeze_scope_changes():
    with pytest.raises(ValueError, match="simulations_per_scenario"):
        run_future_refit_success_probability_v1_calibration(
            simulations_per_scenario=99
        )
    with pytest.raises(ValueError, match="bootstrap_draws"):
        run_future_refit_success_probability_v1_calibration(
            bootstrap_draws=499
        )
    with pytest.raises(ValueError, match="group_count"):
        run_future_refit_success_probability_v1_calibration(group_count=5)
    with pytest.raises(ValueError, match="contrast_count"):
        run_future_refit_success_probability_v1_calibration(contrast_count=4)
    with pytest.raises(ValueError, match="total alpha"):
        run_future_refit_success_probability_v1_calibration(
            validation_alpha=0.02,
            process_alpha=0.02,
        )
    with pytest.raises(ValueError, match="6-oracle-SE"):
        run_future_refit_success_probability_v1_calibration(
            coverage_positive_shift_oracle_se=5.0
        )
    with pytest.raises(ValueError, match="8-oracle-SE"):
        run_future_refit_success_probability_v1_calibration(
            power_positive_shift_oracle_se=7.0
        )
    with pytest.raises(ValueError, match="0.80"):
        run_future_refit_success_probability_v1_calibration(
            minimum_accepted_power=0.79
        )
