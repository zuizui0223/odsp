"""Bind evaluation artifact-ID and SHA-256 access ledgers to one supplied manifest."""
from __future__ import annotations

from collections import Counter
from dataclasses import asdict, dataclass
from typing import Mapping, Sequence
import re

import numpy as np


_SHA256_RE = re.compile(r"^sha256:([0-9a-fA-F]{64})$", re.IGNORECASE)


@dataclass(frozen=True)
class EvaluationLedgerBindingStage:
    stage_name: str
    access_count: int
    unique_artifact_id_count: int
    duplicate_artifact_id_count: int
    unique_digest_count: int
    duplicate_digest_count: int
    missing_expected_digest_occurrence_count: int
    unexpected_declared_digest_occurrence_count: int
    binding_discrepancy_occurrence_count: int
    status: str

    def as_dict(self) -> dict[str, object]:
        return asdict(self)


@dataclass(frozen=True)
class EvaluationLedgerBindingAudit:
    stage_count: int
    stage_names: tuple[str, ...]
    final_evaluation_binding_match: bool
    final_content_alias_id_count: int
    mismatched_stage_count: int
    binding_discrepancy_occurrence_count: int
    duplicate_artifact_id_access_count: int
    duplicate_digest_access_count: int
    ledger_binding_consistent: bool
    separation_category: str
    expected_stage_coverage_checked: bool
    artifact_ids_emitted: bool
    digests_emitted: bool
    automatic_artifact_hashing: bool
    automatic_access_history_inference: bool
    manifest_completeness_assumed: bool
    semantic_equivalence_inferred: bool
    aggregate_confidence_score_emitted: bool
    stages: tuple[EvaluationLedgerBindingStage, ...]

    def as_dict(self) -> dict[str, object]:
        return {
            "stage_count": self.stage_count,
            "stage_names": list(self.stage_names),
            "final_evaluation_binding_match": self.final_evaluation_binding_match,
            "final_content_alias_id_count": self.final_content_alias_id_count,
            "mismatched_stage_count": self.mismatched_stage_count,
            "binding_discrepancy_occurrence_count": self.binding_discrepancy_occurrence_count,
            "duplicate_artifact_id_access_count": self.duplicate_artifact_id_access_count,
            "duplicate_digest_access_count": self.duplicate_digest_access_count,
            "ledger_binding_consistent": self.ledger_binding_consistent,
            "separation_category": self.separation_category,
            "expected_stage_coverage_checked": self.expected_stage_coverage_checked,
            "artifact_ids_emitted": self.artifact_ids_emitted,
            "digests_emitted": self.digests_emitted,
            "automatic_artifact_hashing": self.automatic_artifact_hashing,
            "automatic_access_history_inference": self.automatic_access_history_inference,
            "manifest_completeness_assumed": self.manifest_completeness_assumed,
            "semantic_equivalence_inferred": self.semantic_equivalence_inferred,
            "aggregate_confidence_score_emitted": self.aggregate_confidence_score_emitted,
            "stages": [row.as_dict() for row in self.stages],
        }


def _artifact_id(value: object, *, label: str) -> object:
    if value is None:
        raise ValueError(f"{label} must not be missing")
    try:
        hash(value)
    except TypeError as exc:
        raise ValueError(f"{label} must be a hashable scalar") from exc
    if isinstance(value, (float, np.floating)) and bool(np.isnan(value)):
        raise ValueError(f"{label} must not be missing")
    return value


def _digest(value: object, *, label: str) -> str:
    if value is None:
        raise ValueError(f"{label} must not be missing")
    if not isinstance(value, str):
        raise ValueError(f"{label} must use sha256:<64 hexadecimal characters>")
    match = _SHA256_RE.fullmatch(value.strip())
    if match is None:
        raise ValueError(f"{label} must use sha256:<64 hexadecimal characters>")
    return "sha256:" + match.group(1).lower()


def _stage_name(value: object) -> str:
    name = str(value).strip()
    if not name:
        raise ValueError("access stage names must be non-empty")
    return name


def _expected(values: Sequence[object]) -> tuple[str, ...]:
    names = tuple(_stage_name(value) for value in values)
    if not names:
        raise ValueError("expected_stage_names must contain at least one stage")
    if len(set(names)) != len(names):
        raise ValueError("expected stage names must be unique after canonicalization")
    return tuple(sorted(names))


def _normalize_id_stages(
    values: Mapping[object, Sequence[object]],
    *,
    manifest: Mapping[object, str],
) -> dict[str, tuple[object, ...]]:
    if not values:
        raise ValueError("accessed_artifact_ids_by_stage must contain at least one stage")
    result: dict[str, tuple[object, ...]] = {}
    for raw_name, raw_ids in values.items():
        name = _stage_name(raw_name)
        if name in result:
            raise ValueError("artifact-ID stage names must be unique after canonicalization")
        ids = tuple(raw_ids)
        if not ids:
            raise ValueError(f"access stage {name!r} must contain at least one artifact ID")
        normalized = []
        for value in ids:
            artifact_id = _artifact_id(value, label=f"artifact IDs for stage {name!r}")
            if artifact_id not in manifest:
                raise ValueError("accessed artifact ID is missing from artifact_digest_by_id")
            normalized.append(artifact_id)
        result[name] = tuple(normalized)
    return dict(sorted(result.items()))


