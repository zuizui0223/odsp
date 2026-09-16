"""Generate a pre-outcome semantic freeze manifest for external validation.

The generator reads only an outcome-free external row roster plus an explicit
analysis plan.  It writes a non-overwriting manifest compatible with the v2
semantic-lock validator and returns a receipt containing content hashes.

The freeze timestamp is generated from the runtime UTC clock; the input schema
contains no field through which a caller can supply or backdate it.  ODSP does
not claim that the local system clock is an independently trusted timestamp
authority.
"""
from __future__ import annotations

from datetime import datetime, timezone
import hashlib
import json
import math
from pathlib import Path
from typing import Mapping

from .information_transfer import InformationLevelScore, validate_information_filtration
from .information_transfer_contract import (
    _mapping,
    _read_rows,
    _reject_unknown,
    _text,
    _validate_score_contract,
    _value,
)
from .untouched_external_refit_positive_contract_v2 import _row_roster_sha256


_PLAN_FIELDS = {
    "schema_version",
    "upstream_model_set_id",
    "external_dataset_id",
    "roster",
    "refit_ids",
    "reference_refit_id",
    "score",
    "levels",
    "certification",
}
_ROSTER_FIELDS = {"path", "format", "row_id_column"}
_LEVEL_FIELDS = {"name", "information"}
_CERT_FIELDS = {
    "alternative",
    "familywise_lower_confidence_level",
    "bootstrap_draws",
    "seed",
    "minimum_refits",
    "minimum_blocks_per_group",
    "gain_tolerance",
}


def _file_sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def _finite_number(value: object, *, name: str) -> float:
    if isinstance(value, bool):
        raise ValueError(f"{name} must be numeric")
    try:
        number = float(value)
    except (TypeError, ValueError) as exc:
        raise ValueError(f"{name} must be numeric") from exc
    if not math.isfinite(number):
        raise ValueError(f"{name} must be finite")
    return number


def _integer(value: object, *, name: str) -> int:
    if isinstance(value, bool) or not isinstance(value, int):
        raise ValueError(f"{name} must be an integer")
    return int(value)


def _string_array(value: object, *, name: str) -> tuple[str, ...]:
    if not isinstance(value, list) or not value:
        raise ValueError(f"{name} must be a non-empty JSON array")
    rows = tuple(_text(item, name=f"{name}[{index}]") for index, item in enumerate(value))
    if len(set(rows)) != len(rows):
        raise ValueError(f"{name} values must be unique")
    return rows


