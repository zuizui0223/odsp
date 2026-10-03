"""Pre-outcome semantic freeze for independent all-refit external lattices."""
from __future__ import annotations

from datetime import datetime, timezone
import hashlib
import json
import math
from pathlib import Path
from typing import Mapping, Sequence

from .external_freeze_manifest import _file_sha256
from .external_paired_lattice_freeze_manifest import _validate_lattice_definition
from .frozen_confirmatory_route import build_frozen_confirmatory_route
from .information_transfer_contract import (
    _mapping,
    _read_rows,
    _reject_unknown,
    _required_float,
    _required_int,
    _text,
    _validate_score_contract,
    _value,
    _weight,
)
from .untouched_external_refit_positive_contract_v2 import _row_roster_sha256
from .upstream_model_artifact_lock import (
    MODEL_ARTIFACT_LOCK_ID,
    normalize_upstream_model_artifact_declarations,
    snapshot_upstream_model_artifacts,
)


VALIDATION_DESIGN = {
    "kind": "independent_groups",
    "validation_group_independence_assumed": True,
    "within_group_block_exchangeability_assumed": True,
    "cross_group_shared_resampling": False,
}

_TOP_LEVEL = {
    "schema_version",
    "upstream_model_set_id",
    "upstream_model_artifacts",
    "external_dataset_id",
    "roster",
    "refit_ids",
    "score",
    "base_information",
    "information_blocks",
    "nodes",
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
_CERT_FIELDS = {
    "alternative",
    "familywise_lower_confidence_level",
    "bootstrap_draws",
    "seed",
    "minimum_refits",
    "minimum_blocks_per_group",
    "gain_tolerance",
}


def independent_row_metadata_sha256(
    records: Sequence[tuple[str, str, str, float]],
) -> str:
    """Hash the exact independent row/group/block/weight assignment."""

    canonical = [
        {
            "row_id": str(row_id),
            "group": str(group),
            "block": str(block),
            "weight": float(weight),
        }
        for row_id, group, block, weight in records
    ]
    canonical.sort(key=lambda row: row["row_id"])
    payload = json.dumps(
        canonical,
        ensure_ascii=False,
        sort_keys=True,
        separators=(",", ":"),
    ) + "\n"
    return hashlib.sha256(payload.encode("utf-8")).hexdigest()


def validate_independent_external_lattice_freeze_plan(
    raw: Mapping[str, object],
) -> dict[str, object]:
    plan = _mapping(raw, name="freeze_plan")
    _reject_unknown(plan, _TOP_LEVEL, name="freeze_plan")
    version = plan.get("schema_version")
    if isinstance(version, bool) or version != 1:
        raise ValueError("freeze_plan.schema_version must be 1")

    model_set = _text(plan.get("upstream_model_set_id"), name="upstream_model_set_id")
    dataset_id = _text(plan.get("external_dataset_id"), name="external_dataset_id")

    roster = _mapping(plan.get("roster"), name="roster")
    _reject_unknown(roster, _ROSTER_FIELDS, name="roster")
    roster_path = _text(roster.get("path"), name="roster.path")
    roster_format = _text(roster.get("format"), name="roster.format").lower()
    if roster_format not in {"csv", "json"}:
        raise ValueError("roster.format must be 'csv' or 'json'")
    row_id_column = _text(roster.get("row_id_column"), name="roster.row_id_column")
    group_column = _text(roster.get("group_column"), name="roster.group_column")
    block_column = _text(roster.get("block_column"), name="roster.block_column")
    weight_column = _text(roster.get("weight_column"), name="roster.weight_column")
    role_columns = (row_id_column, group_column, block_column, weight_column)
    if len(set(role_columns)) != len(role_columns):
        raise ValueError("roster row_id, group, block and weight columns must be distinct")

    raw_refits = plan.get("refit_ids")
    if not isinstance(raw_refits, list):
        raise ValueError("refit_ids must be a JSON array")
    refit_ids = sorted(
        _text(item, name=f"refit_ids[{index}]")
        for index, item in enumerate(raw_refits)
    )
    if len(refit_ids) != len(set(refit_ids)):
        raise ValueError("refit_ids must be unique")
    model_artifacts = normalize_upstream_model_artifact_declarations(
        plan.get("upstream_model_artifacts"), refit_ids=refit_ids
    )

    score = _validate_score_contract(plan.get("score"))
    blocks, nodes, base, edge_count = _validate_lattice_definition(
        plan.get("information_blocks"),
        plan.get("nodes"),
        plan.get("base_information"),
    )
    if len(blocks) not in {2, 3} or edge_count not in {4, 12}:
        raise ValueError(
            "independent external lattice is qualified only for 2 or 3 information blocks"
        )

    cert = _mapping(plan.get("certification"), name="certification")
    _reject_unknown(cert, _CERT_FIELDS, name="certification")
    alternative = _text(cert.get("alternative"), name="certification.alternative")
    if alternative != "greater":
        raise ValueError("certification.alternative must be 'greater'")
    confidence = _required_float(
        cert.get("familywise_lower_confidence_level"),
        name="certification.familywise_lower_confidence_level",
    )
    if not math.isfinite(confidence) or not 0 < confidence < 1:
        raise ValueError(
            "certification.familywise_lower_confidence_level must lie strictly between zero and one"
        )
    draws = _required_int(
        cert.get("bootstrap_draws"), name="certification.bootstrap_draws"
    )
    if draws < 500:
        raise ValueError("certification.bootstrap_draws must be >= 500")
    seed = _required_int(cert.get("seed"), name="certification.seed")
    if seed < 0:
        raise ValueError("certification.seed must be non-negative")
    minimum_refits = _required_int(
        cert.get("minimum_refits"), name="certification.minimum_refits"
    )
    if minimum_refits < 2:
        raise ValueError("certification.minimum_refits must be >= 2")
    if len(refit_ids) < minimum_refits:
        raise ValueError("freeze plan contains fewer refits than certification.minimum_refits")
    minimum_blocks = _required_int(
        cert.get("minimum_blocks_per_group"),
        name="certification.minimum_blocks_per_group",
    )
    if minimum_blocks < 2:
        raise ValueError("certification.minimum_blocks_per_group must be >= 2")
    tolerance = _required_float(
        cert.get("gain_tolerance"), name="certification.gain_tolerance"
    )
    if not math.isfinite(tolerance) or tolerance < 0:
        raise ValueError("certification.gain_tolerance must be finite and non-negative")

    return {
        "schema_version": 1,
        "upstream_model_set_id": model_set,
        "upstream_model_artifacts": [dict(row) for row in model_artifacts],
        "external_dataset_id": dataset_id,
        "roster": {
            "path": roster_path,
            "format": roster_format,
            "row_id_column": row_id_column,
            "group_column": group_column,
            "block_column": block_column,
            "weight_column": weight_column,
        },
        "refit_ids": refit_ids,
        "score": score,
        "base_information": base,
        "information_blocks": blocks,
        "nodes": nodes,
        "edge_count": edge_count,
        "certification": {
            "alternative": "greater",
            "familywise_lower_confidence_level": confidence,
            "bootstrap_draws": draws,
            "seed": seed,
            "minimum_refits": minimum_refits,
            "minimum_blocks_per_group": minimum_blocks,
            "gain_tolerance": tolerance,
        },
    }


def load_independent_external_lattice_freeze_plan(
    path: str | Path,
) -> dict[str, object]:
    plan_path = Path(path)
    try:
        raw = json.loads(plan_path.read_text(encoding="utf-8"))
    except json.JSONDecodeError as exc:
        raise ValueError("independent lattice freeze plan is not valid JSON") from exc
    return validate_independent_external_lattice_freeze_plan(
        _mapping(raw, name="freeze_plan")
    )


def create_independent_external_lattice_freeze_manifest(
    plan_path: str | Path,
    manifest_out: str | Path,
) -> dict[str, object]:
    plan_path = Path(plan_path)
    plan = load_independent_external_lattice_freeze_plan(plan_path)
    roster_spec = plan["roster"]
    assert isinstance(roster_spec, Mapping)
    roster_path = Path(str(roster_spec["path"]))
    if not roster_path.is_absolute():
        roster_path = plan_path.parent / roster_path
    if not roster_path.is_file():
        raise FileNotFoundError(roster_path)

    rows = _read_rows(roster_path, str(roster_spec["format"]))
    row_id_column = str(roster_spec["row_id_column"])
    group_column = str(roster_spec["group_column"])
    block_column = str(roster_spec["block_column"])
    weight_column = str(roster_spec["weight_column"])
    expected_columns = {row_id_column, group_column, block_column, weight_column}
    row_ids: list[str] = []
    metadata: list[tuple[str, str, str, float]] = []
    for index, row in enumerate(rows):
        keys = set(row)
        if keys != expected_columns:
            extra = sorted(keys - expected_columns)
            missing = sorted(expected_columns - keys)
            raise ValueError(
                "pre-outcome independent roster must contain only row_id, group, block and weight metadata; "
                f"row={index}, missing={missing!r}, extra={extra!r}"
            )
        row_id = _text(
            _value(row, row_id_column, row_index=index),
            name=f"row {index} row_id",
        )
        group = _text(
            _value(row, group_column, row_index=index),
            name=f"row {index} group",
        )
        block = _text(
            _value(row, block_column, row_index=index),
            name=f"row {index} block",
        )
        weight = _weight(
            _value(row, weight_column, row_index=index),
            column=weight_column,
            row_index=index,
        )
        row_ids.append(row_id)
        metadata.append((row_id, group, block, weight))
    if not row_ids:
        raise ValueError("external row roster is empty")
    if len(row_ids) != len(set(row_ids)):
        raise ValueError("pre-outcome roster row IDs must be unique")
    if not sum(row[3] for row in metadata) > 0:
        raise ValueError("pre-outcome independent roster weights must have positive total mass")

    model_artifact_snapshot = snapshot_upstream_model_artifacts(
        plan["upstream_model_artifacts"],
        base_dir=plan_path.parent,
        refit_ids=plan["refit_ids"],
    )
    confirmatory_route = build_frozen_confirmatory_route(
        validation_design="independent_groups",
        information_structure="complete_lattice",
        information_block_count=len(plan["information_blocks"]),
    )
    frozen_at = (
        datetime.now(timezone.utc)
        .replace(microsecond=0)
        .isoformat()
        .replace("+00:00", "Z")
    )
    manifest = {
        "schema_version": 1,
        "manifest_type": "odsp_pre_external_outcome_independent_lattice_freeze_v1",
        "frozen_at_utc": frozen_at,
        "upstream_model_set_id": plan["upstream_model_set_id"],
        "upstream_model_artifact_lock_id": MODEL_ARTIFACT_LOCK_ID,
        "upstream_model_artifact_snapshot": [
            dict(row) for row in model_artifact_snapshot
        ],
        "external_dataset_id": plan["external_dataset_id"],
        "external_row_ids_sha256": _row_roster_sha256(row_ids),
        "independent_row_metadata_sha256": independent_row_metadata_sha256(metadata),
        "validation_design": dict(VALIDATION_DESIGN),
        "confirmatory_route": confirmatory_route,
        "refit_ids": plan["refit_ids"],
        "score": plan["score"],
        "base_information": plan["base_information"],
        "information_blocks": plan["information_blocks"],
        "nodes": plan["nodes"],
        "edge_count": plan["edge_count"],
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
        "receipt_type": "odsp_pre_external_outcome_independent_lattice_freeze_receipt_v1",
        "manifest_path": str(output_path),
        "manifest_sha256": _file_sha256(output_path),
        "freeze_plan_sha256": _file_sha256(plan_path),
        "roster_file_sha256": _file_sha256(roster_path),
        "frozen_at_utc": frozen_at,
        "external_row_ids_sha256": manifest["external_row_ids_sha256"],
        "independent_row_metadata_sha256": manifest["independent_row_metadata_sha256"],
        "external_row_count": len(row_ids),
        "upstream_model_set_id": plan["upstream_model_set_id"],
        "upstream_model_artifact_lock_id": MODEL_ARTIFACT_LOCK_ID,
        "upstream_model_artifact_snapshot": [
            dict(row) for row in model_artifact_snapshot
        ],
        "external_dataset_id": plan["external_dataset_id"],
        "refit_count": len(plan["refit_ids"]),
        "information_block_count": len(plan["information_blocks"]),
        "node_count": len(plan["nodes"]),
        "edge_count": plan["edge_count"],
        "validation_design": dict(VALIDATION_DESIGN),
        "confirmatory_route": confirmatory_route,
        "boundaries": {
            "manifest_timestamp_generated_by_odsp_runtime_clock": True,
            "caller_supplied_freeze_timestamp_allowed": False,
            "manifest_overwrite_allowed": False,
            "roster_outcome_columns_allowed": False,
            "external_outcomes_read_by_freeze_generator": False,
            "confirmatory_route_frozen_before_outcome_access": True,
            "upstream_model_artifact_bytes_frozen_before_outcome_access": True,
            "model_artifact_local_paths_are_semantic": False,
            "independent_row_metadata_frozen_before_outcome_access": True,
            "complete_lattice_node_table_frozen": True,
            "validation_group_independence_assumed": True,
            "within_group_block_exchangeability_assumed": True,
            "cross_group_shared_resampling": False,
            "four_or_more_information_blocks_allowed": False,
            "runtime_clock_independently_attested": False,
            "trusted_timestamp_authority_used": False,
        },
    }
