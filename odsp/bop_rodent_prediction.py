"""Prospectively frozen multi-species state prediction for BOP_RODENT v3.

This endpoint implements ``BOP_RODENT_STATE_PREDICTION_CONTRACT.json``.
Prediction is species-aware and context-conditioned, while independent validation
remains individual-based.  Altitude states are absolute height above mean sea
level and inherit the frozen bins from the closed MH_ANTWERPEN endpoint.
"""
from __future__ import annotations

from collections import Counter, defaultdict
from dataclasses import asdict, dataclass
from datetime import datetime
import hashlib
import math
from typing import Mapping, Sequence

import numpy as np

from .covariate_state_prediction import fit_covariate_state_model, make_state_classifier
from .mh_antwerpen_prediction import STATE_LABELS, altitude_state, parse_timestamp_utc
from .transferability import classify_independent_gains


CONTINUOUS_FEATURE_NAMES = (
    "external_temperature_c",
    "latitude",
    "longitude",
    "sin_local_solar_hour",
    "cos_local_solar_hour",
    "sin_day_of_year",
    "cos_day_of_year",
)


@dataclass(frozen=True)
class BOPEvent:
    timestamp_utc: datetime
    longitude: float
    latitude: float
    external_temperature_c: float
    height_m_amsl: float
    individual_id: str
    species: str
    altitude_state: str
    source_file: str

    @property
    def continuous_features(self) -> tuple[float, ...]:
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
class BOPIndividualAdmission:
    individual_id: str
    species: str
    thinned_event_count: int
    state_counts: dict[str, int]
    supported_states: tuple[str, ...]
    individually_eligible: bool
    species_admitted: bool
    final_eligible: bool
    exclusion_reasons: tuple[str, ...]

    def as_dict(self) -> dict[str, object]:
        return asdict(self)


@dataclass(frozen=True)
class BOPHeldoutResult:
    fold: int
    heldout_individual: str
    species: str
    primary_status: str
    primary_score: dict[str, object] | None
    sensitivity_status: str
    sensitivity_score: dict[str, object] | None
    training_event_count: int
    heldout_event_count: int
    training_individual_count: int
    training_species_count: int
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
        raise ValueError("missing numeric")
    text = str(value).strip()
    if not text or text.lower() in {"na", "nan", "none", "null"}:
        raise ValueError("missing numeric")
    result = float(text)
    if not math.isfinite(result):
        raise ValueError("non-finite numeric")
    return result


def parse_admissible_bop_row(
    row: Mapping[str, object], *, source_file: str
) -> tuple[BOPEvent | None, str | None]:
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
    species = str(row.get("individual-taxon-canonical-name") or "").strip()
    if not individual:
        return None, "missing_individual"
    if not species:
        return None, "missing_species"
    if not (-180.0 <= longitude <= 180.0 and -90.0 <= latitude <= 90.0):
        return None, "coordinate_out_of_range"
    if not (-40.0 <= temperature <= 60.0):
        return None, "temperature_out_of_range"
    if not (-100.0 <= height <= 5000.0):
        return None, "height_out_of_range"
    return (
        BOPEvent(
            timestamp_utc=timestamp,
            longitude=longitude,
            latitude=latitude,
            external_temperature_c=temperature,
            height_m_amsl=height,
            individual_id=individual,
            species=species,
            altitude_state=altitude_state(height),
            source_file=source_file,
        ),
        None,
    )


def thin_hourly_earliest(events: Sequence[BOPEvent]) -> tuple[BOPEvent, ...]:
    chosen: dict[tuple[str, int], BOPEvent] = {}
    for event in events:
        key = (event.individual_id, int(math.floor(event.timestamp_utc.timestamp() / 3600.0)))
        previous = chosen.get(key)
        if previous is None or event.timestamp_utc < previous.timestamp_utc:
            chosen[key] = event
    return tuple(sorted(chosen.values(), key=lambda e: (e.individual_id, e.timestamp_utc)))


