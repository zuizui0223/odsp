"""Long-table workflow for state-resolved ecological prediction.

This module provides a deliberately thin operational layer above the scientific
cores in :mod:`odsp.covariate_state_prediction` and
:mod:`odsp.distributional_gain`.

The core design rule is explicitness: the caller declares the state, predictor,
independence-unit, stratum, fold and weight columns.  The workflow never invents
folds, groups, strata or training weights from column names.
"""
from __future__ import annotations

from dataclasses import asdict, dataclass
import math
from typing import Callable, Mapping, Sequence

import numpy as np

from .covariate_state_prediction import fit_covariate_state_model
from .distributional_gain import score_distributional_gain
from .transferability import classify_independent_gains


@dataclass(frozen=True)
class EventTableSpec:
    """Column contract for an event-level long table."""

    state: str
    features: tuple[str, ...]
    group: str
    stratum: str | None = None
    fold: str | None = None
    weight: str | None = None

    def __post_init__(self) -> None:
        if not self.state or not self.group:
            raise ValueError("state and group column names must be non-empty")
        if not self.features:
            raise ValueError("features must contain at least one column")
        names = [self.state, self.group, *self.features]
        for optional in (self.stratum, self.fold, self.weight):
            if optional is not None:
                if not optional:
                    raise ValueError("optional column names must be non-empty")
                names.append(optional)
        if len(set(names)) != len(names):
            raise ValueError("state, features, group, stratum, fold and weight columns must be distinct")


@dataclass(frozen=True)
class PreparedEventTable:
    """Validated numerical arrays extracted from a long event table."""

    X: np.ndarray
    state: np.ndarray
    group: np.ndarray
    stratum: np.ndarray | None
    fold: np.ndarray | None
    event_weight: np.ndarray
    feature_names: tuple[str, ...]
    row_count: int


@dataclass(frozen=True)
class BaselineHierarchy:
    """Training-only lower-information state distributions for one fold."""

    classes: tuple[object, ...]
    pooled: tuple[float, ...]
    by_stratum: tuple[tuple[object, tuple[float, ...]], ...]

    def stratum_probability(self, stratum: object) -> np.ndarray:
        for key, probability in self.by_stratum:
            if key == stratum:
                return np.asarray(probability, dtype=float)
        raise KeyError(stratum)

    def as_dict(self) -> dict[str, object]:
        return {
            "classes": list(self.classes),
            "pooled": list(self.pooled),
            "by_stratum": [
                {"stratum": key, "probability": list(probability)}
                for key, probability in self.by_stratum
            ],
        }


@dataclass(frozen=True)
class EventGroupScore:
    """Held-out score and baseline decomposition for one independent group."""

    group: object
    fold: object
    stratum: object | None
    row_count: int
    total_weight: float
    mean_model_log_score: float
    mean_pooled_log_score: float
    mean_stratum_log_score: float | None
    pooled_gain: float
    stratum_component: float | None
    context_within_stratum_component: float | None
    requested_baseline_gain: float
    additivity_error: float | None

    def as_dict(self) -> dict[str, object]:
        return asdict(self)


@dataclass(frozen=True)
class EventWorkflowResult:
    """Grouped transfer result from the generic event-table workflow."""

    baseline: str
    groups: tuple[EventGroupScore, ...]
    gain_category: str

    @property
    def gains(self) -> tuple[float, ...]:
        return tuple(row.requested_baseline_gain for row in self.groups)

    def as_dict(self) -> dict[str, object]:
        return {
            "baseline": self.baseline,
            "groups": [row.as_dict() for row in self.groups],
            "gains": list(self.gains),
            "gain_category": self.gain_category,
        }


TrainingWeightPolicy = Callable[[PreparedEventTable, np.ndarray], Sequence[float]]


def _records(table: object) -> list[Mapping[str, object]]:
    if hasattr(table, "to_dict"):
        try:
            candidate = table.to_dict(orient="records")  # type: ignore[attr-defined]
        except TypeError:
            candidate = None
        if candidate is not None:
            table = candidate
    if isinstance(table, Mapping):
        raise ValueError("event table must be row-oriented, not a single mapping")
    try:
        rows = list(table)  # type: ignore[arg-type]
    except TypeError as exc:
        raise ValueError("event table must be an iterable of row mappings") from exc
    if not rows:
        raise ValueError("event table must contain at least one row")
    if not all(isinstance(row, Mapping) for row in rows):
        raise ValueError("every event-table row must be a mapping")
    return rows


