from odsp.selection_validation_provenance_benchmark import (
    run_selection_validation_provenance_benchmark,
)


def test_selection_validation_provenance_known_truth_benchmark():
    result = run_selection_validation_provenance_benchmark()
    assert result["passed"] is True
    assert len(result["checks"]) == 15
    assert all(row["passed"] for row in result["checks"])
    assert result["final_validation_row_count"] == 8
    assert result["selection_stage_count"] == 3

    clean = result["clean"]
    assert clean["separation_category"] == "selection_validation_disjoint"
    assert clean["selection_validation_separated"] is True
    assert clean["overlapping_stage_count"] == 0
    assert clean["duplicate_selection_row_count"] == 1

    single = result["single_leak"]
    assert single["separation_category"] == "selection_validation_leakage"
    assert single["overlapping_stage_count"] == 1
    assert single["unique_overlapping_final_validation_row_count"] == 1

    repeated = result["repeated_leak"]
    assert repeated["unique_overlapping_final_validation_row_count"] == 1
    assert repeated["duplicate_selection_row_count"] == 2

    multi = result["multi_stage_leak"]
    assert multi["overlapping_stage_count"] == 3
    assert multi["unique_overlapping_final_validation_row_count"] == 5
    assert multi["maximum_stage_overlap_count"] == 3

    assert result["duplicate_final_rejected"] is True
    assert result["empty_stage_rejected"] is True
    assert result["missing_expected_rejected"] is True
    assert result["extra_expected_rejected"] is True
    assert result["extra_actual_rejected"] is True
    assert result["stage_order_invariant"] is True
    assert result["row_relabeling_invariant"] is True
