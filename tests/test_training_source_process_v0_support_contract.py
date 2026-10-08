from __future__ import annotations
import json
from pathlib import Path

P=Path("ODSP_TRAINING_SOURCE_PROCESS_V0_SUPPORT_CONTRACT.json")


def test_source_v0_support_is_frozen_before_support_results():
    p=json.loads(P.read_text(encoding="utf-8"))
    assert p["base_result_known_before_support_freeze"] is True
    assert p["run"]["seed"] == 20261018
    assert p["run"]["simulations_per_scenario"] == 1000
    assert len(p["support_scenarios"]) == 5
    assert p["selection_boundary"]["support_results_observed_before_freeze"] is False
    assert p["selection_boundary"]["scenario_may_be_dropped_after_result_to_rescue_v0"] is False
    assert p["acceptance_rule"]["maximum_accepted_component_rate"] == 0.06378404875209022
    assert p["promotion_boundary"]["route_registration_forbidden"] is True
