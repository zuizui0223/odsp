"""State-resolved ecological prediction on top of the ODSP evidence core.

This module moves ODSP beyond measuring projection loss.  It learns or accepts
conditional added-state distributions ``P(A|B)`` and returns predictions that
retain the ecological state axis itself: layer, depth, time bin, behaviour,
phenophase or any other declared finite state.

The native model is intentionally simple and dependency-light: it estimates a
Dirichlet-smoothed conditional distribution from non-negative support counts or
weights.  More complex learners (RF, boosted trees, neural networks, MaxEnt-like
state models, Bayesian models) can feed their own conditional probability fields
into the same scoring functions.
"""
from __future__ import annotations

from dataclasses import asdict, dataclass
import math
from typing import Mapping, Sequence

import numpy as np

from .transferability import classify_independent_gains


@dataclass(frozen=True)
class StatePredictionSummary:
    """Human-readable prediction for one declared base state."""

    base_state: tuple[int, ...]
    added_shape: tuple[int, ...]
    probabilities: tuple[float, ...]
    dominant_added_state: tuple[int, ...]
    dominant_probability: float
    entropy_nats: float
    effective_states: float
    training_mass: float
    seen_in_training: bool

    def as_dict(self) -> dict[str, object]:
        return asdict(self)


@dataclass(frozen=True)
class StatePredictionScore:
    """Held-out predictive performance of a state-resolved probability field."""

    heldout_total_mass: float
    scored_cell_count: int
    mean_log_score: float
    mean_marginal_log_score: float
    mean_log_score_gain: float
    conditional_brier_score: float
    marginal_brier_score: float
    brier_improvement: float
    top1_accuracy: float
    marginal_top1_accuracy: float
    top1_improvement: float
    mean_assigned_probability: float
    marginal_mean_assigned_probability: float
    seen_base_mass_fraction: float

    def as_dict(self) -> dict[str, object]:
        return asdict(self)


@dataclass(frozen=True)
class GroupedStatePredictionScore:
    """Per-group predictive scores plus conservative gain classification."""

    groups: tuple[tuple[str, StatePredictionScore], ...]
    gain_category: str

    @property
    def gains(self) -> tuple[float, ...]:
        return tuple(score.mean_log_score_gain for _, score in self.groups)

    def as_dict(self) -> dict[str, object]:
        return {
            "groups": [
                {"group": name, **score.as_dict()} for name, score in self.groups
            ],
            "gains": list(self.gains),
            "gain_category": self.gain_category,
        }


@dataclass(frozen=True)
class EncodedStateSupport:
    """Discrete support tensor created from event-level base and added states."""

    support: np.ndarray
    base_levels: tuple[tuple[object, ...], ...]
    added_levels: tuple[tuple[object, ...], ...]

    @property
    def base_shape(self) -> tuple[int, ...]:
        return tuple(len(levels) for levels in self.base_levels)

    @property
    def added_shape(self) -> tuple[int, ...]:
        return tuple(len(levels) for levels in self.added_levels)


