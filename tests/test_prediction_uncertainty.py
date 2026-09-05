from __future__ import annotations

import numpy as np

from odsp.prediction_uncertainty import fit_state_conformal_calibrator


def _draw_labels(rng: np.random.Generator, probability: np.ndarray) -> np.ndarray:
    cumulative = np.cumsum(probability, axis=1)
    draws = rng.random(probability.shape[0])
    return np.sum(draws[:, None] > cumulative, axis=1)


def _probabilities(rng: np.random.Generator, n: int) -> np.ndarray:
    raw = rng.gamma(shape=np.array([1.5, 2.5, 4.0]), scale=1.0, size=(n, 3))
    return raw / raw.sum(axis=1, keepdims=True)


def test_split_conformal_has_near_nominal_exchangeable_coverage():
    rng = np.random.default_rng(20260905)
    calibration_probability = _probabilities(rng, 6000)
    calibration_y = _draw_labels(rng, calibration_probability)
    test_probability = _probabilities(rng, 30000)
    test_y = _draw_labels(rng, test_probability)

    calibrator = fit_state_conformal_calibrator(
        calibration_probability,
        calibration_y,
        classes=(0, 1, 2),
        miscoverage=0.1,
    )
    report = calibrator.evaluate(test_probability, test_y)

    assert calibrator.target_coverage == 0.9
    assert 0.89 <= report.empirical_coverage <= 0.92
    assert report.empty_set_fraction == 0.0
    assert 1.0 <= report.mean_set_size <= 3.0


def test_lower_miscoverage_produces_weakly_larger_prediction_sets():
    rng = np.random.default_rng(14)
    calibration_probability = _probabilities(rng, 2000)
    calibration_y = _draw_labels(rng, calibration_probability)
    query = _probabilities(rng, 500)

    c90 = fit_state_conformal_calibrator(
        calibration_probability, calibration_y, classes=(0, 1, 2), miscoverage=0.1
    )
    c95 = fit_state_conformal_calibrator(
        calibration_probability, calibration_y, classes=(0, 1, 2), miscoverage=0.05
    )
    n90 = c90.prediction_mask(query).sum(axis=1)
    n95 = c95.prediction_mask(query).sum(axis=1)
    assert np.all(n95 >= n90)


def test_distribution_shift_is_not_hidden_by_conformal_layer():
    rng = np.random.default_rng(81)
    calibration_probability = _probabilities(rng, 3000)
    calibration_y = _draw_labels(rng, calibration_probability)
    query = _probabilities(rng, 3000)
    shifted_y = np.argmin(query, axis=1)

    calibrator = fit_state_conformal_calibrator(
        calibration_probability, calibration_y, classes=(0, 1, 2), miscoverage=0.1
    )
    report = calibrator.evaluate(query, shifted_y)
    assert report.empirical_coverage < 0.6
    assert report.empirical_coverage < report.target_coverage


def test_conformal_rejects_training_on_malformed_probabilities():
    probability = np.array([[0.2, 0.2], [0.5, 0.5]])
    try:
        fit_state_conformal_calibrator(probability, [0, 1], classes=(0, 1))
    except ValueError as exc:
        assert "sum to one" in str(exc)
    else:
        raise AssertionError("expected malformed probability rows to fail")
