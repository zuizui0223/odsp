"""Prospectively frozen state-resolved prediction for MH_ANTWERPEN.

This module implements the design in ``MH_ANTWERPEN_STATE_PREDICTION_CONTRACT.json``.
It is intentionally specific to the empirical endpoint: fixed altitude states,
context features, 10-minute temporal thinning, individual admission and
leave-one-individual-out validation.  The generic prediction machinery remains
in :mod:`odsp.state_prediction` and :mod:`odsp.covariate_state_prediction`.
"""
from __future__ import annotations

from collections import Counter, defaultdict
from dataclasses import asdict, dataclass
from datetime import datetime, timezone
import math
from typing import Iterable, Mapping, Sequence

import numpy as np

from .covariate_state_prediction import fit_covariate_state_model, make_state_classifier
from .transferability import classify_independent_gains


STATE_LABELS = (
    "low_lt50",
    "lower_mid_50_200",
    "upper_mid_200_500",
    "high_ge500",
)
FEATURE_NAMES = (
    "external_temperature_c",
    "latitude",
    "longitude",
    "sin_local_solar_hour",
    "cos_local_solar_hour",
    "sin_day_of_year",
    "cos_day_of_year",
)


@dataclass(frozen=True)
class MarshHarrierEvent:
    timestamp_utc: datetime
    longitude: float
    latitude: float
    external_temperature_c: float
    height_m_amsl: float
    individual_id: str
    altitude_state: str
    source_file: str

    @property
    def features(self) -> tuple[float, ...]:
        utc_hour = (
            self.timestamp_utc.hour
            + self.timestamp_utc.minute / 60.0
            + self.timestamp_utc.second / 3600.0
            + self.timestamp_utc.microsecond / 3.6e9
        )
        solar_hour = (utc_hour + self.longitude / 15.0) % 24.0
        solar_angle = 2.0 * math.pi * solar_hour / 24.0
        doy = self.timestamp_utc.timetuple().tm_yday
        day_angle = 2.0 * math.pi * (float(doy) - 1.0) / 365.2425
        return (
            self.external_temperature_c,
            self.latitude,
            self.longitude,
            math.sin(solar_angle),
            math.cos(solar_angle),
            math.sin(day_angle),
            math.cos(day_angle),
        )


@dataclass(frozen=True)
class IndividualAdmission:
    individual_id: str
    thinned_event_count: int
    state_counts: dict[str, int]
    supported_states: tuple[str, ...]
    eligible: bool
    exclusion_reasons: tuple[str, ...]

    def as_dict(self) -> dict[str, object]:
        return asdict(self)


@dataclass(frozen=True)
class FoldResult:
    heldout_individual: str
    primary_status: str
    primary_score: dict[str, object] | None
    sensitivity_status: str
    sensitivity_score: dict[str, object] | None
    training_event_count: int
    heldout_event_count: int
    training_individual_count: int
    training_state_counts: dict[str, int]
    heldout_state_counts: dict[str, int]
    confusion_matrix: dict[str, dict[str, int]] | None
    primary_feature_importance: dict[str, float] | None

    def as_dict(self) -> dict[str, object]:
        return asdict(self)


def _bool_true(value: object) -> bool:
    text = "" if value is None else str(value).strip().lower()
    return text in {"true", "t", "1", "yes", "y"}


def _parse_float(value: object) -> float:
    if value is None:
        raise ValueError("missing numeric value")
    text = str(value).strip()
    if not text or text.lower() in {"na", "nan", "none", "null"}:
        raise ValueError("missing numeric value")
    result = float(text)
    if not math.isfinite(result):
        raise ValueError("non-finite numeric value")
    return result


def parse_timestamp_utc(value: object) -> datetime:
    if value is None:
        raise ValueError("missing timestamp")
    text = str(value).strip()
    if not text:
        raise ValueError("missing timestamp")
    normalized = text.replace("Z", "+00:00")
    try:
        parsed = datetime.fromisoformat(normalized)
    except ValueError:
        parsed = None
        for fmt in (
            "%Y-%m-%d %H:%M:%S.%f",
            "%Y-%m-%d %H:%M:%S",
            "%Y-%m-%dT%H:%M:%S.%f",
            "%Y-%m-%dT%H:%M:%S",
        ):
            try:
                parsed = datetime.strptime(text, fmt)
                break
            except ValueError:
                continue
        if parsed is None:
            raise ValueError(f"unparseable timestamp: {text!r}")
    if parsed.tzinfo is None:
        return parsed.replace(tzinfo=timezone.utc)
    return parsed.astimezone(timezone.utc)


def altitude_state(height_m_amsl: float) -> str:
    height = float(height_m_amsl)
    if height < 50.0:
        return STATE_LABELS[0]
    if height < 200.0:
        return STATE_LABELS[1]
    if height < 500.0:
        return STATE_LABELS[2]
    return STATE_LABELS[3]