def build_admissions(
    events: Sequence[BOPEvent],
    *,
    min_events: int = 300,
    min_states: int = 2,
    min_state_events: int = 20,
    min_individuals_per_species: int = 3,
) -> tuple[BOPIndividualAdmission, ...]:
    grouped: dict[str, list[BOPEvent]] = defaultdict(list)
    for event in events:
        grouped[event.individual_id].append(event)
    prelim: dict[str, dict[str, object]] = {}
    species_individuals: dict[str, list[str]] = defaultdict(list)
    for individual in sorted(grouped):
        group = grouped[individual]
        species_set = {event.species for event in group}
        if len(species_set) != 1:
            raise ValueError(f"individual {individual!r} maps to multiple species")
        species = next(iter(species_set))
        counts = Counter(event.altitude_state for event in group)
        supported = tuple(s for s in STATE_LABELS if counts.get(s, 0) >= min_state_events)
        reasons: list[str] = []
        if len(group) < min_events:
            reasons.append("too_few_hourly_thinned_events")
        if len(supported) < min_states:
            reasons.append("too_few_supported_altitude_states")
        individually_eligible = not reasons
        prelim[individual] = {
            "species": species,
            "n": len(group),
            "counts": counts,
            "supported": supported,
            "individually_eligible": individually_eligible,
            "reasons": reasons,
        }
        if individually_eligible:
            species_individuals[species].append(individual)
    admitted_species = {
        species for species, ids in species_individuals.items() if len(ids) >= min_individuals_per_species
    }
    result: list[BOPIndividualAdmission] = []
    for individual in sorted(prelim):
        item = prelim[individual]
        species = str(item["species"])
        reasons = list(item["reasons"])
        species_admitted = species in admitted_species
        if bool(item["individually_eligible"]) and not species_admitted:
            reasons.append("species_has_too_few_eligible_individuals")
        result.append(
            BOPIndividualAdmission(
                individual_id=individual,
                species=species,
                thinned_event_count=int(item["n"]),
                state_counts={s: int(item["counts"].get(s, 0)) for s in STATE_LABELS},
                supported_states=tuple(item["supported"]),
                individually_eligible=bool(item["individually_eligible"]),
                species_admitted=species_admitted,
                final_eligible=bool(item["individually_eligible"]) and species_admitted,
                exclusion_reasons=tuple(reasons),
            )
        )
    return tuple(result)


def deterministic_folds(admissions: Sequence[BOPIndividualAdmission], n_folds: int = 5) -> dict[str, int]:
    by_species: dict[str, list[str]] = defaultdict(list)
    for item in admissions:
        if item.final_eligible:
            by_species[item.species].append(item.individual_id)
    result: dict[str, int] = {}
    for species in sorted(by_species):
        ids = sorted(
            by_species[species],
            key=lambda value: (hashlib.sha256(value.encode("utf-8")).hexdigest(), value),
        )
        for index, individual in enumerate(ids):
            result[individual] = int(index % n_folds)
    return result


def admitted_species(admissions: Sequence[BOPIndividualAdmission]) -> tuple[str, ...]:
    return tuple(sorted({item.species for item in admissions if item.final_eligible}))


def _feature_names(species_labels: Sequence[str]) -> tuple[str, ...]:
    return CONTINUOUS_FEATURE_NAMES + tuple(f"species::{s}" for s in species_labels)


def feature_matrix(
    events: Sequence[BOPEvent], species_labels: Sequence[str]
) -> tuple[np.ndarray, np.ndarray, list[str], list[str]]:
    species_labels = tuple(species_labels)
    species_index = {value: i for i, value in enumerate(species_labels)}
    X = np.zeros((len(events), len(CONTINUOUS_FEATURE_NAMES) + len(species_labels)), dtype=float)
    y = np.empty(len(events), dtype=object)
    ids: list[str] = []
    species_values: list[str] = []
    for row, event in enumerate(events):
        if event.species not in species_index:
            raise ValueError(f"event species not admitted: {event.species!r}")
        X[row, : len(CONTINUOUS_FEATURE_NAMES)] = event.continuous_features
        X[row, len(CONTINUOUS_FEATURE_NAMES) + species_index[event.species]] = 1.0
        y[row] = event.altitude_state
        ids.append(event.individual_id)
        species_values.append(event.species)
    if not np.isfinite(X).all():
        raise ValueError("derived features are non-finite")
    return X, y, ids, species_values


