"""Known-truth validation for circular ODSP state prediction."""
from __future__ import annotations

from dataclasses import asdict, dataclass

import numpy as np

from .circular_state import (
    circular_distance,
    fit_von_mises_circular_state_model,
)


@dataclass(frozen=True)
class CircularStateBenchmarkFamily:
    family: str
    replicate_count: int
    mean_log_density_gain: float
    minimum_log_density_gain: float
    maximum_log_density_gain: float
    positive_gain_fraction: float
    negative_gain_fraction: float
    mean_circular_mae_improvement: float

    def as_dict(self) -> dict[str, object]:
        return asdict(self)


@dataclass(frozen=True)
class CircularStateBenchmarkResult:
    seed: int
    replicate_count: int
    training_rows: int
    heldout_rows: int
    period: float
    families: tuple[CircularStateBenchmarkFamily, ...]
    stable_all_positive: bool
    shifted_all_negative: bool
    null_mean_gain_near_zero: bool
    phase_origin_gain_invariance_error: float
    period_unit_gain_invariance_error: float
    interval_target_coverage: float
    interval_empirical_coverage: float
    passed: bool

    def as_dict(self) -> dict[str, object]:
        return {
            "seed": self.seed,
            "replicate_count": self.replicate_count,
            "training_rows": self.training_rows,
            "heldout_rows": self.heldout_rows,
            "period": self.period,
            "families": [row.as_dict() for row in self.families],
            "stable_all_positive": self.stable_all_positive,
            "shifted_all_negative": self.shifted_all_negative,
            "null_mean_gain_near_zero": self.null_mean_gain_near_zero,
            "phase_origin_gain_invariance_error": self.phase_origin_gain_invariance_error,
            "period_unit_gain_invariance_error": self.period_unit_gain_invariance_error,
            "interval_target_coverage": self.interval_target_coverage,
            "interval_empirical_coverage": self.interval_empirical_coverage,
            "passed": self.passed,
        }


def _sample(
    rng: np.random.Generator,
    n: int,
    *,
    beta: np.ndarray,
    base_angle: float = 1.1,
    kappa: float = 8.0,
    response_shift: float = 0.0,
    period: float = 24.0,
) -> tuple[np.ndarray, np.ndarray]:
    X = rng.uniform(-1.0, 1.0, size=(n, beta.size))
    mean_angle = base_angle + X @ beta + response_shift
    angle = rng.vonmises(mean_angle, kappa)
    state = np.mod(angle, 2.0 * np.pi) * period / (2.0 * np.pi)
    return X, state


def _summarize(
    family: str,
    gains: list[float],
    mae_improvements: list[float],
) -> CircularStateBenchmarkFamily:
    values = np.asarray(gains, dtype=float)
    return CircularStateBenchmarkFamily(
        family=family,
        replicate_count=int(values.size),
        mean_log_density_gain=float(np.mean(values)),
        minimum_log_density_gain=float(np.min(values)),
        maximum_log_density_gain=float(np.max(values)),
        positive_gain_fraction=float(np.mean(values > 0.0)),
        negative_gain_fraction=float(np.mean(values < 0.0)),
        mean_circular_mae_improvement=float(np.mean(mae_improvements)),
    )


