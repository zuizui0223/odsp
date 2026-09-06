"""Deterministic known-truth benchmark for group-safe forecast stacking."""
from __future__ import annotations

import math

import numpy as np

from .forecast_stacking import (
    evaluate_stacked_forecast,
    fit_log_score_stacking,
    stacked_log_density,
)


def _normal_logpdf(y: np.ndarray, mean: float, sd: float) -> np.ndarray:
    return -0.5 * math.log(2.0 * math.pi * sd * sd) - 0.5 * ((y - mean) / sd) ** 2


def _candidate_log_density(y: np.ndarray) -> np.ndarray:
    return np.column_stack(
        [
            _normal_logpdf(y, -2.0, 0.7),
            _normal_logpdf(y, 2.0, 0.7),
            _normal_logpdf(y, 0.0, 3.0),
        ]
    )


def _marginal_log_density(y: np.ndarray) -> np.ndarray:
    return _normal_logpdf(y, 0.0, 3.0)


def _draw_complementary(rng: np.random.Generator, n: int) -> np.ndarray:
    component = rng.integers(0, 2, n)
    return np.where(
        component == 0,
        rng.normal(-2.0, 0.7, n),
        rng.normal(2.0, 0.7, n),
    )


def _validation_matrix(
    rng: np.random.Generator,
    *,
    group_count: int,
    rows_per_group: int,
    family: str,
) -> tuple[np.ndarray, tuple[str, ...]]:
    values: list[np.ndarray] = []
    groups: list[str] = []
    for group_index in range(group_count):
        if family == "complementary_stable":
            y = _draw_complementary(rng, rows_per_group)
        elif family == "validation_shift":
            y = rng.normal(7.0, 0.7, rows_per_group)
        elif family == "mixed_group":
            y = (
                _draw_complementary(rng, rows_per_group)
                if group_index < group_count - 1
                else rng.normal(3.5, 0.7, rows_per_group)
            )
        else:
            raise ValueError(f"unknown family: {family}")
        values.append(y)
        groups.extend([f"group-{group_index + 1}"] * rows_per_group)
    return np.concatenate(values), tuple(groups)


def _single_candidate_mean_gains(log_density: np.ndarray, marginal: np.ndarray) -> tuple[float, ...]:
    return tuple(float(np.mean(log_density[:, index] - marginal)) for index in range(log_density.shape[1]))


def run_forecast_stacking_benchmark(
    *,
    seed: int = 20260906,
    tuning_rows: int = 4000,
    validation_group_count: int = 6,
    validation_rows_per_group: int = 600,
) -> dict[str, object]:
    rng = np.random.default_rng(seed)
    names = ("left_specialist", "right_specialist", "broad_marginal")

    tuning_y = _draw_complementary(rng, tuning_rows)
    tuning_log_density = _candidate_log_density(tuning_y)
    fit = fit_log_score_stacking(
        tuning_log_density,
        candidate_names=names,
        tolerance=1e-13,
    )

    families: dict[str, dict[str, object]] = {}
    for family in ("complementary_stable", "validation_shift", "mixed_group"):
        validation_y, groups = _validation_matrix(
            rng,
            group_count=validation_group_count,
            rows_per_group=validation_rows_per_group,
            family=family,
        )
        candidate_log_density = _candidate_log_density(validation_y)
        marginal = _marginal_log_density(validation_y)
        validation = evaluate_stacked_forecast(
            fit,
            candidate_log_density,
            marginal,
            groups,
            candidate_names=names,
            gain_tolerance=1e-12,
        )
        single_gains = _single_candidate_mean_gains(candidate_log_density, marginal)
        families[family] = {
            "stack": validation.as_dict(),
            "single_candidate_mean_gains": {
                name: gain for name, gain in zip(names, single_gains)
            },
            "best_single_mean_gain": float(max(single_gains)),
            "stack_minus_best_single_gain": float(
                validation.mean_log_density_gain - max(single_gains)
            ),
        }

    permutation = np.asarray([2, 0, 1], dtype=int)
    permuted_names = tuple(names[index] for index in permutation)
    permuted_fit = fit_log_score_stacking(
        tuning_log_density[:, permutation],
        candidate_names=permuted_names,
        tolerance=1e-13,
    )
    remapped = {
        name: weight
        for name, weight in zip(permuted_fit.candidate_names, permuted_fit.weights)
    }
    original = {name: weight for name, weight in zip(fit.candidate_names, fit.weights)}
    permutation_error = max(abs(original[name] - remapped[name]) for name in names)

    obligations = {
        "weights_sum_to_one": abs(sum(fit.weights) - 1.0) <= 1e-12,
        "specialist_weights_in_frozen_range": (
            0.25 <= original["left_specialist"] <= 0.75
            and 0.25 <= original["right_specialist"] <= 0.75
        ),
        "broad_weight_below_frozen_max": original["broad_marginal"] <= 0.20,
        "stable_is_generalizing": (
            families["complementary_stable"]["stack"]["transfer_category"] == "generalizing"
            and families["complementary_stable"]["stack"]["positive_group_count"] == validation_group_count
        ),
        "stable_beats_best_single": (
            families["complementary_stable"]["stack_minus_best_single_gain"] >= 0.10
        ),
        "shift_is_non_generalizing": (
            families["validation_shift"]["stack"]["transfer_category"] == "non_generalizing"
            and families["validation_shift"]["stack"]["nonpositive_group_count"] == validation_group_count
        ),
        "mixed_group_remains_mixed": (
            families["mixed_group"]["stack"]["transfer_category"] == "mixed"
            and families["mixed_group"]["stack"]["mean_log_density_gain"] > 0.0
            and families["mixed_group"]["stack"]["minimum_group_gain"] < 0.0
        ),
        "candidate_permutation_invariant": permutation_error <= 1e-10,
        "validation_not_used_for_fit": fit.validation_used_for_fit is False,
        "coverage_not_inherited": fit.coverage_inherited_from_members is False,
        "recalibration_required": fit.requires_independent_recalibration is True,
        "no_aggregate_confidence_score": all(
            family["stack"]["aggregate_confidence_score_emitted"] is False
            for family in families.values()
        ),
    }

    return {
        "seed": int(seed),
        "tuning_rows": int(tuning_rows),
        "validation_group_count": int(validation_group_count),
        "validation_rows_per_group": int(validation_rows_per_group),
        "candidate_names": list(names),
        "fit": fit.as_dict(),
        "candidate_permutation_weight_max_abs_error": float(permutation_error),
        "families": families,
        "checks": [
            {"name": name, "passed": bool(passed)}
            for name, passed in obligations.items()
        ],
        "passed": bool(all(obligations.values())),
    }
