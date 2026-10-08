from __future__ import annotations
import json
from pathlib import Path

P=Path("ODSP_TRAINING_SOURCE_PROCESS_V0_FOCUSED_TEST_CORRECTION.json")

def test_source_v0_focused_test_correction_is_test_only_and_drops_nothing():
    p=json.loads(P.read_text(encoding="utf-8"))
    assert p["first_failed_focused_run"]["failed_test_count"] == 5
    assert len(p["corrections"]) == 5
    assert all(row["method_code_changed"] is False for row in p["corrections"])
    inv=p["invariants"]
    assert inv["required_test_files_removed"] is False
    assert inv["required_failure_modes_removed"] is False
    assert inv["numeric_estimator_changed"] is False
    assert inv["managed_scoring_implementation_changed"] is False
    assert inv["evidence_plan_v3_membership_changed"] is False

def test_source_v0_correction_is_not_added_as_posthoc_qualification_evidence():
    p=json.loads(P.read_text(encoding="utf-8"))
    b=p["qualification_boundary"]
    assert b["this_contract_is_new_qualification_evidence"] is False
    assert b["focused_receipt_contract_remains_authoritative"] is True
    assert b["all_predeclared_required_test_files_still_must_pass_together"] is True
