"""Joint continuous-circular ecological-state prediction for ODSP.

The reference factorization is autoregressive::

    p(z, t | X) = p(t | X) p(z | X, t)

where ``t`` is a circular state and ``z`` a continuous scalar state.  The primary
contextual joint gain compares this density with an X-free training joint
comparator ``p(t) p(z|t)``.  A second, directional coupling gain asks whether the
realized circular state improves continuous-state prediction beyond context alone::

    E[log p(z | X,t) - log p(z | X)]

The coupling gain is predictive and directional; it is not a symmetric causal
interaction or evidence of temporal/vertical displacement.
"""
from __future__ import annotations

from dataclasses import asdict, dataclass
import math
from typing import Sequence

import numpy as np

from .circular_state import (
    VonMisesCircularStateModel,
    angle_to_state,
    fit_von_mises_circular_state_model,
    state_to_angle,
)
from .continuous_state import (
    GaussianContinuousStateModel,
    fit_gaussian_continuous_state_model,
)
from .transferability import classify_independent_gains


@dataclass(frozen=True)
class JointStatePredictionSummary:
    row_index: int
    time_mean_state: float
    time_period: float
    time_concentration: float
    time_arc_level: float
    time_arc_lower: float
    time_arc_upper: float
    time_arc_wraps_origin: bool
    height_mean_at_time_mode: float
    height_standard_deviation: float
    height_interval_level: float
    height_lower_at_time_mode: float
    height_upper_at_time_mode: float

    def as_dict(self) -> dict[str, object]:
        return asdict(self)


@dataclass(frozen=True)
class JointStateScore:
    row_count: int
    total_weight: float
    mean_joint_log_density: float
    mean_joint_marginal_log_density: float
    mean_joint_log_density_gain: float
    mean_factorized_contextual_log_density: float
    mean_coupling_log_density_gain: float

    def as_dict(self) -> dict[str, object]:
        return asdict(self)


@dataclass(frozen=True)
class JointLogDensityGain:
    row_count: int
    total_weight: float
    mean_conditional_joint_log_density: float
    mean_marginal_joint_log_density: float
    mean_joint_log_density_gain: float
    mean_factorized_contextual_log_density: float | None
    mean_coupling_log_density_gain: float | None

    def as_dict(self) -> dict[str, object]:
        return asdict(self)


@dataclass(frozen=True)
class JointStateGroupScore:
    group: str
    score: JointStateScore

    def as_dict(self) -> dict[str, object]:
        return {"group": self.group, **self.score.as_dict()}


@dataclass(frozen=True)
class GroupedJointStateScore:
    groups: tuple[JointStateGroupScore, ...]
    joint_gain_category: str
    coupling_gain_category: str

    @property
    def joint_gains(self) -> tuple[float, ...]:
        return tuple(row.score.mean_joint_log_density_gain for row in self.groups)

    @property
    def coupling_gains(self) -> tuple[float, ...]:
        return tuple(row.score.mean_coupling_log_density_gain for row in self.groups)

    def as_dict(self) -> dict[str, object]:
        return {
            "groups": [row.as_dict() for row in self.groups],
            "joint_gains": list(self.joint_gains),
            "coupling_gains": list(self.coupling_gains),
            "joint_gain_category": self.joint_gain_category,
            "coupling_gain_category": self.coupling_gain_category,
        }


