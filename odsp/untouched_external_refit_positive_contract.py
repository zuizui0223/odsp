"""Executable untouched-external validation contract for refit-sensitive positive transfer.

This route is intentionally stricter than ordinary held-out scoring.  It requires
a concrete pre-outcome freeze artifact, verifies that artifact by SHA256, validates
that its timestamp precedes first external-outcome access, and records explicit
no-use declarations for the external rows/outcomes.

ODSP can verify contract consistency, hashes, timestamps and row/refit alignment.
It cannot independently prove a researcher's historical claim that an outcome was
never viewed before the declared access time; receipts state that boundary.
"""
from __future__ import annotations

from datetime import datetime, timedelta
import hashlib
import json
import math
from pathlib import Path
import re
from typing import Mapping

import numpy as np

from .information_transfer import InformationLevelScore, validate_information_filtration
from .information_transfer_contract import (
    _bool,
    _mapping,
    _read_rows,
    _reject_unknown,
    _required_float,
    _required_int,
    _score,
    _text,
    _validate_score_contract,
    _value,
    _weight,
)
from .refit_information_transfer import RefitInformationLevelScores
from .refit_positive_information_transfer import (
    certify_refit_positive_information_transfer,
)


_TOP_LEVEL = {
    "schema_version",
    "endpoint_id",
    "data",
    "columns",
    "score",
    "external_validation",
    "levels",
    "certification",
}
_DATA_FIELDS = {"path", "format"}
_COLUMN_FIELDS = {"row_id", "refit_id", "group", "block", "weight"}
_LEVEL_FIELDS = {"name", "information", "score_column"}
_FREEZE_FIELDS = {"path", "sha256", "frozen_at_utc"}
_EXTERNAL_FIELDS = {
    "dataset_role",
    "freeze_manifest",
    "external_outcomes_first_accessed_at_utc",
    "development_data_disjoint",
    "external_rows_used_for_upstream_fit",
    "external_rows_used_for_refit_generation",
    "external_rows_used_for_model_selection",
    "external_rows_used_for_filtration_selection",
    "external_outcomes_used_for_threshold_selection",
    "external_outcomes_used_for_score_rule_selection",
    "external_outcomes_used_for_any_development_decision",
    "models_frozen_before_external_outcome_access",
    "refit_ensemble_frozen_before_external_outcome_access",
    "filtration_frozen_before_external_outcome_access",
    "score_rule_frozen_before_external_outcome_access",
    "gain_tolerance_frozen_before_external_outcome_access",
    "alternative_frozen_before_external_outcome_access",
}
_CERT_FIELDS = {
    "alternative",
    "familywise_lower_confidence_level",
    "bootstrap_draws",
    "seed",
    "minimum_refits",
    "minimum_blocks_per_group",
    "gain_tolerance",
    "reference_refit_id",
}
_SHA256_RE = re.compile(r"^[0-9a-f]{64}$")


def _file_sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def _utc_timestamp(value: object, *, name: str) -> tuple[str, datetime]:
    text = _text(value, name=name)
    parse_text = text[:-1] + "+00:00" if text.endswith("Z") else text
    try:
        stamp = datetime.fromisoformat(parse_text)
    except ValueError as exc:
        raise ValueError(f"{name} must be an ISO-8601 UTC timestamp") from exc
    if stamp.tzinfo is None or stamp.utcoffset() != timedelta(0):
        raise ValueError(f"{name} must include an explicit UTC offset")
    normalized = stamp.astimezone().isoformat()
    # astimezone() uses the runner timezone; preserve UTC explicitly instead.
    normalized = stamp.isoformat().replace("+00:00", "Z")
    return normalized, stamp


def _must_true(value: Mapping[str, object], field: str) -> bool:
    flag = _bool(value.get(field), name=f"external_validation.{field}")
    if not flag:
        raise ValueError(f"external_validation.{field} must be true")
    return True


def _must_false(value: Mapping[str, object], field: str) -> bool:
    flag = _bool(value.get(field), name=f"external_validation.{field}")
    if flag:
        raise ValueError(f"external_validation.{field} must be false")
    return False


