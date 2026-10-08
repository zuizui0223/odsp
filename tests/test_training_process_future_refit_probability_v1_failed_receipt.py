from __future__ import annotations

import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
RECEIPT = ROOT / "TRAINING_PROCESS_FUTURE_REFIT_SUCCESS_PROBABILITY_V1_FAILED_RECEIPT.json"

def test_first_prospective_probability_v1_power_failure_is_preserved():
    p = json.loads(RECEIPT.read_text(encoding="utf-8"))
    assert p["first_official_run"]["github_actions_run_id"] == 37645429154
    assert p["first_official_run"]["head_sha"] == "6cd4d73b20f170b3bb03cb4111fd5b66d7250c10"
    assert p["first_official_run"]["simulations_per_scenario"] == 1000
    assert p["coverage"]["gate_pass"] is True
    assert p["strong_power"]["gate_pass"] is False
    assert p["summary"]["qualification_pass"] is False
    assert p["summary"]["v1_closed_to_primary"] is True
    assert p["strong_power"]["certified_all_refits_power_by_scenario"] == {
        "all-success-r8-b8": 0.0,
        "all-success-r20-b8": 0.0,
    }
    assert p["strong_power"]["minimum_accepted_power"] == 0.8

def test_failure_cannot_be_promoted_or_used_to_modify_other_estimands():
    p = json.loads(RECEIPT.read_text(encoding="utf-8"))
    assert p["claim_boundary"]["positive_future_refit_probability_inference_qualified"] is False
    assert p["claim_boundary"]["a_successor_requires_distinct_prefrozen_method_and_calibration"] is True
    assert p["summary"]["thresholds_relaxed_after_outcome"] is False
    assert p["summary"]["process_mean_v5_unchanged"] is True
    assert p["summary"]["fixed_set_routes_unchanged"] is True
