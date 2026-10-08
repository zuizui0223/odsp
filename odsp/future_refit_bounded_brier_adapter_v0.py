"""Bounded proper-scoring adapter for three ordered categorical state predictions.

This module ONLY converts already-frozen model predictions to validated
two-contrast [-1,1] row gains. It does not create independent training
refits, establish validation-block exchangeability, verify model-to-score
provenance, or qualify a future-refit probability claim.

For a K-category observation y and probability vector p, define the
normalized Brier skill score

    S(p,y) = 1 - (1/2) * sum_k (p[k] - 1[k=y])**2.

On the entire probability simplex S is in [0,1]. Hence every difference
of two scores is in [-1,1] WITHOUT probability clipping or data-dependent
winsorization. Positive differences mean improved proper score.
"""
from __future__ import annotations

from dataclasses import dataclass
import math
from typing import Sequence

import numpy as np


METHOD_VERSION = "future_refit_bounded_brier_filtration_adapter_v0"


@dataclass(frozen=True)
class BoundedBrierFiltrationScores:
    """Score matrices are observations × levels, separately for each refit."""

    method_version: str
    refit_ids: tuple[str, ...]
    row_ids: tuple[str, ...]
    level_names: tuple[str, str, str]
    information_axes: tuple[tuple[str, ...], ...]
    category_count: int
    probability_simplex_verified: bool
    normalized_brier_score_bounds: tuple[float, float]
    contrast_gain_bounds: tuple[float, float]
    score_tensor: np.ndarray
    contrast_gains: np.ndarray
    provenance_verified: bool
    training_process_iid_verified: bool
    independent_validation_blocks_verified: bool
    eligible_for_primary_route: bool

    def metadata(self) -> dict[str, object]:
        """Serializable *structural-only* data, with no outcomes or scores."""
        return {
            "method_version": self.method_version,
            "refit_count": len(self.refit_ids),
            "row_count": len(self.row_ids),
            "level_names": list(self.level_names),
            "information_axes": [list(row) for row in self.information_axes],
            "contrast_count": 2,
            "category_count": self.category_count,
            "probability_simplex_verified": self.probability_simplex_verified,
            "normalized_brier_score_bounds": [0.0, 1.0],
            "contrast_gain_bounds": [-1.0, 1.0],
            "provenance_verified": False,
            "training_process_iid_verified": False,
            "independent_validation_blocks_verified": False,
            "eligible_for_primary_route": False,
        }


def _unique_labels(seq: Sequence[object], *, n: int, name: str) -> tuple[str, ...]:
    if len(seq) != n:
        raise ValueError(f"{name} length does not match data")
    values = tuple(str(x).strip() for x in seq)
    if any(not x for x in values) or len(values) != len(set(values)):
        raise ValueError(f"{name} must be non-empty, unique and aligned")
    return values


def _validate_axes(
    level_names: Sequence[object],
    axes: Sequence[Sequence[str]],
) -> tuple[tuple[str, str, str], tuple[tuple[str, ...], ...]]:
    names = _unique_labels(level_names, n=3, name="level_names")
    if len(axes) != 3:
        raise ValueError("exactly three ordered information axis sets required")
    normalized = []
    for level in axes:
        if isinstance(level, str):
            raise ValueError("information_axes must be sequences of axis names")
        vals = tuple(str(x).strip() for x in level)
        if any(not x for x in vals) or len(vals) != len(set(vals)):
            raise ValueError("information axes within a level must be unique and nonempty")
        normalized.append(vals)
    if not (
        set(normalized[0]) < set(normalized[1])
        and set(normalized[1]) < set(normalized[2])
    ):
        raise ValueError("information levels must be strictly nested by axis inclusion")
    return names, tuple(normalized)


def normalized_brier_filtration_gains(
    probabilities: np.ndarray | Sequence,
    observed_state: Sequence[object],
    *,
    refit_ids: Sequence[object],
    row_ids: Sequence[object],
    level_names: Sequence[object] = ("marginal", "identity", "identity-context"),
    information_axes: Sequence[Sequence[str]] = (
        (),
        ("identity",),
        ("identity", "context"),
    ),
    simplex_tolerance: float = 1e-10,
) -> BoundedBrierFiltrationScores:
    """Score *frozen* refit × row × 3-level × category probabilities.

    The caller must separately freeze the predictive levels, training process,
    validation roster and physical block sampling design BEFORE accessing
    outcome labels. This raw adapter does not attest that chronology.

    Input outcome states are zero-based category indices and cannot be
    probabilistic/imputed targets. Missing labels fail closed.
    """
    a = np.asarray(probabilities, dtype=float)
    if a.ndim != 4 or 0 in a.shape or a.shape[2] != 3 or a.shape[3] < 2:
        raise ValueError(
            "probabilities must be [refit,row,three_levels,categories>=2]"
        )
    R, N, _, K = a.shape
    rid = _unique_labels(refit_ids, n=R, name="refit_ids")
    row = _unique_labels(row_ids, n=N, name="row_ids")
    names, axes = _validate_axes(level_names, information_axes)
    if (
        isinstance(simplex_tolerance, bool)
        or not isinstance(simplex_tolerance, (int, float))
        or not math.isfinite(simplex_tolerance)
        or not 0 < simplex_tolerance <= 1e-8
    ):
        raise ValueError("simplex_tolerance must be in (0, 1e-8]")
    if not np.isfinite(a).all():
        raise ValueError("predicted probability values must all be finite")
    if np.any(a < 0) or np.any(a > 1):
        raise ValueError("predicted probabilities must lie in [0,1]")
    if np.any(np.abs(a.sum(axis=-1) - 1.0) > simplex_tolerance):
        raise ValueError("every refit-row-level distribution must sum to one")

    original = np.asarray(observed_state)
    if original.shape != (N,):
        raise ValueError("observed_state must have exactly one category per row")
    if original.dtype.kind not in "iu":
        raise ValueError("observed_state must contain integer category indices")
    if np.any(original < 0) or np.any(original >= K):
        raise ValueError("observed_state indices must lie in [0, K)")
    observed = original.astype(int, copy=False)
    # We do not round/renormalize probabilities. The score proof holds for
    # genuine simplex predictions and tiny numerical normalization tolerance.
    one_hot = np.eye(K, dtype=float)[observed]
    score = 1.0 - 0.5 * np.sum(
        np.square(a - one_hot[None, :, None, :]), axis=-1
    )
    if (
        np.any(score < -1e-9)
        or np.any(score > 1.0 + 1e-9)
        or not np.isfinite(score).all()
    ):
        raise ValueError("normalized Brier score outside its theoretical [0,1] bounds")
    gain = np.stack((score[:, :, 1] - score[:, :, 0],
                     score[:, :, 2] - score[:, :, 1]), axis=-1)
    if np.any(gain < -1.0-1e-9) or np.any(gain > 1.0+1e-9):
        raise ValueError("Brier score contrasts outside [-1,1]")
    return BoundedBrierFiltrationScores(
        method_version=METHOD_VERSION,
        refit_ids=rid,
        row_ids=row,
        level_names=names,
        information_axes=axes,
        category_count=K,
        probability_simplex_verified=True,
        normalized_brier_score_bounds=(0.0, 1.0),
        contrast_gain_bounds=(-1.0, 1.0),
        score_tensor=score,
        contrast_gains=gain,
        provenance_verified=False,
        training_process_iid_verified=False,
        independent_validation_blocks_verified=False,
        eligible_for_primary_route=False,
    )
