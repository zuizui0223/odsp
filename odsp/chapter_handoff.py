"""Explicit Chapter-2 to Chapter-3 evidence handoff gate.

N2 can produce several scientifically different objects: descriptive thickness,
structural state-space capacity, known-truth method states, and empirically
supported axis-resolved species states. N3/EOG should not receive those objects
as if they were interchangeable.

The key rule is conservative: an empirical ``P(added|base)`` state map is eligible
for N3 realization/reachability analysis only when its added-axis semantics and
prospective source boundary are explicit, thickness is estimable, and independent
held-out evidence supports transferability of the base-resolved organization.
Descriptive thickness may still be retained when this stronger handoff fails.
"""
from __future__ import annotations

from dataclasses import asdict, dataclass
from typing import Literal

EvidenceScope = Literal["known_truth", "empirical"]
SupportSemantics = Literal["species_support", "structural_capacity"]
TransferabilityCategory = Literal[
    "generalizing",
    "mixed",
    "non_generalizing",
    "unavailable",
    "not_tested",
]
HandoffCategory = Literal[
    "empirical_axis_resolved_supported",
    "known_truth_method_state_only",
    "descriptive_projection_only",
    "structural_capacity_only",
    "unavailable",
]

_ALLOWED_SCOPES = {"known_truth", "empirical"}
_ALLOWED_SEMANTICS = {"species_support", "structural_capacity"}
_ALLOWED_TRANSFERABILITY = {
    "generalizing",
    "mixed",
    "non_generalizing",
    "unavailable",
    "not_tested",
}


def _derive_handoff_fields(
    *,
    evidence_scope: EvidenceScope,
    support_semantics: SupportSemantics,
    axis_semantics_declared: bool,
    prospective_source_boundary_frozen: bool,
    thickness_estimable: bool,
    transferability_category: TransferabilityCategory,
) -> tuple[HandoffCategory, bool, bool, bool, tuple[str, ...]]:
    """Derive the only valid downstream permissions from upstream evidence fields."""

    if evidence_scope not in _ALLOWED_SCOPES:
        raise ValueError(f"unsupported evidence_scope: {evidence_scope!r}")
    if support_semantics not in _ALLOWED_SEMANTICS:
        raise ValueError(f"unsupported support_semantics: {support_semantics!r}")
    if transferability_category not in _ALLOWED_TRANSFERABILITY:
        raise ValueError(
            f"unsupported transferability_category: {transferability_category!r}"
        )
    for name, value in (
        ("axis_semantics_declared", axis_semantics_declared),
        ("prospective_source_boundary_frozen", prospective_source_boundary_frozen),
        ("thickness_estimable", thickness_estimable),
    ):
        if not isinstance(value, bool):
            raise ValueError(f"{name} must be boolean")

    reasons: list[str] = []
    if not axis_semantics_declared:
        reasons.append("added_axis_semantics_not_declared")
    if not thickness_estimable:
        reasons.append("thickness_not_estimable")
    if evidence_scope == "empirical" and not prospective_source_boundary_frozen:
        reasons.append("empirical_source_boundary_not_prospectively_frozen")

    projection_summary_allowed = bool(axis_semantics_declared and thickness_estimable)
    method_state_allowed = bool(
        evidence_scope == "known_truth"
        and support_semantics == "species_support"
        and axis_semantics_declared
        and thickness_estimable
    )
    empirical_state_allowed = bool(
        evidence_scope == "empirical"
        and support_semantics == "species_support"
        and axis_semantics_declared
        and prospective_source_boundary_frozen
        and thickness_estimable
        and transferability_category == "generalizing"
    )

    if support_semantics == "structural_capacity":
        reasons.append("structural_capacity_is_not_species_support")
        handoff_category: HandoffCategory = (
            "structural_capacity_only" if projection_summary_allowed else "unavailable"
        )
    elif method_state_allowed:
        reasons.append("known_truth_state_not_empirical_species_evidence")
        handoff_category = "known_truth_method_state_only"
    elif empirical_state_allowed:
        handoff_category = "empirical_axis_resolved_supported"
    elif projection_summary_allowed:
        if transferability_category == "non_generalizing":
            reasons.append("independent_axis_resolved_organization_not_generalizing")
        elif transferability_category == "mixed":
            reasons.append("independent_axis_resolved_organization_mixed")
        elif transferability_category == "unavailable":
            reasons.append("independent_transferability_unavailable")
        elif transferability_category == "not_tested":
            reasons.append("independent_transferability_not_tested")
        handoff_category = "descriptive_projection_only"
    else:
        handoff_category = "unavailable"

    return (
        handoff_category,
        projection_summary_allowed,
        method_state_allowed,
        empirical_state_allowed,
        tuple(reasons),
    )


