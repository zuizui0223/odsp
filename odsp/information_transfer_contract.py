"""Executable contracts for model-agnostic information-transfer audits.

This contract intentionally begins *after* model fitting. Upstream software may be
R, Stan, INLA, Python, a neural network or any other system. The input table must
contain held-out row-wise predictive scores for each declared information level.
ODSP binds those score columns to an explicit strict information filtration,
independent groups, optional resampling blocks and optional row weights, then
returns point and familywise-certified transfer ceilings.

No model is fitted or refitted by this module. Unknown contract fields fail
closed so modelling choices cannot accidentally leak into the ODSP inference
contract.
"""
from __future__ import annotations

import csv
import hashlib
import json
import math
from pathlib import Path
from typing import Mapping

from .information_transfer import (
    InformationLevelScore,
    certify_information_transfer,
    decompose_information_transfer,
    validate_information_filtration,
)


_TOP_LEVEL = {
    "schema_version",
    "endpoint_id",
    "data",
    "columns",
    "score_name",
    "levels",
    "certification",
}
_DATA_FIELDS = {"path", "format"}
_COLUMN_FIELDS = {"group", "block", "weight"}
_LEVEL_FIELDS = {"name", "information", "score_column"}
_CERTIFICATION_FIELDS = {
    "familywise_confidence_level",
    "bootstrap_draws",
    "seed",
    "minimum_blocks_per_group",
    "gain_tolerance",
}


def _mapping(value: object, *, name: str) -> Mapping[str, object]:
    if not isinstance(value, Mapping):
        raise ValueError(f"{name} must be a JSON object")
    return value


def _text(value: object, *, name: str) -> str:
    if not isinstance(value, str) or not value.strip():
        raise ValueError(f"{name} must be a non-empty string")
    return value.strip()


def _reject_unknown(mapping: Mapping[str, object], allowed: set[str], *, name: str) -> None:
    unknown = sorted(set(mapping) - allowed)
    if unknown:
        raise ValueError(f"{name} contains unknown fields: {', '.join(unknown)}")


def _required_float(value: object, *, name: str) -> float:
    if isinstance(value, bool):
        raise ValueError(f"{name} must be numeric")
    try:
        number = float(value)
    except (TypeError, ValueError) as exc:
        raise ValueError(f"{name} must be numeric") from exc
    return number


def _required_int(value: object, *, name: str) -> int:
    if isinstance(value, bool):
        raise ValueError(f"{name} must be an integer")
    try:
        number = int(value)
    except (TypeError, ValueError) as exc:
        raise ValueError(f"{name} must be an integer") from exc
    if isinstance(value, float) and not value.is_integer():
        raise ValueError(f"{name} must be an integer")
    return number


