from __future__ import annotations

import json
import math
from pathlib import Path

from odsp.joint_bias_uncertainty_robustness_benchmark import (
    run_joint_bias_uncertainty_robustness_benchmark,
)

ROOT = Path(__file__).resolve().parents[1]
RECEIPT = ROOT / "JOINT_BIAS_UNCERTAINTY_ROBUSTNESS_VALIDATION_RECEIPT.json"


def _close(a: float, b: float, tol: float = 1e-14) -> None:
    assert math.isclose(float(a), float(b), rel_tol=0.0, abs_tol=tol)


def test_joint_bias_uncertainty_receipt_replays_frozen_benchmark():
    receipt = json.loads(RECEIPT.read_text(encoding="utf-8"))
    cfg = receipt["benchmark_config"]
    result = run_joint_bias_uncertainty_robustness_benchmark(
        seed=cfg["seed"], bootstrap_draws=cfg["bootstrap_draws"]
    )
    assert result["passed"] is True
    assert len(result["checks"]) == 10
    assert all(row["passed"] for row in result["checks"])

    expected = receipt["canonical_results"]
    assert expected["passed"] is True

    for key in ("strong_positive", "mixed_sign", "negative", "weak_positive_gamma_1"):
        actual = result[key]
        frozen = expected[key]
        assert actual["point_transfer_category"] == frozen["point_transfer_category"]
        assert actual["deterministic_envelope_category"] == frozen["deterministic_envelope_category"]
        assert actual["joint_robust_category"] == frozen["joint_robust_category"]
        _close(actual["minimum_worst_case_lower_bound"], frozen["minimum_worst_case_lower_bound"])
        _close(actual["maximum_best_case_upper_bound"], frozen["maximum_best_case_upper_bound"])

    mixed = result["mixed_sign"]
    frozen_mixed = expected["mixed_sign"]
    _close(
        mixed["groups"][0]["deterministic_worst_case_gain"],
        frozen_mixed["deterministic_worst_case_gain"],
    )
    _close(
        mixed["groups"][0]["deterministic_best_case_gain"],
        frozen_mixed["deterministic_best_case_gain"],
    )

    actual_few = result["too_few_blocks"]
    frozen_few = expected["too_few_blocks"]
    assert actual_few["point_transfer_category"] == frozen_few["point_transfer_category"]
    assert actual_few["deterministic_envelope_category"] == frozen_few["deterministic_envelope_category"]
    assert actual_few["joint_robust_category"] == "unavailable"
    assert actual_few["unavailable_group_count"] == frozen_few["unavailable_group_count"]

    _close(result["gamma_1_existing_bound_error"], expected["gamma_1_existing_bound_error"])
    _close(result["base_weight_scaling_error"], expected["base_weight_scaling_error"])
    assert result["gamma_monotonicity_passed"] is expected["gamma_monotonicity_passed"]
    assert expected["automatic_bias_correction_performed"] is False
    assert expected["aggregate_confidence_score_emitted"] is False


def test_joint_bias_uncertainty_receipt_preserves_claim_boundary():
    receipt = json.loads(RECEIPT.read_text(encoding="utf-8"))
    boundary = receipt["claim_boundary"]
    assert all(value is False for value in boundary.values())
    frozen = receipt["frozen_v4_preservation"]
    assert frozen["v4_manuscript_modified"] is False
    assert frozen["v4_submission_artifact_modified"] is False
    assert frozen["closed_empirical_endpoint_reopened"] is False