def validate_external_freeze_plan(plan: Mapping[str, object]) -> dict[str, object]:
    """Validate a plan that is safe to consume before external outcomes exist."""

    plan = _mapping(plan, name="freeze plan")
    _reject_unknown(plan, _PLAN_FIELDS, name="freeze plan")
    version = plan.get("schema_version")
    if isinstance(version, bool) or version != 1:
        raise ValueError("freeze plan schema_version must be 1")

    model_set_id = _text(plan.get("upstream_model_set_id"), name="upstream_model_set_id")
    dataset_id = _text(plan.get("external_dataset_id"), name="external_dataset_id")

    roster = _mapping(plan.get("roster"), name="roster")
    _reject_unknown(roster, _ROSTER_FIELDS, name="roster")
    roster_path = _text(roster.get("path"), name="roster.path")
    roster_format = _text(roster.get("format"), name="roster.format").lower()
    if roster_format not in {"csv", "json"}:
        raise ValueError("roster.format must be 'csv' or 'json'")
    row_id_column = _text(roster.get("row_id_column"), name="roster.row_id_column")

    refit_ids = tuple(sorted(_string_array(plan.get("refit_ids"), name="refit_ids")))
    reference_refit_id = _text(
        plan.get("reference_refit_id"), name="reference_refit_id"
    )
    if reference_refit_id not in refit_ids:
        raise ValueError("reference_refit_id must identify one frozen refit_id")

    score = _validate_score_contract(plan.get("score"))

    raw_levels = plan.get("levels")
    if not isinstance(raw_levels, list) or len(raw_levels) < 2:
        raise ValueError("levels must contain at least two information levels")
    levels: list[dict[str, object]] = []
    dummy: list[InformationLevelScore] = []
    for index, raw in enumerate(raw_levels):
        level = _mapping(raw, name=f"levels[{index}]")
        _reject_unknown(level, _LEVEL_FIELDS, name=f"levels[{index}]")
        name = _text(level.get("name"), name=f"levels[{index}].name")
        raw_information = level.get("information")
        if not isinstance(raw_information, list):
            raise ValueError(f"levels[{index}].information must be a JSON array")
        information = [
            _text(item, name=f"levels[{index}].information[{j}]")
            for j, item in enumerate(raw_information)
        ]
        if len(set(information)) != len(information):
            raise ValueError(f"levels[{index}].information values must be unique")
        levels.append({"name": name, "information": information})
        dummy.append(InformationLevelScore(name=name, information=tuple(information), score=[0.0]))
    validate_information_filtration(dummy)

    cert = _mapping(plan.get("certification"), name="certification")
    _reject_unknown(cert, _CERT_FIELDS, name="certification")
    alternative = _text(cert.get("alternative"), name="certification.alternative")
    if alternative != "greater":
        raise ValueError("certification.alternative must be 'greater'")
    confidence = _finite_number(
        cert.get("familywise_lower_confidence_level"),
        name="certification.familywise_lower_confidence_level",
    )
    if not 0.0 < confidence < 1.0:
        raise ValueError(
            "certification.familywise_lower_confidence_level must lie strictly between zero and one"
        )
    draws = _integer(cert.get("bootstrap_draws"), name="certification.bootstrap_draws")
    if draws < 500:
        raise ValueError("certification.bootstrap_draws must be >= 500")
    seed = _integer(cert.get("seed"), name="certification.seed")
    if seed < 0:
        raise ValueError("certification.seed must be non-negative")
    minimum_refits = _integer(cert.get("minimum_refits"), name="certification.minimum_refits")
    if minimum_refits < 2:
        raise ValueError("certification.minimum_refits must be >= 2")
    if len(refit_ids) < minimum_refits:
        raise ValueError("frozen refit_ids do not satisfy certification.minimum_refits")
    minimum_blocks = _integer(
        cert.get("minimum_blocks_per_group"), name="certification.minimum_blocks_per_group"
    )
    if minimum_blocks < 2:
        raise ValueError("certification.minimum_blocks_per_group must be >= 2")
    tolerance = _finite_number(cert.get("gain_tolerance"), name="certification.gain_tolerance")
    if tolerance < 0:
        raise ValueError("certification.gain_tolerance must be non-negative")

    return {
        "schema_version": 1,
        "upstream_model_set_id": model_set_id,
        "external_dataset_id": dataset_id,
        "roster": {
            "path": roster_path,
            "format": roster_format,
            "row_id_column": row_id_column,
        },
        "refit_ids": list(refit_ids),
        "reference_refit_id": reference_refit_id,
        "score": score,
        "levels": levels,
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


def load_external_freeze_plan(path: str | Path) -> dict[str, object]:
    plan_path = Path(path)
    try:
        raw = json.loads(plan_path.read_text(encoding="utf-8"))
    except json.JSONDecodeError as exc:
        raise ValueError(f"freeze plan is not valid JSON: {plan_path}") from exc
    return validate_external_freeze_plan(_mapping(raw, name="freeze plan"))


def create_external_freeze_manifest(
    plan_path: str | Path,
    manifest_out: str | Path,
) -> dict[str, object]:
    """Create a non-overwriting pre-outcome freeze manifest and return its receipt."""

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
        row_ids.append(_text(_value(row, row_id_column, row_index=index), name=f"row {index} row_id"))
    if len(set(row_ids)) != len(row_ids):
        raise ValueError("pre-outcome roster row IDs must be unique")

    frozen_at_utc = datetime.now(timezone.utc).replace(microsecond=0).isoformat().replace("+00:00", "Z")
    manifest = {
        "schema_version": 1,
        "manifest_type": "odsp_pre_external_outcome_freeze_v1",
        "frozen_at_utc": frozen_at_utc,
        "upstream_model_set_id": plan["upstream_model_set_id"],
        "external_dataset_id": plan["external_dataset_id"],
        "external_row_ids_sha256": _row_roster_sha256(row_ids),
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
        "receipt_type": "odsp_pre_external_outcome_freeze_receipt_v1",
        "manifest_path": str(output_path),
        "manifest_sha256": _file_sha256(output_path),
        "frozen_at_utc": frozen_at_utc,
        "freeze_plan_sha256": _file_sha256(plan_path),
        "roster_file_sha256": _file_sha256(roster_path),
        "external_row_ids_sha256": manifest["external_row_ids_sha256"],
        "external_row_count": len(row_ids),
        "upstream_model_set_id": plan["upstream_model_set_id"],
        "external_dataset_id": plan["external_dataset_id"],
        "refit_count": len(plan["refit_ids"]),
        "reference_refit_id": plan["reference_refit_id"],
        "boundaries": {
            "manifest_timestamp_generated_by_odsp_runtime_clock": True,
            "caller_supplied_freeze_timestamp_allowed": False,
            "manifest_overwrite_allowed": False,
            "roster_outcome_columns_allowed": False,
            "external_outcomes_read_by_freeze_generator": False,
            "runtime_clock_independently_attested": False,
            "trusted_timestamp_authority_used": False,
        },
    }
