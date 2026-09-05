"""Continuous scalar ecological-state prediction for ODSP.

This module removes the need to discretize a scalar ecological state such as
altitude or depth when a continuous response is scientifically meaningful.  The
native reference learner is intentionally transparent: weighted linear Gaussian
regression with a constant residual scale.  More complex learners can still be
compared through the model-agnostic held-out log-density gain helper.

The primary transfer quantity is the continuous analogue of the discrete ODSP
score::

    E_heldout[log p_train(a | X) - log p_train(a)]

where ``a`` is the realized continuous ecological state.  Positive gain means the
context-conditioned density assigns greater held-out density than the lower-
information training marginal density.  CRPS and point-prediction error are
reported as complementary diagnostics; they do not override the primary gain.
"""
from __future__ import annotations

from dataclasses import asdict, dataclass
import math
from statistics import NormalDist
from typing import Mapping, Sequence

import numpy as np

from .transferability import classify_independent_gains


_LOG_2PI = math.log(2.0 * math.pi)
_INV_SQRT_PI = 1.0 / math.sqrt(math.pi)
_STANDARD_NORMAL = NormalDist()


@dataclass(frozen=True)
class ContinuousStatePredictionSummary:
    row_index: int
    mean: float
    standard_deviation: float
    median: float
    interval_level: float
    lower: float
    upper: float

    def as_dict(self) -> dict[str, object]:
        return asdict(self)


@dataclass(frozen=True)
class ContinuousStateScore:
    row_count: int
    total_weight: float
    mean_log_density: float
    mean_marginal_log_density: float
    mean_log_density_gain: float
    rmse: float
    marginal_rmse: float
    rmse_improvement: float
    crps: float
    marginal_crps: float
    crps_improvement: float

    def as_dict(self) -> dict[str, object]:
        return asdict(self)


@dataclass(frozen=True)
class ContinuousGroupScore:
    group: str
    score: ContinuousStateScore

    def as_dict(self) -> dict[str, object]:
        return {"group": self.group, **self.score.as_dict()}


@dataclass(frozen=True)
class GroupedContinuousStateScore:
    groups: tuple[ContinuousGroupScore, ...]
    gain_category: str

    @property
    def gains(self) -> tuple[float, ...]:
        return tuple(row.score.mean_log_density_gain for row in self.groups)

    def as_dict(self) -> dict[str, object]:
        return {
            "groups": [row.as_dict() for row in self.groups],
            "gains": list(self.gains),
            "gain_category": self.gain_category,
        }


@dataclass(frozen=True)
class ContinuousLogDensityGain:
    row_count: int
    total_weight: float
    mean_conditional_log_density: float
    mean_marginal_log_density: float
    mean_log_density_gain: float

    def as_dict(self) -> dict[str, object]:
        return asdict(self)


@dataclass
class GaussianContinuousStateModel:
    """Weighted linear-Gaussian reference learner for a continuous state."""

    coefficients: np.ndarray
    residual_standard_deviation: float
    marginal_mean: float
    marginal_standard_deviation: float
    feature_count: int
    training_row_count: int
    training_total_weight: float

    def predict_mean(self, X: np.ndarray) -> np.ndarray:
        matrix = _validate_X(X, expected_features=self.feature_count)
        design = np.column_stack([np.ones(matrix.shape[0]), matrix])
        return np.asarray(design @ self.coefficients, dtype=float)

    def predict_standard_deviation(self, X: np.ndarray) -> np.ndarray:
        matrix = _validate_X(X, expected_features=self.feature_count)
        return np.full(matrix.shape[0], self.residual_standard_deviation, dtype=float)

    def predict_log_density(self, X: np.ndarray, y: Sequence[float]) -> np.ndarray:
        matrix = _validate_X(X, expected_features=self.feature_count)
        target = _validate_y(y, matrix.shape[0])
        return _normal_logpdf(
            target,
            self.predict_mean(matrix),
            self.residual_standard_deviation,
        )

    def marginal_log_density(self, y: Sequence[float]) -> np.ndarray:
        target = np.asarray(y, dtype=float)
        if target.ndim != 1 or target.size == 0 or not np.isfinite(target).all():
            raise ValueError("y must be a non-empty finite one-dimensional array")
        return _normal_logpdf(
            target,
            np.full(target.shape[0], self.marginal_mean, dtype=float),
            self.marginal_standard_deviation,
        )

    def summarize(
        self,
        X: np.ndarray,
        *,
        interval_level: float = 0.90,
    ) -> tuple[ContinuousStatePredictionSummary, ...]:
        if not math.isfinite(interval_level) or not 0.0 < interval_level < 1.0:
            raise ValueError("interval_level must lie strictly between zero and one")
        matrix = _validate_X(X, expected_features=self.feature_count)
        means = self.predict_mean(matrix)
        z = _STANDARD_NORMAL.inv_cdf((1.0 + interval_level) / 2.0)
        half_width = z * self.residual_standard_deviation
        return tuple(
            ContinuousStatePredictionSummary(
                row_index=int(row),
                mean=float(mean),
                standard_deviation=float(self.residual_standard_deviation),
                median=float(mean),
                interval_level=float(interval_level),
                lower=float(mean - half_width),
                upper=float(mean + half_width),
            )
            for row, mean in enumerate(means)
        )

    def score(
        self,
        X: np.ndarray,
        y: Sequence[float],
        *,
        sample_weight: Sequence[float] | None = None,
    ) -> ContinuousStateScore:
        matrix = _validate_X(X, expected_features=self.feature_count)
        target = _validate_y(y, matrix.shape[0])
        weights = _validate_weights(sample_weight, matrix.shape[0])
        mean = self.predict_mean(matrix)
        conditional_log = _normal_logpdf(
            target, mean, self.residual_standard_deviation
        )
        marginal_mean = np.full(target.shape[0], self.marginal_mean, dtype=float)
        marginal_log = _normal_logpdf(
            target, marginal_mean, self.marginal_standard_deviation
        )
        return _continuous_score_from_gaussian(
            target,
            mean,
            self.residual_standard_deviation,
            marginal_mean,
            self.marginal_standard_deviation,
            conditional_log,
            marginal_log,
            weights,
        )


