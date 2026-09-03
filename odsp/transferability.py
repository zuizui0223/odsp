"""Model-agnostic organization and held-out transferability for added niche axes.

Thickness magnitude and thickness organization are different Chapter-2 questions.
For a base state B (for example x-y) and one or more added states A (for example
z, t, or a declared structural state):

* ``H(A|B)`` describes how many added states remain after the base state is known;
* ``I(A;B)`` describes in-sample organization of the added states across the base;
* held-out log-score gain tests whether ``P_model(A|B)`` predicts independent
  support better than the lower-information marginal ``P_model(A)``.

The functions here operate on non-negative support/count arrays and deliberately
do not add smoothing. If a prospective analysis needs smoothing, it must be
specified before held-out outcomes are opened and applied before calling this
module. This keeps zero-probability handling scientifically explicit.
"""
from __future__ import annotations

from dataclasses import asdict, dataclass
import math
from typing import Sequence

import numpy as np


@dataclass(frozen=True)
class ConditionalTransferabilityScore:
    """Held-out comparison of conditional versus marginal added-state support."""

    base_axes: tuple[int, ...]
    added_axes: tuple[int, ...]
    model_total_mass: float
    heldout_total_mass: float
    scored_cell_count: int
    mean_conditional_log_score: float
    mean_marginal_log_score: float
    mean_log_score_gain: float
    in_sample_organization_information_nats: float
    gain_category: str

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


def _validate_field(
    field: np.ndarray,
    *,
    name: str,
    unavailable_mask: np.ndarray | None,
) -> tuple[np.ndarray, np.ndarray, float]:
    values = np.asarray(field, dtype=float)
    if values.ndim < 2 or values.size == 0:
        raise ValueError(f"{name} must be a non-empty array with at least two axes")
    mask = (
        np.zeros(values.shape, dtype=bool)
        if unavailable_mask is None
        else np.asarray(unavailable_mask, dtype=bool)
    )
    if mask.shape != values.shape:
        raise ValueError(f"{name}_unavailable_mask must match {name} shape")
    available = ~mask
    if not np.any(available):
        raise ValueError(f"{name} contains no available state")
    observed = values[available]
    if not np.isfinite(observed).all():
        raise ValueError(f"{name} must be finite on available states")
    if np.any(observed < 0):
        raise ValueError(f"{name} must be non-negative")
    total = float(observed.sum())
    if not total > 0:
        raise ValueError(f"{name} must have positive total mass")
    cleaned = np.zeros(values.shape, dtype=float)
    cleaned[available] = observed
    return cleaned, available, total


def _ordered_marginal(field: np.ndarray, keep_axes: Sequence[int]) -> np.ndarray:
    keep = _canonical_axes(keep_axes, field.ndim)
    dropped = tuple(axis for axis in range(field.ndim) if axis not in keep)
    result = field.sum(axis=dropped) if dropped else field.copy()

    # numpy.sum preserves surviving axes in original order. Reorder them to the
    # explicit caller order so base axes always precede added axes downstream.
    surviving = tuple(axis for axis in range(field.ndim) if axis in keep)
    permutation = tuple(surviving.index(axis) for axis in keep)
    if permutation != tuple(range(len(keep))):
        result = np.transpose(result, permutation)
    return result


def _validated_axis_partition(
    *,
    ndim: int,
    base_axes: Sequence[int],
    added_axes: Sequence[int],
) -> tuple[tuple[int, ...], tuple[int, ...]]:
    base = _canonical_axes(base_axes, ndim)
    added = _canonical_axes(added_axes, ndim)
    if not base or not added:
        raise ValueError("base_axes and added_axes must each contain at least one axis")
    if set(base) & set(added):
        raise ValueError("base_axes and added_axes must be disjoint")
    return base, added


def base_added_mutual_information(
    support: np.ndarray,
    *,
    base_axes: Sequence[int],
    added_axes: Sequence[int],
    unavailable_mask: np.ndarray | None = None,
) -> float:
    """Return ``I(added; base)`` in nats for a support distribution.

    This is the expected log-score advantage of ``P(added|base)`` over
    ``P(added)`` when the evaluation distribution is the same as ``support``.
    It therefore measures *in-sample organization*, not held-out transferability.
    A value of zero can coexist with large ``H(added|base)``: a niche may be
    thick while having the same added-state distribution in every base cell.
    """

    field, _, total = _validate_field(
        support,
        name="support",
        unavailable_mask=unavailable_mask,
    )
    base, added = _validated_axis_partition(
        ndim=field.ndim,
        base_axes=base_axes,
        added_axes=added_axes,
    )
    joint = _ordered_marginal(field, (*base, *added)) / total
    base_ndim = len(base)
    added_ndim = len(added)
    base_probability = joint.sum(axis=tuple(range(base_ndim, joint.ndim)))
    added_probability = joint.sum(axis=tuple(range(base_ndim)))
    denominator = (
        base_probability.reshape(base_probability.shape + (1,) * added_ndim)
        * added_probability.reshape((1,) * base_ndim + added_probability.shape)
    )
    positive = joint > 0
    value = float(np.sum(joint[positive] * np.log(joint[positive] / denominator[positive])))
    if value < 0 and value > -1e-12:
        value = 0.0
    return float(max(0.0, value))


