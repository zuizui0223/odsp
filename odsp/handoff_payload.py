"""Versioned N2 -> N3 payloads for reproducible cross-chapter handoff.

The handoff decision answers *what kind of object is scientifically allowed*.
This module standardizes *how that object and its provenance are serialized*.
It intentionally keeps empirical species support, known-truth method states,
structural capacity and descriptive-only results distinct.
"""
from __future__ import annotations

from dataclasses import asdict, dataclass
import hashlib
import json
import math
import re
from typing import Mapping, Sequence

from .chapter_handoff import N2ToN3HandoffDecision

SCHEMA_ID = "n2-to-n3-payload-v1"
PROGRAM_ID = "niche-to-survey-four-chapter-v1"
PRODUCER_REPOSITORY = "zuizui0223/odsp"

_SHA256_RE = re.compile(r"^[0-9a-f]{64}$")
_ALLOWED_ARTIFACT_SEMANTICS = {
    "empirical_species_support",
    "known_truth_method_state",
    "structural_capacity",
}


@dataclass(frozen=True)
class AxisDescriptor:
    """Semantic description of one serialized state axis."""

    name: str
    semantic: str
    units: str | None = None
    reference_frame: str | None = None

    def as_dict(self) -> dict[str, object]:
        return asdict(self)


@dataclass(frozen=True)
class StateArtifact:
    """Pointer and integrity metadata for an axis-resolved state object."""

    artifact_semantics: str
    uri: str
    sha256: str
    media_type: str
    shape: tuple[int, ...]
    axis_order: tuple[str, ...]

    def as_dict(self) -> dict[str, object]:
        payload = asdict(self)
        payload["shape"] = list(self.shape)
        payload["axis_order"] = list(self.axis_order)
        return payload


@dataclass(frozen=True)
class N2ToN3Payload:
    """Portable, validated Chapter-2 evidence envelope for Chapter 3."""

    schema_id: str
    program_id: str
    producer_chapter: str
    producer_repository: str
    evidence_id: str
    base_axes: tuple[AxisDescriptor, ...]
    added_axes: tuple[AxisDescriptor, ...]
    handoff: N2ToN3HandoffDecision
    projection_summary: Mapping[str, float] | None
    transferability_gains: tuple[float, ...]
    source_contract: str | None
    decision_receipt: str | None
    source_fingerprint: str | None
    state_artifact: StateArtifact | None
    fingerprint: str

    def as_dict(self) -> dict[str, object]:
        return {
            "schema_id": self.schema_id,
            "program_id": self.program_id,
            "producer": {
                "chapter": self.producer_chapter,
                "repository": self.producer_repository,
            },
            "evidence_id": self.evidence_id,
            "axes": {
                "base": [axis.as_dict() for axis in self.base_axes],
                "added": [axis.as_dict() for axis in self.added_axes],
            },
            "handoff": self.handoff.as_dict(),
            "projection_summary": (
                None
                if self.projection_summary is None
                else {str(key): float(value) for key, value in self.projection_summary.items()}
            ),
            "transferability": {
                "category": self.handoff.transferability_category,
                "independent_gains": [float(value) for value in self.transferability_gains],
            },
            "provenance": {
                "source_contract": self.source_contract,
                "decision_receipt": self.decision_receipt,
                "source_fingerprint": self.source_fingerprint,
            },
            "state_artifact": (
                None if self.state_artifact is None else self.state_artifact.as_dict()
            ),
            "fingerprint": self.fingerprint,
        }


def _clean_text(value: object, *, name: str) -> str:
    text = str(value).strip()
    if not text:
        raise ValueError(f"{name} must be non-empty")
    return text


def _validate_axis(axis: AxisDescriptor) -> AxisDescriptor:
    _clean_text(axis.name, name="axis name")
    _clean_text(axis.semantic, name=f"axis semantic for {axis.name!r}")
    if axis.units is not None:
        _clean_text(axis.units, name=f"axis units for {axis.name!r}")
    if axis.reference_frame is not None:
        _clean_text(axis.reference_frame, name=f"axis reference_frame for {axis.name!r}")
    return axis


def _validate_artifact(artifact: StateArtifact, axis_names: tuple[str, ...]) -> None:
    if artifact.artifact_semantics not in _ALLOWED_ARTIFACT_SEMANTICS:
        raise ValueError(f"unsupported artifact_semantics: {artifact.artifact_semantics!r}")
    _clean_text(artifact.uri, name="state_artifact uri")
    _clean_text(artifact.media_type, name="state_artifact media_type")
    if not _SHA256_RE.fullmatch(artifact.sha256):
        raise ValueError("state_artifact sha256 must be 64 lowercase hexadecimal characters")
    if not artifact.shape or any(int(value) <= 0 for value in artifact.shape):
        raise ValueError("state_artifact shape must contain positive dimensions")
    if tuple(artifact.axis_order) != axis_names:
        raise ValueError("state_artifact axis_order must match declared base+added axis order")
    if len(artifact.shape) != len(axis_names):
        raise ValueError("state_artifact shape rank must match declared axis count")


