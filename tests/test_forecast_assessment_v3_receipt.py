import json
from pathlib import Path

import pytest

pytest.importorskip("sklearn")

from odsp.forecast_assessment_v3_benchmark import run_forecast_assessment_v3_benchmark


ROOT = Path(__file__).resolve().parents[1]


def _scheme_row(audit, name):
    return next(row for row in audit["schemes"] if row["scheme_name"] == name)


def test_forecast_assessment_v3_receipt_replays():
    receipt = json.loads(
        (ROOT / "FORECAST_ASSESSMENT_V3_VALIDATION_RECEIPT.json").read_text(encoding="utf-8")
    )
    result = run_forecast_assessment_v3_benchmark(seed=20260907)
    canonical = receipt["canonical_results"]

    assert result["passed"] is canonical["passed"] is True
    assert len(result["checks"]) == canonical["obligation_count"] == 12
    assert all(row["passed"] for row in result["checks"])

    strong = result["strong"]
    expected = canonical["strong"]
    cert = strong["v3_certification"]
    audit = strong["refit_scheme_audit"]
    assert cert["base_validation_status"] == expected["base_validation_status"]
    assert cert["v2_certification_status"] == expected["v2_certification_status"]
    assert cert["certification_status"] == expected["certification_status"]
    assert cert["operational_status"] == expected["operational_status"]
    assert audit["sensitivity_category"] == expected["sensitivity_category"]
    assert audit["scheme_names"] == expected["scheme_names"]
    assert audit["scheme_category_set"] == expected["scheme_category_set"]
    assert audit["point_category_set"] == expected["point_category_set"]
    assert audit["unavailable_scheme_count"] == expected["unavailable_scheme_count"]
    assert audit["minimum_nested_max_t_lower_bound"] == pytest.approx(
        expected["minimum_nested_max_t_lower_bound"], abs=1e-15
    )
    assert audit["maximum_nested_max_t_upper_bound"] == pytest.approx(
        expected["maximum_nested_max_t_upper_bound"], abs=1e-15
    )
    assert audit["minimum_scheme_mean_gain"] == pytest.approx(
        expected["minimum_scheme_mean_gain"], abs=1e-15
    )
    assert audit["maximum_scheme_mean_gain"] == pytest.approx(
        expected["maximum_scheme_mean_gain"], abs=1e-15
    )

    sensitive = result["scheme_sensitive"]
    expected = canonical["scheme_sensitive"]
    cert = sensitive["v3_certification"]
    audit = sensitive["refit_scheme_audit"]
    seed_row = _scheme_row(audit, "seed")
    assert cert["v2_certification_status"] == expected["v2_certification_status"]
    assert cert["certification_status"] == expected["certification_status"]
    assert cert["operational_status"] == expected["operational_status"]
    assert cert["extended_blocking_reasons"] == expected["blocking_reasons"]
    assert audit["sensitivity_category"] == expected["sensitivity_category"]
    assert audit["scheme_category_set"] == expected["scheme_category_set"]
    assert audit["point_category_set"] == expected["point_category_set"]
    assert audit["minimum_nested_max_t_lower_bound"] == pytest.approx(
        expected["minimum_nested_max_t_lower_bound"], abs=1e-15
    )
    assert audit["maximum_nested_max_t_upper_bound"] == pytest.approx(
        expected["maximum_nested_max_t_upper_bound"], abs=1e-15
    )
    assert audit["minimum_scheme_mean_gain"] == pytest.approx(
        expected["minimum_scheme_mean_gain"], abs=1e-15
    )
    assert seed_row["refit_aware_category"] == expected["seed_refit_aware_category"]
    assert seed_row["minimum_nested_max_t_lower_bound"] == pytest.approx(
        expected["seed_minimum_nested_max_t_lower_bound"], abs=1e-15
    )
    assert seed_row["maximum_nested_max_t_upper_bound"] == pytest.approx(
        expected["seed_maximum_nested_max_t_upper_bound"], abs=1e-15
    )
    assert seed_row["ensemble_mean_gain"] == pytest.approx(
        expected["seed_ensemble_mean_gain"], abs=1e-15
    )

    unavailable = result["scheme_unavailable"]
    expected = canonical["scheme_unavailable"]
    assert unavailable["v3_certification"]["certification_status"] == expected["certification_status"]
    assert unavailable["v3_certification"]["operational_status"] == expected["operational_status"]
    assert unavailable["v3_certification"]["extended_blocking_reasons"] == expected["blocking_reasons"]
    assert unavailable["refit_scheme_audit"]["sensitivity_category"] == expected["sensitivity_category"]
    assert unavailable["refit_scheme_audit"]["unavailable_scheme_count"] == expected["unavailable_scheme_count"]

    prior = result["v2_already_not_certified"]
    expected = canonical["v2_already_not_certified"]
    assert prior["v3_certification"]["v2_certification_status"] == expected["v2_certification_status"]
    assert prior["refit_scheme_audit"]["sensitivity_category"] == expected["scheme_category"]
    assert prior["v3_certification"]["certification_status"] == expected["certification_status"]
    assert prior["v3_certification"]["operational_status"] == expected["operational_status"]
    assert prior["v3_certification"]["extended_blocking_reasons"] == expected["blocking_reasons"]

    strict = result["strict_extrapolation"]
    expected = canonical["strict_extrapolation"]
    cert = strict["v3_certification"]
    deployment = strict["base_v2_assessment"]["base_assessment"]["dossier"]["deployment"]
    assert cert["certification_status"] == expected["certification_status"]
    assert cert["operational_status"] == expected["operational_status"]
    assert cert["warning_reasons"] == expected["warning_reasons"]
    assert strict["refit_scheme_audit"]["sensitivity_category"] == expected["scheme_category"]
    assert deployment["status"] == expected["deployment_status"]
    assert deployment["strict_extrapolation_fraction"] == pytest.approx(
        expected["strict_extrapolation_fraction"], abs=1e-15
    )
    assert deployment["novel_fraction"] == pytest.approx(expected["novel_fraction"], abs=1e-15)

    omitted = result["omitted_scheme"]
    expected = canonical["omitted_scheme"]
    assert omitted["refit_scheme_audit"] is None
    assert expected["refit_scheme_audit_is_null"] is True
    assert omitted["v3_certification"]["v2_certification_status"] == expected["v2_certification_status"]
    assert omitted["v3_certification"]["refit_scheme_status"] == expected["refit_scheme_status"]
    assert omitted["v3_certification"]["certification_status"] == expected["certification_status"]

    scheme_only = result["scheme_only"]
    expected = canonical["scheme_only"]
    assert scheme_only["v3_certification"]["v2_certification_status"] == expected["v2_certification_status"]
    assert scheme_only["refit_scheme_audit"]["sensitivity_category"] == expected["scheme_category"]
    assert scheme_only["v3_certification"]["certification_status"] == expected["certification_status"]

    block = result["block_definition_warning"]
    expected = canonical["block_definition_warning"]
    block_audit = block["base_v2_assessment"]["block_definition_audit"]
    assert block_audit["sensitivity_category"] == expected["block_definition_category"]
    assert block_audit["group_status_flip_count"] == expected["group_status_flip_count"]
    assert block["refit_scheme_audit"]["sensitivity_category"] == expected["scheme_category"]
    assert block["v3_certification"]["certification_status"] == expected["certification_status"]
    assert block["v3_certification"]["operational_status"] == expected["operational_status"]
    assert block["v3_certification"]["warning_reasons"] == expected["warning_reasons"]

    assert canonical["base_v2_history_preserved_exactly"] is True
    assert canonical["aggregate_confidence_score_emitted"] is False
    assert receipt["claim_boundary"]["aggregate_confidence_score_emitted"] is False
    assert all(value is False for value in receipt["frozen_v4_preservation"].values())
