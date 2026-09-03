import copy

import pytest

from odsp.chapter_handoff import assess_n2_to_n3_handoff
from odsp.handoff_payload import (
    AxisDescriptor,
    StateArtifact,
    build_n2_to_n3_payload,
    validate_n2_to_n3_payload,
)


XY_AXES = (
    AxisDescriptor("x", "projected easting", "m", "EPSG:3035"),
    AxisDescriptor("y", "projected northing", "m", "EPSG:3035"),
)
Z_AXIS = (AxisDescriptor("z", "native GPS height above mean sea level", "m", "MSL"),)


def test_bat_like_descriptive_payload_roundtrips_without_state_artifact():
    decision = assess_n2_to_n3_handoff(
        evidence_scope="empirical",
        support_semantics="species_support",
        axis_semantics_declared=True,
        prospective_source_boundary_frozen=True,
        thickness_estimable=True,
        transferability_category="non_generalizing",
    )
    payload = build_n2_to_n3_payload(
        evidence_id="tadarida-teniotis-n2-terminal",
        decision=decision,
        base_axes=XY_AXES,
        added_axes=Z_AXIS,
        projection_summary={
            "H_Z_given_XY_nats": 1.3918623004770097,
            "effective_vertical_states": 4.022333876564191,
        },
        transferability_gains=(-0.43541033813280833, -0.021938657402345435),
        source_contract="N2_BAT_THICKNESS_CONTRACT.json",
        decision_receipt="N2_BAT_THICKNESS_TERMINAL_DECISION.json",
    )

    serialized = payload.as_dict()
    assert serialized["handoff"]["handoff_category"] == "descriptive_projection_only"
    assert serialized["state_artifact"] is None
    assert validate_n2_to_n3_payload(serialized) == payload.fingerprint


def test_tawaki_like_unavailable_payload_forbids_projection_summary():
    decision = assess_n2_to_n3_handoff(
        evidence_scope="empirical",
        support_semantics="species_support",
        axis_semantics_declared=True,
        prospective_source_boundary_frozen=True,
        thickness_estimable=False,
        transferability_category="unavailable",
    )
    payload = build_n2_to_n3_payload(
        evidence_id="tawaki-gate-d-terminal",
        decision=decision,
        base_axes=XY_AXES,
        added_axes=(AxisDescriptor("z", "dive depth", "m", "sea surface"),),
        decision_receipt="GATE_D_TAWAKI_TERMINAL_RECEIPT.json",
    )

    assert payload.projection_summary is None
    assert payload.state_artifact is None
    assert validate_n2_to_n3_payload(payload.as_dict()) == payload.fingerprint

    with pytest.raises(ValueError, match="must be absent"):
        build_n2_to_n3_payload(
            evidence_id="bad-tawaki",
            decision=decision,
            base_axes=XY_AXES,
            added_axes=(AxisDescriptor("z", "dive depth", "m"),),
            projection_summary={"effective_vertical_states": 1.0},
        )


def test_empirical_generalizing_payload_requires_integrity_pinned_species_state():
    decision = assess_n2_to_n3_handoff(
        evidence_scope="empirical",
        support_semantics="species_support",
        axis_semantics_declared=True,
        prospective_source_boundary_frozen=True,
        thickness_estimable=True,
        transferability_category="generalizing",
    )
    artifact = StateArtifact(
        artifact_semantics="empirical_species_support",
        uri="artifact://future-axis-resolved-support.npz",
        sha256="a" * 64,
        media_type="application/x-npz",
        shape=(2, 3, 4),
        axis_order=("x", "y", "z"),
    )
    payload = build_n2_to_n3_payload(
        evidence_id="future-generalizing-lane",
        decision=decision,
        base_axes=XY_AXES,
        added_axes=Z_AXIS,
        projection_summary={"effective_vertical_states": 2.5},
        transferability_gains=(0.12, 0.08),
        state_artifact=artifact,
        source_fingerprint="source-v1",
    )

    assert payload.state_artifact == artifact
    assert payload.handoff.axis_resolved_species_state_allowed_for_empirical_n3 is True
    assert validate_n2_to_n3_payload(payload.as_dict()) == payload.fingerprint

    with pytest.raises(ValueError, match="all supplied gains > 0"):
        build_n2_to_n3_payload(
            evidence_id="bad-gain",
            decision=decision,
            base_axes=XY_AXES,
            added_axes=Z_AXIS,
            projection_summary={"effective_vertical_states": 2.5},
            transferability_gains=(0.12, -0.01),
            state_artifact=artifact,
        )


