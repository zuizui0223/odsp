from __future__ import annotations

import json
from pathlib import Path

RECEIPT = Path("TRAINING_PROCESS_POSITIVE_CV3TWO_IUT_V5_QUALIFICATION_RECEIPT.json")


def test_v5_base_qualification_is_frozen_as_pass():
    p = json.loads(RECEIPT.read_text(encoding="utf-8"))
    assert p["summary"]["base_qualification_pass"] is True
    assert p["summary"]["base_null_gate_pass"] is True
    assert p["summary"]["base_power_gate_pass"] is True
    assert p["summary"]["largest_component_false_positive_rate"] == 0.056
    assert p["summary"]["smallest_strong_terminal_power"] == 0.859
    assert p["null_run"]["github_actions_run_id"] == 37253208181
    assert p["power_run"]["github_actions_run_id"] == 37253208133


def test_v5_was_frozen_before_v4_official_result_completed():
    p = json.loads(RECEIPT.read_text(encoding="utf-8"))
    assert p["chronology"]["v5_frozen_before_v4_official_results_completed"] is True
    assert p["chronology"]["v5_contract_commit_time_utc"] < p["chronology"]["v4_official_null_completed_utc"]
    assert p["chronology"]["v5_contract_commit_time_utc"] < p["chronology"]["v4_official_power_completed_utc"]


def test_v5_base_receipt_does_not_expand_claim():
    b = json.loads(RECEIPT.read_text(encoding="utf-8"))["claim_boundary"]
    assert b["individual_future_refit_success_probability_claimed"] is False
    assert b["fixed_set_results_reclassified"] is False
    assert b["untouched_external_endpoint_qualified_by_this_receipt"] is False
