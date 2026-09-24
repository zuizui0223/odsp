"""Fresh Palmer Penguins audit for frozen N2 stage-2 real-data triangulation."""
from __future__ import annotations

from dataclasses import asdict, dataclass
import csv
import hashlib
import json
import math
from pathlib import Path
from typing import Mapping, Sequence

import numpy as np

from .covariate_state_prediction import fit_covariate_state_model, make_state_classifier
from .population_transfer import PopulationTransferStep, _summarize_gain_vector


FROZEN_STAGE2_CONTRACT_MERGE_SHA = "8a83079f395b7e22bf82d87a430d8169247bf996"
SOURCE_COMMIT = "8957207b78d6ccd1b4654a9dd9c9041b657478ab"
FEATURES = (
    "bill_length_mm",
    "bill_depth_mm",
    "flipper_length_mm",
    "body_mass_g",
)


@dataclass(frozen=True)
class PenguinPreparedRow:
    row_id: str
    species: str
    island: str
    year: str
    features: tuple[float, ...]

    def as_dict(self) -> dict[str, object]:
        return asdict(self)


def load_stage2_contract(path: str | Path) -> dict[str, object]:
    value = json.loads(Path(path).read_text(encoding="utf-8"))
    if value.get("contract_id") != "n2-pooled-reference-failure-mode-stage2-real-data-v1":
        raise ValueError("unexpected N2 stage-2 contract")
    if value.get("status") != "pre_fresh_result_frozen":
        raise ValueError("N2 stage-2 contract is not frozen pre-result")
    prerequisite = value["prerequisites"]["few_cluster_fix_merge_sha"]
    if prerequisite != "6bc65a1a5575d61835838e711d6f0221af320034":
        raise ValueError("stage-2 contract is not bound to the corrected few-cluster rule")
    return value


def _sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def prepare_penguins(path: str | Path) -> tuple[PenguinPreparedRow, ...]:
    source = Path(path)
    with source.open("r", encoding="utf-8-sig", newline="") as handle:
        rows = list(csv.DictReader(handle))
    prepared: list[PenguinPreparedRow] = []
    for index, row in enumerate(rows):
        required_text = ("species", "island", "year")
        if any(not str(row.get(name, "")).strip() for name in required_text):
            continue
        raw_features = [str(row.get(name, "")).strip() for name in FEATURES]
        if any(value in {"", "NA", "NaN", "nan"} for value in raw_features):
            continue
        try:
            features = tuple(float(value) for value in raw_features)
        except ValueError:
            continue
        if not all(math.isfinite(value) for value in features):
            continue
        prepared.append(
            PenguinPreparedRow(
                row_id=f"penguin-{index:03d}",
                species=str(row["species"]).strip(),
                island=str(row["island"]).strip(),
                year=str(row["year"]).strip(),
                features=features,
            )
        )
    if not prepared:
        raise ValueError("no complete Palmer Penguins rows remain")
    return tuple(prepared)


def _training_weights(species: np.ndarray) -> np.ndarray:
    values = species.tolist()
    labels = tuple(sorted(set(values)))
    if len(labels) < 2:
        raise ValueError("at least two training species are required")
    counts = {label: values.count(label) for label in labels}
    return np.asarray(
        [1.0 / (len(labels) * counts[value]) for value in values],
        dtype=float,
    )


def _weighted_distribution(
    labels: np.ndarray,
    weights: np.ndarray,
    classes: tuple[object, ...],
) -> np.ndarray:
    lookup = {value: index for index, value in enumerate(classes)}
    result = np.zeros(len(classes), dtype=float)
    for label, weight in zip(labels.tolist(), weights.tolist()):
        if label not in lookup:
            raise ValueError(f"training label absent from canonical classes: {label!r}")
        result[lookup[label]] += float(weight)
    total = float(np.sum(result))
    if not total > 0:
        raise ValueError("baseline training mass must be positive")
    return result / total


def _species_distributions(
    state: np.ndarray,
    species: np.ndarray,
    weights: np.ndarray,
    classes: tuple[object, ...],
) -> dict[object, np.ndarray]:
    result: dict[object, np.ndarray] = {}
    for value in sorted(set(species.tolist())):
        mask = species == value
        result[value] = _weighted_distribution(
            state[mask],
            weights[mask],
            classes,
        )
    return result


