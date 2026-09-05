"""High-level trusted joint ecological-state forecasting for ODSP.

This module composes four already separate ODSP ideas without collapsing them:

* joint continuous-circular state density prediction;
* split-conformal height x time prediction regions;
* environmental novelty / strict extrapolation diagnostics;
* independent validation and grouped transferability scoring.

Training and conformal calibration rows have distinct roles.  Calibration rows do
not refit the joint density model or the environmental novelty reference cloud.
"""
from __future__ import annotations

from dataclasses import asdict, dataclass
from typing import Sequence

import numpy as np

from .continuous_circular_conformal import (
    JointBonferroniConformalCalibrator,
    JointBonferroniCoverage,
    fit_joint_bonferroni_conformal_calibrator,
)
from .joint_state import (
    GroupedJointStateScore,
    JointContinuousCircularStateModel,
    JointStateScore,
    fit_joint_continuous_circular_state_model,
    score_joint_state_groups,
)
from .prediction_novelty import (
    EnvironmentalNoveltyModel,
    fit_environmental_novelty_model,
)


@dataclass(frozen=True)
class TrustedJointForecastRow:
    row_index: int
    time_mean_state: float
    time_period: float
    time_model_arc_lower: float
    time_model_arc_upper: float
    time_model_arc_wraps_origin: bool
    height_mean_at_time_mode: float
    height_model_standard_deviation: float
    height_model_lower_at_time_mode: float
    height_model_upper_at_time_mode: float
    conformal_joint_target_coverage: float
    conformal_height_lower: float
    conformal_height_upper: float
    conformal_time_arc_lower: float
    conformal_time_arc_upper: float
    conformal_time_arc_wraps_origin: bool
    novelty_ratio: float
    novelty_category: str
    outside_feature_indices: tuple[int, ...]

    def as_dict(self) -> dict[str, object]:
        return asdict(self)


@dataclass
class TrustedJointStateForecaster:
    model: JointContinuousCircularStateModel
    conformal: JointBonferroniConformalCalibrator
    novelty: EnvironmentalNoveltyModel
    training_row_count: int
    calibration_row_count: int
    period: float
    total_miscoverage: float

    def _summary_arrays(
        self,
        X: np.ndarray,
    ) -> tuple[tuple[object, ...], np.ndarray, np.ndarray, np.ndarray]:
        summaries = self.model.summarize(X)
        time_center = np.asarray(
            [row.time_mean_state for row in summaries], dtype=float
        )
        height_center = np.asarray(
            [row.height_mean_at_time_mode for row in summaries], dtype=float
        )
        height_scale = np.asarray(
            [row.height_standard_deviation for row in summaries], dtype=float
        )
        return summaries, time_center, height_center, height_scale

    def forecast(self, X: np.ndarray) -> tuple[TrustedJointForecastRow, ...]:
        summaries, time_center, height_center, height_scale = self._summary_arrays(X)
        regions = self.conformal.regions(
            height_center,
            time_center,
            height_scale=height_scale,
        )
        novelty_rows = self.novelty.summarize(X)
        if not (len(summaries) == len(regions) == len(novelty_rows)):
            raise RuntimeError("joint forecast components returned inconsistent row counts")

        result: list[TrustedJointForecastRow] = []
        for index, (summary, region, novelty) in enumerate(
            zip(summaries, regions, novelty_rows)
        ):
            result.append(
                TrustedJointForecastRow(
                    row_index=int(index),
                    time_mean_state=float(summary.time_mean_state),
                    time_period=float(summary.time_period),
                    time_model_arc_lower=float(summary.time_arc_lower),
                    time_model_arc_upper=float(summary.time_arc_upper),
                    time_model_arc_wraps_origin=bool(summary.time_arc_wraps_origin),
                    height_mean_at_time_mode=float(summary.height_mean_at_time_mode),
                    height_model_standard_deviation=float(
                        summary.height_standard_deviation
                    ),
                    height_model_lower_at_time_mode=float(
                        summary.height_lower_at_time_mode
                    ),
                    height_model_upper_at_time_mode=float(
                        summary.height_upper_at_time_mode
                    ),
                    conformal_joint_target_coverage=float(
                        region.joint_target_coverage
                    ),
                    conformal_height_lower=float(region.height_interval.lower),
                    conformal_height_upper=float(region.height_interval.upper),
                    conformal_time_arc_lower=float(region.time_arc.arc_lower),
                    conformal_time_arc_upper=float(region.time_arc.arc_upper),
                    conformal_time_arc_wraps_origin=bool(
                        region.time_arc.wraps_origin
                    ),
                    novelty_ratio=float(novelty.novelty_ratio),
                    novelty_category=str(novelty.category),
                    outside_feature_indices=tuple(novelty.outside_feature_indices),
                )
            )
        return tuple(result)

    def evaluate_conformal(
        self,
        X: np.ndarray,
        height: Sequence[float],
        time_state: Sequence[float],
    ) -> JointBonferroniCoverage:
        _, time_center, height_center, height_scale = self._summary_arrays(X)
        return self.conformal.evaluate(
            height_center,
            height,
            time_center,
            time_state,
            height_scale=height_scale,
        )

    def score(
        self,
        X: np.ndarray,
        height: Sequence[float],
        time_state: Sequence[float],
        *,
        sample_weight: Sequence[float] | None = None,
    ) -> JointStateScore:
        return self.model.score(
            X,
            height,
            time_state,
            sample_weight=sample_weight,
        )

    def score_groups(
        self,
        X: np.ndarray,
        height: Sequence[float],
        time_state: Sequence[float],
        groups: Sequence[object],
        *,
        sample_weight: Sequence[float] | None = None,
        tolerance: float = 0.0,
    ) -> GroupedJointStateScore:
        return score_joint_state_groups(
            self.model,
            X,
            height,
            time_state,
            groups,
            sample_weight=sample_weight,
            tolerance=tolerance,
        )

    def sample_joint(
        self,
        X: np.ndarray,
        *,
        draws_per_row: int = 100,
        random_state: int = 20260905,
    ) -> tuple[np.ndarray, np.ndarray]:
        return self.model.sample_joint(
            X,
            draws_per_row=draws_per_row,
            random_state=random_state,
        )