@dataclass
class StateResolvedModel:
    """Native ODSP predictor for finite ecological state distributions."""

    source_shape: tuple[int, ...]
    base_axes: tuple[int, ...]
    added_axes: tuple[int, ...]
    base_shape: tuple[int, ...]
    added_shape: tuple[int, ...]
    conditional_probability: np.ndarray
    marginal_probability: np.ndarray
    base_training_mass: np.ndarray
    seen_base_mask: np.ndarray
    joint_available_mask: np.ndarray
    alpha: float
    unseen_base_policy: str

    def predict_distribution(self, base_state: Sequence[int]) -> np.ndarray:
        index = _validated_base_index(base_state, self.base_shape)
        if not bool(np.any(self.joint_available_mask[index])):
            raise ValueError("requested base state is structurally unavailable")
        if (
            not bool(self.seen_base_mask[index])
            and self.unseen_base_policy == "error"
        ):
            raise ValueError("requested base state was not seen in training")
        return np.asarray(self.conditional_probability[index], dtype=float).copy()

    def summarize(self, base_state: Sequence[int]) -> StatePredictionSummary:
        index = _validated_base_index(base_state, self.base_shape)
        probability = self.predict_distribution(index)
        flat = probability.reshape(-1)
        positive = flat > 0
        entropy = float(-np.sum(flat[positive] * np.log(flat[positive])))
        dominant_flat = int(np.argmax(flat))
        dominant_state = tuple(
            int(value) for value in np.unravel_index(dominant_flat, self.added_shape)
        )
        return StatePredictionSummary(
            base_state=index,
            added_shape=self.added_shape,
            probabilities=tuple(float(value) for value in flat),
            dominant_added_state=dominant_state,
            dominant_probability=float(flat[dominant_flat]),
            entropy_nats=entropy,
            effective_states=float(math.exp(entropy)),
            training_mass=float(self.base_training_mass[index]),
            seen_in_training=bool(self.seen_base_mask[index]),
        )

    def summaries(self, *, include_unavailable: bool = False) -> tuple[StatePredictionSummary, ...]:
        result: list[StatePredictionSummary] = []
        for index in np.ndindex(self.base_shape):
            if not np.any(self.joint_available_mask[index]):
                if include_unavailable:
                    continue
                continue
            if not self.seen_base_mask[index] and self.unseen_base_policy == "error":
                continue
            result.append(self.summarize(index))
        return tuple(result)

    def score(
        self,
        heldout_support: np.ndarray,
        *,
        heldout_unavailable_mask: np.ndarray | None = None,
    ) -> StatePredictionScore:
        joint = _heldout_to_joint(
            heldout_support,
            source_shape=self.source_shape,
            base_axes=self.base_axes,
            added_axes=self.added_axes,
            heldout_unavailable_mask=heldout_unavailable_mask,
        )
        return _score_joint_probability_field(
            self.conditional_probability,
            joint,
            marginal_probability=self.marginal_probability,
            base_shape=self.base_shape,
            added_shape=self.added_shape,
            seen_base_mask=self.seen_base_mask,
            joint_available_mask=self.joint_available_mask,
        )


@dataclass
class EncodedStateResolvedModel:
    """State-resolved model with label encoders for event-table workflows."""

    encoded_support: EncodedStateSupport
    model: StateResolvedModel

    def predict_distribution(self, base_state: Sequence[object]) -> np.ndarray:
        codes = _encode_known_state(base_state, self.encoded_support.base_levels, "base_state")
        return self.model.predict_distribution(codes)

    def summarize(self, base_state: Sequence[object]) -> dict[str, object]:
        codes = _encode_known_state(base_state, self.encoded_support.base_levels, "base_state")
        summary = self.model.summarize(codes)
        dominant_labels = tuple(
            self.encoded_support.added_levels[axis][code]
            for axis, code in enumerate(summary.dominant_added_state)
        )
        result = summary.as_dict()
        result["base_state_labels"] = tuple(base_state)
        result["dominant_added_state_labels"] = dominant_labels
        return result


def _canonical_axis(axis: int, ndim: int) -> int:
    value = int(axis)
    if value < 0:
        value += ndim
    if not 0 <= value < ndim:
        raise ValueError(f"axis {axis} is outside a {ndim}-dimensional array")
    return value


def _canonical_axes(axes: Sequence[int], ndim: int, *, name: str) -> tuple[int, ...]:
    result = tuple(_canonical_axis(axis, ndim) for axis in axes)
    if not result:
        raise ValueError(f"{name} must contain at least one axis")
    if len(set(result)) != len(result):
        raise ValueError(f"{name} must contain unique axes")
    return result


