"""Known-truth benchmark for the predictive-resolution decomposition."""
from __future__ import annotations

from dataclasses import asdict, dataclass
import math

import numpy as np

from .predictive_resolution import decompose_predictive_resolution


@dataclass(frozen=True)
class PredictiveResolutionBenchmark:
    oracle_species_information: float
    oracle_context_information: float
    misspecified_full_kl_penalty: float
    misspecified_species_increment: float
    misspecified_context_increment: float
    misspecified_total_gain: float
    oracle_additivity_error: float
    misspecified_additivity_error: float
    oracle_information_identity_error: float
    misspecification_identity_error: float
    total_positive_context_negative_recovered: bool

    def as_dict(self) -> dict[str, object]:
        return asdict(self)


def _sigmoid(value: float) -> float:
    return 1.0 / (1.0 + math.exp(-value))


def _binary_log_score(probability_one: float, outcome: int) -> float:
    probability = probability_one if outcome == 1 else 1.0 - probability_one
    return math.log(probability)


def _binary_kl(true_probability: float, fitted_probability: float) -> float:
    p = true_probability
    q = fitted_probability
    return (
        p * math.log(p / q)
        + (1.0 - p) * math.log((1.0 - p) / (1.0 - q))
    )


def run_predictive_resolution_benchmark(
    *,
    species_effect: float = 1.2,
    context_effect: float = 0.4,
    misspecified_context_effect: float = 0.5,
) -> PredictiveResolutionBenchmark:
    """Run an exact finite-state benchmark with known oracle information.

    Species is a strong predictor of a binary ecological state and context adds a
    weaker effect. The oracle ladder therefore has two positive information
    increments. A deliberately misspecified richest predictor reverses the
    context effect while retaining the species effect. It remains better than
    the pooled comparator overall but worse than the species-only comparator,
    reproducing the positive-total/negative-context pattern without sampling
    error.
    """

    if species_effect <= 0 or context_effect <= 0 or misspecified_context_effect <= 0:
        raise ValueError("benchmark effects must be strictly positive")

    alpha = {0: -float(species_effect), 1: float(species_effect)}
    context_values = (-1, 1)
    species_values = (0, 1)
    true_probability = {
        (species, context): _sigmoid(alpha[species] + context_effect * context)
        for species in species_values
        for context in context_values
    }
    species_probability = {
        species: float(
            np.mean(
                [true_probability[(species, context)] for context in context_values]
            )
        )
        for species in species_values
    }
    pooled_probability = float(np.mean(list(species_probability.values())))

    pooled_score: list[float] = []
    species_score: list[float] = []
    oracle_score: list[float] = []
    misspecified_score: list[float] = []
    groups: list[str] = []
    weights: list[float] = []
    kl_weighted = 0.0

    for species in species_values:
        for context in context_values:
            truth = true_probability[(species, context)]
            wrong = _sigmoid(
                alpha[species] - misspecified_context_effect * context
            )
            cell_weight = 1.0 / (len(species_values) * len(context_values))
            kl_weighted += cell_weight * _binary_kl(truth, wrong)
            for outcome in (0, 1):
                outcome_probability = truth if outcome == 1 else 1.0 - truth
                weights.append(cell_weight * outcome_probability)
                groups.append(f"species-{species}")
                pooled_score.append(_binary_log_score(pooled_probability, outcome))
                species_score.append(
                    _binary_log_score(species_probability[species], outcome)
                )
                oracle_score.append(_binary_log_score(truth, outcome))
                misspecified_score.append(_binary_log_score(wrong, outcome))

    oracle = decompose_predictive_resolution(
        (
            ("pooled", pooled_score),
            ("species", species_score),
            ("species+context", oracle_score),
        ),
        groups,
        sample_weight=weights,
    )
    misspecified = decompose_predictive_resolution(
        (
            ("pooled", pooled_score),
            ("species", species_score),
            ("species+context", misspecified_score),
        ),
        groups,
        sample_weight=weights,
    )

    oracle_species = float(
        np.mean([row.increments[0].mean_gain for row in oracle.groups])
    )
    oracle_context = float(
        np.mean([row.increments[1].mean_gain for row in oracle.groups])
    )
    bad_species = float(
        np.mean([row.increments[0].mean_gain for row in misspecified.groups])
    )
    bad_context = float(
        np.mean([row.increments[1].mean_gain for row in misspecified.groups])
    )
    bad_total = float(np.mean([row.total_gain for row in misspecified.groups]))

    oracle_identity_error = max(
        abs(row.total_gain - sum(step.mean_gain for step in row.increments))
        for row in oracle.groups
    )
    bad_identity_error = max(
        abs(row.total_gain - sum(step.mean_gain for step in row.increments))
        for row in misspecified.groups
    )
    misspecification_identity_error = abs(
        bad_context - (oracle_context - kl_weighted)
    )

    return PredictiveResolutionBenchmark(
        oracle_species_information=oracle_species,
        oracle_context_information=oracle_context,
        misspecified_full_kl_penalty=float(kl_weighted),
        misspecified_species_increment=bad_species,
        misspecified_context_increment=bad_context,
        misspecified_total_gain=bad_total,
        oracle_additivity_error=float(
            max(abs(row.additivity_error) for row in oracle.groups)
        ),
        misspecified_additivity_error=float(
            max(abs(row.additivity_error) for row in misspecified.groups)
        ),
        oracle_information_identity_error=float(oracle_identity_error),
        misspecification_identity_error=float(misspecification_identity_error),
        total_positive_context_negative_recovered=bool(
            bad_total > 0.0 and bad_context < 0.0
        ),
    )
