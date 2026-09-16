"""Pre-outcome semantic freeze for paired all-refit external lattices."""
from __future__ import annotations

from datetime import datetime, timezone
import hashlib
import itertools
import json
import math
from pathlib import Path
from typing import Mapping, Sequence

from .external_freeze_manifest import _file_sha256
from .information_lattice import InformationBlock, _canonical_subset, _validate_blocks
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
from .untouched_external_refit_shared_block_positive_contract_v3 import _VALIDATION_DESIGN


_TOP_LEVEL = {
    "schema_version",
    "upstream_model_set_id",
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
_BLOCK_FIELDS = {"name", "variables"}
_NODE_FIELDS = {"blocks", "score_column"}
_CERT_FIELDS = {
    "alternative",
    "familywise_lower_confidence_level",
    "bootstrap_draws",
    "seed",
    "minimum_refits",
    "minimum_shared_blocks",
    "gain_tolerance",
}


def _paired_row_metadata_sha256(
    records: Sequence[tuple[str, str, str, float]],
) -> str:
    """Content-address the exact pre-outcome paired row assignment.

    Records are canonicalized by row ID and serialized as compact sorted-key JSON,
    avoiding dependence on input row order or delimiter escaping conventions.
    """

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


def _all_subsets(order: tuple[str, ...]) -> tuple[tuple[str, ...], ...]:
    result: list[tuple[str, ...]] = []
    for size in range(len(order) + 1):
        result.extend(tuple(combo) for combo in itertools.combinations(order, size))
    return tuple(result)


def _validate_lattice_definition(
    raw_blocks: object,
    raw_nodes: object,
    raw_base: object,
) -> tuple[list[dict[str, object]], list[dict[str, object]], list[str], int]:
    if not isinstance(raw_blocks, list):
        raise ValueError("information_blocks must be a JSON array")
    block_rows: list[InformationBlock] = []
    normalized_blocks: list[dict[str, object]] = []
    for index, raw in enumerate(raw_blocks):
        value = _mapping(raw, name=f"information_blocks[{index}]")
        _reject_unknown(value, _BLOCK_FIELDS, name=f"information_blocks[{index}]")
        name = _text(value.get("name"), name=f"information_blocks[{index}].name")
        variables_raw = value.get("variables")
        if not isinstance(variables_raw, list) or not variables_raw:
            raise ValueError(f"information_blocks[{index}].variables must be a non-empty JSON array")
        variables = [
            _text(item, name=f"information_blocks[{index}].variables[{j}]")
            for j, item in enumerate(variables_raw)
        ]
        row = InformationBlock(name=name, variables=tuple(variables))
        block_rows.append(row)
        normalized_blocks.append({"name": row.name, "variables": list(row.variables)})
    blocks = _validate_blocks(block_rows)
    if len(blocks) not in {2, 3}:
        raise ValueError(
            "paired external lattice is qualified only for 2 or 3 information blocks"
        )
    order = tuple(row.name for row in blocks)

    if not isinstance(raw_base, list):
        raise ValueError("base_information must be a JSON array")
    base = [
        _text(item, name=f"base_information[{index}]")
        for index, item in enumerate(raw_base)
    ]
    if len(set(base)) != len(base):
        raise ValueError("base_information must contain unique labels")
    block_variables = {value for row in blocks for value in row.variables}
    overlap = sorted(set(base) & block_variables)
    if overlap:
        raise ValueError(
            f"base_information must be disjoint from added information-block variables; overlap={overlap!r}"
        )

    if not isinstance(raw_nodes, list):
        raise ValueError("nodes must be a JSON array")
    mapping: dict[tuple[str, ...], str] = {}
    score_columns: set[str] = set()
    for index, raw in enumerate(raw_nodes):
        value = _mapping(raw, name=f"nodes[{index}]")
        _reject_unknown(value, _NODE_FIELDS, name=f"nodes[{index}]")
        raw_subset = value.get("blocks")
        if not isinstance(raw_subset, list):
            raise ValueError(f"nodes[{index}].blocks must be a JSON array")
        subset = _canonical_subset(
            [
                _text(item, name=f"nodes[{index}].blocks[{j}]")
                for j, item in enumerate(raw_subset)
            ],
            order,
        )
        score_column = _text(value.get("score_column"), name=f"nodes[{index}].score_column")
        if subset in mapping:
            raise ValueError(f"duplicate lattice node for blocks {subset!r}")
        if score_column in score_columns:
            raise ValueError("nodes.score_column values must be unique")
        mapping[subset] = score_column
        score_columns.add(score_column)
    expected = set(_all_subsets(order))
    missing = sorted(expected - set(mapping), key=lambda item: (len(item), item))
    extra = sorted(set(mapping) - expected, key=lambda item: (len(item), item))
    if missing or extra:
        raise ValueError(
            "nodes must supply the complete lattice subset table; "
            f"missing={missing!r}, extra={extra!r}"
        )
    normalized_nodes = [
        {"blocks": list(subset), "score_column": mapping[subset]}
        for subset in _all_subsets(order)
    ]
    edge_count = len(order) * 2 ** (len(order) - 1)
    if edge_count not in {4, 12}:
        raise AssertionError("paired external lattice edge family is outside calibrated scope")
    return normalized_blocks, normalized_nodes, base, edge_count


def validate_paired_external_lattice_freeze_plan(
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
    roster_columns = (row_id_column, group_column, block_column, weight_column)
    if len(set(roster_columns)) != len(roster_columns):
        raise ValueError("roster row_id, group, block and weight columns must be distinct")

    raw_refits = plan.get("refit_ids")
    if not isinstance(raw_refits, list):
        raise ValueError("refit_ids must be a JSON array")
    refit_ids = sorted(_text(item, name=f"refit_ids[{i}]") for i, item in enumerate(raw_refits))
    if len(refit_ids) != len(set(refit_ids)):
        raise ValueError("refit_ids must be unique")

    score = _validate_score_contract(plan.get("score"))
    blocks, nodes, base, edge_count = _validate_lattice_definition(
        plan.get("information_blocks"),
        plan.get("nodes"),
        plan.get("base_information"),
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
        raise ValueError("familywise lower confidence level must lie strictly between zero and one")
    draws = _required_int(cert.get("bootstrap_draws"), name="certification.bootstrap_draws")
    if draws < 500:
        raise ValueError("certification.bootstrap_draws must be >= 500")
    seed = _required_int(cert.get("seed"), name="certification.seed")
    minimum_refits = _required_int(cert.get("minimum_refits"), name="certification.minimum_refits")
    if minimum_refits < 2:
        raise ValueError("certification.minimum_refits must be >= 2")
    if len(refit_ids) < minimum_refits:
        raise ValueError("freeze plan contains fewer refits than certification.minimum_refits")
    minimum_shared = _required_int(
        cert.get("minimum_shared_blocks"), name="certification.minimum_shared_blocks"
    )
    if minimum_shared < 2:
        raise ValueError("certification.minimum_shared_blocks must be >= 2")
    tolerance = _required_float(cert.get("gain_tolerance"), name="certification.gain_tolerance")
    if not math.isfinite(tolerance) or tolerance < 0:
        raise ValueError("certification.gain_tolerance must be finite and non-negative")

    return {
        "schema_version": 1,
        "upstream_model_set_id": model_set,
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
            "minimum_shared_blocks": minimum_shared,
            "gain_tolerance": tolerance,
        },
    }


def load_paired_external_lattice_freeze_plan(path: str | Path) -> dict[str, object]:
    plan_path = Path(path)
    try:
        raw = json.loads(plan_path.read_text(encoding="utf-8"))
    except json.JSONDecodeError as exc:
        raise ValueError("paired lattice freeze plan is not valid JSON") from exc
    return validate_paired_external_lattice_freeze_plan(_mapping(raw, name="freeze_plan"))


def create_paired_external_lattice_freeze_manifest(
    plan_path: str | Path,
    manifest_out: str | Path,
) -> dict[str, object]:
    plan_path = Path(plan_path)
    plan = load_paired_external_lattice_freeze_plan(plan_path)
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
    paired_records: list[tuple[str, str, str, float]] = []
    for index, row in enumerate(rows):
        keys = set(row)
        if keys != expected_columns:
            extra = sorted(keys - expected_columns)
            missing = sorted(expected_columns - keys)
            raise ValueError(
                "pre-outcome paired roster must contain only row_id, group, block and weight metadata; "
                f"row={index}, missing={missing!r}, extra={extra!r}"
            )
        row_id = _text(_value(row, row_id_column, row_index=index), name=f"row {index} row_id")
        group = _text(_value(row, group_column, row_index=index), name=f"row {index} group")
        block = _text(_value(row, block_column, row_index=index), name=f"row {index} block")
        weight = _weight(
            _value(row, weight_column, row_index=index),
            column=weight_column,
            row_index=index,
        )
        row_ids.append(row_id)
        paired_records.append((row_id, group, block, weight))
    if not row_ids:
        raise ValueError("external row roster is empty")
    if len(row_ids) != len(set(row_ids)):
        raise ValueError("pre-outcome roster row IDs must be unique")
    if not sum(record[3] for record in paired_records) > 0:
        raise ValueError("pre-outcome paired roster weights must have positive total mass")

    frozen_at = datetime.now(timezone.utc).replace(microsecond=0).isoformat().replace("+00:00", "Z")
    manifest = {
        "schema_version": 1,
        "manifest_type": "odsp_pre_external_outcome_paired_lattice_freeze_v1",
        "frozen_at_utc": frozen_at,
        "upstream_model_set_id": plan["upstream_model_set_id"],
        "external_dataset_id": plan["external_dataset_id"],
        "external_row_ids_sha256": _row_roster_sha256(row_ids),
        "paired_row_metadata_sha256": _paired_row_metadata_sha256(paired_records),
        "validation_design": dict(_VALIDATION_DESIGN),
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
        raise FileExistsError(f"freeze manifest already exists and will not be overwritten: {output_path}")
    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_text(json.dumps(manifest, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    return {
        "receipt_type": "odsp_pre_external_outcome_paired_lattice_freeze_receipt_v1",
        "manifest_path": str(output_path),
        "manifest_sha256": _file_sha256(output_path),
        "freeze_plan_sha256": _file_sha256(plan_path),
        "roster_file_sha256": _file_sha256(roster_path),
        "frozen_at_utc": frozen_at,
        "external_row_ids_sha256": manifest["external_row_ids_sha256"],
        "paired_row_metadata_sha256": manifest["paired_row_metadata_sha256"],
        "external_row_count": len(row_ids),
        "upstream_model_set_id": plan["upstream_model_set_id"],
        "external_dataset_id": plan["external_dataset_id"],
        "refit_count": len(plan["refit_ids"]),
        "information_block_count": len(plan["information_blocks"]),
        "node_count": len(plan["nodes"]),
        "edge_count": plan["edge_count"],
        "validation_design": dict(_VALIDATION_DESIGN),
        "boundaries": {
            "manifest_timestamp_generated_by_odsp_runtime_clock": True,
            "caller_supplied_freeze_timestamp_allowed": False,
            "manifest_overwrite_allowed": False,
            "roster_outcome_columns_allowed": False,
            "external_outcomes_read_by_freeze_generator": False,
            "paired_row_metadata_frozen_before_outcome_access": True,
            "complete_lattice_node_table_frozen": True,
            "paired_shared_block_design_frozen": True,
            "four_or_more_information_blocks_allowed": False,
            "runtime_clock_independently_attested": False,
            "trusted_timestamp_authority_used": False,
        },
    }