@dataclass
class JointContinuousCircularStateModel:
    time_model: VonMisesCircularStateModel
    height_given_context_model: GaussianContinuousStateModel
    height_given_context_time_model: GaussianContinuousStateModel
    height_given_time_model: GaussianContinuousStateModel
    context_feature_count: int
    period: float

    def _validate_X(self, X: np.ndarray) -> np.ndarray:
        matrix = np.asarray(X, dtype=float)
        if matrix.ndim != 2 or matrix.shape[0] == 0:
            raise ValueError("X must be a non-empty two-dimensional numeric matrix")
        if matrix.shape[1] != self.context_feature_count:
            raise ValueError("X has a different number of features than the fitted joint model")
        if not np.isfinite(matrix).all():
            raise ValueError("X must contain only finite values")
        return matrix

    def _time_features(self, time_state: Sequence[float]) -> np.ndarray:
        state = np.asarray(time_state, dtype=float)
        if state.ndim != 1 or state.size == 0 or not np.isfinite(state).all():
            raise ValueError("time_state must be a non-empty finite vector")
        angle = state_to_angle(np.mod(state, self.period), period=self.period)
        return np.column_stack([np.sin(angle), np.cos(angle)])

    def _context_time_features(
        self,
        X: np.ndarray,
        time_state: Sequence[float],
    ) -> np.ndarray:
        matrix = self._validate_X(X)
        time_features = self._time_features(time_state)
        if time_features.shape[0] != matrix.shape[0]:
            raise ValueError("time_state must contain one value per context row")
        return np.column_stack([matrix, time_features])

    def joint_log_density(
        self,
        X: np.ndarray,
        height: Sequence[float],
        time_state: Sequence[float],
    ) -> np.ndarray:
        matrix = self._validate_X(X)
        height_values = _validate_height(height, matrix.shape[0])
        context_time = self._context_time_features(matrix, time_state)
        return (
            self.time_model.predict_log_density(matrix, time_state)
            + self.height_given_context_time_model.predict_log_density(
                context_time, height_values
            )
        )

    def marginal_joint_log_density(
        self,
        height: Sequence[float],
        time_state: Sequence[float],
    ) -> np.ndarray:
        height_values = np.asarray(height, dtype=float)
        time_values = np.asarray(time_state, dtype=float)
        if height_values.ndim != 1 or height_values.size == 0:
            raise ValueError("height must be a non-empty vector")
        if time_values.shape != height_values.shape:
            raise ValueError("height and time_state must have equal length")
        if not np.isfinite(height_values).all() or not np.isfinite(time_values).all():
            raise ValueError("height and time_state must be finite")
        time_features = self._time_features(time_values)
        return (
            self.time_model.marginal_log_density(time_values)
            + self.height_given_time_model.predict_log_density(
                time_features, height_values
            )
        )

    def factorized_contextual_log_density(
        self,
        X: np.ndarray,
        height: Sequence[float],
        time_state: Sequence[float],
    ) -> np.ndarray:
        matrix = self._validate_X(X)
        height_values = _validate_height(height, matrix.shape[0])
        return (
            self.time_model.predict_log_density(matrix, time_state)
            + self.height_given_context_model.predict_log_density(
                matrix, height_values
            )
        )

    def score(
        self,
        X: np.ndarray,
        height: Sequence[float],
        time_state: Sequence[float],
        *,
        sample_weight: Sequence[float] | None = None,
    ) -> JointStateScore:
        matrix = self._validate_X(X)
        height_values = _validate_height(height, matrix.shape[0])
        time_values = _validate_time(time_state, matrix.shape[0])
        weights = _validate_weights(sample_weight, matrix.shape[0])
        joint = self.joint_log_density(matrix, height_values, time_values)
        marginal = self.marginal_joint_log_density(height_values, time_values)
        factorized = self.factorized_contextual_log_density(
            matrix, height_values, time_values
        )
        mean_joint = _weighted_mean(joint, weights)
        mean_marginal = _weighted_mean(marginal, weights)
        mean_factorized = _weighted_mean(factorized, weights)
        return JointStateScore(
            row_count=int(matrix.shape[0]),
            total_weight=float(weights.sum()),
            mean_joint_log_density=float(mean_joint),
            mean_joint_marginal_log_density=float(mean_marginal),
            mean_joint_log_density_gain=float(mean_joint - mean_marginal),
            mean_factorized_contextual_log_density=float(mean_factorized),
            mean_coupling_log_density_gain=float(mean_joint - mean_factorized),
        )

    def summarize(
        self,
        X: np.ndarray,
        *,
        time_interval_level: float = 0.90,
        height_interval_level: float = 0.90,
    ) -> tuple[JointStatePredictionSummary, ...]:
        matrix = self._validate_X(X)
        time_rows = self.time_model.summarize(
            matrix, interval_level=time_interval_level
        )
        time_mode = np.asarray([row.mean_state for row in time_rows], dtype=float)
        context_time = self._context_time_features(matrix, time_mode)
        height_rows = self.height_given_context_time_model.summarize(
            context_time, interval_level=height_interval_level
        )
        return tuple(
            JointStatePredictionSummary(
                row_index=int(index),
                time_mean_state=float(time_row.mean_state),
                time_period=float(time_row.period),
                time_concentration=float(time_row.concentration),
                time_arc_level=float(time_row.interval_level),
                time_arc_lower=float(time_row.arc_lower),
                time_arc_upper=float(time_row.arc_upper),
                time_arc_wraps_origin=bool(time_row.arc_wraps_origin),
                height_mean_at_time_mode=float(height_row.mean),
                height_standard_deviation=float(height_row.standard_deviation),
                height_interval_level=float(height_row.interval_level),
                height_lower_at_time_mode=float(height_row.lower),
                height_upper_at_time_mode=float(height_row.upper),
            )
            for index, (time_row, height_row) in enumerate(
                zip(time_rows, height_rows)
            )
        )

    def sample_joint(
        self,
        X: np.ndarray,
        *,
        draws_per_row: int = 100,
        random_state: int = 20260905,
    ) -> tuple[np.ndarray, np.ndarray]:
        matrix = self._validate_X(X)
        if draws_per_row < 1:
            raise ValueError("draws_per_row must be at least one")
        rng = np.random.default_rng(random_state)
        mean_angle = self.time_model.predict_angle(matrix)
        n = matrix.shape[0]
        time_angle = np.empty((n, draws_per_row), dtype=float)
        for row in range(n):
            time_angle[row] = rng.vonmises(
                mean_angle[row],
                self.time_model.concentration,
                size=draws_per_row,
            )
        time_state = angle_to_state(time_angle, period=self.period)
        repeated_X = np.repeat(matrix, draws_per_row, axis=0)
        flat_time = time_state.reshape(-1)
        context_time = self._context_time_features(repeated_X, flat_time)
        height_mean = self.height_given_context_time_model.predict_mean(context_time)
        height = rng.normal(
            loc=height_mean,
            scale=self.height_given_context_time_model.residual_standard_deviation,
        ).reshape(n, draws_per_row)
        return height, time_state


