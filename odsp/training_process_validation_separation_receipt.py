"""Content-locked process-wide training/validation separation receipt."""
from __future__ import annotations

from datetime import datetime, timezone
import json
from pathlib import Path

from .information_transfer_contract import _read_rows, _text, _value
from .training_process_freeze_manifest import (
    _canonical_sha256,
    _file_sha256,
)
from .training_process_validation_provenance import (
    audit_training_process_validation_frame_separation,
)


SEPARATION_RECEIPT_TYPE = (
    "odsp_training_process_validation_separation_receipt_v1"
)


def _validation_ids(
    path: Path,
    *,
    file_format: str,
    row_id_column: str,
) -> tuple[tuple[str, ...], str]:
    fmt = str(file_format).strip().lower()
    if fmt not in {"csv", "json"}:
        raise ValueError("validation roster format must be 'csv' or 'json'")
    column = str(row_id_column).strip()
    if not column:
        raise ValueError("validation row ID column must be non-empty")
    if not path.is_file():
        raise FileNotFoundError(path)

    rows = _read_rows(path, fmt)
    if not rows:
        raise ValueError("validation roster is empty")
    values: list[str] = []
    for index, row in enumerate(rows):
        if set(row) != {column}:
            raise ValueError(
                "validation separation roster must contain exactly one "
                "metadata-only row-ID column"
            )
        values.append(
            _text(
                _value(row, column, row_index=index),
                name=f"validation row {index} ID",
            )
        )
    if len(values) != len(set(values)):
        raise ValueError("validation row IDs must be unique")
    ordered = tuple(sorted(values))
    semantic_sha = _canonical_sha256(
        [{"validation_row_id": value} for value in ordered]
    )
    return ordered, semantic_sha


def create_training_process_validation_separation_receipt(
    process_manifest_path: str | Path,
    training_roster_path: str | Path,
    validation_roster_path: str | Path,
    receipt_out: str | Path,
    *,
    row_identity_namespace: object,
    training_roster_format: str,
    training_unit_id_column: str,
    training_stratum_column: str | None = None,
    validation_format: str = "csv",
    validation_row_id_column: str = "row_id",
) -> dict[str, object]:
    """Run the canonical frame audit and freeze a metadata-only pass receipt."""

    manifest_path = Path(process_manifest_path)
    training_path = Path(training_roster_path)
    validation_path = Path(validation_roster_path)
    output_path = Path(receipt_out)
    if output_path.exists():
        raise FileExistsError(
            "training-process validation separation receipt already exists "
            f"and will not be overwritten: {output_path}"
        )

    validation_ids, validation_semantic_sha = _validation_ids(
        validation_path,
        file_format=validation_format,
        row_id_column=validation_row_id_column,
    )
    audit = audit_training_process_validation_frame_separation(
        manifest_path,
        training_path,
        validation_ids,
        row_identity_namespace=row_identity_namespace,
        roster_format=training_roster_format,
        unit_id_column=training_unit_id_column,
        stratum_column=training_stratum_column,
    )
    if not audit.training_source_frame_validation_disjoint:
        raise ValueError(
            "full frozen training-process source frame is not disjoint "
            "from declared validation support"
        )

    created_at = (
        datetime.now(timezone.utc)
        .replace(microsecond=0)
        .isoformat()
        .replace("+00:00", "Z")
    )
    receipt = {
        "schema_version": 1,
        "receipt_type": SEPARATION_RECEIPT_TYPE,
        "created_at_utc": created_at,
        "training_process_id": audit.training_process_id,
        "row_identity_namespace": audit.row_identity_namespace,
        "process_manifest_sha256": _file_sha256(manifest_path),
        "training_roster_file_sha256": _file_sha256(training_path),
        "validation_roster_file_sha256": _file_sha256(validation_path),
        "validation_row_id_semantic_sha256": validation_semantic_sha,
        "training_source_unit_count": audit.training_source_unit_count,
        "validation_row_count": audit.validation_row_count,
        "overlapping_unit_count": 0,
        "training_source_frame_validation_disjoint": True,
        "entire_training_source_frame_checked": True,
        "realized_refit_memberships_only": False,
        "canonical_audit": audit.as_dict(),
        "boundaries": {
            "validation_outcomes_read": False,
            "validation_roster_extra_columns_allowed": False,
            "row_ids_emitted": False,
            "automatic_identity_crosswalk_inference": False,
            "proves_model_generation_followed_manifest": False,
            "proves_validation_block_exchangeability": False,
            "fixed_set_results_reclassified": False,
        },
    }
    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_text(
        json.dumps(
            receipt,
            indent=2,
            sort_keys=True,
            allow_nan=False,
        )
        + "\n",
        encoding="utf-8",
    )
    return {
        "receipt_path": str(output_path),
        "receipt_sha256": _file_sha256(output_path),
        "receipt": receipt,
    }
