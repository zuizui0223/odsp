from __future__ import annotations

import json
from pathlib import Path

import numpy as np
import pytest

from odsp.training_process_positive_pigeonhole_iut_calibration import (
    NULL_GENERATOR_VERSION,
    POWER_GENERATOR_VERSION,
    run_training_process_positive_pigeonhole_iut_v3_null_calibration,
    run_training_process_positive_pigeonhole_iut_v3_power_calibration,
)


ROOT = Path(__file__).resolve().parents[1]
NULL_CONTRACT = ROOT / "ODSP_TRAINING_PROCESS_POSITIVE_PIGEONHOLE_IUT_V3_NULL_CALIBRATION_CONTRACT.json"
POWER_CONTRACT = ROOT / "ODSP_TRAINING_PROCESS_POSITIVE_PIGEONHOLE_IUT_V3_POWER_CALIBRATION_CONTRACT.json"


def test_v3_contracts_are_frozen_before_results():
    null = json.loads(NULL_CONTRACT.read_text(encoding="utf-8"))
    power = json.loads(POWER_CONTRACT.read_text(encoding="utf-8"))
    assert null["generator_version"] == NULL_GENERATOR_VERSION
    assert power["generator_version"] == POWER_GENERATOR_VERSION
    assert null["prequalification_history"]["v3_results_observed_before_this_freeze"] is False
    assert power["prequalification_history"]["v3_power_results_observed_before_this_freeze"] is False
    assert null["acceptance_rule"]["maximum_accepted_component_rate"] == pytest.approx(
        0.06378404875209022
    )
    assert power["acceptance_rule"]["minimum_strong_terminal_power"] == 0.8


def test_v3_calibration_rejects_out_of_scope_settings():
    with pytest.raises(ValueError, match="simulations_per_scenario"):
        run_training_process_positive_pigeonhole_iut_v3_null_calibration(
            simulations_per_scenario=99
        )
    with pytest.raises(ValueError, match="contrast_count"):
        run_training_process_positive_pigeonhole_iut_v3_null_calibration(
            contrast_count=4
        )
    with pytest.raises(ValueError, match="standardized shifts"):
        run_training_process_positive_pigeonhole_iut_v3_power_calibration(
            moderate_standardized_shift=5,
            strong_standardized_shift=3,
        )
