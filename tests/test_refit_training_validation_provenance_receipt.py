import json
from pathlib import Path

from odsp.refit_training_validation_provenance_benchmark import (
    run_refit_training_validation_provenance_benchmark,
)


ROOT = Path(__file__).resolve().parents[1]


def test_refit_training_validation_provenance_receipt_replays():
    receipt = json.loads(
        (ROOT / "REFIT_TRAINING_VALIDATION_PROVENANCE_VALIDATION_RECEIPT.json").read_text(
            encoding="utf-8"
        )
    )
    result = run_refit_training_validation_provenance_benchmark()
    canonical = receipt["canonical_results"]

    assert result["passed"] is canonical["passed"] is True
    assert len(result["checks"]) == canonical["obligation_count"] == 15
    assert all(row["passed"] for row in result["checks"])
    assert result["validation_row_count"] == canonical["validation_row_count"]
    assert result["scheme_count"] == canonical["scheme_count"]

    for key in ("disjoint", "single_leak", "repeated_leak", "multiple_leak"):
        row = result[key]
        expected = canonical[key]
        for field, value in expected.items():
            assert row[field] == value

    for field in (
        "duplicate_validation_rejected",
        "empty_training_refit_rejected",
        "missing_expected_refit_rejected",
        "extra_expected_refit_rejected",
        "extra_actual_refit_rejected",
    ):
        assert result[field] is canonical[field] is True

    assert result["disjoint"]["refit_count"] == canonical["refit_count"]
    assert result["disjoint"]["overlapping_row_ids_emitted"] is canonical["overlapping_row_ids_emitted"] is False
    assert result["disjoint"]["automatic_training_row_inference"] is canonical["automatic_training_row_inference"] is False
    assert result["disjoint"]["aggregate_confidence_score_emitted"] is canonical["aggregate_confidence_score_emitted"] is False
    assert all(value is False for value in receipt["claim_boundary"].values())
    assert all(value is False for value in receipt["frozen_v4_preservation"].values())
