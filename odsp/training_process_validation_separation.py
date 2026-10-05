"""Process-wide training/validation support separation receipt.

The receipt proves a stronger property than checking only realized refits:
the complete frozen training-unit roster is disjoint from a metadata-only
validation-row roster.  Because the admitted v1 training process resamples only
from that frozen roster, every possible process draw is then training/validation
disjoint at the declared row-ID level.

No validation outcomes are read and no row IDs are emitted.
"""
from __future__ import annotations

from datetime import datetime, timezone
import json
from pathlib import Path
from typing import Mapping

from .information_transfer_contract import _read_rows, _text, _value
from .training_process_freeze_manifest import (
    PROCESS_MANIFEST_TYPE,
    _canonical_sha256,
    _file_sha256,
    load_training_process_freeze_plan,
)


SEPARATION_RECEIPT_TYPE = (
    "odsp_training_process_validation_separation_receipt_v1"
)


def _load_json_object(path: Path, *, name: str) -> dict[str, object]:
    try:
        raw = json.loads(path.read_text(encoding="utf-8"))
    except json.JSONDecodeError as exc:
        raise ValueError(f"{name} is not valid JSON: {path}") from exc
    if not isinstance(raw, Mapping):
        raise ValueError(f"{name} must contain a JSON object")
    return dict(raw)


def _canonical_training_roster(
    freeze_plan_path: Path,
    plan: Mapping[str, object],
) -> tuple[
    tuple[dict[str, str], ...],
    dict[str, tuple[str, ...]],
    Path,
]:
    roster_spec = plan["training_roster"]
    if not isinstance(roster_spec, Mapping):
        raise ValueError("training process plan training_roster is invalid")

    roster_path = Path(str(roster_spec["path"]))
    if not roster_path.is_absolute():
        roster_path = freeze_plan_path.parent / roster_path
    if not roster_path.is_file():
        raise FileNotFoundError(roster_path)

    rows = _read_rows(roster_path, str(roster_spec["format"]))
    if not rows:
        raise ValueError("training roster is empty")

    unit_column = str(roster_spec["unit_id_column"])
    raw_stratum_column = roster_spec["stratum_column"]
    stratum_column = (
        None
        if raw_stratum_column is None
        else str(raw_stratum_column)
    )
    expected = {unit_column}
    if stratum_column is not None:
        expected.add(stratum_column)

    canonical: list[dict[str, str]] = []
    strata: dict[str, list[str]] = {}
    seen: set[str] = set()
    for index, row in enumerate(rows):
        if set(row) != expected:
            raise ValueError(
                "training roster content no longer matches the frozen "
                "unit/stratum-only schema"
            )
        unit = _text(
            _value(row, unit_column, row_index=index),
            name=f"training row {index} unit_id",
        )
        if unit in seen:
            raise ValueError("training roster unit IDs must be unique")
        seen.add(unit)
        stratum = (
            "__all__"
            if stratum_column is None
            else _text(
                _value(row, stratum_column, row_index=index),
                name=f"training row {index} stratum",
            )
        )
        canonical.append({"unit_id": unit, "stratum": stratum})
        strata.setdefault(stratum, []).append(unit)

    canonical.sort(key=lambda row: (row["stratum"], row["unit_id"]))
    normalized_strata = {
        key: tuple(sorted(values))
        for key, values in sorted(strata.items())
    }
    return tuple(canonical), normalized_strata, roster_path


