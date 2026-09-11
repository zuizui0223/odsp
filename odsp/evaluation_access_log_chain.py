"""Internal hash-chain provenance for declared evaluation-access event logs."""
from __future__ import annotations

from collections import defaultdict
from dataclasses import asdict, dataclass
from hashlib import sha256
import json
import re
from typing import Mapping, Sequence


_SHA256_RE = re.compile(r"^sha256:([0-9a-fA-F]{64})$", re.IGNORECASE)
GENESIS_EVENT_HASH = "sha256:" + "0" * 64
_REQUIRED_EVENT_KEYS = {
    "sequence_index",
    "stage_name",
    "artifact_id",
    "artifact_digest",
    "previous_event_hash",
    "event_hash",
}


@dataclass(frozen=True)
class EvaluationAccessLogStage:
    stage_name: str
    event_count: int
    unique_artifact_id_count: int
    duplicate_artifact_id_count: int
    unique_digest_count: int
    duplicate_digest_count: int
    artifact_id_ledger_match: bool
    digest_ledger_match: bool
    status: str

    def as_dict(self) -> dict[str, object]:
        return asdict(self)


@dataclass(frozen=True)
class EvaluationAccessLogChainAudit:
    event_count: int
    stage_count: int
    stage_names: tuple[str, ...]
    committed_event_count_match: bool
    terminal_event_hash_match: bool
    sequence_contiguous: bool
    previous_hash_chain_match: bool
    recomputed_event_hash_match: bool
    stage_artifact_id_ledger_match: bool
    stage_digest_ledger_match: bool
    mismatched_stage_count: int
    duplicate_artifact_id_access_count: int
    duplicate_digest_access_count: int
    log_chain_consistent: bool
    separation_category: str
    artifact_ids_emitted: bool
    digests_emitted: bool
    event_hashes_emitted: bool
    automatic_external_anchor_verification: bool
    automatic_access_history_inference: bool
    real_world_log_completeness_assumed: bool
    aggregate_confidence_score_emitted: bool
    stages: tuple[EvaluationAccessLogStage, ...]

    def as_dict(self) -> dict[str, object]:
        return {
            "event_count": self.event_count,
            "stage_count": self.stage_count,
            "stage_names": list(self.stage_names),
            "committed_event_count_match": self.committed_event_count_match,
            "terminal_event_hash_match": self.terminal_event_hash_match,
            "sequence_contiguous": self.sequence_contiguous,
            "previous_hash_chain_match": self.previous_hash_chain_match,
            "recomputed_event_hash_match": self.recomputed_event_hash_match,
            "stage_artifact_id_ledger_match": self.stage_artifact_id_ledger_match,
            "stage_digest_ledger_match": self.stage_digest_ledger_match,
            "mismatched_stage_count": self.mismatched_stage_count,
            "duplicate_artifact_id_access_count": self.duplicate_artifact_id_access_count,
            "duplicate_digest_access_count": self.duplicate_digest_access_count,
            "log_chain_consistent": self.log_chain_consistent,
            "separation_category": self.separation_category,
            "artifact_ids_emitted": self.artifact_ids_emitted,
            "digests_emitted": self.digests_emitted,
            "event_hashes_emitted": self.event_hashes_emitted,
            "automatic_external_anchor_verification": self.automatic_external_anchor_verification,
            "automatic_access_history_inference": self.automatic_access_history_inference,
            "real_world_log_completeness_assumed": self.real_world_log_completeness_assumed,
            "aggregate_confidence_score_emitted": self.aggregate_confidence_score_emitted,
            "stages": [row.as_dict() for row in self.stages],
        }


def _sha256(value: object, *, label: str) -> str:
    if not isinstance(value, str):
        raise ValueError(f"{label} must use sha256:<64 hexadecimal characters>")
    match = _SHA256_RE.fullmatch(value.strip())
    if match is None:
        raise ValueError(f"{label} must use sha256:<64 hexadecimal characters>")
    return "sha256:" + match.group(1).lower()


def _text(value: object, *, label: str) -> str:
    if not isinstance(value, str):
        raise ValueError(f"{label} must be a non-empty string")
    result = value.strip()
    if not result:
        raise ValueError(f"{label} must be a non-empty string")
    return result


def _sequence_index(value: object) -> int:
    if isinstance(value, bool) or not isinstance(value, int) or value < 0:
        raise ValueError("sequence_index must be a zero-based non-negative integer")
    return int(value)


