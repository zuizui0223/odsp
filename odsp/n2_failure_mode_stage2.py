"""Stage-2 real-data triangulation for the N2 pooled-reference failure mode."""
from __future__ import annotations

import csv
from dataclasses import asdict, dataclass
import hashlib
import json
import math
from pathlib import Path
from typing import Mapping, Sequence

import numpy as np

from .covariate_state_prediction import fit_covariate_state_model, make_state_classifier
from .information_transfer import (
    InformationLevelScore,
    decompose_information_transfer,
)
from .population_transfer import summarize_population_transfer


CONTRACT_FILENAME = "N2_POOLED_REFERENCE_FAILURE_MODE_STAGE2_REAL_DATA_CONTRACT.json"
FROZEN_CONTRACT_MERGE_SHA = "8a83079f395b7e22bf82d87a430d8169247bf996"
PENGUINS_UPSTREAM_COMMIT = "8957207b78d6ccd1b4654a9dd9c9041b657478ab"
MORPHOLOGY = (
    "bill_length_mm",
    "bill_depth_mm",
    "flipper_length_mm",
    "body_mass_g",
)


@dataclass(frozen=True)
class PenguinRow:
    row_id: str
    species: str
    island: str
    year: str
    morphology: tuple[float, ...]

    def as_dict(self) -> dict[str, object]:
        return asdict(self)


def load_stage2_contract(path: str | Path) -> dict[str, object]:
    value = json.loads(Path(path).read_text(encoding="utf-8"))
    if value.get("contract_id") != "n2-pooled-reference-failure-mode-stage2-real-data-v1":
        raise ValueError("unexpected N2 stage-2 contract")
    if value.get("status") != "pre_fresh_result_frozen":
        raise ValueError("N2 stage-2 contract is not frozen pre-fresh-result")
    return value


def _sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def prepare_penguins_rows(path: str | Path) -> tuple[PenguinRow, ...]:
    source = Path(path)
    rows: list[PenguinRow] = []
    with source.open("r", encoding="utf-8-sig", newline="") as handle:
        reader = csv.DictReader(handle)
        required = {"species", "island", "year", *MORPHOLOGY}
        missing = sorted(required - set(reader.fieldnames or ()))
        if missing:
            raise ValueError("penguins source missing columns: " + ", ".join(missing))
        for source_index, row in enumerate(reader):
            if any(str(row.get(name, "")).strip() in {"", "NA"} for name in required):
                continue
            try:
                morphology = tuple(float(row[name]) for name in MORPHOLOGY)
            except (TypeError, ValueError) as exc:
                raise ValueError(
                    f"penguins source row {source_index} has nonnumeric morphology"
                ) from exc
            if not all(math.isfinite(value) for value in morphology):
                raise ValueError(
                    f"penguins source row {source_index} has nonfinite morphology"
                )
            species = str(row["species"]).strip()
            island = str(row["island"]).strip()
            year = str(row["year"]).strip()
            if not species or not island or not year:
                raise ValueError("penguins categorical fields must be non-empty")
            rows.append(
                PenguinRow(
                    row_id=f"penguin-{source_index:03d}",
                    species=species,
                    island=island,
                    year=year,
                    morphology=morphology,
                )
            )
    if len(rows) < 300:
        raise ValueError("unexpectedly few complete Palmer Penguins rows")
    if len({row.species for row in rows}) != 3:
        raise ValueError("Palmer Penguins stage-2 source must contain three species")
    if len({row.island for row in rows}) != 3:
        raise ValueError("Palmer Penguins stage-2 source must contain three islands")
    if len({row.year for row in rows}) != 3:
        raise ValueError("Palmer Penguins stage-2 source must contain three years")
    return tuple(rows)


def _training_weights(rows: Sequence[PenguinRow], indices: np.ndarray) -> np.ndarray:
    species = [rows[int(index)].species for index in indices]
    counts: dict[str, int] = {}
    for value in species:
        counts[value] = counts.get(value, 0) + 1
    labels = sorted(counts)
    if not labels:
        raise ValueError("training fold contains no species")
    weight = np.asarray(
        [1.0 / (len(labels) * counts[value]) for value in species],
        dtype=float,
    )
    return weight