def test_descriptive_payload_cannot_smuggle_axis_resolved_species_artifact():
    decision = assess_n2_to_n3_handoff(
        evidence_scope="empirical",
        support_semantics="species_support",
        axis_semantics_declared=True,
        prospective_source_boundary_frozen=True,
        thickness_estimable=True,
        transferability_category="non_generalizing",
    )
    artifact = StateArtifact(
        artifact_semantics="empirical_species_support",
        uri="artifact://forbidden.npz",
        sha256="b" * 64,
        media_type="application/x-npz",
        shape=(2, 3, 4),
        axis_order=("x", "y", "z"),
    )

    with pytest.raises(ValueError, match="state_artifact is forbidden"):
        build_n2_to_n3_payload(
            evidence_id="no-rescue",
            decision=decision,
            base_axes=XY_AXES,
            added_axes=Z_AXIS,
            projection_summary={"effective_vertical_states": 4.0},
            transferability_gains=(-0.1, -0.2),
            state_artifact=artifact,
        )


def test_artifact_axis_order_and_sha_are_fail_closed():
    decision = assess_n2_to_n3_handoff(
        evidence_scope="empirical",
        support_semantics="species_support",
        axis_semantics_declared=True,
        prospective_source_boundary_frozen=True,
        thickness_estimable=True,
        transferability_category="generalizing",
    )

    with pytest.raises(ValueError, match="sha256"):
        build_n2_to_n3_payload(
            evidence_id="bad-sha",
            decision=decision,
            base_axes=XY_AXES,
            added_axes=Z_AXIS,
            projection_summary={"effective_vertical_states": 2.0},
            transferability_gains=(0.1, 0.2),
            state_artifact=StateArtifact(
                "empirical_species_support",
                "artifact://state.npz",
                "not-a-sha",
                "application/x-npz",
                (2, 3, 4),
                ("x", "y", "z"),
            ),
        )

    with pytest.raises(ValueError, match="axis_order"):
        build_n2_to_n3_payload(
            evidence_id="bad-order",
            decision=decision,
            base_axes=XY_AXES,
            added_axes=Z_AXIS,
            projection_summary={"effective_vertical_states": 2.0},
            transferability_gains=(0.1, 0.2),
            state_artifact=StateArtifact(
                "empirical_species_support",
                "artifact://state.npz",
                "c" * 64,
                "application/x-npz",
                (2, 3, 4),
                ("y", "x", "z"),
            ),
        )


def test_payload_fingerprint_detects_serialized_tampering():
    decision = assess_n2_to_n3_handoff(
        evidence_scope="empirical",
        support_semantics="species_support",
        axis_semantics_declared=True,
        prospective_source_boundary_frozen=True,
        thickness_estimable=True,
        transferability_category="non_generalizing",
    )
    payload = build_n2_to_n3_payload(
        evidence_id="fingerprint-test",
        decision=decision,
        base_axes=XY_AXES,
        added_axes=Z_AXIS,
        projection_summary={"effective_vertical_states": 4.0},
        transferability_gains=(-0.1, -0.2),
    ).as_dict()
    tampered = copy.deepcopy(payload)
    tampered["projection_summary"]["effective_vertical_states"] = 8.0

    with pytest.raises(ValueError, match="fingerprint mismatch"):
        validate_n2_to_n3_payload(tampered)


def test_axis_names_must_be_unique_across_base_and_added_axes():
    decision = assess_n2_to_n3_handoff(
        evidence_scope="empirical",
        support_semantics="species_support",
        axis_semantics_declared=True,
        prospective_source_boundary_frozen=True,
        thickness_estimable=True,
        transferability_category="non_generalizing",
    )

    with pytest.raises(ValueError, match="axis names must be unique"):
        build_n2_to_n3_payload(
            evidence_id="duplicate-axis",
            decision=decision,
            base_axes=XY_AXES,
            added_axes=(AxisDescriptor("x", "duplicate x"),),
            projection_summary={"effective_vertical_states": 2.0},
            transferability_gains=(-0.1,),
        )
