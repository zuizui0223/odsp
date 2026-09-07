"""Selection/final-validation row-overlap provenance.

This layer checks caller-supplied row identities consulted during data-driven
selection stages (candidate comparison, hyperparameter tuning, early stopping,
threshold choice, and similar decisions) against one canonical final-validation
target.  It detects direct row overlap only; a clean result cannot prove that the
caller supplied the complete selection history or that no validation summaries
were used indirectly.
"""
from __future__ import annotations

from dataclasses import asdict, dataclass
from typing import Mapping, Sequence

import numpy as np


@dataclass(frozen=True)
class SelectionStageProvenance:
    stage_name: str
    selection_row_count: int
    unique_selection_row_count: int
    duplicate_selection_row_count: int
    overlapping_final_validation_row_count: int
    status: str

    def as_dict(self) -> dict[str, object]:
        return asdict(self)


@dataclass(frozen=True)
class SelectionValidationProvenanceAudit:
    final_validation_row_count: int
    selection_stage_count: int
    stage_names: tuple[str, ...]
    overlapping_stage_count: int
    unique_overlapping_final_validation_row_count: int
    maximum_stage_overlap_count: int
    duplicate_selection_row_count: int
    separation_category: str
    selection_validation_separated: bool
    expected_stage_coverage_checked: bool
    overlapping_row_ids_emitted: bool
    automatic_selection_history_inference: bool
    automatic_candidate_selection: bool
    aggregate_confidence_score_emitted: bool
    stages: tuple[SelectionStageProvenance, ...]

    def as_dict(self) -> dict[str, object]:
        return {
            "final_validation_row_count": self.final_validation_row_count,
            "selection_stage_count": self.selection_stage_count,
            "stage_names": list(self.stage_names),
            "overlapping_stage_count": self.overlapping_stage_count,
            "unique_overlapping_final_validation_row_count": self.unique_overlapping_final_validation_row_count,
            "maximum_stage_overlap_count": self.maximum_stage_overlap_count,
            "duplicate_selection_row_count": self.duplicate_selection_row_count,
            "separation_category": self.separation_category,
            "selection_validation_separated": self.selection_validation_separated,
            "expected_stage_coverage_checked": self.expected_stage_coverage_checked,
            "overlapping_row_ids_emitted": self.overlapping_row_ids_emitted,
            "automatic_selection_history_inference": self.automatic_selection_history_inference,
            "automatic_candidate_selection": self.automatic_candidate_selection,
            "aggregate_confidence_score_emitted": self.aggregate_confidence_score_emitted,
            "stages": [row.as_dict() for row in self.stages],
        }


def _validate_row_id(value: object, *, label: str) -> None:
    if value is None:
        raise ValueError(f"{label} must not contain missing row IDs")
    try:
        hash(value)
    except TypeError as exc:
        raise ValueError(f"{label} row IDs must be hashable scalar values") from exc
    if isinstance(value, (float, np.floating)) and bool(np.isnan(value)):
        raise ValueError(f"{label} must not contain missing row IDs")


def _row_ids(
    values: Sequence[object],
    *,
    label: str,
    require_nonempty: bool,
) -> tuple[object, ...]:
    rows = tuple(values)
    if require_nonempty and not rows:
        raise ValueError(f"{label} must contain at least one row ID")
    for value in rows:
        _validate_row_id(value, label=label)
    return rows


def _stage_name(value: object) -> str:
    name = str(value).strip()
    if not name:
        raise ValueError("selection stage names must be non-empty")
    return name


def _canonical_selection_stages(
    selection_row_ids_by_stage: Mapping[object, Sequence[object]],
) -> dict[str, tuple[object, ...]]:
    if not selection_row_ids_by_stage:
        raise ValueError("selection_row_ids_by_stage must contain at least one stage")
    result: dict[str, tuple[object, ...]] = {}
    for raw_stage, raw_rows in selection_row_ids_by_stage.items():
        stage = _stage_name(raw_stage)
        if stage in result:
            raise ValueError("selection stage names must be unique after canonicalization")
        result[stage] = _row_ids(
            raw_rows,
            label=f"selection rows for {stage}",
            require_nonempty=True,
        )
    return dict(sorted(result.items()))


