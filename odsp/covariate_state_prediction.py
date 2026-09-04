"""Optional scikit-learn bridge for covariate-to-state prediction.

This module lets ODSP predict ecological state distributions at new covariate
rows, such as previously unsampled map cells, while keeping the scoring layer
model-agnostic.  scikit-learn is imported lazily and remains an optional package
extra (`odsp-niche-geometry[predict]`).
"""
from __future__ import annotations

from dataclasses import asdict, dataclass
import math
from typing import Sequence

import numpy as np

from .state_prediction import StatePredictionScore, score_state_probability_field


@dataclass(frozen=True)
class CovariateStatePredictionSummary:
    row_index: int
    state_probabilities: tuple[float, ...]
    dominant_state: object
    dominant_probability: float
    entropy_nats: float
    effective_states: float

    def as_dict(self) -> dict[str, object]:
        return asdict(self)


@dataclass
class CovariateStateModel:
    """Fitted probability estimator plus ODSP-compatible state metadata."""

    estimator: object
    classes: tuple[object, ...]
    marginal_probability: np.ndarray
    feature_count: int
    estimator_name: str

    def predict_proba(self, X: np.ndarray) -> np.ndarray:
        matrix = _validate_X(X, expected_features=self.feature_count)
        probability = np.asarray(self.estimator.predict_proba(matrix), dtype=float)
        if probability.shape != (matrix.shape[0], len(self.classes)):
            raise ValueError("estimator predict_proba returned an unexpected shape")
        if not np.isfinite(probability).all() or np.any(probability < 0):
            raise ValueError("estimator predict_proba must return finite non-negative values")
        totals = probability.sum(axis=1)
        if np.any(np.abs(totals - 1.0) > 1e-8):
            raise ValueError("estimator predict_proba rows must sum to one")
        return probability

    def summarize(self, X: np.ndarray) -> tuple[CovariateStatePredictionSummary, ...]:
        probability = self.predict_proba(X)
        result: list[CovariateStatePredictionSummary] = []
        for row_index, row in enumerate(probability):
            positive = row > 0
            entropy = float(-np.sum(row[positive] * np.log(row[positive])))
            dominant = int(np.argmax(row))
            result.append(
                CovariateStatePredictionSummary(
                    row_index=int(row_index),
                    state_probabilities=tuple(float(value) for value in row),
                    dominant_state=self.classes[dominant],
                    dominant_probability=float(row[dominant]),
                    entropy_nats=entropy,
                    effective_states=float(math.exp(entropy)),
                )
            )
        return tuple(result)

    def score(
        self,
        X: np.ndarray,
        y: Sequence[object],
        *,
        sample_weight: Sequence[float] | None = None,
    ) -> StatePredictionScore:
        matrix = _validate_X(X, expected_features=self.feature_count)
        labels = np.asarray(y, dtype=object)
        if labels.shape != (matrix.shape[0],):
            raise ValueError("y must contain one state label per covariate row")
        weights = _validated_weights(sample_weight, matrix.shape[0])
        probability = self.predict_proba(matrix)
        class_index = {value: index for index, value in enumerate(self.classes)}
        heldout = np.zeros_like(probability, dtype=float)
        for row, (label, weight) in enumerate(zip(labels, weights)):
            if label not in class_index:
                raise ValueError(f"held-out state was absent from training classes: {label!r}")
            heldout[row, class_index[label]] += float(weight)
        return score_state_probability_field(
            conditional_probability=probability,
            heldout_support=heldout,
            base_ndim=1,
            marginal_probability=self.marginal_probability,
            seen_base_mask=np.ones(matrix.shape[0], dtype=bool),
        )


def _require_sklearn():
    try:
        from sklearn.base import clone
    except ImportError as exc:
        raise ImportError(
            "covariate state prediction requires the optional 'predict' extra: "
            "pip install 'odsp-niche-geometry[predict]'"
        ) from exc
    return clone


