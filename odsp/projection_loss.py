"""Pairwise niche-overlap inflation caused by lower-dimensional projection.

Two taxa can have nearly identical horizontal x-y maps while occupying different
vertical strata, times, or joint z×t states.  This module measures how much
Schoener overlap changes when those added axes are marginalized.

The metrics are descriptive.  They do not by themselves establish competition,
coexistence, predation, avoidance, or a fundamental-niche difference.
"""
from __future__ import annotations

from dataclasses import asdict, dataclass
from typing import Sequence

import numpy as np

from .niche_geometry import (
    _canonical_axis,
    _canonical_axes,
    _validate_support,
    marginal_probability,
)


@dataclass(frozen=True)
class ProjectionOverlapProfile:
    shape: tuple[int, ...]
    horizontal_axes: tuple[int, int]
    vertical_axis: int | None
    temporal_axis: int | None
    full_overlap: float
    horizontal_overlap: float
    horizontal_vertical_overlap: float | None
    horizontal_temporal_overlap: float | None
    horizontal_vertical_temporal_overlap: float | None
    planar_overlap_inflation: float
    vertical_projection_inflation: float | None
    temporal_projection_inflation: float | None
    joint_only_projection_inflation: float | None

    def as_dict(self) -> dict[str, object]:
        return asdict(self)


def _schoener_probability_overlap(a: np.ndarray, b: np.ndarray) -> float:
    if a.shape != b.shape:
        raise ValueError("probability arrays must have the same shape")
    value = 1.0 - 0.5 * float(np.abs(a - b).sum())
    return float(np.clip(value, 0.0, 1.0))


def schoener_overlap(
    support_a: np.ndarray,
    support_b: np.ndarray,
    *,
    keep_axes: Sequence[int] | None = None,
    unavailable_mask: np.ndarray | None = None,
) -> float:
    """Return Schoener overlap in full or marginal state space."""

    a = np.asarray(support_a, dtype=float)
    b = np.asarray(support_b, dtype=float)
    if a.shape != b.shape:
        raise ValueError("support arrays must have the same shape")
    pa, _, _ = _validate_support(a, unavailable_mask)
    pb, _, _ = _validate_support(b, unavailable_mask)
    if keep_axes is not None:
        axes = _canonical_axes(keep_axes, pa.ndim)
        pa = marginal_probability(pa, axes)
        pb = marginal_probability(pb, axes)
    return _schoener_probability_overlap(pa, pb)


def projection_overlap_profile(
    support_a: np.ndarray,
    support_b: np.ndarray,
    *,
    horizontal_axes: Sequence[int] = (0, 1),
    vertical_axis: int | None = None,
    temporal_axis: int | None = None,
    unavailable_mask: np.ndarray | None = None,
) -> ProjectionOverlapProfile:
    """Measure overlap inflation caused by marginalizing z and/or t.

    Positive inflation means the lower-dimensional representation makes the two
    supports appear more similar than the richer state space does.
    """

    a = np.asarray(support_a, dtype=float)
    b = np.asarray(support_b, dtype=float)
    if a.shape != b.shape:
        raise ValueError("support arrays must have the same shape")
    if a.ndim < 2:
        raise ValueError("support arrays must have at least two axes")

    horizontal = _canonical_axes(horizontal_axes, a.ndim)
    if len(horizontal) != 2:
        raise ValueError("horizontal_axes must contain exactly two axes")
    vertical = None if vertical_axis is None else _canonical_axis(vertical_axis, a.ndim)
    temporal = None if temporal_axis is None else _canonical_axis(temporal_axis, a.ndim)
    named = [*horizontal]
    if vertical is not None:
        named.append(vertical)
    if temporal is not None:
        named.append(temporal)
    if len(set(named)) != len(named):
        raise ValueError("horizontal, vertical and temporal axes must be distinct")

    full = schoener_overlap(a, b, unavailable_mask=unavailable_mask)
    xy = schoener_overlap(
        a,
        b,
        keep_axes=horizontal,
        unavailable_mask=unavailable_mask,
    )

    xyz = None
    if vertical is not None:
        xyz = schoener_overlap(
            a,
            b,
            keep_axes=(*horizontal, vertical),
            unavailable_mask=unavailable_mask,
        )

    xyt = None
    if temporal is not None:
        xyt = schoener_overlap(
            a,
            b,
            keep_axes=(*horizontal, temporal),
            unavailable_mask=unavailable_mask,
        )

    xyzt = None
    joint_only = None
    if vertical is not None and temporal is not None:
        xyzt = schoener_overlap(
            a,
            b,
            keep_axes=(*horizontal, vertical, temporal),
            unavailable_mask=unavailable_mask,
        )
        joint_only = max(0.0, min(float(xyz), float(xyt)) - xyzt)

    return ProjectionOverlapProfile(
        shape=tuple(int(value) for value in a.shape),
        horizontal_axes=(int(horizontal[0]), int(horizontal[1])),
        vertical_axis=vertical,
        temporal_axis=temporal,
        full_overlap=full,
        horizontal_overlap=xy,
        horizontal_vertical_overlap=xyz,
        horizontal_temporal_overlap=xyt,
        horizontal_vertical_temporal_overlap=xyzt,
        planar_overlap_inflation=max(0.0, xy - full),
        vertical_projection_inflation=(
            None if xyz is None else max(0.0, xy - xyz)
        ),
        temporal_projection_inflation=(
            None if xyt is None else max(0.0, xy - xyt)
        ),
        joint_only_projection_inflation=joint_only,
    )
