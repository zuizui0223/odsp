import json
from pathlib import Path

from odsp.aligned_refit_scheme_sensitivity_benchmark import (
    run_aligned_refit_scheme_sensitivity_benchmark,
)


ROOT = Path(__file__).resolve().parents[1]


def _bad_source(audit: dict[str, object]) -> dict[str, object]:
    rows = audit["row_alignment"]["sources"]
    return next(row for row in rows if row["status"] == "row_mismatch")


def test_aligned_refit_scheme_sensitivity_receipt_replays():
    receipt = json.loads(
        (ROOT / "ALIGNED_REFIT_SCHEME_SENSITIVITY_VALIDATION_RECEIPT.json").read_text(encoding="utf-8")
    )
    result = run_aligned_refit_scheme_sensitivity_benchmark(nested_draws=1200)
    canonical = receipt["canonical_results"]

    assert result["passed"] is canonical["passed"] is True
    assert len(result["checks"]) == canonical["obligation_count"] == 12
    assert all(row["passed"] for row in result["checks"])
    assert result["base_row_count"] == canonical["base_row_count"]
    assert result["baseline_scheme_category"] == canonical["baseline_scheme_category"]
    assert result["baseline_minimum_nested_max_t_lower_bound"] == canonical["baseline_minimum_nested_max_t_lower_bound"]
    assert result["baseline_maximum_nested_max_t_upper_bound"] == canonical["baseline_maximum_nested_max_t_upper_bound"]
    assert result["baseline_scheme_mean_gains"] == canonical["baseline_scheme_mean_gains"]

    for result_key in ("exact", "permuted"):
        row = result[result_key]
        expected = canonical[result_key]
        assert row["status"] == expected["status"]
        assert row["statistical_audit_run"] is expected["statistical_audit_run"] is True
        assert row["row_alignment"]["alignment_category"] == expected["alignment_category"]
        assert row["row_alignment"]["exact_source_count"] == expected["exact_source_count"]
        assert row["row_alignment"]["reorderable_source_count"] == expected["reorderable_source_count"]
        assert row["row_alignment"]["mismatched_source_count"] == expected["mismatched_source_count"]
        assert row["scheme_sensitivity_category"] == expected["scheme_sensitivity_category"]
        assert row["scheme_robust_admissible"] is expected["scheme_robust_admissible"] is True

    assert result["permuted"]["scheme_audit"] == result["exact"]["scheme_audit"]
    assert canonical["permuted"]["reproduces_existing_scheme_audit_exactly"] is True

    for result_key in ("mismatch", "duplicate"):
        row = result[result_key]
        expected = canonical[result_key]
        bad = _bad_source(row)
        assert row["status"] == expected["status"] == "row_mismatch"
        assert row["statistical_audit_run"] is expected["statistical_audit_run"] is False
        assert row["scheme_audit"] is None
        assert expected["scheme_audit_is_null"] is True
        assert row["row_alignment"]["alignment_category"] == expected["alignment_category"]
        assert row["row_alignment"]["mismatched_source_count"] == expected["mismatched_source_count"]
        assert bad["source_name"] == expected["bad_scheme"]
        assert bad["missing_row_count"] == expected["missing_row_count"]
        assert bad["extra_row_count"] == expected["extra_row_count"]
        assert bad["duplicate_row_id_count"] == expected["duplicate_row_id_count"]

    assert result["missing_mapping_rejected"] is canonical["missing_mapping_rejected"] is True
    assert result["length_mismatch_rejected"] is canonical["length_mismatch_rejected"] is True
    assert result["permuted"]["automatic_row_imputation"] is canonical["automatic_row_imputation"] is False
    assert result["permuted"]["automatic_scheme_selection"] is canonical["automatic_scheme_selection"] is False
    assert result["permuted"]["aggregate_confidence_score_emitted"] is canonical["aggregate_confidence_score_emitted"] is False
    assert all(value is False for value in receipt["claim_boundary"].values())
    assert all(value is False for value in receipt["frozen_v4_preservation"].values())
