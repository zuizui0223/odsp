from __future__ import annotations

import numpy as np

from odsp.trusted_joint_forecast import fit_trusted_joint_state_forecaster


def _sample(seed: int, n: int, *, low: float = -1.5, high: float = 1.5):
    rng = np.random.default_rng(seed)
    X = rng.uniform(low, high, size=(n, 2))
    raw_sin = 0.55 * X[:, 0]
    raw_cos = 1.0 + 0.25 * X[:, 1]
    mean_angle = np.arctan2(raw_sin, raw_cos)
    angle = rng.vonmises(mean_angle, 8.0)
    time = np.mod(24.0 * angle / (2.0 * np.pi), 24.0)
    height = (
        40.0
        + 8.0 * X[:, 1]
        + 4.0 * np.sin(angle)
        + 3.0 * np.cos(angle)
        + rng.normal(scale=1.2, size=n)
    )
    return X, height, time


def test_fit_keeps_training_and_calibration_roles_separate_and_forecasts_rows():
    X_train, h_train, t_train = _sample(1, 1200, low=-2.0, high=2.0)
    X_cal, h_cal, t_cal = _sample(2, 1200)
    forecaster = fit_trusted_joint_state_forecaster(
        X_train,
        h_train,
        t_train,
        X_cal,
        h_cal,
        t_cal,
        period=24.0,
        total_miscoverage=0.10,
    )

    assert forecaster.training_row_count == 1200
    assert forecaster.calibration_row_count == 1200
    assert (
        forecaster.model.height_given_context_model.training_row_count
        == forecaster.training_row_count
    )
    assert forecaster.conformal.continuous.calibration_size == 1200
    assert forecaster.conformal.circular.calibration_size == 1200

    X_test, _, _ = _sample(3, 12)
    rows = forecaster.forecast(X_test)
    assert len(rows) == 12
    first = rows[0]
    assert first.conformal_joint_target_coverage == 0.90
    assert first.conformal_height_lower < first.conformal_height_upper
    assert first.novelty_category in {
        "in_domain",
        "novel",
        "strict_extrapolation",
    }
    assert "confidence" not in first.as_dict()

    height_draws, time_draws = forecaster.sample_joint(
        X_test[:3], draws_per_row=25, random_state=99
    )
    assert height_draws.shape == (3, 25)
    assert time_draws.shape == (3, 25)
    assert np.all((time_draws >= 0.0) & (time_draws < 24.0))


def test_same_process_validation_and_shifted_novelty_are_both_visible():
    X_train, h_train, t_train = _sample(11, 1600, low=-2.0, high=2.0)
    X_cal, h_cal, t_cal = _sample(12, 1400)
    forecaster = fit_trusted_joint_state_forecaster(
        X_train,
        h_train,
        t_train,
        X_cal,
        h_cal,
        t_cal,
    )

    X_test, h_test, t_test = _sample(13, 5000)
    score = forecaster.score(X_test, h_test, t_test)
    assert score.mean_joint_log_density_gain > 0
    assert score.mean_coupling_log_density_gain > 0

    coverage = forecaster.evaluate_conformal(X_test, h_test, t_test)
    assert 0.87 <= coverage.empirical_joint_coverage <= 0.93

    same_domain = forecaster.forecast(X_test[:200])
    assert np.mean(
        [row.novelty_category != "strict_extrapolation" for row in same_domain]
    ) >= 0.90

    shifted_X = np.full((40, 2), 8.0)
    shifted = forecaster.forecast(shifted_X)
    assert all(row.novelty_category == "strict_extrapolation" for row in shifted)
