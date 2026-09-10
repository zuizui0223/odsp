import json
from pathlib import Path

from odsp.evaluation_ledger_binding_benchmark import (
    run_evaluation_ledger_binding_benchmark,
)


ROOT = Path(__file__).resolve().parents[1]


def test_evaluation_ledger_binding_receipt_replays():
    receipt = json.loads(
        (ROOT / "EVALUATION_LEDGER_BINDING_VALIDATION_RECEIPT.json").read_text(
            encoding="utf-8"
        )
    )
    result = run_evaluation_ledger_binding_benchmark(seed=20260910)
    canonical = receipt["canonical_results"]

    assert result["passed"] is canonical["passed"] is True
    assert len(result["checks"]) == canonical["obligation_count"] == 16
    assert all(row["passed"] for row in result["checks"])

    for result_key, receipt_key in (
        ("clean", "clean"),
        ("wrong_declared_final_digest", "wrong_declared_final_digest"),
        ("stage_digest_substitution", "stage_digest_substitution"),
    ):
        row = result[result_key]
        expected = canonical[receipt_key]
        for key, value in expected.items():
            assert row[key] == value

    clean = result["clean"]
    assert result["digest_order_invariant"] == clean
    assert result["stage_mapping_order_invariant"] == clean
    assert result["artifact_id_relabeling_invariant"] == clean
    assert result["uppercase_digest_invariant"] == clean

    for key in (
        "unknown_accessed_artifact_id_rejected",
        "missing_final_artifact_in_manifest_rejected",
        "id_digest_stage_coverage_mismatch_rejected",
        "empty_access_stage_rejected",
        "invalid_digest_format_rejected",
    ):
        assert result[key] is canonical[key] is True

    for key in (
        "artifact_ids_emitted",
        "digests_emitted",
        "automatic_artifact_hashing",
        "automatic_access_history_inference",
        "manifest_completeness_assumed",
        "semantic_equivalence_inferred",
        "aggregate_confidence_score_emitted",
    ):
        assert canonical[key] is False

    assert all(value is False for value in receipt["claim_boundary"].values())
    assert all(value is False for value in receipt["frozen_submission_preservation"].values())