def _validate_X(X: np.ndarray, *, expected_features: int | None = None) -> np.ndarray:
    matrix = np.asarray(X, dtype=float)
    if matrix.ndim != 2 or matrix.shape[0] == 0 or matrix.shape[1] == 0:
        raise ValueError("X must be a non-empty two-dimensional numeric matrix")
    if expected_features is not None and matrix.shape[1] != int(expected_features):
        raise ValueError("X has a different number of features than the fitted model")
    if not np.isfinite(matrix).all():
        raise ValueError("X must contain only finite values")
    return matrix


def _validate_y(y: Sequence[float], n: int) -> np.ndarray:
    target = np.asarray(y, dtype=float)
    if target.shape != (n,):
        raise ValueError("y must contain one continuous state value per row")
    if not np.isfinite(target).all():
        raise ValueError("y must contain only finite values")
    return target


def _validate_weights(weights: Sequence[float] | None, n: int) -> np.ndarray:
    if weights is None:
        return np.ones(n, dtype=float)
    values = np.asarray(weights, dtype=float)
    if values.shape != (n,):
        raise ValueError("sample_weight must contain one value per row")
    if not np.isfinite(values).all() or np.any(values < 0):
        raise ValueError("sample_weight must be finite and non-negative")
    if not float(values.sum()) > 0:
        raise ValueError("sample_weight must have positive total mass")
    return values


def _weighted_mean(values: np.ndarray, weights: np.ndarray) -> float:
    return float(np.sum(weights * values) / np.sum(weights))


def _weighted_variance(values: np.ndarray, weights: np.ndarray, mean: float) -> float:
    return float(np.sum(weights * np.square(values - mean)) / np.sum(weights))


def _normal_logpdf(
    y: np.ndarray,
    mean: np.ndarray,
    standard_deviation: float,
) -> np.ndarray:
    if not math.isfinite(standard_deviation) or standard_deviation <= 0:
        raise ValueError("standard deviation must be finite and positive")
    z = (np.asarray(y, dtype=float) - np.asarray(mean, dtype=float)) / standard_deviation
    return -0.5 * _LOG_2PI - math.log(standard_deviation) - 0.5 * np.square(z)


def _normal_crps(
    y: np.ndarray,
    mean: np.ndarray,
    standard_deviation: float,
) -> np.ndarray:
    """Closed-form CRPS for N(mean, standard_deviation^2)."""

    z = (np.asarray(y, dtype=float) - np.asarray(mean, dtype=float)) / standard_deviation
    # numpy does not expose erf in its minimal public API on every supported build;
    # use the scalar math implementation through fromiter for deterministic support.
    cdf = np.fromiter(
        (0.5 * (1.0 + math.erf(float(value) / math.sqrt(2.0))) for value in z),
        dtype=float,
        count=z.size,
    )
    pdf = np.exp(-0.5 * np.square(z)) / math.sqrt(2.0 * math.pi)
    return standard_deviation * (
        z * (2.0 * cdf - 1.0) + 2.0 * pdf - _INV_SQRT_PI
    )


def fit_gaussian_continuous_state_model(
    X: np.ndarray,
    y: Sequence[float],
    *,
    sample_weight: Sequence[float] | None = None,
    minimum_relative_scale: float = 1e-8,
) -> GaussianContinuousStateModel:
    """Fit weighted least-squares mean and Gaussian residual/marginal densities."""

    if not math.isfinite(minimum_relative_scale) or not 0.0 < minimum_relative_scale < 1.0:
        raise ValueError("minimum_relative_scale must lie strictly between zero and one")
    matrix = _validate_X(X)
    target = _validate_y(y, matrix.shape[0])
    weights = _validate_weights(sample_weight, matrix.shape[0])

    marginal_mean = _weighted_mean(target, weights)
    marginal_variance = _weighted_variance(target, weights, marginal_mean)
    if marginal_variance <= 0:
        raise ValueError("continuous state requires positive weighted training variance")
    marginal_sd = math.sqrt(marginal_variance)

    design = np.column_stack([np.ones(matrix.shape[0]), matrix])
    root_weight = np.sqrt(weights)
    weighted_design = design * root_weight[:, None]
    weighted_target = target * root_weight
    coefficients, _, _, _ = np.linalg.lstsq(weighted_design, weighted_target, rcond=None)
    fitted = design @ coefficients
    residual_variance = _weighted_variance(target - fitted, weights, 0.0)
    floor = max(1e-12, minimum_relative_scale * marginal_sd)
    residual_sd = max(math.sqrt(max(0.0, residual_variance)), floor)

    return GaussianContinuousStateModel(
        coefficients=np.asarray(coefficients, dtype=float),
        residual_standard_deviation=float(residual_sd),
        marginal_mean=float(marginal_mean),
        marginal_standard_deviation=float(marginal_sd),
        feature_count=int(matrix.shape[1]),
        training_row_count=int(matrix.shape[0]),
        training_total_weight=float(weights.sum()),
    )