def classify_independent_gains(
    gains: Sequence[float],
    *,
    tolerance: float = 0.0,
) -> str:
    """Classify prospectively independent held-out gains.

    ``generalizing`` requires every gain to be strictly greater than the supplied
    tolerance. ``non_generalizing`` means every gain is at or below tolerance;
    otherwise the result is ``mixed``. This mirrors the conservative logic used
    by the frozen N2 bat endpoint without importing any bat-specific categories.
    """

    if tolerance < 0 or not math.isfinite(tolerance):
        raise ValueError("tolerance must be finite and non-negative")
    values = tuple(float(value) for value in gains)
    if not values:
        raise ValueError("gains must contain at least one value")
    if any(math.isnan(value) for value in values):
        raise ValueError("gains must not contain NaN")
    if all(value > tolerance for value in values):
        return "generalizing"
    if all(value <= tolerance for value in values):
        return "non_generalizing"
    return "mixed"


def score_conditional_transferability(
    model_support: np.ndarray,
    heldout_support: np.ndarray,
    *,
    base_axes: Sequence[int],
    added_axes: Sequence[int],
    model_unavailable_mask: np.ndarray | None = None,
    heldout_unavailable_mask: np.ndarray | None = None,
    gain_tolerance: float = 1e-12,
) -> ConditionalTransferabilityScore:
    """Score held-out added-state support under conditional and marginal models.

    The returned gain is

    ``E_heldout[log P_model(A|B) - log P_model(A)]``.

    Positive gain means the model's base-conditioned organization predicts the
    held-out support better than the model's marginal added-state distribution.
    Negative gain means conditioning on the base made prediction worse. A gain
    near zero means the detailed organization adds no held-out predictive value.

    No smoothing is performed. A held-out state that is globally absent from the
    model makes the comparison undefined and fails closed. A state that exists in
    the model marginal but has zero conditional probability in its held-out base
    cell yields ``-inf`` gain, which is a valid predictive failure rather than an
    unavailable result.
    """

    if gain_tolerance < 0 or not math.isfinite(gain_tolerance):
        raise ValueError("gain_tolerance must be finite and non-negative")

    model, model_available, model_total = _validate_field(
        model_support,
        name="model_support",
        unavailable_mask=model_unavailable_mask,
    )
    heldout, _, heldout_total = _validate_field(
        heldout_support,
        name="heldout_support",
        unavailable_mask=heldout_unavailable_mask,
    )
    if model.shape != heldout.shape:
        raise ValueError("model_support and heldout_support must have the same shape")
    if np.any((heldout > 0) & ~model_available):
        raise ValueError("heldout_support has mass in a model-unavailable state")

    base, added = _validated_axis_partition(
        ndim=model.ndim,
        base_axes=base_axes,
        added_axes=added_axes,
    )
    keep = (*base, *added)
    model_joint = _ordered_marginal(model, keep)
    heldout_joint = _ordered_marginal(heldout, keep)

    base_ndim = len(base)
    added_ndim = len(added)
    added_local_axes = tuple(range(base_ndim, model_joint.ndim))
    base_local_axes = tuple(range(base_ndim))

    model_base_mass = model_joint.sum(axis=added_local_axes)
    heldout_base_mass = heldout_joint.sum(axis=added_local_axes)
    if np.any((heldout_base_mass > 0) & (model_base_mass <= 0)):
        raise ValueError("heldout_support reaches a base state with zero model support")

    base_denominator = model_base_mass.reshape(
        model_base_mass.shape + (1,) * added_ndim
    )
    conditional_probability = np.divide(
        model_joint,
        base_denominator,
        out=np.zeros_like(model_joint, dtype=float),
        where=base_denominator > 0,
    )
    marginal_added_probability = model_joint.sum(axis=base_local_axes) / float(
        model_joint.sum()
    )
    heldout_added_mass = heldout_joint.sum(axis=base_local_axes)
    if np.any((heldout_added_mass > 0) & (marginal_added_probability <= 0)):
        raise ValueError(
            "heldout_support reaches an added state with zero model marginal support"
        )

    marginal_broadcast = np.broadcast_to(
        marginal_added_probability.reshape(
            (1,) * base_ndim + marginal_added_probability.shape
        ),
        model_joint.shape,
    )
    scored = heldout_joint > 0
    weights = heldout_joint[scored] / float(heldout_joint.sum())
    conditional_values = conditional_probability[scored]
    marginal_values = marginal_broadcast[scored]

    mean_marginal = float(np.sum(weights * np.log(marginal_values)))
    if np.any(conditional_values <= 0):
        mean_conditional = float("-inf")
        gain = float("-inf")
    else:
        mean_conditional = float(np.sum(weights * np.log(conditional_values)))
        gain = float(mean_conditional - mean_marginal)

    if gain > gain_tolerance:
        category = "positive"
    elif gain < -gain_tolerance:
        category = "negative"
    else:
        category = "neutral"

    organization = base_added_mutual_information(
        model,
        base_axes=base,
        added_axes=added,
    )
    return ConditionalTransferabilityScore(
        base_axes=tuple(int(axis) for axis in base),
        added_axes=tuple(int(axis) for axis in added),
        model_total_mass=model_total,
        heldout_total_mass=heldout_total,
        scored_cell_count=int(np.count_nonzero(scored)),
        mean_conditional_log_score=mean_conditional,
        mean_marginal_log_score=mean_marginal,
        mean_log_score_gain=gain,
        in_sample_organization_information_nats=organization,
        gain_category=category,
    )