def _assigned_log_probability(
    probability: np.ndarray,
    state: np.ndarray,
    classes: tuple[object, ...],
) -> np.ndarray:
    lookup = {value: index for index, value in enumerate(classes)}
    result = np.empty(state.size, dtype=float)
    for index, value in enumerate(state.tolist()):
        if value not in lookup:
            raise ValueError(f"held-out island absent from training classes: {value!r}")
        if probability.ndim == 1:
            p = float(probability[lookup[value]])
        else:
            p = float(probability[index, lookup[value]])
        if not p > 0.0:
            raise ValueError("held-out state receives zero predictive probability")
        result[index] = math.log(p)
    return result


def _full_features(
    morphology: np.ndarray,
    species: np.ndarray,
    species_labels: tuple[str, ...],
) -> np.ndarray:
    lookup = {value: index for index, value in enumerate(species_labels)}
    onehot = np.zeros((morphology.shape[0], len(species_labels)), dtype=float)
    for row, value in enumerate(species.tolist()):
        if value not in lookup:
            raise ValueError(f"held-out species absent from training: {value!r}")
        onehot[row, lookup[value]] = 1.0
    return np.column_stack([onehot, morphology])


def _cluster_map(years: Sequence[str]) -> tuple[tuple[str, ...], dict[str, np.ndarray]]:
    labels = tuple(dict.fromkeys(years))
    indices = {
        value: np.asarray(
            [index for index, year in enumerate(years) if year == value],
            dtype=int,
        )
        for value in labels
    }
    return labels, indices


def _summarize(
    values: Sequence[float],
    *,
    lower_level: str,
    upper_level: str,
    years: Sequence[str],
    confidence_level: float,
    seed: int,
) -> PopulationTransferStep:
    labels, indices = _cluster_map(years)
    return _summarize_gain_vector(
        values,
        lower_level=lower_level,
        upper_level=upper_level,
        cluster_labels=labels,
        cluster_indices=indices,
        cluster_variable_declared=True,
        confidence_level=confidence_level,
        bootstrap_draws=4000,
        seed=seed,
        gain_tolerance=0.0,
    )


