"""Environmental novelty and extrapolation diagnostics for state prediction.

This module separates two questions that should not be conflated:

* strict extrapolation: at least one predictor lies outside its training range;
* multivariate novelty: the standardized query point is farther from the training
  cloud than a frozen reference quantile of leave-one-out nearest-neighbour
  distances among training rows.

The diagnostic does not make an extrapolated prediction correct or incorrect by
itself.  It marks where a state prediction is being asked to operate outside the
validated environmental domain.
"""
from __future__ import annotations

from dataclasses import asdict, dataclass
import math

import numpy as np


@dataclass(frozen=True)
class NoveltySummary:
    row_index: int
    nearest_scaled_distance: float
    reference_distance: float
    novelty_ratio: float
    outside_feature_count: int
    outside_feature_indices: tuple[int, ...]
    category: str

    def as_dict(self) -> dict[str, object]:
        return asdict(self)


@dataclass
class EnvironmentalNoveltyModel:
    center: np.ndarray
    scale: np.ndarray
    feature_min: np.ndarray
    feature_max: np.ndarray
    reference_distance: float
    reference_quantile: float
    training_size: int
    feature_count: int
    neighbour_model: object

    def summarize(self, X: np.ndarray) -> tuple[NoveltySummary, ...]:
        matrix = _validate_X(X, expected_features=self.feature_count)
        scaled = (matrix - self.center) / self.scale
        distances = np.asarray(
            self.neighbour_model.kneighbors(scaled, n_neighbors=1, return_distance=True)[0],
            dtype=float,
        ).reshape(-1)
        below = matrix < self.feature_min
        above = matrix > self.feature_max
        outside = below | above
        result: list[NoveltySummary] = []
        for row_index, (distance, flags) in enumerate(zip(distances, outside)):
            outside_indices = tuple(int(i) for i in np.flatnonzero(flags))
            ratio = float(distance / self.reference_distance)
            if outside_indices:
                category = "strict_extrapolation"
            elif ratio > 1.0:
                category = "novel"
            else:
                category = "in_domain"
            result.append(
                NoveltySummary(
                    row_index=int(row_index),
                    nearest_scaled_distance=float(distance),
                    reference_distance=float(self.reference_distance),
                    novelty_ratio=ratio,
                    outside_feature_count=len(outside_indices),
                    outside_feature_indices=outside_indices,
                    category=category,
                )
            )
        return tuple(result)


def _require_neighbours():
    try:
        from sklearn.neighbors import NearestNeighbors
    except ImportError as exc:
        raise ImportError(
            "environmental novelty diagnostics require the optional 'predict' extra: "
            "pip install 'odsp-niche-geometry[predict]'"
        ) from exc
    return NearestNeighbors


def _validate_X(X: np.ndarray, *, expected_features: int | None = None) -> np.ndarray:
    matrix = np.asarray(X, dtype=float)
    if matrix.ndim != 2 or matrix.shape[0] == 0 or matrix.shape[1] == 0:
        raise ValueError("X must be a non-empty two-dimensional numeric matrix")
    if expected_features is not None and matrix.shape[1] != expected_features:
        raise ValueError("X has a different number of features than the fitted novelty model")
    if not np.isfinite(matrix).all():
        raise ValueError("X must contain only finite values")
    return matrix


def fit_environmental_novelty_model(
    X_train: np.ndarray,
    *,
    reference_quantile: float = 0.95,
) -> EnvironmentalNoveltyModel:
    """Fit a standardized nearest-neighbour environmental novelty diagnostic.

    The scaling is fitted from training means and population standard deviations.
    Constant features receive scale one.  The reference distance is the requested
    quantile of each training row's distance to its nearest *other* training row.
    A query inside all univariate training ranges but above that distance is
    labelled ``novel``; any univariate range violation is labelled
    ``strict_extrapolation``.
    """

    if not math.isfinite(reference_quantile) or not 0.5 <= reference_quantile < 1.0:
        raise ValueError("reference_quantile must lie in [0.5, 1)")
    matrix = _validate_X(X_train)
    if matrix.shape[0] < 3:
        raise ValueError("at least three training rows are required for novelty calibration")
    center = matrix.mean(axis=0)
    scale = matrix.std(axis=0)
    scale = np.where(scale > 1e-12, scale, 1.0)
    scaled = (matrix - center) / scale

    NearestNeighbors = _require_neighbours()
    model = NearestNeighbors(n_neighbors=2)
    model.fit(scaled)
    distances = np.asarray(
        model.kneighbors(scaled, n_neighbors=2, return_distance=True)[0],
        dtype=float,
    )[:, 1]
    reference = float(np.quantile(distances, reference_quantile, method="higher"))
    if not math.isfinite(reference) or reference <= 1e-12:
        positive = distances[distances > 1e-12]
        reference = float(np.median(positive)) if positive.size else 1.0

    return EnvironmentalNoveltyModel(
        center=np.asarray(center, dtype=float),
        scale=np.asarray(scale, dtype=float),
        feature_min=np.asarray(matrix.min(axis=0), dtype=float),
        feature_max=np.asarray(matrix.max(axis=0), dtype=float),
        reference_distance=float(reference),
        reference_quantile=float(reference_quantile),
        training_size=int(matrix.shape[0]),
        feature_count=int(matrix.shape[1]),
        neighbour_model=model,
    )
