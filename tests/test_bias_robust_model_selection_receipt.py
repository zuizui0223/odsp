from __future__ import annotations

import json
import math
from pathlib import Path

from odsp.bias_robust_model_selection_benchmark import run_bias_robust_model_selection_benchmark

ROOT=Path(__file__).resolve().parents[1]
RECEIPT=ROOT/"BIAS_ROBUST_MODEL_SELECTION_VALIDATION_RECEIPT.json"


def _close(a,b,tol=1e-14):
    assert math.isclose(float(a),float(b),rel_tol=0.0,abs_tol=tol)


def test_bias_robust_model_selection_receipt_replays():
    receipt=json.loads(RECEIPT.read_text(encoding="utf-8"))
    result=run_bias_robust_model_selection_benchmark()
    assert result["passed"] is True
    assert all(row["passed"] for row in result["checks"])
    expected=receipt["canonical_results"]
    actual_by={row["name"]:row for row in result["candidates"]}
    for name in ("robust_balanced","gamma_fragile","robust_broad","coverage_failure","too_few_blocks"):
        actual=actual_by[name]
        frozen=expected[name]
        score=actual["point_and_coverage"]["forecast_score"]
        trust=actual["point_and_coverage"]["groupwise_trust"]
        joint=actual["joint_robustness"]
        _close(score["mean_log_density_gain"],frozen["mean_log_density_gain"])
        assert trust["coverage_category"]==frozen["coverage_category"]
        _close(actual["point_and_coverage"]["worst_group_coverage_error"],frozen["worst_group_coverage_error"])
        assert actual["point_and_coverage"]["trusted_admissible"] is frozen["point_trusted"]
        assert joint["joint_robust_category"]==frozen["joint_robust_category"]
        if frozen["minimum_worst_case_lower_bound"] is None:
            assert joint["minimum_worst_case_lower_bound"] is None
        else:
            _close(joint["minimum_worst_case_lower_bound"],frozen["minimum_worst_case_lower_bound"])
        assert actual["bias_robust_trusted_admissible"] is frozen["bias_robust_trusted"]
        _close(score["mean_region_size"],frozen["mean_region_size"])

    selection=result["selection"]
    assert selection["point_trusted_names"]==expected["point_trusted_names"]
    assert selection["bias_robust_trusted_names"]==expected["bias_robust_trusted_names"]
    assert selection["point_trusted_but_bias_robust_rejected_names"]==expected["point_trusted_but_bias_robust_rejected_names"]
    assert selection["pareto_front_names"]==expected["pareto_front_names"]
    assert selection["recommended_by_log_score"]==expected["recommended_by_log_score"]
    assert selection["aggregate_confidence_score_emitted"] is False


def test_bias_robust_receipt_preserves_claim_ceiling():
    receipt=json.loads(RECEIPT.read_text(encoding="utf-8"))
    assert all(value is False for value in receipt["claim_boundary"].values())
    frozen=receipt["frozen_v4_preservation"]
    assert frozen["v4_manuscript_modified"] is False
    assert frozen["v4_submission_artifact_modified"] is False
    assert frozen["closed_empirical_endpoint_reopened"] is False