def hierarchical_training_weights(individual_ids: Sequence[str], species_values: Sequence[str]) -> np.ndarray:
    if len(individual_ids) != len(species_values):
        raise ValueError("individual_ids and species_values lengths differ")
    individual_species: dict[str, str] = {}
    event_counts = Counter(individual_ids)
    species_individual_sets: dict[str, set[str]] = defaultdict(set)
    for individual, species in zip(individual_ids, species_values):
        old = individual_species.setdefault(individual, species)
        if old != species:
            raise ValueError("individual occurs under multiple species")
        species_individual_sets[species].add(individual)
    species_count = len(species_individual_sets)
    if species_count == 0:
        raise ValueError("no training species")
    weights = []
    for individual, species in zip(individual_ids, species_values):
        value = 1.0 / (
            species_count
            * len(species_individual_sets[species])
            * event_counts[individual]
        )
        weights.append(value)
    return np.asarray(weights, dtype=float)


def _score_dict(score) -> dict[str, object]:
    data = score.as_dict()
    for key, value in list(data.items()):
        if isinstance(value, float) and not math.isfinite(value):
            data[key] = None
    return data


def _confusion(model, X: np.ndarray, y: np.ndarray) -> dict[str, dict[str, int]]:
    probability = model.predict_proba(X)
    classes = tuple(model.classes)
    predicted = [classes[int(i)] for i in np.argmax(probability, axis=1)]
    result = {truth: {pred: 0 for pred in STATE_LABELS} for truth in STATE_LABELS}
    for truth, pred in zip(y.tolist(), predicted):
        result[str(truth)][str(pred)] += 1
    return result


def execute_five_fold_prediction(
    events: Sequence[BOPEvent],
    admissions: Sequence[BOPIndividualAdmission],
    *,
    random_state: int = 20260905,
) -> tuple[BOPHeldoutResult, ...]:
    eligible = {item.individual_id for item in admissions if item.final_eligible}
    species_labels = admitted_species(admissions)
    fold_map = deterministic_folds(admissions)
    filtered = tuple(event for event in events if event.individual_id in eligible)
    results: list[BOPHeldoutResult] = []
    names = _feature_names(species_labels)

    for fold in range(5):
        fold_ids = sorted(ind for ind, value in fold_map.items() if value == fold)
        if not fold_ids:
            continue
        training = tuple(event for event in filtered if fold_map[event.individual_id] != fold)
        X_train, y_train, train_ids, train_species = feature_matrix(training, species_labels)
        weights = hierarchical_training_weights(train_ids, train_species)
        train_classes = set(y_train.tolist())
        train_species_count = len(set(train_species))

        rf = make_state_classifier(
            "random_forest",
            random_state=random_state,
            n_estimators=500,
            min_samples_leaf=25,
            max_features="sqrt",
            class_weight=None,
        )
        primary_model = fit_covariate_state_model(rf, X_train, y_train, sample_weight=weights)
        importance_raw = getattr(primary_model.estimator, "feature_importances_", None)
        importance = None
        if importance_raw is not None:
            importance = {name: float(value) for name, value in zip(names, importance_raw)}

        continuous_mean = X_train[:, : len(CONTINUOUS_FEATURE_NAMES)].mean(axis=0)
        continuous_scale = X_train[:, : len(CONTINUOUS_FEATURE_NAMES)].std(axis=0)
        logit_available = bool(np.all(np.isfinite(continuous_scale)) and np.all(continuous_scale > 0))
        sensitivity_model = None
        X_train_logit = X_train.copy()
        if logit_available:
            X_train_logit[:, : len(CONTINUOUS_FEATURE_NAMES)] = (
                X_train[:, : len(CONTINUOUS_FEATURE_NAMES)] - continuous_mean
            ) / continuous_scale
            logit = make_state_classifier(
                "multinomial_logit",
                random_state=random_state,
                C=1.0,
                solver="lbfgs",
                max_iter=3000,
            )
            sensitivity_model = fit_covariate_state_model(
                logit, X_train_logit, y_train, sample_weight=weights
            )

        for heldout in fold_ids:
            testing = tuple(event for event in filtered if event.individual_id == heldout)
            X_test, y_test, _, _ = feature_matrix(testing, species_labels)
            species = testing[0].species
            state_counts = Counter(y_test.tolist())
            if not set(y_test.tolist()).issubset(train_classes):
                results.append(
                    BOPHeldoutResult(
                        fold=fold,
                        heldout_individual=heldout,
                        species=species,
                        primary_status="unscorable_training_absent_state",
                        primary_score=None,
                        sensitivity_status="not_run_primary_unscorable",
                        sensitivity_score=None,
                        training_event_count=len(training),
                        heldout_event_count=len(testing),
                        training_individual_count=len(set(train_ids)),
                        training_species_count=train_species_count,
                        heldout_state_counts={s: int(state_counts.get(s, 0)) for s in STATE_LABELS},
                        confusion_matrix=None,
                        primary_feature_importance=importance,
                    )
                )
                continue
            primary_score = primary_model.score(X_test, y_test)
            sensitivity_status = "unavailable_zero_sd_feature"
            sensitivity_score = None
            if sensitivity_model is not None:
                X_test_logit = X_test.copy()
                X_test_logit[:, : len(CONTINUOUS_FEATURE_NAMES)] = (
                    X_test[:, : len(CONTINUOUS_FEATURE_NAMES)] - continuous_mean
                ) / continuous_scale
                sensitivity_status = "scored"
                sensitivity_score = _score_dict(sensitivity_model.score(X_test_logit, y_test))
            results.append(
                BOPHeldoutResult(
                    fold=fold,
                    heldout_individual=heldout,
                    species=species,
                    primary_status="scored",
                    primary_score=_score_dict(primary_score),
                    sensitivity_status=sensitivity_status,
                    sensitivity_score=sensitivity_score,
                    training_event_count=len(training),
                    heldout_event_count=len(testing),
                    training_individual_count=len(set(train_ids)),
                    training_species_count=train_species_count,
                    heldout_state_counts={s: int(state_counts.get(s, 0)) for s in STATE_LABELS},
                    confusion_matrix=_confusion(primary_model, X_test, y_test),
                    primary_feature_importance=importance,
                )
            )
    return tuple(sorted(results, key=lambda x: (x.fold, x.species, x.heldout_individual)))