def _require_hashable(value: object, *, column: str) -> object:
    if value is None:
        raise ValueError(f"column {column!r} contains a missing value")
    try:
        hash(value)
    except TypeError as exc:
        raise ValueError(f"column {column!r} values must be hashable") from exc
    return value


def prepare_event_table(table: object, spec: EventTableSpec) -> PreparedEventTable:
    """Validate a row-oriented long table without adding a pandas dependency."""

    rows = _records(table)
    n = len(rows)
    X = np.empty((n, len(spec.features)), dtype=float)
    state = np.empty(n, dtype=object)
    group = np.empty(n, dtype=object)
    stratum = None if spec.stratum is None else np.empty(n, dtype=object)
    fold = None if spec.fold is None else np.empty(n, dtype=object)
    event_weight = np.ones(n, dtype=float)

    required = [spec.state, spec.group, *spec.features]
    if spec.stratum is not None:
        required.append(spec.stratum)
    if spec.fold is not None:
        required.append(spec.fold)
    if spec.weight is not None:
        required.append(spec.weight)

    for i, row in enumerate(rows):
        missing = [name for name in required if name not in row]
        if missing:
            raise ValueError(f"row {i} is missing required columns: {', '.join(missing)}")
        state[i] = _require_hashable(row[spec.state], column=spec.state)
        group[i] = _require_hashable(row[spec.group], column=spec.group)
        for j, name in enumerate(spec.features):
            try:
                value = float(row[name])
            except (TypeError, ValueError) as exc:
                raise ValueError(f"column {name!r} must be numeric") from exc
            if not math.isfinite(value):
                raise ValueError(f"column {name!r} must be finite")
            X[i, j] = value
        if stratum is not None and spec.stratum is not None:
            stratum[i] = _require_hashable(row[spec.stratum], column=spec.stratum)
        if fold is not None and spec.fold is not None:
            fold[i] = _require_hashable(row[spec.fold], column=spec.fold)
        if spec.weight is not None:
            try:
                weight = float(row[spec.weight])
            except (TypeError, ValueError) as exc:
                raise ValueError(f"column {spec.weight!r} must be numeric") from exc
            if not math.isfinite(weight) or weight < 0:
                raise ValueError(f"column {spec.weight!r} must be finite and non-negative")
            event_weight[i] = weight

    if not float(event_weight.sum()) > 0:
        raise ValueError("event weights must have positive total mass")

    for name, values in (("stratum", stratum), ("fold", fold)):
        if values is None:
            continue
        mapping: dict[object, object] = {}
        for g, value in zip(group.tolist(), values.tolist()):
            old = mapping.setdefault(g, value)
            if old != value:
                raise ValueError(f"group {g!r} maps to multiple {name} values")

    return PreparedEventTable(
        X=X,
        state=state,
        group=group,
        stratum=stratum,
        fold=fold,
        event_weight=event_weight,
        feature_names=tuple(spec.features),
        row_count=n,
    )


def equal_stratum_equal_group_training_weights(
    table: PreparedEventTable,
    train_index: np.ndarray,
) -> np.ndarray:
    """Give equal total mass to strata, then groups within strata, then rows.

    This reproduces the weighting family used by the BOP raptor endpoint when the
    stratum is species and the independent group is individual.
    """

    if table.stratum is None:
        raise ValueError("equal-stratum weighting requires a declared stratum column")
    index = np.asarray(train_index, dtype=int)
    if index.ndim != 1 or index.size == 0:
        raise ValueError("train_index must be a non-empty one-dimensional index")
    groups = table.group[index].tolist()
    strata = table.stratum[index].tolist()

    group_stratum: dict[object, object] = {}
    group_count: dict[object, int] = {}
    stratum_groups: dict[object, set[object]] = {}
    for group, stratum in zip(groups, strata):
        old = group_stratum.setdefault(group, stratum)
        if old != stratum:
            raise ValueError(f"group {group!r} maps to multiple strata")
        group_count[group] = group_count.get(group, 0) + 1
        stratum_groups.setdefault(stratum, set()).add(group)
    n_strata = len(stratum_groups)
    if n_strata == 0:
        raise ValueError("training rows contain no strata")

    weights = np.empty(index.size, dtype=float)
    for i, (group, stratum) in enumerate(zip(groups, strata)):
        weights[i] = 1.0 / (
            n_strata
            * len(stratum_groups[stratum])
            * group_count[group]
        )
    return weights


