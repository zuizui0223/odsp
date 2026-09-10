"""Provenance audit for pre-final access to a declared final-evaluation artifact."""
from __future__ import annotations

from dataclasses import asdict, dataclass
from typing import Mapping, Sequence

import numpy as np


@dataclass(frozen=True)
class EvaluationAccessStage:
    stage_name: str
    access_count: int
    unique_access_count: int
    duplicate_access_count: int
    final_evaluation_access_count: int
    status: str

    def as_dict(self) -> dict[str, object]:
        return asdict(self)


@dataclass(frozen=True)
class EvaluationAccessProvenanceAudit:
    stage_count: int
    stage_names: tuple[str, ...]
    leaking_stage_count: int
    final_evaluation_access_occurrence_count: int
    final_evaluation_accessed: bool
    maximum_stage_final_access_count: int
    duplicate_access_count: int
    separation_category: str
    expected_stage_coverage_checked: bool
    accessed_artifact_ids_emitted: bool
    automatic_access_history_inference: bool
    ledger_completeness_assumed: bool
    automatic_candidate_selection: bool
    aggregate_confidence_score_emitted: bool
    stages: tuple[EvaluationAccessStage, ...]

    def as_dict(self) -> dict[str, object]:
        return {
            "stage_count": self.stage_count,
            "stage_names": list(self.stage_names),
            "leaking_stage_count": self.leaking_stage_count,
            "final_evaluation_access_occurrence_count": self.final_evaluation_access_occurrence_count,
            "final_evaluation_accessed": self.final_evaluation_accessed,
            "maximum_stage_final_access_count": self.maximum_stage_final_access_count,
            "duplicate_access_count": self.duplicate_access_count,
            "separation_category": self.separation_category,
            "expected_stage_coverage_checked": self.expected_stage_coverage_checked,
            "accessed_artifact_ids_emitted": self.accessed_artifact_ids_emitted,
            "automatic_access_history_inference": self.automatic_access_history_inference,
            "ledger_completeness_assumed": self.ledger_completeness_assumed,
            "automatic_candidate_selection": self.automatic_candidate_selection,
            "aggregate_confidence_score_emitted": self.aggregate_confidence_score_emitted,
            "stages": [row.as_dict() for row in self.stages],
        }


def _validate_id(value: object, *, label: str) -> None:
    if value is None:
        raise ValueError(f"{label} must not be missing")
    try:
        hash(value)
    except TypeError as exc:
        raise ValueError(f"{label} must be a hashable scalar") from exc
    if isinstance(value, (float, np.floating)) and bool(np.isnan(value)):
        raise ValueError(f"{label} must not be missing")


def _stage_name(value: object) -> str:
    name = str(value).strip()
    if not name:
        raise ValueError("access stage names must be non-empty")
    return name


def _expected(values: Sequence[object]) -> tuple[str, ...]:
    names = tuple(_stage_name(v) for v in values)
    if not names:
        raise ValueError("expected_stage_names must contain at least one stage")
    if len(set(names)) != len(names):
        raise ValueError("expected stage names must be unique after canonicalization")
    return tuple(sorted(names))


def audit_evaluation_access_provenance(
    final_evaluation_artifact_id: object,
    accessed_artifact_ids_by_stage: Mapping[object, Sequence[object]],
    *,
    expected_stage_names: Sequence[object] | None = None,
) -> EvaluationAccessProvenanceAudit:
    """Check a declared pre-final access ledger for direct final-artifact reuse."""
    _validate_id(final_evaluation_artifact_id, label="final_evaluation_artifact_id")
    if not accessed_artifact_ids_by_stage:
        raise ValueError("accessed_artifact_ids_by_stage must contain at least one stage")

    stages: dict[str, tuple[object, ...]] = {}
    for raw_name, raw_ids in accessed_artifact_ids_by_stage.items():
        name = _stage_name(raw_name)
        if name in stages:
            raise ValueError("access stage names must be unique after canonicalization")
        ids = tuple(raw_ids)
        if not ids:
            raise ValueError(f"access stage {name!r} must contain at least one artifact ID")
        for value in ids:
            _validate_id(value, label=f"artifact IDs for stage {name!r}")
        stages[name] = ids
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

    rows: list[EvaluationAccessStage] = []
    leaking_stage_count = 0
    occurrence_count = 0
    maximum_stage_count = 0
    duplicate_count = 0
    for name, ids in stages.items():
        unique = set(ids)
        duplicates = len(ids) - len(unique)
        final_count = sum(value == final_evaluation_artifact_id for value in ids)
        status = (
            "final_evaluation_access_leakage"
            if final_count
            else "final_evaluation_not_accessed_in_declared_pre_final_stages"
        )
        if final_count:
            leaking_stage_count += 1
        occurrence_count += final_count
        maximum_stage_count = max(maximum_stage_count, final_count)
        duplicate_count += duplicates
        rows.append(EvaluationAccessStage(
            stage_name=name,
            access_count=len(ids),
            unique_access_count=len(unique),
            duplicate_access_count=duplicates,
            final_evaluation_access_count=final_count,
            status=status,
        ))

    leaked = occurrence_count > 0
    return EvaluationAccessProvenanceAudit(
        stage_count=len(rows),
        stage_names=tuple(row.stage_name for row in rows),
        leaking_stage_count=leaking_stage_count,
        final_evaluation_access_occurrence_count=occurrence_count,
        final_evaluation_accessed=leaked,
        maximum_stage_final_access_count=maximum_stage_count,
        duplicate_access_count=duplicate_count,
        separation_category=(
            "final_evaluation_access_leakage"
            if leaked
            else "final_evaluation_not_accessed_in_declared_pre_final_stages"
        ),
        expected_stage_coverage_checked=expected_checked,
        accessed_artifact_ids_emitted=False,
        automatic_access_history_inference=False,
        ledger_completeness_assumed=False,
        automatic_candidate_selection=False,
        aggregate_confidence_score_emitted=False,
        stages=tuple(rows),
    )
