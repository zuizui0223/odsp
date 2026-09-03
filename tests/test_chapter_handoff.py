import json
from pathlib import Path

import pytest

from odsp.chapter_handoff import assess_n2_to_n3_handoff


ROOT = Path(__file__).resolve().parents[1]


def test_empirical_generalizing_species_state_is_eligible_for_n3():
    decision = assess_n2_to_n3_handoff(
        evidence_scope="empirical",
        support_semantics="species_support",
        axis_semantics_declared=True,
        prospective_source_boundary_frozen=True,
        thickness_estimable=True,
        transferability_category="generalizing",
    )

    assert decision.handoff_category == "empirical_axis_resolved_supported"
    assert decision.projection_summary_allowed is True
    assert decision.axis_resolved_species_state_allowed_for_empirical_n3 is True
    assert decision.axis_resolved_state_allowed_for_method_testing is False
    assert decision.reason_codes == ()


def test_bat_like_non_generalizing_result_is_descriptive_only():
    decision = assess_n2_to_n3_handoff(
        evidence_scope="empirical",
        support_semantics="species_support",
        axis_semantics_declared=True,
        prospective_source_boundary_frozen=True,
        thickness_estimable=True,
        transferability_category="non_generalizing",
    )

    assert decision.handoff_category == "descriptive_projection_only"
    assert decision.projection_summary_allowed is True
    assert decision.axis_resolved_species_state_allowed_for_empirical_n3 is False
    assert "independent_axis_resolved_organization_not_generalizing" in decision.reason_codes


def test_mixed_transferability_is_not_promoted_to_empirical_n3_state():
    decision = assess_n2_to_n3_handoff(
        evidence_scope="empirical",
        support_semantics="species_support",
        axis_semantics_declared=True,
        prospective_source_boundary_frozen=True,
        thickness_estimable=True,
        transferability_category="mixed",
    )

    assert decision.handoff_category == "descriptive_projection_only"
    assert decision.axis_resolved_species_state_allowed_for_empirical_n3 is False
    assert "independent_axis_resolved_organization_mixed" in decision.reason_codes


def test_tawaki_like_unestimable_result_is_unavailable():
    decision = assess_n2_to_n3_handoff(
        evidence_scope="empirical",
        support_semantics="species_support",
        axis_semantics_declared=True,
        prospective_source_boundary_frozen=True,
        thickness_estimable=False,
        transferability_category="unavailable",
    )

    assert decision.handoff_category == "unavailable"
    assert decision.projection_summary_allowed is False
    assert decision.axis_resolved_species_state_allowed_for_empirical_n3 is False
    assert "thickness_not_estimable" in decision.reason_codes


def test_known_truth_state_is_method_only_not_empirical_evidence():
    decision = assess_n2_to_n3_handoff(
        evidence_scope="known_truth",
        support_semantics="species_support",
        axis_semantics_declared=True,
        prospective_source_boundary_frozen=False,
        thickness_estimable=True,
        transferability_category="generalizing",
    )

    assert decision.handoff_category == "known_truth_method_state_only"
    assert decision.axis_resolved_state_allowed_for_method_testing is True
    assert decision.axis_resolved_species_state_allowed_for_empirical_n3 is False
    assert "known_truth_state_not_empirical_species_evidence" in decision.reason_codes


def test_structural_capacity_cannot_be_relabelled_as_species_support():
    decision = assess_n2_to_n3_handoff(
        evidence_scope="empirical",
        support_semantics="structural_capacity",
        axis_semantics_declared=True,
        prospective_source_boundary_frozen=True,
        thickness_estimable=True,
        transferability_category="not_tested",
    )

    assert decision.handoff_category == "structural_capacity_only"
    assert decision.projection_summary_allowed is True
    assert decision.axis_resolved_species_state_allowed_for_empirical_n3 is False
    assert "structural_capacity_is_not_species_support" in decision.reason_codes


def test_unfrozen_empirical_boundary_blocks_axis_resolved_handoff():
    decision = assess_n2_to_n3_handoff(
        evidence_scope="empirical",
        support_semantics="species_support",
        axis_semantics_declared=True,
        prospective_source_boundary_frozen=False,
        thickness_estimable=True,
        transferability_category="generalizing",
    )

    assert decision.handoff_category == "descriptive_projection_only"
    assert decision.axis_resolved_species_state_allowed_for_empirical_n3 is False
    assert "empirical_source_boundary_not_prospectively_frozen" in decision.reason_codes


def test_missing_axis_semantics_blocks_even_descriptive_projection_summary():
    decision = assess_n2_to_n3_handoff(
        evidence_scope="empirical",
        support_semantics="species_support",
        axis_semantics_declared=False,
        prospective_source_boundary_frozen=True,
        thickness_estimable=True,
        transferability_category="generalizing",
    )

    assert decision.handoff_category == "unavailable"
    assert decision.projection_summary_allowed is False
    assert "added_axis_semantics_not_declared" in decision.reason_codes


def test_frozen_current_handoff_decisions_reproduce_from_gate():
    payload = json.loads((ROOT / "N2_CURRENT_HANDOFF_DECISIONS.json").read_text())

    for lane in payload["decisions"].values():
        decision = assess_n2_to_n3_handoff(**lane["inputs"])
        assert decision.handoff_category == lane["expected_handoff_category"]
        assert (
            decision.axis_resolved_species_state_allowed_for_empirical_n3
            is lane["axis_resolved_species_state_allowed_for_empirical_n3"]
        )
        if "projection_summary_allowed" in lane:
            assert decision.projection_summary_allowed is lane["projection_summary_allowed"]


def test_handoff_contract_keeps_non_retroactivity_closed():
    contract = json.loads((ROOT / "N2_TO_N3_HANDOFF_CONTRACT.json").read_text())
    rules = contract["non_retroactivity"]

    assert rules["downstream_results_may_retune_completed_n2_endpoint"] is False
    assert rules["failed_or_non_generalizing_n2_lane_may_be_rescued_by_handoff_relabeling"] is False
    assert rules["descriptive_thickness_alone_may_be_promoted_to_empirical_axis_resolved_state"] is False


def test_invalid_categories_fail_closed():
    with pytest.raises(ValueError, match="evidence_scope"):
        assess_n2_to_n3_handoff(
            evidence_scope="observational",  # type: ignore[arg-type]
            support_semantics="species_support",
            axis_semantics_declared=True,
            prospective_source_boundary_frozen=True,
            thickness_estimable=True,
            transferability_category="generalizing",
        )

    with pytest.raises(ValueError, match="transferability_category"):
        assess_n2_to_n3_handoff(
            evidence_scope="empirical",
            support_semantics="species_support",
            axis_semantics_declared=True,
            prospective_source_boundary_frozen=True,
            thickness_estimable=True,
            transferability_category="probably",  # type: ignore[arg-type]
        )
