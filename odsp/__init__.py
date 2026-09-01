"""ODSP — Chapter 2 multidimensional niche geometry.

The active ODSP surface keeps source-preserving occurrence information and adds
model-agnostic niche-thickness and projection-loss metrics. The historical
spatial-patch method remains superseded by EOG.
"""

from .niche_geometry import (
    NicheThicknessProfile,
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

__all__ = [
    "NicheThicknessProfile",
    "ProjectionOverlapProfile",
    "TemporalObservation",
    "conditional_information",
    "effective_conditional_states",
    "marginal_probability",
    "niche_thickness_profile",
    "normalize_gbif_time",
    "normalize_inaturalist_time",
    "normalize_occurrence_time",
    "projection_overlap_profile",
    "schoener_overlap",
    "shannon_entropy",
]