def _canonical_expected_stages(values: Sequence[object]) -> tuple[str, ...]:
    names = tuple(_stage_name(value) for value in values)
    if not names:
        raise ValueError("expected_stage_names must contain at least one stage")
    if len(set(names)) != len(names):
        raise ValueError("expected stage names must be unique after canonicalization")
    return tuple(sorted(names))


def audit_selection_validation_provenance(
    final_validation_row_ids: Sequence[object],
    selection_row_ids_by_stage: Mapping[object, Sequence[object]],
    *,
    expected_stage_names: Sequence[object] | None = None,
) -> SelectionValidationProvenanceAudit:
    """Check declared selection-stage rows for direct final-validation overlap.

    Rows may repeat inside a selection stage, for example when repeated
    cross-validation revisits the same development row.  Duplicates are reported
    but do not multiply unique leaked final-validation rows.
    """

    final_validation = _row_ids(
        final_validation_row_ids,
        label="final_validation_row_ids",
        require_nonempty=True,
    )
    if len(set(final_validation)) != len(final_validation):
        raise ValueError("final_validation_row_ids must be unique")
    final_set = set(final_validation)

    stages = _canonical_selection_stages(selection_row_ids_by_stage)
    expected_checked = expected_stage_names is not None
    if expected_stage_names is not None:
        expected = _canonical_expected_stages(expected_stage_names)
        actual = tuple(stages)
        if actual != expected:
            missing = tuple(sorted(set(expected) - set(actual)))
            extra = tuple(sorted(set(actual) - set(expected)))
            if missing and not extra:
                raise ValueError("expected selection stage coverage includes a missing declared stage")
            if extra and not missing:
                raise ValueError("declared selection stages include an unexpected extra stage")
            raise ValueError("expected selection stage coverage must exactly match declared stages")

    results: list[SelectionStageProvenance] = []
    global_overlap: set[object] = set()
    overlapping_stage_count = 0
    maximum_overlap = 0
    total_duplicates = 0

    for stage, selection_rows in stages.items():
        unique_selection = set(selection_rows)
        duplicate_count = len(selection_rows) - len(unique_selection)
        overlap = unique_selection & final_set
        overlap_count = len(overlap)
        status = (
            "selection_validation_leakage"
            if overlap_count
            else "selection_validation_disjoint"
        )
        if overlap_count:
            overlapping_stage_count += 1
            global_overlap.update(overlap)
        maximum_overlap = max(maximum_overlap, overlap_count)
        total_duplicates += duplicate_count
        results.append(
            SelectionStageProvenance(
                stage_name=stage,
                selection_row_count=len(selection_rows),
                unique_selection_row_count=len(unique_selection),
                duplicate_selection_row_count=duplicate_count,
                overlapping_final_validation_row_count=overlap_count,
                status=status,
            )
        )

    category = (
        "selection_validation_leakage"
        if overlapping_stage_count
        else "selection_validation_disjoint"
    )
    return SelectionValidationProvenanceAudit(
        final_validation_row_count=len(final_validation),
        selection_stage_count=len(results),
        stage_names=tuple(row.stage_name for row in results),
        overlapping_stage_count=overlapping_stage_count,
        unique_overlapping_final_validation_row_count=len(global_overlap),
        maximum_stage_overlap_count=maximum_overlap,
        duplicate_selection_row_count=total_duplicates,
        separation_category=category,
        selection_validation_separated=bool(overlapping_stage_count == 0),
        expected_stage_coverage_checked=expected_checked,
        overlapping_row_ids_emitted=False,
        automatic_selection_history_inference=False,
        automatic_candidate_selection=False,
        aggregate_confidence_score_emitted=False,
        stages=tuple(results),
    )