def _validation_support(
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
        value = _text(
            _value(row, column, row_index=index),
            name=f"validation row {index} ID",
        )
        values.append(value)
    if len(values) != len(set(values)):
        raise ValueError("validation row IDs must be unique")
    ordered = tuple(sorted(values))
    semantic_sha = _canonical_sha256(
        [{"validation_row_id": value} for value in ordered]
    )
    return ordered, semantic_sha


def create_training_process_validation_separation_receipt(
    process_manifest_path: str | Path,
    freeze_plan_path: str | Path,
    validation_roster_path: str | Path,
    receipt_out: str | Path,
    *,
    validation_format: str = "csv",
    validation_row_id_column: str = "row_id",
) -> dict[str, object]:
    """Create a non-overwriting process-wide separation receipt.

    This function reads training-unit metadata and validation row IDs only.  It
    rejects any validation roster with additional columns so outcome values
    cannot be smuggled into this pre-outcome governance step.
    """

    manifest_path = Path(process_manifest_path)
    plan_path = Path(freeze_plan_path)
    validation_path = Path(validation_roster_path)
    receipt_path = Path(receipt_out)
    if receipt_path.exists():
        raise FileExistsError(
            "training-process validation separation receipt already exists "
            f"and will not be overwritten: {receipt_path}"
        )

    manifest = _load_json_object(
        manifest_path,
        name="training process manifest",
    )
    if manifest.get("manifest_type") != PROCESS_MANIFEST_TYPE:
        raise ValueError("unrecognized training process manifest_type")

    plan = load_training_process_freeze_plan(plan_path)
    manifest_process = _text(
        manifest.get("training_process_id"),
        name="manifest.training_process_id",
    )
    plan_process = str(plan["training_process_id"])
    if plan_process != manifest_process:
        raise ValueError(
            "training process freeze plan does not identify the frozen manifest"
        )

    canonical_training, strata, training_path = _canonical_training_roster(
        plan_path,
        plan,
    )
    frozen_roster = manifest.get("training_roster")
    if not isinstance(frozen_roster, Mapping):
        raise ValueError("manifest.training_roster is invalid")

    training_file_sha = _file_sha256(training_path)
    training_semantic_sha = _canonical_sha256(
        list(canonical_training)
    )
    if training_file_sha != frozen_roster.get("file_sha256"):
        raise ValueError(
            "runtime training roster bytes do not match frozen manifest"
        )
    if training_semantic_sha != frozen_roster.get("semantic_sha256"):
        raise ValueError(
            "runtime training roster semantics do not match frozen manifest"
        )
    if len(canonical_training) != frozen_roster.get("row_count"):
        raise ValueError(
            "runtime training roster row count does not match frozen manifest"
        )
    stratum_sizes = {
        key: len(values) for key, values in strata.items()
    }
    if stratum_sizes != frozen_roster.get("stratum_sizes"):
        raise ValueError(
            "runtime training roster stratum sizes do not match frozen manifest"
        )

    validation_ids, validation_semantic_sha = _validation_support(
        validation_path,
        file_format=validation_format,
        row_id_column=validation_row_id_column,
    )
    training_ids = tuple(
        row["unit_id"] for row in canonical_training
    )
    overlap_count = len(set(training_ids) & set(validation_ids))
    if overlap_count:
        raise ValueError(
            "frozen training-process support overlaps declared validation "
            f"support in {overlap_count} row ID(s)"
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
        "training_process_id": manifest_process,
        "process_manifest_sha256": _file_sha256(manifest_path),
        "training_roster_file_sha256": training_file_sha,
        "training_roster_semantic_sha256": training_semantic_sha,
        "training_unit_count": len(training_ids),
        "training_stratum_count": len(strata),
        "validation_roster_file_sha256": _file_sha256(validation_path),
        "validation_row_id_semantic_sha256": validation_semantic_sha,
        "validation_row_count": len(validation_ids),
        "overlap_count": 0,
        "process_support_disjoint": True,
        "consequence": {
            "every_possible_refit_draw_from_frozen_roster_is_validation_disjoint": True,
            "realized_refit_enumeration_required": False,
        },
        "boundaries": {
            "validation_outcomes_read": False,
            "validation_roster_extra_columns_allowed": False,
            "row_ids_emitted": False,
            "proves_model_generation_followed_manifest": False,
            "proves_validation_block_exchangeability": False,
            "fixed_set_results_reclassified": False,
        },
    }
    receipt_path.parent.mkdir(parents=True, exist_ok=True)
    receipt_path.write_text(
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
        "receipt_path": str(receipt_path),
        "receipt_sha256": _file_sha256(receipt_path),
        "receipt": receipt,
    }