def _classes(rows: Sequence[PenguinRow]) -> tuple[str, ...]:
    return tuple(sorted({row.island for row in rows}))


def _species_labels(rows: Sequence[PenguinRow]) -> tuple[str, ...]:
    return tuple(sorted({row.species for row in rows}))


def _morphology_matrix(rows: Sequence[PenguinRow], indices: np.ndarray) -> np.ndarray:
    return np.asarray([rows[int(index)].morphology for index in indices], dtype=float)


def _full_matrix(
    rows: Sequence[PenguinRow],
    indices: np.ndarray,
    species_labels: Sequence[str],
) -> np.ndarray:
    labels = tuple(species_labels)
    lookup = {value: index for index, value in enumerate(labels)}
    morphology = _morphology_matrix(rows, indices)
    onehot = np.zeros((indices.size, len(labels)), dtype=float)
    for row_index, source_index in enumerate(indices.tolist()):
        species = rows[int(source_index)].species
        if species not in lookup:
            raise ValueError(f"held-out species absent from frozen encoding: {species!r}")
        onehot[row_index, lookup[species]] = 1.0
    return np.column_stack([morphology, onehot])


def _labels(rows: Sequence[PenguinRow], indices: np.ndarray) -> np.ndarray:
    return np.asarray([rows[int(index)].island for index in indices], dtype=object)


def _weighted_baselines(
    rows: Sequence[PenguinRow],
    indices: np.ndarray,
    classes: Sequence[str],
    weight: np.ndarray,
) -> tuple[np.ndarray, dict[str, np.ndarray]]:
    class_labels = tuple(classes)
    class_index = {value: index for index, value in enumerate(class_labels)}
    pooled = np.zeros(len(class_labels), dtype=float)
    by_species: dict[str, np.ndarray] = {}
    by_species_mass: dict[str, float] = {}
    for local_index, source_index in enumerate(indices.tolist()):
        row = rows[int(source_index)]
        pooled[class_index[row.island]] += float(weight[local_index])
        by_species.setdefault(row.species, np.zeros(len(class_labels), dtype=float))[
            class_index[row.island]
        ] += float(weight[local_index])
        by_species_mass[row.species] = by_species_mass.get(row.species, 0.0) + float(
            weight[local_index]
        )
    pooled /= float(np.sum(pooled))
    for species, probability in by_species.items():
        mass = by_species_mass[species]
        if not mass > 0:
            raise ValueError("species baseline has no positive training mass")
        by_species[species] = probability / mass
    return pooled, by_species


def _assigned_log(
    probability: np.ndarray,
    y: Sequence[str],
    classes: Sequence[str],
) -> np.ndarray:
    labels = tuple(classes)
    lookup = {value: index for index, value in enumerate(labels)}
    result = np.empty(len(y), dtype=float)
    for index, label in enumerate(y):
        if label not in lookup:
            raise ValueError(f"held-out island absent from training classes: {label!r}")
        value = (
            float(probability[index, lookup[label]])
            if probability.ndim == 2
            else float(probability[lookup[label]])
        )
        if value <= 0.0 or not math.isfinite(value):
            raise ValueError(
                f"held-out realized state {label!r} has zero/nonfinite baseline support"
            )
        result[index] = math.log(value)
    return result


def _mean_status(step: Mapping[str, object]) -> str:
    return str(step["mean_gain_status"])


