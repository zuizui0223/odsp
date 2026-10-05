"""Create a pre-outcome internal confirmatory freeze for process inference."""
from __future__ import annotations

from datetime import datetime, timezone
import json
import math
from pathlib import Path
from typing import Mapping

import numpy as np

from .confirmatory_environment_lock import (
    ENVIRONMENT_LOCK_ID,
    runtime_environment_snapshot_for_surface,
)
from .confirmatory_implementation_lock import (
    IMPLEMENTATION_LOCK_ID,
    implementation_source_snapshot_for_surface,
)
from .information_transfer import (
    InformationLevelScore,
    validate_information_filtration,
)
from .information_transfer_contract import (
    _mapping,
    _read_rows,
    _reject_unknown,
    _text,
    _validate_score_contract,
    _value,
)
from .training_process_freeze_manifest import (
    PROCESS_MANIFEST_TYPE,
    _file_sha256,
)
from .training_process_internal_confirmatory_contract import (
    CANONICAL_SURFACE,
    INTERNAL_FREEZE_MANIFEST_TYPE,
    STATISTICAL_CORE,
    _load_json,
    _require_generation_receipt,
    _require_separation_receipt,
    _require_v5_qualification_receipt,
    validation_metadata_sha256,
    validation_row_id_semantic_sha256,
)
from .upstream_model_artifact_lock import (
    MODEL_ARTIFACT_LOCK_ID,
    normalize_upstream_model_artifact_declarations,
    verify_upstream_model_artifact_snapshot,
)


_PLAN_FIELDS = {
    "schema_version",
    "analysis_id",
    "process_manifest",
    "generation_receipt",
    "validation_separation_receipt",
    "qualification_receipt",
    "upstream_model_artifacts",
    "validation_dataset_id",
    "validation_roster",
    "score",
    "levels",
    "certification",
}
_ROSTER_FIELDS = {
    "path",
    "format",
    "row_id_column",
    "group_column",
    "block_column",
    "weight_column",
}
_LEVEL_FIELDS = {"name", "information"}
_CERT_FIELDS = {
    "component_one_sided_alpha",
    "minimum_refits",
    "minimum_blocks_per_group",
    "gain_tolerance",
}


def _path(value: object, *, name: str) -> str:
    return _text(value, name=name)


def _integer(value: object, *, name: str) -> int:
    if isinstance(value, bool) or not isinstance(value, int):
        raise ValueError(f"{name} must be an integer")
    return int(value)


def _finite_number(value: object, *, name: str) -> float:
    if isinstance(value, bool):
        raise ValueError(f"{name} must be numeric")
    try:
        result = float(value)
    except (TypeError, ValueError) as exc:
        raise ValueError(f"{name} must be numeric") from exc
    if not math.isfinite(result):
        raise ValueError(f"{name} must be finite")
    return result


def _resolve(base: Path, declared: str) -> Path:
    path = Path(declared)
    return path if path.is_absolute() else base / path


