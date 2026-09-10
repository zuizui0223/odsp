import json
from pathlib import Path

from odsp.evaluation_access_provenance_benchmark import run_evaluation_access_provenance_benchmark

ROOT = Path(__file__).resolve().parents[1]


def test_evaluation_access_provenance_receipt_replays():
    receipt = json.loads((ROOT / "EVALUATION_ACCESS_PROVENANCE_VALIDATION_RECEIPT.json").read_text(encoding="utf-8"))
    result = run_evaluation_access_provenance_benchmark()
    c = receipt["canonical_results"]
    assert result["passed"] is c["passed"] is True
    assert len(result["checks"]) == c["obligation_count"] == 15
    assert all(row["passed"] for row in result["checks"])
    assert result["pre_final_stage_count"] == c["pre_final_stage_count"]
    assert result["clean"]["separation_category"] == c["clean_category"]
    assert result["single_leak"]["separation_category"] == c["single_leak_category"]
    assert result["single_leak"]["leaking_stage_count"] == c["single_leak_stage_count"]
    assert result["single_leak"]["final_evaluation_access_occurrence_count"] == c["single_leak_occurrence_count"]
    assert result["repeated_leak"]["final_evaluation_access_occurrence_count"] == c["repeated_leak_occurrence_count"]
    assert result["multi_stage_leak"]["leaking_stage_count"] == c["multi_stage_leak_stage_count"]
    assert result["multi_stage_leak"]["final_evaluation_access_occurrence_count"] == c["multi_stage_leak_occurrence_count"]
    assert result["multi_stage_leak"]["maximum_stage_final_access_count"] == c["multi_stage_maximum_stage_final_access_count"]
    assert result["clean"]["duplicate_access_count"] == c["clean_duplicate_nonfinal_access_count"]
    assert result["multi_stage_leak"]["accessed_artifact_ids_emitted"] is c["accessed_artifact_ids_emitted"] is False
    assert result["multi_stage_leak"]["automatic_access_history_inference"] is c["automatic_access_history_inference"] is False
    assert result["multi_stage_leak"]["ledger_completeness_assumed"] is c["ledger_completeness_assumed"] is False
    assert result["multi_stage_leak"]["automatic_candidate_selection"] is c["automatic_candidate_selection"] is False
    assert result["multi_stage_leak"]["aggregate_confidence_score_emitted"] is c["aggregate_confidence_score_emitted"] is False
    assert all(v is False for v in receipt["claim_boundary"].values())
    assert all(v is False for v in receipt["frozen_submission_preservation"].values())
