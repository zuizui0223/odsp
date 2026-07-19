"""Occurrence-Defined Survey Patches."""
from .benchmark import (
    BenchmarkConfig,
    BenchmarkUnit,
    benchmark_status_table,
    evaluate_benchmark_unit,
    summarize_benchmark_cohort,
)
from .patches import (
    DEFAULT_RECOVERY_RADII_KM,
    CandidatePatchConfig,
    OccurrenceConnectivityConfig,
    annotate_occurrence_connectivity,
    build_candidate_patches,
    build_occurrence_patches,
    cluster_detections,
    connected_components,
    connectivity_sensitivity,
    haversine_distance_m,
    incremental_recovery_summary,
    patch_recovery_table,
    summarize_candidate_patches,
)

__all__ = [
    "BenchmarkConfig",
    "BenchmarkUnit",
    "benchmark_status_table",
    "evaluate_benchmark_unit",
    "summarize_benchmark_cohort",
    "DEFAULT_RECOVERY_RADII_KM",
    "CandidatePatchConfig",
    "OccurrenceConnectivityConfig",
    "annotate_occurrence_connectivity",
    "build_candidate_patches",
    "build_occurrence_patches",
    "cluster_detections",
    "connected_components",
    "connectivity_sensitivity",
    "haversine_distance_m",
    "incremental_recovery_summary",
    "patch_recovery_table",
    "summarize_candidate_patches",
]

__version__ = "0.1.0-dev"