def _validate_X(X: np.ndarray, *, expected_features: int | None = None) -> np.ndarray:
    matrix = np.asarray(X, dtype=float)
    if matrix.ndim != 2 or matrix.shape[0] == 0 or matrix.shape[1] == 0:
        raise ValueError("X must be a non-empty two-dimensional numeric matrix")
    if not np.isfinite(matrix).all():
        raise ValueError("X must contain only finite values")
    if expected_features is not None and matrix.shape[1] != expected_features:
        raise ValueError("X has a different number of features than the fitted model")
    return matrix


def _validated_weights(weights: Sequence[float] | None, n: int) -> np.ndarray:
    if weights is None:
        return np.ones(n, dtype=float)
    result = np.asarray(weights, dtype=float)
    if result.shape != (n,):
        raise ValueError("sample_weight must contain one value per row")
    if not np.isfinite(result).all() or np.any(result < 0):
        raise ValueError("sample_weight must be finite and non-negative")
    if not float(result.sum()) > 0:
        raise ValueError("sample_weight must have positive total mass")
    return result


def fit_covariate_state_model(
    estimator: object,
    X: np.ndarray,
    y: Sequence[object],
    *,
    sample_weight: Sequence[float] | None = None,
) -> CovariateStateModel:
    """Fit any scikit-learn-compatible probabilistic classifier as a state model.

    The estimator must expose `fit`, `predict_proba` and `classes_`.  A clone is
    fitted so the caller's estimator instance is not mutated.
    """

    clone = _require_sklearn()
    matrix = _validate_X(X)
    labels = np.asarray(y, dtype=object)
    if labels.shape != (matrix.shape[0],):
        raise ValueError("y must contain one state label per covariate row")
    weights = _validated_weights(sample_weight, matrix.shape[0])

    fitted = clone(estimator)
    try:
        fitted.fit(matrix, labels, sample_weight=weights)
    except TypeError:
        if sample_weight is not None:
            raise ValueError("the supplied estimator does not accept sample_weight")
        fitted.fit(matrix, labels)
    if not hasattr(fitted, "predict_proba") or not hasattr(fitted, "classes_"):
        raise ValueError("estimator must provide predict_proba and classes_ after fitting")
    classes = tuple(fitted.classes_.tolist())
    if len(classes) < 2:
        raise ValueError("state prediction requires at least two observed classes")

    class_index = {value: index for index, value in enumerate(classes)}
    counts = np.zeros(len(classes), dtype=float)
    for label, weight in zip(labels, weights):
        counts[class_index[label]] += float(weight)
    marginal = counts / float(counts.sum())

    return CovariateStateModel(
        estimator=fitted,
        classes=classes,
        marginal_probability=marginal,
        feature_count=int(matrix.shape[1]),
        estimator_name=f"{type(fitted).__module__}.{type(fitted).__name__}",
    )


def make_state_classifier(
    kind: str,
    *,
    random_state: int = 20260904,
    **kwargs: object,
) -> object:
    """Create common reference classifiers without making them ODSP-specific.

    Supported convenience kinds are `multinomial_logit` and `random_forest`.
    Any other probabilistic scikit-learn classifier can be passed directly to
    `fit_covariate_state_model`.
    """

    _require_sklearn()
    if kind == "multinomial_logit":
        from sklearn.linear_model import LogisticRegression

        defaults: dict[str, object] = {
            "max_iter": 2000,
            "solver": "lbfgs",
            "random_state": random_state,
        }
        defaults.update(kwargs)
        return LogisticRegression(**defaults)
    if kind == "random_forest":
        from sklearn.ensemble import RandomForestClassifier

        defaults = {
            "n_estimators": 500,
            "random_state": random_state,
            "n_jobs": -1,
        }
        defaults.update(kwargs)
        return RandomForestClassifier(**defaults)
    raise ValueError("kind must be 'multinomial_logit' or 'random_forest'")
