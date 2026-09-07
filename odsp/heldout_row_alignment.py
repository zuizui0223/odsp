"""Alignment checks for row-keyed held-out ODSP evidence."""
from __future__ import annotations

from dataclasses import asdict, dataclass
from typing import Mapping, Sequence

import numpy as np


@dataclass(frozen=True)
class HeldoutSourceAlignment:
    source_name: str
    source_row_count: int
    status: str
    exact_order: bool
    same_row_set: bool
    duplicate_row_id_count: int
    missing_row_count: int
    extra_row_count: int
    permutation_to_base: tuple[int, ...] | None

    def as_dict(self) -> dict[str, object]:
        payload = asdict(self)
        payload["permutation_to_base"] = None if self.permutation_to_base is None else list(self.permutation_to_base)
        return payload


@dataclass(frozen=True)
class HeldoutRowAlignmentAudit:
    base_row_count: int
    source_count: int
    source_names: tuple[str, ...]
    alignment_category: str
    alignment_passed: bool
    exact_source_count: int
    reorderable_source_count: int
    mismatched_source_count: int
    automatic_row_imputation: bool
    row_contents_used_for_identity: bool
    aggregate_confidence_score_emitted: bool
    sources: tuple[HeldoutSourceAlignment, ...]

    def as_dict(self) -> dict[str, object]:
        return {
            "base_row_count": self.base_row_count,
            "source_count": self.source_count,
            "source_names": list(self.source_names),
            "alignment_category": self.alignment_category,
            "alignment_passed": self.alignment_passed,
            "exact_source_count": self.exact_source_count,
            "reorderable_source_count": self.reorderable_source_count,
            "mismatched_source_count": self.mismatched_source_count,
            "automatic_row_imputation": self.automatic_row_imputation,
            "row_contents_used_for_identity": self.row_contents_used_for_identity,
            "aggregate_confidence_score_emitted": self.aggregate_confidence_score_emitted,
            "sources": [row.as_dict() for row in self.sources],
        }


def _ids(values: Sequence[object], *, label: str, nonempty: bool) -> tuple[object, ...]:
    rows = tuple(values)
    if nonempty and not rows:
        raise ValueError(f"{label} must contain at least one key")
    for value in rows:
        if value is None:
            raise ValueError(f"{label} must not contain missing keys")
        try:
            hash(value)
        except TypeError as exc:
            raise ValueError(f"{label} keys must be hashable scalars") from exc
        if isinstance(value, (float, np.floating)) and bool(np.isnan(value)):
            raise ValueError(f"{label} must not contain missing keys")
    return rows


def audit_heldout_row_alignment(
    base_row_ids: Sequence[object],
    row_ids_by_source: Mapping[str, Sequence[object]],
) -> HeldoutRowAlignmentAudit:
    """Compare named source row keys with one canonical base ordering."""
    base = _ids(base_row_ids, label="base_row_ids", nonempty=True)
    if len(set(base)) != len(base):
        raise ValueError("base_row_ids must be unique")
    if not row_ids_by_source:
        raise ValueError("row_ids_by_source must contain at least one source")

    named = [(str(raw).strip(), values) for raw, values in row_ids_by_source.items()]
    if any(not name for name, _ in named):
        raise ValueError("source names must be non-empty")
    if len({name for name, _ in named}) != len(named):
        raise ValueError("source names must be unique after canonicalization")

    base_set = set(base)
    results: list[HeldoutSourceAlignment] = []
    for name, values in sorted(named, key=lambda row: row[0]):
        source = _ids(values, label=f"source {name!r}", nonempty=False)
        source_set = set(source)
        duplicate_count = len(source) - len(source_set)
        missing_count = len(base_set - source_set)
        extra_count = len(source_set - base_set)
        same_set = duplicate_count == 0 and len(source) == len(base) and missing_count == 0 and extra_count == 0
        exact = same_set and source == base
        if same_set:
            lookup = {key: idx for idx, key in enumerate(source)}
            permutation = tuple(lookup[key] for key in base)
            status = "exact_alignment" if exact else "reorderable_alignment"
        else:
            permutation = None
            status = "row_mismatch"
        results.append(HeldoutSourceAlignment(
            source_name=name,
            source_row_count=len(source),
            status=status,
            exact_order=bool(exact),
            same_row_set=bool(same_set),
            duplicate_row_id_count=duplicate_count,
            missing_row_count=missing_count,
            extra_row_count=extra_count,
            permutation_to_base=permutation,
        ))

    exact_count = sum(row.status == "exact_alignment" for row in results)
    reorderable_count = sum(row.status == "reorderable_alignment" for row in results)
    mismatch_count = sum(row.status == "row_mismatch" for row in results)
    category = "row_mismatch" if mismatch_count else ("reorderable_alignment" if reorderable_count else "exact_alignment")
    return HeldoutRowAlignmentAudit(
        base_row_count=len(base),
        source_count=len(results),
        source_names=tuple(row.source_name for row in results),
        alignment_category=category,
        alignment_passed=mismatch_count == 0,
        exact_source_count=exact_count,
        reorderable_source_count=reorderable_count,
        mismatched_source_count=mismatch_count,
        automatic_row_imputation=False,
        row_contents_used_for_identity=False,
        aggregate_confidence_score_emitted=False,
        sources=tuple(results),
    )


def reorder_validation_rows(
    values: Sequence[object],
    permutation_to_base: Sequence[int],
    *,
    axis: int = -1,
) -> np.ndarray:
    """Apply a verified source-to-base row permutation along one array axis."""
    array = np.asarray(values)
    if array.ndim == 0:
        raise ValueError("values must have at least one dimension")
    selected_axis = int(axis)
    if selected_axis < 0:
        selected_axis += array.ndim
    if selected_axis < 0 or selected_axis >= array.ndim:
        raise ValueError("axis is out of bounds")
    permutation = tuple(int(idx) for idx in permutation_to_base)
    if len(permutation) != array.shape[selected_axis]:
        raise ValueError("permutation length must match the selected row axis")
    if tuple(sorted(permutation)) != tuple(range(len(permutation))):
        raise ValueError("permutation must contain each row index exactly once")
    return np.take(array, permutation, axis=selected_axis)
