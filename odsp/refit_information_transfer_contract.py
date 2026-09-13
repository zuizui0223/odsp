"""Executable long-table contracts for refit-aware information transfer.

The input repeats each held-out row once per upstream refit. ODSP verifies that
all refits contain exactly the same held-out row IDs and identical group, block
and weight metadata before constructing aligned [refit, row] score matrices.
No model fitting, refit generation or refit-scheme inference occurs here.
"""
from __future__ import annotations

import json
import math
from pathlib import Path
from typing import Mapping

from .information_transfer import InformationLevelScore, validate_information_filtration
from .information_transfer_contract import (
    _bool,
    _mapping,
    _read_rows,
    _reject_unknown,
    _required_float,
    _required_int,
    _score,
    _sha256,
    _text,
    _validate_score_contract,
    _value,
    _weight,
)
from .refit_information_transfer import (
    RefitInformationLevelScores,
    certify_refit_information_transfer,
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
_COLUMN_FIELDS = {"row_id", "refit_id", "group", "block", "weight"}
_LEVEL_FIELDS = {"name", "information", "score_column"}
_EVALUATION_FIELDS = {
    "analysis_mode",
    "heldout_predictions",
    "same_rows_across_levels",
    "same_rows_across_refits",
    "heldout_outcome_not_used_for_prediction_or_selection",
    "filtration_frozen_before_outcome_scoring",
    "refit_scheme_frozen_before_outcome_scoring",
    "refit_independence_assumed",
    "refit_mixture_weighting",
}
_CERTIFICATION_FIELDS = {
    "familywise_confidence_level",
    "nested_draws",
    "seed",
    "minimum_refits",
    "minimum_blocks_per_group",
    "gain_tolerance",
    "reference_refit_id",
}


def _id(value: object, *, name: str) -> str:
    if value is None:
        raise ValueError(f"{name} must be non-missing")
    text = str(value).strip()
    if not text:
        raise ValueError(f"{name} must be non-empty")
    return text


def _validate_evaluation(raw: object) -> dict[str, object]:
    value = _mapping(raw, name="evaluation")
    _reject_unknown(value, _EVALUATION_FIELDS, name="evaluation")
    mode = _text(value.get("analysis_mode"), name="evaluation.analysis_mode")
    if mode not in {"confirmatory", "descriptive"}:
        raise ValueError("evaluation.analysis_mode must be 'confirmatory' or 'descriptive'")
    required_true = (
        "heldout_predictions",
        "same_rows_across_levels",
        "same_rows_across_refits",
        "heldout_outcome_not_used_for_prediction_or_selection",
    )
    normalized: dict[str, object] = {"analysis_mode": mode}
    for field in required_true:
        flag = _bool(value.get(field), name=f"evaluation.{field}")
        if not flag:
            raise ValueError(f"evaluation.{field} must be true")
        normalized[field] = True
    frozen_filtration = _bool(
        value.get("filtration_frozen_before_outcome_scoring"),
        name="evaluation.filtration_frozen_before_outcome_scoring",
    )
    frozen_refits = _bool(
        value.get("refit_scheme_frozen_before_outcome_scoring"),
        name="evaluation.refit_scheme_frozen_before_outcome_scoring",
    )
    if mode == "confirmatory" and not (frozen_filtration and frozen_refits):
        raise ValueError(
            "confirmatory analysis requires both the information filtration and refit scheme to be frozen before outcome scoring"
        )
    independence = _bool(
        value.get("refit_independence_assumed"),
        name="evaluation.refit_independence_assumed",
    )
    if independence:
        raise ValueError(
            "evaluation.refit_independence_assumed must be false; ODSP treats supplied refits as an empirical sensitivity mixture"
        )
    weighting = _text(
        value.get("refit_mixture_weighting"),
        name="evaluation.refit_mixture_weighting",
    )
    if weighting != "uniform":
        raise ValueError("evaluation.refit_mixture_weighting must be 'uniform'")
    normalized.update(
        {
            "filtration_frozen_before_outcome_scoring": frozen_filtration,
            "refit_scheme_frozen_before_outcome_scoring": frozen_refits,
            "refit_independence_assumed": False,
            "refit_mixture_weighting": "uniform",
        }
    )
    return normalized


def validate_refit_information_transfer_contract(
    contract: Mapping[str, object],
) -> dict[str, object]:
    """Validate and normalize a long-form external refit-score contract."""

    contract = _mapping(contract, name="contract")
    _reject_unknown(contract, _TOP_LEVEL, name="contract")
    version = contract.get("schema_version")
    if isinstance(version, bool) or version != 1:
        raise ValueError("schema_version must be 1")
    endpoint_id = _text(contract.get("endpoint_id"), name="endpoint_id")

    data = _mapping(contract.get("data"), name="data")
    _reject_unknown(data, _DATA_FIELDS, name="data")
    path = _text(data.get("path"), name="data.path")
    fmt = _text(data.get("format"), name="data.format").lower()
    if fmt not in {"csv", "json"}:
        raise ValueError("data.format must be 'csv' or 'json'")

    columns = _mapping(contract.get("columns"), name="columns")
    _reject_unknown(columns, _COLUMN_FIELDS, name="columns")
    normalized_columns = {
        "row_id": _text(columns.get("row_id"), name="columns.row_id"),
        "refit_id": _text(columns.get("refit_id"), name="columns.refit_id"),
        "group": _text(columns.get("group"), name="columns.group"),
        "block": _text(columns.get("block"), name="columns.block"),
        "weight": None,
    }
    if columns.get("weight") is not None:
        normalized_columns["weight"] = _text(
            columns.get("weight"), name="columns.weight"
        )
    role_columns = [
        normalized_columns["row_id"],
        normalized_columns["refit_id"],
        normalized_columns["group"],
        normalized_columns["block"],
    ]
    if normalized_columns["weight"] is not None:
        role_columns.append(normalized_columns["weight"])
    if len(set(role_columns)) != len(role_columns):
        raise ValueError("row_id, refit_id, group, block and weight columns must be distinct")

    score = _validate_score_contract(contract.get("score"))
    evaluation = _validate_evaluation(contract.get("evaluation"))

    raw_levels = contract.get("levels")
    if not isinstance(raw_levels, list) or len(raw_levels) < 2:
        raise ValueError("levels must contain at least two information levels")
    levels: list[dict[str, object]] = []
    score_columns: list[str] = []
    dummy: list[InformationLevelScore] = []
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
            _text(item, name=f"levels[{index}].information[{j}]")
            for j, item in enumerate(raw_information)
        ]
        levels.append(
            {"name": name, "information": information, "score_column": score_column}
        )
        score_columns.append(score_column)
        dummy.append(
            InformationLevelScore(name=name, information=tuple(information), score=[0.0])
        )
    if len(set(score_columns)) != len(score_columns):
        raise ValueError("levels.score_column values must be unique")
    collision = sorted(set(score_columns) & set(role_columns))
    if collision:
        raise ValueError(
            "score columns must be distinct from row-role columns: " + ", ".join(collision)
        )
    validate_information_filtration(dummy)

    cert = _mapping(contract.get("certification"), name="certification")
    _reject_unknown(cert, _CERTIFICATION_FIELDS, name="certification")
    confidence = _required_float(
        cert.get("familywise_confidence_level"),
        name="certification.familywise_confidence_level",
    )
    if not math.isfinite(confidence) or not 0 < confidence < 1:
        raise ValueError(
            "certification.familywise_confidence_level must lie strictly between zero and one"
        )
    draws = _required_int(cert.get("nested_draws"), name="certification.nested_draws")
    if draws < 500:
        raise ValueError("certification.nested_draws must be >= 500")
    seed = _required_int(cert.get("seed"), name="certification.seed")
    minimum_refits = _required_int(
        cert.get("minimum_refits"), name="certification.minimum_refits"
    )
    if minimum_refits < 2:
        raise ValueError("certification.minimum_refits must be >= 2")
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
    reference_raw = cert.get("reference_refit_id")
    reference = None if reference_raw is None else _text(
        reference_raw, name="certification.reference_refit_id"
    )
    if evaluation["analysis_mode"] == "confirmatory" and reference is None:
        raise ValueError(
            "confirmatory refit analysis requires certification.reference_refit_id"
        )

    return {
        "schema_version": 1,
        "endpoint_id": endpoint_id,
        "data": {"path": path, "format": fmt},
        "columns": normalized_columns,
        "score": score,
        "evaluation": evaluation,
        "levels": levels,
        "certification": {
            "familywise_confidence_level": confidence,
            "nested_draws": draws,
            "seed": seed,
            "minimum_refits": minimum_refits,
            "minimum_blocks_per_group": minimum_blocks,
            "gain_tolerance": tolerance,
            "reference_refit_id": reference,
        },
    }


