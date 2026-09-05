"""Multi-level transfer profiles for already-held-out state predictions.

A single terminal label can hide scientifically important heterogeneity.  This
module accepts *out-of-sample* state probability vectors and groups the same row-
level conditional-versus-marginal log gains at multiple caller-declared levels
(e.g. individual, site, year, species).  Every level is classified separately.
Coarser positive aggregation never overrides a mixed or failed finer level.
"""
from __future__ import annotations

from dataclasses import asdict, dataclass
import math
from typing import Mapping, Sequence

import numpy as np

from .transferability import classify_independent_gains


@dataclass(frozen=True)
class GeneralizationGroupScore:
    group: str
    row_count: int
    total_weight: float
    mean_log_score_gain: float

    def as_dict(self) -> dict[str, object]:
        return asdict(self)


@dataclass(frozen=True)
class GeneralizationLevelProfile:
    level: str
    groups: tuple[GeneralizationGroupScore, ...]
    gain_category: str
    positive_group_count: int
    nonpositive_group_count: int
    positive_group_fraction: float
    mean_gain_descriptive: float
    median_gain_descriptive: float
    minimum_group_gain: float
    maximum_group_gain: float

    @property
    def gains(self) -> tuple[float, ...]:
        return tuple(group.mean_log_score_gain for group in self.groups)

    def as_dict(self) -> dict[str, object]:
        result = asdict(self)
        result["gains"] = list(self.gains)
        return result


@dataclass(frozen=True)
class GeneralizationProfile:
    levels: tuple[GeneralizationLevelProfile, ...]
    row_count: int
    class_count: int
    scoring_epsilon: float
    fine_level_failures_may_not_be_overridden: bool = True

    def as_dict(self) -> dict[str, object]:
        return {
            "levels": [level.as_dict() for level in self.levels],
            "row_count": int(self.row_count),
            "class_count": int(self.class_count),
            "scoring_epsilon": float(self.scoring_epsilon),
            "fine_level_failures_may_not_be_overridden": True,
        }


def _validate_probability_matrix(probability: np.ndarray, class_count: int | None = None) -> np.ndarray:
    matrix = np.asarray(probability, dtype=float)
    if matrix.ndim != 2 or matrix.shape[0] == 0 or matrix.shape[1] < 2:
        raise ValueError("probability must be a non-empty rows-by-state matrix with at least two states")
    if class_count is not None and matrix.shape[1] != int(class_count):
        raise ValueError("probability state count does not match classes")
    if not np.isfinite(matrix).all() or np.any(matrix < 0):
        raise ValueError("probability must contain finite non-negative values")
    if np.any(np.abs(matrix.sum(axis=1) - 1.0) > 1e-8):
        raise ValueError("probability rows must sum to one")
    return matrix


def _validate_marginal(marginal: np.ndarray, class_count: int) -> np.ndarray:
    values = np.asarray(marginal, dtype=float)
    if values.shape != (class_count,):
        raise ValueError("marginal_probability must contain one probability per state")
    if not np.isfinite(values).all() or np.any(values < 0):
        raise ValueError("marginal_probability must be finite and non-negative")
    if abs(float(values.sum()) - 1.0) > 1e-8:
        raise ValueError("marginal_probability must sum to one")
    return values


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


def _weights(sample_weight: Sequence[float] | None, n: int) -> np.ndarray:
    if sample_weight is None:
        return np.ones(n, dtype=float)
    values = np.asarray(sample_weight, dtype=float)
    if values.shape != (n,):
        raise ValueError("sample_weight must contain one value per row")
    if not np.isfinite(values).all() or np.any(values < 0):
        raise ValueError("sample_weight must be finite and non-negative")
    if not float(values.sum()) > 0:
        raise ValueError("sample_weight must have positive total mass")
    return values


def _group_text(value: object) -> str:
    return value if isinstance(value, str) else repr(value)