def validate_information_transfer_contract(
    contract: Mapping[str, object],
) -> dict[str, object]:
    """Validate and normalize an external-score information-transfer contract."""

    contract = _mapping(contract, name="contract")
    _reject_unknown(contract, _TOP_LEVEL, name="contract")
    if int(contract.get("schema_version", -1)) != 1:
        raise ValueError("schema_version must be 1")

    endpoint_id = _text(contract.get("endpoint_id"), name="endpoint_id")
    score_name = _text(contract.get("score_name"), name="score_name")

    data = _mapping(contract.get("data"), name="data")
    _reject_unknown(data, _DATA_FIELDS, name="data")
    data_path = _text(data.get("path"), name="data.path")
    data_format = _text(data.get("format"), name="data.format").lower()
    if data_format not in {"csv", "json"}:
        raise ValueError("data.format must be 'csv' or 'json'")

    columns = _mapping(contract.get("columns"), name="columns")
    _reject_unknown(columns, _COLUMN_FIELDS, name="columns")
    group = _text(columns.get("group"), name="columns.group")
    block_raw = columns.get("block")
    weight_raw = columns.get("weight")
    block = None if block_raw is None else _text(block_raw, name="columns.block")
    weight = None if weight_raw is None else _text(weight_raw, name="columns.weight")

    raw_levels = contract.get("levels")
    if not isinstance(raw_levels, list) or len(raw_levels) < 2:
        raise ValueError("levels must be a JSON array containing at least two levels")
    normalized_levels: list[dict[str, object]] = []
    score_columns: list[str] = []
    filtration_levels: list[InformationLevelScore] = []
    for index, raw_level in enumerate(raw_levels):
        level = _mapping(raw_level, name=f"levels[{index}]")
        _reject_unknown(level, _LEVEL_FIELDS, name=f"levels[{index}]")
        name = _text(level.get("name"), name=f"levels[{index}].name")
        score_column = _text(
            level.get("score_column"), name=f"levels[{index}].score_column"
        )
        raw_information = level.get("information")
        if not isinstance(raw_information, list):
            raise ValueError(f"levels[{index}].information must be a JSON array")
        information = [
            _text(value, name=f"levels[{index}].information[{item_index}]")
            for item_index, value in enumerate(raw_information)
        ]
        normalized_levels.append(
            {
                "name": name,
                "information": information,
                "score_column": score_column,
            }
        )
        score_columns.append(score_column)
        filtration_levels.append(
            InformationLevelScore(name=name, information=tuple(information), score=[0.0])
        )
    if len(set(score_columns)) != len(score_columns):
        raise ValueError("levels.score_column values must be unique")
    validate_information_filtration(filtration_levels)

    certification = _mapping(contract.get("certification"), name="certification")
    _reject_unknown(
        certification, _CERTIFICATION_FIELDS, name="certification"
    )
    confidence = _required_float(
        certification.get("familywise_confidence_level"),
        name="certification.familywise_confidence_level",
    )
    if not math.isfinite(confidence) or not 0.0 < confidence < 1.0:
        raise ValueError(
            "certification.familywise_confidence_level must lie strictly between zero and one"
        )
    draws = _required_int(
        certification.get("bootstrap_draws"),
        name="certification.bootstrap_draws",
    )
    if draws < 500:
        raise ValueError("certification.bootstrap_draws must be >= 500")
    seed = _required_int(certification.get("seed"), name="certification.seed")
    minimum_blocks = _required_int(
        certification.get("minimum_blocks_per_group"),
        name="certification.minimum_blocks_per_group",
    )
    if minimum_blocks < 2:
        raise ValueError("certification.minimum_blocks_per_group must be >= 2")
    tolerance = _required_float(
        certification.get("gain_tolerance"),
        name="certification.gain_tolerance",
    )
    if not math.isfinite(tolerance) or tolerance < 0:
        raise ValueError(
            "certification.gain_tolerance must be finite and non-negative"
        )

    return {
        "schema_version": 1,
        "endpoint_id": endpoint_id,
        "data": {"path": data_path, "format": data_format},
        "columns": {"group": group, "block": block, "weight": weight},
        "score_name": score_name,
        "levels": normalized_levels,
        "certification": {
            "familywise_confidence_level": confidence,
            "bootstrap_draws": draws,
            "seed": seed,
            "minimum_blocks_per_group": minimum_blocks,
            "gain_tolerance": tolerance,
        },
    }


def load_information_transfer_contract(path: str | Path) -> dict[str, object]:
    contract_path = Path(path)
    try:
        raw = json.loads(contract_path.read_text(encoding="utf-8"))
    except json.JSONDecodeError as exc:
        raise ValueError(f"contract is not valid JSON: {contract_path}") from exc
    return validate_information_transfer_contract(_mapping(raw, name="contract"))


def _read_rows(data_path: Path, data_format: str) -> list[dict[str, object]]:
    if data_format == "csv":
        with data_path.open("r", encoding="utf-8-sig", newline="") as handle:
            rows = [dict(row) for row in csv.DictReader(handle)]
    else:
        raw = json.loads(data_path.read_text(encoding="utf-8"))
        if not isinstance(raw, list) or not all(isinstance(row, Mapping) for row in raw):
            raise ValueError("JSON data must be an array of row objects")
        rows = [dict(row) for row in raw]
    if not rows:
        raise ValueError("information-transfer data contains no rows")
    return rows


def _value(row: Mapping[str, object], column: str, *, row_index: int) -> object:
    if column not in row:
        raise ValueError(f"row {row_index} is missing declared column {column!r}")
    return row[column]


def _score(value: object, *, column: str, row_index: int) -> float:
    if value is None or value == "":
        raise ValueError(
            f"row {row_index} score column {column!r} is missing"
        )
    try:
        number = float(value)
    except (TypeError, ValueError) as exc:
        raise ValueError(
            f"row {row_index} score column {column!r} is not numeric"
        ) from exc
    if math.isnan(number) or number == math.inf:
        raise ValueError(
            f"row {row_index} score column {column!r} must be finite or -inf"
        )
    return number