def _training_weights(
    table: PreparedEventTable,
    train_index: np.ndarray,
    policy: TrainingWeightPolicy | None,
) -> np.ndarray:
    if policy is None:
        result = np.asarray(table.event_weight[train_index], dtype=float)
    else:
        result = np.asarray(policy(table, train_index), dtype=float)
    if result.shape != (train_index.size,):
        raise ValueError("training weight policy must return one weight per training row")
    if not np.isfinite(result).all() or np.any(result < 0):
        raise ValueError("training weights must be finite and non-negative")
    if not float(result.sum()) > 0:
        raise ValueError("training weights must have positive total mass")
    return result


def _probability_from_training(
    labels: np.ndarray,
    weights: np.ndarray,
    classes: tuple[object, ...],
) -> np.ndarray:
    lookup = {value: i for i, value in enumerate(classes)}
    probability = np.zeros(len(classes), dtype=float)
    for label, weight in zip(labels.tolist(), weights.tolist()):
        if label not in lookup:
            raise ValueError(f"training state absent from fitted classes: {label!r}")
        probability[lookup[label]] += float(weight)
    total = float(probability.sum())
    if not total > 0:
        raise ValueError("baseline training mass must be positive")
    return probability / total


def training_state_baselines(
    table: PreparedEventTable,
    train_index: Sequence[int],
    *,
    classes: Sequence[object],
    training_weight_policy: TrainingWeightPolicy | None = None,
) -> BaselineHierarchy:
    """Compute pooled and optional stratum baselines from training rows only."""

    index = np.asarray(train_index, dtype=int)
    if index.ndim != 1 or index.size == 0:
        raise ValueError("train_index must be a non-empty one-dimensional index")
    class_tuple = tuple(classes)
    if len(class_tuple) < 2 or len(set(class_tuple)) != len(class_tuple):
        raise ValueError("classes must contain at least two unique state labels")
    weights = _training_weights(table, index, training_weight_policy)
    pooled = _probability_from_training(table.state[index], weights, class_tuple)

    by_stratum: list[tuple[object, tuple[float, ...]]] = []
    if table.stratum is not None:
        for value in dict.fromkeys(table.stratum[index].tolist()):
            local = np.asarray(
                [i for i, row in enumerate(index) if table.stratum[row] == value],
                dtype=int,
            )
            probability = _probability_from_training(
                table.state[index[local]],
                weights[local],
                class_tuple,
            )
            by_stratum.append(
                (value, tuple(float(item) for item in probability))
            )
    return BaselineHierarchy(
        classes=class_tuple,
        pooled=tuple(float(item) for item in pooled),
        by_stratum=tuple(by_stratum),
    )


def _assigned_log_probability(
    probability: np.ndarray,
    labels: np.ndarray,
    classes: tuple[object, ...],
) -> np.ndarray:
    lookup = {value: i for i, value in enumerate(classes)}
    result = np.empty(labels.shape[0], dtype=float)
    for i, label in enumerate(labels.tolist()):
        if label not in lookup:
            raise ValueError(f"held-out state was absent from training classes: {label!r}")
        value = float(probability[i, lookup[label]]) if probability.ndim == 2 else float(probability[lookup[label]])
        result[i] = -math.inf if value <= 0 else math.log(value)
    return result