def validate_training_process_internal_freeze_plan(
    raw: Mapping[str, object],
) -> dict[str, object]:
    plan = _mapping(raw, name="training-process internal freeze plan")
    _reject_unknown(
        plan,
        _PLAN_FIELDS,
        name="training-process internal freeze plan",
    )
    version = plan.get("schema_version")
    if isinstance(version, bool) or version != 1:
        raise ValueError("internal freeze plan schema_version must be 1")

    analysis_id = _text(plan.get("analysis_id"), name="analysis_id")
    dataset_id = _text(
        plan.get("validation_dataset_id"),
        name="validation_dataset_id",
    )

    roster = _mapping(
        plan.get("validation_roster"),
        name="validation_roster",
    )
    _reject_unknown(
        roster,
        _ROSTER_FIELDS,
        name="validation_roster",
    )
    fmt = _text(
        roster.get("format"),
        name="validation_roster.format",
    ).lower()
    if fmt not in {"csv", "json"}:
        raise ValueError(
            "validation_roster.format must be 'csv' or 'json'"
        )
    normalized_roster = {
        "path": _path(
            roster.get("path"),
            name="validation_roster.path",
        ),
        "format": fmt,
        "row_id_column": _text(
            roster.get("row_id_column"),
            name="validation_roster.row_id_column",
        ),
        "group_column": _text(
            roster.get("group_column"),
            name="validation_roster.group_column",
        ),
        "block_column": _text(
            roster.get("block_column"),
            name="validation_roster.block_column",
        ),
        "weight_column": _text(
            roster.get("weight_column"),
            name="validation_roster.weight_column",
        ),
    }
    columns = {
        normalized_roster["row_id_column"],
        normalized_roster["group_column"],
        normalized_roster["block_column"],
        normalized_roster["weight_column"],
    }
    if len(columns) != 4:
        raise ValueError(
            "validation roster row/group/block/weight columns must be distinct"
        )

    raw_levels = plan.get("levels")
    if not isinstance(raw_levels, list) or len(raw_levels) != 3:
        raise ValueError(
            "v1 internal process envelope requires exactly three levels "
            "= two ordered contrasts"
        )
    levels: list[dict[str, object]] = []
    dummy: list[InformationLevelScore] = []
    for index, raw_level in enumerate(raw_levels):
        level = _mapping(
            raw_level,
            name=f"levels[{index}]",
        )
        _reject_unknown(
            level,
            _LEVEL_FIELDS,
            name=f"levels[{index}]",
        )
        name = _text(
            level.get("name"),
            name=f"levels[{index}].name",
        )
        information_raw = level.get("information")
        if not isinstance(information_raw, list):
            raise ValueError(
                f"levels[{index}].information must be a JSON array"
            )
        information = [
            _text(
                value,
                name=f"levels[{index}].information[{j}]",
            )
            for j, value in enumerate(information_raw)
        ]
        if len(information) != len(set(information)):
            raise ValueError(
                f"levels[{index}].information must be unique"
            )
        levels.append(
            {"name": name, "information": information}
        )
        dummy.append(
            InformationLevelScore(
                name,
                tuple(information),
                [0.0],
            )
        )
    validate_information_filtration(dummy)

    cert = _mapping(
        plan.get("certification"),
        name="certification",
    )
    _reject_unknown(
        cert,
        _CERT_FIELDS,
        name="certification",
    )
    alpha = _finite_number(
        cert.get("component_one_sided_alpha"),
        name="certification.component_one_sided_alpha",
    )
    minimum_refits = _integer(
        cert.get("minimum_refits"),
        name="certification.minimum_refits",
    )
    minimum_blocks = _integer(
        cert.get("minimum_blocks_per_group"),
        name="certification.minimum_blocks_per_group",
    )
    tolerance = _finite_number(
        cert.get("gain_tolerance"),
        name="certification.gain_tolerance",
    )
    if alpha != 0.05:
        raise ValueError(
            "v1 internal process envelope freezes component alpha at 0.05"
        )
    if minimum_refits != 8:
        raise ValueError(
            "v1 internal process envelope freezes minimum_refits at 8"
        )
    if minimum_blocks != 8:
        raise ValueError(
            "v1 internal process envelope freezes minimum_blocks_per_group at 8"
        )
    if tolerance < 0:
        raise ValueError(
            "certification.gain_tolerance must be non-negative"
        )

    return {
        "schema_version": 1,
        "analysis_id": analysis_id,
        "process_manifest": _path(
            plan.get("process_manifest"),
            name="process_manifest",
        ),
        "generation_receipt": _path(
            plan.get("generation_receipt"),
            name="generation_receipt",
        ),
        "validation_separation_receipt": _path(
            plan.get("validation_separation_receipt"),
            name="validation_separation_receipt",
        ),
        "qualification_receipt": _path(
            plan.get("qualification_receipt"),
            name="qualification_receipt",
        ),
        "upstream_model_artifacts": [
            dict(row)
            for row in normalize_upstream_model_artifact_declarations(
                plan.get("upstream_model_artifacts")
            )
        ],
        "validation_dataset_id": dataset_id,
        "validation_roster": normalized_roster,
        "score": _validate_score_contract(plan.get("score")),
        "levels": levels,
        "certification": {
            "component_one_sided_alpha": alpha,
            "minimum_refits": minimum_refits,
            "minimum_blocks_per_group": minimum_blocks,
            "gain_tolerance": tolerance,
        },
    }


def load_training_process_internal_freeze_plan(
    path: str | Path,
) -> dict[str, object]:
    plan_path = Path(path)
    try:
        raw = json.loads(plan_path.read_text(encoding="utf-8"))
    except json.JSONDecodeError as exc:
        raise ValueError(
            f"internal freeze plan is not valid JSON: {plan_path}"
        ) from exc
    return validate_training_process_internal_freeze_plan(
        _mapping(raw, name="internal freeze plan")
    )


