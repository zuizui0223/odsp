from __future__ import annotations

import json
import math
from pathlib import Path

from odsp.joint_robustness_radius_benchmark import run_joint_robustness_radius_benchmark

ROOT=Path(__file__).resolve().parents[1]


def _close(a,b,tol=1e-15):
    return math.isclose(float(a),float(b),rel_tol=0.0,abs_tol=tol)


def test_joint_robustness_radius_receipt_replays_frozen_benchmark():
    receipt=json.loads((ROOT/"JOINT_ROBUSTNESS_RADIUS_VALIDATION_RECEIPT.json").read_text(encoding="utf-8"))
    result=run_joint_robustness_radius_benchmark(seed=20260906,bootstrap_draws=500)
    canonical=receipt["canonical_results"]
    assert result["passed"] is canonical["passed"] is True
    assert len(result["checks"])==canonical["obligation_count"]==12
    assert all(row["passed"] for row in result["checks"])

    for key in ("strong_positive","strong_negative"):
        actual=result[key];expected=canonical[key]
        assert actual["radius_status"]==expected["radius_status"]
        assert actual["baseline_joint_category"]==expected["baseline_joint_category"]
        assert _close(actual["certified_gamma"],expected["certified_gamma"])
        assert actual["radius_is_lower_bound_only"] is expected["radius_is_lower_bound_only"]
        assert _close(actual["certified_maximum_multiplier_ratio"],expected["certified_maximum_multiplier_ratio"])

    mixed=result["mixed_positive"]
    expected=canonical["mixed_positive"]
    assert mixed["radius_status"]==expected["radius_status"]
    assert mixed["baseline_joint_category"]==expected["baseline_joint_category"]
    assert mixed["target_joint_category"]==expected["target_joint_category"]
    assert _close(mixed["certified_gamma"],expected["certified_gamma"])
    assert _close(mixed["break_gamma"],expected["break_gamma"])
    assert _close(mixed["boundary_interval_width"],expected["boundary_interval_width"])
    assert _close(mixed["certified_maximum_multiplier_ratio"],expected["certified_maximum_multiplier_ratio"])
    assert len(mixed["limiting_group_ids"])==expected["limiting_group_count"]

    weak=result["weak_positive"]
    expected=canonical["weak_positive"]
    assert weak["radius_status"]==expected["radius_status"]
    assert weak["baseline_joint_category"]==expected["baseline_joint_category"]
    assert weak["certified_gamma"] is expected["certified_gamma"] is None
    assert _close(weak["baseline_minimum_worst_case_lower_bound"],expected["baseline_minimum_worst_case_lower_bound"])

    few=result["too_few_blocks"]
    expected=canonical["too_few_blocks"]
    assert few["radius_status"]==expected["radius_status"]
    assert few["baseline_joint_category"]==expected["baseline_joint_category"]
    assert few["certified_gamma"] is expected["certified_gamma"] is None
    assert len(few["limiting_group_ids"])==expected["limiting_group_count"]

    assert _close(result["sqrt3"],canonical["sqrt3"])
    assert _close(result["break_gamma_error"],canonical["break_gamma_error"],tol=1e-14)
    assert _close(result["base_weight_scaling_error"],canonical["base_weight_scaling_error"])
    assert [(row["gamma"],row["category"]) for row in result["gamma_path"]]==[
        (row["gamma"],row["category"]) for row in canonical["gamma_path"]
    ]
    assert canonical["automatic_bias_correction_performed"] is False
    assert canonical["aggregate_confidence_score_emitted"] is False
    assert receipt["claim_boundary"]["radius_is_probability_of_correctness"] is False
    assert receipt["claim_boundary"]["radius_proves_no_observation_bias"] is False
    assert receipt["frozen_v4_preservation"]["closed_empirical_endpoint_reopened"] is False
