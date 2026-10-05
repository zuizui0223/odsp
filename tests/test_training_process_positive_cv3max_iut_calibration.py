from __future__ import annotations

import json
from pathlib import Path

import pytest

from odsp.training_process_positive_cv3max_iut_calibration import (
    NULL_GENERATOR_VERSION,
    POWER_GENERATOR_VERSION,
    run_training_process_positive_cv3max_iut_v4_null_calibration,
    run_training_process_positive_cv3max_iut_v4_power_calibration,
)


ROOT = Path(__file__).resolve().parents[1]
NULL_CONTRACT = ROOT / "ODSP_TRAINING_PROCESS_POSITIVE_CV3MAX_IUT_V4_NULL_CALIBRATION_CONTRACT.json"
POWER_CONTRACT = ROOT / "ODSP_TRAINING_PROCESS_POSITIVE_CV3MAX_IUT_V4_POWER_CALIBRATION_CONTRACT.json"


def test_v4_contracts_match_generators_and_are_pre_result():
    null = json.loads(NULL_CONTRACT.read_text(encoding="utf-8"))
    power = json.loads(POWER_CONTRACT.read_text(encoding="utf-8"))
    assert null["generator_version"] == NULL_GENERATOR_VERSION
    assert power["generator_version"] == POWER_GENERATOR_VERSION
    assert null["prequalification_history"]["v4_null_results_observed_before_this_freeze"] is False
    assert power["prequalification_history"]["v4_power_results_observed_before_this_freeze"] is False
    assert null["acceptance_rule"]["maximum_accepted_component_rate"] == pytest.approx(
        0.06378404875209022
    )
    assert power["acceptance_rule"]["minimum_strong_terminal_power"] == 0.8


def test_v4_panels_reject_out_of_scope_settings():
    with pytest.raises(ValueError, match="simulations_per_scenario"):
        run_training_process_positive_cv3max_iut_v4_null_calibration(
            simulations_per_scenario=99
        )
    with pytest.raises(ValueError, match="contrast_count"):
        run_training_process_positive_cv3max_iut_v4_null_calibration(
            contrast_count=4
        )
    with pytest.raises(ValueError, match="standardized shifts"):
        run_training_process_positive_cv3max_iut_v4_power_calibration(
            moderate_standardized_shift=5,
            strong_standardized_shift=3,
        )
