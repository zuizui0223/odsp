"""Model-agnostic niche-thickness and projection-information metrics.

Chapter 2 treats a horizontal x-y map as a projection of a potentially richer
ecological state distribution. This module quantifies how much information is
carried by added axes such as vertical stratum/depth (z), time (t), or declared
structural microhabitat once horizontal location is already known.

The functions operate on non-negative support arrays. They do not assume that
raw opportunistic occurrence counts are unbiased biological use probabilities;
callers remain responsible for effort/detectability semantics.
"""
from __future__ import annotations

from dataclasses import asdict, dataclass
import math
from typing import Sequence

import numpy as np


@dataclass(frozen=True)
class AxisThicknessMap:
    """Per-horizontal-cell information retained by one or more added axes."""

    horizontal_axes: tuple[int, int]
    added_axes: tuple[int, ...]
    horizontal_mass: np.ndarray
    information_nats: np.ndarray
    effective_states: np.ndarray


@dataclass(frozen=True)
class NicheThicknessProfile:
    """Information and effective-state thickness beyond the x-y projection."""

    shape: tuple[int, ...]
    horizontal_axes: tuple[int, int]
    vertical_axis: int | None
    temporal_axis: int | None
    total_mass: float
    horizontal_entropy_nats: float
    full_entropy_nats: float
    added_axis_information_nats: float
    effective_added_states: float
    vertical_information_nats: float | None
    effective_vertical_states: float | None
    temporal_information_nats: float | None
    effective_temporal_states: float | None
    joint_vertical_temporal_information_nats: float | None
    effective_joint_vertical_temporal_states: float | None
    vertical_temporal_conditional_mutual_information_nats: float | None

    def as_dict(self) -> dict[str, object]:
        return asdict(self)


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


def _validate_support(
    support: np.ndarray,
    unavailable_mask: np.ndarray | None,
) -> tuple[np.ndarray, np.ndarray, float]:
    field = np.asarray(support, dtype=float)
    if field.ndim < 2 or field.size == 0:
        raise ValueError("support must be a non-empty array with at least two axes")
    mask = (
        np.zeros(field.shape, dtype=bool)
        if unavailable_mask is None
        else np.asarray(unavailable_mask, dtype=bool)
    )
    if mask.shape != field.shape:
        raise ValueError("unavailable_mask must match support shape")
    available = ~mask
    if not np.any(available):
        raise ValueError("support contains no available state")
    values = field[available]
    if not np.isfinite(values).all():
        raise ValueError("support must be finite on available states")
    if np.any(values < 0):
        raise ValueError("support must be non-negative")
    total = float(values.sum())
    if not total > 0:
        raise ValueError("support must have positive total mass")
    probability = np.zeros(field.shape, dtype=float)
    probability[available] = values / total
    return probability, available, total


def shannon_entropy(probability: np.ndarray) -> float:
    """Return Shannon entropy in nats for an already normalized distribution."""

    p = np.asarray(probability, dtype=float)
    if np.any(~np.isfinite(p)) or np.any(p < 0):
        raise ValueError("probability must be finite and non-negative")
    total = float(p.sum())
    if not np.isclose(total, 1.0, rtol=1e-9, atol=1e-12):
        raise ValueError("probability must sum to one")
    positive = p[p > 0]
    return float(-np.sum(positive * np.log(positive)))


def marginal_probability(
    probability: np.ndarray,
    keep_axes: Sequence[int],
) -> np.ndarray:
    """Marginalize a probability distribution while retaining selected axes.

    The surviving dimensions remain in their original array order. Callers that
    need a particular order should explicitly transpose the result.
    """

    p = np.asarray(probability, dtype=float)
    keep = _canonical_axes(keep_axes, p.ndim)
    dropped = tuple(axis for axis in range(p.ndim) if axis not in keep)
    return p.sum(axis=dropped) if dropped else p.copy()