def _ordered_marginal(field: np.ndarray, keep_axes: Sequence[int]) -> np.ndarray:
    keep = tuple(int(axis) for axis in keep_axes)
    dropped = tuple(axis for axis in range(field.ndim) if axis not in keep)
    result = field.sum(axis=dropped) if dropped else field.copy()
    surviving = tuple(axis for axis in range(field.ndim) if axis in keep)
    permutation = tuple(surviving.index(axis) for axis in keep)
    if permutation != tuple(range(len(keep))):
        result = np.transpose(result, permutation)
    return np.asarray(result)


def _ordered_any(field: np.ndarray, keep_axes: Sequence[int]) -> np.ndarray:
    keep = tuple(int(axis) for axis in keep_axes)
    dropped = tuple(axis for axis in range(field.ndim) if axis not in keep)
    result = np.any(field, axis=dropped) if dropped else field.copy()
    surviving = tuple(axis for axis in range(field.ndim) if axis in keep)
    permutation = tuple(surviving.index(axis) for axis in keep)
    if permutation != tuple(range(len(keep))):
        result = np.transpose(result, permutation)
    return np.asarray(result, dtype=bool)


def _validate_support(
    support: np.ndarray,
    unavailable_mask: np.ndarray | None,
) -> tuple[np.ndarray, np.ndarray]:
    values = np.asarray(support, dtype=float)
    if values.ndim < 2 or values.size == 0:
        raise ValueError("support must be a non-empty array with at least two axes")
    mask = (
        np.zeros(values.shape, dtype=bool)
        if unavailable_mask is None
        else np.asarray(unavailable_mask, dtype=bool)
    )
    if mask.shape != values.shape:
        raise ValueError("unavailable_mask must match support shape")
    available = ~mask
    if not np.any(available):
        raise ValueError("support contains no available states")
    observed = values[available]
    if not np.isfinite(observed).all():
        raise ValueError("support must be finite on available states")
    if np.any(observed < 0):
        raise ValueError("support must be non-negative")
    cleaned = np.zeros(values.shape, dtype=float)
    cleaned[available] = observed
    if not float(cleaned.sum()) > 0:
        raise ValueError("support must have positive total mass")
    return cleaned, available


def _validated_base_index(base_state: Sequence[int], shape: Sequence[int]) -> tuple[int, ...]:
    index = tuple(int(value) for value in base_state)
    if len(index) != len(shape):
        raise ValueError("base_state length does not match number of base axes")
    for axis, (value, size) in enumerate(zip(index, shape)):
        if not 0 <= value < int(size):
            raise ValueError(f"base_state index {value} is out of bounds on axis {axis}")
    return index


