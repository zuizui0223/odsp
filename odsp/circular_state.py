"""Circular ecological-state density prediction for ODSP.

This module handles periodic scalar states such as local clock time without an
artificial boundary at the period origin.  The native reference learner predicts
a mean direction from weighted linear regressions of cosine and sine components
and uses a von Mises residual density.  The primary transfer quantity is

    E_heldout[log p_train(t | X) - log p_train(t)]

with both densities evaluated on the same circular state and period.
"""
from __future__ import annotations

from dataclasses import asdict, dataclass
import math
from typing import Sequence

import numpy as np

from .transferability import classify_independent_gains


_TWO_PI = 2.0 * math.pi


@dataclass(frozen=True)
class CircularStatePredictionSummary:
    row_index: int
    mean_state: float
    period: float
    concentration: float
    resultant_length: float
    circular_standard_deviation: float
    interval_level: float
    arc_lower: float
    arc_upper: float
    arc_half_width: float
    arc_wraps_origin: bool

    def as_dict(self) -> dict[str, object]:
        return asdict(self)


@dataclass(frozen=True)
class CircularStateScore:
    row_count: int
    total_weight: float
    mean_log_density: float
    mean_marginal_log_density: float
    mean_log_density_gain: float
    circular_mae: float
    marginal_circular_mae: float
    circular_mae_improvement: float

    def as_dict(self) -> dict[str, object]:
        return asdict(self)


@dataclass(frozen=True)
class CircularLogDensityGain:
    row_count: int
    total_weight: float
    mean_conditional_log_density: float
    mean_marginal_log_density: float
    mean_log_density_gain: float

    def as_dict(self) -> dict[str, object]:
        return asdict(self)


@dataclass(frozen=True)
class CircularGroupScore:
    group: str
    score: CircularStateScore

    def as_dict(self) -> dict[str, object]:
        return {"group": self.group, **self.score.as_dict()}


@dataclass(frozen=True)
class GroupedCircularStateScore:
    groups: tuple[CircularGroupScore, ...]
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


