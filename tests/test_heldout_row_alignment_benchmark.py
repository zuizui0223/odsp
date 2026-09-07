from odsp.heldout_row_alignment_benchmark import run_heldout_row_alignment_benchmark


def test_heldout_row_alignment_known_truth_benchmark():
    result = run_heldout_row_alignment_benchmark()
    assert result["passed"] is True
    assert len(result["checks"]) == 13
    assert all(row["passed"] for row in result["checks"])
    assert result["base_row_count"] == 8
    assert result["exact"]["alignment_category"] == "exact_alignment"
    assert result["reorderable"]["alignment_category"] == "reorderable_alignment"
    assert result["permutation_to_base"] == [1, 3, 5, 0, 7, 6, 4, 2]
    assert result["one_dimensional_max_restore_error"] == 0.0
    assert result["matrix_max_restore_error"] == 0.0
    assert result["missing"]["sources"][0]["missing_row_count"] == 1
    assert result["missing_extra"]["sources"][0]["missing_row_count"] == 1
    assert result["missing_extra"]["sources"][0]["extra_row_count"] == 1
    assert result["duplicate"]["sources"][0]["duplicate_row_id_count"] == 1
    assert result["multiple_sources"]["alignment_category"] == "row_mismatch"
    assert result["duplicate_base_rejected"] is True
    assert result["source_order_invariance"] is True
