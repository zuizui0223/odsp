"""Semantically locked untouched-external validation contract.

Version 1 verifies that a pre-outcome freeze artifact exists, matches its declared
SHA256 and predates external-outcome access.  This v2 wrapper additionally proves
that the *contents* of that frozen artifact describe the analysis actually run:
external row roster, upstream refit IDs, reference refit, score semantics,
information filtration and every inferential setting must match exactly.

The semantic lock prevents a valid old freeze artifact from being reused for a
post-outcome-changed analysis.  Historical non-access and development-data
disjointness remain provenance declarations rather than facts ODSP can observe.
"""
from __future__ import annotations

import hashlib
import json
import math
from pathlib import Path
from typing import Mapping, Sequence

from .frozen_confirmatory_route import verify_frozen_confirmatory_route
from .information_transfer_contract import _mapping, _reject_unknown, _text
from .untouched_external_refit_positive_contract import (
    _file_sha256,
    _read_rows,
    _value,
    load_untouched_external_refit_positive_contract,
    run_untouched_external_refit_positive_contract,
)


_MANIFEST_FIELDS = {
    "schema_version",
    "manifest_type",
    "frozen_at_utc",
    "upstream_model_set_id",
    "external_dataset_id",
    "external_row_ids_sha256",
    "confirmatory_route",
    "refit_ids",
    "reference_refit_id",
    "score",
    "levels",
    "certification",
}
_MANIFEST_SCORE_FIELDS = {
    "kind",
    "name",
    "orientation",
    "common_scoring_rule",
    "common_reference_measure",
}
_MANIFEST_LEVEL_FIELDS = {"name", "information"}
_MANIFEST_CERT_FIELDS = {
    "alternative",
    "familywise_lower_confidence_level",
    "bootstrap_draws",
    "seed",
    "minimum_refits",
    "minimum_blocks_per_group",
    "gain_tolerance",
}


def _row_roster_sha256(row_ids: Sequence[str]) -> str:
    canonical = "\n".join(sorted(row_ids)) + "\n"
    return hashlib.sha256(canonical.encode("utf-8")).hexdigest()


def _number(value: object, *, name: str) -> float:
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


def _string_list(value: object, *, name: str, allow_empty: bool = False) -> tuple[str, ...]:
    if not isinstance(value, list):
        raise ValueError(f"{name} must be a JSON array")
    rows = tuple(_text(item, name=f"{name}[{index}]") for index, item in enumerate(value))
    if not allow_empty and not rows:
        raise ValueError(f"{name} must not be empty")
    if len(set(rows)) != len(rows):
        raise ValueError(f"{name} values must be unique")
    return rows


def _load_manifest(path: Path) -> Mapping[str, object]:
    try:
        raw = json.loads(path.read_text(encoding="utf-8"))
    except json.JSONDecodeError as exc:
        raise ValueError("freeze manifest must be valid JSON") from exc
    manifest = _mapping(raw, name="freeze manifest")
    _reject_unknown(manifest, _MANIFEST_FIELDS, name="freeze manifest")
    if manifest.get("schema_version") != 1 or isinstance(manifest.get("schema_version"), bool):
        raise ValueError("freeze manifest schema_version must be 1")
    if _text(manifest.get("manifest_type"), name="freeze manifest.manifest_type") != "odsp_pre_external_outcome_freeze_v1":
        raise ValueError(
            "freeze manifest.manifest_type must be 'odsp_pre_external_outcome_freeze_v1'"
        )
    return manifest


def _normalize_manifest_score(raw: object) -> dict[str, object]:
    score = _mapping(raw, name="freeze manifest.score")
    _reject_unknown(score, _MANIFEST_SCORE_FIELDS, name="freeze manifest.score")
    common_rule = score.get("common_scoring_rule")
    reference = score.get("common_reference_measure")
    if not isinstance(common_rule, bool) or not isinstance(reference, bool):
        raise ValueError(
            "freeze manifest.score common_scoring_rule and common_reference_measure must be booleans"
        )
    return {
        "kind": _text(score.get("kind"), name="freeze manifest.score.kind"),
        "name": _text(score.get("name"), name="freeze manifest.score.name"),
        "orientation": _text(score.get("orientation"), name="freeze manifest.score.orientation"),
        "common_scoring_rule": common_rule,
        "common_reference_measure": reference,
    }