def fit_state_resolved_model(
    support: np.ndarray,
    *,
    base_axes: Sequence[int],
    added_axes: Sequence[int],
    alpha: float = 0.5,
    unavailable_mask: np.ndarray | None = None,
    unseen_base_policy: str = "marginal",
) -> StateResolvedModel:
    """Fit a native conditional state predictor ``P(A|B)``.

    ``support`` may be counts, weights or another declared non-negative support.
    Dirichlet smoothing is applied only to structurally available added states.
    For base states with zero training mass, ``unseen_base_policy='marginal'``
    backs off to the fitted marginal added-state distribution; ``'uniform'`` uses
    a uniform distribution over locally available states and ``'error'`` refuses
    prediction for unseen base states.
    """

    if not math.isfinite(alpha) or alpha < 0:
        raise ValueError("alpha must be finite and non-negative")
    if unseen_base_policy not in {"marginal", "uniform", "error"}:
        raise ValueError("unseen_base_policy must be marginal, uniform or error")

    field, available = _validate_support(support, unavailable_mask)
    base = _canonical_axes(base_axes, field.ndim, name="base_axes")
    added = _canonical_axes(added_axes, field.ndim, name="added_axes")
    if set(base) & set(added):
        raise ValueError("base_axes and added_axes must be disjoint")
    keep = (*base, *added)
    joint = _ordered_marginal(field, keep)
    joint_available = _ordered_any(available, keep)

    base_shape = tuple(int(field.shape[axis]) for axis in base)
    added_shape = tuple(int(field.shape[axis]) for axis in added)
    base_count = int(np.prod(base_shape))
    added_count = int(np.prod(added_shape))
    counts2 = joint.reshape(base_count, added_count)
    available2 = joint_available.reshape(base_count, added_count)
    base_mass = counts2.sum(axis=1)
    seen = base_mass > 0

    global_counts = counts2.sum(axis=0)
    global_available = np.any(available2, axis=0)
    global_denominator = float(global_counts.sum() + alpha * np.count_nonzero(global_available))
    if not global_denominator > 0:
        raise ValueError("cannot fit marginal added-state distribution")
    marginal = np.zeros(added_count, dtype=float)
    marginal[global_available] = (
        global_counts[global_available] + alpha
    ) / global_denominator

    conditional = np.zeros((base_count, added_count), dtype=float)
    for base_index in range(base_count):
        local_available = available2[base_index]
        n_available = int(np.count_nonzero(local_available))
        if n_available == 0:
            continue
        mass = float(base_mass[base_index])
        if mass > 0:
            denominator = mass + alpha * n_available
            if denominator <= 0:
                raise ValueError("invalid conditional denominator")
            conditional[base_index, local_available] = (
                counts2[base_index, local_available] + alpha
            ) / denominator
            continue
        if unseen_base_policy == "uniform":
            conditional[base_index, local_available] = 1.0 / n_available
        elif unseen_base_policy == "marginal":
            local = marginal.copy()
            local[~local_available] = 0.0
            total = float(local.sum())
            if total > 0:
                conditional[base_index] = local / total
            else:
                conditional[base_index, local_available] = 1.0 / n_available
        # error policy deliberately leaves zeros and is enforced on prediction.

    return StateResolvedModel(
        source_shape=tuple(int(value) for value in field.shape),
        base_axes=base,
        added_axes=added,
        base_shape=base_shape,
        added_shape=added_shape,
        conditional_probability=conditional.reshape(base_shape + added_shape),
        marginal_probability=marginal.reshape(added_shape),
        base_training_mass=base_mass.reshape(base_shape),
        seen_base_mask=seen.reshape(base_shape),
        joint_available_mask=joint_available.reshape(base_shape + added_shape),
        alpha=float(alpha),
        unseen_base_policy=unseen_base_policy,
    )


def _heldout_to_joint(
    heldout_support: np.ndarray,
    *,
    source_shape: Sequence[int],
    base_axes: Sequence[int],
    added_axes: Sequence[int],
    heldout_unavailable_mask: np.ndarray | None,
) -> np.ndarray:
    values = np.asarray(heldout_support, dtype=float)
    joint_shape = tuple(source_shape[axis] for axis in (*base_axes, *added_axes))
    if values.shape == tuple(source_shape):
        cleaned, _ = _validate_support(values, heldout_unavailable_mask)
        return _ordered_marginal(cleaned, (*base_axes, *added_axes))
    if values.shape == joint_shape:
        cleaned, _ = _validate_support(values, heldout_unavailable_mask)
        return cleaned
    raise ValueError("heldout_support shape must match training source or base+added joint shape")


def _validate_probability_field(
    conditional_probability: np.ndarray,
    *,
    base_shape: Sequence[int],
    added_shape: Sequence[int],
    tolerance: float = 1e-8,
) -> np.ndarray:
    probability = np.asarray(conditional_probability, dtype=float)
    expected_shape = tuple(base_shape) + tuple(added_shape)
    if probability.shape != expected_shape:
        raise ValueError("conditional_probability shape does not match base_shape + added_shape")
    if not np.isfinite(probability).all() or np.any(probability < 0):
        raise ValueError("conditional_probability must be finite and non-negative")
    flat = probability.reshape(int(np.prod(base_shape)), int(np.prod(added_shape)))
    totals = flat.sum(axis=1)
    active = totals > 0
    if np.any(np.abs(totals[active] - 1.0) > tolerance):
        raise ValueError("each active base-state probability distribution must sum to one")
    return probability


