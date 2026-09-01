"""ODSP — Chapter 2 multidimensional niche geometry.

The active ODSP surface keeps source-preserving occurrence information and adds
model-agnostic niche-thickness, projection-loss and known-truth recovery tools.
The historical spatial-patch method remains superseded by EOG.
"""

from .concealed_recovery import (
    ConcealedRecoveryBenchmark,
    ConcealedRecoveryCheck,
    estimate_projection_overlap_from_counts,
    estimate_thickness_from_counts,
    run_concealed_recovery_benchmark,
    sample_state_counts,
)
from .niche_geometry import (
    AxisThicknessMap,
    NicheThicknessProfile,
    axis_thickness_map,
    conditional_information,
    effective_conditional_states,
    marginal_probability,
    niche_thickness_profile,
    shannon_entropy,
)
from .projection_loss import (
    ProjectionOverlapProfile,
    projection_overlap_profile,
    schoener_overlap,
)
from .temporal_information import (
    TemporalObservation,
    normalize_gbif_time,
    normalize_inaturalist_time,
    normalize_occurrence_time,
)
from .vertical_information import (
    VerticalFieldMap,
    VerticalObservation,
    gbif_locality_elevation_mapping,
    normalize_vertical_information,
)

__all__ = [
    "AxisThicknessMap",
    "ConcealedRecoveryBenchmark",
    "ConcealedRecoveryCheck",
    "NicheThicknessProfile",
    "ProjectionOverlapProfile",
    "TemporalObservation",
    "VerticalFieldMap",
    "VerticalObservation",
    "axis_thickness_map",
    "conditional_information",
    "effective_conditional_states",
    "estimate_projection_overlap_from_counts",
    "estimate_thickness_from_counts",
    "gbif_locality_elevation_mapping",
    "marginal_probability",
    "niche_thickness_profile",
    "normalize_gbif_time",
    "normalize_inaturalist_time",
    "normalize_occurrence_time",
    "normalize_vertical_information",
    "projection_overlap_profile",
    "run_concealed_recovery_benchmark",
    "sample_state_counts",
    "schoener_overlap",
    "shannon_entropy",
]
