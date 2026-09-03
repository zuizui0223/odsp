"""Temporal niche thickness, partitioning and held-out decision logic.

ODSP treats time as an added ecological state axis rather than as metadata that
is automatically biologically meaningful. This module separates three claims:

* temporal thickness: ``H(T | B)`` — how many time states remain after context B;
* temporal partitioning: ``I(C; T | B)`` — whether identity C and time are
  associated after the declared context is known;
* transferability: whether an identity-conditioned temporal distribution learned
  from one set of independent sampling units predicts held-out units better than
  the identity-blind temporal marginal.

The functions are model-agnostic and do not manufacture effort correction,
detection probabilities, local solar time or missing timestamps. Those choices
must be declared by the empirical caller before outcomes are opened.
"""
from __future__ import annotations

from dataclasses import asdict, dataclass
import math
from typing import Mapping, Sequence

import numpy as np

from .grouped_transferability import (
    GroupedTransferabilityResult,
    score_independent_groups,
)
from .niche_geometry import conditional_information
from .transferability import (
    ConditionalTransferabilityScore,
    classify_independent_gains,
    score_conditional_transferability,
)


@dataclass(frozen=True)
class TemporalPartitionProfile:
    """Information decomposition for an identity × time state distribution."""

    context_axes: tuple[int, ...]
    identity_axis: int
    time_axis: int
    temporal_information_given_context_nats: float
    effective_temporal_states_given_context: float
    identity_information_given_context_nats: float
    joint_identity_time_information_given_context_nats: float
    identity_time_partition_information_nats: float

    def as_dict(self) -> dict[str, object]:
        return asdict(self)


@dataclass(frozen=True)
class TemporalPartitionDecision:
    """Frozen decision from a conditional-information null and held-out gains.

    ``gain_tolerance`` is stored explicitly so the transfer category can be
    reproduced later. ``heldout_group_ids`` is populated by the grouped temporal
    workflow and remains empty for legacy/manual gain vectors.
    """

    observed_partition_information_nats: float
    null_draw_count: int
    permutation_p_value: float
    alpha: float
    heldout_gains: tuple[float, ...]
    transfer_category: str
    terminal_category: str
    gain_tolerance: float = 0.0
    heldout_group_ids: tuple[str, ...] = ()

    def __post_init__(self) -> None:
        if not math.isfinite(self.observed_partition_information_nats) or self.observed_partition_information_nats < 0:
            raise ValueError("observed_partition_information_nats must be finite and non-negative")
        if not isinstance(self.null_draw_count, int) or isinstance(self.null_draw_count, bool) or self.null_draw_count < 1:
            raise ValueError("null_draw_count must be a positive integer")
        if not math.isfinite(self.permutation_p_value) or not 0.0 <= self.permutation_p_value <= 1.0:
            raise ValueError("permutation_p_value must lie between zero and one")
        if not 0.0 < self.alpha < 1.0:
            raise ValueError("alpha must lie strictly between zero and one")
        if not math.isfinite(self.gain_tolerance) or self.gain_tolerance < 0:
            raise ValueError("gain_tolerance must be finite and non-negative")

        gains = tuple(float(value) for value in self.heldout_gains)
        expected_transfer = classify_independent_gains(gains, tolerance=self.gain_tolerance)
        if self.transfer_category != expected_transfer:
            raise ValueError("transfer_category is inconsistent with heldout_gains and gain_tolerance")

        if self.permutation_p_value > self.alpha:
            expected_terminal = "temporal_partition_not_detected"
        elif expected_transfer == "generalizing":
            expected_terminal = "temporal_partition_generalizing"
        elif expected_transfer == "non_generalizing":
            expected_terminal = "temporal_partition_present_not_generalizing"
        else:
            expected_terminal = "temporal_partition_present_mixed_transfer"
        if self.terminal_category != expected_terminal:
            raise ValueError("terminal_category is inconsistent with the frozen temporal decision fields")

        if self.heldout_group_ids:
            if len(self.heldout_group_ids) != len(gains):
                raise ValueError("heldout_group_ids must align one-to-one with heldout_gains")
            if len(set(self.heldout_group_ids)) != len(self.heldout_group_ids):
                raise ValueError("heldout_group_ids must be unique")
            if any(not isinstance(value, str) or not value.strip() or value != value.strip() for value in self.heldout_group_ids):
                raise ValueError("heldout_group_ids must be canonical non-empty strings")

    def as_dict(self) -> dict[str, object]:
        payload = asdict(self)
        payload["heldout_gains"] = list(self.heldout_gains)
        payload["heldout_group_ids"] = list(self.heldout_group_ids)
        return payload


