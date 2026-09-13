"""Descriptive species-baseline decomposition for the frozen BOP_RODENT endpoint.

This module does not refit the prospective model and does not redefine the frozen
primary comparator.  It reconstructs the exact hierarchical training marginals
from the frozen result artifact and decomposes each already-frozen primary gain
into a species-baseline component plus a within-species context component.
"""
from __future__ import annotations

from collections import defaultdict
from dataclasses import asdict, dataclass
import math
from typing import Mapping, Sequence

import numpy as np

from .mh_antwerpen_prediction import STATE_LABELS


@dataclass(frozen=True)
class BOPSpeciesBaselineRow:
    fold: int
    heldout_individual: str
    species: str
    heldout_event_count: int
    heldout_state_counts: dict[str, int]
    pooled_training_marginal: dict[str, float]
    species_training_marginal: dict[str, float]
    mean_log_model: float
    mean_log_pooled_baseline: float
    mean_log_species_baseline: float
    total_gain_frozen: float
    species_component: float
    context_within_species_component: float
    pooled_baseline_reconstruction_error: float
    additivity_error: float

    def as_dict(self) -> dict[str, object]:
        return asdict(self)


def _state_distribution(
    counts: Mapping[str, object], state_labels: Sequence[str]
) -> np.ndarray:
    values = np.asarray([float(counts.get(state, 0)) for state in state_labels], dtype=float)
    if not np.isfinite(values).all() or np.any(values < 0):
        raise ValueError("state counts must be finite and non-negative")
    total = float(values.sum())
    if not total > 0:
        raise ValueError("state counts must have positive total mass")
    return values / total


def reconstruct_fold_training_marginals(
    admissions: Sequence[Mapping[str, object]],
    fold_assignment: Mapping[str, object],
    heldout_fold: int,
    *,
    state_labels: Sequence[str] = STATE_LABELS,
) -> tuple[dict[str, np.ndarray], np.ndarray]:
    """Reconstruct the frozen hierarchical species and pooled marginals.

    The original endpoint gave each admitted species equal total training weight
    and each training individual equal total weight within species.  Conditional
    on species, the resulting marginal is therefore the arithmetic mean of each
    training individual's own state-frequency vector.  The pooled marginal is
    the arithmetic mean of those species marginals.
    """

    eligible: list[Mapping[str, object]] = []
    seen_ids: set[str] = set()
    for admission in admissions:
        if not bool(admission.get("final_eligible", False)):
            continue
        individual = str(admission["individual_id"])
        if individual in seen_ids:
            raise ValueError(f"duplicate eligible individual: {individual!r}")
        seen_ids.add(individual)
        if individual not in fold_assignment:
            raise ValueError(f"missing frozen fold assignment for {individual!r}")
        if int(fold_assignment[individual]) != heldout_fold:
            eligible.append(admission)

    by_species: dict[str, list[np.ndarray]] = defaultdict(list)
    for admission in eligible:
        species = str(admission["species"])
        by_species[species].append(
            _state_distribution(admission["state_counts"], state_labels)
        )
    if len(by_species) < 2:
        raise ValueError("at least two training species are required")

    species_marginals = {
        species: np.mean(np.vstack(vectors), axis=0)
        for species, vectors in sorted(by_species.items())
    }
    pooled = np.mean(np.vstack(list(species_marginals.values())), axis=0)
    return species_marginals, pooled


def _mean_log_probability(
    heldout_counts: Mapping[str, object],
    probability: np.ndarray,
    state_labels: Sequence[str],
) -> float:
    observed = _state_distribution(heldout_counts, state_labels)
    positive_observed = observed > 0
    if np.any(probability[positive_observed] <= 0):
        return float("-inf")
    return float(np.dot(observed[positive_observed], np.log(probability[positive_observed])))


