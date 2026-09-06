from __future__ import annotations

import json
from pathlib import Path

from odsp.robust_trust_aware_model_selection_benchmark import (
    run_robust_trust_aware_model_selection_benchmark,
)

ROOT=Path(__file__).resolve().parents[1]


def _close(a: float,b: float,tol: float=1e-15)->None:
    assert abs(a-b)<=tol


def test_robust_selection_receipt_replays_frozen_benchmark():
    receipt=json.loads((ROOT/"ROBUST_TRUST_AWARE_MODEL_SELECTION_VALIDATION_RECEIPT.json").read_text(encoding="utf-8"))
    cfg=receipt["benchmark_config"]
    result=run_robust_trust_aware_model_selection_benchmark(seed=cfg["seed"],bootstrap_draws=cfg["bootstrap_draws"])
    assert result["passed"] is True
    expected=receipt["canonical_results"]
    comparison=result["comparison"]
    assert comparison["point_trusted_names"]==expected["point_trusted_names"]
    assert comparison["robust_trusted_names"]==expected["robust_trusted_names"]
    assert comparison["legacy_trusted_but_robust_rejected_names"]==expected["legacy_trusted_but_robust_rejected_names"]
    assert comparison["pareto_front_names"]==expected["pareto_front_names"]
    assert comparison["recommended_by_log_score"]==expected["recommended_by_log_score"]
    assert comparison["aggregate_confidence_score_emitted"] is False

    for name, exp in expected["candidates"].items():
        row=result["candidates"][name]
        point=row["point_and_coverage"]
        uncertainty=row["transfer_uncertainty"]
        _close(point["forecast_score"]["mean_log_density_gain"],exp["mean_log_density_gain"])
        assert point["groupwise_trust"]["coverage_category"]==exp["coverage_category"]
        _close(point["worst_group_coverage_error"],exp["worst_group_coverage_error"])
        assert point["trusted_admissible"] is exp["point_trusted"]
        assert uncertainty["robust_transfer_category"]==exp["robust_transfer_category"]
        if exp["minimum_group_lower_bound"] is None:
            assert row["minimum_group_lower_bound"] is None
        else:
            _close(row["minimum_group_lower_bound"],exp["minimum_group_lower_bound"])
        assert row["robust_trusted_admissible"] is exp["robust_trusted"]
        if "uncertain_group_count" in exp:
            assert uncertainty["uncertain_group_count"]==exp["uncertain_group_count"]
        if "unavailable_group_count" in exp:
            assert uncertainty["unavailable_group_count"]==exp["unavailable_group_count"]
