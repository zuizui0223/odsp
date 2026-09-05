from __future__ import annotations

import numpy as np
import pytest

from odsp.forecast_model_comparison import (
    compare_forecast_candidates,
    evaluate_forecast_candidate,
)


def _base_rows():
    groups = np.repeat(["a", "b", "c"], 4)
    marginal = np.full(groups.size, -2.0)
    covered = np.asarray([True, True, True, False] * 3)
    return groups, marginal, covered


def test_group_failure_is_not_rescued_by_positive_pool():
    groups, marginal, covered = _base_rows()
    gain = np.asarray([0.5] * 4 + [0.4] * 4 + [-0.1] * 4)
    score = evaluate_forecast_candidate(
        "mixed",
        marginal + gain,
        marginal,
        groups,
        covered=covered,
        target_coverage=0.75,
        region_size=np.full(gain.size, 4.0),
    )
    assert score.mean_log_density_gain > 0
    assert score.transfer_category == "mixed"
    assert score.transfer_admissible is False
    assert score.trusted_admissible is False


def test_bad_coverage_rejects_high_gain_candidate():
    groups, marginal, _ = _base_rows()
    gain = np.full(groups.size, 0.8)
    covered = np.asarray([True, True, False, False] * 3)
    score = evaluate_forecast_candidate(
        "overconfident",
        marginal + gain,
        marginal,
        groups,
        covered=covered,
        target_coverage=0.90,
        region_size=np.full(gain.size, 1.0),
        coverage_tolerance=0.03,
    )
    assert score.transfer_category == "generalizing"
    assert score.transfer_admissible is True
    assert score.coverage_ok is False
    assert score.trusted_admissible is False


def test_comparison_uses_admission_gate_before_log_score_ranking():
    groups = np.repeat(["a", "b"], 10)
    marginal = np.full(groups.size, -2.0)
    covered_90 = np.asarray([True] * 9 + [False] + [True] * 9 + [False])
    covered_60 = np.asarray([True] * 6 + [False] * 4 + [True] * 6 + [False] * 4)

    trusted = evaluate_forecast_candidate(
        "trusted",
        marginal + 0.3,
        marginal,
        groups,
        covered=covered_90,
        target_coverage=0.90,
        region_size=np.full(groups.size, 4.0),
    )
    high_gain_bad_coverage = evaluate_forecast_candidate(
        "high_gain_bad_coverage",
        marginal + 0.8,
        marginal,
        groups,
        covered=covered_60,
        target_coverage=0.90,
        region_size=np.full(groups.size, 1.0),
    )
    result = compare_forecast_candidates([trusted, high_gain_bad_coverage])
    assert result.recommended_by_log_score == "trusted"
    assert result.trusted_admissible_names == ("trusted",)
    assert result.aggregate_confidence_score_emitted is False


def test_pareto_front_retains_sharp_high_gain_candidate():
    groups = np.repeat(["a", "b"], 10)
    marginal = np.full(groups.size, -2.0)
    covered = np.asarray([True] * 9 + [False] + [True] * 9 + [False])
    sharp = evaluate_forecast_candidate(
        "sharp",
        marginal + 0.3,
        marginal,
        groups,
        covered=covered,
        target_coverage=0.90,
        region_size=np.full(groups.size, 3.0),
    )
    broad = evaluate_forecast_candidate(
        "broad",
        marginal + 0.2,
        marginal,
        groups,
        covered=covered,
        target_coverage=0.90,
        region_size=np.full(groups.size, 8.0),
    )
    result = compare_forecast_candidates([sharp, broad])
    assert result.pareto_front_names == ("sharp",)
    assert result.recommended_by_log_score == "sharp"


def test_coverage_evidence_must_be_complete():
    groups, marginal, covered = _base_rows()
    with pytest.raises(ValueError, match="supplied together"):
        evaluate_forecast_candidate(
            "bad",
            marginal + 0.2,
            marginal,
            groups,
            covered=covered,
        )


def test_candidate_names_must_be_unique():
    groups, marginal, covered = _base_rows()
    score = evaluate_forecast_candidate(
        "same",
        marginal + 0.2,
        marginal,
        groups,
        covered=covered,
        target_coverage=0.75,
        region_size=np.ones(groups.size),
    )
    with pytest.raises(ValueError, match="unique"):
        compare_forecast_candidates([score, score])
