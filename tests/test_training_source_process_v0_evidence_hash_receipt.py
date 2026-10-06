from __future__ import annotations
import json
from pathlib import Path

P=Path("TRAINING_SOURCE_PROCESS_V0_EVIDENCE_HASH_RECEIPT.json")
PLAN=Path("ODSP_TRAINING_SOURCE_PROCESS_V0_EVIDENCE_PLAN_V3.json")

def test_source_v0_hash_receipt_matches_final_pre_result_plan():
    p=json.loads(P.read_text(encoding="utf-8"))
    plan=json.loads(PLAN.read_text(encoding="utf-8"))
    assert p["official_run"]["github_actions_run_id"] == 37545859351
    assert p["official_run"]["github_actions_job_id"] == 112549579222
    assert p["official_run"]["conclusion"] == "success"
    assert [row["artifact"] for row in p["artifacts"]] == plan["ordered_evidence_artifacts"]
    assert len(p["artifacts"]) == 15
    assert all(len(row["sha256"]) == 64 for row in p["artifacts"])

def test_source_v0_hash_receipt_precedes_and_does_not_perform_registration():
    p=json.loads(P.read_text(encoding="utf-8"))
    v=p["verification"]
    assert v["hash_snapshot_completed_before_route_registration"] is True
    assert v["ordered_artifact_membership_matches_pre_result_plan_v3"] is True
    b=p["boundary"]
    assert b["this_receipt_changes_evidence_membership"] is False
    assert b["this_receipt_registers_route"] is False
    assert b["this_receipt_claims_unknown_ecological_superpopulation_generalization"] is False