def _validate_external_validation(raw: object) -> dict[str, object]:
    value = _mapping(raw, name="external_validation")
    _reject_unknown(value, _EXTERNAL_FIELDS, name="external_validation")
    role = _text(value.get("dataset_role"), name="external_validation.dataset_role")
    if role != "untouched_external_validation":
        raise ValueError(
            "external_validation.dataset_role must be 'untouched_external_validation'"
        )

    freeze = _mapping(value.get("freeze_manifest"), name="external_validation.freeze_manifest")
    _reject_unknown(freeze, _FREEZE_FIELDS, name="external_validation.freeze_manifest")
    freeze_path = _text(freeze.get("path"), name="external_validation.freeze_manifest.path")
    freeze_sha = _text(
        freeze.get("sha256"), name="external_validation.freeze_manifest.sha256"
    ).lower()
    if _SHA256_RE.fullmatch(freeze_sha) is None:
        raise ValueError("external_validation.freeze_manifest.sha256 must be 64 lowercase hex characters")
    frozen_text, frozen_at = _utc_timestamp(
        freeze.get("frozen_at_utc"),
        name="external_validation.freeze_manifest.frozen_at_utc",
    )
    access_text, first_access = _utc_timestamp(
        value.get("external_outcomes_first_accessed_at_utc"),
        name="external_validation.external_outcomes_first_accessed_at_utc",
    )
    if not frozen_at < first_access:
        raise ValueError(
            "freeze manifest must predate first external-outcome access"
        )

    normalized: dict[str, object] = {
        "dataset_role": role,
        "freeze_manifest": {
            "path": freeze_path,
            "sha256": freeze_sha,
            "frozen_at_utc": frozen_text,
        },
        "external_outcomes_first_accessed_at_utc": access_text,
    }
    for field in (
        "development_data_disjoint",
        "models_frozen_before_external_outcome_access",
        "refit_ensemble_frozen_before_external_outcome_access",
        "filtration_frozen_before_external_outcome_access",
        "score_rule_frozen_before_external_outcome_access",
        "gain_tolerance_frozen_before_external_outcome_access",
        "alternative_frozen_before_external_outcome_access",
    ):
        normalized[field] = _must_true(value, field)
    for field in (
        "external_rows_used_for_upstream_fit",
        "external_rows_used_for_refit_generation",
        "external_rows_used_for_model_selection",
        "external_rows_used_for_filtration_selection",
        "external_outcomes_used_for_threshold_selection",
        "external_outcomes_used_for_score_rule_selection",
        "external_outcomes_used_for_any_development_decision",
    ):
        normalized[field] = _must_false(value, field)
    return normalized


def validate_untouched_external_refit_positive_contract(
    contract: Mapping[str, object],
) -> dict[str, object]:
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
    normalized_columns = {
        "row_id": _text(columns.get("row_id"), name="columns.row_id"),
        "refit_id": _text(columns.get("refit_id"), name="columns.refit_id"),
        "group": _text(columns.get("group"), name="columns.group"),
        "block": _text(columns.get("block"), name="columns.block"),
        "weight": None,
    }
    if columns.get("weight") is not None:
        normalized_columns["weight"] = _text(columns.get("weight"), name="columns.weight")
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
    external = _validate_external_validation(contract.get("external_validation"))

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
        score_column = _text(level.get("score_column"), name=f"levels[{index}].score_column")
        raw_information = level.get("information")
        if not isinstance(raw_information, list):
            raise ValueError(f"levels[{index}].information must be a JSON array")
        information = [
            _text(item, name=f"levels[{index}].information[{j}]")
            for j, item in enumerate(raw_information)
        ]
        levels.append({"name": name, "information": information, "score_column": score_column})
        score_columns.append(score_column)
        dummy.append(InformationLevelScore(name=name, information=tuple(information), score=[0.0]))
    if len(set(score_columns)) != len(score_columns):
        raise ValueError("levels.score_column values must be unique")
    collision = sorted(set(score_columns) & set(role_columns))
    if collision:
        raise ValueError(
            "score columns must be distinct from row-role columns: " + ", ".join(collision)
        )
    validate_information_filtration(dummy)

    cert = _mapping(contract.get("certification"), name="certification")
    _reject_unknown(cert, _CERT_FIELDS, name="certification")
    alternative = _text(cert.get("alternative"), name="certification.alternative")
    if alternative != "greater":
        raise ValueError("certification.alternative must be 'greater'")
    confidence = _required_float(
        cert.get("familywise_lower_confidence_level"),
        name="certification.familywise_lower_confidence_level",
    )
    if not math.isfinite(confidence) or not 0 < confidence < 1:
        raise ValueError("certification.familywise_lower_confidence_level must lie strictly between zero and one")
    draws = _required_int(cert.get("bootstrap_draws"), name="certification.bootstrap_draws")
    if draws < 500:
        raise ValueError("certification.bootstrap_draws must be >= 500")
    seed = _required_int(cert.get("seed"), name="certification.seed")
    minimum_refits = _required_int(cert.get("minimum_refits"), name="certification.minimum_refits")
    if minimum_refits < 2:
        raise ValueError("certification.minimum_refits must be >= 2")
    minimum_blocks = _required_int(
        cert.get("minimum_blocks_per_group"), name="certification.minimum_blocks_per_group"
    )
    if minimum_blocks < 2:
        raise ValueError("certification.minimum_blocks_per_group must be >= 2")
    tolerance = _required_float(cert.get("gain_tolerance"), name="certification.gain_tolerance")
    if not math.isfinite(tolerance) or tolerance < 0:
        raise ValueError("certification.gain_tolerance must be finite and non-negative")
    reference = _text(cert.get("reference_refit_id"), name="certification.reference_refit_id")

    return {
        "schema_version": 1,
        "endpoint_id": endpoint_id,
        "data": {"path": data_path, "format": data_format},
        "columns": normalized_columns,
        "score": score,
        "external_validation": external,
        "levels": levels,
        "certification": {
            "alternative": "greater",
            "familywise_lower_confidence_level": confidence,
            "bootstrap_draws": draws,
            "seed": seed,
            "minimum_refits": minimum_refits,
            "minimum_blocks_per_group": minimum_blocks,
            "gain_tolerance": tolerance,
            "reference_refit_id": reference,
        },
    }


