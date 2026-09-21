"""Generate a pre-outcome freeze manifest for paired shared-block validation."""
from __future__ import annotations

from datetime import datetime, timezone
import json
from pathlib import Path
from typing import Mapping

from .external_freeze_manifest import (
    _file_sha256,
    load_external_freeze_plan,
)
from .frozen_confirmatory_route import build_frozen_confirmatory_route
from .information_transfer_contract import _read_rows, _text, _value
from .untouched_external_refit_positive_contract_v2 import _row_roster_sha256
from .untouched_external_refit_shared_block_positive_contract_v3 import (
    _VALIDATION_DESIGN,
)


def create_paired_external_freeze_manifest(
    plan_path: str | Path,
    manifest_out: str | Path,
) -> dict[str, object]:
    """Freeze the exact paired external analysis before outcomes are accessed."""

    plan_path = Path(plan_path)
    plan = load_external_freeze_plan(plan_path)
    roster_spec = plan["roster"]
    assert isinstance(roster_spec, Mapping)
    roster_path = Path(str(roster_spec["path"]))
    if not roster_path.is_absolute():
        roster_path = plan_path.parent / roster_path
    if not roster_path.is_file():
        raise FileNotFoundError(roster_path)
    rows = _read_rows(roster_path, str(roster_spec["format"]))
    if not rows:
        raise ValueError("external row roster is empty")
    row_id_column = str(roster_spec["row_id_column"])
    row_ids: list[str] = []
    for index, row in enumerate(rows):
        keys = set(row)
        if keys != {row_id_column}:
            extra = sorted(keys - {row_id_column})
            missing = [] if row_id_column in keys else [row_id_column]
            raise ValueError(
                "pre-outcome roster must contain only the row_id column; "
                f"row={index}, missing={missing!r}, extra={extra!r}"
            )
        row_ids.append(
            _text(
                _value(row, row_id_column, row_index=index),
                name=f"row {index} row_id",
            )
        )
    if len(set(row_ids)) != len(row_ids):
        raise ValueError("pre-outcome roster row IDs must be unique")

    confirmatory_route = build_frozen_confirmatory_route(
        validation_design="paired_shared_blocks",
        information_structure="filtration",
        contrast_count=len(plan["levels"]) - 1,
    )
    frozen_at_utc = (
        datetime.now(timezone.utc)
        .replace(microsecond=0)
        .isoformat()
        .replace("+00:00", "Z")
    )
    manifest = {
        "schema_version": 2,
        "manifest_type": "odsp_pre_external_outcome_paired_freeze_v1",
        "frozen_at_utc": frozen_at_utc,
        "upstream_model_set_id": plan["upstream_model_set_id"],
        "external_dataset_id": plan["external_dataset_id"],
        "external_row_ids_sha256": _row_roster_sha256(row_ids),
        "validation_design": dict(_VALIDATION_DESIGN),
        "confirmatory_route": confirmatory_route,
        "refit_ids": plan["refit_ids"],
        "reference_refit_id": plan["reference_refit_id"],
        "score": plan["score"],
        "levels": plan["levels"],
        "certification": plan["certification"],
    }

    output_path = Path(manifest_out)
    if output_path.exists():
        raise FileExistsError(
            f"freeze manifest already exists and will not be overwritten: {output_path}"
        )
    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_text(
        json.dumps(manifest, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )

    return {
        "receipt_type": "odsp_pre_external_outcome_paired_freeze_receipt_v1",
        "manifest_path": str(output_path),
        "manifest_sha256": _file_sha256(output_path),
        "frozen_at_utc": frozen_at_utc,
        "freeze_plan_sha256": _file_sha256(plan_path),
        "roster_file_sha256": _file_sha256(roster_path),
        "external_row_ids_sha256": manifest["external_row_ids_sha256"],
        "external_row_count": len(row_ids),
        "upstream_model_set_id": plan["upstream_model_set_id"],
        "external_dataset_id": plan["external_dataset_id"],
        "validation_design": dict(_VALIDATION_DESIGN),
        "confirmatory_route": confirmatory_route,
        "refit_count": len(plan["refit_ids"]),
        "reference_refit_id": plan["reference_refit_id"],
        "boundaries": {
            "manifest_timestamp_generated_by_odsp_runtime_clock": True,
            "caller_supplied_freeze_timestamp_allowed": False,
            "manifest_overwrite_allowed": False,
            "roster_outcome_columns_allowed": False,
            "external_outcomes_read_by_freeze_generator": False,
            "paired_shared_block_design_frozen": True,
            "validation_group_independence_assumed": False,
            "exact_positive_mass_shared_block_support_required": True,
            "missing_shared_blocks_imputed": False,
            "runtime_clock_independently_attested": False,
            "trusted_timestamp_authority_used": False,
        },
    }