def _artifact_semantics_for_category(category: str) -> str | None:
    return {
        "empirical_axis_resolved_supported": "empirical_species_support",
        "known_truth_method_state_only": "known_truth_method_state",
        "structural_capacity_only": "structural_capacity",
        "descriptive_projection_only": None,
        "unavailable": None,
    }[category]


def _payload_fingerprint(payload: Mapping[str, object]) -> str:
    data = json.dumps(payload, sort_keys=True, separators=(",", ":"), allow_nan=False).encode(
        "utf-8"
    )
    return hashlib.sha256(data).hexdigest()


def build_n2_to_n3_payload(
    *,
    evidence_id: str,
    decision: N2ToN3HandoffDecision,
    base_axes: Sequence[AxisDescriptor],
    added_axes: Sequence[AxisDescriptor],
    projection_summary: Mapping[str, float] | None = None,
    transferability_gains: Sequence[float] = (),
    source_contract: str | None = None,
    decision_receipt: str | None = None,
    source_fingerprint: str | None = None,
    state_artifact: StateArtifact | None = None,
) -> N2ToN3Payload:
    """Build a validated, fingerprinted N2 -> N3 evidence payload."""

    evidence_id = _clean_text(evidence_id, name="evidence_id")
    base = tuple(_validate_axis(axis) for axis in base_axes)
    added = tuple(_validate_axis(axis) for axis in added_axes)
    if not base or not added:
        raise ValueError("base_axes and added_axes must each contain at least one axis")
    axis_names = tuple(axis.name for axis in (*base, *added))
    if len(set(axis_names)) != len(axis_names):
        raise ValueError("axis names must be unique across base and added axes")

    if decision.projection_summary_allowed:
        if projection_summary is None:
            raise ValueError("projection_summary is required when the handoff permits one")
    elif projection_summary is not None:
        raise ValueError("projection_summary must be absent when the handoff marks it unavailable")

    normalized_summary: dict[str, float] | None = None
    if projection_summary is not None:
        normalized_summary = {}
        for key, value in projection_summary.items():
            metric = _clean_text(key, name="projection_summary metric")
            number = float(value)
            if not math.isfinite(number):
                raise ValueError("projection_summary values must be finite")
            normalized_summary[metric] = number

    gains = tuple(float(value) for value in transferability_gains)
    if any(not math.isfinite(value) for value in gains):
        raise ValueError("transferability_gains must be finite")

    required_artifact_semantics = _artifact_semantics_for_category(decision.handoff_category)
    if required_artifact_semantics is None:
        if state_artifact is not None:
            raise ValueError(
                f"state_artifact is forbidden for handoff category {decision.handoff_category!r}"
            )
    else:
        if state_artifact is None:
            raise ValueError(
                f"state_artifact is required for handoff category {decision.handoff_category!r}"
            )
        _validate_artifact(state_artifact, axis_names)
        if state_artifact.artifact_semantics != required_artifact_semantics:
            raise ValueError(
                "state_artifact semantics do not match the handoff category"
            )

    if decision.transferability_category == "generalizing" and decision.evidence_scope == "empirical":
        if not gains:
            raise ValueError("empirical generalizing handoff requires independent transferability gains")
        if not all(value > 0.0 for value in gains):
            raise ValueError("empirical generalizing handoff requires all independent gains > 0")
    if decision.transferability_category == "non_generalizing" and gains:
        if not all(value <= 0.0 for value in gains):
            raise ValueError("non_generalizing handoff requires all supplied gains <= 0")

    provenance = {
        "source_contract": source_contract,
        "decision_receipt": decision_receipt,
        "source_fingerprint": source_fingerprint,
    }
    core = {
        "schema_id": SCHEMA_ID,
        "program_id": PROGRAM_ID,
        "producer": {"chapter": "N2", "repository": PRODUCER_REPOSITORY},
        "evidence_id": evidence_id,
        "axes": {
            "base": [axis.as_dict() for axis in base],
            "added": [axis.as_dict() for axis in added],
        },
        "handoff": decision.as_dict(),
        "projection_summary": normalized_summary,
        "transferability": {
            "category": decision.transferability_category,
            "independent_gains": list(gains),
        },
        "provenance": provenance,
        "state_artifact": None if state_artifact is None else state_artifact.as_dict(),
    }
    fingerprint = _payload_fingerprint(core)
    return N2ToN3Payload(
        schema_id=SCHEMA_ID,
        program_id=PROGRAM_ID,
        producer_chapter="N2",
        producer_repository=PRODUCER_REPOSITORY,
        evidence_id=evidence_id,
        base_axes=base,
        added_axes=added,
        handoff=decision,
        projection_summary=normalized_summary,
        transferability_gains=gains,
        source_contract=source_contract,
        decision_receipt=decision_receipt,
        source_fingerprint=source_fingerprint,
        state_artifact=state_artifact,
        fingerprint=fingerprint,
    )


