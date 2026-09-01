"""Outcome-blind admission checks for Chapter N2 empirical axis datasets.

This module evaluates measurement architecture only. It must not inspect the
observed distribution of z/t states, niche thickness, projection loss, or any
held-out biological outcome.
"""
from __future__ import annotations

from dataclasses import asdict, dataclass
import hashlib
import json

_ALLOWED_AXIS_KINDS = {
    "organism_vertical",
    "organism_depth",
    "biological_time",
    "structural_state",
    "joint_vertical_time",
}


@dataclass(frozen=True)
class EmpiricalAxisArchitecture:
    """Pre-outcome measurement architecture for one candidate empirical lane."""

    architecture_id: str
    axis_kind: str
    xy_and_axis_same_event: bool
    axis_is_native_biological_or_structural_state: bool
    effort_denominator_available: bool
    prospective_abstention_if_effort_unavailable: bool
    cluster_identifier_available: bool
    source_precision_preserved: bool
    sensor_schedule_or_effort_semantics_preserved: bool
    public_reproducible_data: bool
    source_version_pinnable: bool
    structural_preflight_without_axis_outcomes: bool
    contextual_proxy_used_as_axis: bool = False
    upload_time_used_as_biological_time: bool = False

    def as_dict(self) -> dict[str, object]:
        return asdict(self)


@dataclass(frozen=True)
class EmpiricalAxisAdmission:
    """Deterministic architecture-only admission result."""

    architecture_id: str
    admitted: bool
    reasons: tuple[str, ...]
    fingerprint: str

    def as_dict(self) -> dict[str, object]:
        return asdict(self)


def _fingerprint(spec: EmpiricalAxisArchitecture) -> str:
    payload = json.dumps(
        spec.as_dict(), sort_keys=True, separators=(",", ":"), ensure_ascii=False
    ).encode("utf-8")
    return hashlib.sha256(payload).hexdigest()


def assess_empirical_axis_architecture(
    spec: EmpiricalAxisArchitecture,
) -> EmpiricalAxisAdmission:
    """Admit or reject a candidate using measurement architecture only.

    The result is intentionally blind to axis distributions and biological
    effects. A dataset that fails here should be rejected before any N2
    thickness outcome is computed.
    """

    reasons: list[str] = []

    if not spec.architecture_id.strip():
        reasons.append("architecture_id_missing")
    if spec.axis_kind not in _ALLOWED_AXIS_KINDS:
        reasons.append("axis_kind_not_explicitly_supported")
    if not spec.xy_and_axis_same_event:
        reasons.append("xy_and_added_axis_not_joint_on_same_event")
    if not spec.axis_is_native_biological_or_structural_state:
        reasons.append("added_axis_is_not_native_biological_or_structural_state")
    if spec.contextual_proxy_used_as_axis:
        reasons.append("contextual_proxy_used_as_added_axis")
    if spec.upload_time_used_as_biological_time:
        reasons.append("upload_time_used_as_biological_time")

    effort_ok = (
        spec.effort_denominator_available
        or spec.prospective_abstention_if_effort_unavailable
    )
    if not effort_ok:
        reasons.append("effort_semantics_unavailable_without_abstention_rule")
    if not spec.cluster_identifier_available:
        reasons.append("cluster_identifier_unavailable")
    if not spec.source_precision_preserved:
        reasons.append("source_axis_or_time_precision_not_preserved")
    if not spec.sensor_schedule_or_effort_semantics_preserved:
        reasons.append("sensor_schedule_or_effort_semantics_not_preserved")
    if not spec.public_reproducible_data:
        reasons.append("primary_data_not_publicly_reproducible")
    if not spec.source_version_pinnable:
        reasons.append("source_not_version_pinnable")
    if not spec.structural_preflight_without_axis_outcomes:
        reasons.append("cannot_audit_structural_support_without_axis_outcomes")

    return EmpiricalAxisAdmission(
        architecture_id=spec.architecture_id,
        admitted=not reasons,
        reasons=tuple(reasons),
        fingerprint=_fingerprint(spec),
    )
