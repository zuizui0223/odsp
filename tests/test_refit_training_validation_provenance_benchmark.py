from odsp.refit_training_validation_provenance_benchmark import (
    run_refit_training_validation_provenance_benchmark,
)


def test_refit_training_validation_provenance_known_truth_benchmark():
    result = run_refit_training_validation_provenance_benchmark()
    assert result["passed"] is True
    assert len(result["checks"]) == 15
    assert all(row["passed"] for row in result["checks"])
    assert result["validation_row_count"] == 8
    assert result["scheme_count"] == 3
    assert result["refits_per_scheme"] == 4

    disjoint = result["disjoint"]
    assert disjoint["separation_category"] == "training_validation_disjoint"
    assert disjoint["training_validation_separated"] is True
    assert disjoint["overlapping_refit_count"] == 0
    assert disjoint["duplicate_training_row_count"] == 2

    single = result["single_leak"]
    assert single["separation_category"] == "leakage_detected"
    assert single["overlapping_refit_count"] == 1
    assert single["affected_scheme_count"] == 1
    assert single["unique_overlapping_validation_row_count"] == 1

    repeated = result["repeated_leak"]
    assert repeated["unique_overlapping_validation_row_count"] == 1

    multiple = result["multiple_leak"]
    assert multiple["overlapping_refit_count"] == 3
    assert multiple["affected_scheme_count"] == 3
    assert multiple["unique_overlapping_validation_row_count"] == 5
    assert multiple["maximum_refit_overlap_count"] == 3

    assert result["duplicate_validation_rejected"] is True
    assert result["empty_training_refit_rejected"] is True
    assert result["missing_expected_refit_rejected"] is True
    assert result["extra_expected_refit_rejected"] is True
    assert result["extra_actual_refit_rejected"] is True
