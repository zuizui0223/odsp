from odsp.aligned_refit_scheme_sensitivity_benchmark import (
    run_aligned_refit_scheme_sensitivity_benchmark,
)


def test_aligned_refit_scheme_sensitivity_known_truth_benchmark():
    result = run_aligned_refit_scheme_sensitivity_benchmark(nested_draws=1200)
    assert result["passed"] is True
    assert len(result["checks"]) == 12
    assert all(row["passed"] for row in result["checks"])
    assert result["base_row_count"] == 1920
    assert result["baseline_scheme_category"] == "scheme_robust_generalizing"
    assert result["exact"]["status"] == "audited_exact_alignment"
    assert result["permuted"]["status"] == "audited_reordered_alignment"
    assert result["permuted"]["reordered_scheme_count"] == 2
    assert result["permuted"]["scheme_sensitivity_category"] == "scheme_robust_generalizing"
    assert result["mismatch"]["status"] == "row_mismatch"
    assert result["mismatch"]["statistical_audit_run"] is False
    assert result["mismatch"]["scheme_audit"] is None
    assert result["duplicate"]["status"] == "row_mismatch"
    assert result["missing_mapping_rejected"] is True
    assert result["length_mismatch_rejected"] is True
