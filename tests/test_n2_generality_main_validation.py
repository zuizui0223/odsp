from __future__ import annotations

import json
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
SUMMARY = ROOT / "N2_GENERALITY_BENCHMARK_SUMMARY.json"
STATUS = ROOT / "N2_MANUSCRIPT_GENERALITY_STATUS.json"


def test_generality_summary_is_pinned_to_merged_main_validation():
    summary = json.loads(SUMMARY.read_text(encoding="utf-8"))
    workflow = summary["workflow"]
    result = summary["result"]

    assert workflow["branch"] == "main"
    assert workflow["event"] == "push"
    assert workflow["head_sha"] == "85acaa69e2dcc1a3052294dd6fac6471458391fa"
    assert workflow["run_id"] == 33833816625
    assert workflow["conclusion"] == "success"
    assert workflow["artifact_id"] == 9922590229
    assert workflow["artifact_digest"] == "sha256:281a3a33eafd3490500b73a6cc77babcb8c6164f5995e03998359d78b96d4c13"
    assert result["passed"] is True
    assert result["check_count"] == result["passed_count"] == 1873
    assert result["failed_count"] == 0
    assert result["maximum_absolute_error"] == 2.4868995751603507e-14


def test_manuscript_generality_status_matches_main_validation():
    summary = json.loads(SUMMARY.read_text(encoding="utf-8"))
    status = json.loads(STATUS.read_text(encoding="utf-8"))
    validated = status["validated_on_main"]

    assert validated["main_sha"] == summary["workflow"]["head_sha"]
    assert validated["generality_run_id"] == summary["workflow"]["run_id"]
    assert validated["generality_artifact_id"] == summary["workflow"]["artifact_id"]
    assert validated["generality_artifact_digest"] == summary["workflow"]["artifact_digest"]
    assert validated["proof_obligations_passed"] == summary["result"]["passed_count"]
    assert validated["proof_obligations_failed"] == 0
    assert validated["maximum_absolute_error"] == summary["result"]["maximum_absolute_error"]


def test_generality_status_keeps_biological_claim_ceiling():
    status = json.loads(STATUS.read_text(encoding="utf-8"))
    claim = status["strongest_defensible_generality_claim"]
    not_claimed = set(status["not_claimed"])

    assert "axis-agnostic over finite discrete support tensors" in claim
    assert "empirical portability" in claim
    assert "universal biological frequency of thick or generalizing niches" in not_claimed
    assert "causal generality across ecological systems" in not_claimed
    assert "elimination of detectability, sampling or representativeness bias" in not_claimed