def conditional_information(
    support: np.ndarray,
    *,
    base_axes: Sequence[int],
    added_axes: Sequence[int],
    unavailable_mask: np.ndarray | None = None,
) -> float:
    """Return H(added axes | base axes) in nats.

    This is H(base, added) - H(base), computed from the normalized support
    distribution. Axes not listed in either set are marginalized out first.
    """

    probability, _, _ = _validate_support(support, unavailable_mask)
    base = _canonical_axes(base_axes, probability.ndim)
    added = _canonical_axes(added_axes, probability.ndim)
    if set(base) & set(added):
        raise ValueError("base_axes and added_axes must be disjoint")
    if not added:
        return 0.0
    joint = marginal_probability(probability, (*base, *added))
    base_probability = marginal_probability(probability, base)
    value = shannon_entropy(joint) - shannon_entropy(base_probability)
    if value < 0 and value > -1e-12:
        value = 0.0
    return float(max(0.0, value))


def effective_conditional_states(
    support: np.ndarray,
    *,
    base_axes: Sequence[int],
    added_axes: Sequence[int],
    unavailable_mask: np.ndarray | None = None,
) -> float:
    """Return exp(H(added|base)), the effective number of added states."""

    return float(
        math.exp(
            conditional_information(
                support,
                base_axes=base_axes,
                added_axes=added_axes,
                unavailable_mask=unavailable_mask,
            )
        )
    )


def axis_thickness_map(
    support: np.ndarray,
    *,
    horizontal_axes: Sequence[int] = (0, 1),
    added_axes: Sequence[int],
    unavailable_mask: np.ndarray | None = None,
) -> AxisThicknessMap:
    """Return H(added|x,y) and exp(H) separately for every supported x-y cell.

    Horizontal cells with zero support mass are returned as NaN rather than being
    assigned an artificial thickness of one. The horizontal-mass array is always
    ordered as ``horizontal_axes``; added-state order has no effect on entropy.

    Supplying an equal-weight availability tensor rather than a species support
    tensor yields a descriptive *structural state-space capacity* map. Supplying a
    species support tensor yields a descriptive species niche-thickness map.
    Neither interpretation is an occupancy probability by itself.
    """

    probability, _, _ = _validate_support(support, unavailable_mask)
    horizontal = _canonical_axes(horizontal_axes, probability.ndim)
    if len(horizontal) != 2:
        raise ValueError("horizontal_axes must contain exactly two axes")
    added = _canonical_axes(added_axes, probability.ndim)
    if not added:
        raise ValueError("added_axes must contain at least one axis")
    if set(horizontal) & set(added):
        raise ValueError("horizontal_axes and added_axes must be disjoint")

    keep = (*horizontal, *added)
    dropped = tuple(axis for axis in range(probability.ndim) if axis not in keep)
    joint = probability.sum(axis=dropped) if dropped else probability.copy()

    # After marginalization, NumPy retains surviving axes in their original order.
    surviving_original_order = tuple(sorted(keep))
    desired_order = keep
    permutation = tuple(surviving_original_order.index(axis) for axis in desired_order)
    if permutation != tuple(range(len(keep))):
        joint = np.transpose(joint, permutation)

    horizontal_shape = joint.shape[:2]
    added_shape = joint.shape[2:]
    flat = joint.reshape((*horizontal_shape, int(np.prod(added_shape))))
    mass = flat.sum(axis=-1)
    information = np.full(horizontal_shape, np.nan, dtype=float)
    supported = mass > 0
    if np.any(supported):
        conditional = np.zeros_like(flat)
        conditional[supported] = flat[supported] / mass[supported, None]
        positive = conditional > 0
        terms = np.zeros_like(conditional)
        terms[positive] = -conditional[positive] * np.log(conditional[positive])
        information[supported] = terms.sum(axis=-1)[supported]
    effective = np.full(horizontal_shape, np.nan, dtype=float)
    effective[supported] = np.exp(information[supported])
    return AxisThicknessMap(
        horizontal_axes=(int(horizontal[0]), int(horizontal[1])),
        added_axes=tuple(int(axis) for axis in added),
        horizontal_mass=mass,
        information_nats=information,
        effective_states=effective,
    )


