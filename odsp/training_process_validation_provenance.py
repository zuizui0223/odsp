"""Sampling-frame training/validation provenance for process inference.

A stochastic training-process claim is about future draws from a frozen source
frame. Therefore separation must be checked against the complete source roster,
not only the finite realized refits. This module verifies the frozen roster
content and compares its unit IDs with caller-supplied validation IDs inside one
explicit shared identity namespace. It never emits overlapping IDs.
"""
from __future__ import annotations

from dataclasses import asdict, dataclass
import json
from pathlib import Path
from typing import Mapping, Sequence

import numpy as np

from .information_transfer_contract import _read_rows
from .training_process_freeze_manifest import (
    PROCESS_MANIFEST_TYPE,
    _canonical_sha256,
    _file_sha256,
)


@dataclass(frozen=True)
class TrainingProcessValidationFrameAudit:
    schema_version: int
    training_process_id: str
    row_identity_namespace: str
    training_source_unit_count: int
    validation_row_count: int
    overlapping_unit_count: int
    separation_category: str
    training_source_frame_validation_disjoint: bool
    manifest_roster_file_hash_verified: bool
    manifest_roster_semantic_hash_verified: bool
    entire_training_source_frame_checked: bool
    realized_refit_memberships_only: bool
    validation_outcomes_required: bool
    overlapping_row_ids_emitted: bool
    automatic_identity_crosswalk_inference: bool

    def as_dict(self) -> dict[str, object]:
        return asdict(self)


def _text(value: object, *, name: str) -> str:
    if not isinstance(value, str) or not value.strip():
        raise ValueError(f"{name} must be non-empty text")
    return value.strip()


def _row_ids(values: Sequence[object], *, name: str) -> tuple[object, ...]:
    rows = tuple(values)
    if not rows:
        raise ValueError(f"{name} must not be empty")
    for value in rows:
        if value is None:
            raise ValueError(f"{name} must not contain missing IDs")
        try:
            hash(value)
        except TypeError as exc:
            raise ValueError(f"{name} IDs must be hashable scalars") from exc
        if isinstance(value, (float, np.floating)) and np.isnan(value):
            raise ValueError(f"{name} must not contain missing IDs")
    if len(rows) != len(set(rows)):
        raise ValueError(f"{name} IDs must be unique")
    return rows


def audit_training_process_validation_frame_separation(
    manifest_path: str | Path,
    training_roster_path: str | Path,
    validation_row_ids: Sequence[object],
    *,
    row_identity_namespace: object,
    roster_format: str,
    unit_id_column: str,
    stratum_column: str | None = None,
) -> TrainingProcessValidationFrameAudit:
    """Verify frozen source-frame identity and require validation disjointness."""

    namespace = _text(
        row_identity_namespace, name="row_identity_namespace"
    )
    manifest_path = Path(manifest_path)
    roster_path = Path(training_roster_path)
    try:
        manifest_raw = json.loads(manifest_path.read_text(encoding="utf-8"))
    except json.JSONDecodeError as exc:
        raise ValueError("training process manifest is not valid JSON") from exc
    if not isinstance(manifest_raw, Mapping):
        raise ValueError("training process manifest must be a JSON object")
    manifest = dict(manifest_raw)
    if manifest.get("manifest_type") != PROCESS_MANIFEST_TYPE:
        raise ValueError("training process manifest_type is not recognized")
    process_id = _text(
        manifest.get("training_process_id"),
        name="manifest.training_process_id",
    )
    roster_snapshot = manifest.get("training_roster")
    if not isinstance(roster_snapshot, Mapping):
        raise ValueError("manifest.training_roster must be an object")
    frozen_file_sha = _text(
        roster_snapshot.get("file_sha256"),
        name="manifest.training_roster.file_sha256",
    )
    frozen_semantic_sha = _text(
        roster_snapshot.get("semantic_sha256"),
        name="manifest.training_roster.semantic_sha256",
    )
    if not roster_path.is_file():
        raise FileNotFoundError(roster_path)
    if _file_sha256(roster_path) != frozen_file_sha:
        raise ValueError("training roster file bytes do not match frozen manifest")

    fmt = _text(roster_format, name="roster_format").lower()
    if fmt not in {"csv", "json"}:
        raise ValueError("roster_format must be 'csv' or 'json'")
    unit_column = _text(unit_id_column, name="unit_id_column")
    stratum = None if stratum_column is None else _text(
        stratum_column, name="stratum_column"
    )
    if stratum == unit_column:
        raise ValueError("unit_id_column and stratum_column must differ")

    rows = _read_rows(roster_path, fmt)
    if not rows:
        raise ValueError("training roster is empty")
    expected = {unit_column}
    if stratum is not None:
        expected.add(stratum)

    canonical: list[dict[str, str]] = []
    training_ids: list[str] = []
    seen: set[str] = set()
    for index, row in enumerate(rows):
        if set(row) != expected:
            raise ValueError(
                "training roster must contain only unit and optional stratum columns"
            )
        raw_unit = row.get(unit_column)
        unit = _text(raw_unit, name=f"training roster row {index} unit ID")
        if unit in seen:
            raise ValueError("training roster unit IDs must be unique")
        seen.add(unit)
        training_ids.append(unit)
        group = (
            "__all__"
            if stratum is None
            else _text(
                row.get(stratum),
                name=f"training roster row {index} stratum",
            )
        )
        canonical.append({"unit_id": unit, "stratum": group})

    canonical.sort(key=lambda row: (row["stratum"], row["unit_id"]))
    if _canonical_sha256(canonical) != frozen_semantic_sha:
        raise ValueError(
            "training roster semantics do not match frozen manifest"
        )

    validation = _row_ids(
        validation_row_ids, name="validation_row_ids"
    )
    overlap_count = len(set(training_ids) & set(validation))
    disjoint = overlap_count == 0
    return TrainingProcessValidationFrameAudit(
        schema_version=1,
        training_process_id=process_id,
        row_identity_namespace=namespace,
        training_source_unit_count=len(training_ids),
        validation_row_count=len(validation),
        overlapping_unit_count=overlap_count,
        separation_category=(
            "training_source_frame_validation_disjoint"
            if disjoint
            else "training_source_frame_validation_leakage"
        ),
        training_source_frame_validation_disjoint=disjoint,
        manifest_roster_file_hash_verified=True,
        manifest_roster_semantic_hash_verified=True,
        entire_training_source_frame_checked=True,
        realized_refit_memberships_only=False,
        validation_outcomes_required=False,
        overlapping_row_ids_emitted=False,
        automatic_identity_crosswalk_inference=False,
    )
