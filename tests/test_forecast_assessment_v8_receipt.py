import json
from pathlib import Path

import pytest

pytest.importorskip("sklearn")

from odsp.forecast_assessment_v8_benchmark import run_forecast_assessment_v8_benchmark


ROOT = Path(__file__).resolve().parents[1]


def _values_for_key(value, key):
    found = []
    if isinstance(value, dict):
        for child_key, child in value.items():
            if child_key == key:
                found.append(child)
            found.extend(_values_for_key(child, key))
    elif isinstance(value, list):
        for child in value:
            found.extend(_values_for_key(child, key))
    return found


def test_forecast_assessment_v8_receipt_replays():
    receipt = json.loads(
        (ROOT / "FORECAST_ASSESSMENT_V8_CONTENT_PROVENANCE_VALIDATION_RECEIPT.json").read_text(
            encoding="utf-8"
        )
    )
    result = run_forecast_assessment_v8_benchmark(seed=20260910)
    canonical = receipt["canonical_results"]

    assert result["passed"] is canonical["passed"] is True
    assert len(result["checks"]) == canonical["obligation_count"] == 16
    assert all(row["passed"] for row in result["checks"])

    clean = result["clean_content"]
    expected = canonical["clean_content"]
    assert clean["evaluation_content_provenance"]["separation_category"] == expected["content_category"]
    assert clean["settings"]["downstream_v7_assessment_run"] is expected["downstream_v7_assessment_run"] is True
    assert clean["v8_certification"]["certification_status"] == expected["certification_status"]
    assert clean["v8_certification"]["operational_status"] == expected["operational_status"]
    assert clean["v8_certification"]["provenance_blocking_reasons"] == expected["provenance_blocking_reasons"]
    assert clean["v8_certification"]["statistical_blocking_reasons"] == expected["statistical_blocking_reasons"]
    assert clean["v8_certification"]["warning_reasons"] == expected["warning_reasons"]

    leaked = result["final_evaluation_content_leakage"]
    expected = canonical["content_leakage"]
    provenance = leaked["evaluation_content_provenance"]
    assert provenance["separation_category"] == expected["content_category"]
    assert provenance["leaking_stage_count"] == expected["leaking_stage_count"]
    assert provenance["final_evaluation_content_match_occurrence_count"] == expected["match_occurrence_count"]
    assert provenance["maximum_stage_final_content_match_count"] == expected["maximum_stage_match_count"]
    assert leaked["downstream_v7_assessment"] is None
    assert leaked["settings"]["downstream_v7_assessment_run"] is expected["downstream_v7_assessment_run"] is False
    assert leaked["v8_certification"]["certification_status"] == expected["certification_status"]
    assert leaked["v8_certification"]["operational_status"] == expected["operational_status"]
    assert leaked["v8_certification"]["provenance_blocking_reasons"] == expected["provenance_blocking_reasons"]
    assert leaked["v8_certification"]["statistical_blocking_reasons"] == expected["statistical_blocking_reasons"]
    assert leaked["v8_certification"]["evaluation_access_provenance_status"] == expected["evaluation_access_provenance_status"]
    assert leaked["v8_certification"]["selection_validation_provenance_status"] == expected["selection_validation_provenance_status"]

    prior = result["prior_v7_failure_with_content_leakage"]
    expected = canonical["prior_v7_failure_with_content_leakage"]
    assert prior["v8_certification"]["certification_status"] == expected["certification_status"]
    assert prior["v8_certification"]["operational_status"] == expected["operational_status"]
    assert prior["v8_certification"]["provenance_blocking_reasons"] == expected["provenance_blocking_reasons"]
    assert prior["v8_certification"]["statistical_blocking_reasons"] == expected["statistical_blocking_reasons"]
    assert prior["downstream_v7_assessment"] is None

    for result_key, receipt_key in (
        ("clean_content_artifact_access_leakage", "clean_content_artifact_access_leakage"),
        ("clean_content_selection_leakage", "clean_content_selection_leakage"),
        ("clean_content_training_leakage", "clean_content_training_leakage"),
        ("clean_content_row_mismatch", "clean_content_row_mismatch"),
    ):
        row = result[result_key]
        expected = canonical[receipt_key]
        assert row["v8_certification"]["certification_status"] == expected["certification_status"]
        assert row["v8_certification"]["provenance_blocking_reasons"] == expected["provenance_blocking_reasons"]

    sensitive = result["clean_content_scheme_sensitive"]
    expected = canonical["clean_content_scheme_sensitive"]
    assert sensitive["v8_certification"]["certification_status"] == expected["certification_status"]
    assert sensitive["v8_certification"]["statistical_blocking_reasons"] == expected["statistical_blocking_reasons"]

    no_downstream = result["content_leakage_without_downstream_layers"]
    expected = canonical["content_leakage_without_downstream_layers"]
    assert no_downstream["v8_certification"]["certification_status"] == expected["certification_status"]
    assert no_downstream["settings"]["downstream_v7_assessment_run"] is expected["downstream_v7_assessment_run"] is False
    assert no_downstream["downstream_v7_assessment"] is None

    strict = result["strict_extrapolation"]
    expected = canonical["strict_extrapolation"]
    assert strict["v8_certification"]["certification_status"] == expected["certification_status"]
    assert strict["v8_certification"]["operational_status"] == expected["operational_status"]
    assert strict["v8_certification"]["warning_reasons"] == expected["warning_reasons"]
    ratios = _values_for_key(strict, "maximum_novelty_ratio")
    assert ratios and all(value == expected["maximum_novelty_ratio"] for value in ratios)

    omitted = result["omitted_content"]
    expected = canonical["omitted_content"]
    assert omitted["evaluation_content_provenance"] is None
    assert expected["content_provenance_is_null"] is True
    assert omitted["settings"]["downstream_v7_assessment_run"] is expected["downstream_v7_assessment_run"] is True
    assert omitted["v8_certification"]["certification_status"] == expected["certification_status"]

    assert canonical["aggregate_confidence_score_emitted"] is False
    assert all(value is False for value in receipt["claim_boundary"].values())
    assert all(value is False for value in receipt["frozen_submission_preservation"].values())