def _validation_metadata(
    path: Path,
    roster: Mapping[str, object],
    *,
    minimum_blocks: int,
) -> tuple[
    tuple[str, ...],
    tuple[str, ...],
    tuple[str, ...],
    tuple[float, ...],
    dict[str, int],
]:
    rows = _read_rows(path, str(roster["format"]))
    if not rows:
        raise ValueError("validation metadata roster is empty")
    columns = {
        str(roster["row_id_column"]),
        str(roster["group_column"]),
        str(roster["block_column"]),
        str(roster["weight_column"]),
    }
    row_ids: list[str] = []
    groups: list[str] = []
    blocks: list[str] = []
    weights: list[float] = []
    for index, row in enumerate(rows):
        if set(row) != columns:
            raise ValueError(
                "pre-outcome validation roster must contain exactly "
                "row_id/group/block/weight metadata columns"
            )
        row_ids.append(
            _text(
                _value(
                    row,
                    str(roster["row_id_column"]),
                    row_index=index,
                ),
                name=f"validation row {index} row_id",
            )
        )
        groups.append(
            _text(
                _value(
                    row,
                    str(roster["group_column"]),
                    row_index=index,
                ),
                name=f"validation row {index} group",
            )
        )
        blocks.append(
            _text(
                _value(
                    row,
                    str(roster["block_column"]),
                    row_index=index,
                ),
                name=f"validation row {index} block",
            )
        )
        weights.append(
            _finite_number(
                _value(
                    row,
                    str(roster["weight_column"]),
                    row_index=index,
                ),
                name=f"validation row {index} weight",
            )
        )
    if len(row_ids) != len(set(row_ids)):
        raise ValueError("validation metadata row IDs must be unique")
    if any(weight < 0 for weight in weights) or not any(
        weight > 0 for weight in weights
    ):
        raise ValueError(
            "validation metadata weights must be non-negative and positive in total"
        )

    block_counts: dict[str, int] = {}
    group_set = tuple(sorted(set(groups)))
    for group in group_set:
        positive_blocks = {
            blocks[index]
            for index, value in enumerate(groups)
            if value == group and weights[index] > 0
        }
        if len(positive_blocks) < minimum_blocks:
            raise ValueError(
                f"validation group {group!r} has fewer than "
                f"{minimum_blocks} positive-mass blocks"
            )
        block_counts[group] = len(positive_blocks)

    return (
        tuple(row_ids),
        tuple(groups),
        tuple(blocks),
        tuple(weights),
        block_counts,
    )