def load_refit_information_transfer_contract(path: str | Path) -> dict[str, object]:
    contract_path = Path(path)
    try:
        raw = json.loads(contract_path.read_text(encoding="utf-8"))
    except json.JSONDecodeError as exc:
        raise ValueError(f"contract is not valid JSON: {contract_path}") from exc
    return validate_refit_information_transfer_contract(_mapping(raw, name="contract"))


def run_refit_information_transfer_contract(path: str | Path) -> dict[str, object]:
    """Validate long-table refit alignment and run refit-aware certification."""

    contract_path = Path(path)
    contract = load_refit_information_transfer_contract(contract_path)
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
    row_id_col = str(columns["row_id"])
    refit_id_col = str(columns["refit_id"])
    group_col = str(columns["group"])
    block_col = str(columns["block"])
    weight_col = None if columns.get("weight") is None else str(columns["weight"])
    level_specs = contract["levels"]
    assert isinstance(level_specs, list)

    # refit -> row_id -> record. Duplicate pairs are forbidden.
    table: dict[str, dict[str, dict[str, object]]] = {}
    for row_index, row in enumerate(rows):
        refit_id = _id(_value(row, refit_id_col, row_index=row_index), name=f"row {row_index} refit_id")
        row_id = _id(_value(row, row_id_col, row_index=row_index), name=f"row {row_index} row_id")
        group = _id(_value(row, group_col, row_index=row_index), name=f"row {row_index} group")
        block = _id(_value(row, block_col, row_index=row_index), name=f"row {row_index} block")
        weight = 1.0 if weight_col is None else _weight(
            _value(row, weight_col, row_index=row_index),
            column=weight_col,
            row_index=row_index,
        )
        score_values: list[float] = []
        for level in level_specs:
            assert isinstance(level, Mapping)
            score_col = str(level["score_column"])
            score_values.append(
                _score(
                    _value(row, score_col, row_index=row_index),
                    column=score_col,
                    row_index=row_index,
                )
            )
        refit_rows = table.setdefault(refit_id, {})
        if row_id in refit_rows:
            raise ValueError(
                f"duplicate refit_id,row_id pair: ({refit_id!r}, {row_id!r})"
            )
        refit_rows[row_id] = {
            "group": group,
            "block": block,
            "weight": weight,
            "scores": score_values,
        }

    refit_ids = tuple(sorted(table))
    if not refit_ids:
        raise ValueError("refit score table contains no refits")
    canonical_rows = tuple(sorted(table[refit_ids[0]]))
    if not canonical_rows:
        raise ValueError("refit score table contains no held-out rows")
    canonical_set = set(canonical_rows)
    for refit_id in refit_ids[1:]:
        local = set(table[refit_id])
        if local != canonical_set:
            missing = sorted(canonical_set - local)
            extra = sorted(local - canonical_set)
            raise ValueError(
                f"refit {refit_id!r} does not contain the canonical held-out row set; missing={missing!r}, extra={extra!r}"
            )

    groups: list[str] = []
    blocks: list[str] = []
    weights: list[float] = []
    first = table[refit_ids[0]]
    for row_id in canonical_rows:
        record = first[row_id]
        groups.append(str(record["group"]))
        blocks.append(str(record["block"]))
        weights.append(float(record["weight"]))
    if not sum(weights) > 0:
        raise ValueError("held-out row weights must have positive total mass")

    # Metadata must be identical for the same held-out row in every refit.
    for refit_id in refit_ids[1:]:
        for row_index, row_id in enumerate(canonical_rows):
            record = table[refit_id][row_id]
            expected = (groups[row_index], blocks[row_index], weights[row_index])
            observed = (
                str(record["group"]),
                str(record["block"]),
                float(record["weight"]),
            )
            if observed != expected:
                raise ValueError(
                    f"held-out row metadata differs across refits for row_id {row_id!r}: expected={expected!r}, observed={observed!r}"
                )

    level_objects: list[RefitInformationLevelScores] = []
    for level_index, level in enumerate(level_specs):
        assert isinstance(level, Mapping)
        matrix = [
            [
                float(table[refit_id][row_id]["scores"][level_index])
                for row_id in canonical_rows
            ]
            for refit_id in refit_ids
        ]
        level_objects.append(
            RefitInformationLevelScores(
                name=str(level["name"]),
                information=tuple(str(value) for value in level["information"]),
                score=matrix,
            )
        )

    cert = contract["certification"]
    assert isinstance(cert, Mapping)
    score_spec = contract["score"]
    assert isinstance(score_spec, Mapping)
    result = certify_refit_information_transfer(
        level_objects,
        groups,
        blocks=blocks,
        refit_ids=refit_ids,
        reference_refit_id=cert.get("reference_refit_id"),
        score_name=str(score_spec["name"]),
        sample_weight=weights,
        familywise_confidence_level=float(cert["familywise_confidence_level"]),
        nested_draws=int(cert["nested_draws"]),
        seed=int(cert["seed"]),
        minimum_refits=int(cert["minimum_refits"]),
        minimum_blocks_per_group=int(cert["minimum_blocks_per_group"]),
        gain_tolerance=float(cert["gain_tolerance"]),
    )

    evaluation = contract["evaluation"]
    assert isinstance(evaluation, Mapping)
    confirmatory = bool(
        evaluation["analysis_mode"] == "confirmatory"
        and evaluation["filtration_frozen_before_outcome_scoring"] is True
        and evaluation["refit_scheme_frozen_before_outcome_scoring"] is True
    )
    return {
        "schema_version": 1,
        "receipt_type": "odsp_refit_information_transfer_endpoint",
        "endpoint_id": contract["endpoint_id"],
        "contract_sha256": _sha256(contract_path),
        "data_sha256": _sha256(data_path),
        "data_path_declared": data_spec["path"],
        "data_format": data_spec["format"],
        "input_long_row_count": len(rows),
        "refit_count": len(refit_ids),
        "heldout_row_count_per_refit": len(canonical_rows),
        "score_contract": score_spec,
        "evaluation_declarations": evaluation,
        "scientific_roles": {
            "row_id": row_id_col,
            "refit_id": refit_id_col,
            "independence_unit": group_col,
            "resampling_block": block_col,
            "row_weight": weight_col,
            "levels": level_specs,
            "certification": cert,
        },
        "result": result.as_dict(),
        "scientific_boundary": {
            "upstream_model_fitted_by_odsp": False,
            "refit_scheme_inferred_by_odsp": False,
            "refit_independence_assumed": False,
            "refit_mixture_weighting": "uniform",
            "same_heldout_row_set_across_refits_validated": True,
            "same_group_block_weight_metadata_across_refits_validated": True,
            "duplicate_refit_row_pairs_rejected": True,
            "strict_information_filtration_validated": True,
            "reference_fit_can_override_refit_aware_failure": False,
            "confirmatory_eligible_from_contract_declarations": confirmatory,
            "contract_declarations_empirically_verified_by_odsp": False,
        },
    }
