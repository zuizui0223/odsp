import json
from pathlib import Path

import pytest

pytest.importorskip("sklearn")

from odsp.forecast_assessment_v5_benchmark import run_forecast_assessment_v5_benchmark


ROOT = Path(__file__).resolve().parents[1]


def _scheme_row(scheme_audit: dict[str, object], name: str) -> dict[str, object]:
    return next(row for row in scheme_audit["schemes"] if row["scheme_name"] == name)


def test_forecast_assessment_v5_receipt_replays():
    receipt = json.loads(
        (ROOT / "FORECAST_ASSESSMENT_V5_TRAINING_PROVENANCE_VALIDATION_RECEIPT.json").read_text(
            encoding="utf-8"
        )
    )
    result = run_forecast_assessment_v5_benchmark(seed=20260907)
    canonical = receipt["canonical_results"]

    assert result["passed"] is canonical["passed"] is True
    assert len(result["checks"]) == canonical["obligation_count"] == 15
    assert all(row["passed"] for row in result["checks"])

    clean = result["clean_exact"]
    expected = canonical["clean_exact"]
    provenance = clean["training_validation_provenance"]
    qualified = clean["provenance_qualified_v4_assessment"]
    aligned = qualified["aligned_refit_scheme_audit"]
    scheme = aligned["scheme_audit"]
    assert clean["base_v4_assessment"]["v4_certification"]["certification_status"] == expected["base_v4_certification_status"]
    assert clean["v5_certification"]["certification_status"] == expected["v5_certification_status"]
    assert clean["v5_certification"]["operational_status"] == expected["operational_status"]
    assert provenance["separation_category"] == expected["training_validation_category"]
    assert provenance["scheme_count"] == expected["training_scheme_count"]
    assert provenance["refit_count"] == expected["training_refit_count"]
    assert provenance["overlapping_refit_count"] == expected["overlapping_refit_count"]
    assert provenance["affected_scheme_count"] == expected["affected_scheme_count"]
    assert provenance["unique_overlapping_validation_row_count"] == expected["unique_overlapping_validation_row_count"]
    assert qualified["v4_certification"]["row_provenance_status"] == expected["heldout_row_provenance_status"]
    assert aligned["status"] == expected["aligned_scheme_audit_status"]
    assert aligned["scheme_sensitivity_category"] == expected["aligned_scheme_category"]
    assert scheme["minimum_nested_max_t_lower_bound"] == pytest.approx(expected["minimum_nested_max_t_lower_bound"], abs=1e-15)
    assert scheme["maximum_nested_max_t_upper_bound"] == pytest.approx(expected["maximum_nested_max_t_upper_bound"], abs=1e-15)
    assert scheme["minimum_scheme_mean_gain"] == pytest.approx(expected["minimum_scheme_mean_gain"], abs=1e-15)
    assert scheme["maximum_scheme_mean_gain"] == pytest.approx(expected["maximum_scheme_mean_gain"], abs=1e-15)

    permuted = result["clean_permuted"]
    expected = canonical["clean_permuted"]
    permuted_qualified = permuted["provenance_qualified_v4_assessment"]
    permuted_aligned = permuted_qualified["aligned_refit_scheme_audit"]
    assert permuted["v5_certification"]["certification_status"] == expected["v5_certification_status"]
    assert permuted_qualified["v4_certification"]["row_provenance_status"] == expected["heldout_row_provenance_status"]
    assert permuted_aligned["status"] == expected["aligned_scheme_audit_status"]
    assert permuted_aligned["reordered_scheme_count"] == expected["reordered_scheme_count"]
    assert permuted_aligned["scheme_audit"] == aligned["scheme_audit"]
    assert expected["reproduces_clean_exact_scheme_audit"] is True

    leakage = result["training_leakage"]
    expected = canonical["training_leakage"]
    leakage_provenance = leakage["training_validation_provenance"]
    assert leakage["base_v4_assessment"]["v4_certification"]["certification_status"] == expected["base_v4_certification_status"]
    assert leakage["v5_certification"]["certification_status"] == expected["v5_certification_status"]
    assert leakage["v5_certification"]["operational_status"] == expected["operational_status"]
    assert leakage_provenance["separation_category"] == expected["training_validation_category"]
    assert leakage_provenance["overlapping_refit_count"] == expected["overlapping_refit_count"]
    assert leakage_provenance["affected_scheme_count"] == expected["affected_scheme_count"]
    assert leakage_provenance["unique_overlapping_validation_row_count"] == expected["unique_overlapping_validation_row_count"]
    assert leakage_provenance["maximum_refit_overlap_count"] == expected["maximum_refit_overlap_count"]
    assert leakage["provenance_qualified_v4_assessment"] is None
    assert expected["provenance_qualified_v4_assessment_is_null"] is True
    assert leakage["settings"]["downstream_v4_scheme_assessment_run"] is expected["downstream_v4_scheme_assessment_run"] is False
    assert leakage["v5_certification"]["provenance_blocking_reasons"] == expected["provenance_blocking_reasons"]
    assert not any(reason.startswith("refit_scheme") for reason in leakage["v5_certification"]["statistical_blocking_reasons"])
    assert expected["refit_scheme_statistical_blocker_added"] is False

    mismatch = result["clean_row_mismatch"]
    expected = canonical["clean_row_mismatch"]
    mismatch_qualified = mismatch["provenance_qualified_v4_assessment"]
    assert mismatch["v5_certification"]["certification_status"] == expected["v5_certification_status"]
    assert mismatch["training_validation_provenance"]["separation_category"] == expected["training_validation_category"]
    assert mismatch["v5_certification"]["heldout_row_provenance_status"] == expected["heldout_row_provenance_status"]
    assert mismatch_qualified["aligned_refit_scheme_audit"]["status"] == expected["aligned_scheme_audit_status"]
    assert mismatch["v5_certification"]["provenance_blocking_reasons"] == expected["provenance_blocking_reasons"]

    sensitive = result["clean_scheme_sensitive"]
    expected = canonical["clean_scheme_sensitive"]
    sensitive_scheme = sensitive["provenance_qualified_v4_assessment"]["aligned_refit_scheme_audit"]["scheme_audit"]
    seed_row = _scheme_row(sensitive_scheme, "seed")
    assert sensitive["v5_certification"]["certification_status"] == expected["v5_certification_status"]
    assert sensitive_scheme["sensitivity_category"] == expected["aligned_scheme_category"]
    assert sensitive_scheme["minimum_nested_max_t_lower_bound"] == pytest.approx(expected["minimum_nested_max_t_lower_bound"], abs=1e-15)
    assert sensitive["v5_certification"]["statistical_blocking_reasons"] == expected["statistical_blocking_reasons"]
    assert seed_row["ensemble_mean_gain"] == pytest.approx(expected["seed_ensemble_mean_gain"], abs=1e-15)
    assert seed_row["reference_fit_category"] == expected["seed_reference_fit_category"]
    assert seed_row["refit_aware_category"] == expected["seed_refit_aware_category"]

    prior = result["prior_v4_failure_with_leakage"]
    expected = canonical["prior_v4_failure_with_leakage"]
    assert prior["base_v4_assessment"]["v4_certification"]["certification_status"] == expected["base_v4_certification_status"]
    assert prior["v5_certification"]["certification_status"] == expected["v5_certification_status"]
    assert prior["v5_certification"]["statistical_blocking_reasons"] == expected["statistical_blocking_reasons"]
    assert prior["v5_certification"]["provenance_blocking_reasons"] == expected["provenance_blocking_reasons"]
    assert prior["provenance_qualified_v4_assessment"] is None
    assert expected["provenance_qualified_v4_assessment_is_null"] is True

    strict = result["strict_extrapolation"]
    expected = canonical["strict_extrapolation"]
    deployment = strict["provenance_qualified_v4_assessment"]["base_v3_assessment"]["base_v2_assessment"]["base_assessment"]["dossier"]["deployment"]
    assert strict["v5_certification"]["certification_status"] == expected["v5_certification_status"]
    assert strict["v5_certification"]["operational_status"] == expected["operational_status"]
    assert strict["v5_certification"]["warning_reasons"] == expected["warning_reasons"]
    assert deployment["strict_extrapolation_fraction"] == pytest.approx(expected["strict_extrapolation_fraction"], abs=1e-15)
    assert deployment["novel_fraction"] == pytest.approx(expected["novel_fraction"], abs=1e-15)
    assert deployment["maximum_novelty_ratio"] == pytest.approx(expected["maximum_novelty_ratio"], abs=1e-15)

    omitted = result["omitted_scheme"]
    expected = canonical["omitted_scheme"]
    assert omitted["v5_certification"]["certification_status"] == expected["v5_certification_status"]
    assert omitted["training_validation_provenance"] is None
    assert omitted["provenance_qualified_v4_assessment"] is None
    assert expected["training_validation_provenance_is_null"] is True
    assert expected["provenance_qualified_v4_assessment_is_null"] is True
    checks = {row["name"]: row["passed"] for row in result["checks"]}
    assert checks["omitted_scheme_layer_preserves_base_v4_result_and_certification"] is expected["preserves_direct_v4_omitted_result"] is True

    scheme_only = result["scheme_only"]
    expected = canonical["scheme_only"]
    assert scheme_only["base_v4_assessment"]["v4_certification"]["certification_status"] == expected["base_v4_certification_status"]
    assert scheme_only["v5_certification"]["certification_status"] == expected["v5_certification_status"]
    assert scheme_only["training_validation_provenance"]["separation_category"] == expected["training_validation_category"]

    block = result["block_definition_warning"]
    expected = canonical["block_definition_warning"]
    block_audit = block["provenance_qualified_v4_assessment"]["base_v3_assessment"]["base_v2_assessment"]["block_definition_audit"]
    definitions = {row["name"]: row for row in block_audit["definitions"]}
    assert block["v5_certification"]["certification_status"] == expected["v5_certification_status"]
    assert block["v5_certification"]["operational_status"] == expected["operational_status"]
    assert block["v5_certification"]["warning_reasons"] == expected["warning_reasons"]
    assert block_audit["sensitivity_category"] == expected["block_definition_category"]
    assert block_audit["group_status_flip_count"] == expected["group_status_flip_count"]
    assert definitions["primary"]["minimum_group_lower_bound"] == pytest.approx(expected["primary_minimum_group_lower_bound"], abs=1e-15)
    assert definitions["eight_cluster"]["minimum_group_lower_bound"] == pytest.approx(expected["eight_cluster_minimum_group_lower_bound"], abs=1e-15)

    assert canonical["aggregate_confidence_score_emitted"] is False
    assert all(value is False for value in receipt["claim_boundary"].values())
    assert all(value is False for value in receipt["frozen_v4_submission_boundary"].values())
    assert receipt["pre_green_diagnostic"]["benchmark_ran"] is False
    assert receipt["pre_green_diagnostic"]["contract_modified_after_failure"] is False
    assert receipt["pre_green_diagnostic"]["v5_api_modified_after_failure"] is False
    assert receipt["pre_green_diagnostic"]["known_truth_benchmark_modified_after_failure"] is False
    assert receipt["pre_green_diagnostic"]["benchmark_thresholds_modified_after_failure"] is False
