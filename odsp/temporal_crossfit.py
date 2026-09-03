"""Temporal-axis wrappers for cross-fitted independent-group transferability."""
from __future__ import annotations

from typing import Mapping, Sequence

import numpy as np

from .crossfitted_transferability import score_crossfitted_independent_groups
from .grouped_transferability import GroupedTransferabilityResult


def _canonical_axis(axis: int, ndim: int) -> int:
    axis = int(axis)
    if axis < 0:
        axis += ndim
    if not 0 <= axis < ndim:
        raise ValueError(f"axis {axis} is outside a {ndim}-dimensional array")
    return axis


def score_identity_temporal_crossfitted_groups(
    groups: (
        Mapping[str, tuple[np.ndarray, np.ndarray]]
        | Sequence[tuple[str, np.ndarray, np.ndarray]]
    ),
    *,
    identity_axis: int,
    time_axis: int,
    model_unavailable_masks: Mapping[str, np.ndarray | None] | None = None,
    heldout_unavailable_masks: Mapping[str, np.ndarray | None] | None = None,
    gain_tolerance: float = 0.0,
) -> GroupedTransferabilityResult:
    """Score independent temporal folds when every fold has its own training model.

    This is the appropriate wrapper for deterministic leave-one-site-fold-out
    designs such as the frozen Snapshot Serengeti lane. It preserves the exact
    per-fold model/held-out pairing rather than replacing cross-fitting with one
    common model.
    """

    items = tuple(groups.items()) if isinstance(groups, Mapping) else tuple(groups)
    if not items:
        raise ValueError("groups must contain at least one cross-fitted temporal group")

    first_pair = items[0][1] if isinstance(groups, Mapping) else (items[0][1], items[0][2])
    model_support = np.asarray(first_pair[0])
    identity = _canonical_axis(identity_axis, model_support.ndim)
    time = _canonical_axis(time_axis, model_support.ndim)
    if identity == time:
        raise ValueError("identity_axis and time_axis must be distinct")

    return score_crossfitted_independent_groups(
        groups,
        base_axes=(identity,),
        added_axes=(time,),
        model_unavailable_masks=model_unavailable_masks,
        heldout_unavailable_masks=heldout_unavailable_masks,
        gain_tolerance=gain_tolerance,
    )
