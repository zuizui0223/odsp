from __future__ import annotations

import numpy as np

from odsp.trust_aware_model_selection import (
    compare_trust_aware_candidates,
    evaluate_trust_aware_candidate,
)


def _candidate(name: str, gains, coverage_counts, region_size: float):
    group_count = len(gains)
    rows_per_group = 100
    groups = tuple(
        label
        for index in range(group_count)
        for label in [f"g{index + 1}"] * rows_per_group
    )
    marginal = np.full(group_count * rows_per_group, -2.0)
    gain = np.concatenate([np.full(rows_per_group, value) for value in gains])
    covered = np.concatenate([
        np.r_[np.ones(count, dtype=bool), np.zeros(rows_per_group - count, dtype=bool)]
        for count in coverage_counts
    ])
    return evaluate_trust_aware_candidate(
        name,
        marginal + gain,
        marginal,
        covered,
        groups,
        region_size=np.full(marginal.size, region_size),
    )


def test_groupwise_failure_blocks_high_pooled_candidate():
    good = _candidate("good", [0.25] * 4, [90] * 4, 4.0)
    masked = _candidate("masked", [0.50] * 4, [60, 90, 90, 90], 2.0)
    assert masked.forecast_score.mean_log_density_gain > good.forecast_score.mean_log_density_gain
    assert masked.groupwise_trust.coverage_category == "mixed"
    assert masked.trusted_admissible is False
    result = compare_trust_aware_candidates([masked, good])
    assert result.recommended_by_log_score == "good"
    assert result.pareto_front_names == ("good",)
    assert result.aggregate_confidence_score_emitted is False


def test_pareto_uses_worst_group_coverage_error_and_sharpness():
    strong = _candidate("strong", [0.25] * 4, [90] * 4, 4.0)
    broad = _candidate("broad", [0.15] * 4, [90] * 4, 7.0)
    result = compare_trust_aware_candidates([strong, broad])
    assert set(result.trusted_admissible_names) == {"strong", "broad"}
    assert result.pareto_front_names == ("strong",)
    assert result.recommended_by_log_score == "strong"
