import json
from pathlib import Path

import pytest

pytest.importorskip("sklearn")

from odsp.forecast_assessment_v6_benchmark import run_forecast_assessment_v6_benchmark


ROOT = Path(__file__).resolve().parents[1]


def test_forecast_assessment_v6_receipt_replays():
    receipt = json.loads(
        (ROOT / "FORECAST_ASSESSMENT_V6_SELECTION_PROVENANCE_VALIDATION_RECEIPT.json").read_text(
            encoding="utf-8"
        )
    )
    result = run_forecast_assessment_v6_benchmark(seed=20260907)
    canonical = receipt["canonical_results"]

    assert result["passed"] is canonical["passed"] is True
    assert len(result["checks"]) == canonical["obligation_count"] == 15
    assert all(row["passed"] for row in result["checks"])

    clean = result["clean_selection"]
    expected = canonical["clean_selection"]
    assert clean["selection_validation_provenance"]["separation_category"] == expected["selection_category"]
    assert clean["settings"]["downstream_v5_assessment_run"] is expected["downstream_v5_assessment_run"] is True
    assert clean["v6_certification"]["certification_status"] == expected["certification_status"]
    assert clean["v6_certification"]["operational_status"] == expected["operational_status"]
    assert clean["v6_certification"]["provenance_blocking_reasons"] == expected["provenance_blocking_reasons"]
    assert clean["v6_certification"]["statistical_blocking_reasons"] == expected["statistical_blocking_reasons"]
    assert clean["v6_certification"]["warning_reasons"] == expected["warning_reasons"]

    leaked = result["selection_leakage"]
    expected = canonical["selection_leakage"]
    assert leaked["selection_validation_provenance"]["separation_category"] == expected["selection_category"]
    assert leaked["settings"]["downstream_v5_assessment_run"] is expected["downstream_v5_assessment_run"] is False
    assert leaked["downstream_v5_assessment"] is None
    assert leaked["v6_certification"]["certification_status"] == expected["certification_status"]
    assert leaked["v6_certification"]["operational_status"] == expected["operational_status"]
    assert leaked["v6_certification"]["provenance_blocking_reasons"] == expected["provenance_blocking_reasons"]
    assert leaked["v6_certification"]["statistical_blocking_reasons"] == expected["statistical_blocking_reasons"]
    assert leaked["v6_certification"]["training_validation_provenance_status"] == expected["training_validation_provenance_status"]
    assert leaked["v6_certification"]["heldout_row_provenance_status"] == expected["heldout_row_provenance_status"]

    prior = result["prior_v5_failure_with_selection_leakage"]
    expected = canonical["prior_v5_failure_with_selection_leakage"]
    assert prior["v6_certification"]["certification_status"] == expected["certification_status"]
    assert prior["v6_certification"]["operational_status"] == expected["operational_status"]
    assert prior["v6_certification"]["provenance_blocking_reasons"] == expected["provenance_blocking_reasons"]
    assert prior["v6_certification"]["statistical_blocking_reasons"] == expected["statistical_blocking_reasons"]
    assert prior["downstream_v5_assessment"] is None

    for result_key, receipt_key, reason_field in (
        ("clean_selection_training_leakage", "clean_selection_training_leakage", "provenance_blocking_reasons"),
        ("clean_selection_row_mismatch", "clean_selection_row_mismatch", "provenance_blocking_reasons"),
        ("clean_selection_scheme_sensitive", "clean_selection_scheme_sensitive", "statistical_blocking_reasons"),
    ):
        row = result[result_key]
        expected = canonical[receipt_key]
        assert row["v6_certification"]["certification_status"] == expected["certification_status"]
        assert row["v6_certification"][reason_field] == expected[reason_field]

    no_scheme = result["selection_leakage_without_scheme"]
    expected = canonical["selection_leakage_without_scheme"]
    assert no_scheme["v6_certification"]["certification_status"] == expected["certification_status"]
    assert no_scheme["settings"]["downstream_v5_assessment_run"] is expected["downstream_v5_assessment_run"] is False
    assert no_scheme["downstream_v5_assessment"] is None

    strict = result["strict_extrapolation"]
    expected = canonical["strict_extrapolation"]
    assert strict["v6_certification"]["certification_status"] == expected["certification_status"]
    assert strict["v6_certification"]["operational_status"] == expected["operational_status"]
    assert strict["v6_certification"]["warning_reasons"] == expected["warning_reasons"]

    omitted = result["omitted_selection"]
    expected = canonical["omitted_selection"]
    assert omitted["selection_validation_provenance"] is None
    assert expected["selection_provenance_is_null"] is True
    assert omitted["settings"]["downstream_v5_assessment_run"] is expected["downstream_v5_assessment_run"] is True
    assert omitted["v6_certification"]["certification_status"] == expected["certification_status"]

    block = result["block_definition_warning"]
    expected = canonical["block_definition_warning"]
    assert block["v6_certification"]["certification_status"] == expected["certification_status"]
    assert block["v6_certification"]["operational_status"] == expected["operational_status"]
    assert block["v6_certification"]["warning_reasons"] == expected["warning_reasons"]

    assert canonical["aggregate_confidence_score_emitted"] is False
    assert all(value is False for value in receipt["claim_boundary"].values())
    assert all(value is False for value in receipt["frozen_submission_preservation"].values())
    repair = receipt["pre_green_fixture_repair"]
    assert repair["contract_modified"] is False
    assert repair["decision_rule_modified"] is False
    assert repair["threshold_modified"] is False
