"""Deterministic, outcome-blind screen for Chapter N2 empirical candidates.

This module consumes only source/measurement-architecture declarations. It must
not read observed z/t distributions, niche-thickness outputs, projection loss,
or held-out biological scores.
"""
from __future__ import annotations

from dataclasses import asdict, dataclass
import hashlib
import json
from typing import Mapping, Sequence

from .empirical_axis_admission import (
    EmpiricalAxisArchitecture,
    assess_empirical_axis_architecture,
)


@dataclass(frozen=True)
class ScreenedCandidate:
    candidate_id: str
    admitted: bool
    reasons: tuple[str, ...]
    architecture_fingerprint: str
    feature_vector: tuple[bool, ...]

    def as_dict(self) -> dict[str, object]:
        return asdict(self)


@dataclass(frozen=True)
class ArchitectureScreenResult:
    screen_id: str
    selection_id: str
    selected_candidate_id: str
    candidates: tuple[ScreenedCandidate, ...]
    fingerprint: str
    outcome_metrics_computed: bool = False

    def as_dict(self) -> dict[str, object]:
        return asdict(self)


def _bool_vector(value: object) -> tuple[bool, ...]:
    if not isinstance(value, list) or not value:
        raise ValueError("feature_vector must be a non-empty list")
    if any(type(item) is not bool for item in value):
        raise ValueError("feature_vector entries must be booleans")
    return tuple(value)


def _architecture_from_mapping(value: Mapping[str, object]) -> EmpiricalAxisArchitecture:
    return EmpiricalAxisArchitecture(
        architecture_id=str(value["architecture_id"]),
        axis_kind=str(value["axis_kind"]),
        xy_and_axis_same_event=bool(value["xy_and_axis_same_event"]),
        axis_is_native_biological_or_structural_state=bool(
            value["axis_is_native_biological_or_structural_state"]
        ),
        effort_denominator_available=bool(value["effort_denominator_available"]),
        prospective_abstention_if_effort_unavailable=bool(
            value["prospective_abstention_if_effort_unavailable"]
        ),
        cluster_identifier_available=bool(value["cluster_identifier_available"]),
        source_precision_preserved=bool(value["source_precision_preserved"]),
        sensor_schedule_or_effort_semantics_preserved=bool(
            value["sensor_schedule_or_effort_semantics_preserved"]
        ),
        public_reproducible_data=bool(value["public_reproducible_data"]),
        source_version_pinnable=bool(value["source_version_pinnable"]),
        structural_preflight_without_axis_outcomes=bool(
            value["structural_preflight_without_axis_outcomes"]
        ),
        contextual_proxy_used_as_axis=bool(value.get("contextual_proxy_used_as_axis", False)),
        upload_time_used_as_biological_time=bool(
            value.get("upload_time_used_as_biological_time", False)
        ),
    )


def _ranking_key(candidate: ScreenedCandidate) -> tuple[object, ...]:
    # False sorts before True, so invert each source-only quality feature to make
    # higher-quality vectors rank first. Candidate ID is the frozen tie-break.
    return tuple(not flag for flag in candidate.feature_vector) + (candidate.candidate_id,)


def run_architecture_screen(
    screen: Mapping[str, object],
    selection: Mapping[str, object],
) -> ArchitectureScreenResult:
    """Evaluate the frozen architecture universe and enforce deterministic selection."""

    if not bool(screen.get("candidate_universe_frozen")):
        raise ValueError("candidate universe must be frozen before screening")
    if bool(selection.get("selection_uses_biological_outcomes")):
        raise ValueError("architecture selection may not use biological outcomes")
    if screen.get("screen_id") != selection.get("screen_id"):
        raise ValueError("selection references a different screen")

    screen_candidates = screen.get("candidates")
    selection_candidates = selection.get("candidates")
    if not isinstance(screen_candidates, list) or not isinstance(selection_candidates, list):
        raise ValueError("screen and selection candidates must be lists")

    priority_by_id: dict[str, Mapping[str, object]] = {}
    for item in selection_candidates:
        if not isinstance(item, Mapping):
            raise ValueError("selection candidate must be an object")
        candidate_id = str(item.get("candidate_id", ""))
        if not candidate_id or candidate_id in priority_by_id:
            raise ValueError("selection candidate IDs must be unique and non-empty")
        priority_by_id[candidate_id] = item

    screened: list[ScreenedCandidate] = []
    for item in screen_candidates:
        if not isinstance(item, Mapping):
            raise ValueError("screen candidate must be an object")
        candidate_id = str(item.get("candidate_id", ""))
        if candidate_id not in priority_by_id:
            raise ValueError(f"candidate {candidate_id!r} missing from selection manifest")
        architecture = item.get("architecture")
        if not isinstance(architecture, Mapping):
            raise ValueError(f"candidate {candidate_id!r} lacks architecture object")
        spec = _architecture_from_mapping(architecture)
        if spec.architecture_id != candidate_id:
            raise ValueError(f"candidate/architecture ID mismatch for {candidate_id!r}")
        admission = assess_empirical_axis_architecture(spec)
        priority = priority_by_id[candidate_id]
        expected = bool(priority.get("architecture_admitted_expected"))
        if admission.admitted != expected:
            raise ValueError(
                f"architecture admission changed for {candidate_id}: "
                f"expected {expected}, observed {admission.admitted}"
            )
        screened.append(
            ScreenedCandidate(
                candidate_id=candidate_id,
                admitted=admission.admitted,
                reasons=admission.reasons,
                architecture_fingerprint=admission.fingerprint,
                feature_vector=_bool_vector(priority.get("feature_vector")),
            )
        )

    if set(priority_by_id) != {candidate.candidate_id for candidate in screened}:
        raise ValueError("screen and selection candidate universes differ")

    admitted = [candidate for candidate in screened if candidate.admitted]
    if not admitted:
        raise ValueError("no architecture-admitted candidate remains")
    selected = min(admitted, key=_ranking_key).candidate_id
    declared = str(selection.get("selected_candidate_id", ""))
    if selected != declared:
        raise ValueError(
            f"declared selected candidate {declared!r} does not match deterministic {selected!r}"
        )

    payload = {
        "screen_id": screen["screen_id"],
        "selection_id": selection["selection_id"],
        "selected_candidate_id": selected,
        "candidates": [candidate.as_dict() for candidate in screened],
        "outcome_metrics_computed": False,
    }
    fingerprint = hashlib.sha256(
        json.dumps(payload, sort_keys=True, separators=(",", ":")).encode("utf-8")
    ).hexdigest()
    return ArchitectureScreenResult(
        screen_id=str(screen["screen_id"]),
        selection_id=str(selection["selection_id"]),
        selected_candidate_id=selected,
        candidates=tuple(screened),
        fingerprint=fingerprint,
        outcome_metrics_computed=False,
    )
