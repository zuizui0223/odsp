"""Distribution-free split-conformal uncertainty for continuous and circular states.

The calibrators are model-agnostic: callers supply predictions from any upstream
learner plus an independent calibration set.  Guarantees are marginal and require
exchangeability between calibration and target rows.  Distribution shift can and
should be visible as degraded empirical coverage.
"""
from __future__ import annotations

from dataclasses import asdict, dataclass
import math
from typing import Sequence

import numpy as np

from .circular_state import circular_distance


@dataclass(frozen=True)
class ContinuousConformalInterval:
    row_index: int
    center: float
    scale: float
    target_coverage: float
    standardized_quantile: float
    half_width: float
    lower: float
    upper: float

    def as_dict(self) -> dict[str, object]:
        return asdict(self)


@dataclass(frozen=True)
class ContinuousConformalCoverage:
    row_count: int
    target_coverage: float
    empirical_coverage: float
    mean_width: float
    median_width: float

    def as_dict(self) -> dict[str, object]:
        return asdict(self)


@dataclass
class ContinuousConformalCalibrator:
    miscoverage: float
    target_coverage: float
    calibration_size: int
    score_quantile: float
    scale_adaptive: bool
    scale_floor: float

    def intervals(
        self,
        predicted_center: Sequence[float],
        *,
        predicted_scale: Sequence[float] | None = None,
    ) -> tuple[ContinuousConformalInterval, ...]:
        center = _validate_vector(predicted_center, "predicted_center")
        scale = _validated_scale(
            predicted_scale,
            center.size,
            scale_floor=self.scale_floor,
            required=self.scale_adaptive,
        )
        half = self.score_quantile * scale
        return tuple(
            ContinuousConformalInterval(
                row_index=int(index),
                center=float(mu),
                scale=float(local_scale),
                target_coverage=float(self.target_coverage),
                standardized_quantile=float(self.score_quantile),
                half_width=float(width),
                lower=float(mu - width),
                upper=float(mu + width),
            )
            for index, (mu, local_scale, width) in enumerate(
                zip(center, scale, half)
            )
        )

    def evaluate(
        self,
        predicted_center: Sequence[float],
        observed: Sequence[float],
        *,
        predicted_scale: Sequence[float] | None = None,
    ) -> ContinuousConformalCoverage:
        center = _validate_vector(predicted_center, "predicted_center")
        y = _validate_vector(observed, "observed", expected=center.size)
        intervals = self.intervals(center, predicted_scale=predicted_scale)
        lower = np.asarray([row.lower for row in intervals], dtype=float)
        upper = np.asarray([row.upper for row in intervals], dtype=float)
        width = upper - lower
        covered = (y >= lower) & (y <= upper)
        return ContinuousConformalCoverage(
            row_count=int(y.size),
            target_coverage=float(self.target_coverage),
            empirical_coverage=float(np.mean(covered)),
            mean_width=float(np.mean(width)),
            median_width=float(np.median(width)),
        )


@dataclass(frozen=True)
class CircularConformalArc:
    row_index: int
    center: float
    period: float
    target_coverage: float
    half_width: float
    arc_lower: float
    arc_upper: float
    wraps_origin: bool
    full_circle: bool

    def as_dict(self) -> dict[str, object]:
        return asdict(self)


@dataclass(frozen=True)
class CircularConformalCoverage:
    row_count: int
    target_coverage: float
    empirical_coverage: float
    mean_arc_width: float
    median_arc_width: float
    full_circle_fraction: float

    def as_dict(self) -> dict[str, object]:
        return asdict(self)


@dataclass
class CircularConformalCalibrator:
    miscoverage: float
    target_coverage: float
    calibration_size: int
    distance_quantile: float
    period: float

    def arcs(
        self,
        predicted_center: Sequence[float],
    ) -> tuple[CircularConformalArc, ...]:
        center = np.mod(
            _validate_vector(predicted_center, "predicted_center"), self.period
        )
        half = min(float(self.distance_quantile), self.period / 2.0)
        rows: list[CircularConformalArc] = []
        full = bool(half >= self.period / 2.0 - 1e-15)
        for index, value in enumerate(center):
            if full:
                lower = 0.0
                upper = self.period
                wraps = False
            else:
                lower_raw = float(value - half)
                upper_raw = float(value + half)
                lower = lower_raw % self.period
                upper = upper_raw % self.period
                wraps = bool(lower_raw < 0.0 or upper_raw >= self.period)
            rows.append(
                CircularConformalArc(
                    row_index=int(index),
                    center=float(value),
                    period=float(self.period),
                    target_coverage=float(self.target_coverage),
                    half_width=float(half),
                    arc_lower=float(lower),
                    arc_upper=float(upper),
                    wraps_origin=wraps,
                    full_circle=full,
                )
            )
        return tuple(rows)

    def evaluate(
        self,
        predicted_center: Sequence[float],
        observed: Sequence[float],
    ) -> CircularConformalCoverage:
        center = np.mod(
            _validate_vector(predicted_center, "predicted_center"), self.period
        )
        y = np.mod(_validate_vector(observed, "observed", expected=center.size), self.period)
        half = min(float(self.distance_quantile), self.period / 2.0)
        distance = circular_distance(y, center, period=self.period)
        covered = distance <= half + 1e-12
        width = min(self.period, 2.0 * half)
        return CircularConformalCoverage(
            row_count=int(y.size),
            target_coverage=float(self.target_coverage),
            empirical_coverage=float(np.mean(covered)),
            mean_arc_width=float(width),
            median_arc_width=float(width),
            full_circle_fraction=float(1.0 if width >= self.period - 1e-15 else 0.0),
        )