def terminal_decision(
    admissions: Sequence[BOPIndividualAdmission],
    results: Sequence[BOPHeldoutResult],
    *,
    minimum_species: int = 3,
    minimum_individuals: int = 12,
) -> dict[str, object]:
    eligible = [item for item in admissions if item.final_eligible]
    species = sorted({item.species for item in eligible})
    if len(species) < minimum_species or len(eligible) < minimum_individuals:
        return {
            "terminal_category": "empirical_state_prediction_unavailable",
            "reason": "frozen_multi_species_admission_minimum_failed",
            "admitted_species_count": len(species),
            "eligible_individual_count": len(eligible),
            "individual_primary_gains": [],
            "species_categories": {},
        }
    if len(results) != len(eligible) or any(item.primary_status != "scored" for item in results):
        return {
            "terminal_category": "empirical_state_prediction_unavailable",
            "reason": "heldout_individual_unscorable_under_frozen_training_support",
            "admitted_species_count": len(species),
            "eligible_individual_count": len(eligible),
            "individual_primary_gains": [],
            "species_categories": {},
        }
    gains = [float(item.primary_score["mean_log_score_gain"]) for item in results if item.primary_score]
    overall = classify_independent_gains(gains, tolerance=0.0)
    terminal = {
        "generalizing": "empirical_state_prediction_generalizing",
        "non_generalizing": "empirical_state_prediction_non_generalizing",
        "mixed": "empirical_state_prediction_mixed",
    }[overall]
    by_species: dict[str, list[float]] = defaultdict(list)
    for item in results:
        by_species[item.species].append(float(item.primary_score["mean_log_score_gain"]))
    species_categories = {
        name: {
            "category": classify_independent_gains(values, tolerance=0.0),
            "gains": values,
            "mean_gain_descriptive": float(np.mean(values)),
        }
        for name, values in sorted(by_species.items())
    }
    return {
        "terminal_category": terminal,
        "reason": "frozen_all_individual_primary_rf_gain_rule",
        "admitted_species_count": len(species),
        "eligible_individual_count": len(eligible),
        "individual_primary_gains": gains,
        "positive_individual_count": int(sum(value > 0 for value in gains)),
        "nonpositive_individual_count": int(sum(value <= 0 for value in gains)),
        "mean_primary_gain_descriptive": float(np.mean(gains)),
        "minimum_primary_gain": float(np.min(gains)),
        "maximum_primary_gain": float(np.max(gains)),
        "species_categories": species_categories,
    }
