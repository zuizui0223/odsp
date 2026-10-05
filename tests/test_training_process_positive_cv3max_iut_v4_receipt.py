from __future__ import annotations
import json
from pathlib import Path

RECEIPT = Path("TRAINING_PROCESS_POSITIVE_CV3MAX_IUT_V4_QUALIFICATION_RECEIPT.json")

def test_v4_cv3max_result_is_frozen_as_null_failure_power_pass():
    payload=json.loads(RECEIPT.read_text(encoding="utf-8"))
    assert payload["summary"]["qualification_pass"] is False
    assert payload["summary"]["null_gate_pass"] is False
    assert payload["summary"]["power_gate_pass"] is True
    assert payload["summary"]["largest_component_rate"] == 0.065
    assert payload["boundary"]["v4_may_be_reclassified_as_qualified"] is False
