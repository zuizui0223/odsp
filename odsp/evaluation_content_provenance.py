"""Provenance audit for byte-identical pre-final access to final-evaluation content."""
from __future__ import annotations

from dataclasses import asdict, dataclass
from typing import Mapping, Sequence
import re


_SHA256_RE = re.compile(r"^sha256:([0-9a-fA-F]{64})$", re.IGNORECASE)


@dataclass(frozen=True)
class EvaluationContentStage:
    stage_name: str
    access_count: int
    unique_digest_count: int
    duplicate_digest_count: int
    final_evaluation_content_match_count: int
    status: str

    def as_dict(self) -> dict[str, object]:
        return asdict(self)


@dataclass(frozen=True)
class EvaluationContentProvenanceAudit:
    stage_count: int
    stage_names: tuple[str, ...]
    leaking_stage_count: int
    final_evaluation_content_match_occurrence_count: int
    unique_final_evaluation_content_match_count: int
    final_evaluation_content_accessed: bool
    maximum_stage_final_content_match_count: int
    duplicate_digest_count: int
    separation_category: str
    expected_stage_coverage_checked: bool
    digests_emitted: bool
    automatic_artifact_hashing: bool
    automatic_access_history_inference: bool
    ledger_completeness_assumed: bool
    semantic_equivalence_inferred: bool
    aggregate_confidence_score_emitted: bool
    stages: tuple[EvaluationContentStage, ...]

    def as_dict(self) -> dict[str, object]:
        return {
            "stage_count": self.stage_count,
            "stage_names": list(self.stage_names),
            "leaking_stage_count": self.leaking_stage_count,
            "final_evaluation_content_match_occurrence_count": self.final_evaluation_content_match_occurrence_count,
            "unique_final_evaluation_content_match_count": self.unique_final_evaluation_content_match_count,
            "final_evaluation_content_accessed": self.final_evaluation_content_accessed,
            "maximum_stage_final_content_match_count": self.maximum_stage_final_content_match_count,
            "duplicate_digest_count": self.duplicate_digest_count,
            "separation_category": self.separation_category,
            "expected_stage_coverage_checked": self.expected_stage_coverage_checked,
            "digests_emitted": self.digests_emitted,
            "automatic_artifact_hashing": self.automatic_artifact_hashing,
            "automatic_access_history_inference": self.automatic_access_history_inference,
            "ledger_completeness_assumed": self.ledger_completeness_assumed,
            "semantic_equivalence_inferred": self.semantic_equivalence_inferred,
            "aggregate_confidence_score_emitted": self.aggregate_confidence_score_emitted,
            "stages": [row.as_dict() for row in self.stages],
        }


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


def audit_evaluation_content_provenance(
    final_evaluation_digest: object,
    accessed_artifact_digests_by_stage: Mapping[object, Sequence[object]],
    *,
    expected_stage_names: Sequence[object] | None = None,
) -> EvaluationContentProvenanceAudit:
    """Check a declared digest ledger for byte-identical final-artifact reuse."""
    final_digest = _digest(final_evaluation_digest, label="final_evaluation_digest")
    if not accessed_artifact_digests_by_stage:
        raise ValueError("accessed_artifact_digests_by_stage must contain at least one stage")

    stages: dict[str, tuple[str, ...]] = {}
    for raw_name, raw_digests in accessed_artifact_digests_by_stage.items():
        name = _stage_name(raw_name)
        if name in stages:
            raise ValueError("access stage names must be unique after canonicalization")
        raw = tuple(raw_digests)
        if not raw:
            raise ValueError(f"access stage {name!r} must contain at least one digest")
        stages[name] = tuple(
            _digest(value, label=f"digests for stage {name!r}") for value in raw
        )
    stages = dict(sorted(stages.items()))

    expected_checked = expected_stage_names is not None
    if expected_stage_names is not None:
        expected = _expected(expected_stage_names)
        actual = tuple(stages)
        if actual != expected:
            missing = set(expected) - set(actual)
            extra = set(actual) - set(expected)
            if missing and not extra:
                raise ValueError("expected access stage coverage includes a missing declared stage")
            if extra and not missing:
                raise ValueError("declared access stages include an unexpected extra stage")
            raise ValueError("expected access stage coverage must exactly match declared stages")

    rows: list[EvaluationContentStage] = []
    leaking_stage_count = 0
    occurrence_count = 0
    maximum_stage_count = 0
    duplicate_count = 0
    for name, digests in stages.items():
        unique = set(digests)
        duplicates = len(digests) - len(unique)
        final_count = sum(value == final_digest for value in digests)
        status = (
            "final_evaluation_content_leakage"
            if final_count
            else "final_evaluation_content_not_accessed_in_declared_pre_final_stages"
        )
        if final_count:
            leaking_stage_count += 1
        occurrence_count += final_count
        maximum_stage_count = max(maximum_stage_count, final_count)
        duplicate_count += duplicates
        rows.append(EvaluationContentStage(
            stage_name=name,
            access_count=len(digests),
            unique_digest_count=len(unique),
            duplicate_digest_count=duplicates,
            final_evaluation_content_match_count=final_count,
            status=status,
        ))

    leaked = occurrence_count > 0
    return EvaluationContentProvenanceAudit(
        stage_count=len(rows),
        stage_names=tuple(row.stage_name for row in rows),
        leaking_stage_count=leaking_stage_count,
        final_evaluation_content_match_occurrence_count=occurrence_count,
        unique_final_evaluation_content_match_count=1 if leaked else 0,
        final_evaluation_content_accessed=leaked,
        maximum_stage_final_content_match_count=maximum_stage_count,
        duplicate_digest_count=duplicate_count,
        separation_category=(
            "final_evaluation_content_leakage"
            if leaked
            else "final_evaluation_content_not_accessed_in_declared_pre_final_stages"
        ),
        expected_stage_coverage_checked=expected_checked,
        digests_emitted=False,
        automatic_artifact_hashing=False,
        automatic_access_history_inference=False,
        ledger_completeness_assumed=False,
        semantic_equivalence_inferred=False,
        aggregate_confidence_score_emitted=False,
        stages=tuple(rows),
    )
