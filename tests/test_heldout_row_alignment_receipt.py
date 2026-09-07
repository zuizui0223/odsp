import json
from pathlib import Path

from odsp.heldout_row_alignment_benchmark import run_heldout_row_alignment_benchmark


ROOT = Path(__file__).resolve().parents[1]


def test_heldout_row_alignment_receipt_replays():
    receipt = json.loads((ROOT / "HELDOUT_ROW_ALIGNMENT_VALIDATION_RECEIPT.json").read_text(encoding="utf-8"))
    result = run_heldout_row_alignment_benchmark()
    canonical = receipt["canonical_results"]

    assert result["passed"] is canonical["passed"] is True
    assert len(result["checks"]) == canonical["obligation_count"] == 13
    assert all(row["passed"] for row in result["checks"])
    assert result["base_row_count"] == canonical["base_row_count"]

    exact = result["exact"]
    assert exact["alignment_category"] == canonical["exact"]["alignment_category"]
    assert exact["alignment_passed"] is canonical["exact"]["alignment_passed"] is True
    assert exact["sources"][0]["permutation_to_base"] == canonical["exact"]["permutation_to_base"]

    reordered = result["reorderable"]
    assert reordered["alignment_category"] == canonical["reorderable"]["alignment_category"]
    assert reordered["alignment_passed"] is canonical["reorderable"]["alignment_passed"] is True
    assert result["permutation_to_base"] == canonical["reorderable"]["permutation_to_base"]
    assert result["one_dimensional_max_restore_error"] == canonical["one_dimensional_max_restore_error"] == 0.0
    assert result["matrix_max_restore_error"] == canonical["matrix_max_restore_error"] == 0.0

    for result_key, receipt_key in (("missing", "missing"), ("missing_extra", "missing_extra")):
        row = result[result_key]
        expected = canonical[receipt_key]
        assert row["alignment_category"] == expected["alignment_category"]
        assert row["sources"][0]["missing_row_count"] == expected["missing_row_count"]
        assert row["sources"][0]["extra_row_count"] == expected["extra_row_count"]

    duplicate = result["duplicate"]
    expected = canonical["duplicate"]
    assert duplicate["alignment_category"] == expected["alignment_category"]
    assert duplicate["sources"][0]["duplicate_row_id_count"] == expected["duplicate_row_id_count"]
    assert duplicate["sources"][0]["missing_row_count"] == expected["missing_row_count"]

    multiple = result["multiple_sources"]
    expected = canonical["multiple_sources"]
    assert multiple["alignment_category"] == expected["alignment_category"]
    assert multiple["exact_source_count"] == expected["exact_source_count"]
    assert multiple["reorderable_source_count"] == expected["reorderable_source_count"]
    assert multiple["mismatched_source_count"] == expected["mismatched_source_count"]

    assert result["duplicate_base_rejected"] is canonical["duplicate_base_rejected"] is True
    assert result["source_order_invariance"] is canonical["source_order_invariance"] is True
    assert reordered["automatic_row_imputation"] is canonical["automatic_row_imputation"] is False
    assert reordered["row_contents_used_for_identity"] is canonical["row_contents_used_for_identity"] is False
    assert reordered["aggregate_confidence_score_emitted"] is canonical["aggregate_confidence_score_emitted"] is False
    assert all(value is False for value in receipt["claim_boundary"].values())
    assert all(value is False for value in receipt["frozen_v4_preservation"].values())
