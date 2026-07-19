"""Confirmatory benchmark utilities for ODSP.

This module evaluates already reconstructed, training-only candidate-support
layers.  It deliberately does not build environmental support from held-out
records.  Each row in the benchmark therefore represents an auditable
 taxon-region-fold evaluation unit.
"""
from __future__ import annotations

from dataclasses import asdict, dataclass
from typing import Iterable, Sequence

import pandas as pd

from .patches import (
    DEFAULT_RECOVERY_RADII_KM,
    CandidatePatchConfig,
    OccurrenceConnectivityConfig,
    annotate_occurrence_connectivity,
    build_candidate_patches,
    cluster_detections,
    incremental_recovery_summary,
)


@dataclass(frozen=True)
class BenchmarkUnit:
    """Identifiers for one frozen taxon-region-fold evaluation unit."""

    taxon: str
    region: str
    fold_id: str


@dataclass(frozen=True)
class BenchmarkConfig:
    """Frozen ODSP benchmark settings."""

    candidate_patch: CandidatePatchConfig = CandidatePatchConfig()
    connectivity: OccurrenceConnectivityConfig = OccurrenceConnectivityConfig()
    holdout_cluster_radius_m: float = 500.0
    recovery_radii_km: tuple[float, ...] = DEFAULT_RECOVERY_RADII_KM
    holdout_group_col: str | None = None

    def validate(self) -> None:
        self.candidate_patch.validate()
        self.connectivity.validate()
        if self.holdout_cluster_radius_m <= 0:
            raise ValueError("holdout_cluster_radius_m must be positive")
        if not self.recovery_radii_km:
            raise ValueError("recovery_radii_km must not be empty")
        if any(float(value) < 0 for value in self.recovery_radii_km):
            raise ValueError("recovery_radii_km must be non-negative")


def evaluate_benchmark_unit(
    unit: BenchmarkUnit,
    training_occurrences: pd.DataFrame,
    candidate_support: pd.DataFrame,
    held_out_occurrences: pd.DataFrame,
    *,
    support_col: str = "candidate_support",
    config: BenchmarkConfig | None = None,
) -> tuple[pd.DataFrame, pd.DataFrame, pd.DataFrame]:
    """Evaluate one frozen unit and retain failures in the output.

    Returns ``(metrics, annotated_members, held_out_clusters)``.  ``metrics``
    always contains one row per requested recovery radius, including failed or
    empty units.  This supports intention-to-evaluate cohort summaries.
    """

    cfg = config or BenchmarkConfig()
    cfg.validate()
    identifiers = asdict(unit)
    radii = tuple(sorted({float(value) for value in cfg.recovery_radii_km}))

    try:
        clusters = cluster_detections(
            held_out_occurrences,
            radius_m=cfg.holdout_cluster_radius_m,
            group_col=cfg.holdout_group_col,
        )
        candidate_members = build_candidate_patches(
            candidate_support,
            support_col=support_col,
            config=cfg.candidate_patch,
        )
        annotated = annotate_occurrence_connectivity(
            candidate_members,
            training_occurrences,
            config=cfg.connectivity,
        )

        if clusters.empty:
            status = "no_held_out_clusters"
            summary = pd.DataFrame(
                {
                    "radius_km": radii,
                    "extension_only_recall": [0.0] * len(radii),
                    "extension_plus_near_disconnected_recall": [0.0] * len(radii),
                    "incremental_recall": [0.0] * len(radii),
                }
            )
        elif annotated.empty:
            status = "no_candidate_patches"
            summary = pd.DataFrame(
                {
                    "radius_km": radii,
                    "extension_only_recall": [0.0] * len(radii),
                    "extension_plus_near_disconnected_recall": [0.0] * len(radii),
                    "incremental_recall": [0.0] * len(radii),
                }
            )
        else:
            status = "ok"
            summary = incremental_recovery_summary(
                annotated,
                clusters,
                radii_km=radii,
            )

        summary = summary.assign(
            **identifiers,
            status=status,
            n_training_occurrences=len(training_occurrences),
            n_candidate_points=len(candidate_support),
            n_candidate_patches=(
                int(annotated["candidate_patch_id"].nunique())
                if not annotated.empty and "candidate_patch_id" in annotated.columns
                else 0
            ),
            n_held_out_clusters=len(clusters),
        )
        return summary, annotated, clusters
    except Exception as exc:  # retain failed units in confirmatory denominator
        metrics = pd.DataFrame(
            {
                "radius_km": radii,
                "extension_only_recall": [0.0] * len(radii),
                "extension_plus_near_disconnected_recall": [0.0] * len(radii),
                "incremental_recall": [0.0] * len(radii),
            }
        ).assign(
            **identifiers,
            status="failed",
            error_type=type(exc).__name__,
            error_message=str(exc),
            n_training_occurrences=len(training_occurrences),
            n_candidate_points=len(candidate_support),
            n_candidate_patches=0,
            n_held_out_clusters=0,
        )
        return metrics, pd.DataFrame(), pd.DataFrame()


def summarize_benchmark_cohort(metrics: pd.DataFrame) -> pd.DataFrame:
    """Summarize pair-level benchmark metrics without fold pseudoreplication.

    Fold results are averaged within taxon-region pairs first.  Cohort means are
    then calculated across pairs, while failed and empty units remain as zero
    recovery through the intention-to-evaluate table returned by
    :func:`evaluate_benchmark_unit`.
    """

    required = {
        "taxon",
        "region",
        "fold_id",
        "radius_km",
        "extension_only_recall",
        "extension_plus_near_disconnected_recall",
        "incremental_recall",
        "status",
    }
    missing = required - set(metrics.columns)
    if missing:
        raise ValueError(f"metrics is missing columns: {', '.join(sorted(missing))}")
    if metrics.empty:
        return pd.DataFrame()

    pair = (
        metrics.groupby(["taxon", "region", "radius_km"], as_index=False)
        .agg(
            extension_only_recall=("extension_only_recall", "mean"),
            extension_plus_near_disconnected_recall=(
                "extension_plus_near_disconnected_recall",
                "mean",
            ),
            incremental_recall=("incremental_recall", "mean"),
            n_folds=("fold_id", "nunique"),
            n_successful_folds=("status", lambda values: int((values == "ok").sum())),
        )
    )
    cohort = (
        pair.groupby("radius_km", as_index=False)
        .agg(
            extension_only_recall_mean=("extension_only_recall", "mean"),
            extension_plus_near_disconnected_recall_mean=(
                "extension_plus_near_disconnected_recall",
                "mean",
            ),
            incremental_recall_mean=("incremental_recall", "mean"),
            n_pairs=("taxon", "size"),
            n_pairs_positive_increment=(
                "incremental_recall",
                lambda values: int((values > 0).sum()),
            ),
        )
    )
    return cohort


def benchmark_status_table(metrics: pd.DataFrame) -> pd.DataFrame:
    """Return one status record per taxon-region-fold unit."""

    required = {"taxon", "region", "fold_id", "status"}
    missing = required - set(metrics.columns)
    if missing:
        raise ValueError(f"metrics is missing columns: {', '.join(sorted(missing))}")
    columns = [
        column
        for column in (
            "taxon",
            "region",
            "fold_id",
            "status",
            "error_type",
            "error_message",
            "n_training_occurrences",
            "n_candidate_points",
            "n_candidate_patches",
            "n_held_out_clusters",
        )
        if column in metrics.columns
    ]
    return metrics[columns].drop_duplicates(["taxon", "region", "fold_id"]).reset_index(drop=True)
