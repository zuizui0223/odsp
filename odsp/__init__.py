"""ODSP — multidimensional niche geometry and state-resolved ecological prediction.

The active surface combines information-theoretic niche geometry, independent
transferability, state-resolved prediction and trust diagnostics.  The frozen v4
submission remains a historical scientific artifact; later package development
must not rewrite its empirical endpoints or validated hashes.
"""

from .added_axis_evidence import (
    AddedAxisEvidenceProfile,
    AddedAxisEvidenceResult,
    evaluate_added_axis_evidence,
)
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
from .covariate_state_prediction import (
    CovariateStateModel,
    CovariateStatePredictionSummary,
    fit_covariate_state_model,
    make_state_classifier,
)
from .crossfitted_transferability import score_crossfitted_independent_groups
from .generality_benchmark import (
    GeneralityBenchmarkResult,
    GeneralityCheck,
    run_n2_generality_benchmark,
)
from .generalization_profile import (
    GeneralizationGroupScore,
    GeneralizationLevelProfile,
    GeneralizationProfile,
    generalization_profile_from_probability_field,
)
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
from .prediction_novelty import (
    EnvironmentalNoveltyModel,
    NoveltySummary,
    fit_environmental_novelty_model,
)
from .prediction_trust_benchmark import (
    PredictionTrustBenchmarkResult,
    PredictionTrustCheck,
    run_prediction_trust_benchmark,
)
from .prediction_uncertainty import (
    ConformalCoverageReport,
    ConformalPredictionSummary,
    StateConformalCalibrator,
    fit_state_conformal_calibrator,
)
from .projection_loss import (
    ProjectionOverlapProfile,
    projection_overlap_profile,
    schoener_overlap,
)
from .serengeti_terminal import (
    SerengetiTerminalReceipt,
    validate_serengeti_terminal_result,
)
from .state_prediction import (
    EncodedStateResolvedModel,
    EncodedStateSupport,
    GroupedStatePredictionScore,
    StatePredictionScore,
    StatePredictionSummary,
    StateResolvedModel,
    encode_state_events,
    fit_state_resolved_events,
    fit_state_resolved_model,
    score_state_prediction_groups,
    score_state_probability_field,
)
from .state_prediction_benchmark import (
    StatePredictionBenchmarkCell,
    StatePredictionBenchmarkResult,
    run_state_prediction_benchmark,
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
    "AddedAxisEvidenceProfile",
    "AddedAxisEvidenceResult",
    "AxisDescriptor",
    "AxisThicknessMap",
    "ConcealedRecoveryBenchmark",
    "ConcealedRecoveryCheck",
    "ConditionalTransferabilityScore",
    "ConformalCoverageReport",
    "ConformalPredictionSummary",
    "CovariateStateModel",
    "CovariateStatePredictionSummary",
    "EncodedStateResolvedModel",
    "EncodedStateSupport",
    "EnvironmentalNoveltyModel",
    "GeneralityBenchmarkResult",
    "GeneralityCheck",
    "GeneralizationGroupScore",
    "GeneralizationLevelProfile",
    "GeneralizationProfile",
    "GroupedHandoffPayload",
    "GroupedStatePredictionScore",
    "GroupedTransferabilityResult",
    "IndependentGroupTransferability",
    "N2ToN3HandoffDecision",
    "N2ToN3Payload",
    "NicheThicknessProfile",
    "NoveltySummary",
    "PredictionTrustBenchmarkResult",
    "PredictionTrustCheck",
    "ProjectionOverlapProfile",
    "SerengetiTerminalReceipt",
    "StateArtifact",
    "StateConformalCalibrator",
    "StatePredictionBenchmarkCell",
    "StatePredictionBenchmarkResult",
    "StatePredictionScore",
    "StatePredictionSummary",
    "StateResolvedModel",
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
    "encode_state_events",
    "estimate_projection_overlap_from_counts",
    "estimate_thickness_from_counts",
    "evaluate_added_axis_evidence",
    "fit_covariate_state_model",
    "fit_environmental_novelty_model",
    "fit_state_conformal_calibrator",
    "fit_state_resolved_events",
    "fit_state_resolved_model",
    "gbif_locality_elevation_mapping",
    "generalization_profile_from_probability_field",
    "make_state_classifier",
    "marginal_probability",
    "niche_thickness_profile",
    "normalize_gbif_time",
    "normalize_inaturalist_time",
    "normalize_occurrence_time",
    "normalize_vertical_information",
    "projection_overlap_profile",
    "run_concealed_recovery_benchmark",
    "run_n2_generality_benchmark",
    "run_prediction_trust_benchmark",
    "run_state_prediction_benchmark",
    "sample_state_counts",
    "schoener_overlap",
    "score_conditional_transferability",
    "score_crossfitted_independent_groups",
    "score_identity_temporal_crossfitted_groups",
    "score_identity_temporal_groups",
    "score_identity_temporal_transferability",
    "score_independent_groups",
    "score_state_prediction_groups",
    "score_state_probability_field",
    "shannon_entropy",
    "temporal_partition_profile",
    "validate_n2_to_n3_payload",
    "validate_serengeti_terminal_result",
]
