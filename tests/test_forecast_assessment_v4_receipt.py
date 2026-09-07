import json
from pathlib import Path

import pytest

pytest.importorskip("sklearn")

from odsp.forecast_assessment_v4_benchmark import run_forecast_assessment_v4_benchmark


ROOT = Path(__file__).resolve().parents[1]


def _bad_source(result):
    return next(
        row
        for row in result["aligned_refit_scheme_audit"]["row_alignment"]["sources"]
        if row["status"] == "row_mismatch"
    )


def _scheme_row(audit, name):
    return next(row for row in audit["schemes"] if row["scheme_name"] == name)


def test_forecast_assessment_v4_receipt_replays():
    receipt = json.loads(
        (ROOT / "FORECAST_ASSESSMENT_V4_PROVENANCE_VALIDATION_RECEIPT.json").read_text(
            encoding="utf-8"
        )
    )
    result = run_forecast_assessment_v4_benchmark(seed=20260907)
    canonical = receipt["canonical_results"]

    assert result["passed"] is canonical["passed"] is True
    assert len(result["checks"]) == canonical["obligation_count"] == 13
    assert all(row["passed"] for row in result["checks"])

    strong = result["strong_exact"]
    expected = canonical["strong_exact"]
    cert = strong["v4_certification"]
    aligned = strong["aligned_refit_scheme_audit"]
    scheme = aligned["scheme_audit"]
    assert strong["base_v3_assessment"]["v3_certification"]["certification_status"] == expected["base_v3_certification_status"]
    assert cert["certification_status"] == expected["certification_status"]
    assert cert["operational_status"] == expected["operational_status"]
    assert cert["row_provenance_status"] == expected["row_provenance_status"]
    assert aligned["status"] == expected["aligned_scheme_audit_status"]
    assert aligned["scheme_sensitivity_category"] == expected["aligned_scheme_category"]
    assert aligned["reordered_scheme_count"] == expected["reordered_scheme_count"]
    assert scheme["minimum_nested_max_t_lower_bound"] == pytest.approx(expected["minimum_nested_max_t_lower_bound"], abs=1e-15)
    assert scheme["maximum_nested_max_t_upper_bound"] == pytest.approx(expected["maximum_nested_max_t_upper_bound"], abs=1e-15)
    assert scheme["minimum_scheme_mean_gain"] == pytest.approx(expected["minimum_scheme_mean_gain"], abs=1e-15)
    assert scheme["maximum_scheme_mean_gain"] == pytest.approx(expected["maximum_scheme_mean_gain"], abs=1e-15)

    permuted = result["strong_permuted"]
    expected = canonical["strong_permuted"]
    cert = permuted["v4_certification"]
    aligned = permuted["aligned_refit_scheme_audit"]
    assert cert["certification_status"] == expected["certification_status"]
    assert cert["operational_status"] == expected["operational_status"]
    assert cert["row_provenance_status"] == expected["row_provenance_status"]
    assert aligned["status"] == expected["aligned_scheme_audit_status"]
    assert aligned["scheme_sensitivity_category"] == expected["aligned_scheme_category"]
    assert aligned["reordered_scheme_count"] == expected["reordered_scheme_count"]
    assert aligned["scheme_audit"] == result["strong_exact"]["aligned_refit_scheme_audit"]["scheme_audit"]
    assert permuted["aligned_v3_certification"] == result["strong_exact"]["aligned_v3_certification"]

    mismatch = result["row_mismatch"]
    expected = canonical["row_mismatch"]
    cert = mismatch["v4_certification"]
    aligned = mismatch["aligned_refit_scheme_audit"]
    bad = _bad_source(mismatch)
    assert mismatch["base_v3_assessment"]["v3_certification"]["certification_status"] == expected["base_v3_certification_status"]
    assert cert["certification_status"] == expected["certification_status"]
    assert cert["operational_status"] == expected["operational_status"]
    assert cert["row_provenance_status"] == expected["row_provenance_status"]
    assert cert["provenance_blocking_reasons"] == expected["provenance_blocking_reasons"]
    assert cert["statistical_blocking_reasons"] == expected["statistical_blocking_reasons"]
    assert aligned["status"] == expected["aligned_scheme_audit_status"]
    assert aligned["scheme_sensitivity_category"] == expected["aligned_scheme_category"]
    assert aligned["statistical_audit_run"] is expected["statistical_audit_run"] is False
    assert aligned["scheme_audit"] is None
    assert expected["scheme_audit_is_null"] is True
    assert bad["source_name"] == expected["bad_scheme"]
    assert bad["missing_row_count"] == expected["missing_row_count"]
    assert bad["extra_row_count"] == expected["extra_row_count"]
    assert bad["duplicate_row_id_count"] == expected["duplicate_row_id_count"]

    sensitive = result["scheme_sensitive"]
    expected = canonical["scheme_sensitive"]
    cert = sensitive["v4_certification"]
    scheme = sensitive["aligned_refit_scheme_audit"]["scheme_audit"]
    seed_row = _scheme_row(scheme, "seed")
    assert sensitive["base_v3_assessment"]["v3_certification"]["certification_status"] == expected["base_v3_certification_status"]
    assert cert["certification_status"] == expected["certification_status"]
    assert cert["operational_status"] == expected["operational_status"]
    assert cert["row_provenance_status"] == expected["row_provenance_status"]
    assert sensitive["aligned_refit_scheme_audit"]["scheme_sensitivity_category"] == expected["aligned_scheme_category"]
    assert scheme["scheme_category_set"] == expected["scheme_category_set"]
    assert scheme["point_category_set"] == expected["point_category_set"]
    assert seed_row["refit_aware_category"] == expected["seed_refit_aware_category"]
    assert seed_row["reference_fit_category"] == expected["seed_reference_fit_category"]
    assert seed_row["refit_sign_stability"] == expected["seed_refit_sign_stability"]
    assert seed_row["ensemble_mean_gain"] == pytest.approx(expected["seed_ensemble_mean_gain"], abs=1e-15)
    assert seed_row["minimum_nested_max_t_lower_bound"] == pytest.approx(expected["seed_minimum_nested_max_t_lower_bound"], abs=1e-15)
    assert seed_row["maximum_nested_max_t_upper_bound"] == pytest.approx(expected["seed_maximum_nested_max_t_upper_bound"], abs=1e-15)
    assert cert["statistical_blocking_reasons"] == expected["statistical_blocking_reasons"]
    assert cert["provenance_blocking_reasons"] == expected["provenance_blocking_reasons"]

    prior = result["prior_v3_failure"]
    expected = canonical["prior_v3_failure"]
    cert = prior["v4_certification"]
    assert prior["base_v3_assessment"]["v3_certification"]["certification_status"] == expected["base_v3_certification_status"]
    assert prior["base_v3_assessment"]["base_v2_assessment"]["model_refit_audit"]["refit_aware_category"] == expected["base_model_refit_category"]
    assert cert["certification_status"] == expected["certification_status"]
    assert cert["operational_status"] == expected["operational_status"]
    assert cert["row_provenance_status"] == expected["row_provenance_status"]
    assert cert["statistical_blocking_reasons"] == expected["statistical_blocking_reasons"]
    assert cert["provenance_blocking_reasons"] == expected["provenance_blocking_reasons"]

    strict = result["strict_extrapolation"]
    expected = canonical["strict_extrapolation"]
    cert = strict["v4_certification"]
    deployment = strict["base_v3_assessment"]["base_v2_assessment"]["base_assessment"]["dossier"]["deployment"]
    assert cert["certification_status"] == expected["certification_status"]
    assert cert["operational_status"] == expected["operational_status"]
    assert cert["row_provenance_status"] == expected["row_provenance_status"]
    assert strict["aligned_refit_scheme_audit"]["scheme_sensitivity_category"] == expected["aligned_scheme_category"]
    assert deployment["status"] == expected["deployment_status"]
    assert deployment["strict_extrapolation_fraction"] == pytest.approx(expected["strict_extrapolation_fraction"], abs=1e-15)
    assert deployment["novel_fraction"] == pytest.approx(expected["novel_fraction"], abs=1e-15)
    assert deployment["maximum_novelty_ratio"] == pytest.approx(expected["maximum_novelty_ratio"], abs=1e-15)
    assert cert["warning_reasons"] == expected["warning_reasons"]

    omitted = result["omitted_scheme"]
    expected = canonical["omitted_scheme"]
    assert omitted["aligned_refit_scheme_audit"] is None
    assert expected["aligned_scheme_audit_is_null"] is True
    assert omitted["v4_certification"]["row_provenance_status"] == expected["row_provenance_status"]
    assert omitted["base_v3_assessment"]["v3_certification"]["certification_status"] == expected["base_v3_certification_status"]
    assert omitted["v4_certification"]["certification_status"] == expected["certification_status"]
    assert omitted["v4_certification"]["operational_status"] == expected["operational_status"]

    scheme_only = result["scheme_only"]
    expected = canonical["scheme_only"]
    assert scheme_only["base_v3_assessment"]["v3_certification"]["certification_status"] == expected["base_v3_certification_status"]
    assert scheme_only["v4_certification"]["row_provenance_status"] == expected["row_provenance_status"]
    assert scheme_only["aligned_refit_scheme_audit"]["scheme_sensitivity_category"] == expected["aligned_scheme_category"]
    assert scheme_only["v4_certification"]["certification_status"] == expected["certification_status"]

    block = result["block_definition_warning"]
    expected = canonical["block_definition_warning"]
    block_audit = block["base_v3_assessment"]["base_v2_assessment"]["block_definition_audit"]
    by_name = {row["name"]: row for row in block_audit["definitions"]}
    assert block_audit["sensitivity_category"] == expected["block_definition_category"]
    assert block_audit["group_status_flip_count"] == expected["group_status_flip_count"]
    assert by_name["primary"]["minimum_group_lower_bound"] == pytest.approx(expected["primary_minimum_group_lower_bound"], abs=1e-15)
    assert by_name["eight_cluster"]["minimum_group_lower_bound"] == pytest.approx(expected["eight_cluster_minimum_group_lower_bound"], abs=1e-15)
    assert block["v4_certification"]["certification_status"] == expected["certification_status"]
    assert block["v4_certification"]["warning_reasons"] == expected["warning_reasons"]

    assert canonical["aggregate_confidence_score_emitted"] is False
    assert receipt["pre_green_diagnostic"]["known_truth_benchmark_ran_before_fix"] is False
    assert receipt["pre_green_diagnostic"]["contract_changed"] is False
    assert receipt["pre_green_diagnostic"]["decision_rule_changed"] is False
    assert receipt["pre_green_diagnostic"]["benchmark_generator_changed"] is False
    assert receipt["pre_green_diagnostic"]["threshold_changed"] is False
    assert all(value is False for value in receipt["claim_boundary"].values())
    assert all(value is False for value in receipt["frozen_v4_submission_preservation"].values())
