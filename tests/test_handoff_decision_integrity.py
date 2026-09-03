import pytest

from odsp.chapter_handoff import N2ToN3HandoffDecision, assess_n2_to_n3_handoff


def test_assessed_handoff_decision_is_self_consistent():
    decision = assess_n2_to_n3_handoff(
        evidence_scope="empirical",
        support_semantics="species_support",
        axis_semantics_declared=True,
        prospective_source_boundary_frozen=True,
        thickness_estimable=True,
        transferability_category="non_generalizing",
    )

    assert decision.handoff_category == "descriptive_projection_only"
    assert decision.axis_resolved_species_state_allowed_for_empirical_n3 is False


def test_handoff_decision_serializes_reason_codes_as_json_array():
    decision = assess_n2_to_n3_handoff(
        evidence_scope="empirical",
        support_semantics="species_support",
        axis_semantics_declared=True,
        prospective_source_boundary_frozen=True,
        thickness_estimable=True,
        transferability_category="non_generalizing",
    )

    serialized = decision.as_dict()
    assert isinstance(serialized["reason_codes"], list)
    assert serialized["reason_codes"] == [
        "independent_axis_resolved_organization_not_generalizing"
    ]


def test_forged_empirical_promotion_cannot_be_constructed():
    with pytest.raises(ValueError, match="inconsistent with upstream evidence"):
        N2ToN3HandoffDecision(
            evidence_scope="empirical",
            support_semantics="species_support",
            axis_semantics_declared=True,
            prospective_source_boundary_frozen=True,
            thickness_estimable=True,
            transferability_category="non_generalizing",
            handoff_category="empirical_axis_resolved_supported",
            projection_summary_allowed=True,
            axis_resolved_state_allowed_for_method_testing=False,
            axis_resolved_species_state_allowed_for_empirical_n3=True,
            reason_codes=(),
        )


def test_known_truth_cannot_be_forged_as_empirical_permission():
    with pytest.raises(ValueError, match="inconsistent with upstream evidence"):
        N2ToN3HandoffDecision(
            evidence_scope="known_truth",
            support_semantics="species_support",
            axis_semantics_declared=True,
            prospective_source_boundary_frozen=False,
            thickness_estimable=True,
            transferability_category="generalizing",
            handoff_category="empirical_axis_resolved_supported",
            projection_summary_allowed=True,
            axis_resolved_state_allowed_for_method_testing=False,
            axis_resolved_species_state_allowed_for_empirical_n3=True,
            reason_codes=(),
        )


def test_non_boolean_boundary_fields_fail_closed():
    with pytest.raises(ValueError, match="must be boolean"):
        N2ToN3HandoffDecision(
            evidence_scope="empirical",
            support_semantics="species_support",
            axis_semantics_declared=1,  # type: ignore[arg-type]
            prospective_source_boundary_frozen=True,
            thickness_estimable=True,
            transferability_category="generalizing",
            handoff_category="empirical_axis_resolved_supported",
            projection_summary_allowed=True,
            axis_resolved_state_allowed_for_method_testing=False,
            axis_resolved_species_state_allowed_for_empirical_n3=True,
            reason_codes=(),
        )