def _canonical_axis(axis: int, ndim: int) -> int:
    axis = int(axis)
    if axis < 0:
        axis += ndim
    if not 0 <= axis < ndim:
        raise ValueError(f"axis {axis} is outside a {ndim}-dimensional array")
    return axis


def _canonical_axes(axes: Sequence[int], ndim: int) -> tuple[int, ...]:
    result = tuple(_canonical_axis(axis, ndim) for axis in axes)
    if len(set(result)) != len(result):
        raise ValueError("axes must be unique")
    return result


def temporal_partition_profile(
    support: np.ndarray,
    *,
    context_axes: Sequence[int],
    identity_axis: int,
    time_axis: int,
    unavailable_mask: np.ndarray | None = None,
) -> TemporalPartitionProfile:
    """Return ``H(T|B)`` and ``I(C;T|B)`` for declared context B."""

    field = np.asarray(support)
    if field.ndim < 2:
        raise ValueError("support must have at least two axes")
    context = _canonical_axes(context_axes, field.ndim)
    identity = _canonical_axis(identity_axis, field.ndim)
    time = _canonical_axis(time_axis, field.ndim)
    named = (*context, identity, time)
    if len(set(named)) != len(named):
        raise ValueError("context, identity and time axes must be distinct")

    temporal = conditional_information(
        support,
        base_axes=context,
        added_axes=(time,),
        unavailable_mask=unavailable_mask,
    )
    identity_information = conditional_information(
        support,
        base_axes=context,
        added_axes=(identity,),
        unavailable_mask=unavailable_mask,
    )
    joint = conditional_information(
        support,
        base_axes=context,
        added_axes=(identity, time),
        unavailable_mask=unavailable_mask,
    )
    partition = float(identity_information + temporal - joint)
    if partition < 0 and partition > -1e-12:
        partition = 0.0
    partition = float(max(0.0, partition))

    return TemporalPartitionProfile(
        context_axes=tuple(int(axis) for axis in context),
        identity_axis=int(identity),
        time_axis=int(time),
        temporal_information_given_context_nats=float(temporal),
        effective_temporal_states_given_context=float(math.exp(temporal)),
        identity_information_given_context_nats=float(identity_information),
        joint_identity_time_information_given_context_nats=float(joint),
        identity_time_partition_information_nats=partition,
    )


def score_identity_temporal_transferability(
    model_support: np.ndarray,
    heldout_support: np.ndarray,
    *,
    identity_axis: int,
    time_axis: int,
    model_unavailable_mask: np.ndarray | None = None,
    heldout_unavailable_mask: np.ndarray | None = None,
    gain_tolerance: float = 1e-12,
) -> ConditionalTransferabilityScore:
    """Test held-out ``P_model(T|C)`` against the temporal marginal ``P_model(T)``."""

    field = np.asarray(model_support)
    identity = _canonical_axis(identity_axis, field.ndim)
    time = _canonical_axis(time_axis, field.ndim)
    if identity == time:
        raise ValueError("identity_axis and time_axis must be distinct")
    return score_conditional_transferability(
        model_support,
        heldout_support,
        base_axes=(identity,),
        added_axes=(time,),
        model_unavailable_mask=model_unavailable_mask,
        heldout_unavailable_mask=heldout_unavailable_mask,
        gain_tolerance=gain_tolerance,
    )


