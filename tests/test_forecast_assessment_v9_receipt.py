import json
from pathlib import Path

import pytest

pytest.importorskip("sklearn")

from odsp.forecast_assessment_v9_benchmark import run_forecast_assessment_v9_benchmark


ROOT = Path(__file__).resolve().parents[1]


def test_forecast_assessment_v9_receipt_replays():
    receipt = json.loads(
        (ROOT / "FORECAST_ASSESSMENT_V9_LEDGER_BINDING_VALIDATION_RECEIPT.json").read_text(
            encoding="utf-8"
        )
    )
    result = run_forecast_assessment_v9_benchmark(seed=20260910)
    canonical = receipt["canonical_results"]

    assert result["passed"] is canonical["passed"] is True
    assert len(result["checks"]) == canonical["obligation_count"] == 17
    assert all(row["passed"] for row in result["checks"])

    clean = result["clean_binding"]
    expected = canonical["clean_binding"]
    binding = clean["evaluation_ledger_binding"]
    cert = clean["v9_certification"]
    assert binding["separation_category"] == expected["binding_category"]
    assert binding["final_evaluation_binding_match"] is expected["final_binding_match"] is True
    assert binding["mismatched_stage_count"] == expected["mismatched_stage_count"] == 0
    assert binding["binding_discrepancy_occurrence_count"] == expected["binding_discrepancy_occurrence_count"] == 0
    assert binding["final_content_alias_id_count"] == expected["final_content_alias_id_count"] == 1
    assert clean["settings"]["downstream_v8_assessment_run"] is expected["downstream_v8_assessment_run"] is True
    assert cert["certification_status"] == expected["certification_status"]
    assert cert["operational_status"] == expected["operational_status"]
    assert cert["provenance_blocking_reasons"] == expected["provenance_blocking_reasons"]
    assert cert["statistical_blocking_reasons"] == expected["statistical_blocking_reasons"]
    assert cert["warning_reasons"] == expected["warning_reasons"]

    mismatch = result["ledger_binding_mismatch"]
    expected = canonical["ledger_binding_mismatch"]
    binding = mismatch["evaluation_ledger_binding"]
    cert = mismatch["v9_certification"]
    assert binding["separation_category"] == expected["binding_category"]
    assert binding["final_evaluation_binding_match"] is expected["final_binding_match"] is True
    assert binding["mismatched_stage_count"] == expected["mismatched_stage_count"] == 1
    assert binding["binding_discrepancy_occurrence_count"] == expected["binding_discrepancy_occurrence_count"] == 1
    assert mismatch["downstream_v8_assessment"] is None
    assert mismatch["settings"]["downstream_v8_assessment_run"] is expected["downstream_v8_assessment_run"] is False
    assert cert["certification_status"] == expected["certification_status"]
    assert cert["operational_status"] == expected["operational_status"]
    assert cert["provenance_blocking_reasons"] == expected["provenance_blocking_reasons"]
    assert cert["statistical_blocking_reasons"] == expected["statistical_blocking_reasons"]

    prior = result["prior_v8_failure_with_binding_mismatch"]
    expected = canonical["prior_v8_failure_with_binding_mismatch"]
    assert prior["v9_certification"]["certification_status"] == expected["certification_status"]
    assert prior["v9_certification"]["operational_status"] == expected["operational_status"]
    assert prior["v9_certification"]["provenance_blocking_reasons"] == expected["provenance_blocking_reasons"]
    assert prior["v9_certification"]["statistical_blocking_reasons"] == expected["statistical_blocking_reasons"]
    assert prior["downstream_v8_assessment"] is None

    for result_key, receipt_key, reason_field in (
        ("clean_binding_content_leakage", "clean_binding_content_leakage", "provenance_blocking_reasons"),
        ("clean_binding_direct_artifact_id_leakage", "clean_binding_direct_artifact_id_leakage", "provenance_blocking_reasons"),
        ("clean_binding_selection_leakage", "clean_binding_selection_leakage", "provenance_blocking_reasons"),
        ("clean_binding_training_leakage", "clean_binding_training_leakage", "provenance_blocking_reasons"),
        ("clean_binding_row_mismatch", "clean_binding_row_mismatch", "provenance_blocking_reasons"),
        ("clean_binding_scheme_sensitive", "clean_binding_scheme_sensitive", "statistical_blocking_reasons"),
    ):
        row = result[result_key]
        expected = canonical[receipt_key]
        assert row["v9_certification"]["certification_status"] == expected["certification_status"]
        assert row["v9_certification"][reason_field] == expected[reason_field]

    no_lower = result["binding_mismatch_without_downstream_layers"]
    expected = canonical["binding_mismatch_without_downstream_layers"]
    assert no_lower["downstream_v8_assessment"] is None
    assert no_lower["settings"]["downstream_v8_assessment_run"] is expected["downstream_v8_assessment_run"] is False
    assert no_lower["v9_certification"]["certification_status"] == expected["certification_status"]
    assert no_lower["v9_certification"]["provenance_blocking_reasons"] == expected["provenance_blocking_reasons"]

    strict = result["strict_extrapolation"]
    expected = canonical["strict_extrapolation"]
    assert strict["v9_certification"]["certification_status"] == expected["certification_status"]
    assert strict["v9_certification"]["operational_status"] == expected["operational_status"]
    assert strict["v9_certification"]["warning_reasons"] == expected["warning_reasons"]
    novelty = strict["downstream_v8_assessment"]["downstream_v7_assessment"]["downstream_v6_assessment"]["downstream_v5_assessment"]["provenance_qualified_v4_assessment"]["base_v3_assessment"]["base_v2_assessment"]["base_assessment"]["dossier"]["deployment"]
    assert novelty["maximum_novelty_ratio"] == expected["maximum_novelty_ratio"]

    omitted = result["omitted_binding"]
    expected = canonical["omitted_binding"]
    assert omitted["evaluation_ledger_binding"] is None
    assert expected["binding_is_null"] is True
    assert omitted["settings"]["downstream_v8_assessment_run"] is expected["downstream_v8_assessment_run"] is True
    assert omitted["v9_certification"]["certification_status"] == expected["certification_status"]

    assert canonical["aggregate_confidence_score_emitted"] is False
    assert all(value is False for value in receipt["claim_boundary"].values())
    assert all(value is False for value in receipt["frozen_submission_preservation"].values())