def _validate_split_X(X: np.ndarray, *, name: str) -> np.ndarray:
    matrix = np.asarray(X, dtype=float)
    if matrix.ndim != 2 or matrix.shape[0] == 0 or matrix.shape[1] == 0:
        raise ValueError(f"{name} must be a non-empty two-dimensional matrix")
    if not np.isfinite(matrix).all():
        raise ValueError(f"{name} must contain only finite values")
    return matrix


def _validate_state_vector(values: Sequence[float], *, n: int, name: str) -> np.ndarray:
    vector = np.asarray(values, dtype=float)
    if vector.shape != (n,) or not np.isfinite(vector).all():
        raise ValueError(f"{name} must contain one finite value per row")
    return vector


def fit_trusted_joint_state_forecaster(
    X_train: np.ndarray,
    height_train: Sequence[float],
    time_train: Sequence[float],
    X_calibration: np.ndarray,
    height_calibration: Sequence[float],
    time_calibration: Sequence[float],
    *,
    period: float = 24.0,
    sample_weight_train: Sequence[float] | None = None,
    total_miscoverage: float = 0.10,
    novelty_reference_quantile: float = 0.95,
) -> TrustedJointStateForecaster:
    """Fit joint model on training rows and conformal trust only on calibration rows."""

    X_train_array = _validate_split_X(X_train, name="X_train")
    X_cal_array = _validate_split_X(X_calibration, name="X_calibration")
    if X_cal_array.shape[1] != X_train_array.shape[1]:
        raise ValueError("training and calibration covariates must have equal feature count")
    h_train = _validate_state_vector(
        height_train, n=X_train_array.shape[0], name="height_train"
    )
    t_train = _validate_state_vector(
        time_train, n=X_train_array.shape[0], name="time_train"
    )
    h_cal = _validate_state_vector(
        height_calibration,
        n=X_cal_array.shape[0],
        name="height_calibration",
    )
    t_cal = _validate_state_vector(
        time_calibration,
        n=X_cal_array.shape[0],
        name="time_calibration",
    )

    model = fit_joint_continuous_circular_state_model(
        X_train_array,
        h_train,
        t_train,
        period=period,
        sample_weight=sample_weight_train,
    )
    novelty = fit_environmental_novelty_model(
        X_train_array,
        reference_quantile=novelty_reference_quantile,
    )

    calibration_summary = model.summarize(X_cal_array)
    time_center = np.asarray(
        [row.time_mean_state for row in calibration_summary], dtype=float
    )
    height_center = np.asarray(
        [row.height_mean_at_time_mode for row in calibration_summary], dtype=float
    )
    height_scale = np.asarray(
        [row.height_standard_deviation for row in calibration_summary], dtype=float
    )
    conformal = fit_joint_bonferroni_conformal_calibrator(
        height_center,
        h_cal,
        time_center,
        t_cal,
        height_scale=height_scale,
        period=period,
        total_miscoverage=total_miscoverage,
    )
    return TrustedJointStateForecaster(
        model=model,
        conformal=conformal,
        novelty=novelty,
        training_row_count=int(X_train_array.shape[0]),
        calibration_row_count=int(X_cal_array.shape[0]),
        period=float(period),
        total_miscoverage=float(total_miscoverage),
    )
