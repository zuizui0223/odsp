"""State-space agnostic predictive gain for ecological-state distributions.

ODSP can represent an ecological state as a finite category, a real-valued scalar,
a circular variable or a joint state.  Those representations require different
learners and probability objects, but their primary transfer question can be
written on one common scoring layer.

For each independently held-out realized state ``a_i`` the caller supplies

    log q(a_i | X_i)

from the richer context-conditioned predictor and

    log q0(a_i)

from a declared lower-information comparator fitted on the same training data.
The primary gain is their weighted held-out mean difference.

Because both terms are evaluated against the same reference measure, any common
row-wise log-Jacobian or reference-measure term cancels exactly.  This is the key
bridge between probability masses for discrete states and densities for
continuous, circular and joint states.

This module deliberately does not choose a learner, state geometry, comparator or
independence unit.  Those are scientific design choices that remain explicit in
state-space-specific code and prospective empirical contracts.
"""
from __future__ import annotations

from dataclasses import asdict, dataclass
import math
from typing import Mapping, Sequence

import numpy as np

from .transferability import classify_independent_gains


@dataclass(frozen=True)
class DistributionalGainScore:
    """Held-out conditional-versus-baseline logarithmic score."""

    row_count: int
    positive_weight_row_count: int
    total_weight: float
    mean_conditional_log_score: float
    mean_baseline_log_score: float
    mean_log_score_gain: float

    def as_dict(self) -> dict[str, object]:
        return asdict(self)


@dataclass(frozen=True)
class DistributionalGroupScore:
    """One independently scored transfer group."""

    group: str
    score: DistributionalGainScore

    def as_dict(self) -> dict[str, object]:
        return {"group": self.group, **self.score.as_dict()}


@dataclass(frozen=True)
class GroupedDistributionalGainScore:
    """Independent-group scores plus the conservative ODSP sign category."""

    groups: tuple[DistributionalGroupScore, ...]
    gain_category: str

    @property
    def gains(self) -> tuple[float, ...]:
        return tuple(row.score.mean_log_score_gain for row in self.groups)

    def as_dict(self) -> dict[str, object]:
        return {
            "groups": [row.as_dict() for row in self.groups],
            "gains": list(self.gains),
            "gain_category": self.gain_category,
        }


def _validate_log_vector(values: Sequence[float], *, name: str) -> np.ndarray:
    result = np.asarray(values, dtype=float)
    if result.ndim != 1 or result.size == 0:
        raise ValueError(f"{name} must be a non-empty one-dimensional vector")
    if np.isnan(result).any() or np.isposinf(result).any():
        raise ValueError(f"{name} may contain finite values or -inf, but not NaN or +inf")
    return result


def _validate_weights(values: Sequence[float] | None, n: int) -> np.ndarray:
    if values is None:
        return np.ones(n, dtype=float)
    result = np.asarray(values, dtype=float)
    if result.shape != (n,):
        raise ValueError("sample_weight must contain one value per score row")
    if not np.isfinite(result).all() or np.any(result < 0):
        raise ValueError("sample_weight must be finite and non-negative")
    if not float(result.sum()) > 0:
        raise ValueError("sample_weight must have positive total mass")
    return result


def _weighted_log_mean(values: np.ndarray, weights: np.ndarray) -> float:
    positive = weights > 0
    selected = values[positive]
    selected_weight = weights[positive]
    if np.isneginf(selected).any():
        return float("-inf")
    return float(np.sum(selected_weight * selected) / np.sum(selected_weight))


def score_distributional_gain(
    conditional_log_score: Sequence[float],
    baseline_log_score: Sequence[float],
    *,
    sample_weight: Sequence[float] | None = None,
) -> DistributionalGainScore:
    """Score any ecological-state distribution on a common log-score layer.

    ``conditional_log_score`` and ``baseline_log_score`` must be evaluated on the
    same realized held-out states and against the same reference measure.  The
    baseline must assign positive probability/density to every positive-weight
    realized state, so its log score must remain finite.  The richer predictor may
    assign zero mass and therefore ``-inf``; in that case its mean gain is
    conservatively ``-inf``.
    """

    conditional = _validate_log_vector(
        conditional_log_score, name="conditional_log_score"
    )
    baseline = _validate_log_vector(baseline_log_score, name="baseline_log_score")
    if baseline.shape != conditional.shape:
        raise ValueError("conditional and baseline log-score vectors must have equal length")
    weights = _validate_weights(sample_weight, conditional.size)
    positive = weights > 0
    if not np.isfinite(baseline[positive]).all():
        raise ValueError("baseline log score must be finite on every positive-weight row")

    mean_conditional = _weighted_log_mean(conditional, weights)
    mean_baseline = _weighted_log_mean(baseline, weights)
    gain = (
        float("-inf")
        if math.isinf(mean_conditional) and mean_conditional < 0
        else float(mean_conditional - mean_baseline)
    )
    return DistributionalGainScore(
        row_count=int(conditional.size),
        positive_weight_row_count=int(np.count_nonzero(positive)),
        total_weight=float(weights.sum()),
        mean_conditional_log_score=float(mean_conditional),
        mean_baseline_log_score=float(mean_baseline),
        mean_log_score_gain=float(gain),
    )


def score_distributional_groups(
    groups: Mapping[str, tuple[Sequence[float], Sequence[float]]]
    | Sequence[tuple[str, Sequence[float], Sequence[float]]],
    *,
    sample_weights: Mapping[str, Sequence[float]] | None = None,
    tolerance: float = 0.0,
) -> GroupedDistributionalGainScore:
    """Score independent groups without pooling their observation mass.

    Each group receives its own conditional-versus-baseline gain.  The terminal
    category is then computed from the vector of group gains, so a large group
    cannot rescue a conflicting independent group through pooled event count.
    """

    if isinstance(groups, Mapping):
        items = [(str(name), values[0], values[1]) for name, values in groups.items()]
    else:
        items = [(str(name), conditional, baseline) for name, conditional, baseline in groups]
    if not items:
        raise ValueError("groups must contain at least one independent group")
    if not math.isfinite(tolerance) or tolerance < 0:
        raise ValueError("tolerance must be finite and non-negative")

    seen: set[str] = set()
    rows: list[DistributionalGroupScore] = []
    weight_lookup = {} if sample_weights is None else dict(sample_weights)
    for name, conditional, baseline in items:
        if name in seen:
            raise ValueError("independent group names must be unique")
        seen.add(name)
        weights = weight_lookup.get(name)
        rows.append(
            DistributionalGroupScore(
                group=name,
                score=score_distributional_gain(
                    conditional,
                    baseline,
                    sample_weight=weights,
                ),
            )
        )

    extra_weights = set(weight_lookup) - seen
    if extra_weights:
        raise ValueError(
            "sample_weights contains unknown groups: " + ", ".join(sorted(extra_weights))
        )
    category = classify_independent_gains(
        [row.score.mean_log_score_gain for row in rows],
        tolerance=tolerance,
    )
    return GroupedDistributionalGainScore(groups=tuple(rows), gain_category=category)
