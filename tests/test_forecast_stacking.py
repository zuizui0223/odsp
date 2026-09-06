from __future__ import annotations

import numpy as np
import pytest

from odsp.forecast_stacking import (
    evaluate_stacked_forecast,
    fit_log_score_stacking,
    stacked_log_density,
)


def _logpdf(y: np.ndarray, mean: float, sd: float) -> np.ndarray:
    return -0.5 * np.log(2.0 * np.pi * sd * sd) - 0.5 * ((y - mean) / sd) ** 2


def test_stacking_learns_complementary_members_without_validation_leakage():
    rng = np.random.default_rng(19)
    component = rng.integers(0, 2, 2400)
    y = np.where(component == 0, rng.normal(-2.0, 0.7, 2400), rng.normal(2.0, 0.7, 2400))
    log_density = np.column_stack([_logpdf(y, -2.0, 0.7), _logpdf(y, 2.0, 0.7), _logpdf(y, 0.0, 3.0)])
    names = ("left", "right", "broad")
    fit = fit_log_score_stacking(log_density, candidate_names=names)

    assert fit.converged
    assert sum(fit.weights) == pytest.approx(1.0)
    assert fit.validation_used_for_fit is False
    assert fit.coverage_inherited_from_members is False
    assert fit.requires_independent_recalibration is True
    assert fit.weights[0] > 0.25
    assert fit.weights[1] > 0.25
    assert fit.weights[2] < 0.20


def test_stacked_validation_retains_failed_group():
    rng = np.random.default_rng(23)
    tune_component = rng.integers(0, 2, 3000)
    tune_y = np.where(tune_component == 0, rng.normal(-2.0, 0.7, 3000), rng.normal(2.0, 0.7, 3000))
    tune_log = np.column_stack([_logpdf(tune_y, -2.0, 0.7), _logpdf(tune_y, 2.0, 0.7), _logpdf(tune_y, 0.0, 3.0)])
    names = ("left", "right", "broad")
    fit = fit_log_score_stacking(tune_log, candidate_names=names)

    good = np.concatenate([
        np.where(rng.integers(0, 2, 500) == 0, rng.normal(-2.0, 0.7, 500), rng.normal(2.0, 0.7, 500))
        for _ in range(3)
    ])
    bad = rng.normal(3.5, 0.7, 500)
    y = np.concatenate([good, bad])
    groups = tuple(["g1"] * 500 + ["g2"] * 500 + ["g3"] * 500 + ["g4"] * 500)
    candidate_log = np.column_stack([_logpdf(y, -2.0, 0.7), _logpdf(y, 2.0, 0.7), _logpdf(y, 0.0, 3.0)])
    marginal = _logpdf(y, 0.0, 3.0)
    result = evaluate_stacked_forecast(
        fit,
        candidate_log,
        marginal,
        groups,
        candidate_names=names,
    )

    assert result.mean_log_density_gain > 0.0
    assert result.transfer_category == "mixed"
    assert result.minimum_group_gain < 0.0
    assert result.transfer_admissible is False
    assert result.requires_independent_recalibration is True
    assert result.aggregate_confidence_score_emitted is False


def test_candidate_order_is_part_of_frozen_stack_identity():
    rng = np.random.default_rng(29)
    y = rng.normal(0.0, 1.0, 100)
    log_density = np.column_stack([_logpdf(y, -1.0, 1.0), _logpdf(y, 1.0, 1.0)])
    fit = fit_log_score_stacking(log_density, candidate_names=("a", "b"))
    with pytest.raises(ValueError):
        stacked_log_density(fit, log_density[:, ::-1], candidate_names=("b", "a"))
