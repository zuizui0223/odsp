from __future__ import annotations
import json
from pathlib import Path

RECEIPT=Path("TRAINING_PROCESS_CV3TWO_V5_SUPPORT_ENVELOPE_RECEIPT.json")

def test_v5_support_envelope_is_frozen_as_pass():
    p=json.loads(RECEIPT.read_text(encoding="utf-8"))
    assert p["official_run"]["qualification_pass"] is True
    assert p["official_run"]["github_actions_run_id"] == 37253654051
    assert p["acceptance"]["largest_observed_component_rate"] == 0.058
    assert p["acceptance"]["all_five_support_scenarios_pass"] is True
    assert max(p["scenarios"].values()) <= p["acceptance"]["maximum_accepted_component_rate"]

def test_support_receipt_keeps_scope_supplementary():
    b=json.loads(RECEIPT.read_text(encoding="utf-8"))["boundary"]
    assert b["supplementary_support_not_substitute_for_base_qualification"] is True
    assert b["support_scenarios_dropped_after_results"] is False
    assert b["fixed_set_results_reclassified"] is False
