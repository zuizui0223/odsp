from __future__ import annotations

import numpy as np

from odsp.continuous_state import (
    fit_gaussian_continuous_state_model,
    score_continuous_log_density_gain,
    score_continuous_state_groups,
)


def _data(seed: int, n: int, beta: np.ndarray, noise: float = 0.7):
    rng = np.random.default_rng(seed)
    X = rng.normal(size=(n, beta.size))
    y = 2.0 + X @ beta + rng.normal(scale=noise, size=n)
    return X, y


def test_gaussian_continuous_model_recovers_positive_stable_density_gain_and_intervals():
    beta = np.array([1.2, -0.8, 0.5])
    X_train, y_train = _data(1, 4000, beta)
    X_test, y_test = _data(2, 10000, beta)
    model = fit_gaussian_continuous_state_model(X_train, y_train)
    score = model.score(X_test, y_test)
    summary = model.summarize(X_test[:20], interval_level=0.90)

    assert score.mean_log_density_gain > 0.5
    assert score.crps_improvement > 0
    assert score.rmse_improvement > 0
    assert abs(model.residual_standard_deviation - 0.7) < 0.04
    assert len(summary) == 20
    assert all(row.lower < row.mean < row.upper for row in summary)
    assert all(row.interval_level == 0.90 for row in summary)

    intervals = model.summarize(X_test, interval_level=0.90)
    covered = np.mean(
        [row.lower <= value <= row.upper for row, value in zip(intervals, y_test)]
    )
    assert 0.89 <= covered <= 0.91


def test_shifted_relationship_produces_negative_density_gain():
    beta = np.array([1.2, -0.8, 0.5])
    X_train, y_train = _data(3, 4000, beta)
    X_test, y_test = _data(4, 6000, -beta)
    model = fit_gaussian_continuous_state_model(X_train, y_train)
    score = model.score(X_test, y_test)
    assert score.mean_log_density_gain < -1.0
    assert score.crps_improvement < 0


def test_null_relationship_gain_is_near_zero_at_large_sample():
    beta = np.zeros(3)
    X_train, y_train = _data(5, 8000, beta)
    X_test, y_test = _data(6, 20000, beta)
    model = fit_gaussian_continuous_state_model(X_train, y_train)
    score = model.score(X_test, y_test)
    assert abs(score.mean_log_density_gain) < 0.01
    assert abs(score.crps_improvement) < 0.01


def test_positive_affine_response_transform_preserves_log_density_gain():
    beta = np.array([0.9, -0.4])
    X_train, y_train = _data(7, 3000, beta)
    X_test, y_test = _data(8, 5000, beta)
    original = fit_gaussian_continuous_state_model(X_train, y_train)
    original_score = original.score(X_test, y_test)

    scale = 7.5
    offset = -31.0
    transformed = fit_gaussian_continuous_state_model(
        X_train, scale * y_train + offset
    )
    transformed_score = transformed.score(X_test, scale * y_test + offset)

    assert np.isclose(
        original_score.mean_log_density_gain,
        transformed_score.mean_log_density_gain,
        rtol=0.0,
        atol=1e-10,
    )
    assert np.isclose(
        transformed_score.crps,
        scale * original_score.crps,
        rtol=0.0,
        atol=1e-10,
    )


def test_external_log_density_scoring_and_groupwise_failure_are_model_agnostic():
    conditional = np.log(np.array([0.8, 0.9, 0.7, 0.2]))
    marginal = np.log(np.array([0.5, 0.5, 0.5, 0.5]))
    result = score_continuous_log_density_gain(conditional, marginal)
    assert result.mean_log_density_gain > 0

    beta = np.array([1.0, -0.5])
    X_train, y_train = _data(11, 3000, beta)
    X_good, y_good = _data(12, 2000, beta)
    X_bad, y_bad = _data(13, 2000, -beta)
    X = np.vstack([X_good, X_bad])
    y = np.concatenate([y_good, y_bad])
    groups = np.array(["stable"] * len(y_good) + ["shifted"] * len(y_bad), dtype=object)
    model = fit_gaussian_continuous_state_model(X_train, y_train)
    grouped = score_continuous_state_groups(model, X, y, groups)
    assert grouped.gain_category == "mixed"
    assert grouped.groups[0].score.mean_log_density_gain > 0
    assert grouped.groups[1].score.mean_log_density_gain < 0
