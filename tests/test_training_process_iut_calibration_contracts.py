from __future__ import annotations

import json
from pathlib import Path

from odsp.training_process_positive_iut_null_calibration import (
    GENERATOR_VERSION as NULL_GENERATOR,
)
from odsp.training_process_positive_iut_power_calibration import (
    GENERATOR_VERSION as POWER_GENERATOR,
)


ROOT=Path(__file__).resolve().parents[1]


def test_v2_null_contract_freezes_iut_not_simultaneous_ci_logic():
    payload=json.loads(
        (ROOT/"ODSP_TRAINING_PROCESS_IUT_NULL_CALIBRATION_CONTRACT.json").read_text()
    )
    assert payload["generator"]["generator_version"]==NULL_GENERATOR
    logic=payload["inferential_logic"]
    assert logic["additional_component_axis_multiplicity_correction_required"] is False
    assert logic["component_lower_bounds_are_simultaneous"] is False
    assert payload["qualification_run"]["seed"]==20261013
    assert payload["prequalification_history"]["formal_v2_seed_unused_before_this_freeze"] is True


def test_v2_power_contract_preserves_v1_5se_as_descriptive_and_freezes_6se_gate():
    payload=json.loads(
        (ROOT/"ODSP_TRAINING_PROCESS_IUT_POWER_CALIBRATION_CONTRACT.json").read_text()
    )
    assert payload["standardized_alternatives"]["carryover_shift_standard_errors"]==5.0
    assert payload["standardized_alternatives"]["carryover_role"].startswith("descriptive")
    assert payload["standardized_alternatives"]["strong_shift_standard_errors"]==6.0
    assert payload["acceptance_rule"]["minimum_strong_terminal_power"]==0.8
    assert payload["qualification_run"]["seed"]==20261014
    assert payload["prequalification_history"]["exploratory_iut_results_are_qualification_evidence"] is False
