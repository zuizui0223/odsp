import numpy as np
import pytest

from odsp.grouped_handoff import build_grouped_n2_to_n3_payload
from odsp.grouped_transferability import (
    GroupedTransferabilityResult,
    score_independent_groups,
)
from odsp.handoff_payload import AxisDescriptor, StateArtifact, validate_n2_to_n3_payload


BASE = (
    AxisDescriptor("x", "projected easting", "m", "EPSG:3035"),
    AxisDescriptor("y", "projected northing", "m", "EPSG:3035"),
)
ADDED = (AxisDescriptor("z", "native vertical state", "m", "MSL"),)


def _model():
    model = np.zeros((2, 1, 2), dtype=float)
    model[0, 0, :] = [9.0, 1.0]
    model[1, 0, :] = [1.0, 9.0]
    return model


def test_generalizing_grouped_result_promotes_without_manual_category_or_gains():
    model = _model()
    grouped = score_independent_groups(
        model,
        {"a": model.copy(), "b": model * 4.0},
        base_axes=(0, 1),
        added_axes=(2,),
        gain_tolerance=0.0,
    )
    artifact = StateArtifact(
        artifact_semantics="empirical_species_support",
        uri="artifact://future-grouped-state.npz",
        sha256="a" * 64,
        media_type="application/x-npz",
        shape=(2, 1, 2),
        axis_order=("x", "y", "z"),
    )
    bundle = build_grouped_n2_to_n3_payload(
        evidence_id="future-grouped-generalizing",
        grouped_result=grouped,
        evidence_scope="empirical",
        support_semantics="species_support",
        axis_semantics_declared=True,
        prospective_source_boundary_frozen=True,
        thickness_estimable=True,
        base_axes=BASE,
        added_axes=ADDED,
        projection_summary={"effective_vertical_states": 2.0},
        state_artifact=artifact,
    )

    assert bundle.decision.handoff_category == "empirical_axis_resolved_supported"
    assert bundle.payload.transferability_gains == grouped.gains
    assert bundle.payload.state_artifact == artifact
    assert validate_n2_to_n3_payload(bundle.payload.as_dict()) == bundle.payload.fingerprint


def test_mixed_grouped_result_becomes_descriptive_only_without_manual_relabeling():
    model = _model()
    grouped = score_independent_groups(
        model,
        {"stable": model.copy(), "shifted": model[::-1].copy()},
        base_axes=(0, 1),
        added_axes=(2,),
        gain_tolerance=0.0,
    )
    bundle = build_grouped_n2_to_n3_payload(
        evidence_id="future-grouped-mixed",
        grouped_result=grouped,
        evidence_scope="empirical",
        support_semantics="species_support",
        axis_semantics_declared=True,
        prospective_source_boundary_frozen=True,
        thickness_estimable=True,
        base_axes=BASE,
        added_axes=ADDED,
        projection_summary={"effective_vertical_states": 2.0},
    )

    assert grouped.classification == "mixed"
    assert bundle.decision.handoff_category == "descriptive_projection_only"
    assert bundle.payload.state_artifact is None
    assert bundle.payload.transferability_gains == grouped.gains


def test_payload_v1_rejects_grouped_nonzero_gain_tolerance():
    model = np.ones((2, 1, 2), dtype=float)
    grouped = score_independent_groups(
        model,
        {"a": model.copy(), "b": model.copy()},
        base_axes=(0, 1),
        added_axes=(2,),
        gain_tolerance=1e-6,
    )

    with pytest.raises(ValueError, match="gain_tolerance == 0"):
        build_grouped_n2_to_n3_payload(
            evidence_id="nonzero-threshold",
            grouped_result=grouped,
            evidence_scope="empirical",
            support_semantics="species_support",
            axis_semantics_declared=True,
            prospective_source_boundary_frozen=True,
            thickness_estimable=True,
            base_axes=BASE,
            added_axes=ADDED,
            projection_summary={"effective_vertical_states": 1.0},
        )


def test_grouped_result_cannot_be_forged_after_scoring():
    model = _model()
    grouped = score_independent_groups(
        model,
        {"a": model.copy(), "b": model.copy()},
        base_axes=(0, 1),
        added_axes=(2,),
        gain_tolerance=0.0,
    )

    with pytest.raises(ValueError, match="classification is inconsistent"):
        GroupedTransferabilityResult(
            base_axes=grouped.base_axes,
            added_axes=grouped.added_axes,
            groups=grouped.groups,
            gains=grouped.gains,
            equal_group_mean_gain=grouped.equal_group_mean_gain,
            classification="non_generalizing",
            gain_tolerance=grouped.gain_tolerance,
        )


def test_axis_descriptor_rank_mismatch_fails_before_payload_build():
    model = _model()
    grouped = score_independent_groups(
        model,
        {"a": model.copy(), "b": model.copy()},
        base_axes=(0, 1),
        added_axes=(2,),
        gain_tolerance=0.0,
    )

    with pytest.raises(ValueError, match="base axis descriptors"):
        build_grouped_n2_to_n3_payload(
            evidence_id="bad-axis-rank",
            grouped_result=grouped,
            evidence_scope="empirical",
            support_semantics="species_support",
            axis_semantics_declared=True,
            prospective_source_boundary_frozen=True,
            thickness_estimable=True,
            base_axes=BASE[:1],
            added_axes=ADDED,
            projection_summary={"effective_vertical_states": 2.0},
        )
