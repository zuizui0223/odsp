"""Checkpoint binding for declared evaluation-access event hashes."""
from __future__ import annotations

from dataclasses import asdict, dataclass
import re
from typing import Mapping, Sequence


_SHA256_RE = re.compile(r"^sha256:([0-9a-fA-F]{64})$", re.IGNORECASE)
_REQUIRED_CHECKPOINT_KEYS = {"event_index", "event_hash"}


@dataclass(frozen=True)
class EvaluationAccessCheckpointAudit:
    event_count: int
    checkpoint_count: int
    matched_checkpoint_count: int
    mismatched_checkpoint_count: int
    checkpoint_order_strictly_increasing: bool
    terminal_checkpoint_present: bool
    checkpoints_consistent: bool
    separation_category: str
    checkpoint_indices_emitted: bool
    checkpoint_hashes_emitted: bool
    automatic_external_timestamp_verification: bool
    automatic_witness_identity_verification: bool
    checkpoint_preexistence_assumed: bool
    real_world_log_completeness_assumed: bool
    aggregate_confidence_score_emitted: bool

    def as_dict(self) -> dict[str, object]:
        return asdict(self)


def _sha256(value: object, *, label: str) -> str:
    if not isinstance(value, str):
        raise ValueError(f"{label} must use sha256:<64 hexadecimal characters>")
    match = _SHA256_RE.fullmatch(value.strip())
    if match is None:
        raise ValueError(f"{label} must use sha256:<64 hexadecimal characters>")
    return "sha256:" + match.group(1).lower()


def _index(value: object) -> int:
    if isinstance(value, bool) or not isinstance(value, int) or value < 0:
        raise ValueError("checkpoint event_index must be a zero-based non-negative integer")
    return int(value)


def audit_evaluation_access_checkpoints(
    event_hashes: Sequence[object],
    checkpoints: Sequence[Mapping[str, object]],
) -> EvaluationAccessCheckpointAudit:
    """Check checkpoint commitments against selected hashes from one supplied event log.

    This is an internal consistency audit only. A match does not establish when a
    checkpoint was created, who retained it, or whether the supplied access log is
    complete in the real world.
    """

    normalized_event_hashes = tuple(
        _sha256(value, label="event hashes") for value in event_hashes
    )
    if not normalized_event_hashes:
        raise ValueError("event_hashes must contain at least one event hash")

    rows = tuple(checkpoints)
    if len(rows) < 2:
        raise ValueError("checkpoints must contain at least two checkpoint commitments")

    normalized_checkpoints: list[tuple[int, str]] = []
    seen_indices: set[int] = set()
    for raw in rows:
        if not isinstance(raw, Mapping):
            raise ValueError("each checkpoint must be a mapping")
        if set(raw) != _REQUIRED_CHECKPOINT_KEYS:
            raise ValueError("each checkpoint must contain exactly event_index and event_hash")
        index = _index(raw["event_index"])
        if index >= len(normalized_event_hashes):
            raise ValueError("checkpoint event_index is outside the supplied event hash range")
        if index in seen_indices:
            raise ValueError("checkpoint event_index values must be unique")
        seen_indices.add(index)
        normalized_checkpoints.append(
            (index, _sha256(raw["event_hash"], label="checkpoint event_hash"))
        )

    checkpoint_order_strictly_increasing = all(
        normalized_checkpoints[index][0] < normalized_checkpoints[index + 1][0]
        for index in range(len(normalized_checkpoints) - 1)
    )
    terminal_index = len(normalized_event_hashes) - 1
    terminal_checkpoint_present = any(
        index == terminal_index for index, _ in normalized_checkpoints
    )

    matched = sum(
        checkpoint_hash == normalized_event_hashes[index]
        for index, checkpoint_hash in normalized_checkpoints
    )
    mismatched = len(normalized_checkpoints) - matched
    consistent = (
        mismatched == 0
        and checkpoint_order_strictly_increasing
        and terminal_checkpoint_present
    )

    return EvaluationAccessCheckpointAudit(
        event_count=len(normalized_event_hashes),
        checkpoint_count=len(normalized_checkpoints),
        matched_checkpoint_count=matched,
        mismatched_checkpoint_count=mismatched,
        checkpoint_order_strictly_increasing=checkpoint_order_strictly_increasing,
        terminal_checkpoint_present=terminal_checkpoint_present,
        checkpoints_consistent=consistent,
        separation_category=(
            "evaluation_access_checkpoints_consistent"
            if consistent
            else "evaluation_access_checkpoint_mismatch"
        ),
        checkpoint_indices_emitted=False,
        checkpoint_hashes_emitted=False,
        automatic_external_timestamp_verification=False,
        automatic_witness_identity_verification=False,
        checkpoint_preexistence_assumed=False,
        real_world_log_completeness_assumed=False,
        aggregate_confidence_score_emitted=False,
    )