def _score_joint_probability_field(
    conditional_probability: np.ndarray,
    heldout_joint: np.ndarray,
    *,
    marginal_probability: np.ndarray,
    base_shape: Sequence[int],
    added_shape: Sequence[int],
    seen_base_mask: np.ndarray | None,
    joint_available_mask: np.ndarray | None = None,
) -> StatePredictionScore:
    probability = _validate_probability_field(
        conditional_probability,
        base_shape=base_shape,
        added_shape=added_shape,
    )
    heldout = np.asarray(heldout_joint, dtype=float)
    expected_shape = tuple(base_shape) + tuple(added_shape)
    if heldout.shape != expected_shape:
        raise ValueError("heldout joint support shape does not match probability field")
    if not np.isfinite(heldout).all() or np.any(heldout < 0):
        raise ValueError("heldout support must be finite and non-negative")
    total = float(heldout.sum())
    if not total > 0:
        raise ValueError("heldout support must have positive mass")

    marginal = np.asarray(marginal_probability, dtype=float)
    if marginal.shape != tuple(added_shape):
        raise ValueError("marginal_probability shape does not match added_shape")
    if not np.isfinite(marginal).all() or np.any(marginal < 0):
        raise ValueError("marginal_probability must be finite and non-negative")
    if not math.isclose(float(marginal.sum()), 1.0, rel_tol=0.0, abs_tol=1e-8):
        raise ValueError("marginal_probability must sum to one")

    if joint_available_mask is not None:
        available = np.asarray(joint_available_mask, dtype=bool)
        if available.shape != expected_shape:
            raise ValueError("joint_available_mask shape mismatch")
        if np.any((heldout > 0) & ~available):
            raise ValueError("heldout support reaches a structurally unavailable state")

    bcount = int(np.prod(base_shape))
    acount = int(np.prod(added_shape))
    q = probability.reshape(bcount, acount)
    h = heldout.reshape(bcount, acount)
    r = marginal.reshape(acount)
    if np.any((h.sum(axis=0) > 0) & (r <= 0)):
        raise ValueError("heldout support reaches an added state with zero marginal probability")

    weighted_log = 0.0
    weighted_marginal_log = 0.0
    conditional_log_zero = False
    brier_sum = 0.0
    marginal_brier_sum = 0.0
    top1_mass = 0.0
    marginal_top1_mass = 0.0
    assigned_probability_sum = 0.0
    marginal_assigned_probability_sum = 0.0
    seen_mass = 0.0
    marginal_top = int(np.argmax(r))
    seen_flat = (
        np.ones(bcount, dtype=bool)
        if seen_base_mask is None
        else np.asarray(seen_base_mask, dtype=bool).reshape(bcount)
    )

    for b in range(bcount):
        row = h[b]
        row_mass = float(row.sum())
        if row_mass <= 0:
            continue
        if not float(q[b].sum()) > 0:
            raise ValueError("heldout support reaches a base state without a prediction")
        if seen_flat[b]:
            seen_mass += row_mass
        top = int(np.argmax(q[b]))
        q_squared = float(np.sum(q[b] ** 2))
        r_squared = float(np.sum(r ** 2))
        for a in np.flatnonzero(row > 0):
            mass = float(row[a])
            if q[b, a] <= 0:
                conditional_log_zero = True
            else:
                weighted_log += mass * math.log(float(q[b, a]))
            weighted_marginal_log += mass * math.log(float(r[a]))
            brier_sum += mass * (1.0 - 2.0 * float(q[b, a]) + q_squared)
            marginal_brier_sum += mass * (1.0 - 2.0 * float(r[a]) + r_squared)
            assigned_probability_sum += mass * float(q[b, a])
            marginal_assigned_probability_sum += mass * float(r[a])
        top1_mass += float(row[top])
        marginal_top1_mass += float(row[marginal_top])

    mean_log = float("-inf") if conditional_log_zero else weighted_log / total
    mean_marginal_log = weighted_marginal_log / total
    gain = float("-inf") if conditional_log_zero else mean_log - mean_marginal_log
    conditional_brier = brier_sum / total
    marginal_brier = marginal_brier_sum / total

    return StatePredictionScore(
        heldout_total_mass=total,
        scored_cell_count=int(np.count_nonzero(heldout > 0)),
        mean_log_score=float(mean_log),
        mean_marginal_log_score=float(mean_marginal_log),
        mean_log_score_gain=float(gain),
        conditional_brier_score=float(conditional_brier),
        marginal_brier_score=float(marginal_brier),
        brier_improvement=float(marginal_brier - conditional_brier),
        top1_accuracy=float(top1_mass / total),
        marginal_top1_accuracy=float(marginal_top1_mass / total),
        top1_improvement=float((top1_mass - marginal_top1_mass) / total),
        mean_assigned_probability=float(assigned_probability_sum / total),
        marginal_mean_assigned_probability=float(marginal_assigned_probability_sum / total),
        seen_base_mass_fraction=float(seen_mass / total),
    )


