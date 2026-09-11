import json
from pathlib import Path

import pytest

pytest.importorskip("sklearn")

from odsp.forecast_assessment_v10_benchmark import run_forecast_assessment_v10_benchmark


RECEIPT = Path(__file__).resolve().parents[1] / "FORECAST_ASSESSMENT_V10_LOG_CHAIN_VALIDATION_RECEIPT.json"


def _maximum_novelty_ratio(payload):
    if isinstance(payload, dict):
        if "maximum_novelty_ratio" in payload:
            return payload["maximum_novelty_ratio"]
        for value in payload.values():
            found = _maximum_novelty_ratio(value)
            if found is not None:
                return found
    elif isinstance(payload, list):
        for value in payload:
            found = _maximum_novelty_ratio(value)
            if found is not None:
                return found
    return None


def test_forecast_assessment_v10_first_green_receipt_replays():
    receipt = json.loads(RECEIPT.read_text())
    canonical = receipt["canonical_results"]
    result = run_forecast_assessment_v10_benchmark(seed=20260911)

    assert result["passed"] is canonical["passed"] is True
    assert len(result["checks"]) == canonical["obligation_count"] == 18
    assert all(row["passed"] for row in result["checks"])

    clean = result["clean_log_chain"]
    clean_audit = clean["evaluation_access_log_chain"]
    clean_cert = clean["v10_certification"]
    expected = canonical["clean_log_chain"]
    assert clean_audit["separation_category"] == expected["log_chain_category"]
    for key in (
        "event_count",
        "stage_count",
        "committed_event_count_match",
        "terminal_event_hash_match",
        "sequence_contiguous",
        "previous_hash_chain_match",
        "recomputed_event_hash_match",
        "stage_artifact_id_ledger_match",
        "stage_digest_ledger_match",
        "mismatched_stage_count",
    ):
        assert clean_audit[key] == expected[key]
    assert clean["settings"]["downstream_v9_assessment_run"] == expected["downstream_v9_assessment_run"]
    assert clean_cert["certification_status"] == expected["certification_status"]
    assert clean_cert["operational_status"] == expected["operational_status"]
    assert clean_cert["provenance_blocking_reasons"] == expected["provenance_blocking_reasons"]
    assert clean_cert["statistical_blocking_reasons"] == expected["statistical_blocking_reasons"]
    assert clean_cert["warning_reasons"] == expected["warning_reasons"]

    mismatch = result["log_chain_mismatch"]
    mismatch_audit = mismatch["evaluation_access_log_chain"]
    mismatch_cert = mismatch["v10_certification"]
    expected = canonical["log_chain_mismatch"]
    assert mismatch_audit["separation_category"] == expected["log_chain_category"]
    for key in (
        "event_count",
        "stage_count",
        "committed_event_count_match",
        "terminal_event_hash_match",
        "sequence_contiguous",
        "previous_hash_chain_match",
        "recomputed_event_hash_match",
        "stage_artifact_id_ledger_match",
        "stage_digest_ledger_match",
        "mismatched_stage_count",
    ):
        assert mismatch_audit[key] == expected[key]
    assert mismatch["downstream_v9_assessment"] is None
    assert mismatch["settings"]["downstream_v9_assessment_run"] == expected["downstream_v9_assessment_run"]
    assert mismatch_cert["certification_status"] == expected["certification_status"]
    assert mismatch_cert["operational_status"] == expected["operational_status"]
    assert mismatch_cert["provenance_blocking_reasons"] == expected["provenance_blocking_reasons"]
    assert mismatch_cert["statistical_blocking_reasons"] == expected["statistical_blocking_reasons"]

    prior = result["prior_v9_failure_with_log_chain_mismatch"]["v10_certification"]
    expected = canonical["prior_v9_failure_with_log_chain_mismatch"]
    assert prior["certification_status"] == expected["certification_status"]
    assert prior["operational_status"] == expected["operational_status"]
    assert prior["provenance_blocking_reasons"] == expected["provenance_blocking_reasons"]
    assert prior["statistical_blocking_reasons"] == expected["statistical_blocking_reasons"]

    blocker_cases = (
        ("clean_log_chain_binding_mismatch", "provenance_blocking_reasons"),
        ("clean_log_chain_content_leakage", "provenance_blocking_reasons"),
        ("clean_log_chain_selection_leakage", "provenance_blocking_reasons"),
        ("clean_log_chain_training_leakage", "provenance_blocking_reasons"),
        ("clean_log_chain_row_mismatch", "provenance_blocking_reasons"),
        ("clean_log_chain_scheme_sensitive", "statistical_blocking_reasons"),
    )
    for case, blocker_key in blocker_cases:
        cert = result[case]["v10_certification"]
        expected = canonical[case]
        assert cert["certification_status"] == expected["certification_status"]
        assert cert[blocker_key] == expected[blocker_key]

    lower = result["log_chain_mismatch_without_lower_layers"]
    expected = canonical["log_chain_mismatch_without_lower_layers"]
    assert lower["downstream_v9_assessment"] is None
    assert lower["settings"]["downstream_v9_assessment_run"] == expected["downstream_v9_assessment_run"]
    assert lower["v10_certification"]["certification_status"] == expected["certification_status"]
    assert lower["v10_certification"]["provenance_blocking_reasons"] == expected["provenance_blocking_reasons"]

    strict = result["strict_extrapolation"]
    expected = canonical["strict_extrapolation"]
    assert strict["v10_certification"]["certification_status"] == expected["certification_status"]
    assert strict["v10_certification"]["operational_status"] == expected["operational_status"]
    assert strict["v10_certification"]["warning_reasons"] == expected["warning_reasons"]
    assert _maximum_novelty_ratio(strict) == expected["maximum_novelty_ratio"]

    omitted = result["omitted_log_chain"]
    expected = canonical["omitted_log_chain"]
    assert (omitted["evaluation_access_log_chain"] is None) == expected["log_chain_is_null"]
    assert omitted["settings"]["downstream_v9_assessment_run"] == expected["downstream_v9_assessment_run"]
    assert omitted["v10_certification"]["certification_status"] == expected["certification_status"]

    assert all(not result[key]["aggregate_confidence_score_emitted"] for key in result if isinstance(result[key], dict) and "aggregate_confidence_score_emitted" in result[key])
    assert canonical["aggregate_confidence_score_emitted"] is False

    for value in receipt["claim_boundary"].values():
        assert value is False
    for value in receipt["frozen_submission_preservation"].values():
        assert value is False