def decompose_frozen_bop_gains(
    frozen_result: Mapping[str, object],
    *,
    reconstruction_tolerance: float = 1e-10,
    additivity_tolerance: float = 1e-12,
    state_labels: Sequence[str] = STATE_LABELS,
) -> dict[str, object]:
    """Decompose already-frozen BOP gains without refitting any prediction model."""

    admissions = frozen_result.get("admissions")
    fold_assignment = frozen_result.get("fold_assignment")
    heldout_results = frozen_result.get("heldout_results")
    if not isinstance(admissions, list):
        raise ValueError("frozen result admissions must be a list")
    if not isinstance(fold_assignment, Mapping):
        raise ValueError("frozen result fold_assignment must be a mapping")
    if not isinstance(heldout_results, list):
        raise ValueError("frozen result heldout_results must be a list")

    eligible = [row for row in admissions if bool(row.get("final_eligible", False))]
    eligible_by_id = {str(row["individual_id"]): row for row in eligible}
    if len(eligible_by_id) != len(eligible):
        raise ValueError("eligible admission identifiers must be unique")

    fold_cache: dict[int, tuple[dict[str, np.ndarray], np.ndarray]] = {}
    rows: list[BOPSpeciesBaselineRow] = []
    for heldout in heldout_results:
        if str(heldout.get("primary_status")) != "scored":
            raise ValueError("all amendment rows require the frozen primary result to be scored")
        primary_score = heldout.get("primary_score")
        if not isinstance(primary_score, Mapping):
            raise ValueError("scored held-out result is missing primary_score")
        fold = int(heldout["fold"])
        individual = str(heldout["heldout_individual"])
        species = str(heldout["species"])
        if individual not in eligible_by_id:
            raise ValueError(f"held-out individual absent from eligible admissions: {individual!r}")
        if str(eligible_by_id[individual]["species"]) != species:
            raise ValueError("held-out species disagrees with frozen admission")
        if int(fold_assignment[individual]) != fold:
            raise ValueError("held-out fold disagrees with frozen fold assignment")
        if fold not in fold_cache:
            fold_cache[fold] = reconstruct_fold_training_marginals(
                admissions, fold_assignment, fold, state_labels=state_labels
            )
        species_marginals, pooled = fold_cache[fold]
        if species not in species_marginals:
            raise ValueError(f"held-out species absent from training fold: {species!r}")
        species_marginal = species_marginals[species]
        heldout_counts = heldout["heldout_state_counts"]
        mean_log_pool = _mean_log_probability(heldout_counts, pooled, state_labels)
        mean_log_species = _mean_log_probability(
            heldout_counts, species_marginal, state_labels
        )
        mean_log_model = float(primary_score["mean_log_score"])
        frozen_mean_log_pool = float(primary_score["mean_marginal_log_score"])
        total_gain = float(primary_score["mean_log_score_gain"])
        reconstruction_error = mean_log_pool - frozen_mean_log_pool
        if not abs(reconstruction_error) <= reconstruction_tolerance:
            raise AssertionError(
                f"pooled baseline reconstruction failed for {individual}: {reconstruction_error}"
            )
        species_component = mean_log_species - mean_log_pool
        context_component = mean_log_model - mean_log_species
        additivity_error = total_gain - (species_component + context_component)
        if not abs(additivity_error) <= additivity_tolerance:
            raise AssertionError(
                f"gain decomposition failed for {individual}: {additivity_error}"
            )
        rows.append(
            BOPSpeciesBaselineRow(
                fold=fold,
                heldout_individual=individual,
                species=species,
                heldout_event_count=int(heldout["heldout_event_count"]),
                heldout_state_counts={
                    state: int(heldout_counts.get(state, 0)) for state in state_labels
                },
                pooled_training_marginal={
                    state: float(pooled[index]) for index, state in enumerate(state_labels)
                },
                species_training_marginal={
                    state: float(species_marginal[index])
                    for index, state in enumerate(state_labels)
                },
                mean_log_model=mean_log_model,
                mean_log_pooled_baseline=mean_log_pool,
                mean_log_species_baseline=mean_log_species,
                total_gain_frozen=total_gain,
                species_component=species_component,
                context_within_species_component=context_component,
                pooled_baseline_reconstruction_error=reconstruction_error,
                additivity_error=additivity_error,
            )
        )

    rows.sort(key=lambda row: (row.fold, row.species, row.heldout_individual))
    if len(rows) != len(eligible):
        raise ValueError("held-out result count does not match frozen eligible individual count")

    species_names = sorted({row.species for row in rows})
    species_summary: dict[str, object] = {}
    for species in species_names:
        subset = [row for row in rows if row.species == species]
        frozen_species_admissions = [
            admission for admission in eligible if str(admission["species"]) == species
        ]
        allfold_counts = {
            state: int(
                sum(int(admission["state_counts"].get(state, 0)) for admission in frozen_species_admissions)
            )
            for state in state_labels
        }
        heldout_counts = {
            state: int(sum(row.heldout_state_counts[state] for row in subset))
            for state in state_labels
        }
        species_summary[species] = {
            "individual_count": len(subset),
            "mean_total_gain": float(np.mean([row.total_gain_frozen for row in subset])),
            "mean_species_component": float(
                np.mean([row.species_component for row in subset])
            ),
            "mean_context_within_species_component": float(
                np.mean([row.context_within_species_component for row in subset])
            ),
            "positive_species_component_count": int(
                sum(row.species_component > 0 for row in subset)
            ),
            "positive_context_component_count": int(
                sum(row.context_within_species_component > 0 for row in subset)
            ),
            "eligible_allfold_state_counts": allfold_counts,
            "heldout_state_counts": heldout_counts,
        }

    overall = {
        "individual_count": len(rows),
        "mean_total_gain": float(np.mean([row.total_gain_frozen for row in rows])),
        "mean_species_component": float(np.mean([row.species_component for row in rows])),
        "mean_context_within_species_component": float(
            np.mean([row.context_within_species_component for row in rows])
        ),
        "positive_species_component_count": int(sum(row.species_component > 0 for row in rows)),
        "positive_context_component_count": int(
            sum(row.context_within_species_component > 0 for row in rows)
        ),
        "max_abs_pooled_baseline_reconstruction_error": float(
            max(abs(row.pooled_baseline_reconstruction_error) for row in rows)
        ),
        "max_abs_additivity_error": float(max(abs(row.additivity_error) for row in rows)),
    }

    return {
        "state_order": list(state_labels),
        "individual_rows": [row.as_dict() for row in rows],
        "species_summary": species_summary,
        "overall_summary": overall,
        "primary_terminal_decision_recomputed": False,
        "primary_terminal_decision_changed": False,
    }
