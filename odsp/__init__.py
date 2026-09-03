"""ODSP — Chapter 2 multidimensional niche geometry.

The active ODSP surface keeps source-preserving occurrence information and adds
model-agnostic niche-thickness, projection-loss, organization, transferability,
temporal partitioning, chapter-handoff payloads and known-truth recovery tools.
The historical spatial-patch method remains superseded by EOG.
"""

from .chapter_handoff import (
    N2ToN3HandoffDecision,
    assess_n2_to_n3_handoff,
)
from .concealed_recovery import (
    ConcealedRecoveryBenchmark,
    ConcealedRecoveryCheck,
    estimate_projection_overlap_from_counts,
    estimate_thickness_from_counts,
    run_concealed_recovery_benchmark,
    sample_state_counts,
)
from .crossfitted_transferability import score_crossfitted_independent_groups
from .grouped_handoff import (
    GroupedHandoffPayload,
    build_grouped_n2_to_n3_payload,
)
from .grouped_transferability import (
    GroupedTransferabilityResult,
    IndependentGroupTransferability,
    score_independent_groups,
)
from .handoff_payload import (
    AxisDescriptor,
    N2ToN3Payload,
    StateArtifact,
    build_n2_to_n3_payload,
    validate_n2_to_n3_payload,
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
from .temporal_crossfit import score_identity_temporal_crossfitted_groups
from .temporal_information import (
    TemporalObservation,
    normalize_gbif_time,
    normalize_inaturalist_time,
    normalize_occurrence_time,
)
from .temporal_partition import (
    TemporalPartitionDecision,
    TemporalPartitionProfile,
    classify_grouped_temporal_partition_result,
    classify_temporal_partition_result,
    score_identity_temporal_groups,
    score_identity_temporal_transferability,
    temporal_partition_profile,
)
from .transferability import (
    ConditionalTransferabilityScore,
    base_added_mutual_information,
    classify_independent_gains,
    score_conditional_transferability,
)
from .vertical_information import (
    VerticalFieldMap,
    VerticalObservation,
    gbif_locality_elevation_mapping,
    normalize_vertical_information,
)

__all__ = [
    "AxisDescriptor",
    "AxisThicknessMap",
    "ConcealedRecoveryBenchmark",
    "ConcealedRecoveryCheck",
    "ConditionalTransferabilityScore",
    "GroupedHandoffPayload",
    "GroupedTransferabilityResult",
    "IndependentGroupTransferability",
    "N2ToN3HandoffDecision",
    "N2ToN3Payload",
    "NicheThicknessProfile",
    "ProjectionOverlapProfile",
    "StateArtifact",
    "TemporalObservation",
    "TemporalPartitionDecision",
    "TemporalPartitionProfile",
    "VerticalFieldMap",
    "VerticalObservation",
    "assess_n2_to_n3_handoff",
    "axis_thickness_map",
    "base_added_mutual_information",
    "build_grouped_n2_to_n3_payload",
    "build_n2_to_n3_payload",
    "classify_grouped_temporal_partition_result",
    "classify_independent_gains",
    "classify_temporal_partition_result",
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
    "score_conditional_transferability",
    "score_crossfitted_independent_groups",
    "score_identity_temporal_crossfitted_groups",
    "score_identity_temporal_groups",
    "score_identity_temporal_transferability",
    "score_independent_groups",
    "shannon_entropy",
    "temporal_partition_profile",
    "validate_n2_to_n3_payload",
]