def parse_admissible_row(
    row: Mapping[str, object],
    *,
    source_file: str,
) -> tuple[MarshHarrierEvent | None, str | None]:
    """Parse one GPS row under the frozen complete-case and quality rules."""

    if _bool_true(row.get("import-marked-outlier")):
        return None, "import_marked_outlier"
    if _bool_true(row.get("manually-marked-outlier")):
        return None, "manually_marked_outlier"
    try:
        timestamp = parse_timestamp_utc(row.get("timestamp"))
        longitude = _parse_float(row.get("location-long"))
        latitude = _parse_float(row.get("location-lat"))
        temperature = _parse_float(row.get("external-temperature"))
        height = _parse_float(row.get("height-above-msl"))
    except (TypeError, ValueError):
        return None, "required_complete_case_failure"

    individual = str(row.get("individual-local-identifier") or "").strip()
    if not individual:
        return None, "missing_individual"
    if not (-180.0 <= longitude <= 180.0 and -90.0 <= latitude <= 90.0):
        return None, "coordinate_out_of_range"
    if not (-40.0 <= temperature <= 60.0):
        return None, "temperature_out_of_range"
    if not (-100.0 <= height <= 5000.0):
        return None, "height_out_of_range"

    return (
        MarshHarrierEvent(
            timestamp_utc=timestamp,
            longitude=longitude,
            latitude=latitude,
            external_temperature_c=temperature,
            height_m_amsl=height,
            individual_id=individual,
            altitude_state=altitude_state(height),
            source_file=source_file,
        ),
        None,
    )


def thin_10min_earliest(events: Sequence[MarshHarrierEvent]) -> tuple[MarshHarrierEvent, ...]:
    """Keep the earliest event per individual in each absolute UTC 10-minute bin."""

    chosen: dict[tuple[str, int], MarshHarrierEvent] = {}
    for event in events:
        epoch = event.timestamp_utc.timestamp()
        key = (event.individual_id, int(math.floor(epoch / 600.0)))
        previous = chosen.get(key)
        if previous is None or event.timestamp_utc < previous.timestamp_utc:
            chosen[key] = event
    return tuple(sorted(chosen.values(), key=lambda e: (e.individual_id, e.timestamp_utc)))


def individual_admission(
    events: Sequence[MarshHarrierEvent],
    *,
    min_events: int = 300,
    min_states: int = 2,
    min_events_per_supported_state: int = 10,
) -> tuple[IndividualAdmission, ...]:
    grouped: dict[str, list[MarshHarrierEvent]] = defaultdict(list)
    for event in events:
        grouped[event.individual_id].append(event)
    result: list[IndividualAdmission] = []
    for individual in sorted(grouped):
        group = grouped[individual]
        counts = Counter(event.altitude_state for event in group)
        supported = tuple(
            state for state in STATE_LABELS if counts.get(state, 0) >= min_events_per_supported_state
        )
        reasons: list[str] = []
        if len(group) < min_events:
            reasons.append("too_few_thinned_events")
        if len(supported) < min_states:
            reasons.append("too_few_supported_altitude_states")
        result.append(
            IndividualAdmission(
                individual_id=individual,
                thinned_event_count=len(group),
                state_counts={state: int(counts.get(state, 0)) for state in STATE_LABELS},
                supported_states=supported,
                eligible=not reasons,
                exclusion_reasons=tuple(reasons),
            )
        )
    return tuple(result)


def _training_weights(individual_ids: Sequence[str]) -> np.ndarray:
    counts = Counter(individual_ids)
    return np.asarray([1.0 / counts[value] for value in individual_ids], dtype=float)


def _matrix(events: Sequence[MarshHarrierEvent]) -> tuple[np.ndarray, np.ndarray, list[str]]:
    X = np.asarray([event.features for event in events], dtype=float)
    y = np.asarray([event.altitude_state for event in events], dtype=object)
    individuals = [event.individual_id for event in events]
    if not np.isfinite(X).all():
        raise ValueError("derived feature matrix contains non-finite values")
    return X, y, individuals


def _confusion(model, X: np.ndarray, y: np.ndarray) -> dict[str, dict[str, int]]:
    probability = model.predict_proba(X)
    classes = tuple(model.classes)
    predicted = np.asarray([classes[int(index)] for index in np.argmax(probability, axis=1)], dtype=object)
    matrix = {truth: {pred: 0 for pred in STATE_LABELS} for truth in STATE_LABELS}
    for truth, pred in zip(y.tolist(), predicted.tolist()):
        matrix[str(truth)][str(pred)] += 1
    return matrix


def _score_dict(score) -> dict[str, object]:
    data = score.as_dict()
    for key, value in list(data.items()):
        if isinstance(value, float) and not math.isfinite(value):
            data[key] = None
    return data