def niche_thickness_profile(
    support: np.ndarray,
    *,
    horizontal_axes: Sequence[int] = (0, 1),
    vertical_axis: int | None = None,
    temporal_axis: int | None = None,
    unavailable_mask: np.ndarray | None = None,
) -> NicheThicknessProfile:
    """Summarize niche thickness beyond a horizontal x-y projection.

    ``support`` may have any number of axes. The two horizontal axes are always
    retained as the planar reference. Optional vertical and temporal axes are
    reported separately and jointly. Any other axes contribute to the overall
    ``added_axis_information_nats`` after x-y is known.

    ``vertical_temporal_conditional_mutual_information_nats`` is

        I(Z;T|X,Y) = H(Z|X,Y) + H(T|X,Y) - H(Z,T|X,Y)

    and measures conditional dependence/redundancy between z and t after
    horizontal location is known. Zero means conditional independence in this
    support distribution; a positive value means the z and t dimensions are not
    independent. It is descriptive and is not a causal interaction metric.
    """

    probability, _, total = _validate_support(support, unavailable_mask)
    horizontal = _canonical_axes(horizontal_axes, probability.ndim)
    if len(horizontal) != 2:
        raise ValueError("horizontal_axes must contain exactly two axes")

    vertical = (
        None if vertical_axis is None else _canonical_axis(vertical_axis, probability.ndim)
    )
    temporal = (
        None if temporal_axis is None else _canonical_axis(temporal_axis, probability.ndim)
    )
    named_axes = [*horizontal]
    if vertical is not None:
        named_axes.append(vertical)
    if temporal is not None:
        named_axes.append(temporal)
    if len(set(named_axes)) != len(named_axes):
        raise ValueError("horizontal, vertical and temporal axes must be distinct")

    horizontal_probability = marginal_probability(probability, horizontal)
    horizontal_entropy = shannon_entropy(horizontal_probability)
    full_entropy = shannon_entropy(probability)
    added_information = max(0.0, full_entropy - horizontal_entropy)

    vertical_information = None
    effective_vertical = None
    if vertical is not None:
        vertical_information = conditional_information(
            support,
            base_axes=horizontal,
            added_axes=(vertical,),
            unavailable_mask=unavailable_mask,
        )
        effective_vertical = float(math.exp(vertical_information))

    temporal_information = None
    effective_temporal = None
    if temporal is not None:
        temporal_information = conditional_information(
            support,
            base_axes=horizontal,
            added_axes=(temporal,),
            unavailable_mask=unavailable_mask,
        )
        effective_temporal = float(math.exp(temporal_information))

    joint_information = None
    effective_joint = None
    conditional_mutual_information = None
    if vertical is not None and temporal is not None:
        joint_information = conditional_information(
            support,
            base_axes=horizontal,
            added_axes=(vertical, temporal),
            unavailable_mask=unavailable_mask,
        )
        effective_joint = float(math.exp(joint_information))
        conditional_mutual_information = max(
            0.0,
            float(vertical_information + temporal_information - joint_information),
        )

    return NicheThicknessProfile(
        shape=tuple(int(value) for value in probability.shape),
        horizontal_axes=(int(horizontal[0]), int(horizontal[1])),
        vertical_axis=vertical,
        temporal_axis=temporal,
        total_mass=total,
        horizontal_entropy_nats=horizontal_entropy,
        full_entropy_nats=full_entropy,
        added_axis_information_nats=added_information,
        effective_added_states=float(math.exp(added_information)),
        vertical_information_nats=vertical_information,
        effective_vertical_states=effective_vertical,
        temporal_information_nats=temporal_information,
        effective_temporal_states=effective_temporal,
        joint_vertical_temporal_information_nats=joint_information,
        effective_joint_vertical_temporal_states=effective_joint,
        vertical_temporal_conditional_mutual_information_nats=(
            conditional_mutual_information
        ),
    )