def cross_validate_state_events(
    table: object,
    *,
    spec: EventTableSpec,
    estimator: object,
    baseline: str = "pooled",
    training_weight_policy: TrainingWeightPolicy | None = None,
    gain_tolerance: float = 0.0,
) -> EventWorkflowResult:
    """Fit and score a probabilistic state learner on explicit independent groups.

    If ``spec.fold`` is declared, rows sharing a fold are excluded from training
    together and every independent group in that fold is scored separately.  If
    no fold column is declared, leave-one-group-out transfer is used.

    ``baseline='pooled'`` reports gain over the training state marginal.
    ``baseline='stratum'`` reports gain over a training marginal conditioned only
    on the declared stratum.  Whenever a stratum is declared, the returned rows
    also contain the additive pooled -> stratum -> model decomposition.
    """

    if baseline not in {"pooled", "stratum"}:
        raise ValueError("baseline must be 'pooled' or 'stratum'")
    prepared = prepare_event_table(table, spec)
    if baseline == "stratum" and prepared.stratum is None:
        raise ValueError("baseline='stratum' requires spec.stratum")

    if prepared.fold is None:
        fold_values = tuple(dict.fromkeys(prepared.group.tolist()))
        fold_vector = prepared.group
    else:
        fold_values = tuple(dict.fromkeys(prepared.fold.tolist()))
        fold_vector = prepared.fold

    rows: list[EventGroupScore] = []
    for fold_value in fold_values:
        test_fold = np.asarray([value == fold_value for value in fold_vector], dtype=bool)
        train_index = np.flatnonzero(~test_fold)
        test_index = np.flatnonzero(test_fold)
        if train_index.size == 0 or test_index.size == 0:
            raise ValueError(f"fold {fold_value!r} leaves no training or testing rows")

        train_weights = _training_weights(prepared, train_index, training_weight_policy)
        model = fit_covariate_state_model(
            estimator,
            prepared.X[train_index],
            prepared.state[train_index],
            sample_weight=train_weights,
        )
        classes = tuple(model.classes)
        baselines = training_state_baselines(
            prepared,
            train_index,
            classes=classes,
            training_weight_policy=training_weight_policy,
        )
        pooled_probability = np.asarray(baselines.pooled, dtype=float)

        for group_value in dict.fromkeys(prepared.group[test_index].tolist()):
            group_index = np.asarray(
                [row for row in test_index if prepared.group[row] == group_value],
                dtype=int,
            )
            y = prepared.state[group_index]
            score_weight = prepared.event_weight[group_index]
            conditional_probability = model.predict_proba(prepared.X[group_index])
            conditional_log = _assigned_log_probability(
                conditional_probability, y, classes
            )
            pooled_log = _assigned_log_probability(pooled_probability, y, classes)
            pooled_score = score_distributional_gain(
                conditional_log, pooled_log, sample_weight=score_weight
            )

            stratum_value: object | None = None
            mean_stratum: float | None = None
            stratum_component: float | None = None
            context_component: float | None = None
            additivity_error: float | None = None
            requested_gain = pooled_score.mean_log_score_gain

            if prepared.stratum is not None:
                stratum_value = prepared.stratum[group_index[0]]
                try:
                    stratum_probability = baselines.stratum_probability(stratum_value)
                except KeyError as exc:
                    raise ValueError(
                        f"held-out stratum {stratum_value!r} is absent from training"
                    ) from exc
                stratum_log = _assigned_log_probability(
                    stratum_probability, y, classes
                )
                context_score = score_distributional_gain(
                    conditional_log, stratum_log, sample_weight=score_weight
                )
                shift_score = score_distributional_gain(
                    stratum_log, pooled_log, sample_weight=score_weight
                )
                mean_stratum = context_score.mean_baseline_log_score
                stratum_component = shift_score.mean_log_score_gain
                context_component = context_score.mean_log_score_gain
                if all(math.isfinite(value) for value in (
                    pooled_score.mean_log_score_gain,
                    stratum_component,
                    context_component,
                )):
                    additivity_error = float(
                        pooled_score.mean_log_score_gain
                        - (stratum_component + context_component)
                    )
                elif (
                    pooled_score.mean_log_score_gain == -math.inf
                    and context_component == -math.inf
                    and math.isfinite(stratum_component)
                ):
                    additivity_error = 0.0
                if baseline == "stratum":
                    requested_gain = context_component

            rows.append(
                EventGroupScore(
                    group=group_value,
                    fold=fold_value,
                    stratum=stratum_value,
                    row_count=int(group_index.size),
                    total_weight=float(score_weight.sum()),
                    mean_model_log_score=float(pooled_score.mean_conditional_log_score),
                    mean_pooled_log_score=float(pooled_score.mean_baseline_log_score),
                    mean_stratum_log_score=None if mean_stratum is None else float(mean_stratum),
                    pooled_gain=float(pooled_score.mean_log_score_gain),
                    stratum_component=None if stratum_component is None else float(stratum_component),
                    context_within_stratum_component=None if context_component is None else float(context_component),
                    requested_baseline_gain=float(requested_gain),
                    additivity_error=additivity_error,
                )
            )

    rows.sort(key=lambda row: (str(row.fold), str(row.stratum), str(row.group)))
    category = classify_independent_gains(
        [row.requested_baseline_gain for row in rows],
        tolerance=gain_tolerance,
    )
    return EventWorkflowResult(
        baseline=baseline,
        groups=tuple(rows),
        gain_category=category,
    )
