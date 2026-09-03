"""Direct adapter from independent-group transferability to the N2 -> N3 payload.

The adapter removes manual transcription of group gains and the terminal
transferability classification. Payload schema v1 uses zero as the gain boundary,
so grouped results with a non-zero tolerance are deliberately rejected rather
than silently reinterpreted.
"""
from __future__ import annotations

from dataclasses import dataclass
from typing import Mapping, Sequence

from .chapter_handoff import (
    EvidenceScope,
    N2ToN3HandoffDecision,
    SupportSemantics,
    assess_n2_to_n3_handoff,
)
from .grouped_transferability import GroupedTransferabilityResult
from .handoff_payload import (
    AxisDescriptor,
    N2ToN3Payload,
    StateArtifact,
    build_n2_to_n3_payload,
)


@dataclass(frozen=True)
class GroupedHandoffPayload:
    """One validated grouped result plus its derived decision and payload."""

    grouped_result: GroupedTransferabilityResult
    decision: N2ToN3HandoffDecision
    payload: N2ToN3Payload

    def as_dict(self) -> dict[str, object]:
        return {
            "grouped_result": self.grouped_result.as_dict(),
            "decision": self.decision.as_dict(),
            "payload": self.payload.as_dict(),
        }


def build_grouped_n2_to_n3_payload(
    *,
    evidence_id: str,
    grouped_result: GroupedTransferabilityResult,
    evidence_scope: EvidenceScope,
    support_semantics: SupportSemantics,
    axis_semantics_declared: bool,
    prospective_source_boundary_frozen: bool,
    thickness_estimable: bool,
    base_axes: Sequence[AxisDescriptor],
    added_axes: Sequence[AxisDescriptor],
    projection_summary: Mapping[str, float] | None = None,
    source_contract: str | None = None,
    decision_receipt: str | None = None,
    source_fingerprint: str | None = None,
    state_artifact: StateArtifact | None = None,
) -> GroupedHandoffPayload:
    """Derive an N2 handoff directly from an independent-group result.

    No caller-supplied transferability category or gain vector is accepted. Both
    are taken from ``grouped_result``. Schema v1 does not serialize a gain
    tolerance, therefore only the zero-threshold grouped rule can be handed off.
    A future non-zero threshold requires an explicitly versioned payload schema.
    """

    if grouped_result.gain_tolerance != 0.0:
        raise ValueError(
            "n2-to-n3-payload-v1 requires grouped gain_tolerance == 0; "
            "use an explicitly versioned schema for non-zero thresholds"
        )
    if len(tuple(base_axes)) != len(grouped_result.base_axes):
        raise ValueError("base axis descriptors must match grouped_result base-axis rank")
    if len(tuple(added_axes)) != len(grouped_result.added_axes):
        raise ValueError("added axis descriptors must match grouped_result added-axis rank")

    decision = assess_n2_to_n3_handoff(
        evidence_scope=evidence_scope,
        support_semantics=support_semantics,
        axis_semantics_declared=axis_semantics_declared,
        prospective_source_boundary_frozen=prospective_source_boundary_frozen,
        thickness_estimable=thickness_estimable,
        transferability_category=grouped_result.classification,  # type: ignore[arg-type]
    )
    payload = build_n2_to_n3_payload(
        evidence_id=evidence_id,
        decision=decision,
        base_axes=base_axes,
        added_axes=added_axes,
        projection_summary=projection_summary,
        transferability_gains=grouped_result.gains,
        source_contract=source_contract,
        decision_receipt=decision_receipt,
        source_fingerprint=source_fingerprint,
        state_artifact=state_artifact,
    )
    return GroupedHandoffPayload(
        grouped_result=grouped_result,
        decision=decision,
        payload=payload,
    )