def _continuous_score_from_gaussian(
    y: np.ndarray,
    mean: np.ndarray,
    conditional_sd: float,
    marginal_mean: np.ndarray,
    marginal_sd: float,
    conditional_log: np.ndarray,
    marginal_log: np.ndarray,
    weights: np.ndarray,
) -> ContinuousStateScore:
    conditional_error = y - mean
    marginal_error = y - marginal_mean
    rmse = math.sqrt(_weighted_mean(np.square(conditional_error), weights))
    marginal_rmse = math.sqrt(_weighted_mean(np.square(marginal_error), weights))
    crps = _weighted_mean(_normal_crps(y, mean, conditional_sd), weights)
    marginal_crps = _weighted_mean(
        _normal_crps(y, marginal_mean, marginal_sd), weights
    )
    mean_log = _weighted_mean(conditional_log, weights)
    mean_marginal_log = _weighted_mean(marginal_log, weights)
    return ContinuousStateScore(
        row_count=int(y.size),
        total_weight=float(weights.sum()),
        mean_log_density=mean_log,
        mean_marginal_log_density=mean_marginal_log,
        mean_log_density_gain=float(mean_log - mean_marginal_log),
        rmse=float(rmse),
        marginal_rmse=float(marginal_rmse),
        rmse_improvement=float(marginal_rmse - rmse),
        crps=float(crps),
        marginal_crps=float(marginal_crps),
        crps_improvement=float(marginal_crps - crps),
    )


def score_continuous_log_density_gain(
    conditional_log_density: Sequence[float],
    marginal_log_density: Sequence[float],
    *,
    sample_weight: Sequence[float] | None = None,
) -> ContinuousLogDensityGain:
    """Score any external continuous state density at the realized held-out rows."""

    conditional = np.asarray(conditional_log_density, dtype=float)
    marginal = np.asarray(marginal_log_density, dtype=float)
    if conditional.ndim != 1 or conditional.size == 0 or marginal.shape != conditional.shape:
        raise ValueError("conditional and marginal log densities must be equal-length non-empty vectors")
    if not np.isfinite(conditional).all() or not np.isfinite(marginal).all():
        raise ValueError("log densities must be finite")
    weights = _validate_weights(sample_weight, conditional.size)
    mean_conditional = _weighted_mean(conditional, weights)
    mean_marginal = _weighted_mean(marginal, weights)
    return ContinuousLogDensityGain(
        row_count=int(conditional.size),
        total_weight=float(weights.sum()),
        mean_conditional_log_density=float(mean_conditional),
        mean_marginal_log_density=float(mean_marginal),
        mean_log_density_gain=float(mean_conditional - mean_marginal),
    )


def score_continuous_state_groups(
    model: GaussianContinuousStateModel,
    X: np.ndarray,
    y: Sequence[float],
    groups: Sequence[object],
    *,
    sample_weight: Sequence[float] | None = None,
    tolerance: float = 0.0,
) -> GroupedContinuousStateScore:
    """Score independent held-out groups separately under the frozen model."""

    matrix = _validate_X(X, expected_features=model.feature_count)
    target = _validate_y(y, matrix.shape[0])
    weights = _validate_weights(sample_weight, matrix.shape[0])
    group_values = np.asarray(groups, dtype=object)
    if group_values.shape != (matrix.shape[0],):
        raise ValueError("groups must contain one group identifier per row")

    ordered: list[object] = []
    seen: set[object] = set()
    for value in group_values.tolist():
        try:
            if value not in seen:
                seen.add(value)
                ordered.append(value)
        except TypeError as exc:
            raise ValueError("group identifiers must be hashable") from exc

    rows: list[ContinuousGroupScore] = []
    for value in ordered:
        mask = group_values == value
        if float(weights[mask].sum()) <= 0:
            continue
        score = model.score(
            matrix[mask], target[mask], sample_weight=weights[mask]
        )
        rows.append(ContinuousGroupScore(group=str(value), score=score))
    if not rows:
        raise ValueError("no positive-weight independent group remains")
    gains = [row.score.mean_log_density_gain for row in rows]
    return GroupedContinuousStateScore(
        groups=tuple(rows),
        gain_category=classify_independent_gains(gains, tolerance=tolerance),
    )