def _weight(value: object, *, column: str, row_index: int) -> float:
    try:
        number = float(value)
    except (TypeError, ValueError) as exc:
        raise ValueError(
            f"row {row_index} weight column {column!r} is not numeric"
        ) from exc
    if not math.isfinite(number) or number < 0:
        raise ValueError(
            f"row {row_index} weight column {column!r} must be finite and non-negative"
        )
    return number


def _sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def run_information_transfer_contract(path: str | Path) -> dict[str, object]:
    """Execute an external-score transfer contract and emit an audit receipt."""

    contract_path = Path(path)
    contract = load_information_transfer_contract(contract_path)
    data_spec = contract["data"]
    assert isinstance(data_spec, Mapping)
    data_path = Path(str(data_spec["path"]))
    if not data_path.is_absolute():
        data_path = contract_path.parent / data_path
    if not data_path.is_file():
        raise FileNotFoundError(data_path)
    rows = _read_rows(data_path, str(data_spec["format"]))

    columns = contract["columns"]
    assert isinstance(columns, Mapping)
    group_column = str(columns["group"])
    block_column = None if columns.get("block") is None else str(columns["block"])
    weight_column = None if columns.get("weight") is None else str(columns["weight"])

    groups: list[object] = []
    blocks: list[object] | None = [] if block_column is not None else None
    weights: list[float] | None = [] if weight_column is not None else None
    level_scores: list[list[float]] = [[] for _ in contract["levels"]]

    for row_index, row in enumerate(rows):
        group_value = _value(row, group_column, row_index=row_index)
        if group_value is None or group_value == "":
            raise ValueError(f"row {row_index} group column {group_column!r} is missing")
        groups.append(group_value)
        if blocks is not None and block_column is not None:
            block_value = _value(row, block_column, row_index=row_index)
            if block_value is None or block_value == "":
                raise ValueError(
                    f"row {row_index} block column {block_column!r} is missing"
                )
            blocks.append(block_value)
        if weights is not None and weight_column is not None:
            weights.append(
                _weight(
                    _value(row, weight_column, row_index=row_index),
                    column=weight_column,
                    row_index=row_index,
                )
            )
        for level_index, level in enumerate(contract["levels"]):
            assert isinstance(level, Mapping)
            score_column = str(level["score_column"])
            level_scores[level_index].append(
                _score(
                    _value(row, score_column, row_index=row_index),
                    column=score_column,
                    row_index=row_index,
                )
            )

    information_levels = tuple(
        InformationLevelScore(
            name=str(level["name"]),
            information=tuple(str(value) for value in level["information"]),
            score=level_scores[index],
        )
        for index, level in enumerate(contract["levels"])
    )
    certification_spec = contract["certification"]
    assert isinstance(certification_spec, Mapping)
    point = decompose_information_transfer(
        information_levels,
        groups,
        score_name=str(contract["score_name"]),
        sample_weight=weights,
        gain_tolerance=float(certification_spec["gain_tolerance"]),
    )
    certified = certify_information_transfer(
        information_levels,
        groups,
        score_name=str(contract["score_name"]),
        blocks=blocks,
        sample_weight=weights,
        familywise_confidence_level=float(
            certification_spec["familywise_confidence_level"]
        ),
        bootstrap_draws=int(certification_spec["bootstrap_draws"]),
        seed=int(certification_spec["seed"]),
        minimum_blocks_per_group=int(
            certification_spec["minimum_blocks_per_group"]
        ),
        gain_tolerance=float(certification_spec["gain_tolerance"]),
    )

    return {
        "schema_version": 1,
        "receipt_type": "odsp_information_transfer_endpoint",
        "endpoint_id": contract["endpoint_id"],
        "contract_sha256": _sha256(contract_path),
        "data_sha256": _sha256(data_path),
        "data_path_declared": data_spec["path"],
        "data_format": data_spec["format"],
        "input_row_count": len(rows),
        "scientific_roles": {
            "score_name": contract["score_name"],
            "independence_unit": group_column,
            "resampling_block": block_column,
            "row_weight": weight_column,
            "levels": contract["levels"],
            "certification": certification_spec,
        },
        "point_result": point.as_dict(),
        "certified_result": certified.as_dict(),
        "scientific_boundary": {
            "upstream_model_fitted_by_odsp": False,
            "upstream_model_refit_uncertainty_included": False,
            "score_columns_generated_by_odsp": False,
            "information_sets_inferred": False,
            "independence_unit_inferred": False,
            "resampling_block_inferred": False,
            "strict_information_filtration_validated": True,
            "familywise_family_is_all_estimable_group_by_step_cells": True,
        },
    }