@dataclass(frozen=True)
class JointBonferroniRegion:
    row_index: int
    joint_target_coverage: float
    height_interval: ContinuousConformalInterval
    time_arc: CircularConformalArc

    def as_dict(self) -> dict[str, object]:
        return {
            "row_index": self.row_index,
            "joint_target_coverage": self.joint_target_coverage,
            "height_interval": self.height_interval.as_dict(),
            "time_arc": self.time_arc.as_dict(),
        }


@dataclass(frozen=True)
class JointBonferroniCoverage:
    row_count: int
    joint_target_coverage: float
    continuous_component_target_coverage: float
    circular_component_target_coverage: float
    empirical_joint_coverage: float
    empirical_continuous_coverage: float
    empirical_circular_coverage: float

    def as_dict(self) -> dict[str, object]:
        return asdict(self)


@dataclass
class JointBonferroniConformalCalibrator:
    continuous: ContinuousConformalCalibrator
    circular: CircularConformalCalibrator
    total_miscoverage: float
    joint_target_coverage: float

    def regions(
        self,
        height_center: Sequence[float],
        time_center: Sequence[float],
        *,
        height_scale: Sequence[float] | None = None,
    ) -> tuple[JointBonferroniRegion, ...]:
        height_intervals = self.continuous.intervals(
            height_center, predicted_scale=height_scale
        )
        time_arcs = self.circular.arcs(time_center)
        if len(height_intervals) != len(time_arcs):
            raise ValueError("height_center and time_center must have equal length")
        return tuple(
            JointBonferroniRegion(
                row_index=int(index),
                joint_target_coverage=float(self.joint_target_coverage),
                height_interval=height_row,
                time_arc=time_row,
            )
            for index, (height_row, time_row) in enumerate(
                zip(height_intervals, time_arcs)
            )
        )

    def evaluate(
        self,
        height_center: Sequence[float],
        height_observed: Sequence[float],
        time_center: Sequence[float],
        time_observed: Sequence[float],
        *,
        height_scale: Sequence[float] | None = None,
    ) -> JointBonferroniCoverage:
        hc = _validate_vector(height_center, "height_center")
        hy = _validate_vector(height_observed, "height_observed", expected=hc.size)
        tc = _validate_vector(time_center, "time_center", expected=hc.size)
        ty = _validate_vector(time_observed, "time_observed", expected=hc.size)
        regions = self.regions(hc, tc, height_scale=height_scale)
        height_covered = np.asarray(
            [row.height_interval.lower <= y <= row.height_interval.upper for row, y in zip(regions, hy)],
            dtype=bool,
        )
        time_half = self.circular.distance_quantile
        time_distance = circular_distance(
            np.mod(ty, self.circular.period),
            np.mod(tc, self.circular.period),
            period=self.circular.period,
        )
        time_covered = time_distance <= min(time_half, self.circular.period / 2.0) + 1e-12
        joint = height_covered & time_covered
        return JointBonferroniCoverage(
            row_count=int(hc.size),
            joint_target_coverage=float(self.joint_target_coverage),
            continuous_component_target_coverage=float(self.continuous.target_coverage),
            circular_component_target_coverage=float(self.circular.target_coverage),
            empirical_joint_coverage=float(np.mean(joint)),
            empirical_continuous_coverage=float(np.mean(height_covered)),
            empirical_circular_coverage=float(np.mean(time_covered)),
        )


