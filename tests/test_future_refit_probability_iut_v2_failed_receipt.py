from __future__ import annotations

import json
from pathlib import Path

RECEIPT=Path("TRAINING_PROCESS_FUTURE_REFIT_PROBABILITY_REFIT_IUT_V2_FAILED_RECEIPT.json")

def test_v2_first_1000_panel_is_frozen_as_power_failure():
    p=json.loads(RECEIPT.read_text(encoding="utf-8"))
    assert p["official_first_1000"]["github_actions_run_id"]==37706446179
    assert p["official_first_1000"]["head_sha"]=="2c17eb1217e0037e3b671eb608ae505a8f3dd511"
    assert p["official_first_1000"]["seed"]==20261019
    assert p["coverage"]["acceptance_pass"] is True
    assert p["power"]["acceptance_pass"] is False
    assert p["power"]["all-success-r8-b8"]["all_refits_certified_power"]==0.852
    assert p["power"]["all-success-r20-b8"]["all_refits_certified_power"]==0.096
    assert p["summary"]["qualification_pass"] is False

def test_v2_failure_not_relabelled_or_used_to_rescue_v1():
    b=json.loads(RECEIPT.read_text(encoding="utf-8"))["boundary"]
    assert b["fixed_v1_failure_remains_failure"] is True
    assert b["v2_primary_confirmatory_now"] is False
    assert b["future_refit_success_probability_claim_not_qualified"] is True
    assert b["underlying_v5_process_mean_route_unchanged"] is True
    assert b["fixed_set_intersection_unchanged"] is True
