import pytest

pytest.importorskip("sklearn")

from odsp.forecast_assessment_v4_benchmark import run_forecast_assessment_v4_benchmark


def test_forecast_assessment_v4_known_truth_benchmark():
    result = run_forecast_assessment_v4_benchmark(seed=20260907)
    assert result["passed"] is True
    assert len(result["checks"]) == 13
    assert all(row["passed"] for row in result["checks"])

    strong = result["strong_exact"]
    assert strong["v4_certification"]["certification_status"] == "certified"
    assert strong["v4_certification"]["row_provenance_status"] == "exact_alignment"
    assert strong["aligned_refit_scheme_audit"]["status"] == "audited_exact_alignment"

    permuted = result["strong_permuted"]
    assert permuted["v4_certification"]["certification_status"] == "certified"
    assert permuted["v4_certification"]["row_provenance_status"] == "reorderable_alignment"
    assert permuted["aligned_refit_scheme_audit"]["reordered_scheme_count"] == 2

    mismatch = result["row_mismatch"]
    assert mismatch["v4_certification"]["certification_status"] == "unavailable"
    assert mismatch["aligned_refit_scheme_audit"]["statistical_audit_run"] is False
    assert mismatch["aligned_refit_scheme_audit"]["scheme_audit"] is None
    assert mismatch["v4_certification"]["provenance_blocking_reasons"] == ["heldout_row_mismatch"]

    sensitive = result["scheme_sensitive"]
    assert sensitive["base_v3_assessment"]["v3_certification"]["certification_status"] == "certified"
    assert sensitive["v4_certification"]["certification_status"] == "not_certified"

    prior = result["prior_v3_failure"]
    assert prior["base_v3_assessment"]["v3_certification"]["certification_status"] == "not_certified"
    assert prior["v4_certification"]["certification_status"] == "not_certified"

    omitted = result["omitted_scheme"]
    assert omitted["aligned_refit_scheme_audit"] is None
    assert omitted["v4_certification"]["row_provenance_status"] == "not_audited"
