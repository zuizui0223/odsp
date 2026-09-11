import json
from pathlib import Path

import pytest

pytest.importorskip("sklearn")

from odsp.forecast_assessment_v11_benchmark import run_forecast_assessment_v11_benchmark


RECEIPT = Path(__file__).resolve().parents[1] / "FORECAST_ASSESSMENT_V11_CHECKPOINT_VALIDATION_RECEIPT.json"


def _maximum_novelty_ratio(value):
    found = []

    def walk(obj):
        if isinstance(obj, dict):
            for key, item in obj.items():
                if key == "maximum_novelty_ratio":
                    found.append(item)
                walk(item)
        elif isinstance(obj, list):
            for item in obj:
                walk(item)

    walk(value)
    assert found
    return max(found)


def test_forecast_assessment_v11_first_green_receipt_replays():
    receipt = json.loads(RECEIPT.read_text())
    canonical = receipt["canonical_results"]
    result = run_forecast_assessment_v11_benchmark()

    assert result["passed"] is canonical["passed"] is True
    assert len(result["checks"]) == canonical["obligation_count"] == 19
    assert all(row["passed"] for row in result["checks"])

    clean = result["clean_checkpoints"]
    clean_audit = clean["evaluation_access_checkpoints"]
    clean_cert = clean["v11_certification"]
    expected = canonical["clean_checkpoints"]
    assert clean_audit["separation_category"] == expected["checkpoint_category"]
    assert clean_audit["checkpoint_count"] == expected["checkpoint_count"]
    assert clean_audit["matched_checkpoint_count"] == expected["matched_checkpoint_count"]
    assert clean_audit["mismatched_checkpoint_count"] == expected["mismatched_checkpoint_count"]
    assert clean_audit["checkpoint_order_strictly_increasing"] is expected["checkpoint_order_strictly_increasing"]
    assert clean_audit["terminal_checkpoint_present"] is expected["terminal_checkpoint_present"]
    assert (clean["downstream_v10_assessment"] is not None) is expected["downstream_v10_assessment_run"]
    assert clean_cert["certification_status"] == expected["certification_status"]
    assert clean_cert["operational_status"] == expected["operational_status"]
    assert clean_cert["provenance_blocking_reasons"] == expected["provenance_blocking_reasons"]
    assert clean_cert["statistical_blocking_reasons"] == expected["statistical_blocking_reasons"]
    assert clean_cert["warning_reasons"] == expected["warning_reasons"]

    mismatch = result["checkpoint_mismatch"]
    mismatch_audit = mismatch["evaluation_access_checkpoints"]
    mismatch_cert = mismatch["v11_certification"]
    expected = canonical["checkpoint_mismatch"]
    assert mismatch_audit["separation_category"] == expected["checkpoint_category"]
    assert mismatch_audit["checkpoint_count"] == expected["checkpoint_count"]
    assert mismatch_audit["matched_checkpoint_count"] == expected["matched_checkpoint_count"]
    assert mismatch_audit["mismatched_checkpoint_count"] == expected["mismatched_checkpoint_count"]
    assert mismatch_audit["checkpoint_order_strictly_increasing"] is expected["checkpoint_order_strictly_increasing"]
    assert mismatch_audit["terminal_checkpoint_present"] is expected["terminal_checkpoint_present"]
    assert (mismatch["downstream_v10_assessment"] is not None) is expected["downstream_v10_assessment_run"]
    assert mismatch_cert["certification_status"] == expected["certification_status"]
    assert mismatch_cert["operational_status"] == expected["operational_status"]
    assert mismatch_cert["provenance_blocking_reasons"] == expected["provenance_blocking_reasons"]
    assert mismatch_cert["statistical_blocking_reasons"] == expected["statistical_blocking_reasons"]

    inherited = {
        "clean_checkpoints_log_chain_mismatch": "provenance_blocking_reasons",
        "clean_checkpoints_binding_mismatch": "provenance_blocking_reasons",
        "clean_checkpoints_content_leakage": "provenance_blocking_reasons",
        "clean_checkpoints_selection_leakage": "provenance_blocking_reasons",
        "clean_checkpoints_training_leakage": "provenance_blocking_reasons",
        "clean_checkpoints_row_mismatch": "provenance_blocking_reasons",
        "clean_checkpoints_scheme_sensitive": "statistical_blocking_reasons",
    }
    for key, reasons_key in inherited.items():
        cert = result[key]["v11_certification"]
        expected = canonical[key]
        assert cert["certification_status"] == expected["certification_status"]
        assert cert[reasons_key] == expected[reasons_key]

    prior = result["prior_v10_failure_with_checkpoint_mismatch"]
    prior_cert = prior["v11_certification"]
    expected = canonical["prior_v10_failure_with_checkpoint_mismatch"]
    assert prior_cert["certification_status"] == expected["certification_status"]
    assert prior_cert["operational_status"] == expected["operational_status"]
    assert prior_cert["provenance_blocking_reasons"] == expected["provenance_blocking_reasons"]
    assert prior_cert["statistical_blocking_reasons"] == expected["statistical_blocking_reasons"]
    assert (prior["downstream_v10_assessment"] is not None) is expected["downstream_v10_assessment_run"]

    lowerless = result["checkpoint_mismatch_without_lower_layers"]
    lowerless_cert = lowerless["v11_certification"]
    expected = canonical["checkpoint_mismatch_without_lower_layers"]
    assert lowerless_cert["certification_status"] == expected["certification_status"]
    assert lowerless_cert["provenance_blocking_reasons"] == expected["provenance_blocking_reasons"]
    assert (lowerless["downstream_v10_assessment"] is not None) is expected["downstream_v10_assessment_run"]

    strict = result["strict_extrapolation"]
    strict_cert = strict["v11_certification"]
    expected = canonical["strict_extrapolation"]
    assert strict_cert["certification_status"] == expected["certification_status"]
    assert strict_cert["operational_status"] == expected["operational_status"]
    assert strict_cert["warning_reasons"] == expected["warning_reasons"]
    assert _maximum_novelty_ratio(strict) == expected["maximum_novelty_ratio"]

    omitted = result["omitted_checkpoints"]
    expected = canonical["omitted_checkpoints"]
    assert (omitted["evaluation_access_checkpoints"] is None) is expected["checkpoint_audit_is_null"]
    assert (omitted["downstream_v10_assessment"] is not None) is expected["downstream_v10_assessment_run"]
    assert omitted["v11_certification"]["certification_status"] == expected["certification_status"]

    assert canonical["aggregate_confidence_score_emitted"] is False
    assert all(not row["aggregate_confidence_score_emitted"] for row in (
        clean,
        mismatch,
        prior,
        result["clean_checkpoints_log_chain_mismatch"],
        result["clean_checkpoints_binding_mismatch"],
        result["clean_checkpoints_content_leakage"],
        result["clean_checkpoints_selection_leakage"],
        result["clean_checkpoints_training_leakage"],
        result["clean_checkpoints_row_mismatch"],
        result["clean_checkpoints_scheme_sensitive"],
        lowerless,
        strict,
        omitted,
    ))

    assert all(value is False for value in receipt["claim_boundary"].values())
    assert all(value is False for value in receipt["frozen_submission_preservation"].values())