def load_untouched_external_refit_positive_contract(path: str | Path) -> dict[str, object]:
    contract_path = Path(path)
    try:
        raw = json.loads(contract_path.read_text(encoding="utf-8"))
    except json.JSONDecodeError as exc:
        raise ValueError(f"contract is not valid JSON: {contract_path}") from exc
    return validate_untouched_external_refit_positive_contract(_mapping(raw, name="contract"))


def _identifier(value: object, *, name: str) -> str:
    if value is None:
        raise ValueError(f"{name} is missing")
    text = str(value).strip()
    if not text:
        raise ValueError(f"{name} is missing")
    return text


def run_untouched_external_refit_positive_contract(path: str | Path) -> dict[str, object]:
    contract_path = Path(path)
    contract = load_untouched_external_refit_positive_contract(contract_path)

    data_spec = contract["data"]
    assert isinstance(data_spec, Mapping)
    data_path = Path(str(data_spec["path"]))
    if not data_path.is_absolute():
        data_path = contract_path.parent / data_path
    if not data_path.is_file():
        raise FileNotFoundError(data_path)

    external = contract["external_validation"]
    assert isinstance(external, Mapping)
    freeze_spec = external["freeze_manifest"]
    assert isinstance(freeze_spec, Mapping)
    freeze_path = Path(str(freeze_spec["path"]))
    if not freeze_path.is_absolute():
        freeze_path = contract_path.parent / freeze_path
    if not freeze_path.is_file():
        raise FileNotFoundError(freeze_path)
    actual_freeze_sha = _file_sha256(freeze_path)
    declared_freeze_sha = str(freeze_spec["sha256"])
    if actual_freeze_sha != declared_freeze_sha:
        raise ValueError(
            "freeze manifest SHA256 does not match the declared pre-outcome artifact"
        )

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

    table: dict[str, dict[str, dict[str, object]]] = {}
    for row_index, row in enumerate(rows):
        refit_id = _identifier(_value(row, refit_id_col, row_index=row_index), name=f"row {row_index} refit_id")
        row_id = _identifier(_value(row, row_id_col, row_index=row_index), name=f"row {row_index} row_id")
        group = _identifier(_value(row, group_col, row_index=row_index), name=f"row {row_index} group")
        block = _identifier(_value(row, block_col, row_index=row_index), name=f"row {row_index} block")
        weight = 1.0 if weight_col is None else _weight(
            _value(row, weight_col, row_index=row_index), column=weight_col, row_index=row_index
        )
        scores: list[float] = []
        for level in level_specs:
            assert isinstance(level, Mapping)
            score_col = str(level["score_column"])
            scores.append(_score(_value(row, score_col, row_index=row_index), column=score_col, row_index=row_index))
        local = table.setdefault(refit_id, {})
        if row_id in local:
            raise ValueError(f"duplicate refit_id,row_id pair: ({refit_id!r}, {row_id!r})")
        local[row_id] = {"group": group, "block": block, "weight": weight, "scores": scores}

    refit_ids = tuple(sorted(table))
    if not refit_ids:
        raise ValueError("external refit score table contains no refits")
    canonical_rows = tuple(sorted(table[refit_ids[0]]))
    if not canonical_rows:
        raise ValueError("external refit score table contains no held-out rows")
    canonical_set = set(canonical_rows)
    for refit_id in refit_ids[1:]:
        local_set = set(table[refit_id])
        if local_set != canonical_set:
            missing = sorted(canonical_set - local_set)
            extra = sorted(local_set - canonical_set)
            raise ValueError(
                f"refit {refit_id!r} does not contain the canonical external row set; missing={missing!r}, extra={extra!r}"
            )

    first = table[refit_ids[0]]
    groups: list[str] = []
    blocks: list[str] = []
    weights: list[float] = []
    for row_id in canonical_rows:
        record = first[row_id]
        groups.append(str(record["group"]))
        blocks.append(str(record["block"]))
        weights.append(float(record["weight"]))
    if not sum(weights) > 0:
        raise ValueError("external row weights must have positive total mass")

    for refit_id in refit_ids[1:]:
        for row_index, row_id in enumerate(canonical_rows):
            record = table[refit_id][row_id]
            expected = (groups[row_index], blocks[row_index], weights[row_index])
            observed = (str(record["group"]), str(record["block"]), float(record["weight"]))
            if observed != expected:
                raise ValueError(
                    f"external row metadata differs across refits for row_id {row_id!r}"
                )

    refit_levels: list[RefitInformationLevelScores] = []
    for level_index, level in enumerate(level_specs):
        assert isinstance(level, Mapping)
        matrix = np.asarray(
            [
                [float(table[refit_id][row_id]["scores"][level_index]) for row_id in canonical_rows]
                for refit_id in refit_ids
            ],
            dtype=float,
        )
        refit_levels.append(
            RefitInformationLevelScores(
                name=str(level["name"]),
                information=tuple(str(item) for item in level["information"]),
                score=matrix,
            )
        )

    cert = contract["certification"]
    assert isinstance(cert, Mapping)
    result = certify_refit_positive_information_transfer(
        refit_levels,
        groups,
        blocks=blocks,
        refit_ids=refit_ids,
        reference_refit_id=str(cert["reference_refit_id"]),
        score_name=str(contract["score"]["name"]),
        sample_weight=weights,
        familywise_lower_confidence_level=float(cert["familywise_lower_confidence_level"]),
        bootstrap_draws=int(cert["bootstrap_draws"]),
        seed=int(cert["seed"]),
        minimum_refits=int(cert["minimum_refits"]),
        minimum_blocks_per_group=int(cert["minimum_blocks_per_group"]),
        gain_tolerance=float(cert["gain_tolerance"]),
    )

    return {
        "receipt_type": "odsp_untouched_external_refit_positive_validation_endpoint",
        "endpoint_id": contract["endpoint_id"],
        "contract_sha256": _file_sha256(contract_path),
        "data_sha256": _file_sha256(data_path),
        "freeze_manifest_sha256": actual_freeze_sha,
        "input_long_row_count": len(rows),
        "refit_count": len(refit_ids),
        "external_heldout_row_count": len(canonical_rows),
        "external_validation": external,
        "scientific_roles": {
            "alternative": "greater",
            "dataset_role": "untouched_external_validation",
            "refit_uncertainty_role": "empirical_sensitivity_intersection",
            "validation_uncertainty_role": "one_sided_familywise_bootstrap_t_within_refit",
        },
        "result": result.as_dict(),
        "boundaries": {
            "untouched_external_validation_contract_satisfied": True,
            "freeze_manifest_hash_verified": True,
            "freeze_timestamp_precedes_declared_first_outcome_access": True,
            "upstream_model_fitted_by_odsp": False,
            "upstream_refits_generated_by_odsp": False,
            "refit_ensemble_probability_sample_assumed": False,
            "population_refit_confidence_claimed": False,
            "historical_no_prior_outcome_access_independently_proven_by_odsp": False,
            "development_data_disjointness_independently_proven_by_odsp": False,
            "provenance_declarations_are_user_supplied": True,
        },
    }
