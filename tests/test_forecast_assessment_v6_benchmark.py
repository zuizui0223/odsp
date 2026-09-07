import pytest

pytest.importorskip("sklearn")

from odsp.forecast_assessment_v6_benchmark import run_forecast_assessment_v6_benchmark


def test_forecast_assessment_v6_known_truth_benchmark():
    result = run_forecast_assessment_v6_benchmark(seed=20260907)
    assert result["passed"] is True
    assert len(result["checks"]) == 15
    assert all(row["passed"] for row in result["checks"])

    clean = result["clean_selection"]
    assert clean["selection_validation_provenance"]["separation_category"] == "selection_validation_disjoint"
    assert clean["downstream_v5_assessment"] is not None
    assert clean["v6_certification"]["certification_status"] == "certified"

    leaked = result["selection_leakage"]
    assert leaked["selection_validation_provenance"]["separation_category"] == "selection_validation_leakage"
    assert leaked["downstream_v5_assessment"] is None
    assert leaked["v6_certification"]["certification_status"] == "unavailable"
    assert leaked["v6_certification"]["provenance_blocking_reasons"] == ["selection_validation_leakage"]

    prior = result["prior_v5_failure_with_selection_leakage"]
    assert prior["base_v5_assessment"]["v5_certification"]["certification_status"] == "not_certified"
    assert prior["v6_certification"]["certification_status"] == "not_certified"

    training = result["clean_selection_training_leakage"]
    assert training["downstream_v5_assessment"]["v5_certification"]["certification_status"] == "unavailable"
    assert "training_validation_leakage" in training["v6_certification"]["provenance_blocking_reasons"]

    mismatch = result["clean_selection_row_mismatch"]
    assert mismatch["v6_certification"]["certification_status"] == "unavailable"
    assert "heldout_row_mismatch" in mismatch["v6_certification"]["provenance_blocking_reasons"]

    sensitive = result["clean_selection_scheme_sensitive"]
    assert sensitive["v6_certification"]["certification_status"] == "not_certified"

    no_scheme = result["selection_leakage_without_scheme"]
    assert no_scheme["downstream_v5_assessment"] is None
    assert no_scheme["v6_certification"]["certification_status"] == "unavailable"

    strict = result["strict_extrapolation"]
    assert strict["v6_certification"]["certification_status"] == "certified"
    assert strict["v6_certification"]["operational_status"] == "admitted_with_warnings"
    assert "strict_extrapolation" in strict["v6_certification"]["warning_reasons"]

    omitted = result["omitted_selection"]
    assert omitted["selection_validation_provenance"] is None
    assert omitted["downstream_v5_assessment"] is not None

    block = result["block_definition_warning"]
    assert block["v6_certification"]["certification_status"] == "certified"
    assert "block_definition_sensitive" in block["v6_certification"]["warning_reasons"]
