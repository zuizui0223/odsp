from __future__ import annotations

import json
import math
from pathlib import Path

from odsp.sampling_weight_sensitivity_benchmark import (
    run_sampling_weight_sensitivity_benchmark,
)

ROOT = Path(__file__).resolve().parents[1]


def _scenario_map(payload):
    return {row["name"]: row for row in payload["scenarios"]}


def _close(actual, expected, tol=1e-14):
    assert math.isclose(float(actual), float(expected), rel_tol=0.0, abs_tol=tol)


def test_sampling_weight_validation_receipt_replays_frozen_benchmark():
    receipt = json.loads(
        (ROOT / "SAMPLING_WEIGHT_SENSITIVITY_VALIDATION_RECEIPT.json").read_text(
            encoding="utf-8"
        )
    )
    assert receipt["receipt_id"] == "odsp-sampling-weight-sensitivity-v1-validation"
    cfg = receipt["benchmark_config"]
    result = run_sampling_weight_sensitivity_benchmark(
        seed=cfg["seed"], bootstrap_draws=cfg["bootstrap_draws"]
    )
    assert result["passed"] is True
    assert all(row["passed"] for row in result["checks"])

    expected = receipt["canonical_results"]
    assert result["stable"]["sensitivity_category"] == expected["stable"]["sensitivity_category"]
    assert result["sensitive"]["sensitivity_category"] == expected["sensitive"]["sensitivity_category"]
    assert result["too_few_blocks"]["sensitivity_category"] == expected["too_few_blocks"]["sensitivity_category"]
    assert result["sensitive"]["group_status_flip_count"] == expected["sensitive"]["group_status_flip_count"]
    assert result["global_scale_mean_gain_error"] == expected["global_weight_scaling_mean_gain_error"]
    assert result["scenario_order_mean_gain_error"] == expected["scenario_order_mean_gain_error"]

    stable = _scenario_map(result["stable"])
    for name, recorded in expected["stable"]["scenarios"].items():
        row = stable[name]
        assert row["robust_transfer_category"] == recorded["robust_transfer_category"]
        _close(row["mean_gain"], recorded["mean_gain"])
        _close(row["minimum_group_lower_bound"], recorded["minimum_group_lower_bound"])
        _close(row["overall_effective_sample_size"], recorded["overall_effective_sample_size"], 1e-10)
        _close(row["minimum_group_effective_sample_size"], recorded["minimum_group_effective_sample_size"], 1e-10)

    sensitive = _scenario_map(result["sensitive"])
    for name, recorded in expected["sensitive"]["scenarios"].items():
        row = sensitive[name]
        assert row["point_transfer_category"] == recorded["point_transfer_category"]
        assert row["robust_transfer_category"] == recorded["robust_transfer_category"]
        _close(row["mean_gain"], recorded["mean_gain"])
        _close(row["minimum_group_lower_bound"], recorded["minimum_group_lower_bound"])
        _close(row["overall_effective_sample_size"], recorded["overall_effective_sample_size"], 1e-10)
        _close(row["minimum_group_effective_sample_size"], recorded["minimum_group_effective_sample_size"], 1e-10)

    diagnostic = receipt["pre_green_diagnostic"]
    assert diagnostic["contract_changed"] is False
    assert diagnostic["decision_rule_changed"] is False
    assert diagnostic["threshold_changed"] is False
    assert diagnostic["interpretation_before_correction"] is False

    boundary = receipt["claim_boundary"]
    assert boundary["stable_result_proves_no_observation_bias"] is False
    assert boundary["weighting_replaces_detection_model"] is False
    assert boundary["aggregate_confidence_score_emitted"] is False