def _comparison(
    naive: Mapping[str, object],
    corrected: Mapping[str, object],
) -> dict[str, object]:
    naive_mean = float(naive["mean_gain"])
    corrected_mean = float(corrected["mean_gain"])
    point_reversal = bool(naive_mean > 0.0 and corrected_mean <= 0.0)
    downgrade = bool(_mean_status(naive) == "positive" and _mean_status(corrected) != "positive")
    attenuation = bool(
        naive_mean > 0.0
        and abs(corrected_mean) <= 0.5 * abs(naive_mean)
    )
    if point_reversal or downgrade:
        category = "fresh_empirical_reversal"
    elif attenuation:
        category = "fresh_empirical_attenuation"
    else:
        category = "fresh_empirical_no_support"
    return {
        "naive_mean_gain": naive_mean,
        "naive_mean_status": _mean_status(naive),
        "corrected_context_mean_gain": corrected_mean,
        "corrected_context_mean_status": _mean_status(corrected),
        "point_sign_reversal": point_reversal,
        "inferential_downgrade": downgrade,
        "strong_attenuation": attenuation,
        "fresh_penguins_decision": category,
    }


def run_penguins_stage2(
    source_path: str | Path,
    *,
    contract: Mapping[str, object],
) -> dict[str, object]:
    rows = prepare_penguins_rows(source_path)
    penguins_contract = next(
        row for row in contract["systems"] if row["system_id"] == "PALMER_PENGUINS"
    )
    learner = penguins_contract["learner"]
    parameters = dict(learner["parameters"])
    random_state = int(learner["random_state"])

    classes = _classes(rows)
    species_labels = _species_labels(rows)
    years = tuple(sorted({row.year for row in rows}))
    n = len(rows)

    pooled_log = np.empty(n, dtype=float)
    species_log = np.empty(n, dtype=float)
    naive_log = np.empty(n, dtype=float)
    full_log = np.empty(n, dtype=float)

    for year in years:
        test_index = np.asarray(
            [index for index, row in enumerate(rows) if row.year == year], dtype=int
        )
        train_index = np.asarray(
            [index for index, row in enumerate(rows) if row.year != year], dtype=int
        )
        weight = _training_weights(rows, train_index)
        y_train = _labels(rows, train_index)
        y_test = _labels(rows, test_index)

        naive_estimator = make_state_classifier(
            "random_forest",
            random_state=random_state,
            **parameters,
        )
        naive_model = fit_covariate_state_model(
            naive_estimator,
            _morphology_matrix(rows, train_index),
            y_train,
            sample_weight=weight,
        )
        full_estimator = make_state_classifier(
            "random_forest",
            random_state=random_state,
            **parameters,
        )
        full_model = fit_covariate_state_model(
            full_estimator,
            _full_matrix(rows, train_index, species_labels),
            y_train,
            sample_weight=weight,
        )

        if tuple(str(value) for value in naive_model.classes) != classes:
            raise ValueError("naive model training classes differ from frozen island classes")
        if tuple(str(value) for value in full_model.classes) != classes:
            raise ValueError("audit model training classes differ from frozen island classes")

        pooled, by_species = _weighted_baselines(rows, train_index, classes, weight)
        for source_index in test_index.tolist():
            if rows[source_index].species not in by_species:
                raise ValueError("held-out species absent from training fold")

        naive_probability = naive_model.predict_proba(
            _morphology_matrix(rows, test_index)
        )
        full_probability = full_model.predict_proba(
            _full_matrix(rows, test_index, species_labels)
        )
        pooled_log[test_index] = _assigned_log(pooled, y_test.tolist(), classes)
        species_log[test_index] = np.asarray(
            [
                _assigned_log(
                    by_species[rows[int(source_index)].species],
                    [rows[int(source_index)].island],
                    classes,
                )[0]
                for source_index in test_index.tolist()
            ],
            dtype=float,
        )
        naive_log[test_index] = _assigned_log(
            naive_probability, y_test.tolist(), classes
        )
        full_log[test_index] = _assigned_log(
            full_probability, y_test.tolist(), classes
        )

    if any(
        np.any(~np.isfinite(value))
        for value in (pooled_log, species_log, naive_log, full_log)
    ):
        raise ValueError("fresh Palmer Penguins score table contains nonfinite values")

    group = [row.row_id for row in rows]
    year_cluster = {row.row_id: row.year for row in rows}

    naive_point = decompose_information_transfer(
        (
            InformationLevelScore("pooled", (), pooled_log),
            InformationLevelScore("morphology", ("morphology",), naive_log),
        ),
        group,
        score_name="heldout_log_probability",
    )
    naive_population = summarize_population_transfer(
        naive_point,
        group_clusters=year_cluster,
        confidence_level=0.95,
        bootstrap_draws=4000,
        seed=20260913,
        gain_tolerance=0.0,
    )

    audit_point = decompose_information_transfer(
        (
            InformationLevelScore("pooled", (), pooled_log),
            InformationLevelScore("species", ("species",), species_log),
            InformationLevelScore(
                "species_morphology",
                ("species", "morphology"),
                full_log,
            ),
        ),
        group,
        score_name="heldout_log_probability",
    )
    audit_population = summarize_population_transfer(
        audit_point,
        group_clusters=year_cluster,
        confidence_level=0.95,
        bootstrap_draws=4000,
        seed=20260913,
        gain_tolerance=0.0,
    )

    corrected = audit_population.steps[1]
    return {
        "source_sha256": _sha256(Path(source_path)),
        "source_upstream_commit": PENGUINS_UPSTREAM_COMMIT,
        "prepared_row_count": len(rows),
        "species": list(species_labels),
        "islands": list(classes),
        "years": list(years),
        "naive_point_result": naive_point.as_dict(),
        "audit_point_result": audit_point.as_dict(),
        "naive_population_result": naive_population.as_dict(),
        "audit_population_result": audit_population.as_dict(),
        "comparison": _comparison(
            naive_population.total_gain.as_dict(),
            corrected.as_dict(),
        ),
        "scientific_boundary": {
            "species_is_the_declared_layer": True,
            "naive_model_omits_species": True,
            "audit_full_model_includes_species": True,
            "naive_and_audit_models_are_not_an_additive_identity": True,
            "causal_morphology_claim_supported": False,
        },
    }


