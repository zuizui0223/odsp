from __future__ import annotations

import json
import math
from pathlib import Path

from odsp.bounded_reweighting_robustness_benchmark import (
    run_bounded_reweighting_robustness_benchmark,
)

ROOT=Path(__file__).resolve().parents[1]


def _close(actual,expected,tol=1e-14):
    assert math.isclose(float(actual),float(expected),rel_tol=0.0,abs_tol=tol)


def test_bounded_reweighting_receipt_replays_frozen_benchmark():
    receipt=json.loads((ROOT/"BOUNDED_REWEIGHTING_ROBUSTNESS_VALIDATION_RECEIPT.json").read_text(encoding="utf-8"))
    assert receipt["receipt_id"]=="odsp-bounded-reweighting-robustness-v1-validation"
    result=run_bounded_reweighting_robustness_benchmark(gamma=receipt["benchmark_config"]["gamma"])
    assert result["passed"] is True
    assert all(row["passed"] for row in result["checks"])
    expected=receipt["canonical_results"]

    for key,source in [
        ("all_positive","all_positive"),
        ("all_negative","all_negative"),
    ]:
        actual=result[source]
        recorded=expected[key]
        assert actual["point_transfer_category"]==recorded["point_transfer_category"]
        assert actual["envelope_transfer_category"]==recorded["envelope_transfer_category"]
        _close(actual["minimum_worst_case_group_gain"],recorded["minimum_worst_case_group_gain"])
        _close(actual["maximum_best_case_group_gain"],recorded["maximum_best_case_group_gain"])

    mixed1=result["mixed_sign_gamma_1"]
    mixed2=result["mixed_sign_primary_gamma"]
    rec=expected["mixed_sign"]
    assert mixed1["envelope_transfer_category"]==rec["gamma_1"]["envelope_transfer_category"]
    assert mixed2["envelope_transfer_category"]==rec["gamma_2"]["envelope_transfer_category"]
    _close(mixed1["minimum_worst_case_group_gain"],rec["gamma_1"]["worst_case_group_gain"])
    _close(mixed2["minimum_worst_case_group_gain"],rec["gamma_2"]["worst_case_group_gain"])
    _close(mixed2["maximum_best_case_group_gain"],rec["gamma_2"]["best_case_group_gain"])
    _close(mixed2["groups"][0]["critical_gamma"],rec["critical_gamma"])
    _close(result["mixed_sign_critical_gamma_error"],rec["critical_gamma_error_vs_sqrt3"])
    _close(result["small_n_exhaustive_error"],expected["small_n_exhaustive_error"])
    assert result["base_weight_scaling_error"]==expected["base_weight_scaling_error"]
    assert result["row_order_error"]==expected["row_order_error"]

    ceiling=receipt["claim_boundary"]
    assert ceiling["gamma_is_inferred_from_data"] is False
    assert ceiling["robustness_within_gamma_proves_no_observation_bias"] is False
    assert ceiling["deterministic_envelope_is_sampling_uncertainty_interval"] is False
