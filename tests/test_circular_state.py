from __future__ import annotations

import numpy as np

from odsp.circular_state import (
    circular_distance,
    fit_von_mises_circular_state_model,
    score_circular_log_density_gain,
    score_circular_state_groups,
)


def _sample(seed: int, n: int, *, shift: float = 0.0):
    rng = np.random.default_rng(seed)
    X = rng.uniform(-1.0, 1.0, size=(n, 2))
    mu = 1.0 + 0.55 * X[:, 0] - 0.35 * X[:, 1] + shift
    angle = rng.vonmises(mu, 9.0)
    state = np.mod(angle, 2.0 * np.pi) * 24.0 / (2.0 * np.pi)
    return X, state


def test_midnight_boundary_is_circular_not_linear():
    distance = circular_distance([23.9, 0.1], [0.1, 23.9], period=24.0)
    np.testing.assert_allclose(distance, [0.2, 0.2], atol=1e-12)


def test_reference_model_predicts_stable_circular_state_better_than_marginal():
    X_train, y_train = _sample(10, 2500)
    X_test, y_test = _sample(11, 5000)
    model = fit_von_mises_circular_state_model(X_train, y_train, period=24.0)
    score = model.score(X_test, y_test)
    assert score.mean_log_density_gain > 0.1
    assert score.circular_mae_improvement > 0.0


def test_phase_origin_shift_preserves_density_gain():
    X_train, y_train = _sample(20, 2500)
    X_test, y_test = _sample(21, 5000)
    original = fit_von_mises_circular_state_model(X_train, y_train, period=24.0)
    original_gain = original.score(X_test, y_test).mean_log_density_gain

    shift = 6.75
    moved = fit_von_mises_circular_state_model(
        X_train, np.mod(y_train + shift, 24.0), period=24.0
    )
    moved_gain = moved.score(
        X_test, np.mod(y_test + shift, 24.0)
    ).mean_log_density_gain
    np.testing.assert_allclose(original_gain, moved_gain, atol=1e-10, rtol=0.0)


def test_period_unit_conversion_preserves_density_gain():
    X_train, y_train = _sample(30, 2500)
    X_test, y_test = _sample(31, 5000)
    hours = fit_von_mises_circular_state_model(X_train, y_train, period=24.0)
    minutes = fit_von_mises_circular_state_model(
        X_train, y_train * 60.0, period=1440.0
    )
    np.testing.assert_allclose(
        hours.score(X_test, y_test).mean_log_density_gain,
        minutes.score(X_test, y_test * 60.0).mean_log_density_gain,
        atol=1e-10,
        rtol=0.0,
    )


def test_prediction_arc_can_wrap_midnight():
    rng = np.random.default_rng(42)
    X = np.zeros((1000, 1))
    angle = rng.vonmises(0.0, 16.0, size=1000)
    state = np.mod(angle, 2.0 * np.pi) * 24.0 / (2.0 * np.pi)
    model = fit_von_mises_circular_state_model(X, state, period=24.0)
    summary = model.summarize(np.zeros((1, 1)), interval_level=0.90)[0]
    assert summary.mean_state < 1.0 or summary.mean_state > 23.0
    assert summary.arc_wraps_origin is True
    assert summary.arc_half_width > 0.0


def test_external_log_density_and_grouped_scoring_interfaces():
    score = score_circular_log_density_gain(
        [-1.0, -1.5, -1.2], [-2.0, -2.0, -2.0]
    )
    assert score.mean_log_density_gain > 0.0

    X_train, y_train = _sample(50, 3000)
    X_test, y_test = _sample(51, 4000)
    model = fit_von_mises_circular_state_model(X_train, y_train)
    groups = np.repeat(["g1", "g2", "g3", "g4"], 1000)
    grouped = score_circular_state_groups(model, X_test, y_test, groups)
    assert len(grouped.groups) == 4
    assert grouped.gain_category == "generalizing"
