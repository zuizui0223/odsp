import pytest

pytest.importorskip("sklearn")

from odsp.forecast_assessment_v5_benchmark import run_forecast_assessment_v5_benchmark


def test_forecast_assessment_v5_known_truth_benchmark():
    result = run_forecast_assessment_v5_benchmark(seed=20260907)
    assert result["passed"] is True
    assert len(result["checks"]) == 15
    assert all(row["passed"] for row in result["checks"])

    clean = result["clean_exact"]
    assert clean["v5_certification"]["certification_status"] == "certified"
    assert clean["training_validation_provenance"]["separation_category"] == "training_validation_disjoint"
    assert clean["provenance_qualified_v4_assessment"] is not None

    permuted = result["clean_permuted"]
    assert permuted["v5_certification"]["certification_status"] == "certified"
    assert permuted["provenance_qualified_v4_assessment"] is not None

    leakage = result["training_leakage"]
    assert leakage["training_validation_provenance"]["separation_category"] == "leakage_detected"
    assert leakage["provenance_qualified_v4_assessment"] is None
    assert leakage["v5_certification"]["certification_status"] == "unavailable"
    assert leakage["v5_certification"]["provenance_blocking_reasons"] == ["training_validation_leakage"]
    assert not any(
        reason.startswith("refit_scheme")
        for reason in leakage["v5_certification"]["statistical_blocking_reasons"]
    )

    row_mismatch = result["clean_row_mismatch"]
    assert row_mismatch["training_validation_provenance"]["separation_category"] == "training_validation_disjoint"
    assert row_mismatch["v5_certification"]["certification_status"] == "unavailable"
    assert "heldout_row_mismatch" in row_mismatch["v5_certification"]["provenance_blocking_reasons"]

    sensitive = result["clean_scheme_sensitive"]
    assert sensitive["v5_certification"]["certification_status"] == "not_certified"

    prior = result["prior_v4_failure_with_leakage"]
    assert prior["v5_certification"]["certification_status"] == "not_certified"
    assert prior["provenance_qualified_v4_assessment"] is None

    strict = result["strict_extrapolation"]
    assert strict["v5_certification"]["certification_status"] == "certified"
    assert strict["v5_certification"]["operational_status"] == "admitted_with_warnings"
    assert "strict_extrapolation" in strict["v5_certification"]["warning_reasons"]

    omitted = result["omitted_scheme"]
    assert omitted["training_validation_provenance"] is None
    assert omitted["provenance_qualified_v4_assessment"] is None

    scheme_only = result["scheme_only"]
    assert scheme_only["v5_certification"]["certification_status"] == "certified"

    block = result["block_definition_warning"]
    assert block["v5_certification"]["certification_status"] == "certified"
    assert "block_definition_sensitive" in block["v5_certification"]["warning_reasons"]