def _canonical_payload(
    sequence_index: int,
    stage_name: str,
    artifact_id: str,
    artifact_digest: str,
    previous_event_hash: str,
) -> bytes:
    payload = {
        "artifact_digest": artifact_digest,
        "artifact_id": artifact_id,
        "previous_event_hash": previous_event_hash,
        "sequence_index": sequence_index,
        "stage_name": stage_name,
    }
    return json.dumps(
        payload,
        sort_keys=True,
        separators=(",", ":"),
        ensure_ascii=False,
    ).encode("utf-8")


def compute_access_event_hash(
    sequence_index: int,
    stage_name: str,
    artifact_id: str,
    artifact_digest: str,
    previous_event_hash: str,
) -> str:
    """Return the canonical SHA-256 event hash used by this audit."""
    seq = _sequence_index(sequence_index)
    stage = _text(stage_name, label="stage_name")
    artifact = _text(artifact_id, label="artifact_id")
    digest = _sha256(artifact_digest, label="artifact_digest")
    previous = _sha256(previous_event_hash, label="previous_event_hash")
    return "sha256:" + sha256(
        _canonical_payload(seq, stage, artifact, digest, previous)
    ).hexdigest()


def _normalize_stage_ids(
    values: Mapping[object, Sequence[object]],
) -> dict[str, tuple[str, ...]]:
    if not values:
        raise ValueError("accessed_artifact_ids_by_stage must contain at least one stage")
    result: dict[str, tuple[str, ...]] = {}
    for raw_stage, raw_ids in values.items():
        stage = _text(raw_stage, label="access stage names")
        if stage in result:
            raise ValueError("access stage names must be unique after canonicalization")
        ids = tuple(_text(value, label=f"artifact IDs for stage {stage!r}") for value in raw_ids)
        if not ids:
            raise ValueError(f"access stage {stage!r} must contain at least one artifact ID")
        result[stage] = ids
    return dict(sorted(result.items()))


def _normalize_stage_digests(
    values: Mapping[object, Sequence[object]],
) -> dict[str, tuple[str, ...]]:
    if not values:
        raise ValueError("accessed_artifact_digests_by_stage must contain at least one stage")
    result: dict[str, tuple[str, ...]] = {}
    for raw_stage, raw_digests in values.items():
        stage = _text(raw_stage, label="access stage names")
        if stage in result:
            raise ValueError("access stage names must be unique after canonicalization")
        digests = tuple(
            _sha256(value, label=f"digests for stage {stage!r}") for value in raw_digests
        )
        if not digests:
            raise ValueError(f"access stage {stage!r} must contain at least one digest")
        result[stage] = digests
    return dict(sorted(result.items()))


