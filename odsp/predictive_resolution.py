"""Model-agnostic decomposition of held-out predictive score across information levels.

ODSP compares richer ecological-state predictions against explicitly declared
lower-information comparators. This module generalizes a two-level
conditional-versus-baseline comparison to an ordered information ladder

    q_0 -> q_1 -> ... -> q_K

evaluated on the same held-out rows. The group-level total gain telescopes exactly
into adjacent resolution increments. No learner, state geometry or probability
representation is chosen here: callers provide row-wise predictive scores from any
upstream modelling stack.

For logarithmic scores, if each q_k equals the true conditional distribution for
a nested information set C_k = (C_{k-1}, Z_k), the expected k-th increment is
I(A; Z_k | C_{k-1}). With fitted or misspecified predictors, the realized
increment remains a held-out predictive quantity rather than a direct estimate
of biological information.
"""
from __future__ import annotations

from dataclasses import asdict, dataclass
import math
from typing import Sequence

import numpy as np

from .transferability import classify_independent_gains


@dataclass(frozen=True)
class ResolutionIncrement:
    """One adjacent information-level gain within an independent group."""

    lower_level: str
    upper_level: str
    mean_gain: float

    def as_dict(self) -> dict[str, object]:
        return asdict(self)


@dataclass(frozen=True)
class ResolutionGroupScore:
    """Predictive resolution decomposition for one independent group."""

    group: object
    row_count: int
    positive_weight_row_count: int
    total_weight: float
    mean_scores: tuple[tuple[str, float], ...]
    increments: tuple[ResolutionIncrement, ...]
    total_gain: float
    additivity_error: float

    def as_dict(self) -> dict[str, object]:
        return {
            "group": self.group,
            "row_count": self.row_count,
            "positive_weight_row_count": self.positive_weight_row_count,
            "total_weight": self.total_weight,
            "mean_scores": [
                {"level": level, "mean_score": value}
                for level, value in self.mean_scores
            ],
            "increments": [row.as_dict() for row in self.increments],
            "total_gain": self.total_gain,
            "additivity_error": self.additivity_error,
        }


@dataclass(frozen=True)
class PredictiveResolutionResult:
    """Independent-group score ladder and conservative sign summaries."""

    levels: tuple[str, ...]
    groups: tuple[ResolutionGroupScore, ...]
    total_gain_category: str
    increment_categories: tuple[tuple[str, str, str], ...]

    def as_dict(self) -> dict[str, object]:
        return {
            "levels": list(self.levels),
            "groups": [row.as_dict() for row in self.groups],
            "total_gains": [row.total_gain for row in self.groups],
            "total_gain_category": self.total_gain_category,
            "increment_categories": [
                {
                    "lower_level": lower,
                    "upper_level": upper,
                    "gain_category": category,
                }
                for lower, upper, category in self.increment_categories
            ],
        }


def _validate_levels(
    levels: Sequence[tuple[str, Sequence[float]]],
) -> tuple[tuple[str, ...], tuple[np.ndarray, ...]]:
    if len(levels) < 2:
        raise ValueError("levels must contain at least two ordered predictive scores")
    names: list[str] = []
    arrays: list[np.ndarray] = []
    n: int | None = None
    for name, values in levels:
        label = str(name).strip()
        if not label:
            raise ValueError("level names must be non-empty")
        if label in names:
            raise ValueError(f"level names must be unique: {label!r}")
        score = np.asarray(values, dtype=float)
        if score.ndim != 1 or score.size == 0:
            raise ValueError(
                f"score vector for level {label!r} must be non-empty and one-dimensional"
            )
        if n is None:
            n = int(score.size)
        elif score.size != n:
            raise ValueError("all score vectors must have equal length")
        if np.isnan(score).any() or np.isposinf(score).any():
            raise ValueError(
                f"score vector for level {label!r} may contain finite values or -inf, "
                "but not NaN or +inf"
            )
        names.append(label)
        arrays.append(score)
    return tuple(names), tuple(arrays)


def _validate_groups(groups: Sequence[object], n: int) -> np.ndarray:
    values = np.asarray(list(groups), dtype=object)
    if values.shape != (n,):
        raise ValueError("groups must contain one value per score row")
    for value in values.tolist():
        if value is None:
            raise ValueError("group labels may not be missing")
        try:
            hash(value)
        except TypeError as exc:
            raise ValueError("group labels must be hashable") from exc
    return values