def stage2_synthesis(
    penguins_result: Mapping[str, object],
    *,
    bop_v2_receipt: Mapping[str, object],
    serengeti_receipt: Mapping[str, object],
) -> dict[str, object]:
    bop_population = bop_v2_receipt["population_result"]
    bop_total = bop_population["total_gain"]
    bop_context = bop_population["steps"][1]
    bop_comparison = _comparison(bop_total, bop_context)

    systems = {
        "BOP_RODENT": {
            "failure_mode_eligible": True,
            "fresh": False,
            "comparison": bop_comparison,
            "population_cluster_count": bop_population["cluster_count"],
        },
        "PALMER_PENGUINS": {
            "failure_mode_eligible": True,
            "fresh": True,
            "comparison": penguins_result["comparison"],
            "population_cluster_count": penguins_result[
                "naive_population_result"
            ]["cluster_count"],
        },
        "SNAPSHOT_SERENGETI": {
            "failure_mode_eligible": False,
            "fresh": False,
            "terminal_category": serengeti_receipt["terminal_category"],
            "transfer_category": serengeti_receipt["transfer_category"],
            "heldout_gains": serengeti_receipt["heldout_gains"],
            "semantic_control": (
                "species identity is itself the claimed transferred information; "
                "the species-blind pooled temporal reference is therefore appropriate"
            ),
        },
    }

    eligible = [systems["BOP_RODENT"], systems["PALMER_PENGUINS"]]
    return {
        "systems": systems,
        "descriptive_counts": {
            "failure_eligible_system_count": 2,
            "point_sign_reversal_count": int(
                sum(bool(row["comparison"]["point_sign_reversal"]) for row in eligible)
            ),
            "inferential_downgrade_count": int(
                sum(bool(row["comparison"]["inferential_downgrade"]) for row in eligible)
            ),
            "strong_attenuation_count": int(
                sum(bool(row["comparison"]["strong_attenuation"]) for row in eligible)
            ),
            "prevalence_or_meta_analytic_rate_claimed": False,
        },
        "fresh_penguins_decision": penguins_result["comparison"][
            "fresh_penguins_decision"
        ],
        "stage1_full_claim_reclassified": False,
        "stage2_estimates_literature_prevalence": False,
    }