def run_circular_state_benchmark(
    *,
    seed: int = 20260905,
    replicates: int = 128,
    training_rows: int = 800,
    heldout_rows: int = 1600,
    period: float = 24.0,
) -> CircularStateBenchmarkResult:
    if replicates < 1 or training_rows < 50 or heldout_rows < 50:
        raise ValueError("benchmark sizes are too small")
    if period <= 0:
        raise ValueError("period must be positive")

    rng = np.random.default_rng(seed)
    beta = np.array([0.55, -0.35], dtype=float)
    zero = np.zeros_like(beta)
    store: dict[str, tuple[list[float], list[float]]] = {
        "stable_generalizing": ([], []),
        "unorganized": ([], []),
        "shifted_non_generalizing": ([], []),
    }

    for _ in range(replicates):
        X_train, y_train = _sample(
            rng, training_rows, beta=beta, period=period
        )
        model = fit_von_mises_circular_state_model(
            X_train, y_train, period=period
        )

        X_test, y_test = _sample(
            rng, heldout_rows, beta=beta, period=period
        )
        stable = model.score(X_test, y_test)
        store["stable_generalizing"][0].append(stable.mean_log_density_gain)
        store["stable_generalizing"][1].append(stable.circular_mae_improvement)

        X_shift, y_shift = _sample(
            rng,
            heldout_rows,
            beta=beta,
            response_shift=np.pi,
            period=period,
        )
        shifted = model.score(X_shift, y_shift)
        store["shifted_non_generalizing"][0].append(shifted.mean_log_density_gain)
        store["shifted_non_generalizing"][1].append(
            shifted.circular_mae_improvement
        )

        X_null_train, y_null_train = _sample(
            rng, training_rows, beta=zero, period=period
        )
        null_model = fit_von_mises_circular_state_model(
            X_null_train, y_null_train, period=period
        )
        X_null, y_null = _sample(
            rng, heldout_rows, beta=zero, period=period
        )
        null = null_model.score(X_null, y_null)
        store["unorganized"][0].append(null.mean_log_density_gain)
        store["unorganized"][1].append(null.circular_mae_improvement)

    families = tuple(
        _summarize(name, *store[name])
        for name in (
            "stable_generalizing",
            "unorganized",
            "shifted_non_generalizing",
        )
    )
    by_name = {row.family: row for row in families}

    # Frozen invariance and coverage checks on a larger same-process sample.
    X_train, y_train = _sample(rng, 3000, beta=beta, period=period)
    X_test, y_test = _sample(rng, 5000, beta=beta, period=period)
    original = fit_von_mises_circular_state_model(
        X_train, y_train, period=period
    )
    original_gain = original.score(X_test, y_test).mean_log_density_gain

    phase_shift = 5.75
    shifted_origin = fit_von_mises_circular_state_model(
        X_train,
        np.mod(y_train + phase_shift, period),
        period=period,
    )
    shifted_origin_gain = shifted_origin.score(
        X_test,
        np.mod(y_test + phase_shift, period),
    ).mean_log_density_gain
    phase_error = float(abs(original_gain - shifted_origin_gain))

    unit_scale = 60.0
    minute_model = fit_von_mises_circular_state_model(
        X_train,
        y_train * unit_scale,
        period=period * unit_scale,
    )
    minute_gain = minute_model.score(
        X_test,
        y_test * unit_scale,
    ).mean_log_density_gain
    unit_error = float(abs(original_gain - minute_gain))

    summaries = original.summarize(X_test, interval_level=0.90)
    predicted = original.predict_state(X_test)
    distance = circular_distance(y_test, predicted, period=period)
    half_width = np.asarray([row.arc_half_width for row in summaries], dtype=float)
    coverage = float(np.mean(distance <= half_width + 1e-12))

    stable_all_positive = by_name["stable_generalizing"].positive_gain_fraction == 1.0
    shifted_all_negative = by_name["shifted_non_generalizing"].negative_gain_fraction == 1.0
    null_near_zero = abs(by_name["unorganized"].mean_log_density_gain) < 0.02
    passed = bool(
        stable_all_positive
        and shifted_all_negative
        and null_near_zero
        and phase_error <= 1e-10
        and unit_error <= 1e-10
        and 0.87 <= coverage <= 0.93
    )
    return CircularStateBenchmarkResult(
        seed=int(seed),
        replicate_count=int(replicates),
        training_rows=int(training_rows),
        heldout_rows=int(heldout_rows),
        period=float(period),
        families=families,
        stable_all_positive=stable_all_positive,
        shifted_all_negative=shifted_all_negative,
        null_mean_gain_near_zero=null_near_zero,
        phase_origin_gain_invariance_error=phase_error,
        period_unit_gain_invariance_error=unit_error,
        interval_target_coverage=0.90,
        interval_empirical_coverage=coverage,
        passed=passed,
    )