def _validate_weights(sample_weight: Sequence[float] | None, n: int) -> np.ndarray:
    if sample_weight is None:
        return np.ones(n, dtype=float)
    weight = np.asarray(sample_weight, dtype=float)
    if weight.shape != (n,):
        raise ValueError("sample_weight must contain one value per score row")
    if not np.isfinite(weight).all() or np.any(weight < 0):
        raise ValueError("sample_weight must be finite and non-negative")
    if not float(weight.sum()) > 0:
        raise ValueError("sample_weight must have positive total mass")
    return weight


def _weighted_mean(values: np.ndarray, weight: np.ndarray) -> float:
    positive = weight > 0
    if not np.any(positive):
        raise ValueError("every independent group must have positive total weight")
    selected = values[positive]
    selected_weight = weight[positive]
    if np.isneginf(selected).any():
        return float("-inf")
    return float(np.sum(selected * selected_weight) / np.sum(selected_weight))


def _difference(upper: float, lower: float) -> float:
    if math.isinf(upper) and upper < 0:
        return float("-inf")
    if not math.isfinite(lower):
        raise ValueError("intermediate comparator score must be finite")
    return float(upper - lower)


def decompose_predictive_resolution(
    levels: Sequence[tuple[str, Sequence[float]]],
    groups: Sequence[object],
    *,
    sample_weight: Sequence[float] | None = None,
    gain_tolerance: float = 0.0,
) -> PredictiveResolutionResult:
    """Decompose held-out predictive utility across ordered information levels.

    ``levels`` is ordered from the least to the most informative predictive
    representation. Each score vector must be evaluated on the same held-out
    realized states and use the same score orientation (larger is better).

    The procedure does not require log scores. Any row-wise proper score can be
    supplied if its orientation is consistent across levels. Log scores retain
    the information-theoretic interpretation described in the module docstring.

    Every intermediate comparator level must be finite on each positive-weight
    row. This is a fail-closed support rule: a zero-density intermediate
    comparator cannot be rewarded merely because a richer level assigns positive
    density. The richest final level may contain ``-inf`` and is then
    conservatively scored as negative infinite gain.
    """

    if not math.isfinite(gain_tolerance) or gain_tolerance < 0:
        raise ValueError("gain_tolerance must be finite and non-negative")
    names, score_arrays = _validate_levels(levels)
    n = score_arrays[0].size
    group_array = _validate_groups(groups, n)
    weight = _validate_weights(sample_weight, n)

    positive = weight > 0
    for name, score in zip(names[:-1], score_arrays[:-1]):
        if not np.isfinite(score[positive]).all():
            raise ValueError(
                f"comparator level {name!r} must be finite on every positive-weight row"
            )

    rows: list[ResolutionGroupScore] = []
    ordered_groups = tuple(dict.fromkeys(group_array.tolist()))
    for group in ordered_groups:
        mask = group_array == group
        local_weight = weight[mask]
        if not float(local_weight.sum()) > 0:
            raise ValueError(f"group {group!r} has zero total score weight")
        local_means = tuple(
            (name, _weighted_mean(score[mask], local_weight))
            for name, score in zip(names, score_arrays)
        )
        increments = tuple(
            ResolutionIncrement(
                lower_level=names[index],
                upper_level=names[index + 1],
                mean_gain=_difference(
                    local_means[index + 1][1],
                    local_means[index][1],
                ),
            )
            for index in range(len(names) - 1)
        )
        total = _difference(local_means[-1][1], local_means[0][1])
        if math.isfinite(total) and all(
            math.isfinite(row.mean_gain) for row in increments
        ):
            additivity_error = float(
                total - sum(row.mean_gain for row in increments)
            )
        elif total == float("-inf") and increments[-1].mean_gain == float("-inf"):
            additivity_error = 0.0
        else:
            raise ValueError(
                "score ladder produced an undefined additive decomposition; "
                "check intermediate support and score orientation"
            )
        rows.append(
            ResolutionGroupScore(
                group=group,
                row_count=int(np.count_nonzero(mask)),
                positive_weight_row_count=int(np.count_nonzero(local_weight > 0)),
                total_weight=float(local_weight.sum()),
                mean_scores=local_means,
                increments=increments,
                total_gain=float(total),
                additivity_error=float(additivity_error),
            )
        )

    total_category = classify_independent_gains(
        [row.total_gain for row in rows],
        tolerance=gain_tolerance,
    )
    increment_categories: list[tuple[str, str, str]] = []
    for index in range(len(names) - 1):
        category = classify_independent_gains(
            [row.increments[index].mean_gain for row in rows],
            tolerance=gain_tolerance,
        )
        increment_categories.append((names[index], names[index + 1], category))

    return PredictiveResolutionResult(
        levels=names,
        groups=tuple(rows),
        total_gain_category=total_category,
        increment_categories=tuple(increment_categories),
    )