def run_leave_one_individual_out(
    events: Sequence[MarshHarrierEvent],
    eligible_individuals: Sequence[str],
    *,
    random_state: int = 20260905,
) -> tuple[FoldResult, ...]:
    eligible = tuple(sorted(str(value) for value in eligible_individuals))
    allowed = set(eligible)
    filtered = tuple(event for event in events if event.individual_id in allowed)
    results: list[FoldResult] = []

    for heldout in eligible:
        training = tuple(event for event in filtered if event.individual_id != heldout)
        testing = tuple(event for event in filtered if event.individual_id == heldout)
        X_train, y_train, train_ids = _matrix(training)
        X_test, y_test, _ = _matrix(testing)
        weights = _training_weights(train_ids)
        train_classes = set(y_train.tolist())
        heldout_classes = set(y_test.tolist())
        train_counts = Counter(y_train.tolist())
        test_counts = Counter(y_test.tolist())

        if not heldout_classes.issubset(train_classes):
            results.append(
                FoldResult(
                    heldout_individual=heldout,
                    primary_status="unscorable_training_absent_state",
                    primary_score=None,
                    sensitivity_status="not_run_primary_unscorable",
                    sensitivity_score=None,
                    training_event_count=len(training),
                    heldout_event_count=len(testing),
                    training_individual_count=len(eligible) - 1,
                    training_state_counts={state: int(train_counts.get(state, 0)) for state in STATE_LABELS},
                    heldout_state_counts={state: int(test_counts.get(state, 0)) for state in STATE_LABELS},
                    confusion_matrix=None,
                    primary_feature_importance=None,
                )
            )
            continue

        rf = make_state_classifier(
            "random_forest",
            random_state=random_state,
            n_estimators=500,
            min_samples_leaf=20,
            max_features="sqrt",
            class_weight=None,
        )
        primary_model = fit_covariate_state_model(rf, X_train, y_train, sample_weight=weights)
        primary_score = primary_model.score(X_test, y_test)
        fitted = primary_model.estimator
        importance = getattr(fitted, "feature_importances_", None)
        importance_dict = None
        if importance is not None:
            importance_dict = {
                name: float(value) for name, value in zip(FEATURE_NAMES, np.asarray(importance, dtype=float))
            }

        sensitivity_status = "scored"
        sensitivity_score_dict = None
        means = X_train.mean(axis=0)
        scales = X_train.std(axis=0)
        if np.any(scales <= 0) or not np.isfinite(scales).all():
            sensitivity_status = "unavailable_zero_sd_feature"
        else:
            X_train_z = (X_train - means) / scales
            X_test_z = (X_test - means) / scales
            logit = make_state_classifier(
                "multinomial_logit",
                random_state=random_state,
                C=1.0,
                solver="lbfgs",
                max_iter=3000,
            )
            sensitivity_model = fit_covariate_state_model(
                logit, X_train_z, y_train, sample_weight=weights
            )
            sensitivity_score_dict = _score_dict(sensitivity_model.score(X_test_z, y_test))

        results.append(
            FoldResult(
                heldout_individual=heldout,
                primary_status="scored",
                primary_score=_score_dict(primary_score),
                sensitivity_status=sensitivity_status,
                sensitivity_score=sensitivity_score_dict,
                training_event_count=len(training),
                heldout_event_count=len(testing),
                training_individual_count=len(eligible) - 1,
                training_state_counts={state: int(train_counts.get(state, 0)) for state in STATE_LABELS},
                heldout_state_counts={state: int(test_counts.get(state, 0)) for state in STATE_LABELS},
                confusion_matrix=_confusion(primary_model, X_test, y_test),
                primary_feature_importance=importance_dict,
            )
        )
    return tuple(results)


def endpoint_decision(
    admissions: Sequence[IndividualAdmission],
    folds: Sequence[FoldResult],
    *,
    minimum_eligible_individuals: int = 4,
) -> dict[str, object]:
    eligible = tuple(item.individual_id for item in admissions if item.eligible)
    if len(eligible) < minimum_eligible_individuals:
        return {
            "terminal_category": "empirical_state_prediction_unavailable",
            "reason": "fewer_than_minimum_eligible_individuals",
            "eligible_individual_count": len(eligible),
            "primary_gains": [],
            "mean_primary_gain_descriptive": None,
        }
    if any(fold.primary_status != "scored" for fold in folds):
        return {
            "terminal_category": "empirical_state_prediction_unavailable",
            "reason": "at_least_one_heldout_individual_unscorable_under_frozen_training_support",
            "eligible_individual_count": len(eligible),
            "primary_gains": [],
            "mean_primary_gain_descriptive": None,
        }
    gains = [float(fold.primary_score["mean_log_score_gain"]) for fold in folds if fold.primary_score]
    category = classify_independent_gains(gains, tolerance=0.0)
    terminal = {
        "generalizing": "empirical_state_prediction_generalizing",
        "non_generalizing": "empirical_state_prediction_non_generalizing",
        "mixed": "empirical_state_prediction_mixed",
    }[category]
    return {
        "terminal_category": terminal,
        "reason": "frozen_groupwise_primary_rf_gain_rule",
        "eligible_individual_count": len(eligible),
        "primary_gains": gains,
        "mean_primary_gain_descriptive": float(np.mean(gains)),
        "minimum_primary_gain": float(np.min(gains)),
        "maximum_primary_gain": float(np.max(gains)),
    }