def _validate_height(height: Sequence[float], n: int) -> np.ndarray:
    values = np.asarray(height, dtype=float)
    if values.shape != (n,) or not np.isfinite(values).all():
        raise ValueError("height must contain one finite value per row")
    return values


def _validate_time(time_state: Sequence[float], n: int) -> np.ndarray:
    values = np.asarray(time_state, dtype=float)
    if values.shape != (n,) or not np.isfinite(values).all():
        raise ValueError("time_state must contain one finite value per row")
    return values


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
    return float(np.sum(np.asarray(values, dtype=float) * weights) / weights.sum())


def _time_features(time_state: Sequence[float], *, period: float) -> np.ndarray:
    angle = state_to_angle(time_state, period=period)
    return np.column_stack([np.sin(angle), np.cos(angle)])


def fit_joint_continuous_circular_state_model(
    X: np.ndarray,
    height: Sequence[float],
    time_state: Sequence[float],
    *,
    period: float = 24.0,
    sample_weight: Sequence[float] | None = None,
) -> JointContinuousCircularStateModel:
    matrix = np.asarray(X, dtype=float)
    if matrix.ndim != 2 or matrix.shape[0] == 0 or matrix.shape[1] == 0:
        raise ValueError("X must be a non-empty two-dimensional numeric matrix")
    if not np.isfinite(matrix).all():
        raise ValueError("X must contain only finite values")
    n = matrix.shape[0]
    height_values = _validate_height(height, n)
    time_values = _validate_time(time_state, n)
    weights = _validate_weights(sample_weight, n)
    time_features = _time_features(time_values, period=period)
    context_time = np.column_stack([matrix, time_features])

    time_model = fit_von_mises_circular_state_model(
        matrix,
        time_values,
        period=period,
        sample_weight=weights,
    )
    height_context = fit_gaussian_continuous_state_model(
        matrix,
        height_values,
        sample_weight=weights,
    )
    height_context_time = fit_gaussian_continuous_state_model(
        context_time,
        height_values,
        sample_weight=weights,
    )
    height_time = fit_gaussian_continuous_state_model(
        time_features,
        height_values,
        sample_weight=weights,
    )
    return JointContinuousCircularStateModel(
        time_model=time_model,
        height_given_context_model=height_context,
        height_given_context_time_model=height_context_time,
        height_given_time_model=height_time,
        context_feature_count=int(matrix.shape[1]),
        period=float(period),
    )


