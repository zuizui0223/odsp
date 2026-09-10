import json
from pathlib import Path

import pytest

pytest.importorskip("sklearn")

from odsp.forecast_assessment_v7_benchmark import run_forecast_assessment_v7_benchmark


ROOT = Path(__file__).resolve().parents[1]


def test_forecast_assessment_v7_receipt_replays():
    receipt = json.loads(
        (ROOT / "FORECAST_ASSESSMENT_V7_EVALUATION_ACCESS_PROVENANCE_VALIDATION_RECEIPT.json").read_text(
            encoding="utf-8"
        )
    )
    result = run_forecast_assessment_v7_benchmark(seed=20260910)
    canonical = receipt["canonical_results"]

    assert result["passed"] is canonical["passed"] is True
    assert len(result["checks"]) == canonical["obligation_count"] == 15
    assert all(row["passed"] for row in result["checks"])

    clean = result["clean_access"]
    access = clean["evaluation_access_provenance"]
    assert access["stage_count"] == canonical["clean_access_stage_count"]
    assert access["separation_category"] == canonical["clean_access_category"]
    assert clean["v7_certification"]["certification_status"] == canonical["clean_certification_status"]
    assert clean["v7_certification"]["operational_status"] == canonical["clean_operational_status"]

    leaked = result["final_evaluation_access_leakage"]
    access = leaked["evaluation_access_provenance"]
    assert access["separation_category"] == canonical["access_leakage_category"]
    assert access["leaking_stage_count"] == canonical["access_leakage_stage_count"]
    assert access["final_evaluation_access_occurrence_count"] == canonical["access_leakage_occurrence_count"]
    assert access["maximum_stage_final_access_count"] == canonical["access_leakage_maximum_stage_count"]
    assert leaked["downstream_v6_assessment"] is None
    assert leaked["v7_certification"]["certification_status"] == canonical["access_leakage_certification_status"]
    assert leaked["v7_certification"]["operational_status"] == canonical["access_leakage_operational_status"]
    assert leaked["v7_certification"]["downstream_v6_status"] == canonical["access_leakage_downstream_v6_status"]
    assert leaked["v7_certification"]["provenance_blocking_reasons"] == canonical["access_leakage_provenance_blockers"]

    prior = result["prior_v6_failure_with_access_leakage"]
    assert prior["v7_certification"]["certification_status"] == canonical["prior_v6_failure_certification_status"]
    assert prior["v7_certification"]["statistical_blocking_reasons"] == canonical["prior_v6_failure_statistical_blockers"]

    assert result["clean_access_selection_leakage"]["v7_certification"]["provenance_blocking_reasons"] == canonical["clean_access_selection_leakage_provenance_blockers"]
    assert result["clean_access_training_leakage"]["v7_certification"]["provenance_blocking_reasons"] == canonical["clean_access_training_leakage_provenance_blockers"]
    assert result["clean_access_row_mismatch"]["v7_certification"]["provenance_blocking_reasons"] == canonical["clean_access_row_mismatch_provenance_blockers"]
    assert result["clean_access_scheme_sensitive"]["v7_certification"]["statistical_blocking_reasons"] == canonical["clean_access_scheme_sensitive_statistical_blockers"]

    strict = result["strict_extrapolation"]
    assert strict["v7_certification"]["warning_reasons"] == canonical["strict_extrapolation_warning_reasons"]
    maximum_novelty_ratio = strict["base_v6_assessment"]["base_v5_assessment"]["base_v4_assessment"]["base_v3_assessment"]["base_v2_assessment"]["base_assessment"]["dossier"]["deployment"]["maximum_novelty_ratio"]
    assert maximum_novelty_ratio == canonical["strict_extrapolation_maximum_novelty_ratio"]

    no_layers = result["access_leakage_without_selection_or_scheme"]
    assert no_layers["downstream_v6_assessment"] is None
    assert no_layers["v7_certification"]["certification_status"] == "unavailable"

    omitted = result["omitted_evaluation_access"]
    assert omitted["evaluation_access_provenance"] is None
    assert omitted["downstream_v6_assessment"] is not None
    assert omitted["v7_certification"]["evaluation_access_provenance_status"] == "not_audited"

    assert canonical["aggregate_confidence_score_emitted"] is False
    assert all(value is False for value in receipt["claim_boundary"].values())
    assert all(value is False for value in receipt["frozen_submission_preservation"].values())