def score_state_probability_field(
    conditional_probability: np.ndarray,
    heldout_support: np.ndarray,
    *,
    base_ndim: int,
    marginal_probability: np.ndarray,
    seen_base_mask: np.ndarray | None = None,
) -> StatePredictionScore:
    """Score state probabilities produced by any upstream learning algorithm.

    The input field must be arranged as ``base axes`` followed by ``added axes``.
    This adapter is the bridge for RF, boosting, GAM, neural-network or other
    state-resolved models: ODSP evaluates their probabilistic state predictions
    without requiring them to use the native Dirichlet learner.
    """

    probability = np.asarray(conditional_probability, dtype=float)
    if not 1 <= int(base_ndim) < probability.ndim:
        raise ValueError("base_ndim must split at least one base and one added axis")
    base_shape = probability.shape[: int(base_ndim)]
    added_shape = probability.shape[int(base_ndim) :]
    return _score_joint_probability_field(
        probability,
        np.asarray(heldout_support, dtype=float),
        marginal_probability=np.asarray(marginal_probability, dtype=float),
        base_shape=base_shape,
        added_shape=added_shape,
        seen_base_mask=seen_base_mask,
    )


def score_state_prediction_groups(
    model: StateResolvedModel,
    heldout_supports: Mapping[str, np.ndarray] | Sequence[tuple[str, np.ndarray]],
    *,
    gain_tolerance: float = 1e-12,
) -> GroupedStatePredictionScore:
    """Score independent groups separately and classify the gain sign pattern."""

    items = (
        list(heldout_supports.items())
        if isinstance(heldout_supports, Mapping)
        else list(heldout_supports)
    )
    if not items:
        raise ValueError("heldout_supports must contain at least one group")
    groups: list[tuple[str, StatePredictionScore]] = []
    names: set[str] = set()
    for name, support in items:
        key = str(name)
        if key in names:
            raise ValueError("heldout group names must be unique")
        names.add(key)
        groups.append((key, model.score(np.asarray(support, dtype=float))))
    category = classify_independent_gains(
        [score.mean_log_score_gain for _, score in groups],
        tolerance=gain_tolerance,
    )
    return GroupedStatePredictionScore(groups=tuple(groups), gain_category=category)


def _as_state_matrix(values: Sequence[object] | Sequence[Sequence[object]], *, name: str) -> np.ndarray:
    matrix = np.asarray(values, dtype=object)
    if matrix.ndim == 1:
        matrix = matrix.reshape(-1, 1)
    if matrix.ndim != 2 or matrix.shape[0] == 0:
        raise ValueError(f"{name} must be a non-empty one- or two-dimensional sequence")
    return matrix