def generalization_profile_from_probability_field(
    probability: np.ndarray,
    y: Sequence[object],
    *,
    classes: Sequence[object],
    marginal_probability: np.ndarray,
    groupings: Mapping[str, Sequence[object]],
    sample_weight: Sequence[float] | None = None,
    tolerance: float = 0.0,
    epsilon: float = 1e-15,
) -> GeneralizationProfile:
    """Build a multi-level profile from genuinely out-of-sample predictions.

    The caller is responsible for supplying probability rows generated without
    fitting on those outcomes (for example cross-fitted or prospectively held-out
    predictions).  Each declared level is summarized independently.  The group
    mean is weighted by ``sample_weight``; the level-wide mean is descriptive and
    cannot rescue a non-positive group under the conservative terminal rule.
    """

    if not math.isfinite(epsilon) or not 0.0 < epsilon < 0.5:
        raise ValueError("epsilon must lie strictly between zero and 0.5")
    if tolerance < 0 or not math.isfinite(tolerance):
        raise ValueError("tolerance must be finite and non-negative")
    if not groupings:
        raise ValueError("groupings must contain at least one independent level")

    class_tuple = tuple(classes)
    if len(class_tuple) < 2 or len(set(class_tuple)) != len(class_tuple):
        raise ValueError("classes must contain at least two unique states")
    matrix = _validate_probability_matrix(probability, len(class_tuple))
    marginal = _validate_marginal(marginal_probability, len(class_tuple))
    labels = _encode_labels(y, class_tuple, matrix.shape[0])
    weights = _weights(sample_weight, matrix.shape[0])

    true_conditional = matrix[np.arange(matrix.shape[0]), labels]
    true_marginal = marginal[labels]
    row_gain = np.log(np.maximum(true_conditional, epsilon)) - np.log(
        np.maximum(true_marginal, epsilon)
    )

    profiles: list[GeneralizationLevelProfile] = []
    for level, values in groupings.items():
        level_name = str(level)
        if not level_name:
            raise ValueError("grouping level names must be non-empty")
        group_values = np.asarray(values, dtype=object)
        if group_values.shape != (matrix.shape[0],):
            raise ValueError(f"grouping {level_name!r} must contain one value per row")

        ordered: list[object] = []
        seen: set[object] = set()
        for value in group_values.tolist():
            try:
                if value not in seen:
                    seen.add(value)
                    ordered.append(value)
            except TypeError as exc:
                raise ValueError(f"group labels for {level_name!r} must be hashable") from exc

        groups: list[GeneralizationGroupScore] = []
        for value in ordered:
            mask = group_values == value
            positive_weight = weights[mask]
            total_weight = float(positive_weight.sum())
            if total_weight <= 0:
                continue
            gain = float(np.sum(weights[mask] * row_gain[mask]) / total_weight)
            groups.append(
                GeneralizationGroupScore(
                    group=_group_text(value),
                    row_count=int(np.count_nonzero(mask)),
                    total_weight=total_weight,
                    mean_log_score_gain=gain,
                )
            )
        if not groups:
            raise ValueError(f"grouping {level_name!r} contains no positive-weight group")

        gains = np.asarray([group.mean_log_score_gain for group in groups], dtype=float)
        positive = gains > tolerance
        profiles.append(
            GeneralizationLevelProfile(
                level=level_name,
                groups=tuple(groups),
                gain_category=classify_independent_gains(gains, tolerance=tolerance),
                positive_group_count=int(np.count_nonzero(positive)),
                nonpositive_group_count=int(gains.size - np.count_nonzero(positive)),
                positive_group_fraction=float(np.mean(positive)),
                mean_gain_descriptive=float(np.mean(gains)),
                median_gain_descriptive=float(np.median(gains)),
                minimum_group_gain=float(np.min(gains)),
                maximum_group_gain=float(np.max(gains)),
            )
        )

    return GeneralizationProfile(
        levels=tuple(profiles),
        row_count=int(matrix.shape[0]),
        class_count=len(class_tuple),
        scoring_epsilon=float(epsilon),
    )
