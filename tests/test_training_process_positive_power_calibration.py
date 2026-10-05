from __future__ import annotations

import json
from pathlib import Path

import numpy as np
import pytest

from odsp.training_process_positive_calibration import (
    _crossed_null_world,
    _flatten_world,
)
from odsp.training_process_positive_power_calibration import (
    GENERATOR_VERSION,
    _oracle_cell_standard_error,
    run_training_process_positive_power_calibration,
)
from odsp.training_process_positive_transfer import (
    certify_training_process_positive_transfer_v1,
)


ROOT = Path(__file__).resolve().parents[1]
CONTRACT = ROOT / "ODSP_TRAINING_PROCESS_POSITIVE_POWER_CALIBRATION_CONTRACT.json"
PROCESS_SHA = "0" * 64


def test_power_contract_is_frozen_before_first_power_run():
    payload = json.loads(CONTRACT.read_text(encoding="utf-8"))
    assert payload["generator"]["generator_version"] == GENERATOR_VERSION
    assert payload["standardized_alternatives"]["moderate_shift_standard_errors"] == 3.0
    assert payload["standardized_alternatives"]["strong_shift_standard_errors"] == 5.0
    assert payload["acceptance_rule"]["minimum_strong_terminal_power"] == 0.8
    assert payload["prequalification_history"]["power_results_observed_before_this_freeze"] is False
    assert payload["prequalification_history"]["threshold_tuned_to_power_results"] is False


def test_oracle_standard_error_matches_crossed_random_effect_formula():
    normal = _oracle_cell_standard_error(
        distribution="normal",
        refit_count=8,
        blocks_per_group=20,
        training_sd=0.8,
        validation_sd=0.2,
        interaction_sd=0.5,
    )
    expected = np.sqrt(0.8**2 / 8 + 0.2**2 / 20 + 0.5**2 / (8 * 20))
    assert normal == pytest.approx(expected)

    heavy = _oracle_cell_standard_error(
        distribution="student_t3",
        refit_count=8,
        blocks_per_group=20,
        training_sd=0.5,
        validation_sd=0.5,
        interaction_sd=0.5,
    )
    expected_heavy = np.sqrt(
        3.0 * (0.5**2 / 8 + 0.5**2 / 20 + 0.5**2 / (8 * 20))
    )
    assert heavy == pytest.approx(expected_heavy)


def test_process_bootstrap_is_exactly_translation_invariant_for_common_shift():
    rng = np.random.default_rng(44)
    world = _crossed_null_world(
        rng,
        refit_count=8,
        blocks_per_group=8,
        group_count=2,
        contrast_count=2,
        training_sd=0.5,
        validation_sd=0.5,
        interaction_sd=0.5,
        training_cross_cell_correlation=0.35,
        contrast_correlation=0.5,
        distribution="normal",
    )
    gains, groups, blocks = _flatten_world(world)
    ids = tuple(f"r{i}" for i in range(8))
    settings = dict(
        blocks=blocks,
        refit_ids=ids,
        training_process_id="translation-test",
        training_process_manifest_sha256=PROCESS_SHA,
        contrast_names=("a", "b"),
        bootstrap_draws=500,
        seed=777,
        minimum_refits=8,
        minimum_blocks_per_group=8,
    )
    base = certify_training_process_positive_transfer_v1(
        gains,
        groups,
        **settings,
    )
    shift = 0.73
    moved = certify_training_process_positive_transfer_v1(
        gains + shift,
        groups,
        **settings,
    )
    assert moved.bootstrap_t_critical_value == pytest.approx(
        base.bootstrap_t_critical_value, abs=1e-12
    )
    for left_contrast, right_contrast in zip(base.contrasts, moved.contrasts):
        for left, right in zip(left_contrast.groups, right_contrast.groups):
            assert right.crossed_studentizing_standard_error == pytest.approx(
                left.crossed_studentizing_standard_error, abs=1e-12
            )
            assert right.lower_bound == pytest.approx(
                left.lower_bound + shift, abs=1e-12
            )


def test_power_calibration_rejects_out_of_scope_settings_before_simulation():
    with pytest.raises(ValueError, match="simulations_per_scenario"):
        run_training_process_positive_power_calibration(simulations_per_scenario=99)
    with pytest.raises(ValueError, match="bootstrap_draws"):
        run_training_process_positive_power_calibration(bootstrap_draws=499)
    with pytest.raises(ValueError, match="contrast_count"):
        run_training_process_positive_power_calibration(contrast_count=4)
    with pytest.raises(ValueError, match="standardized shifts"):
        run_training_process_positive_power_calibration(
            moderate_standardized_shift=5.0,
            strong_standardized_shift=3.0,
        )
