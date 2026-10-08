from __future__ import annotations

import json
from pathlib import Path

import pytest

from odsp.training_process_future_refit_probability_iut_v2_calibration import (
    GENERATOR_VERSION,
    run_future_refit_probability_refit_iut_v2_calibration,
)
from odsp.training_process_future_refit_success_probability_calibration import (
    COVERAGE_SCENARIOS,
    POWER_SCENARIOS,
)

CONTRACT = Path("ODSP_TRAINING_PROCESS_FUTURE_REFIT_SUCCESS_PROBABILITY_REFIT_IUT_V2_CONTRACT.json")

def test_v2_contract_was_frozen_before_any_v2_panel():
    p=json.loads(CONTRACT.read_text(encoding="utf-8"))
    frozen=p["prospective_qualification"]
    assert frozen["generator_version"]==GENERATOR_VERSION
    assert frozen["seed"]==20261019
    assert frozen["results_observed_before_this_freeze"] is False
    assert frozen["coverage_overclaim_max"]==pytest.approx(0.06378404875209022)
    assert frozen["validation_overcertification_max"]==pytest.approx(0.03487420882906575)
    assert frozen["power_all_refits_certified_minimum"]==0.8
    assert len(COVERAGE_SCENARIOS)==6
    assert len(POWER_SCENARIOS)==2
    assert p["validation_stage"]["correction_axis"].startswith("R observed refits only")
    assert p["validation_stage"]["familywise_max_t_used"] is False
    assert p["governance"]["primary_confirmatory_now"] is False

def test_v2_calibration_rejects_unfrozen_inputs():
    with pytest.raises(ValueError,match="simulations_per_scenario"):
        run_future_refit_probability_refit_iut_v2_calibration(simulations_per_scenario=99)
    with pytest.raises(ValueError,match="scope"):
        run_future_refit_probability_refit_iut_v2_calibration(group_count=5)
    with pytest.raises(ValueError,match="scope"):
        run_future_refit_probability_refit_iut_v2_calibration(contrast_count=4)
    with pytest.raises(ValueError,match="seed"):
        run_future_refit_probability_refit_iut_v2_calibration(seed=20261020)
