import copy

import pytest

from odsp import AxisDescriptor, build_n2_to_n3_payload, validate_n2_to_n3_payload
from odsp.chapter_handoff import assess_n2_to_n3_handoff


BASE = (
    AxisDescriptor("x", "easting", "m", "EPSG:3035"),
    AxisDescriptor("y", "northing", "m", "EPSG:3035"),
)
ADDED = (AxisDescriptor("z", "height", "m", "MSL"),)


def _decision(category):
    return assess_n2_to_n3_handoff(
        evidence_scope="empirical",
        support_semantics="species_support",
        axis_semantics_declared=True,
        prospective_source_boundary_frozen=True,
        thickness_estimable=True,
        transferability_category=category,
    )


def test_projection_summary_must_be_nonempty_when_allowed():
    with pytest.raises(ValueError, match="must be non-empty"):
        build_n2_to_n3_payload(
            evidence_id="empty-summary",
            decision=_decision("non_generalizing"),
            base_axes=BASE,
            added_axes=ADDED,
            projection_summary={},
            transferability_gains=(-0.1,),
        )


def test_mixed_transferability_requires_both_positive_and_nonpositive_gains():
    with pytest.raises(ValueError, match="both positive and non-positive"):
        build_n2_to_n3_payload(
            evidence_id="bad-mixed",
            decision=_decision("mixed"),
            base_axes=BASE,
            added_axes=ADDED,
            projection_summary={"effective_vertical_states": 2.0},
            transferability_gains=(0.2, 0.1),
        )

    payload = build_n2_to_n3_payload(
        evidence_id="good-mixed",
        decision=_decision("mixed"),
        base_axes=BASE,
        added_axes=ADDED,
        projection_summary={"effective_vertical_states": 2.0},
        transferability_gains=(0.2, -0.1),
    )
    assert validate_n2_to_n3_payload(payload.as_dict()) == payload.fingerprint


def test_serialized_boolean_strings_are_rejected_not_truthy_coerced():
    payload = build_n2_to_n3_payload(
        evidence_id="strict-booleans",
        decision=_decision("non_generalizing"),
        base_axes=BASE,
        added_axes=ADDED,
        projection_summary={"effective_vertical_states": 2.0},
        transferability_gains=(-0.1,),
    ).as_dict()
    forged = copy.deepcopy(payload)
    forged["handoff"]["axis_semantics_declared"] = "true"

    with pytest.raises(ValueError, match="must be boolean"):
        validate_n2_to_n3_payload(forged)


def test_unavailable_and_not_tested_categories_cannot_carry_gains():
    unavailable = assess_n2_to_n3_handoff(
        evidence_scope="empirical",
        support_semantics="species_support",
        axis_semantics_declared=True,
        prospective_source_boundary_frozen=True,
        thickness_estimable=False,
        transferability_category="unavailable",
    )
    with pytest.raises(ValueError, match="must not carry transferability gains"):
        build_n2_to_n3_payload(
            evidence_id="bad-unavailable-gain",
            decision=unavailable,
            base_axes=BASE,
            added_axes=ADDED,
            transferability_gains=(-0.1,),
        )
