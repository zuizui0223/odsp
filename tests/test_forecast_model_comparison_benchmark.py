from __future__ import annotations

from odsp.forecast_model_comparison_benchmark import (
    run_forecast_model_comparison_benchmark,
)


def test_forecast_model_comparison_benchmark_passes():
    result = run_forecast_model_comparison_benchmark(
        seed=20260905,
        group_count=6,
        rows_per_group=500,
        target_coverage=0.90,
        gain_tolerance=1e-12,
    )
    assert result.passed is True, result.as_dict()
    assert result.gain_tolerance == 1e-12
    assert len(result.checks) == 8
    assert all(row.passed for row in result.checks)
    assert result.recommended_candidate == "well_calibrated"
    assert "well_calibrated" in result.pareto_front_names
    assert "broad_calibrated" not in result.pareto_front_names
    by_name = {row.name: row for row in result.candidates}
    assert by_name["overconfident_high_gain"].mean_log_density_gain > by_name["well_calibrated"].mean_log_density_gain
    assert by_name["overconfident_high_gain"].trusted_admissible is False
    assert by_name["marginal_only"].transfer_category == "non_generalizing"
    assert by_name["marginal_only"].transfer_admissible is False
    assert by_name["mixed_despite_positive_pool"].mean_log_density_gain > 0
    assert by_name["mixed_despite_positive_pool"].transfer_category == "mixed"
    assert result.aggregate_confidence_score_emitted is False