def audit_evaluation_access_log_chain(
    events: Sequence[Mapping[str, object]],
    committed_event_count: int,
    committed_terminal_event_hash: object,
    accessed_artifact_ids_by_stage: Mapping[object, Sequence[object]],
    accessed_artifact_digests_by_stage: Mapping[object, Sequence[object]],
) -> EvaluationAccessLogChainAudit:
    """Check a supplied access log's internal chain, commitment, and ledger binding."""
    event_rows = tuple(events)
    if not event_rows:
        raise ValueError("events must contain at least one access event")
    if isinstance(committed_event_count, bool) or not isinstance(committed_event_count, int) or committed_event_count < 1:
        raise ValueError("committed_event_count must be a positive integer")
    terminal_commitment = _sha256(
        committed_terminal_event_hash, label="committed_terminal_event_hash"
    )

    normalized: list[dict[str, object]] = []
    for raw in event_rows:
        if not isinstance(raw, Mapping):
            raise ValueError("each access event must be a mapping")
        if set(raw) != _REQUIRED_EVENT_KEYS:
            raise ValueError("each access event must contain exactly the canonical event fields")
        normalized.append(
            {
                "sequence_index": _sequence_index(raw["sequence_index"]),
                "stage_name": _text(raw["stage_name"], label="stage_name"),
                "artifact_id": _text(raw["artifact_id"], label="artifact_id"),
                "artifact_digest": _sha256(raw["artifact_digest"], label="artifact_digest"),
                "previous_event_hash": _sha256(raw["previous_event_hash"], label="previous_event_hash"),
                "event_hash": _sha256(raw["event_hash"], label="event_hash"),
            }
        )

    sequence_contiguous = all(
        row["sequence_index"] == index for index, row in enumerate(normalized)
    )
    previous_hash_chain_match = True
    recomputed_event_hash_match = True
    for index, row in enumerate(normalized):
        expected_previous = GENESIS_EVENT_HASH if index == 0 else normalized[index - 1]["event_hash"]
        if row["previous_event_hash"] != expected_previous:
            previous_hash_chain_match = False
        recomputed = compute_access_event_hash(
            row["sequence_index"],
            row["stage_name"],
            row["artifact_id"],
            row["artifact_digest"],
            row["previous_event_hash"],
        )
        if row["event_hash"] != recomputed:
            recomputed_event_hash_match = False

    committed_event_count_match = len(normalized) == committed_event_count
    terminal_event_hash_match = normalized[-1]["event_hash"] == terminal_commitment

    derived_ids: dict[str, list[str]] = defaultdict(list)
    derived_digests: dict[str, list[str]] = defaultdict(list)
    for row in normalized:
        stage = row["stage_name"]
        derived_ids[stage].append(row["artifact_id"])
        derived_digests[stage].append(row["artifact_digest"])
    derived_ids_t = {key: tuple(value) for key, value in derived_ids.items()}
    derived_digests_t = {key: tuple(value) for key, value in derived_digests.items()}

    declared_ids = _normalize_stage_ids(accessed_artifact_ids_by_stage)
    declared_digests = _normalize_stage_digests(accessed_artifact_digests_by_stage)
    all_stages = tuple(sorted(set(derived_ids_t) | set(declared_ids) | set(declared_digests)))

    stage_rows: list[EvaluationAccessLogStage] = []
    mismatch_count = 0
    duplicate_id_total = 0
    duplicate_digest_total = 0
    for stage in all_stages:
        event_ids = derived_ids_t.get(stage, ())
        event_digests = derived_digests_t.get(stage, ())
        ids_match = event_ids == declared_ids.get(stage, ())
        digests_match = event_digests == declared_digests.get(stage, ())
        if not (ids_match and digests_match):
            mismatch_count += 1
        duplicate_ids = len(event_ids) - len(set(event_ids))
        duplicate_digests = len(event_digests) - len(set(event_digests))
        duplicate_id_total += duplicate_ids
        duplicate_digest_total += duplicate_digests
        stage_rows.append(
            EvaluationAccessLogStage(
                stage_name=stage,
                event_count=len(event_ids),
                unique_artifact_id_count=len(set(event_ids)),
                duplicate_artifact_id_count=duplicate_ids,
                unique_digest_count=len(set(event_digests)),
                duplicate_digest_count=duplicate_digests,
                artifact_id_ledger_match=ids_match,
                digest_ledger_match=digests_match,
                status=(
                    "stage_log_ledger_match"
                    if ids_match and digests_match
                    else "stage_log_ledger_mismatch"
                ),
            )
        )

    stage_artifact_id_ledger_match = all(row.artifact_id_ledger_match for row in stage_rows)
    stage_digest_ledger_match = all(row.digest_ledger_match for row in stage_rows)
    consistent = all(
        (
            committed_event_count_match,
            terminal_event_hash_match,
            sequence_contiguous,
            previous_hash_chain_match,
            recomputed_event_hash_match,
            stage_artifact_id_ledger_match,
            stage_digest_ledger_match,
        )
    )
    return EvaluationAccessLogChainAudit(
        event_count=len(normalized),
        stage_count=len(stage_rows),
        stage_names=tuple(row.stage_name for row in stage_rows),
        committed_event_count_match=committed_event_count_match,
        terminal_event_hash_match=terminal_event_hash_match,
        sequence_contiguous=sequence_contiguous,
        previous_hash_chain_match=previous_hash_chain_match,
        recomputed_event_hash_match=recomputed_event_hash_match,
        stage_artifact_id_ledger_match=stage_artifact_id_ledger_match,
        stage_digest_ledger_match=stage_digest_ledger_match,
        mismatched_stage_count=mismatch_count,
        duplicate_artifact_id_access_count=duplicate_id_total,
        duplicate_digest_access_count=duplicate_digest_total,
        log_chain_consistent=consistent,
        separation_category=(
            "evaluation_access_log_chain_consistent"
            if consistent
            else "evaluation_access_log_chain_mismatch"
        ),
        artifact_ids_emitted=False,
        digests_emitted=False,
        event_hashes_emitted=False,
        automatic_external_anchor_verification=False,
        automatic_access_history_inference=False,
        real_world_log_completeness_assumed=False,
        aggregate_confidence_score_emitted=False,
        stages=tuple(stage_rows),
    )