def score_identity_temporal_groups(
    model_support: np.ndarray,
    heldout_supports: Mapping[str, np.ndarray] | Sequence[tuple[str, np.ndarray]],
    *,
    identity_axis: int,
    time_axis: int,
    model_unavailable_mask: np.ndarray | None = None,
    heldout_unavailable_masks: Mapping[str, np.ndarray | None] | None = None,
    gain_tolerance: float = 0.0,
) -> GroupedTransferabilityResult:
    """Score prospectively independent temporal answer-check groups separately."""

    field = np.asarray(model_support)
    identity = _canonical_axis(identity_axis, field.ndim)
    time = _canonical_axis(time_axis, field.ndim)
    if identity == time:
        raise ValueError("identity_axis and time_axis must be distinct")
    return score_independent_groups(
        model_support,
        heldout_supports,
        base_axes=(identity,),
        added_axes=(time,),
        model_unavailable_mask=model_unavailable_mask,
        heldout_unavailable_masks=heldout_unavailable_masks,
        gain_tolerance=gain_tolerance,
    )


def classify_temporal_partition_result(
    observed_partition_information_nats: float,
    null_partition_information_nats: Sequence[float],
    heldout_gains: Sequence[float],
    *,
    alpha: float = 0.05,
    gain_tolerance: float = 0.0,
    heldout_group_ids: Sequence[str] | None = None,
) -> TemporalPartitionDecision:
    """Classify a frozen temporal-partition endpoint without rescue logic."""

    observed = float(observed_partition_information_nats)
    if not math.isfinite(observed) or observed < 0:
        raise ValueError("observed_partition_information_nats must be finite and non-negative")
    null = tuple(float(value) for value in null_partition_information_nats)
    if not null or any((not math.isfinite(value) or value < 0) for value in null):
        raise ValueError("null_partition_information_nats must contain finite non-negative values")
    if not (0 < alpha < 1):
        raise ValueError("alpha must lie strictly between zero and one")
    if not math.isfinite(gain_tolerance) or gain_tolerance < 0:
        raise ValueError("gain_tolerance must be finite and non-negative")

    gains = tuple(float(value) for value in heldout_gains)
    transfer = classify_independent_gains(gains, tolerance=gain_tolerance)
    exceedances = sum(value >= observed for value in null)
    p_value = (1.0 + exceedances) / (1.0 + len(null))

    if p_value > alpha:
        terminal = "temporal_partition_not_detected"
    elif transfer == "generalizing":
        terminal = "temporal_partition_generalizing"
    elif transfer == "non_generalizing":
        terminal = "temporal_partition_present_not_generalizing"
    else:
        terminal = "temporal_partition_present_mixed_transfer"

    group_ids = () if heldout_group_ids is None else tuple(str(value) for value in heldout_group_ids)
    return TemporalPartitionDecision(
        observed_partition_information_nats=observed,
        null_draw_count=len(null),
        permutation_p_value=float(p_value),
        alpha=float(alpha),
        heldout_gains=gains,
        transfer_category=transfer,
        terminal_category=terminal,
        gain_tolerance=float(gain_tolerance),
        heldout_group_ids=group_ids,
    )


def classify_grouped_temporal_partition_result(
    observed_partition_information_nats: float,
    null_partition_information_nats: Sequence[float],
    grouped_transferability: GroupedTransferabilityResult,
    *,
    alpha: float = 0.05,
) -> TemporalPartitionDecision:
    """Classify temporal partitioning directly from a self-validating grouped result."""

    if len(grouped_transferability.base_axes) != 1 or len(grouped_transferability.added_axes) != 1:
        raise ValueError("temporal grouped transferability must have one identity base axis and one time axis")
    return classify_temporal_partition_result(
        observed_partition_information_nats,
        null_partition_information_nats,
        grouped_transferability.gains,
        alpha=alpha,
        gain_tolerance=grouped_transferability.gain_tolerance,
        heldout_group_ids=[group.group_id for group in grouped_transferability.groups],
    )
