"""Prospectively independent group-level transferability for Chapter 2.

A single held-out score can show whether fitted added-axis organization transfers
to one independent support set. Empirical N2 designs often have several genuinely
independent answer-check groups, such as individuals, years, sites or instruments.
This module scores those groups separately and then applies the conservative
all-positive / all-nonpositive / mixed rule without pooling group mass.

The equal-group mean is descriptive only. Promotion decisions are based on the
per-group sign pattern via ``classify_independent_gains``.
"""
from __future__ import annotations

from dataclasses import asdict, dataclass
import math
from typing import Mapping, Sequence

import numpy as np

from .transferability import (
    ConditionalTransferabilityScore,
    classify_independent_gains,
    score_conditional_transferability,
)


@dataclass(frozen=True)
class IndependentGroupTransferability:
    """One prospectively independent held-out group's transferability score."""

    group_id: str
    score: ConditionalTransferabilityScore

    def as_dict(self) -> dict[str, object]:
        return {"group_id": self.group_id, "score": self.score.as_dict()}


@dataclass(frozen=True)
class GroupedTransferabilityResult:
    """Conservative transferability decision across independent held-out groups."""

    base_axes: tuple[int, ...]
    added_axes: tuple[int, ...]
    groups: tuple[IndependentGroupTransferability, ...]
    gains: tuple[float, ...]
    equal_group_mean_gain: float
    classification: str
    gain_tolerance: float

    def as_dict(self) -> dict[str, object]:
        return {
            "base_axes": list(self.base_axes),
            "added_axes": list(self.added_axes),
            "groups": [group.as_dict() for group in self.groups],
            "gains": list(self.gains),
            "equal_group_mean_gain": self.equal_group_mean_gain,
            "classification": self.classification,
            "gain_tolerance": self.gain_tolerance,
        }


def _normalize_group_supports(
    heldout_supports: Mapping[str, np.ndarray] | Sequence[tuple[str, np.ndarray]],
) -> tuple[tuple[str, np.ndarray], ...]:
    items = (
        tuple(heldout_supports.items())
        if isinstance(heldout_supports, Mapping)
        else tuple(heldout_supports)
    )
    if not items:
        raise ValueError("heldout_supports must contain at least one independent group")

    normalized: list[tuple[str, np.ndarray]] = []
    seen: set[str] = set()
    for raw_group_id, support in items:
        if not isinstance(raw_group_id, str) or not raw_group_id.strip():
            raise ValueError("group IDs must be non-empty strings")
        group_id = raw_group_id.strip()
        if group_id in seen:
            raise ValueError(f"duplicate independent group ID: {group_id!r}")
        seen.add(group_id)
        normalized.append((group_id, np.asarray(support, dtype=float)))
    return tuple(normalized)


def score_independent_groups(
    model_support: np.ndarray,
    heldout_supports: Mapping[str, np.ndarray] | Sequence[tuple[str, np.ndarray]],
    *,
    base_axes: Sequence[int],
    added_axes: Sequence[int],
    model_unavailable_mask: np.ndarray | None = None,
    heldout_unavailable_masks: Mapping[str, np.ndarray | None] | None = None,
    gain_tolerance: float = 1e-12,
) -> GroupedTransferabilityResult:
    """Score multiple prospectively independent held-out support groups.

    Each group is normalized and scored independently with
    ``score_conditional_transferability``. Group sample size therefore cannot
    silently dominate the terminal classification. The returned
    ``equal_group_mean_gain`` is the arithmetic mean of group gains and is
    descriptive; ``classification`` is the conservative sign-pattern decision.

    ``generalizing`` means every independent group has gain strictly greater than
    ``gain_tolerance``. ``non_generalizing`` means every gain is at or below the
    tolerance. Otherwise the result is ``mixed``.
    """

    if gain_tolerance < 0 or not math.isfinite(gain_tolerance):
        raise ValueError("gain_tolerance must be finite and non-negative")

    groups = _normalize_group_supports(heldout_supports)
    masks = {} if heldout_unavailable_masks is None else dict(heldout_unavailable_masks)
    unknown_masks = set(masks) - {group_id for group_id, _ in groups}
    if unknown_masks:
        unknown = ", ".join(sorted(unknown_masks))
        raise ValueError(f"heldout_unavailable_masks contains unknown groups: {unknown}")

    scored_groups: list[IndependentGroupTransferability] = []
    gains: list[float] = []
    for group_id, support in groups:
        score = score_conditional_transferability(
            model_support,
            support,
            base_axes=base_axes,
            added_axes=added_axes,
            model_unavailable_mask=model_unavailable_mask,
            heldout_unavailable_mask=masks.get(group_id),
            gain_tolerance=gain_tolerance,
        )
        scored_groups.append(IndependentGroupTransferability(group_id, score))
        gains.append(float(score.mean_log_score_gain))

    classification = classify_independent_gains(gains, tolerance=gain_tolerance)
    if any(value == float("-inf") for value in gains):
        mean_gain = float("-inf")
    else:
        mean_gain = float(sum(gains) / len(gains))

    first_score = scored_groups[0].score
    return GroupedTransferabilityResult(
        base_axes=first_score.base_axes,
        added_axes=first_score.added_axes,
        groups=tuple(scored_groups),
        gains=tuple(gains),
        equal_group_mean_gain=mean_gain,
        classification=classification,
        gain_tolerance=float(gain_tolerance),
    )
