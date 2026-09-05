"""Model-agnostic split-conformal uncertainty for ecological state probabilities.

The calibrator consumes probability vectors from any upstream state learner and a
prospectively separate calibration sample.  It uses the simple multiclass
nonconformity score ``1 - p(true_state)``.  Under exchangeability between the
calibration and target rows, the resulting prediction sets have finite-sample
marginal coverage at the requested level.  No claim of conditional coverage or
robustness to distribution shift is made.
"""
from __future__ import annotations

from dataclasses import asdict, dataclass
import math
from typing import Sequence

import numpy as np


@dataclass(frozen=True)
class ConformalPredictionSummary:
    row_index: int
    included_states: tuple[object, ...]
    set_size: int
    minimum_probability_threshold: float
    dominant_state: object
    dominant_probability: float

    def as_dict(self) -> dict[str, object]:
        return asdict(self)


@dataclass(frozen=True)
class ConformalCoverageReport:
    target_coverage: float
    empirical_coverage: float
    mean_set_size: float
    median_set_size: float
    maximum_set_size: int
    empty_set_fraction: float
    row_count: int

    def as_dict(self) -> dict[str, object]:
        return asdict(self)


@dataclass(frozen=True)
class StateConformalCalibrator:
    classes: tuple[object, ...]
    miscoverage: float
    target_coverage: float
    calibration_size: int
    nonconformity_quantile: float
    minimum_probability_threshold: float
    ensure_nonempty: bool

    def prediction_mask(self, probability: np.ndarray) -> np.ndarray:
        matrix = _validate_probability_matrix(probability, len(self.classes))
        if math.isinf(self.nonconformity_quantile):
            mask = np.ones_like(matrix, dtype=bool)
        else:
            scores = 1.0 - matrix
            mask = scores <= self.nonconformity_quantile + 1e-12
        if self.ensure_nonempty:
            empty = ~np.any(mask, axis=1)
            if np.any(empty):
                rows = np.flatnonzero(empty)
                mask[rows, np.argmax(matrix[rows], axis=1)] = True
        return mask

    def prediction_sets(self, probability: np.ndarray) -> tuple[tuple[object, ...], ...]:
        mask = self.prediction_mask(probability)
        return tuple(
            tuple(self.classes[index] for index in np.flatnonzero(row))
            for row in mask
        )

    def summarize(self, probability: np.ndarray) -> tuple[ConformalPredictionSummary, ...]:
        matrix = _validate_probability_matrix(probability, len(self.classes))
        mask = self.prediction_mask(matrix)
        result: list[ConformalPredictionSummary] = []
        for row_index, (row, included) in enumerate(zip(matrix, mask)):
            dominant = int(np.argmax(row))
            states = tuple(self.classes[index] for index in np.flatnonzero(included))
            result.append(
                ConformalPredictionSummary(
                    row_index=int(row_index),
                    included_states=states,
                    set_size=len(states),
                    minimum_probability_threshold=float(self.minimum_probability_threshold),
                    dominant_state=self.classes[dominant],
                    dominant_probability=float(row[dominant]),
                )
            )
        return tuple(result)

    def evaluate(
        self,
        probability: np.ndarray,
        y: Sequence[object],
    ) -> ConformalCoverageReport:
        matrix = _validate_probability_matrix(probability, len(self.classes))
        labels = _encode_labels(y, self.classes, matrix.shape[0])
        mask = self.prediction_mask(matrix)
        covered = mask[np.arange(matrix.shape[0]), labels]
        sizes = mask.sum(axis=1)
        return ConformalCoverageReport(
            target_coverage=float(self.target_coverage),
            empirical_coverage=float(np.mean(covered)),
            mean_set_size=float(np.mean(sizes)),
            median_set_size=float(np.median(sizes)),
            maximum_set_size=int(np.max(sizes)),
            empty_set_fraction=float(np.mean(sizes == 0)),
            row_count=int(matrix.shape[0]),
        )


def _validate_probability_matrix(probability: np.ndarray, class_count: int | None = None) -> np.ndarray:
    matrix = np.asarray(probability, dtype=float)
    if matrix.ndim != 2 or matrix.shape[0] == 0 or matrix.shape[1] < 2:
        raise ValueError("probability must be a non-empty rows-by-state matrix with at least two states")
    if class_count is not None and matrix.shape[1] != int(class_count):
        raise ValueError("probability state count does not match classes")
    if not np.isfinite(matrix).all() or np.any(matrix < 0):
        raise ValueError("probability must contain finite non-negative values")
    totals = matrix.sum(axis=1)
    if np.any(np.abs(totals - 1.0) > 1e-8):
        raise ValueError("probability rows must sum to one")
    return matrix


def _encode_labels(y: Sequence[object], classes: Sequence[object], n: int) -> np.ndarray:
    labels = np.asarray(y, dtype=object)
    if labels.shape != (n,):
        raise ValueError("y must contain one state label per probability row")
    index = {value: position for position, value in enumerate(classes)}
    result = np.empty(n, dtype=int)
    for row, label in enumerate(labels):
        if label not in index:
            raise ValueError(f"state label was absent from classes: {label!r}")
        result[row] = index[label]
    return result


def fit_state_conformal_calibrator(
    calibration_probability: np.ndarray,
    calibration_y: Sequence[object],
    *,
    classes: Sequence[object],
    miscoverage: float = 0.1,
    ensure_nonempty: bool = True,
) -> StateConformalCalibrator:
    """Fit a split-conformal state prediction-set calibrator.

    ``calibration_probability`` must be generated without fitting on the
    calibration outcomes.  The finite-sample quantile uses
    ``ceil((n + 1) * (1 - miscoverage))``.  If that rank exceeds the calibration
    size, all states are included, which is conservative.
    """

    if not math.isfinite(miscoverage) or not 0.0 < miscoverage < 1.0:
        raise ValueError("miscoverage must lie strictly between zero and one")
    class_tuple = tuple(classes)
    if len(class_tuple) < 2 or len(set(class_tuple)) != len(class_tuple):
        raise ValueError("classes must contain at least two unique state labels")
    matrix = _validate_probability_matrix(calibration_probability, len(class_tuple))
    labels = _encode_labels(calibration_y, class_tuple, matrix.shape[0])
    true_probability = matrix[np.arange(matrix.shape[0]), labels]
    scores = 1.0 - true_probability
    n = int(matrix.shape[0])
    rank = int(math.ceil((n + 1) * (1.0 - miscoverage)))
    if rank > n:
        quantile = math.inf
        threshold = 0.0
    else:
        quantile = float(np.sort(scores)[rank - 1])
        threshold = float(max(0.0, 1.0 - quantile))
    return StateConformalCalibrator(
        classes=class_tuple,
        miscoverage=float(miscoverage),
        target_coverage=float(1.0 - miscoverage),
        calibration_size=n,
        nonconformity_quantile=float(quantile),
        minimum_probability_threshold=threshold,
        ensure_nonempty=bool(ensure_nonempty),
    )
