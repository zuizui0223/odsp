"""End-to-end known-truth validation for the high-level trusted joint forecaster."""
from __future__ import annotations

from dataclasses import asdict, dataclass

import numpy as np

from .trusted_joint_forecast import fit_trusted_joint_state_forecaster


@dataclass(frozen=True)
class TrustedJointForecastBenchmarkResult:
    seed: int
    training_rows: int
    calibration_rows: int
    test_rows: int
    training_split_preserved: bool
    joint_log_density_gain: float
    coupling_log_density_gain: float
    empirical_joint_coverage: float
    same_domain_non_strict_fraction: float
    shifted_strict_extrapolation_fraction: float
    forecast_exposes_aggregate_confidence: bool
    passed: bool

    def as_dict(self) -> dict[str, object]:
        return asdict(self)


def _sample(
    rng: np.random.Generator,
    n: int,
    *,
    low: float,
    high: float,
) -> tuple[np.ndarray, np.ndarray, np.ndarray]:
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


def run_trusted_joint_forecast_benchmark(
    *,
    seed: int = 20260905,
    training_rows: int = 1200,
    calibration_rows: int = 1200,
    test_rows: int = 3000,
) -> TrustedJointForecastBenchmarkResult:
    if training_rows < 300 or calibration_rows < 300 or test_rows < 500:
        raise ValueError("benchmark split sizes are too small")
    rng = np.random.default_rng(seed)
    X_train, h_train, t_train = _sample(
        rng, training_rows, low=-2.0, high=2.0
    )
    X_cal, h_cal, t_cal = _sample(
        rng, calibration_rows, low=-1.5, high=1.5
    )
    X_test, h_test, t_test = _sample(
        rng, test_rows, low=-1.5, high=1.5
    )

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
    split_preserved = bool(
        forecaster.training_row_count == training_rows
        and forecaster.calibration_row_count == calibration_rows
        and forecaster.model.height_given_context_model.training_row_count
        == training_rows
        and forecaster.conformal.continuous.calibration_size == calibration_rows
        and forecaster.conformal.circular.calibration_size == calibration_rows
    )

    score = forecaster.score(X_test, h_test, t_test)
    coverage = forecaster.evaluate_conformal(X_test, h_test, t_test)

    forecast_rows = forecaster.forecast(X_test[:500])
    non_strict = float(
        np.mean(
            [
                row.novelty_category != "strict_extrapolation"
                for row in forecast_rows
            ]
        )
    )
    aggregate_confidence = any(
        "confidence" in row.as_dict() for row in forecast_rows
    )

    shifted_X = rng.uniform(6.0, 8.0, size=(200, X_train.shape[1]))
    shifted_rows = forecaster.forecast(shifted_X)
    strict_fraction = float(
        np.mean(
            [
                row.novelty_category == "strict_extrapolation"
                for row in shifted_rows
            ]
        )
    )

    passed = bool(
        split_preserved
        and score.mean_joint_log_density_gain > 0.0
        and score.mean_coupling_log_density_gain > 0.0
        and 0.88 <= coverage.empirical_joint_coverage <= 0.93
        and non_strict >= 0.90
        and strict_fraction == 1.0
        and not aggregate_confidence
    )
    return TrustedJointForecastBenchmarkResult(
        seed=int(seed),
        training_rows=int(training_rows),
        calibration_rows=int(calibration_rows),
        test_rows=int(test_rows),
        training_split_preserved=split_preserved,
        joint_log_density_gain=float(score.mean_joint_log_density_gain),
        coupling_log_density_gain=float(score.mean_coupling_log_density_gain),
        empirical_joint_coverage=float(coverage.empirical_joint_coverage),
        same_domain_non_strict_fraction=non_strict,
        shifted_strict_extrapolation_fraction=strict_fraction,
        forecast_exposes_aggregate_confidence=bool(aggregate_confidence),
        passed=passed,
    )