@dataclass
class VonMisesCircularStateModel:
    cosine_coefficients: np.ndarray
    sine_coefficients: np.ndarray
    residual_direction_offset: float
    concentration: float
    residual_resultant_length: float
    marginal_mean_direction: float
    marginal_concentration: float
    marginal_resultant_length: float
    period: float
    feature_count: int
    training_row_count: int
    training_total_weight: float
    residual_abs_angles_sorted: np.ndarray
    residual_abs_weight_cdf: np.ndarray

    def predict_angle(self, X: np.ndarray) -> np.ndarray:
        matrix = _validate_X(X, expected_features=self.feature_count)
        design = np.column_stack([np.ones(matrix.shape[0]), matrix])
        cosine = design @ self.cosine_coefficients
        sine = design @ self.sine_coefficients
        raw = _angles_from_components(
            cosine,
            sine,
            fallback=self.marginal_mean_direction,
        )
        return np.mod(raw + self.residual_direction_offset, _TWO_PI)

    def predict_state(self, X: np.ndarray) -> np.ndarray:
        return angle_to_state(self.predict_angle(X), period=self.period)

    def predict_log_density(self, X: np.ndarray, state: Sequence[float]) -> np.ndarray:
        matrix = _validate_X(X, expected_features=self.feature_count)
        target = _validate_state(state, matrix.shape[0], period=self.period)
        angle = state_to_angle(target, period=self.period)
        mean = self.predict_angle(matrix)
        return _von_mises_logpdf_state(
            angle,
            mean,
            self.concentration,
            period=self.period,
        )

    def marginal_log_density(self, state: Sequence[float]) -> np.ndarray:
        target = np.asarray(state, dtype=float)
        if target.ndim != 1 or target.size == 0 or not np.isfinite(target).all():
            raise ValueError("state must be a non-empty finite one-dimensional array")
        angle = state_to_angle(np.mod(target, self.period), period=self.period)
        mean = np.full(angle.shape[0], self.marginal_mean_direction, dtype=float)
        return _von_mises_logpdf_state(
            angle,
            mean,
            self.marginal_concentration,
            period=self.period,
        )

    def summarize(
        self,
        X: np.ndarray,
        *,
        interval_level: float = 0.90,
    ) -> tuple[CircularStatePredictionSummary, ...]:
        if not math.isfinite(interval_level) or not 0.0 < interval_level < 1.0:
            raise ValueError("interval_level must lie strictly between zero and one")
        matrix = _validate_X(X, expected_features=self.feature_count)
        mean_angle = self.predict_angle(matrix)
        mean_state = angle_to_state(mean_angle, period=self.period)
        half_angle = self._residual_half_angle(interval_level)
        half_state = half_angle * self.period / _TWO_PI
        circ_sd_angle = (
            math.sqrt(max(0.0, -2.0 * math.log(self.residual_resultant_length)))
            if self.residual_resultant_length > 0
            else math.inf
        )
        circ_sd_state = circ_sd_angle * self.period / _TWO_PI
        rows: list[CircularStatePredictionSummary] = []
        for index, center in enumerate(mean_state):
            lower_raw = float(center - half_state)
            upper_raw = float(center + half_state)
            wraps = bool(lower_raw < 0.0 or upper_raw >= self.period)
            rows.append(
                CircularStatePredictionSummary(
                    row_index=int(index),
                    mean_state=float(center),
                    period=float(self.period),
                    concentration=float(self.concentration),
                    resultant_length=float(self.residual_resultant_length),
                    circular_standard_deviation=float(circ_sd_state),
                    interval_level=float(interval_level),
                    arc_lower=float(lower_raw % self.period),
                    arc_upper=float(upper_raw % self.period),
                    arc_half_width=float(half_state),
                    arc_wraps_origin=wraps,
                )
            )
        return tuple(rows)

    def _residual_half_angle(self, level: float) -> float:
        index = int(np.searchsorted(self.residual_abs_weight_cdf, level, side="left"))
        index = min(index, self.residual_abs_angles_sorted.size - 1)
        return float(self.residual_abs_angles_sorted[index])

    def score(
        self,
        X: np.ndarray,
        state: Sequence[float],
        *,
        sample_weight: Sequence[float] | None = None,
    ) -> CircularStateScore:
        matrix = _validate_X(X, expected_features=self.feature_count)
        target = _validate_state(state, matrix.shape[0], period=self.period)
        weights = _validate_weights(sample_weight, matrix.shape[0])
        angle = state_to_angle(target, period=self.period)
        conditional_mean = self.predict_angle(matrix)
        marginal_mean = np.full(angle.shape[0], self.marginal_mean_direction, dtype=float)
        conditional_log = _von_mises_logpdf_state(
            angle,
            conditional_mean,
            self.concentration,
            period=self.period,
        )
        marginal_log = _von_mises_logpdf_state(
            angle,
            marginal_mean,
            self.marginal_concentration,
            period=self.period,
        )
        conditional_error = np.abs(_circular_difference(angle, conditional_mean))
        marginal_error = np.abs(_circular_difference(angle, marginal_mean))
        conversion = self.period / _TWO_PI
        conditional_mae = _weighted_mean(conditional_error, weights) * conversion
        marginal_mae = _weighted_mean(marginal_error, weights) * conversion
        mean_log = _weighted_mean(conditional_log, weights)
        mean_marginal_log = _weighted_mean(marginal_log, weights)
        return CircularStateScore(
            row_count=int(target.size),
            total_weight=float(weights.sum()),
            mean_log_density=float(mean_log),
            mean_marginal_log_density=float(mean_marginal_log),
            mean_log_density_gain=float(mean_log - mean_marginal_log),
            circular_mae=float(conditional_mae),
            marginal_circular_mae=float(marginal_mae),
            circular_mae_improvement=float(marginal_mae - conditional_mae),
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


def _validate_period(period: float) -> float:
    value = float(period)
    if not math.isfinite(value) or value <= 0:
        raise ValueError("period must be finite and positive")
    return value


def _validate_state(state: Sequence[float], n: int, *, period: float) -> np.ndarray:
    values = np.asarray(state, dtype=float)
    if values.shape != (n,):
        raise ValueError("state must contain one circular value per row")
    if not np.isfinite(values).all():
        raise ValueError("state must contain only finite values")
    return np.mod(values, period)


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


def state_to_angle(state: Sequence[float] | np.ndarray, *, period: float = 24.0) -> np.ndarray:
    value = _validate_period(period)
    state_array = np.asarray(state, dtype=float)
    if not np.isfinite(state_array).all():
        raise ValueError("state must contain only finite values")
    return np.mod(state_array, value) * (_TWO_PI / value)


def angle_to_state(angle: Sequence[float] | np.ndarray, *, period: float = 24.0) -> np.ndarray:
    value = _validate_period(period)
    angle_array = np.asarray(angle, dtype=float)
    if not np.isfinite(angle_array).all():
        raise ValueError("angle must contain only finite values")
    return np.mod(angle_array, _TWO_PI) * (value / _TWO_PI)


def _circular_difference(angle: np.ndarray, mean: np.ndarray) -> np.ndarray:
    return (np.asarray(angle) - np.asarray(mean) + math.pi) % _TWO_PI - math.pi


def circular_distance(
    first: Sequence[float] | np.ndarray,
    second: Sequence[float] | np.ndarray,
    *,
    period: float = 24.0,
) -> np.ndarray:
    value = _validate_period(period)
    a = state_to_angle(first, period=value)
    b = state_to_angle(second, period=value)
    return np.abs(_circular_difference(a, b)) * (value / _TWO_PI)


def _weighted_mean(values: np.ndarray, weights: np.ndarray) -> float:
    return float(np.sum(weights * values) / np.sum(weights))


def _weighted_circular_moment(angle: np.ndarray, weights: np.ndarray) -> tuple[float, float]:
    cosine = _weighted_mean(np.cos(angle), weights)
    sine = _weighted_mean(np.sin(angle), weights)
    direction = math.atan2(sine, cosine) % _TWO_PI
    length = min(1.0, max(0.0, math.hypot(cosine, sine)))
    return float(direction), float(length)


def _estimate_kappa(resultant_length: float) -> float:
    r = min(0.999999999, max(0.0, float(resultant_length)))
    if r < 1e-12:
        return 0.0
    if r < 0.53:
        kappa = 2.0 * r + r**3 + 5.0 * r**5 / 6.0
    elif r < 0.85:
        kappa = -0.4 + 1.39 * r + 0.43 / (1.0 - r)
    else:
        denominator = r**3 - 4.0 * r**2 + 3.0 * r
        kappa = 1.0 / max(denominator, 1e-12)
    return float(max(0.0, min(kappa, 1e6)))


def _log_i0(kappa: float) -> float:
    value = float(kappa)
    if value < 50.0:
        return float(math.log(float(np.i0(value))))
    # Asymptotic expansion avoids overflow for concentrated distributions.
    return float(
        value
        - 0.5 * math.log(_TWO_PI * value)
        + 1.0 / (8.0 * value)
        + 9.0 / (128.0 * value * value)
    )


def _von_mises_logpdf_state(
    angle: np.ndarray,
    mean: np.ndarray,
    kappa: float,
    *,
    period: float,
) -> np.ndarray:
    # Density is reported per original state unit. The Jacobian term cancels from
    # conditional-versus-marginal gain but makes the absolute density meaningful.
    log_jacobian = math.log(_TWO_PI / period)
    return (
        kappa * np.cos(np.asarray(angle) - np.asarray(mean))
        - math.log(_TWO_PI)
        - _log_i0(kappa)
        + log_jacobian
    )


def _angles_from_components(
    cosine: np.ndarray,
    sine: np.ndarray,
    *,
    fallback: float,
) -> np.ndarray:
    cosine = np.asarray(cosine, dtype=float)
    sine = np.asarray(sine, dtype=float)
    norm = np.hypot(cosine, sine)
    result = np.full(cosine.shape, float(fallback), dtype=float)
    usable = norm > 1e-12
    result[usable] = np.mod(np.arctan2(sine[usable], cosine[usable]), _TWO_PI)
    return result


def _weighted_residual_quantile_support(
    residual_abs: np.ndarray,
    weights: np.ndarray,
) -> tuple[np.ndarray, np.ndarray]:
    order = np.argsort(residual_abs, kind="mergesort")
    sorted_abs = np.asarray(residual_abs[order], dtype=float)
    sorted_weight = np.asarray(weights[order], dtype=float)
    cdf = np.cumsum(sorted_weight) / float(np.sum(sorted_weight))
    return sorted_abs, cdf


def fit_von_mises_circular_state_model(
    X: np.ndarray,
    state: Sequence[float],
    *,
    period: float = 24.0,
    sample_weight: Sequence[float] | None = None,
) -> VonMisesCircularStateModel:
    """Fit a transparent circular conditional-density reference learner."""

    period_value = _validate_period(period)
    matrix = _validate_X(X)
    target = _validate_state(state, matrix.shape[0], period=period_value)
    weights = _validate_weights(sample_weight, matrix.shape[0])
    angle = state_to_angle(target, period=period_value)

    marginal_direction, marginal_r = _weighted_circular_moment(angle, weights)
    marginal_kappa = _estimate_kappa(marginal_r)

    design = np.column_stack([np.ones(matrix.shape[0]), matrix])
    root_weight = np.sqrt(weights)
    weighted_design = design * root_weight[:, None]
    cosine_coefficients, _, _, _ = np.linalg.lstsq(
        weighted_design,
        np.cos(angle) * root_weight,
        rcond=None,
    )
    sine_coefficients, _, _, _ = np.linalg.lstsq(
        weighted_design,
        np.sin(angle) * root_weight,
        rcond=None,
    )
    raw_angle = _angles_from_components(
        design @ cosine_coefficients,
        design @ sine_coefficients,
        fallback=marginal_direction,
    )
    residual = _circular_difference(angle, raw_angle)
    residual_offset, residual_r = _weighted_circular_moment(residual, weights)
    # Residual moment direction is the calibration offset of the raw predictor.
    fitted_angle = np.mod(raw_angle + residual_offset, _TWO_PI)
    calibrated_residual = _circular_difference(angle, fitted_angle)
    _, calibrated_r = _weighted_circular_moment(calibrated_residual, weights)
    concentration = _estimate_kappa(calibrated_r)
    sorted_abs, cdf = _weighted_residual_quantile_support(
        np.abs(calibrated_residual), weights
    )

    return VonMisesCircularStateModel(
        cosine_coefficients=np.asarray(cosine_coefficients, dtype=float),
        sine_coefficients=np.asarray(sine_coefficients, dtype=float),
        residual_direction_offset=float(residual_offset),
        concentration=float(concentration),
        residual_resultant_length=float(calibrated_r),
        marginal_mean_direction=float(marginal_direction),
        marginal_concentration=float(marginal_kappa),
        marginal_resultant_length=float(marginal_r),
        period=float(period_value),
        feature_count=int(matrix.shape[1]),
        training_row_count=int(matrix.shape[0]),
        training_total_weight=float(weights.sum()),
        residual_abs_angles_sorted=sorted_abs,
        residual_abs_weight_cdf=cdf,
    )


def score_circular_log_density_gain(
    conditional_log_density: Sequence[float],
    marginal_log_density: Sequence[float],
    *,
    sample_weight: Sequence[float] | None = None,
) -> CircularLogDensityGain:
    conditional = np.asarray(conditional_log_density, dtype=float)
    marginal = np.asarray(marginal_log_density, dtype=float)
    if conditional.ndim != 1 or conditional.size == 0 or marginal.shape != conditional.shape:
        raise ValueError("conditional and marginal log densities must be equal-length non-empty vectors")
    if not np.isfinite(conditional).all() or not np.isfinite(marginal).all():
        raise ValueError("log densities must be finite")
    weights = _validate_weights(sample_weight, conditional.size)
    mean_conditional = _weighted_mean(conditional, weights)
    mean_marginal = _weighted_mean(marginal, weights)
    return CircularLogDensityGain(
        row_count=int(conditional.size),
        total_weight=float(weights.sum()),
        mean_conditional_log_density=float(mean_conditional),
        mean_marginal_log_density=float(mean_marginal),
        mean_log_density_gain=float(mean_conditional - mean_marginal),
    )


def score_circular_state_groups(
    model: VonMisesCircularStateModel,
    X: np.ndarray,
    state: Sequence[float],
    groups: Sequence[object],
    *,
    sample_weight: Sequence[float] | None = None,
    tolerance: float = 0.0,
) -> GroupedCircularStateScore:
    matrix = _validate_X(X, expected_features=model.feature_count)
    target = _validate_state(state, matrix.shape[0], period=model.period)
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

    rows: list[CircularGroupScore] = []
    for value in ordered:
        mask = group_values == value
        if float(weights[mask].sum()) <= 0:
            continue
        rows.append(
            CircularGroupScore(
                group=str(value),
                score=model.score(
                    matrix[mask],
                    target[mask],
                    sample_weight=weights[mask],
                ),
            )
        )
    if not rows:
        raise ValueError("no positive-weight independent group remains")
    return GroupedCircularStateScore(
        groups=tuple(rows),
        gain_category=classify_independent_gains(
            [row.score.mean_log_density_gain for row in rows],
            tolerance=tolerance,
        ),
    )
