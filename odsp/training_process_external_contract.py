"""Contract wrapper for the qualified training-process v5 untouched-external endpoint.

This module is operational glue only. It does not define a new statistical
method or evidence route. The contract supplies file locations and the declared
first external-outcome access time; row/group/block/weight vectors and frozen
refit IDs are reconstructed from already-frozen artifacts before the canonical
endpoint is called.
"""
from __future__ import annotations

import json
from pathlib import Path
from typing import Mapping

from .information_transfer_contract import _read_rows
from .training_process_external_freeze_v1 import _external_design_rows
from .training_process_untouched_external_v5 import (
    run_untouched_external_training_process_v5,
)


_CONTRACT_FIELDS = {
    "schema_version",
    "external_freeze_manifest_path",
    "external_freeze_receipt_path",
    "managed_scoring_receipt_path",
    "score_bundle_path",
    "validation_data_path",
    "external_roster",
    "training_process_manifest_path",
    "managed_generation_receipt_path",
    "training_roster_path",
    "external_outcomes_first_accessed_at_utc",
}
_ROSTER_FIELDS = {"path", "format"}


def _text(value: object, *, name: str) -> str:
    if not isinstance(value, str) or not value.strip():
        raise ValueError(f"{name} must be non-empty text")
    return value.strip()


def _load_json(path: Path, *, name: str) -> dict[str, object]:
    try:
        value = json.loads(path.read_text(encoding="utf-8"))
    except json.JSONDecodeError as exc:
        raise ValueError(f"{name} is not valid JSON: {path}") from exc
    if not isinstance(value, Mapping):
        raise ValueError(f"{name} must contain a JSON object")
    return dict(value)


def _resolve(base: Path, value: object, *, name: str) -> Path:
    raw = Path(_text(value, name=name))
    return raw if raw.is_absolute() else base / raw


def _validate_contract(raw: Mapping[str, object]) -> dict[str, object]:
    contract = dict(raw)
    if set(contract) != _CONTRACT_FIELDS:
        raise ValueError(
            "training-process external contract fields mismatch: "
            f"missing={sorted(_CONTRACT_FIELDS-set(contract))!r}, "
            f"unknown={sorted(set(contract)-_CONTRACT_FIELDS)!r}"
        )
    if contract.get("schema_version") != 1 or isinstance(
        contract.get("schema_version"), bool
    ):
        raise ValueError("training-process external contract schema_version must be 1")

    roster = contract.get("external_roster")
    if not isinstance(roster, Mapping) or set(roster) != _ROSTER_FIELDS:
        raise ValueError("external_roster fields must be exactly path and format")
    format_name = _text(roster.get("format"), name="external_roster.format").lower()
    if format_name not in {"csv", "json"}:
        raise ValueError("external_roster.format must be csv or json")

    normalized = {
        key: contract[key]
        for key in _CONTRACT_FIELDS
        if key not in {"schema_version", "external_roster"}
    }
    for key in normalized:
        normalized[key] = _text(normalized[key], name=key)

    return {
        "schema_version": 1,
        **normalized,
        "external_roster": {
            "path": _text(roster.get("path"), name="external_roster.path"),
            "format": format_name,
        },
    }


def run_training_process_v5_external_contract(
    contract_path: str | Path,
) -> dict[str, object]:
    """Run the canonical untouched-external v5 endpoint from one file contract."""

    contract_path = Path(contract_path)
    contract = _validate_contract(
        _load_json(contract_path, name="training-process external contract")
    )
    base = contract_path.parent

    roster_spec = contract["external_roster"]
    assert isinstance(roster_spec, Mapping)
    roster_path = _resolve(
        base, roster_spec["path"], name="external_roster.path"
    )
    if not roster_path.is_file():
        raise FileNotFoundError(roster_path)
    raw_rows = _read_rows(roster_path, str(roster_spec["format"]))
    design_rows, _ = _external_design_rows(raw_rows)

    freeze_manifest_path = _resolve(
        base,
        contract["external_freeze_manifest_path"],
        name="external_freeze_manifest_path",
    )
    freeze_manifest = _load_json(
        freeze_manifest_path, name="external freeze manifest"
    )
    refit_ids_raw = freeze_manifest.get("refit_ids")
    if not isinstance(refit_ids_raw, list) or not refit_ids_raw:
        raise ValueError("external freeze manifest refit_ids must be non-empty")
    refit_ids = tuple(
        _text(value, name=f"external freeze refit_ids[{index}]")
        for index, value in enumerate(refit_ids_raw)
    )
    if len(refit_ids) != len(set(refit_ids)):
        raise ValueError("external freeze manifest refit_ids must be unique")

    result = run_untouched_external_training_process_v5(
        freeze_manifest_path,
        _resolve(
            base,
            contract["external_freeze_receipt_path"],
            name="external_freeze_receipt_path",
        ),
        _resolve(
            base,
            contract["managed_scoring_receipt_path"],
            name="managed_scoring_receipt_path",
        ),
        _resolve(base, contract["score_bundle_path"], name="score_bundle_path"),
        _resolve(
            base,
            contract["validation_data_path"],
            name="validation_data_path",
        ),
        tuple(row["group_id"] for row in design_rows),
        blocks=tuple(row["block_id"] for row in design_rows),
        validation_row_ids=tuple(row["row_id"] for row in design_rows),
        sample_weight=tuple(float(row["sample_weight"]) for row in design_rows),
        refit_ids=refit_ids,
        training_process_manifest_path=_resolve(
            base,
            contract["training_process_manifest_path"],
            name="training_process_manifest_path",
        ),
        managed_generation_receipt_path=_resolve(
            base,
            contract["managed_generation_receipt_path"],
            name="managed_generation_receipt_path",
        ),
        training_roster_path=_resolve(
            base,
            contract["training_roster_path"],
            name="training_roster_path",
        ),
        external_outcomes_first_accessed_at_utc=contract[
            "external_outcomes_first_accessed_at_utc"
        ],
    )
    return result.as_dict()