def _normalize_manifest_levels(raw: object) -> list[dict[str, object]]:
    if not isinstance(raw, list) or len(raw) < 2:
        raise ValueError("freeze manifest.levels must contain at least two levels")
    rows: list[dict[str, object]] = []
    for index, item in enumerate(raw):
        level = _mapping(item, name=f"freeze manifest.levels[{index}]")
        _reject_unknown(level, _MANIFEST_LEVEL_FIELDS, name=f"freeze manifest.levels[{index}]")
        info_raw = level.get("information")
        if not isinstance(info_raw, list):
            raise ValueError(
                f"freeze manifest.levels[{index}].information must be a JSON array"
            )
        information = [
            _text(value, name=f"freeze manifest.levels[{index}].information[{j}]")
            for j, value in enumerate(info_raw)
        ]
        if len(set(information)) != len(information):
            raise ValueError(
                f"freeze manifest.levels[{index}].information values must be unique"
            )
        rows.append(
            {
                "name": _text(level.get("name"), name=f"freeze manifest.levels[{index}].name"),
                "information": information,
            }
        )
    return rows


def _normalize_manifest_certification(raw: object) -> dict[str, object]:
    cert = _mapping(raw, name="freeze manifest.certification")
    _reject_unknown(cert, _MANIFEST_CERT_FIELDS, name="freeze manifest.certification")
    return {
        "alternative": _text(cert.get("alternative"), name="freeze manifest.certification.alternative"),
        "familywise_lower_confidence_level": _number(
            cert.get("familywise_lower_confidence_level"),
            name="freeze manifest.certification.familywise_lower_confidence_level",
        ),
        "bootstrap_draws": _integer(
            cert.get("bootstrap_draws"), name="freeze manifest.certification.bootstrap_draws"
        ),
        "seed": _integer(cert.get("seed"), name="freeze manifest.certification.seed"),
        "minimum_refits": _integer(
            cert.get("minimum_refits"), name="freeze manifest.certification.minimum_refits"
        ),
        "minimum_blocks_per_group": _integer(
            cert.get("minimum_blocks_per_group"),
            name="freeze manifest.certification.minimum_blocks_per_group",
        ),
        "gain_tolerance": _number(
            cert.get("gain_tolerance"), name="freeze manifest.certification.gain_tolerance"
        ),
    }


def _assert_equal(actual: object, expected: object, *, field: str) -> None:
    if actual != expected:
        raise ValueError(
            f"freeze manifest semantic mismatch for {field}: frozen={actual!r}, runtime={expected!r}"
        )


