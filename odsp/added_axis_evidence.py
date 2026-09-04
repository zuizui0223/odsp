"""Axis-agnostic N2 evidence evaluation over declared base and added axes.

The empirical adapters for height, depth and time remain useful because they
encode observation semantics and prospective gates.  This module exposes the
shared inferential core without requiring any axis to be named x, y, z or t.
"""
from __future__ import annotations

from dataclasses import asdict, dataclass
from typing import Mapping, Sequence

import numpy as np

from .grouped_transferability import GroupedTransferabilityResult, score_independent_groups
from .niche_geometry import conditional_information, effective_conditional_states
from .transferability import base_added_mutual_information


@dataclass(frozen=True)
class AddedAxisEvidenceProfile:
    """Descriptive thickness and fitted organization for arbitrary declared axes."""

    shape: tuple[int, ...]
    base_axes: tuple[int, ...]
    added_axes: tuple[int, ...]
    conditional_information_nats: float
    effective_added_states: float
    organization_information_nats: float

    def as_dict(self) -> dict[str, object]:
        return asdict(self)


@dataclass(frozen=True)
class AddedAxisEvidenceResult:
    """Generic descriptive profile plus optional independent transferability."""

    profile: AddedAxisEvidenceProfile
    transferability: GroupedTransferabilityResult | None

    def as_dict(self) -> dict[str, object]:
        return {
            "profile": self.profile.as_dict(),
            "transferability": (
                None if self.transferability is None else self.transferability.as_dict()
            ),
        }


def _canonical_axis(axis: int, ndim: int) -> int:
    axis = int(axis)
    if axis < 0:
        axis += ndim
    if not 0 <= axis < ndim:
        raise ValueError(f"axis {axis} is outside a {ndim}-dimensional array")
    return axis


def _canonical_axes(axes: Sequence[int], ndim: int, *, name: str) -> tuple[int, ...]:
    result = tuple(_canonical_axis(axis, ndim) for axis in axes)
    if not result:
        raise ValueError(f"{name} must contain at least one axis")
    if len(set(result)) != len(result):
        raise ValueError(f"{name} must contain unique axes")
    return result


def evaluate_added_axis_evidence(
    model_support: np.ndarray,
    *,
    base_axes: Sequence[int],
    added_axes: Sequence[int],
    heldout_supports: (
        Mapping[str, np.ndarray]
        | Sequence[tuple[str, np.ndarray]]
        | None
    ) = None,
    model_unavailable_mask: np.ndarray | None = None,
    heldout_unavailable_masks: Mapping[str, np.ndarray | None] | None = None,
    gain_tolerance: float = 1e-12,
) -> AddedAxisEvidenceResult:
    """Evaluate the common N2 evidence hierarchy for arbitrary finite axes.

    Parameters
    ----------
    model_support
        Non-negative support/count/weight tensor.  The generic core normalizes
        mass internally; ecological interpretation of the support remains the
        caller's responsibility.
    base_axes
        One or more axes retained as the conditioning/reference state ``B``.
    added_axes
        One or more axes whose information beyond ``B`` is being quantified as
        ``A``.  These axes may represent height, depth, time, behaviour,
        microhabitat, life stage or any other declared discrete state.
    heldout_supports
        Optional prospectively independent groups.  If supplied, every group is
        scored separately under ``P_model(A|B)`` versus ``P_model(A)`` and the
        conservative grouped sign-pattern classification is returned.

    This function deliberately does not infer axis semantics, choose bins,
    smooth zero states, define independence, or decide whether the observation
    architecture is biologically adequate.  Those choices must be fixed by the
    empirical design before outcome access.
    """

    field = np.asarray(model_support, dtype=float)
    if field.ndim < 2 or field.size == 0:
        raise ValueError("model_support must be a non-empty array with at least two axes")
    base = _canonical_axes(base_axes, field.ndim, name="base_axes")
    added = _canonical_axes(added_axes, field.ndim, name="added_axes")
    if set(base) & set(added):
        raise ValueError("base_axes and added_axes must be disjoint")

    h = conditional_information(
        field,
        base_axes=base,
        added_axes=added,
        unavailable_mask=model_unavailable_mask,
    )
    effective = effective_conditional_states(
        field,
        base_axes=base,
        added_axes=added,
        unavailable_mask=model_unavailable_mask,
    )
    organization = base_added_mutual_information(
        field,
        base_axes=base,
        added_axes=added,
        unavailable_mask=model_unavailable_mask,
    )
    profile = AddedAxisEvidenceProfile(
        shape=tuple(int(value) for value in field.shape),
        base_axes=base,
        added_axes=added,
        conditional_information_nats=float(h),
        effective_added_states=float(effective),
        organization_information_nats=float(organization),
    )

    grouped = None
    if heldout_supports is not None:
        grouped = score_independent_groups(
            field,
            heldout_supports,
            base_axes=base,
            added_axes=added,
            model_unavailable_mask=model_unavailable_mask,
            heldout_unavailable_masks=heldout_unavailable_masks,
            gain_tolerance=gain_tolerance,
        )
    return AddedAxisEvidenceResult(profile=profile, transferability=grouped)
