"""Integrated per-row trust summaries for covariate-to-state prediction.

This module does not collapse uncertainty, environmental novelty and transferability
into one opaque confidence score.  It combines the first two row-level diagnostics
with the existing state probability output; dataset-level generalization profiles
remain a separate object because they require independent held-out groups.
"""
from __future__ import annotations

from dataclasses import asdict, dataclass
from typing import Sequence

import numpy as np

from .covariate_state_prediction import CovariateStateModel
from .prediction_novelty import EnvironmentalNoveltyModel
from .prediction_uncertainty import StateConformalCalibrator


@dataclass(frozen=True)
class TrustedStatePredictionSummary:
    row_index: int
    state_probabilities: tuple[float, ...]
    dominant_state: object
    dominant_probability: float
    entropy_nats: float
    effective_states: float
    conformal_states: tuple[object, ...]
    conformal_set_size: int
    conformal_target_coverage: float
    novelty_category: str
    novelty_ratio: float
    outside_feature_indices: tuple[int, ...]

    def as_dict(self) -> dict[str, object]:
        return asdict(self)


def trusted_state_predictions(
    state_model: CovariateStateModel,
    conformal_calibrator: StateConformalCalibrator,
    novelty_model: EnvironmentalNoveltyModel,
    X: np.ndarray,
) -> tuple[TrustedStatePredictionSummary, ...]:
    """Return state probabilities with calibrated sets and domain diagnostics.

    The same covariate matrix is sent to the fitted state model and the novelty
    model.  The conformal calibrator must use the same ordered state classes as the
    state model.  Transfer/generalization is deliberately absent here because it
    must be evaluated from independent outcomes, not inferred from one query row.
    """

    if tuple(state_model.classes) != tuple(conformal_calibrator.classes):
        raise ValueError("state model and conformal calibrator classes must match in order")
    if int(state_model.feature_count) != int(novelty_model.feature_count):
        raise ValueError("state and novelty models must use the same number of covariates")

    probability = state_model.predict_proba(X)
    state_summaries = state_model.summarize(X)
    conformal_sets = conformal_calibrator.prediction_sets(probability)
    novelty_summaries = novelty_model.summarize(X)
    if not (
        len(state_summaries) == len(conformal_sets) == len(novelty_summaries)
    ):
        raise RuntimeError("trust summary components returned inconsistent row counts")

    result: list[TrustedStatePredictionSummary] = []
    for state, conformal_states, novelty in zip(
        state_summaries, conformal_sets, novelty_summaries
    ):
        result.append(
            TrustedStatePredictionSummary(
                row_index=int(state.row_index),
                state_probabilities=tuple(state.state_probabilities),
                dominant_state=state.dominant_state,
                dominant_probability=float(state.dominant_probability),
                entropy_nats=float(state.entropy_nats),
                effective_states=float(state.effective_states),
                conformal_states=tuple(conformal_states),
                conformal_set_size=len(conformal_states),
                conformal_target_coverage=float(conformal_calibrator.target_coverage),
                novelty_category=str(novelty.category),
                novelty_ratio=float(novelty.novelty_ratio),
                outside_feature_indices=tuple(novelty.outside_feature_indices),
            )
        )
    return tuple(result)
