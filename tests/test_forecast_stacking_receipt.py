from __future__ import annotations

import json
from pathlib import Path

import pytest

from odsp.forecast_stacking_benchmark import run_forecast_stacking_benchmark


ROOT = Path(__file__).resolve().parents[1]


def test_forecast_stacking_receipt_replays_frozen_benchmark():
    receipt = json.loads((ROOT / "FORECAST_STACKING_VALIDATION_RECEIPT.json").read_text(encoding="utf-8"))
    result = run_forecast_stacking_benchmark(
        seed=receipt["benchmark_config"]["seed"],
        tuning_rows=receipt["benchmark_config"]["tuning_rows"],
        validation_group_count=receipt["benchmark_config"]["validation_group_count"],
        validation_rows_per_group=receipt["benchmark_config"]["validation_rows_per_group"],
    )
    assert result["passed"] is True
    expected = receipt["canonical_results"]
    assert result["fit"]["weights"] == pytest.approx(expected["fit"]["weights"], abs=1e-15, rel=0.0)
    assert result["fit"]["iterations"] == expected["fit"]["iterations"]
    assert result["fit"]["converged"] is expected["fit"]["converged"]
    assert result["fit"]["objective_improvement"] == pytest.approx(expected["fit"]["objective_improvement"], abs=1e-15, rel=0.0)
    assert result["candidate_permutation_weight_max_abs_error"] == pytest.approx(expected["candidate_permutation_weight_max_abs_error"], abs=1e-15, rel=0.0)

    for family in ("complementary_stable", "validation_shift", "mixed_group"):
        actual = result["families"][family]["stack"]
        frozen = expected[family]
        assert actual["mean_log_density_gain"] == pytest.approx(frozen["mean_log_density_gain"], abs=1e-12, rel=0.0)
        assert actual["minimum_group_gain"] == pytest.approx(frozen["minimum_group_gain"], abs=1e-12, rel=0.0)
        assert actual["maximum_group_gain"] == pytest.approx(frozen["maximum_group_gain"], abs=1e-12, rel=0.0)
        assert actual["positive_group_count"] == frozen["positive_group_count"]
        assert actual["nonpositive_group_count"] == frozen["nonpositive_group_count"]
        assert actual["transfer_category"] == frozen["transfer_category"]
        assert actual["transfer_admissible"] is frozen["transfer_admissible"]

    stable = result["families"]["complementary_stable"]
    assert stable["best_single_mean_gain"] == pytest.approx(expected["complementary_stable"]["best_single_mean_gain"], abs=1e-15, rel=0.0)
    assert stable["stack_minus_best_single_gain"] == pytest.approx(expected["complementary_stable"]["stack_minus_best_single_gain"], abs=1e-12, rel=0.0)
    assert receipt["claim_boundary"]["validation_used_for_weight_fit"] is False
    assert receipt["claim_boundary"]["member_coverage_inherited"] is False
    assert receipt["claim_boundary"]["stack_requires_independent_recalibration"] is True
    assert receipt["claim_boundary"]["aggregate_confidence_score_emitted"] is False