def _encode_columns(matrix: np.ndarray, *, name: str) -> tuple[np.ndarray, tuple[tuple[object, ...], ...]]:
    codes = np.empty(matrix.shape, dtype=int)
    all_levels: list[tuple[object, ...]] = []
    for column in range(matrix.shape[1]):
        lookup: dict[object, int] = {}
        levels: list[object] = []
        for row, raw in enumerate(matrix[:, column]):
            try:
                hash(raw)
            except TypeError as exc:
                raise ValueError(f"{name} values must be hashable") from exc
            if raw not in lookup:
                lookup[raw] = len(levels)
                levels.append(raw)
            codes[row, column] = lookup[raw]
        all_levels.append(tuple(levels))
    return codes, tuple(all_levels)


def encode_state_events(
    base_states: Sequence[object] | Sequence[Sequence[object]],
    added_states: Sequence[object] | Sequence[Sequence[object]],
    *,
    weights: Sequence[float] | None = None,
) -> EncodedStateSupport:
    """Convert public/event-table state records into a finite support tensor."""

    base_matrix = _as_state_matrix(base_states, name="base_states")
    added_matrix = _as_state_matrix(added_states, name="added_states")
    if base_matrix.shape[0] != added_matrix.shape[0]:
        raise ValueError("base_states and added_states must have the same row count")
    base_codes, base_levels = _encode_columns(base_matrix, name="base_states")
    added_codes, added_levels = _encode_columns(added_matrix, name="added_states")
    n = base_matrix.shape[0]
    if weights is None:
        mass = np.ones(n, dtype=float)
    else:
        mass = np.asarray(weights, dtype=float)
        if mass.shape != (n,):
            raise ValueError("weights must have one value per event")
        if not np.isfinite(mass).all() or np.any(mass < 0):
            raise ValueError("weights must be finite and non-negative")
    if not float(mass.sum()) > 0:
        raise ValueError("event weights must have positive total mass")

    shape = tuple(len(levels) for levels in (*base_levels, *added_levels))
    support = np.zeros(shape, dtype=float)
    indices = tuple(
        codes[:, column]
        for codes in (base_codes, added_codes)
        for column in range(codes.shape[1])
    )
    np.add.at(support, indices, mass)
    return EncodedStateSupport(
        support=support,
        base_levels=base_levels,
        added_levels=added_levels,
    )


def _encode_known_state(
    values: Sequence[object],
    levels: Sequence[Sequence[object]],
    name: str,
) -> tuple[int, ...]:
    state = tuple(values)
    if len(state) != len(levels):
        raise ValueError(f"{name} has wrong number of dimensions")
    result: list[int] = []
    for axis, (value, axis_levels) in enumerate(zip(state, levels)):
        lookup = {level: index for index, level in enumerate(axis_levels)}
        if value not in lookup:
            raise ValueError(f"{name} contains unseen label on axis {axis}: {value!r}")
        result.append(int(lookup[value]))
    return tuple(result)


def fit_state_resolved_events(
    base_states: Sequence[object] | Sequence[Sequence[object]],
    added_states: Sequence[object] | Sequence[Sequence[object]],
    *,
    weights: Sequence[float] | None = None,
    alpha: float = 0.5,
    unseen_base_policy: str = "marginal",
) -> EncodedStateResolvedModel:
    """Convenience entry point for event tables with discrete state labels."""

    encoded = encode_state_events(base_states, added_states, weights=weights)
    base_ndim = len(encoded.base_levels)
    added_ndim = len(encoded.added_levels)
    model = fit_state_resolved_model(
        encoded.support,
        base_axes=tuple(range(base_ndim)),
        added_axes=tuple(range(base_ndim, base_ndim + added_ndim)),
        alpha=alpha,
        unseen_base_policy=unseen_base_policy,
    )
    return EncodedStateResolvedModel(encoded_support=encoded, model=model)
