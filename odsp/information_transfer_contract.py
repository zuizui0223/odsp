"""Executable contracts for model-agnostic information-transfer audits.

This contract begins after model fitting. Upstream software may be R, Stan, INLA,
Python, a neural network, or any other modelling stack. The input table contains
one row per held-out observation plus row-wise predictive scores for every
predeclared information level.

ODSP does not fit or refit the upstream models here. It validates the information
filtration, row alignment, score semantics, independence unit, resampling blocks,
and prospective declarations before computing point and familywise-certified
transfer ceilings. Unknown fields fail closed.
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
    "score",
    "evaluation",
    "levels",
    "certification",
}
_DATA_FIELDS = {"path", "format"}
_COLUMN_FIELDS = {"row_id", "group", "block", "weight"}
_SCORE_FIELDS = {
    "kind",
    "name",
    "orientation",
    "common_scoring_rule",
    "common_reference_measure",
}
_EVALUATION_FIELDS = {
    "analysis_mode",
    "heldout_predictions",
    "same_rows_across_levels",
    "heldout_outcome_not_used_for_prediction_or_selection",
    "filtration_frozen_before_outcome_scoring",
    "row_independence_if_no_block",
}
_LEVEL_FIELDS = {"name", "information", "score_column"}
_CERTIFICATION_FIELDS = {
    "familywise_confidence_level",
    "bootstrap_draws",
    "seed",
    "minimum_blocks_per_group",
    "gain_tolerance",
}
_SCORE_KINDS = {"log", "other_proper"}
_ANALYSIS_MODES = {"confirmatory", "descriptive"}


def _mapping(value: object, *, name: str) -> Mapping[str, object]:
    if not isinstance(value, Mapping):
        raise ValueError(f"{name} must be a JSON object")
    return value


def _text(value: object, *, name: str) -> str:
    if not isinstance(value, str) or not value.strip():
        raise ValueError(f"{name} must be a non-empty string")
    return value.strip()


def _bool(value: object, *, name: str) -> bool:
    if not isinstance(value, bool):
        raise ValueError(f"{name} must be true or false")
    return value


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
    if isinstance(value, str) and str(number) != value.strip():
        raise ValueError(f"{name} must be an integer")
    return number


def _validate_score_contract(raw: object) -> dict[str, object]:
    score = _mapping(raw, name="score")
    _reject_unknown(score, _SCORE_FIELDS, name="score")
    kind = _text(score.get("kind"), name="score.kind")
    if kind not in _SCORE_KINDS:
        raise ValueError("score.kind must be 'log' or 'other_proper'")
    name = _text(score.get("name"), name="score.name")
    orientation = _text(score.get("orientation"), name="score.orientation")
    if orientation != "higher_is_better":
        raise ValueError(
            "score.orientation must be 'higher_is_better'; transform lower-is-better losses before ODSP scoring"
        )
    common_rule = _bool(
        score.get("common_scoring_rule"), name="score.common_scoring_rule"
    )
    if not common_rule:
        raise ValueError(
            "score.common_scoring_rule must be true because all information levels must use the same scoring rule"
        )
    reference = score.get("common_reference_measure")
    if reference is not None and not isinstance(reference, bool):
        raise ValueError("score.common_reference_measure must be true, false, or null")
    if kind == "log" and reference is not True:
        raise ValueError(
            "log-score comparisons require score.common_reference_measure=true"
        )
    return {
        "kind": kind,
        "name": name,
        "orientation": orientation,
        "common_scoring_rule": True,
        "common_reference_measure": reference,
    }


def _validate_evaluation_contract(
    raw: object,
    *,
    block_declared: bool,
) -> dict[str, object]:
    evaluation = _mapping(raw, name="evaluation")
    _reject_unknown(evaluation, _EVALUATION_FIELDS, name="evaluation")
    mode = _text(evaluation.get("analysis_mode"), name="evaluation.analysis_mode")
    if mode not in _ANALYSIS_MODES:
        raise ValueError(
            "evaluation.analysis_mode must be 'confirmatory' or 'descriptive'"
        )
    heldout = _bool(
        evaluation.get("heldout_predictions"),
        name="evaluation.heldout_predictions",
    )
    if not heldout:
        raise ValueError("evaluation.heldout_predictions must be true")
    same_rows = _bool(
        evaluation.get("same_rows_across_levels"),
        name="evaluation.same_rows_across_levels",
    )
    if not same_rows:
        raise ValueError("evaluation.same_rows_across_levels must be true")
    no_outcome_leak = _bool(
        evaluation.get("heldout_outcome_not_used_for_prediction_or_selection"),
        name="evaluation.heldout_outcome_not_used_for_prediction_or_selection",
    )
    if not no_outcome_leak:
        raise ValueError(
            "evaluation.heldout_outcome_not_used_for_prediction_or_selection must be true"
        )
    frozen = _bool(
        evaluation.get("filtration_frozen_before_outcome_scoring"),
        name="evaluation.filtration_frozen_before_outcome_scoring",
    )
    if mode == "confirmatory" and not frozen:
        raise ValueError(
            "confirmatory analysis requires evaluation.filtration_frozen_before_outcome_scoring=true"
        )
    row_independence = _bool(
        evaluation.get("row_independence_if_no_block"),
        name="evaluation.row_independence_if_no_block",
    )
    if not block_declared and not row_independence:
        raise ValueError(
            "columns.block is null, so evaluation.row_independence_if_no_block must be true"
        )
    return {
        "analysis_mode": mode,
        "heldout_predictions": True,
        "same_rows_across_levels": True,
        "heldout_outcome_not_used_for_prediction_or_selection": True,
        "filtration_frozen_before_outcome_scoring": frozen,
        "row_independence_if_no_block": row_independence,
    }


def validate_information_transfer_contract(
    contract: Mapping[str, object],
) -> dict[str, object]:
    """Validate and normalize an external-score information-transfer contract."""

    contract = _mapping(contract, name="contract")
    _reject_unknown(contract, _TOP_LEVEL, name="contract")
    version = contract.get("schema_version")
    if isinstance(version, bool) or version != 1:
        raise ValueError("schema_version must be 1")

    endpoint_id = _text(contract.get("endpoint_id"), name="endpoint_id")

    data = _mapping(contract.get("data"), name="data")
    _reject_unknown(data, _DATA_FIELDS, name="data")
    data_path = _text(data.get("path"), name="data.path")
    data_format = _text(data.get("format"), name="data.format").lower()
    if data_format not in {"csv", "json"}:
        raise ValueError("data.format must be 'csv' or 'json'")

    columns = _mapping(contract.get("columns"), name="columns")
    _reject_unknown(columns, _COLUMN_FIELDS, name="columns")
    row_id = _text(columns.get("row_id"), name="columns.row_id")
    group = _text(columns.get("group"), name="columns.group")
    block_raw = columns.get("block")
    weight_raw = columns.get("weight")
    block = None if block_raw is None else _text(block_raw, name="columns.block")
    weight = None if weight_raw is None else _text(weight_raw, name="columns.weight")
    role_columns = [row_id, group] + [value for value in (block, weight) if value is not None]
    if len(set(role_columns)) != len(role_columns):
        raise ValueError("row_id, group, block and weight columns must be distinct")

    score = _validate_score_contract(contract.get("score"))
    evaluation = _validate_evaluation_contract(
        contract.get("evaluation"), block_declared=block is not None
    )

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
            InformationLevelScore(
                name=name,
                information=tuple(information),
                score=[0.0],
            )
        )
    if len(set(score_columns)) != len(score_columns):
        raise ValueError("levels.score_column values must be unique")
    collisions = sorted(set(score_columns) & set(role_columns))
    if collisions:
        raise ValueError(
            "score columns must be distinct from row-role columns: "
            + ", ".join(collisions)
        )
    validate_information_filtration(filtration_levels)

    certification = _mapping(contract.get("certification"), name="certification")
    _reject_unknown(certification, _CERTIFICATION_FIELDS, name="certification")
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
        "columns": {
            "row_id": row_id,
            "group": group,
            "block": block,
            "weight": weight,
        },
        "score": score,
        "evaluation": evaluation,
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
    elif data_format == "json":
        raw = json.loads(data_path.read_text(encoding="utf-8"))
        if not isinstance(raw, list) or not all(isinstance(row, Mapping) for row in raw):
            raise ValueError("JSON data must be an array of row objects")
        rows = [dict(row) for row in raw]
    else:  # pragma: no cover - schema validation prevents this branch.
        raise ValueError(f"unsupported data format: {data_format}")
    if not rows:
        raise ValueError("information-transfer data contains no rows")
    return rows


def _value(row: Mapping[str, object], column: str, *, row_index: int) -> object:
    if column not in row:
        raise ValueError(f"row {row_index} is missing declared column {column!r}")
    return row[column]


def _identifier(value: object, *, column: str, row_index: int) -> object:
    if value is None or value == "":
        raise ValueError(f"row {row_index} column {column!r} is missing")
    try:
        hash(value)
    except TypeError as exc:
        raise ValueError(f"row {row_index} column {column!r} must be hashable") from exc
    return value


def _score(value: object, *, column: str, row_index: int) -> float:
    if value is None or value == "":
        raise ValueError(f"row {row_index} score column {column!r} is missing")
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
    row_id_column = str(columns["row_id"])
    group_column = str(columns["group"])
    block_column = None if columns.get("block") is None else str(columns["block"])
    weight_column = None if columns.get("weight") is None else str(columns["weight"])

    row_ids: list[object] = []
    groups: list[object] = []
    blocks: list[object] | None = [] if block_column is not None else None
    weights: list[float] | None = [] if weight_column is not None else None
    level_specs = contract["levels"]
    assert isinstance(level_specs, list)
    level_scores: list[list[float]] = [[] for _ in level_specs]

    for row_index, row in enumerate(rows):
        row_ids.append(
            _identifier(
                _value(row, row_id_column, row_index=row_index),
                column=row_id_column,
                row_index=row_index,
            )
        )
        groups.append(
            _identifier(
                _value(row, group_column, row_index=row_index),
                column=group_column,
                row_index=row_index,
            )
        )
        if blocks is not None and block_column is not None:
            blocks.append(
                _identifier(
                    _value(row, block_column, row_index=row_index),
                    column=block_column,
                    row_index=row_index,
                )
            )
        if weights is not None and weight_column is not None:
            weights.append(
                _weight(
                    _value(row, weight_column, row_index=row_index),
                    column=weight_column,
                    row_index=row_index,
                )
            )
        for level_index, level in enumerate(level_specs):
            assert isinstance(level, Mapping)
            score_column = str(level["score_column"])
            level_scores[level_index].append(
                _score(
                    _value(row, score_column, row_index=row_index),
                    column=score_column,
                    row_index=row_index,
                )
            )

    if len(set(row_ids)) != len(row_ids):
        raise ValueError("columns.row_id must be unique for every held-out score row")

    score_spec = contract["score"]
    assert isinstance(score_spec, Mapping)
    information_levels = tuple(
        InformationLevelScore(
            name=str(level["name"]),
            information=tuple(str(value) for value in level["information"]),
            score=level_scores[index],
        )
        for index, level in enumerate(level_specs)
    )
    certification_spec = contract["certification"]
    assert isinstance(certification_spec, Mapping)
    point = decompose_information_transfer(
        information_levels,
        groups,
        score_name=str(score_spec["name"]),
        sample_weight=weights,
        gain_tolerance=float(certification_spec["gain_tolerance"]),
    )
    certified = certify_information_transfer(
        information_levels,
        groups,
        score_name=str(score_spec["name"]),
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

    evaluation = contract["evaluation"]
    assert isinstance(evaluation, Mapping)
    confirmatory_eligible = bool(
        evaluation["analysis_mode"] == "confirmatory"
        and evaluation["filtration_frozen_before_outcome_scoring"] is True
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
            "row_id": row_id_column,
            "independence_unit": group_column,
            "resampling_block": block_column,
            "row_weight": weight_column,
            "levels": level_specs,
            "certification": certification_spec,
        },
        "score_contract": score_spec,
        "evaluation_declarations": evaluation,
        "point_result": point.as_dict(),
        "certified_result": certified.as_dict(),
        "scientific_boundary": {
            "upstream_model_fitted_by_odsp": False,
            "upstream_model_refit_uncertainty_included": False,
            "score_columns_generated_by_odsp": False,
            "score_orientation_inferred": False,
            "information_sets_inferred": False,
            "independence_unit_inferred": False,
            "resampling_block_inferred": False,
            "strict_information_filtration_validated": True,
            "unique_heldout_row_ids_validated": True,
            "familywise_family_is_all_estimable_group_by_step_cells": True,
            "row_independence_assumed": block_column is None,
            "row_independence_explicitly_asserted": bool(
                block_column is None
                and evaluation["row_independence_if_no_block"] is True
            ),
            "confirmatory_eligible_from_contract_declarations": confirmatory_eligible,
            "contract_declarations_empirically_verified_by_odsp": False,
        },
    }