def score_joint_log_density_gain(
    conditional_joint_log_density: Sequence[float],
    marginal_joint_log_density: Sequence[float],
    *,
    factorized_contextual_log_density: Sequence[float] | None = None,
    sample_weight: Sequence[float] | None = None,
) -> JointLogDensityGain:
    conditional = np.asarray(conditional_joint_log_density, dtype=float)
    marginal = np.asarray(marginal_joint_log_density, dtype=float)
    if conditional.ndim != 1 or conditional.size == 0 or marginal.shape != conditional.shape:
        raise ValueError("joint log densities must be equal-length non-empty vectors")
    if not np.isfinite(conditional).all() or not np.isfinite(marginal).all():
        raise ValueError("joint log densities must be finite")
    weights = _validate_weights(sample_weight, conditional.size)
    mean_conditional = _weighted_mean(conditional, weights)
    mean_marginal = _weighted_mean(marginal, weights)
    if factorized_contextual_log_density is None:
        mean_factorized = None
        coupling = None
    else:
        factorized = np.asarray(factorized_contextual_log_density, dtype=float)
        if factorized.shape != conditional.shape or not np.isfinite(factorized).all():
            raise ValueError("factorized contextual log density must match joint log density")
        mean_factorized = _weighted_mean(factorized, weights)
        coupling = float(mean_conditional - mean_factorized)
    return JointLogDensityGain(
        row_count=int(conditional.size),
        total_weight=float(weights.sum()),
        mean_conditional_joint_log_density=float(mean_conditional),
        mean_marginal_joint_log_density=float(mean_marginal),
        mean_joint_log_density_gain=float(mean_conditional - mean_marginal),
        mean_factorized_contextual_log_density=(
            None if mean_factorized is None else float(mean_factorized)
        ),
        mean_coupling_log_density_gain=coupling,
    )


def score_joint_state_groups(
    model: JointContinuousCircularStateModel,
    X: np.ndarray,
    height: Sequence[float],
    time_state: Sequence[float],
    groups: Sequence[object],
    *,
    sample_weight: Sequence[float] | None = None,
    tolerance: float = 0.0,
) -> GroupedJointStateScore:
    matrix = model._validate_X(X)
    height_values = _validate_height(height, matrix.shape[0])
    time_values = _validate_time(time_state, matrix.shape[0])
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
    rows: list[JointStateGroupScore] = []
    for value in ordered:
        mask = group_values == value
        if float(weights[mask].sum()) <= 0:
            continue
        rows.append(
            JointStateGroupScore(
                group=str(value),
                score=model.score(
                    matrix[mask],
                    height_values[mask],
                    time_values[mask],
                    sample_weight=weights[mask],
                ),
            )
        )
    if not rows:
        raise ValueError("no positive-weight independent group remains")
    return GroupedJointStateScore(
        groups=tuple(rows),
        joint_gain_category=classify_independent_gains(
            [row.score.mean_joint_log_density_gain for row in rows],
            tolerance=tolerance,
        ),
        coupling_gain_category=classify_independent_gains(
            [row.score.mean_coupling_log_density_gain for row in rows],
            tolerance=tolerance,
        ),
    )
