"""Finite-sample known-truth benchmark for state-resolved ODSP prediction."""
from __future__ import annotations

from dataclasses import asdict, dataclass
from typing import Sequence

import numpy as np

from .state_prediction import fit_state_resolved_model


@dataclass(frozen=True)
class StatePredictionBenchmarkCell:
    family: str
    sample_size_per_base: int
    replicates: int
    mean_log_score_gain: float
    positive_gain_fraction: float
    negative_gain_fraction: float
    mean_probability_rmse: float
    mean_brier_improvement: float
    mean_top1_accuracy: float

    def as_dict(self) -> dict[str, object]:
        return asdict(self)


@dataclass(frozen=True)
class StatePredictionBenchmarkResult:
    seed: int
    alpha: float
    sample_sizes: tuple[int, ...]
    replicates: int
    cells: tuple[StatePredictionBenchmarkCell, ...]

    def as_dict(self) -> dict[str, object]:
        return {
            "seed": self.seed,
            "alpha": self.alpha,
            "sample_sizes": list(self.sample_sizes),
            "replicates": self.replicates,
            "cells": [cell.as_dict() for cell in self.cells],
        }


def _families() -> dict[str, tuple[np.ndarray, np.ndarray]]:
    stable = np.array(
        [
            [0.75, 0.20, 0.05],
            [0.05, 0.20, 0.75],
            [0.20, 0.60, 0.20],
        ],
        dtype=float,
    )
    unorganized = np.tile(np.array([0.20, 0.60, 0.20]), (3, 1))
    shifted = np.roll(stable, 1, axis=0)
    return {
        "stable_generalizing": (stable, stable),
        "unorganized": (unorganized, unorganized),
        "shifted_non_generalizing": (stable, shifted),
    }


def run_state_prediction_benchmark(
    *,
    seed: int = 20260904,
    sample_sizes: Sequence[int] = (50, 250, 1000),
    replicates: int = 128,
    alpha: float = 0.5,
) -> StatePredictionBenchmarkResult:
    """Run deterministic finite-observation prediction benchmarks.

    Each replicate independently samples training and held-out counts for three
    base states and three added states.  The stable family retains its
    base-conditioned organization, the unorganized family has no base-added
    association, and the shifted family changes its organization only in held-out
    support.  This benchmark therefore tests probability recovery and predictive
    transfer rather than projection-loss magnitude alone.
    """

    sizes = tuple(int(value) for value in sample_sizes)
    if not sizes or any(value <= 0 for value in sizes):
        raise ValueError("sample_sizes must contain positive integers")
    if int(replicates) <= 0:
        raise ValueError("replicates must be positive")
    rng = np.random.default_rng(int(seed))
    cells: list[StatePredictionBenchmarkCell] = []

    for sample_size in sizes:
        for family, (train_probability, test_probability) in _families().items():
            gains: list[float] = []
            rmses: list[float] = []
            brier_improvements: list[float] = []
            top1: list[float] = []
            for _ in range(int(replicates)):
                training = np.vstack(
                    [
                        rng.multinomial(sample_size, probability)
                        for probability in train_probability
                    ]
                ).astype(float)
                heldout = np.vstack(
                    [
                        rng.multinomial(sample_size, probability)
                        for probability in test_probability
                    ]
                ).astype(float)
                model = fit_state_resolved_model(
                    training,
                    base_axes=(0,),
                    added_axes=(1,),
                    alpha=alpha,
                )
                score = model.score(heldout)
                gains.append(float(score.mean_log_score_gain))
                fitted = model.conditional_probability.reshape(train_probability.shape)
                rmses.append(
                    float(np.sqrt(np.mean((fitted - train_probability) ** 2)))
                )
                brier_improvements.append(float(score.brier_improvement))
                top1.append(float(score.top1_accuracy))

            gain_array = np.asarray(gains, dtype=float)
            cells.append(
                StatePredictionBenchmarkCell(
                    family=family,
                    sample_size_per_base=sample_size,
                    replicates=int(replicates),
                    mean_log_score_gain=float(np.mean(gain_array)),
                    positive_gain_fraction=float(np.mean(gain_array > 0)),
                    negative_gain_fraction=float(np.mean(gain_array < 0)),
                    mean_probability_rmse=float(np.mean(rmses)),
                    mean_brier_improvement=float(np.mean(brier_improvements)),
                    mean_top1_accuracy=float(np.mean(top1)),
                )
            )

    return StatePredictionBenchmarkResult(
        seed=int(seed),
        alpha=float(alpha),
        sample_sizes=sizes,
        replicates=int(replicates),
        cells=tuple(cells),
    )