def verify_freeze_manifest_semantic_lock(
    contract_path: str | Path,
) -> dict[str, object]:
    """Verify the hashed freeze artifact describes the exact runtime analysis."""

    contract_path = Path(contract_path)
    contract = load_untouched_external_refit_positive_contract(contract_path)
    external = contract["external_validation"]
    assert isinstance(external, Mapping)
    freeze_spec = external["freeze_manifest"]
    assert isinstance(freeze_spec, Mapping)
    freeze_path = Path(str(freeze_spec["path"]))
    if not freeze_path.is_absolute():
        freeze_path = contract_path.parent / freeze_path
    if not freeze_path.is_file():
        raise FileNotFoundError(freeze_path)
    if _file_sha256(freeze_path) != str(freeze_spec["sha256"]):
        raise ValueError("freeze manifest SHA256 does not match the declared pre-outcome artifact")
    manifest = _load_manifest(freeze_path)

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
    refit_ids = sorted(
        {
            _text(_value(row, refit_id_col, row_index=index), name=f"row {index} refit_id")
            for index, row in enumerate(rows)
        }
    )
    row_ids = sorted(
        {
            _text(_value(row, row_id_col, row_index=index), name=f"row {index} row_id")
            for index, row in enumerate(rows)
        }
    )

    frozen_at = _text(manifest.get("frozen_at_utc"), name="freeze manifest.frozen_at_utc")
    _assert_equal(
        frozen_at,
        str(freeze_spec["frozen_at_utc"]),
        field="frozen_at_utc",
    )
    model_set_id = _text(
        manifest.get("upstream_model_set_id"), name="freeze manifest.upstream_model_set_id"
    )
    dataset_id = _text(
        manifest.get("external_dataset_id"), name="freeze manifest.external_dataset_id"
    )
    frozen_roster_sha = _text(
        manifest.get("external_row_ids_sha256"),
        name="freeze manifest.external_row_ids_sha256",
    ).lower()
    runtime_roster_sha = _row_roster_sha256(row_ids)
    _assert_equal(
        frozen_roster_sha,
        runtime_roster_sha,
        field="external_row_ids_sha256",
    )

    frozen_refit_ids = tuple(sorted(_string_list(manifest.get("refit_ids"), name="freeze manifest.refit_ids")))
    _assert_equal(frozen_refit_ids, tuple(refit_ids), field="refit_ids")

    cert = contract["certification"]
    assert isinstance(cert, Mapping)
    frozen_reference = _text(
        manifest.get("reference_refit_id"), name="freeze manifest.reference_refit_id"
    )
    _assert_equal(
        frozen_reference,
        str(cert["reference_refit_id"]),
        field="reference_refit_id",
    )
    if frozen_reference not in frozen_refit_ids:
        raise ValueError("freeze manifest reference_refit_id is not present in frozen refit_ids")

    frozen_score = _normalize_manifest_score(manifest.get("score"))
    runtime_score = dict(contract["score"])
    _assert_equal(frozen_score, runtime_score, field="score")

    frozen_levels = _normalize_manifest_levels(manifest.get("levels"))
    runtime_levels = [
        {
            "name": str(level["name"]),
            "information": list(level["information"]),
        }
        for level in contract["levels"]
    ]
    _assert_equal(frozen_levels, runtime_levels, field="levels")

    confirmatory_route = verify_frozen_confirmatory_route(
        manifest.get("confirmatory_route"),
        validation_design="independent_groups",
        information_structure="filtration",
        contrast_count=len(runtime_levels) - 1,
    )

    frozen_cert = _normalize_manifest_certification(manifest.get("certification"))
    runtime_cert = {
        "alternative": str(cert["alternative"]),
        "familywise_lower_confidence_level": float(cert["familywise_lower_confidence_level"]),
        "bootstrap_draws": int(cert["bootstrap_draws"]),
        "seed": int(cert["seed"]),
        "minimum_refits": int(cert["minimum_refits"]),
        "minimum_blocks_per_group": int(cert["minimum_blocks_per_group"]),
        "gain_tolerance": float(cert["gain_tolerance"]),
    }
    _assert_equal(frozen_cert, runtime_cert, field="certification")

    return {
        "manifest_type": "odsp_pre_external_outcome_freeze_v1",
        "upstream_model_set_id": model_set_id,
        "external_dataset_id": dataset_id,
        "external_row_ids_sha256": runtime_roster_sha,
        "refit_ids": refit_ids,
        "reference_refit_id": frozen_reference,
        "score": frozen_score,
        "levels": frozen_levels,
        "confirmatory_route": confirmatory_route,
        "certification": frozen_cert,
        "freeze_manifest_semantic_lock_verified": True,
    }


def run_untouched_external_refit_positive_contract_v2(
    path: str | Path,
) -> dict[str, object]:
    """Run the untouched external endpoint only after semantic freeze verification."""

    semantic_lock = verify_freeze_manifest_semantic_lock(path)
    receipt = run_untouched_external_refit_positive_contract(path)
    receipt["receipt_type"] = "odsp_untouched_external_refit_positive_validation_endpoint_v2"
    receipt["freeze_manifest_semantic_lock"] = semantic_lock
    boundaries = dict(receipt["boundaries"])
    boundaries["freeze_manifest_semantics_verified"] = True
    boundaries["external_row_roster_locked_before_outcome_access"] = True
    boundaries["runtime_analysis_matches_frozen_manifest"] = True
    boundaries["confirmatory_route_locked_before_outcome_access"] = True
    boundaries["runtime_confirmatory_route_matches_frozen_manifest"] = True
    receipt["boundaries"] = boundaries
    return receipt
