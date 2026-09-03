"""Cross-fitted independent-group transferability for Chapter 2.

Some prospective answer checks use one common fitted support for several held-out
groups. Others are genuinely cross-fitted: each independent group is scored by a
model trained without that group. This module covers the latter without pooling
record mass or changing the conservative all-positive / all-nonpositive / mixed
terminal rule.
"""
from __future__ import annotations

import math
from typing import Mapping, Sequence

import numpy as np

from .grouped_transferability import (
    GroupedTransferabilityResult,
    IndependentGroupTransferability,
)
from .transferability import classify_independent_gains, score_conditional_transferability


def _normalize_crossfit_groups(
    groups: (
        Mapping[str, tuple[np.ndarray, np.ndarray]]
        | Sequence[tuple[str, np.ndarray, np.ndarray]]
    ),
) -> tuple[tuple[str, np.ndarray, np.ndarray], ...]:
    if isinstance(groups, Mapping):
        items = tuple(
            (group_id, pair[0], pair[1])
            for group_id, pair in groups.items()
        )
    else:
        items = tuple(groups)
    if not items:
        raise ValueError("groups must contain at least one cross-fitted independent group")

    normalized: list[tuple[str, np.ndarray, np.ndarray]] = []
    seen: set[str] = set()
    for raw_group_id, model_support, heldout_support in items:
        if not isinstance(raw_group_id, str) or not raw_group_id.strip():
            raise ValueError("group IDs must be non-empty strings")
        group_id = raw_group_id.strip()
        if group_id in seen:
            raise ValueError(f"duplicate independent group ID: {group_id!r}")
        seen.add(group_id)
        normalized.append(
            (
                group_id,
                np.asarray(model_support, dtype=float),
                np.asarray(heldout_support, dtype=float),
            )
        )
    return tuple(normalized)


def score_crossfitted_independent_groups(
    groups: (
        Mapping[str, tuple[np.ndarray, np.ndarray]]
        | Sequence[tuple[str, np.ndarray, np.ndarray]]
    ),
    *,
    base_axes: Sequence[int],
    added_axes: Sequence[int],
    model_unavailable_masks: Mapping[str, np.ndarray | None] | None = None,
    heldout_unavailable_masks: Mapping[str, np.ndarray | None] | None = None,
    gain_tolerance: float = 1e-12,
) -> GroupedTransferabilityResult:
    """Score group-specific model/held-out pairs under one frozen decision rule.

    Each ``group_id`` receives its own ``model_support`` and ``heldout_support``.
    This is appropriate for leave-one-group-out or deterministic-fold designs in
    which the fitted support differs by held-out group. Every group is normalized
    and scored independently; the terminal classification depends only on the
    vector of group-level gains, never on pooled event mass.
    """

    if gain_tolerance < 0 or not math.isfinite(gain_tolerance):
        raise ValueError("gain_tolerance must be finite and non-negative")

    normalized = _normalize_crossfit_groups(groups)
    group_ids = {group_id for group_id, _, _ in normalized}
    model_masks = {} if model_unavailable_masks is None else dict(model_unavailable_masks)
    heldout_masks = (
        {} if heldout_unavailable_masks is None else dict(heldout_unavailable_masks)
    )
    unknown_model_masks = set(model_masks) - group_ids
    unknown_heldout_masks = set(heldout_masks) - group_ids
    if unknown_model_masks:
        unknown = ", ".join(sorted(unknown_model_masks))
        raise ValueError(f"model_unavailable_masks contains unknown groups: {unknown}")
    if unknown_heldout_masks:
        unknown = ", ".join(sorted(unknown_heldout_masks))
        raise ValueError(f"heldout_unavailable_masks contains unknown groups: {unknown}")

    scored_groups: list[IndependentGroupTransferability] = []
    gains: list[float] = []
    for group_id, model_support, heldout_support in normalized:
        score = score_conditional_transferability(
            model_support,
            heldout_support,
            base_axes=base_axes,
            added_axes=added_axes,
            model_unavailable_mask=model_masks.get(group_id),
            heldout_unavailable_mask=heldout_masks.get(group_id),
            gain_tolerance=gain_tolerance,
        )
        scored_groups.append(IndependentGroupTransferability(group_id, score))
        gains.append(float(score.mean_log_score_gain))

    classification = classify_independent_gains(gains, tolerance=gain_tolerance)
    mean_gain = (
        float("-inf")
        if any(value == float("-inf") for value in gains)
        else float(sum(gains) / len(gains))
    )
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