@dataclass(frozen=True)
class N2ToN3HandoffDecision:
    """Machine-readable boundary between ODSP evidence and EOG input claims.

    Instances are self-validating: serialized or hand-constructed downstream
    permissions cannot contradict the upstream evidence fields.
    """

    evidence_scope: EvidenceScope
    support_semantics: SupportSemantics
    axis_semantics_declared: bool
    prospective_source_boundary_frozen: bool
    thickness_estimable: bool
    transferability_category: TransferabilityCategory
    handoff_category: HandoffCategory
    projection_summary_allowed: bool
    axis_resolved_state_allowed_for_method_testing: bool
    axis_resolved_species_state_allowed_for_empirical_n3: bool
    reason_codes: tuple[str, ...]

    def __post_init__(self) -> None:
        (
            expected_category,
            expected_projection,
            expected_method,
            expected_empirical,
            expected_reasons,
        ) = _derive_handoff_fields(
            evidence_scope=self.evidence_scope,
            support_semantics=self.support_semantics,
            axis_semantics_declared=self.axis_semantics_declared,
            prospective_source_boundary_frozen=self.prospective_source_boundary_frozen,
            thickness_estimable=self.thickness_estimable,
            transferability_category=self.transferability_category,
        )
        observed = (
            self.handoff_category,
            self.projection_summary_allowed,
            self.axis_resolved_state_allowed_for_method_testing,
            self.axis_resolved_species_state_allowed_for_empirical_n3,
            tuple(self.reason_codes),
        )
        expected = (
            expected_category,
            expected_projection,
            expected_method,
            expected_empirical,
            expected_reasons,
        )
        if observed != expected:
            raise ValueError("handoff decision fields are inconsistent with upstream evidence")

    def as_dict(self) -> dict[str, object]:
        return asdict(self)


def assess_n2_to_n3_handoff(
    *,
    evidence_scope: EvidenceScope,
    support_semantics: SupportSemantics,
    axis_semantics_declared: bool,
    prospective_source_boundary_frozen: bool,
    thickness_estimable: bool,
    transferability_category: TransferabilityCategory,
) -> N2ToN3HandoffDecision:
    """Classify what Chapter-2 evidence may be passed to Chapter 3.

    ``projection_summary_allowed`` means N2 may report descriptive thickness or
    projection loss under the declared support semantics. It does *not* mean that
    a local axis-resolved distribution may be used by N3 as an empirical species
    state map.

    ``axis_resolved_species_state_allowed_for_empirical_n3`` is intentionally
    stricter. It requires empirical species support with declared axis semantics,
    a prospectively frozen source boundary, estimable thickness, and independently
    held-out organization classified as ``generalizing``.

    Known-truth states may be handed to N3 only for method testing. Structural
    capacity may be reported as capacity but cannot be relabeled as species use.
    """

    (
        handoff_category,
        projection_summary_allowed,
        method_state_allowed,
        empirical_state_allowed,
        reasons,
    ) = _derive_handoff_fields(
        evidence_scope=evidence_scope,
        support_semantics=support_semantics,
        axis_semantics_declared=axis_semantics_declared,
        prospective_source_boundary_frozen=prospective_source_boundary_frozen,
        thickness_estimable=thickness_estimable,
        transferability_category=transferability_category,
    )
    return N2ToN3HandoffDecision(
        evidence_scope=evidence_scope,
        support_semantics=support_semantics,
        axis_semantics_declared=axis_semantics_declared,
        prospective_source_boundary_frozen=prospective_source_boundary_frozen,
        thickness_estimable=thickness_estimable,
        transferability_category=transferability_category,
        handoff_category=handoff_category,
        projection_summary_allowed=projection_summary_allowed,
        axis_resolved_state_allowed_for_method_testing=method_state_allowed,
        axis_resolved_species_state_allowed_for_empirical_n3=empirical_state_allowed,
        reason_codes=reasons,
    )
