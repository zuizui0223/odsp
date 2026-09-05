"""Known-truth validation for continuous, circular and joint conformal uncertainty."""
from __future__ import annotations

from dataclasses import asdict, dataclass

import numpy as np

from .continuous_circular_conformal import (
    fit_circular_conformal_calibrator,
    fit_continuous_conformal_calibrator,
    fit_joint_bonferroni_conformal_calibrator,
)


@dataclass(frozen=True)
class ContinuousCircularConformalBenchmarkResult:
    seed: int
    replicate_count: int
    calibration_rows: int
    test_rows: int
    target_coverage: float
    mean_continuous_coverage: float
    mean_circular_coverage: float
    mean_joint_coverage: float
    mean_shifted_continuous_coverage: float
    mean_shifted_circular_coverage: float
    continuous_affine_quantile_error: float
    circular_phase_quantile_error: float
    circular_unit_relative_error: float
    passed: bool

    def as_dict(self) -> dict[str, object]:
        return asdict(self)


def run_continuous_circular_conformal_benchmark(
    *,
    seed: int = 20260905,
    replicates: int = 128,
    calibration_rows: int = 1000,
    test_rows: int = 2000,
) -> ContinuousCircularConformalBenchmarkResult:
    if replicates < 1 or calibration_rows < 100 or test_rows < 100:
        raise ValueError("benchmark sizes are too small")
    rng = np.random.default_rng(seed)

    continuous_coverage: list[float] = []
    circular_coverage: list[float] = []
    joint_coverage: list[float] = []
    shifted_continuous_coverage: list[float] = []
    shifted_circular_coverage: list[float] = []

    for _ in range(replicates):
        x_cal = rng.normal(size=calibration_rows)
        h_center_cal = 2.0 + 0.9 * x_cal
        h_scale_cal = np.exp(0.22 * x_cal)
        h_cal = h_center_cal + h_scale_cal * rng.normal(size=calibration_rows)

        t_center_cal = np.mod(8.0 + 3.0 * np.tanh(x_cal), 24.0)
        t_noise_cal = rng.vonmises(0.0, 7.5, size=calibration_rows)
        t_cal = np.mod(t_center_cal + 24.0 * t_noise_cal / (2.0 * np.pi), 24.0)

        h_conf = fit_continuous_conformal_calibrator(
            h_center_cal,
            h_cal,
            predicted_scale=h_scale_cal,
            miscoverage=0.10,
        )
        t_conf = fit_circular_conformal_calibrator(
            t_center_cal,
            t_cal,
            period=24.0,
            miscoverage=0.10,
        )
        joint_conf = fit_joint_bonferroni_conformal_calibrator(
            h_center_cal,
            h_cal,
            t_center_cal,
            t_cal,
            height_scale=h_scale_cal,
            period=24.0,
            total_miscoverage=0.10,
        )

        x_test = rng.normal(size=test_rows)
        h_center_test = 2.0 + 0.9 * x_test
        h_scale_test = np.exp(0.22 * x_test)
        h_test = h_center_test + h_scale_test * rng.normal(size=test_rows)
        t_center_test = np.mod(8.0 + 3.0 * np.tanh(x_test), 24.0)
        t_noise_test = rng.vonmises(0.0, 7.5, size=test_rows)
        t_test = np.mod(t_center_test + 24.0 * t_noise_test / (2.0 * np.pi), 24.0)

        continuous_coverage.append(
            h_conf.evaluate(
                h_center_test,
                h_test,
                predicted_scale=h_scale_test,
            ).empirical_coverage
        )
        circular_coverage.append(
            t_conf.evaluate(t_center_test, t_test).empirical_coverage
        )
        joint_coverage.append(
            joint_conf.evaluate(
                h_center_test,
                h_test,
                t_center_test,
                t_test,
                height_scale=h_scale_test,
            ).empirical_joint_coverage
        )

        # Deliberate post-calibration distribution shifts. These are outside the
        # exchangeability guarantee and should visibly reduce empirical coverage.
        h_shift = h_center_test + 2.75 * h_scale_test + h_scale_test * rng.normal(size=test_rows)
        t_shift = np.mod(t_center_test + 8.0 + 24.0 * rng.vonmises(0.0, 7.5, size=test_rows) / (2.0 * np.pi), 24.0)
        shifted_continuous_coverage.append(
            h_conf.evaluate(
                h_center_test,
                h_shift,
                predicted_scale=h_scale_test,
            ).empirical_coverage
        )
        shifted_circular_coverage.append(
            t_conf.evaluate(t_center_test, t_shift).empirical_coverage
        )

    # Representation invariance checks are performed on one large frozen sample.
    n = 6000
    x = rng.normal(size=n)
    center = 1.0 - 0.4 * x
    scale = np.exp(0.15 * x)
    observed = center + scale * rng.normal(size=n)
    original_h = fit_continuous_conformal_calibrator(
        center,
        observed,
        predicted_scale=scale,
        miscoverage=0.10,
    )
    factor = 6.25
    offset = -11.0
    transformed_h = fit_continuous_conformal_calibrator(
        factor * center + offset,
        factor * observed + offset,
        predicted_scale=factor * scale,
        miscoverage=0.10,
    )
    continuous_error = float(abs(original_h.score_quantile - transformed_h.score_quantile))

    t_center = rng.uniform(0.0, 24.0, size=n)
    t_noise = rng.vonmises(0.0, 6.5, size=n)
    t_obs = np.mod(t_center + 24.0 * t_noise / (2.0 * np.pi), 24.0)
    original_t = fit_circular_conformal_calibrator(
        t_center,
        t_obs,
        period=24.0,
        miscoverage=0.10,
    )
    phase = 5.75
    phase_t = fit_circular_conformal_calibrator(
        np.mod(t_center + phase, 24.0),
        np.mod(t_obs + phase, 24.0),
        period=24.0,
        miscoverage=0.10,
    )
    phase_error = float(abs(original_t.distance_quantile - phase_t.distance_quantile))
    minute_t = fit_circular_conformal_calibrator(
        t_center * 60.0,
        t_obs * 60.0,
        period=1440.0,
        miscoverage=0.10,
    )
    unit_error = float(
        abs(minute_t.distance_quantile / 60.0 - original_t.distance_quantile)
        / max(1.0, abs(original_t.distance_quantile))
    )

    mean_cont = float(np.mean(continuous_coverage))
    mean_circ = float(np.mean(circular_coverage))
    mean_joint = float(np.mean(joint_coverage))
    mean_shift_cont = float(np.mean(shifted_continuous_coverage))
    mean_shift_circ = float(np.mean(shifted_circular_coverage))

    passed = bool(
        0.885 <= mean_cont <= 0.915
        and 0.885 <= mean_circ <= 0.915
        and 0.89 <= mean_joint <= 0.93
        and mean_shift_cont < 0.60
        and mean_shift_circ < 0.60
        and continuous_error <= 1e-10
        and phase_error <= 1e-10
        and unit_error <= 1e-10
    )
    return ContinuousCircularConformalBenchmarkResult(
        seed=int(seed),
        replicate_count=int(replicates),
        calibration_rows=int(calibration_rows),
        test_rows=int(test_rows),
        target_coverage=0.90,
        mean_continuous_coverage=mean_cont,
        mean_circular_coverage=mean_circ,
        mean_joint_coverage=mean_joint,
        mean_shifted_continuous_coverage=mean_shift_cont,
        mean_shifted_circular_coverage=mean_shift_circ,
        continuous_affine_quantile_error=continuous_error,
        circular_phase_quantile_error=phase_error,
        circular_unit_relative_error=unit_error,
        passed=passed,
    )