def _normalize_digest_stages(
    values: Mapping[object, Sequence[object]],
) -> dict[str, tuple[str, ...]]:
    if not values:
        raise ValueError("accessed_artifact_digests_by_stage must contain at least one stage")
    result: dict[str, tuple[str, ...]] = {}
    for raw_name, raw_digests in values.items():
        name = _stage_name(raw_name)
        if name in result:
            raise ValueError("digest stage names must be unique after canonicalization")
        digests = tuple(raw_digests)
        if not digests:
            raise ValueError(f"access stage {name!r} must contain at least one digest")
        result[name] = tuple(
            _digest(value, label=f"digests for stage {name!r}") for value in digests
        )
    return dict(sorted(result.items()))


def audit_evaluation_ledger_binding(
    final_evaluation_artifact_id: object,
    final_evaluation_digest: object,
    artifact_digest_by_id: Mapping[object, object],
    accessed_artifact_ids_by_stage: Mapping[object, Sequence[object]],
    accessed_artifact_digests_by_stage: Mapping[object, Sequence[object]],
    *,
    expected_stage_names: Sequence[object] | None = None,
) -> EvaluationLedgerBindingAudit:
    """Check internal binding between declared artifact IDs and SHA-256 ledgers."""
    final_id = _artifact_id(
        final_evaluation_artifact_id, label="final_evaluation_artifact_id"
    )
    final_digest = _digest(final_evaluation_digest, label="final_evaluation_digest")
    if not artifact_digest_by_id:
        raise ValueError("artifact_digest_by_id must contain at least one artifact")

    manifest: dict[object, str] = {}
    for raw_id, raw_digest in artifact_digest_by_id.items():
        artifact_id = _artifact_id(raw_id, label="artifact_digest_by_id keys")
        manifest[artifact_id] = _digest(
            raw_digest, label="artifact_digest_by_id values"
        )
    if final_id not in manifest:
        raise ValueError("final_evaluation_artifact_id is missing from artifact_digest_by_id")

    id_stages = _normalize_id_stages(
        accessed_artifact_ids_by_stage, manifest=manifest
    )
    digest_stages = _normalize_digest_stages(accessed_artifact_digests_by_stage)
    if tuple(id_stages) != tuple(digest_stages):
        raise ValueError("artifact-ID and digest stage coverage must exactly match")

    expected_checked = expected_stage_names is not None
    if expected_stage_names is not None:
        expected = _expected(expected_stage_names)
        if tuple(id_stages) != expected:
            missing = set(expected) - set(id_stages)
            extra = set(id_stages) - set(expected)
            if missing and not extra:
                raise ValueError("expected access stage coverage includes a missing declared stage")
            if extra and not missing:
                raise ValueError("declared access stages include an unexpected extra stage")
            raise ValueError("expected access stage coverage must exactly match declared stages")

    final_binding_match = manifest[final_id] == final_digest
    alias_count = sum(
        artifact_id != final_id and digest == final_digest
        for artifact_id, digest in manifest.items()
    )

    rows: list[EvaluationLedgerBindingStage] = []
    mismatched_stage_count = 0
    discrepancy_total = 0
    duplicate_id_total = 0
    duplicate_digest_total = 0
    for name in id_stages:
        ids = id_stages[name]
        declared_digests = digest_stages[name]
        expected_digests = tuple(manifest[artifact_id] for artifact_id in ids)
        expected_counts = Counter(expected_digests)
        declared_counts = Counter(declared_digests)
        missing = sum((expected_counts - declared_counts).values())
        unexpected = sum((declared_counts - expected_counts).values())
        discrepancy = max(missing, unexpected)
        duplicate_ids = len(ids) - len(set(ids))
        duplicate_digests = len(declared_digests) - len(set(declared_digests))
        matched = missing == 0 and unexpected == 0
        if not matched:
            mismatched_stage_count += 1
        discrepancy_total += discrepancy
        duplicate_id_total += duplicate_ids
        duplicate_digest_total += duplicate_digests
        rows.append(
            EvaluationLedgerBindingStage(
                stage_name=name,
                access_count=len(ids),
                unique_artifact_id_count=len(set(ids)),
                duplicate_artifact_id_count=duplicate_ids,
                unique_digest_count=len(set(declared_digests)),
                duplicate_digest_count=duplicate_digests,
                missing_expected_digest_occurrence_count=missing,
                unexpected_declared_digest_occurrence_count=unexpected,
                binding_discrepancy_occurrence_count=discrepancy,
                status="stage_binding_match" if matched else "stage_binding_mismatch",
            )
        )

    consistent = final_binding_match and mismatched_stage_count == 0
    return EvaluationLedgerBindingAudit(
        stage_count=len(rows),
        stage_names=tuple(row.stage_name for row in rows),
        final_evaluation_binding_match=final_binding_match,
        final_content_alias_id_count=int(alias_count),
        mismatched_stage_count=mismatched_stage_count,
        binding_discrepancy_occurrence_count=discrepancy_total,
        duplicate_artifact_id_access_count=duplicate_id_total,
        duplicate_digest_access_count=duplicate_digest_total,
        ledger_binding_consistent=consistent,
        separation_category=(
            "evaluation_ledgers_consistently_bound"
            if consistent
            else "evaluation_ledger_binding_mismatch"
        ),
        expected_stage_coverage_checked=expected_checked,
        artifact_ids_emitted=False,
        digests_emitted=False,
        automatic_artifact_hashing=False,
        automatic_access_history_inference=False,
        manifest_completeness_assumed=False,
        semantic_equivalence_inferred=False,
        aggregate_confidence_score_emitted=False,
        stages=tuple(rows),
    )
