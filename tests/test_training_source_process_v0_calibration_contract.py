from __future__ import annotations
import json
from pathlib import Path

P=Path("ODSP_TRAINING_SOURCE_PROCESS_V0_CALIBRATION_CONTRACT.json")


def test_source_v0_calibration_is_frozen_before_results():
    p=json.loads(P.read_text(encoding="utf-8"))
    assert p["generator_version"] == "nested_source_refit_x_validation_c2_v0"
    assert p["null_run"]["seed"] == 20261016
    assert p["power_run"]["seed"] == 20261017
    assert p["null_run"]["simulations_per_scenario"] == 1000
    assert p["power_run"]["simulations_per_scenario"] == 1000
    assert p["null_run"]["maximum_accepted_component_rate"] == 0.06378404875209022
    assert p["power_run"]["minimum_accepted_strong_terminal_power"] == 0.8
    assert len(p["scenarios"]) == 6
    assert any(x["scenario_id"].startswith("inner-dominant") for x in p["scenarios"])
    assert p["governance"]["results_observed_before_freeze"] is False
    assert p["governance"]["thresholds_may_change_after_result_to_rescue_v0"] is False
    assert p["governance"]["qualification_pass_alone_promotes_primary_route"] is False
