import pytest

pytest.importorskip("sklearn")

from odsp.forecast_assessment_v4_benchmark import run_forecast_assessment_v4_benchmark


def test_forecast_assessment_v4_known_truth_benchmark():
    result = run_forecast_assessment_v4_benchmark(seed=20260907)
    assert result["passed"] is True
    assert len(result["checks"]) == 12
    assert all(row["passed"] for row in result["checks"])
    assert result["row_count"] == 1920

    exact = result["exact"]
    assert exact["v4_certification"]["certification_status"] == "certified"
    assert exact["v4_certification"]["row_provenance_status"] == "exact_alignment"
    assert exact["v3_assessment"] is not None

    permuted = result["permuted"]
    assert permuted["v4_certification"]["certification_status"] == "certified"
    assert permuted["v4_certification"]["row_provenance_status"] == "reorderable_alignment"
    assert permuted["aligned_refit_scheme_audit"]["reordered_scheme_count"] == 2

    sensitive = result["scheme_sensitive"]
    assert sensitive["v4_certification"]["certification_status"] == "not_certified"

    mismatch = result["row_mismatch"]
    assert mismatch["v3_assessment"] is None
    assert mismatch["v4_certification"]["certification_status"] == "unavailable"
    assert mismatch["v4_certification"]["v3_assessment_status"] == "withheld_row_mismatch"
    assert "heldout_row_mismatch" in mismatch["v4_certification"]["extended_blocking_reasons"]

    prior = result["prior_failed_row_mismatch"]
    assert prior["v4_certification"]["certification_status"] == "not_certified"

    omitted = result["omitted_scheme"]
    assert omitted["v4_certification"]["row_provenance_status"] == "not_required"
    assert omitted["v3_assessment"] is not None

    strict = result["strict_extrapolation"]
    assert strict["v4_certification"]["certification_status"] == "certified"
    assert strict["v4_certification"]["operational_status"] == "admitted_with_warnings"
    assert "strict_extrapolation" in strict["v4_certification"]["warning_reasons"]
