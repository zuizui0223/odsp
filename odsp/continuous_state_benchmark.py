"""Known-truth validation for continuous scalar ODSP state prediction."""
from __future__ import annotations

from dataclasses import asdict, dataclass

import numpy as np

from .continuous_state import fit_gaussian_continuous_state_model


@dataclass(frozen=True)
class ContinuousStateBenchmarkFamily:
    family: str
    replicate_count: int
    mean_log_density_gain: float
    minimum_log_density_gain: float
    maximum_log_density_gain: float
    positive_gain_fraction: float
    negative_gain_fraction: float
    mean_crps_improvement: float
    mean_rmse_improvement: float

    def as_dict(self) -> dict[str, object]:
        return asdict(self)


@dataclass(frozen=True)
class ContinuousStateBenchmarkResult:
    seed: int
    replicate_count: int
    training_rows: int
    heldout_rows: int
    families: tuple[ContinuousStateBenchmarkFamily, ...]
    stable_all_positive: bool
    shifted_all_negative: bool
    null_mean_gain_near_zero: bool
    affine_gain_invariance_error: float
    interval_target_coverage: float
    interval_empirical_coverage: float
    passed: bool

    def as_dict(self) -> dict[str, object]:
        return {
            "seed": self.seed,
            "replicate_count": self.replicate_count,
            "training_rows": self.training_rows,
            "heldout_rows": self.heldout_rows,
            "families": [row.as_dict() for row in self.families],
            "stable_all_positive": self.stable_all_positive,
            "shifted_all_negative": self.shifted_all_negative,
            "null_mean_gain_near_zero": self.null_mean_gain_near_zero,
            "affine_gain_invariance_error": self.affine_gain_invariance_error,
            "interval_target_coverage": self.interval_target_coverage,
            "interval_empirical_coverage": self.interval_empirical_coverage,
            "passed": self.passed,
        }


def _sample(
    rng: np.random.Generator,
    n: int,
    beta: np.ndarray,
    *,
    intercept: float = 2.0,
    noise_sd: float = 0.7,
) -> tuple[np.ndarray, np.ndarray]:
    X = rng.normal(size=(n, beta.size))
    y = intercept + X @ beta + rng.normal(scale=noise_sd, size=n)
    return X, y


def _summarize(name: str, gains: list[float], crps: list[float], rmse: list[float]) -> ContinuousStateBenchmarkFamily:
    values = np.asarray(gains, dtype=float)
    return ContinuousStateBenchmarkFamily(
        family=name,
        replicate_count=int(values.size),
        mean_log_density_gain=float(np.mean(values)),
        minimum_log_density_gain=float(np.min(values)),
        maximum_log_density_gain=float(np.max(values)),
        positive_gain_fraction=float(np.mean(values > 0)),
        negative_gain_fraction=float(np.mean(values < 0)),
        mean_crps_improvement=float(np.mean(crps)),
        mean_rmse_improvement=float(np.mean(rmse)),
    )


def run_continuous_state_benchmark(
    *,
    seed: int = 20260905,
    replicates: int = 128,
    training_rows: int = 800,
    heldout_rows: int = 1600,
) -> ContinuousStateBenchmarkResult:
    if replicates < 1 or training_rows < 50 or heldout_rows < 50:
        raise ValueError("benchmark sizes are too small")
    rng = np.random.default_rng(seed)
    beta = np.array([1.3, -0.9, 0.6], dtype=float)
    zero = np.zeros_like(beta)

    store = {
        "stable_generalizing": ([], [], []),
        "unorganized": ([], [], []),
        "shifted_non_generalizing": ([], [], []),
    }
    for _ in range(replicates):
        X_train, y_train = _sample(rng, training_rows, beta)
        model = fit_gaussian_continuous_state_model(X_train, y_train)

        X_test, y_test = _sample(rng, heldout_rows, beta)
        score = model.score(X_test, y_test)
        store["stable_generalizing"][0].append(score.mean_log_density_gain)
        store["stable_generalizing"][1].append(score.crps_improvement)
        store["stable_generalizing"][2].append(score.rmse_improvement)

        X_shift, y_shift = _sample(rng, heldout_rows, -beta)
        shifted = model.score(X_shift, y_shift)
        store["shifted_non_generalizing"][0].append(shifted.mean_log_density_gain)
        store["shifted_non_generalizing"][1].append(shifted.crps_improvement)
        store["shifted_non_generalizing"][2].append(shifted.rmse_improvement)

        X_null_train, y_null_train = _sample(rng, training_rows, zero)
        null_model = fit_gaussian_continuous_state_model(X_null_train, y_null_train)
        X_null, y_null = _sample(rng, heldout_rows, zero)
        null_score = null_model.score(X_null, y_null)
        store["unorganized"][0].append(null_score.mean_log_density_gain)
        store["unorganized"][1].append(null_score.crps_improvement)
        store["unorganized"][2].append(null_score.rmse_improvement)

    families = tuple(
        _summarize(name, *store[name])
        for name in (
            "stable_generalizing",
            "unorganized",
            "shifted_non_generalizing",
        )
    )
    by_name = {row.family: row for row in families}

    # Response-unit invariance: the Jacobian term appears in both conditional and
    # marginal log densities, so their gain should be unchanged by y' = a*y+b.
    X_train, y_train = _sample(rng, 3000, beta)
    X_test, y_test = _sample(rng, 5000, beta)
    original = fit_gaussian_continuous_state_model(X_train, y_train)
    original_gain = original.score(X_test, y_test).mean_log_density_gain
    scale = 6.25
    offset = -17.0
    transformed = fit_gaussian_continuous_state_model(
        X_train, scale * y_train + offset
    )
    transformed_gain = transformed.score(
        X_test, scale * y_test + offset
    ).mean_log_density_gain
    affine_error = float(abs(original_gain - transformed_gain))

    # Reference Gaussian interval calibration under a correctly specified family.
    summaries = original.summarize(X_test, interval_level=0.90)
    interval_coverage = float(
        np.mean(
            [row.lower <= y <= row.upper for row, y in zip(summaries, y_test)]
        )
    )

    stable_all_positive = by_name["stable_generalizing"].positive_gain_fraction == 1.0
    shifted_all_negative = by_name["shifted_non_generalizing"].negative_gain_fraction == 1.0
    null_near_zero = abs(by_name["unorganized"].mean_log_density_gain) < 0.02
    passed = bool(
        stable_all_positive
        and shifted_all_negative
        and null_near_zero
        and affine_error <= 1e-10
        and 0.88 <= interval_coverage <= 0.92
    )
    return ContinuousStateBenchmarkResult(
        seed=int(seed),
        replicate_count=int(replicates),
        training_rows=int(training_rows),
        heldout_rows=int(heldout_rows),
        families=families,
        stable_all_positive=stable_all_positive,
        shifted_all_negative=shifted_all_negative,
        null_mean_gain_near_zero=null_near_zero,
        affine_gain_invariance_error=affine_error,
        interval_target_coverage=0.90,
        interval_empirical_coverage=interval_coverage,
        passed=passed,
    )
