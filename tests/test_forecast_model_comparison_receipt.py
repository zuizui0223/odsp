from __future__ import annotations

import json
from pathlib import Path

from odsp.forecast_model_comparison_benchmark import (
    run_forecast_model_comparison_benchmark,
)


ROOT = Path(__file__).resolve().parents[1]


def _candidate_summary(row) -> dict[str, object]:
    return {
        "mean_log_density_gain": row.mean_log_density_gain,
        "minimum_group_gain": row.minimum_group_gain,
        "maximum_group_gain": row.maximum_group_gain,
        "positive_group_count": row.positive_group_count,
        "nonpositive_group_count": row.nonpositive_group_count,
        "transfer_category": row.transfer_category,
        "transfer_admissible": row.transfer_admissible,
        "empirical_coverage": row.empirical_coverage,
        "absolute_coverage_error": row.absolute_coverage_error,
        "mean_region_size": row.mean_region_size,
        "trusted_admissible": row.trusted_admissible,
    }


def test_forecast_model_comparison_receipt_replays_canonical_results():
    receipt = json.loads(
        (ROOT / "FORECAST_MODEL_COMPARISON_VALIDATION_RECEIPT.json").read_text(
            encoding="utf-8"
        )
    )
    config = receipt["benchmark_config"]
    result = run_forecast_model_comparison_benchmark(
        seed=config["seed"],
        group_count=config["group_count"],
        rows_per_group=config["rows_per_group"],
        target_coverage=config["target_coverage"],
        coverage_tolerance=config["coverage_tolerance"],
        gain_tolerance=config["gain_tolerance"],
    )
    canonical = receipt["canonical_results"]
    assert result.passed is canonical["passed"]
    assert result.recommended_candidate == canonical["recommended_candidate"]
    assert list(result.pareto_front_names) == canonical["pareto_front_names"]
    assert (
        result.aggregate_confidence_score_emitted
        is canonical["aggregate_confidence_score_emitted"]
    )

    observed = {row.name: _candidate_summary(row) for row in result.candidates}
    assert observed == canonical["candidates"]

    correction = receipt["numeric_correction"]
    assert correction["gain_tolerance"] == 1e-12
    assert correction["candidate_rank_changed"] is False
    assert correction["candidate_admission_changed"] is False
    assert correction["coverage_threshold_changed"] is False
    assert correction["synthetic_generator_changed"] is False

    boundary = receipt["claim_boundary"]
    assert all(value is False for value in boundary.values())
    frozen = receipt["frozen_v4_preservation"]
    assert all(value is False for value in frozen.values())