def validate_n2_to_n3_payload(payload: Mapping[str, object]) -> str:
    """Validate a serialized payload by rebuilding it; return its fingerprint."""

    if payload.get("schema_id") != SCHEMA_ID:
        raise ValueError("unsupported N2 -> N3 payload schema_id")
    if payload.get("program_id") != PROGRAM_ID:
        raise ValueError("unexpected program_id")
    producer = payload.get("producer")
    if not isinstance(producer, Mapping):
        raise ValueError("producer must be an object")
    if producer.get("chapter") != "N2" or producer.get("repository") != PRODUCER_REPOSITORY:
        raise ValueError("unexpected payload producer")

    axes = payload.get("axes")
    if not isinstance(axes, Mapping):
        raise ValueError("axes must be an object")

    def parse_axes(value: object) -> tuple[AxisDescriptor, ...]:
        if not isinstance(value, list):
            raise ValueError("axis collection must be a list")
        result = []
        for item in value:
            if not isinstance(item, Mapping):
                raise ValueError("axis descriptor must be an object")
            result.append(
                AxisDescriptor(
                    name=str(item.get("name", "")),
                    semantic=str(item.get("semantic", "")),
                    units=(None if item.get("units") is None else str(item.get("units"))),
                    reference_frame=(
                        None
                        if item.get("reference_frame") is None
                        else str(item.get("reference_frame"))
                    ),
                )
            )
        return tuple(result)

    handoff_raw = payload.get("handoff")
    if not isinstance(handoff_raw, Mapping):
        raise ValueError("handoff must be an object")
    decision = N2ToN3HandoffDecision(
        evidence_scope=str(handoff_raw.get("evidence_scope")),  # type: ignore[arg-type]
        support_semantics=str(handoff_raw.get("support_semantics")),  # type: ignore[arg-type]
        axis_semantics_declared=bool(handoff_raw.get("axis_semantics_declared")),
        prospective_source_boundary_frozen=bool(
            handoff_raw.get("prospective_source_boundary_frozen")
        ),
        thickness_estimable=bool(handoff_raw.get("thickness_estimable")),
        transferability_category=str(handoff_raw.get("transferability_category")),  # type: ignore[arg-type]
        handoff_category=str(handoff_raw.get("handoff_category")),  # type: ignore[arg-type]
        projection_summary_allowed=bool(handoff_raw.get("projection_summary_allowed")),
        axis_resolved_state_allowed_for_method_testing=bool(
            handoff_raw.get("axis_resolved_state_allowed_for_method_testing")
        ),
        axis_resolved_species_state_allowed_for_empirical_n3=bool(
            handoff_raw.get("axis_resolved_species_state_allowed_for_empirical_n3")
        ),
        reason_codes=tuple(str(value) for value in handoff_raw.get("reason_codes", [])),
    )

    transferability = payload.get("transferability")
    if not isinstance(transferability, Mapping):
        raise ValueError("transferability must be an object")
    if transferability.get("category") != decision.transferability_category:
        raise ValueError("transferability category must match handoff decision")
    gains = transferability.get("independent_gains", [])
    if not isinstance(gains, list):
        raise ValueError("independent_gains must be a list")

    provenance = payload.get("provenance")
    if not isinstance(provenance, Mapping):
        raise ValueError("provenance must be an object")

    artifact_raw = payload.get("state_artifact")
    artifact = None
    if artifact_raw is not None:
        if not isinstance(artifact_raw, Mapping):
            raise ValueError("state_artifact must be an object or null")
        shape = artifact_raw.get("shape")
        axis_order = artifact_raw.get("axis_order")
        if not isinstance(shape, list) or not isinstance(axis_order, list):
            raise ValueError("state_artifact shape and axis_order must be lists")
        artifact = StateArtifact(
            artifact_semantics=str(artifact_raw.get("artifact_semantics")),
            uri=str(artifact_raw.get("uri", "")),
            sha256=str(artifact_raw.get("sha256", "")),
            media_type=str(artifact_raw.get("media_type", "")),
            shape=tuple(int(value) for value in shape),
            axis_order=tuple(str(value) for value in axis_order),
        )

    rebuilt = build_n2_to_n3_payload(
        evidence_id=str(payload.get("evidence_id", "")),
        decision=decision,
        base_axes=parse_axes(axes.get("base")),
        added_axes=parse_axes(axes.get("added")),
        projection_summary=(
            None
            if payload.get("projection_summary") is None
            else payload.get("projection_summary")  # type: ignore[arg-type]
        ),
        transferability_gains=[float(value) for value in gains],
        source_contract=(
            None if provenance.get("source_contract") is None else str(provenance.get("source_contract"))
        ),
        decision_receipt=(
            None if provenance.get("decision_receipt") is None else str(provenance.get("decision_receipt"))
        ),
        source_fingerprint=(
            None if provenance.get("source_fingerprint") is None else str(provenance.get("source_fingerprint"))
        ),
        state_artifact=artifact,
    )
    if payload.get("fingerprint") != rebuilt.fingerprint:
        raise ValueError("payload fingerprint mismatch")
    return rebuilt.fingerprint
