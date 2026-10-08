"""Whole-source-frame validation separation for training-source process v0."""
from __future__ import annotations

from dataclasses import asdict, dataclass
import json
from pathlib import Path
from typing import Mapping, Sequence

import numpy as np

from .information_transfer_contract import _read_rows
from .training_process_freeze_manifest import _canonical_sha256, _file_sha256
from .training_source_process_freeze_manifest import SOURCE_PROCESS_MANIFEST_TYPE


@dataclass(frozen=True)
class TrainingSourceProcessValidationFrameAudit:
    schema_version: int
    source_process_id: str
    row_identity_namespace: str
    source_frame_unit_count: int
    validation_row_count: int
    overlapping_unit_count: int
    separation_category: str
    source_frame_validation_disjoint: bool
    source_roster_file_hash_verified: bool
    source_roster_semantic_hash_verified: bool
    entire_original_source_frame_checked: bool
    realized_outer_draws_only: bool
    nested_inner_refits_only: bool
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


def audit_training_source_process_validation_frame_separation(
    manifest_path: str | Path,
    source_roster_path: str | Path,
    validation_row_ids: Sequence[object],
    *,
    row_identity_namespace: object,
    roster_format: str,
    unit_id_column: str,
    stratum_column: str | None = None,
) -> TrainingSourceProcessValidationFrameAudit:
    """Verify original source-frame identity and held-out validation disjointness."""

    namespace = _text(row_identity_namespace, name="row_identity_namespace")
    manifest_path = Path(manifest_path)
    roster_path = Path(source_roster_path)
    try:
        raw = json.loads(manifest_path.read_text(encoding="utf-8"))
    except json.JSONDecodeError as exc:
        raise ValueError("training source process manifest is not valid JSON") from exc
    if not isinstance(raw, Mapping):
        raise ValueError("training source process manifest must be a JSON object")
    manifest = dict(raw)
    if manifest.get("manifest_type") != SOURCE_PROCESS_MANIFEST_TYPE:
        raise ValueError("training source process manifest_type is not recognized")
    source_process_id = _text(
        manifest.get("source_process_id"), name="manifest.source_process_id"
    )
    frozen = manifest.get("source_roster")
    if not isinstance(frozen, Mapping):
        raise ValueError("manifest.source_roster must be an object")
    if not roster_path.is_file():
        raise FileNotFoundError(roster_path)
    if _file_sha256(roster_path) != str(frozen.get("file_sha256")):
        raise ValueError("source roster file bytes do not match frozen manifest")

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
        raise ValueError("source roster is empty")
    expected = {unit_column}
    if stratum is not None:
        expected.add(stratum)

    canonical: list[dict[str, str]] = []
    source_ids: list[str] = []
    seen: set[str] = set()
    for index, row in enumerate(rows):
        if set(row) != expected:
            raise ValueError(
                "source roster must contain only unit and optional stratum columns"
            )
        unit = _text(row.get(unit_column), name=f"source roster row {index} unit ID")
        if unit in seen:
            raise ValueError("source roster unit IDs must be unique")
        seen.add(unit)
        group = (
            "__all__"
            if stratum is None
            else _text(row.get(stratum), name=f"source roster row {index} stratum")
        )
        source_ids.append(unit)
        canonical.append({"unit_id": unit, "stratum": group})
    canonical.sort(key=lambda row: (row["stratum"], row["unit_id"]))
    if _canonical_sha256(canonical) != str(frozen.get("semantic_sha256")):
        raise ValueError("source roster semantics do not match frozen manifest")

    validation = _row_ids(validation_row_ids, name="validation_row_ids")
    overlap_count = len(set(source_ids) & set(validation))
    disjoint = overlap_count == 0
    return TrainingSourceProcessValidationFrameAudit(
        schema_version=1,
        source_process_id=source_process_id,
        row_identity_namespace=namespace,
        source_frame_unit_count=len(source_ids),
        validation_row_count=len(validation),
        overlapping_unit_count=overlap_count,
        separation_category=(
            "source_frame_validation_disjoint"
            if disjoint
            else "source_frame_validation_leakage"
        ),
        source_frame_validation_disjoint=disjoint,
        source_roster_file_hash_verified=True,
        source_roster_semantic_hash_verified=True,
        entire_original_source_frame_checked=True,
        realized_outer_draws_only=False,
        nested_inner_refits_only=False,
        validation_outcomes_required=False,
        overlapping_row_ids_emitted=False,
        automatic_identity_crosswalk_inference=False,
    )
