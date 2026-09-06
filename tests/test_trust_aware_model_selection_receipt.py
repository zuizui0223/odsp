from __future__ import annotations

import json
from pathlib import Path

import pytest

from odsp.trust_aware_model_selection_benchmark import run_trust_aware_model_selection_benchmark

ROOT = Path(__file__).resolve().parents[1]


def test_trust_aware_selection_receipt_replays_benchmark():
    receipt = json.loads((ROOT / "TRUST_AWARE_MODEL_SELECTION_VALIDATION_RECEIPT.json").read_text(encoding="utf-8"))
    result = run_trust_aware_model_selection_benchmark()
    expected = receipt["canonical_results"]
    assert result["passed"] is expected["passed"] is True
    assert result["selection"]["recommended_by_log_score"] == expected["recommended_candidate"]
    assert result["selection"]["pareto_front_names"] == expected["pareto_front_names"]
    assert result["selection"]["trusted_admissible_names"] == expected["trusted_admissible_names"]
    by_name = {row["name"]: row for row in result["selection"]["candidates"]}

    for name in (
        "balanced_trusted",
        "pooled_masked_coverage_failure",
        "mixed_transfer",
        "broad_trusted",
        "overconfident",
    ):
        actual = by_name[name]
        frozen = expected[name]
        assert actual["forecast_score"]["mean_log_density_gain"] == pytest.approx(frozen["mean_log_density_gain"], abs=1e-15, rel=0.0)
        assert actual["forecast_score"]["minimum_group_gain"] == pytest.approx(frozen["minimum_group_gain"], abs=1e-15, rel=0.0)
        assert actual["forecast_score"]["empirical_coverage"] == pytest.approx(frozen["pooled_coverage"], abs=1e-15, rel=0.0)
        if "coverage_category" in frozen:
            assert actual["groupwise_trust"]["coverage_category"] == frozen["coverage_category"]
        if "transfer_category" in frozen:
            assert actual["groupwise_trust"]["transfer_category"] == frozen["transfer_category"]
        if "worst_group_coverage_error" in frozen:
            assert actual["worst_group_coverage_error"] == pytest.approx(frozen["worst_group_coverage_error"], abs=1e-15, rel=0.0)
        if "mean_region_size" in frozen:
            assert actual["forecast_score"]["mean_region_size"] == pytest.approx(frozen["mean_region_size"], abs=1e-15, rel=0.0)
        assert actual["trusted_admissible"] is frozen["trusted_admissible"]

    assert result["candidate_order_invariant"] is expected["candidate_order_invariant"] is True
    assert result["selection"]["aggregate_confidence_score_emitted"] is expected["aggregate_confidence_score_emitted"] is False
    assert receipt["claim_boundary"]["pooled_coverage_can_override_group_failure"] is False
    assert receipt["claim_boundary"]["groupwise_empirical_coverage_is_conditional_coverage_guarantee"] is False