def run_penguins_stage2(
    raw_csv: str | Path,
    contract_path: str | Path,
) -> dict[str, object]:
    contract = load_stage2_contract(contract_path)
    system = next(
        row for row in contract["systems"] if row["system_id"] == "PALMER_PENGUINS"
    )
    rows = prepare_penguins(raw_csv)
    years = tuple(sorted({row.year for row in rows}))
    species_labels = tuple(sorted({row.species for row in rows}))
    if len(years) != 3:
        raise ValueError(f"frozen Palmer Penguins analysis expects three years, observed {years!r}")
    if len(species_labels) != 3:
        raise ValueError(
            f"frozen Palmer Penguins analysis expects three species, observed {species_labels!r}"
        )

    morphology = np.asarray([row.features for row in rows], dtype=float)
    state = np.asarray([row.island for row in rows], dtype=object)
    species = np.asarray([row.species for row in rows], dtype=object)
    year = np.asarray([row.year for row in rows], dtype=object)

    naive_pooled = np.empty(len(rows), dtype=float)
    audit_layer = np.empty(len(rows), dtype=float)
    audit_context = np.empty(len(rows), dtype=float)
    audit_total = np.empty(len(rows), dtype=float)
    naive_score = np.empty(len(rows), dtype=float)
    full_score = np.empty(len(rows), dtype=float)
    pooled_score = np.empty(len(rows), dtype=float)
    species_score = np.empty(len(rows), dtype=float)

    model_spec = system["learner"]
    parameters = dict(model_spec["parameters"])
    random_state = int(model_spec["random_state"])

    for fold_year in years:
        test = year == fold_year
        train = ~test
        train_weights = _training_weights(species[train])

        naive_estimator = make_state_classifier(
            str(model_spec["kind"]),
            random_state=random_state,
            **parameters,
        )
        naive_model = fit_covariate_state_model(
            naive_estimator,
            morphology[train],
            state[train],
            sample_weight=train_weights,
        )
        classes = tuple(naive_model.classes)

        full_estimator = make_state_classifier(
            str(model_spec["kind"]),
            random_state=random_state,
            **parameters,
        )
        full_model = fit_covariate_state_model(
            full_estimator,
            _full_features(morphology[train], species[train], species_labels),
            state[train],
            sample_weight=train_weights,
        )
        if tuple(full_model.classes) != classes:
            raise ValueError("naive and audit full models learned different island classes")

        pooled_probability = _weighted_distribution(
            state[train],
            train_weights,
            classes,
        )
        by_species = _species_distributions(
            state[train],
            species[train],
            train_weights,
            classes,
        )
        for value in set(species[test].tolist()):
            if value not in by_species:
                raise ValueError(f"held-out species absent from training: {value!r}")

        naive_probability = naive_model.predict_proba(morphology[test])
        full_probability = full_model.predict_proba(
            _full_features(morphology[test], species[test], species_labels)
        )
        local_state = state[test]
        naive_log = _assigned_log_probability(naive_probability, local_state, classes)
        full_log = _assigned_log_probability(full_probability, local_state, classes)
        pooled_log = _assigned_log_probability(
            pooled_probability,
            local_state,
            classes,
        )
        species_log = np.empty(int(np.sum(test)), dtype=float)
        local_species = species[test]
        for local_index, species_value in enumerate(local_species.tolist()):
            species_log[local_index] = _assigned_log_probability(
                by_species[species_value],
                np.asarray([local_state[local_index]], dtype=object),
                classes,
            )[0]

        naive_score[test] = naive_log
        full_score[test] = full_log
        pooled_score[test] = pooled_log
        species_score[test] = species_log
        naive_pooled[test] = naive_log - pooled_log
        audit_layer[test] = species_log - pooled_log
        audit_context[test] = full_log - species_log
        audit_total[test] = full_log - pooled_log

    additivity_error = float(np.max(np.abs(audit_total - audit_layer - audit_context)))
    if additivity_error > 1e-12:
        raise AssertionError("Penguins audit additive identity failed")

    year_values = year.tolist()
    confidence = float(contract["uncertainty"].get("confidence_level", 0.95))
    naive_summary = _summarize(
        naive_pooled,
        lower_level="pooled",
        upper_level="morphology",
        years=year_values,
        confidence_level=confidence,
        seed=20260924,
    )
    layer_summary = _summarize(
        audit_layer,
        lower_level="pooled",
        upper_level="species",
        years=year_values,
        confidence_level=confidence,
        seed=20260925,
    )
    context_summary = _summarize(
        audit_context,
        lower_level="species",
        upper_level="species_morphology",
        years=year_values,
        confidence_level=confidence,
        seed=20260926,
    )
    audit_total_summary = _summarize(
        audit_total,
        lower_level="pooled",
        upper_level="species_morphology",
        years=year_values,
        confidence_level=confidence,
        seed=20260927,
    )

    point_sign_reversal = bool(
        naive_summary.mean_gain > 0.0 and context_summary.mean_gain <= 0.0
    )
    inferential_downgrade = bool(
        naive_summary.mean_gain_status == "positive"
        and context_summary.mean_gain_status != "positive"
    )
    strong_attenuation = bool(
        naive_summary.mean_gain > 0.0
        and abs(context_summary.mean_gain)
        <= 0.5 * abs(naive_summary.mean_gain)
    )
    if point_sign_reversal or inferential_downgrade:
        decision = "fresh_empirical_reversal"
    elif strong_attenuation:
        decision = "fresh_empirical_attenuation"
    else:
        decision = "fresh_empirical_no_support"

    return {
        "schema_version": 1,
        "result_id": "n2-stage2-palmer-penguins-v1",
        "contract_id": contract["contract_id"],
        "contract_merge_sha": FROZEN_STAGE2_CONTRACT_MERGE_SHA,
        "system_id": "PALMER_PENGUINS",
        "fresh_outcome": True,
        "source": {
            "upstream_commit": SOURCE_COMMIT,
            "raw_csv_sha256": _sha256(Path(raw_csv)),
            "prepared_row_count": len(rows),
            "years": list(years),
            "species": list(species_labels),
        },
        "naive_pooled_gain": naive_summary.as_dict(),
        "audit_layer_component": layer_summary.as_dict(),
        "audit_context_gain": context_summary.as_dict(),
        "audit_total_gain": audit_total_summary.as_dict(),
        "audit_additivity_max_abs_error": additivity_error,
        "decision_components": {
            "point_sign_reversal": point_sign_reversal,
            "inferential_downgrade": inferential_downgrade,
            "strong_attenuation": strong_attenuation,
        },
        "decision": decision,
        "scientific_boundary": {
            "species_layer_is_causal": False,
            "morphology_determines_island_causally": False,
            "result_estimates_literature_prevalence": False,
            "stage1_claim_reclassified": False,
        },
    }