def _validate_vector(
    values: Sequence[float],
    name: str,
    *,
    expected: int | None = None,
) -> np.ndarray:
    array = np.asarray(values, dtype=float)
    if array.ndim != 1 or array.size == 0:
        raise ValueError(f"{name} must be a non-empty one-dimensional vector")
    if expected is not None and array.size != expected:
        raise ValueError(f"{name} has an unexpected length")
    if not np.isfinite(array).all():
        raise ValueError(f"{name} must contain only finite values")
    return array


def _validate_miscoverage(miscoverage: float) -> float:
    value = float(miscoverage)
    if not math.isfinite(value) or not 0.0 < value < 1.0:
        raise ValueError("miscoverage must lie strictly between zero and one")
    return value


def _validated_scale(
    scale: Sequence[float] | None,
    n: int,
    *,
    scale_floor: float,
    required: bool,
) -> np.ndarray:
    if scale is None:
        if required:
            raise ValueError("predicted_scale is required because the calibrator is scale-adaptive")
        return np.ones(n, dtype=float)
    values = np.asarray(scale, dtype=float)
    if values.shape != (n,):
        raise ValueError("predicted_scale must contain one value per row")
    if not np.isfinite(values).all() or np.any(values <= 0):
        raise ValueError("predicted_scale must be finite and strictly positive")
    return np.maximum(values, scale_floor)


def _split_conformal_quantile(scores: np.ndarray, miscoverage: float) -> float:
    values = np.sort(np.asarray(scores, dtype=float))
    if values.ndim != 1 or values.size == 0 or not np.isfinite(values).all():
        raise ValueError("calibration scores must be a non-empty finite vector")
    rank = int(math.ceil((values.size + 1) * (1.0 - miscoverage)))
    rank = min(max(rank, 1), values.size)
    return float(values[rank - 1])


def fit_continuous_conformal_calibrator(
    predicted_center: Sequence[float],
    observed: Sequence[float],
    *,
    predicted_scale: Sequence[float] | None = None,
    miscoverage: float = 0.10,
    scale_floor: float = 1e-12,
) -> ContinuousConformalCalibrator:
    alpha = _validate_miscoverage(miscoverage)
    if not math.isfinite(scale_floor) or scale_floor <= 0:
        raise ValueError("scale_floor must be finite and positive")
    center = _validate_vector(predicted_center, "predicted_center")
    y = _validate_vector(observed, "observed", expected=center.size)
    scale_adaptive = predicted_scale is not None
    scale = _validated_scale(
        predicted_scale,
        center.size,
        scale_floor=scale_floor,
        required=False,
    )
    score = np.abs(y - center) / scale
    return ContinuousConformalCalibrator(
        miscoverage=float(alpha),
        target_coverage=float(1.0 - alpha),
        calibration_size=int(center.size),
        score_quantile=_split_conformal_quantile(score, alpha),
        scale_adaptive=bool(scale_adaptive),
        scale_floor=float(scale_floor),
    )


def fit_circular_conformal_calibrator(
    predicted_center: Sequence[float],
    observed: Sequence[float],
    *,
    period: float = 24.0,
    miscoverage: float = 0.10,
) -> CircularConformalCalibrator:
    alpha = _validate_miscoverage(miscoverage)
    period_value = float(period)
    if not math.isfinite(period_value) or period_value <= 0:
        raise ValueError("period must be finite and positive")
    center = np.mod(_validate_vector(predicted_center, "predicted_center"), period_value)
    y = np.mod(_validate_vector(observed, "observed", expected=center.size), period_value)
    score = circular_distance(y, center, period=period_value)
    return CircularConformalCalibrator(
        miscoverage=float(alpha),
        target_coverage=float(1.0 - alpha),
        calibration_size=int(center.size),
        distance_quantile=_split_conformal_quantile(score, alpha),
        period=float(period_value),
    )


def fit_joint_bonferroni_conformal_calibrator(
    height_center: Sequence[float],
    height_observed: Sequence[float],
    time_center: Sequence[float],
    time_observed: Sequence[float],
    *,
    height_scale: Sequence[float] | None = None,
    period: float = 24.0,
    total_miscoverage: float = 0.10,
) -> JointBonferroniConformalCalibrator:
    alpha = _validate_miscoverage(total_miscoverage)
    component_alpha = alpha / 2.0
    continuous = fit_continuous_conformal_calibrator(
        height_center,
        height_observed,
        predicted_scale=height_scale,
        miscoverage=component_alpha,
    )
    circular = fit_circular_conformal_calibrator(
        time_center,
        time_observed,
        period=period,
        miscoverage=component_alpha,
    )
    return JointBonferroniConformalCalibrator(
        continuous=continuous,
        circular=circular,
        total_miscoverage=float(alpha),
        joint_target_coverage=float(1.0 - alpha),
    )
