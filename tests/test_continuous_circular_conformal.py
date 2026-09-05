from __future__ import annotations

import numpy as np

from odsp.continuous_circular_conformal import (
    fit_circular_conformal_calibrator,
    fit_continuous_conformal_calibrator,
    fit_joint_bonferroni_conformal_calibrator,
)


def test_continuous_scale_adaptive_intervals_cover_and_rescale():
    rng = np.random.default_rng(20260905)
    n_cal = 4000
    x = rng.normal(size=n_cal)
    center = 1.5 + 0.8 * x
    scale = np.exp(0.25 * x)
    observed = center + scale * rng.normal(size=n_cal)

    cal = fit_continuous_conformal_calibrator(
        center,
        observed,
        predicted_scale=scale,
        miscoverage=0.10,
    )
    assert cal.scale_adaptive is True
    assert cal.target_coverage == 0.90
    assert cal.score_quantile > 0

    x_test = rng.normal(size=8000)
    center_test = 1.5 + 0.8 * x_test
    scale_test = np.exp(0.25 * x_test)
    observed_test = center_test + scale_test * rng.normal(size=x_test.size)
    report = cal.evaluate(
        center_test,
        observed_test,
        predicted_scale=scale_test,
    )
    assert 0.88 <= report.empirical_coverage <= 0.92

    factor = 7.5
    offset = -13.0
    transformed = fit_continuous_conformal_calibrator(
        factor * center + offset,
        factor * observed + offset,
        predicted_scale=factor * scale,
        miscoverage=0.10,
    )
    assert abs(transformed.score_quantile - cal.score_quantile) <= 1e-12


def test_circular_arcs_cross_midnight_and_are_phase_invariant():
    rng = np.random.default_rng(99)
    center = np.full(2000, 23.5)
    noise_angle = rng.vonmises(mu=0.0, kappa=7.0, size=center.size)
    observed = np.mod(center + 24.0 * noise_angle / (2.0 * np.pi), 24.0)
    cal = fit_circular_conformal_calibrator(
        center,
        observed,
        period=24.0,
        miscoverage=0.10,
    )
    arc = cal.arcs([23.8])[0]
    assert arc.wraps_origin is True
    assert arc.full_circle is False

    shift = 6.25
    shifted = fit_circular_conformal_calibrator(
        np.mod(center + shift, 24.0),
        np.mod(observed + shift, 24.0),
        period=24.0,
        miscoverage=0.10,
    )
    assert abs(shifted.distance_quantile - cal.distance_quantile) <= 1e-12

    minute = fit_circular_conformal_calibrator(
        center * 60.0,
        observed * 60.0,
        period=1440.0,
        miscoverage=0.10,
    )
    assert abs(minute.distance_quantile / 60.0 - cal.distance_quantile) <= 1e-12


def test_joint_bonferroni_region_has_separate_component_and_joint_coverage():
    rng = np.random.default_rng(7)
    n_cal = 6000
    height_center = rng.normal(size=n_cal)
    height_scale = np.exp(rng.normal(scale=0.2, size=n_cal))
    height_observed = height_center + height_scale * rng.normal(size=n_cal)

    time_center = rng.uniform(0.0, 24.0, size=n_cal)
    time_noise = rng.vonmises(0.0, 8.0, size=n_cal)
    time_observed = np.mod(time_center + 24.0 * time_noise / (2.0 * np.pi), 24.0)

    cal = fit_joint_bonferroni_conformal_calibrator(
        height_center,
        height_observed,
        time_center,
        time_observed,
        height_scale=height_scale,
        period=24.0,
        total_miscoverage=0.10,
    )
    assert cal.continuous.target_coverage == 0.95
    assert cal.circular.target_coverage == 0.95
    assert cal.joint_target_coverage == 0.90

    n_test = 12000
    hc = rng.normal(size=n_test)
    hs = np.exp(rng.normal(scale=0.2, size=n_test))
    hy = hc + hs * rng.normal(size=n_test)
    tc = rng.uniform(0.0, 24.0, size=n_test)
    tn = rng.vonmises(0.0, 8.0, size=n_test)
    ty = np.mod(tc + 24.0 * tn / (2.0 * np.pi), 24.0)
    report = cal.evaluate(hc, hy, tc, ty, height_scale=hs)

    assert 0.935 <= report.empirical_continuous_coverage <= 0.965
    assert 0.935 <= report.empirical_circular_coverage <= 0.965
    assert 0.89 <= report.empirical_joint_coverage <= 0.93