def create_training_process_internal_freeze_manifest(
    plan_path: str | Path,
    manifest_out: str | Path,
) -> dict[str, object]:
    """Freeze all non-outcome inputs required by the internal process route."""

    plan_path = Path(plan_path)
    plan = load_training_process_internal_freeze_plan(plan_path)
    base = plan_path.parent

    process_path = _resolve(
        base,
        str(plan["process_manifest"]),
    )
    generation_path = _resolve(
        base,
        str(plan["generation_receipt"]),
    )
    separation_path = _resolve(
        base,
        str(plan["validation_separation_receipt"]),
    )
    qualification_path = _resolve(
        base,
        str(plan["qualification_receipt"]),
    )
    roster_spec = plan["validation_roster"]
    assert isinstance(roster_spec, Mapping)
    validation_path = _resolve(
        base,
        str(roster_spec["path"]),
    )
    for path in (
        process_path,
        generation_path,
        separation_path,
        qualification_path,
        validation_path,
    ):
        if not path.is_file():
            raise FileNotFoundError(path)

    process_manifest = _load_json(
        process_path,
        name="training process manifest",
    )
    if process_manifest.get("manifest_type") != PROCESS_MANIFEST_TYPE:
        raise ValueError("training process manifest_type mismatch")
    process_id = _text(
        process_manifest.get("training_process_id"),
        name="training process manifest.training_process_id",
    )
    refit_ids_raw = process_manifest.get("refit_ids")
    if not isinstance(refit_ids_raw, list) or not refit_ids_raw:
        raise ValueError(
            "training process manifest.refit_ids must be a non-empty array"
        )
    refit_ids = tuple(str(value) for value in refit_ids_raw)
    if len(refit_ids) != len(set(refit_ids)):
        raise ValueError("training process manifest.refit_ids must be unique")
    if len(refit_ids) < 8:
        raise ValueError("training process manifest has fewer than 8 refits")
    process_sha = _file_sha256(process_path)

    generation = _load_json(
        generation_path,
        name="training process generation receipt",
    )
    model_snapshot = _require_generation_receipt(
        generation,
        process_manifest_sha256=process_sha,
        training_process_id=process_id,
        refit_ids=refit_ids,
    )
    verify_upstream_model_artifact_snapshot(
        model_snapshot,
        plan["upstream_model_artifacts"],
        base_dir=base,
        refit_ids=refit_ids,
    )

    (
        row_ids,
        groups,
        blocks,
        weights,
        blocks_by_group,
    ) = _validation_metadata(
        validation_path,
        roster_spec,
        minimum_blocks=int(
            plan["certification"]["minimum_blocks_per_group"]
        ),
    )
    row_semantic_sha = validation_row_id_semantic_sha256(row_ids)
    metadata_sha = validation_metadata_sha256(
        row_ids,
        groups,
        blocks,
        weights,
    )

    separation = _load_json(
        separation_path,
        name="validation-separation receipt",
    )
    _require_separation_receipt(
        separation,
        process_manifest_sha256=process_sha,
        training_process_id=process_id,
        validation_row_semantic_sha256=row_semantic_sha,
    )

    qualification = _load_json(
        qualification_path,
        name="v5 qualification receipt",
    )
    _require_v5_qualification_receipt(qualification)

    implementation_snapshot = [
        dict(row)
        for row in implementation_source_snapshot_for_surface(
            CANONICAL_SURFACE
        )
    ]
    environment_snapshot = runtime_environment_snapshot_for_surface(
        CANONICAL_SURFACE
    )

    frozen_at = (
        datetime.now(timezone.utc)
        .replace(microsecond=0)
        .isoformat()
        .replace("+00:00", "Z")
    )
    manifest = {
        "schema_version": 1,
        "manifest_type": INTERNAL_FREEZE_MANIFEST_TYPE,
        "frozen_at_utc": frozen_at,
        "analysis_id": plan["analysis_id"],
        "canonical_surface": CANONICAL_SURFACE,
        "statistical_core": STATISTICAL_CORE,
        "process": {
            "training_process_id": process_id,
            "process_manifest_sha256": process_sha,
            "generation_receipt_sha256": _file_sha256(
                generation_path
            ),
            "validation_separation_receipt_sha256": _file_sha256(
                separation_path
            ),
            "row_identity_namespace": separation[
                "row_identity_namespace"
            ],
            "refit_ids": sorted(refit_ids),
            "upstream_model_artifact_lock_id": MODEL_ARTIFACT_LOCK_ID,
            "upstream_model_artifact_snapshot": [
                dict(row) for row in model_snapshot
            ],
        },
        "qualification": {
            "receipt_type": qualification["receipt_type"],
            "method_version": qualification["method_version"],
            "receipt_sha256": _file_sha256(qualification_path),
            "null_qualification_passed": True,
            "power_qualification_passed": True,
            "combined_qualification_passed": True,
        },
        "validation": {
            "dataset_id": plan["validation_dataset_id"],
            "metadata_sha256": metadata_sha,
            "row_id_semantic_sha256": row_semantic_sha,
            "metadata_roster_file_sha256": _file_sha256(
                validation_path
            ),
            "row_count": len(row_ids),
            "group_count": len(set(groups)),
            "positive_mass_blocks_by_group": blocks_by_group,
        },
        "score": plan["score"],
        "levels": plan["levels"],
        "certification": plan["certification"],
        "implementation_lock_id": IMPLEMENTATION_LOCK_ID,
        "implementation_source_snapshot": implementation_snapshot,
        "runtime_environment_lock_id": ENVIRONMENT_LOCK_ID,
        "runtime_environment_snapshot": environment_snapshot,
        "boundaries": {
            "validation_outcomes_read_by_freeze_generator": False,
            "validation_roster_outcome_columns_allowed": False,
            "caller_supplied_freeze_timestamp_allowed": False,
            "manifest_overwrite_allowed": False,
            "fixed_set_results_reclassified": False,
            "untouched_external_route_opened": False,
        },
    }

    output_path = Path(manifest_out)
    if output_path.exists():
        raise FileExistsError(
            "internal confirmatory freeze manifest already exists and "
            f"will not be overwritten: {output_path}"
        )
    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_text(
        json.dumps(
            manifest,
            indent=2,
            sort_keys=True,
            allow_nan=False,
        )
        + "\n",
        encoding="utf-8",
    )
    return {
        "receipt_type": (
            "odsp_training_process_internal_confirmatory_freeze_receipt_v1"
        ),
        "manifest_path": str(output_path),
        "manifest_sha256": _file_sha256(output_path),
        "frozen_at_utc": frozen_at,
        "analysis_id": plan["analysis_id"],
        "training_process_id": process_id,
        "validation_dataset_id": plan["validation_dataset_id"],
        "refit_count": len(refit_ids),
        "validation_row_count": len(row_ids),
        "boundaries": manifest["boundaries"],
    }
