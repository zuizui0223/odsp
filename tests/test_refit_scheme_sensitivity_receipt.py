import json
from pathlib import Path

import pytest

from odsp.refit_scheme_sensitivity_benchmark import run_refit_scheme_sensitivity_benchmark

ROOT=Path(__file__).resolve().parents[1]


def test_refit_scheme_sensitivity_receipt_replays_first_green_result():
    receipt=json.loads((ROOT/"REFIT_SCHEME_SENSITIVITY_VALIDATION_RECEIPT.json").read_text(encoding="utf-8"))
    result=run_refit_scheme_sensitivity_benchmark(seed=20260907,nested_draws=2500)
    canonical=receipt["canonical_results"]
    assert result["passed"] is True
    assert len(result["checks"])==canonical["obligation_count"]==12

    stable=result["stable_positive"]
    expected=canonical["stable_positive"]
    assert stable["sensitivity_category"]==expected["sensitivity_category"]
    assert stable["scheme_category_set"]==expected["scheme_category_set"]
    assert stable["minimum_scheme_mean_gain"]==pytest.approx(expected["minimum_scheme_mean_gain"],abs=1e-15)
    assert stable["maximum_scheme_mean_gain"]==pytest.approx(expected["maximum_scheme_mean_gain"],abs=1e-15)
    assert stable["minimum_nested_max_t_lower_bound"]==pytest.approx(expected["minimum_nested_max_t_lower_bound"],abs=1e-15)

    negative=result["stable_negative"]
    expected_neg=canonical["stable_negative"]
    assert negative["sensitivity_category"]==expected_neg["sensitivity_category"]
    assert negative["maximum_nested_max_t_upper_bound"]==pytest.approx(expected_neg["maximum_nested_max_t_upper_bound"],abs=1e-15)

    sensitive=result["scheme_sensitive"]
    expected_s=canonical["scheme_sensitive"]
    assert sensitive["sensitivity_category"]==expected_s["sensitivity_category"]
    assert sensitive["scheme_category_set"]==expected_s["scheme_category_set"]
    assert sensitive["point_category_set"]==expected_s["point_category_set"]
    assert sensitive["minimum_nested_max_t_lower_bound"]==pytest.approx(expected_s["minimum_nested_max_t_lower_bound"],abs=1e-15)
    by_name={row["scheme_name"]:row for row in sensitive["schemes"]}
    assert by_name["bootstrap"]["refit_aware_category"]==expected_s["bootstrap_category"]
    assert by_name["fold"]["refit_aware_category"]==expected_s["fold_category"]
    assert by_name["seed"]["refit_aware_category"]==expected_s["seed_category"]
    assert by_name["seed"]["reference_fit_category"]==expected_s["seed_reference_fit_category"]
    assert by_name["seed"]["refit_sign_stability"]==expected_s["seed_refit_sign_stability"]

    unavailable=result["one_unavailable_scheme"]
    assert unavailable["sensitivity_category"]==canonical["one_unavailable_scheme"]["sensitivity_category"]
    assert unavailable["unavailable_scheme_count"]==1
    assert result["scheme_order_error"]==pytest.approx(canonical["scheme_order_error"],abs=1e-15)
    assert result["row_order_error"]==pytest.approx(canonical["row_order_error"],abs=1e-15)
    assert result["positive_global_weight_scaling_error"]==pytest.approx(canonical["positive_global_weight_scaling_error"],abs=1e-15)
    assert receipt["claim_boundary"]["scheme_stability_identifies_correct_training_resampling_scheme"] is False
    assert receipt["frozen_v4_preservation"]["closed_empirical_endpoint_reopened"] is False
