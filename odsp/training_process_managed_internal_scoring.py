"""Managed held-out scoring for internal training-process v5 validation.

This module derives the internal validation score tensor from the exact
managed-generated model artifacts under a pre-outcome internal validation
freeze.  It does not alter the qualified v5 statistical method.
"""
from __future__ import annotations

from datetime import datetime, timezone
import json
import os
from pathlib import Path
import subprocess
import sys
from typing import Mapping, Sequence

from .information_transfer_contract import _read_rows
from .refit_information_transfer import RefitInformationLevelScores
from .training_process_confirmatory_v5 import _load_json
from .training_process_freeze_manifest import _file_sha256
from .training_process_internal_freeze_v1 import (
    FREEZE_RECEIPT_TYPE,
    MANIFEST_TYPE,
)
from .training_process_validation_helpers import (
    _canonical_sha256,
    _json_score,
    _safe_score,
    _scoring_plan,
    _sha256_text,
    _text,
    _validate_scoring_output,
    _validation_design_rows,
    _verify_generated_models,
    _verify_scoring_identity,
)
from .training_process_managed_generation import _sha256_bytes


MANAGED_INTERNAL_SCORING_RECEIPT_TYPE = (
    "odsp_training_process_v5_managed_internal_scoring_receipt_v1"
)
MANAGED_INTERNAL_SCORE_BUNDLE_TYPE = (
    "odsp_training_process_v5_managed_internal_score_bundle_v1"
)


def _freeze_inputs(
    freeze_manifest_path: Path,
    freeze_receipt_path: Path,
) -> tuple[dict[str, object], dict[str, object]]:
    manifest = _load_json(
        freeze_manifest_path, name="internal validation freeze manifest"
    )
    if manifest.get("manifest_type") != MANIFEST_TYPE:
        raise ValueError("internal validation freeze manifest_type is not recognized")
    if manifest.get("schema_version") != 1:
        raise ValueError("internal validation freeze schema_version must be 1")
    receipt = _load_json(
        freeze_receipt_path, name="internal validation freeze receipt"
    )
    if receipt.get("receipt_type") != FREEZE_RECEIPT_TYPE:
        raise ValueError("internal validation freeze receipt_type is not recognized")
    if receipt.get("manifest_sha256") != _file_sha256(freeze_manifest_path):
        raise ValueError("internal validation freeze receipt manifest SHA256 mismatch")
    if receipt.get("validation_design_sha256") != manifest.get(
        "validation_design_sha256"
    ):
        raise ValueError("internal validation freeze design digest mismatch")
    if receipt.get("managed_generation_receipt_sha256") != manifest.get(
        "managed_generation_receipt_sha256"
    ):
        raise ValueError("internal validation freeze generation digest mismatch")
    return manifest, receipt


def _validation_design(
    roster_path: Path,
    *,
    format_name: str,
    manifest: Mapping[str, object],
) -> list[dict[str, object]]:
    rows = _read_rows(roster_path, format_name)
    canonical, block_counts = _validation_design_rows(rows)
    if _canonical_sha256(canonical) != manifest.get("validation_design_sha256"):
        raise ValueError("validation roster design does not match freeze")
    if len(canonical) != manifest.get("validation_row_count"):
        raise ValueError("validation roster row count does not match freeze")
    if block_counts != manifest.get("positive_block_count_by_group"):
        raise ValueError("validation roster block counts do not match freeze")
    return canonical


def run_managed_internal_scoring_v1(
    internal_freeze_manifest_path: str | Path,
    internal_freeze_receipt_path: str | Path,
    validation_roster_path: str | Path,
    *,
    validation_roster_format: str,
    managed_generation_receipt_path: str | Path,
    generated_model_root: str | Path,
    validation_data_path: str | Path,
    output_root: str | Path,
    score_bundle_out: str | Path,
    scoring_receipt_out: str | Path,
) -> dict[str, object]:
    """Run frozen scoring code for every refit on held-out internal validation."""

    freeze_manifest_path = Path(internal_freeze_manifest_path)
    freeze_receipt_path = Path(internal_freeze_receipt_path)
    roster_path = Path(validation_roster_path)
    managed_receipt_path = Path(managed_generation_receipt_path)
    model_root = Path(generated_model_root)
    validation_path = Path(validation_data_path)
    for path in (
        freeze_manifest_path,
        freeze_receipt_path,
        roster_path,
        managed_receipt_path,
        validation_path,
    ):
        if not path.is_file():
            raise FileNotFoundError(path)
    if not model_root.is_dir():
        raise FileNotFoundError(model_root)

    manifest, _ = _freeze_inputs(
        freeze_manifest_path, freeze_receipt_path
    )
    managed_receipt_sha = _file_sha256(managed_receipt_path)
    if managed_receipt_sha != manifest.get("managed_generation_receipt_sha256"):
        raise ValueError(
            "managed generation receipt does not match internal validation freeze"
        )
    managed_receipt = _load_json(
        managed_receipt_path, name="managed generation receipt"
    )

    format_name = _text(
        validation_roster_format, name="validation_roster_format"
    ).lower()
    if format_name not in {"csv", "json"}:
        raise ValueError("validation_roster_format must be csv or json")
    design = _validation_design(
        roster_path, format_name=format_name, manifest=manifest
    )
    row_ids = [str(row["row_id"]) for row in design]

    scoring_plan = _scoring_plan(manifest)
    validation_format = _text(
        scoring_plan["validation_data_format"],
        name="managed_scoring_plan.validation_data_format",
    ).lower()
    validation_row_id_column = _text(
        scoring_plan["validation_row_id_column"],
        name="managed_scoring_plan.validation_row_id_column",
    )
    validation_data_first_read_by_odsp_at_utc = (
        datetime.now(timezone.utc).isoformat().replace("+00:00", "Z")
    )
    validation_rows = _read_rows(validation_path, validation_format)
    validation_ids: list[str] = []
    for index, row in enumerate(validation_rows):
        if validation_row_id_column not in row:
            raise ValueError(
                f"validation data row {index} is missing frozen row-ID column"
            )
        validation_ids.append(
            _text(
                row[validation_row_id_column],
                name=f"validation data row {index} row ID",
            )
        )
    if len(validation_ids) != len(set(validation_ids)):
        raise ValueError("validation data row IDs must be unique")
    if set(validation_ids) != set(row_ids):
        raise ValueError(
            "validation data row IDs do not exactly match frozen validation roster"
        )

    levels = manifest.get("levels")
    if not isinstance(levels, list) or len(levels) != 3:
        raise ValueError("internal validation freeze levels are invalid")
    level_names = [
        _text(level.get("name"), name=f"levels[{index}].name")
        for index, level in enumerate(levels)
        if isinstance(level, Mapping)
    ]
    if len(level_names) != 3:
        raise ValueError("internal validation level metadata is invalid")

    refit_ids_raw = manifest.get("refit_ids")
    if not isinstance(refit_ids_raw, list) or not refit_ids_raw:
        raise ValueError("internal validation freeze refit_ids are invalid")
    refit_ids = [
        _text(value, name="internal validation freeze refit_id")
        for value in refit_ids_raw
    ]
    models = _verify_generated_models(
        managed_receipt,
        generated_model_root=model_root,
        frozen_snapshot=manifest.get("generated_model_artifact_snapshot"),
    )

    working, runtime = _verify_scoring_identity(
        scoring_plan, freeze_base=freeze_manifest_path.parent
    )

    output_dir = Path(output_root)
    bundle_path = Path(score_bundle_out)
    receipt_path = Path(scoring_receipt_out)
    if output_dir.exists():
        raise FileExistsError(
            f"managed internal scoring output root already exists: {output_dir}"
        )
    if bundle_path.exists():
        raise FileExistsError(f"internal score bundle already exists: {bundle_path}")
    if receipt_path.exists():
        raise FileExistsError(
            f"internal scoring receipt already exists: {receipt_path}"
        )
    output_dir.mkdir(parents=True)
    bundle_path.parent.mkdir(parents=True, exist_ok=True)
    receipt_path.parent.mkdir(parents=True, exist_ok=True)

    scoring_spec = {
        "schema_version": 1,
        "validation_dataset_id": manifest.get("validation_dataset_id"),
        "row_identity_namespace": manifest.get("row_identity_namespace"),
        "rows": design,
        "score": manifest.get("score"),
        "levels": levels,
    }
    scoring_spec_path = output_dir / "scoring-spec.json"
    scoring_spec_path.write_text(
        json.dumps(scoring_spec, indent=2, sort_keys=True, allow_nan=False) + "\n",
        encoding="utf-8",
    )
    scoring_spec_sha = _file_sha256(scoring_spec_path)
    validation_sha = _file_sha256(validation_path)

    env = {
        name: value for name, value in runtime["environment"].items()
    }
    all_scores: dict[str, dict[str, dict[str, float]]] = {}
    executions: list[dict[str, object]] = []

    for refit_id in refit_ids:
        if refit_id not in models:
            raise ValueError(f"generated model missing frozen refit {refit_id}")
        refit_dir = output_dir / refit_id
        refit_dir.mkdir()
        model_manifest_path = refit_dir / "model-manifest.json"
        model_manifest_path.write_text(
            json.dumps(
                {
                    "schema_version": 1,
                    "refit_id": refit_id,
                    "artifacts": models[refit_id],
                },
                indent=2,
                sort_keys=True,
                allow_nan=False,
            )
            + "\n",
            encoding="utf-8",
        )
        output_path = refit_dir / "scores.json"
        replacements = {
            "{refit_id}": refit_id,
            "{model_manifest_path}": str(model_manifest_path.resolve()),
            "{validation_data_path}": str(validation_path.resolve()),
            "{scoring_spec_path}": str(scoring_spec_path.resolve()),
            "{output_path}": str(output_path.resolve()),
            "{python_executable}": str(Path(sys.executable).resolve()),
        }
        argv: list[str] = []
        for token in scoring_plan["command"]:
            value = str(token)
            for key, replacement in replacements.items():
                value = value.replace(key, replacement)
            argv.append(value)

        completed = subprocess.run(
            argv,
            cwd=working,
            env=env,
            shell=False,
            capture_output=True,
            timeout=int(scoring_plan["timeout_seconds"]),
            check=False,
        )
        if completed.returncode != 0:
            raise RuntimeError(
                f"managed internal scoring failed for {refit_id} "
                f"with return code {completed.returncode}"
            )
        if output_path.is_symlink() or not output_path.is_file():
            raise FileNotFoundError(output_path)
        scores = _validate_scoring_output(
            output_path,
            expected_refit_id=refit_id,
            expected_row_ids=row_ids,
            level_names=level_names,
        )
        all_scores[refit_id] = scores
        executions.append(
            {
                "refit_id": refit_id,
                "model_manifest_sha256": _file_sha256(model_manifest_path),
                "argv": argv,
                "stdout_sha256": _sha256_bytes(completed.stdout),
                "stderr_sha256": _sha256_bytes(completed.stderr),
                "return_code": int(completed.returncode),
                "score_output_sha256": _file_sha256(output_path),
            }
        )

    canonical_tensor: list[dict[str, object]] = []
    for refit_id in refit_ids:
        for row_id in row_ids:
            canonical_tensor.append(
                {
                    "refit_id": refit_id,
                    "row_id": row_id,
                    "scores": {
                        level: _json_score(all_scores[refit_id][row_id][level])
                        for level in level_names
                    },
                }
            )
    tensor_sha = _canonical_sha256(canonical_tensor)

    matrices: dict[str, list[list[float | str]]] = {}
    for level in level_names:
        matrices[level] = [
            [
                _json_score(all_scores[refit_id][row_id][level])
                for row_id in row_ids
            ]
            for refit_id in refit_ids
        ]

    bundle = {
        "schema_version": 1,
        "bundle_type": MANAGED_INTERNAL_SCORE_BUNDLE_TYPE,
        "internal_validation_freeze_manifest_sha256": _file_sha256(
            freeze_manifest_path
        ),
        "managed_generation_receipt_sha256": managed_receipt_sha,
        "validation_data_sha256": validation_sha,
        "validation_data_first_read_by_odsp_at_utc": validation_data_first_read_by_odsp_at_utc,
        "refit_ids": refit_ids,
        "row_ids": row_ids,
        "levels": levels,
        "scores_by_level": matrices,
        "canonical_score_tensor_sha256": tensor_sha,
    }
    bundle_path.write_text(
        json.dumps(bundle, indent=2, sort_keys=True, allow_nan=False) + "\n",
        encoding="utf-8",
    )

    created_at = (
        datetime.now(timezone.utc)
        .replace(microsecond=0)
        .isoformat()
        .replace("+00:00", "Z")
    )
    receipt = {
        "schema_version": 1,
        "receipt_type": MANAGED_INTERNAL_SCORING_RECEIPT_TYPE,
        "created_at_utc": created_at,
        "internal_validation_freeze_manifest_sha256": _file_sha256(
            freeze_manifest_path
        ),
        "internal_validation_freeze_receipt_sha256": _file_sha256(
            freeze_receipt_path
        ),
        "managed_generation_receipt_sha256": managed_receipt_sha,
        "validation_data_sha256": validation_sha,
        "validation_roster_file_sha256": _file_sha256(roster_path),
        "scoring_spec_sha256": scoring_spec_sha,
        "scoring_command_artifact_snapshot": scoring_plan[
            "command_artifact_snapshot"
        ],
        "scoring_runtime_environment_snapshot": runtime,
        "generated_model_artifact_snapshot": manifest.get(
            "generated_model_artifact_snapshot"
        ),
        "score_bundle_sha256": _file_sha256(bundle_path),
        "canonical_score_tensor_sha256": tensor_sha,
        "refit_count": len(refit_ids),
        "row_count": len(row_ids),
        "level_names": level_names,
        "executions": executions,
        "boundaries": {
            "score_tensor_derived_by_managed_scoring": True,
            "generated_model_artifacts_reverified_before_scoring": True,
            "shell_used": False,
            "semantic_use_of_model_and_validation_inputs_cryptographically_proven": False,
        },
    }
    receipt_path.write_text(
        json.dumps(receipt, indent=2, sort_keys=True, allow_nan=False) + "\n",
        encoding="utf-8",
    )
    return {
        "receipt": receipt,
        "receipt_path": str(receipt_path),
        "receipt_sha256": _file_sha256(receipt_path),
        "score_bundle": bundle,
        "score_bundle_path": str(bundle_path),
        "score_bundle_sha256": _file_sha256(bundle_path),
    }


def load_managed_internal_score_bundle(
    score_bundle_path: str | Path,
    *,
    expected_bundle_sha256: object,
    expected_internal_validation_freeze_manifest_sha256: object,
    expected_managed_generation_receipt_sha256: object,
    expected_validation_data_sha256: object,
) -> tuple[
    tuple[RefitInformationLevelScores, ...],
    tuple[str, ...],
    tuple[str, ...],
    str,
]:
    """Load one managed internal bundle and reconstruct v5 score matrices."""

    path = Path(score_bundle_path)
    if not path.is_file():
        raise FileNotFoundError(path)
    if _file_sha256(path) != _sha256_text(
        expected_bundle_sha256, name="expected_bundle_sha256"
    ):
        raise ValueError("managed internal score bundle SHA256 mismatch")
    raw = _load_json(path, name="managed internal score bundle")
    required = {
        "schema_version",
        "bundle_type",
        "internal_validation_freeze_manifest_sha256",
        "managed_generation_receipt_sha256",
        "validation_data_sha256",
        "refit_ids",
        "row_ids",
        "levels",
        "scores_by_level",
        "canonical_score_tensor_sha256",
    }
    if set(raw) != required:
        raise ValueError("managed internal score bundle fields mismatch")
    if (
        raw["schema_version"] != 1
        or raw["bundle_type"] != MANAGED_INTERNAL_SCORE_BUNDLE_TYPE
    ):
        raise ValueError("managed internal score bundle identity is invalid")

    checks = (
        (
            "internal_validation_freeze_manifest_sha256",
            expected_internal_validation_freeze_manifest_sha256,
        ),
        (
            "managed_generation_receipt_sha256",
            expected_managed_generation_receipt_sha256,
        ),
        ("validation_data_sha256", expected_validation_data_sha256),
    )
    for field, expected in checks:
        if raw[field] != _sha256_text(expected, name=f"expected {field}"):
            raise ValueError(f"managed internal score bundle {field} mismatch")

    refit_ids_raw = raw["refit_ids"]
    row_ids_raw = raw["row_ids"]
    levels_raw = raw["levels"]
    scores_raw = raw["scores_by_level"]
    if not isinstance(refit_ids_raw, list) or not refit_ids_raw:
        raise ValueError("managed internal bundle refit_ids are invalid")
    if not isinstance(row_ids_raw, list) or not row_ids_raw:
        raise ValueError("managed internal bundle row_ids are invalid")
    if not isinstance(levels_raw, list) or len(levels_raw) != 3:
        raise ValueError("managed internal bundle levels are invalid")
    if not isinstance(scores_raw, Mapping):
        raise ValueError("managed internal bundle scores_by_level is invalid")

    refit_ids = tuple(_text(x, name="bundle refit_id") for x in refit_ids_raw)
    row_ids = tuple(_text(x, name="bundle row_id") for x in row_ids_raw)
    if len(refit_ids) != len(set(refit_ids)) or len(row_ids) != len(set(row_ids)):
        raise ValueError("managed internal bundle IDs must be unique")

    levels: list[RefitInformationLevelScores] = []
    level_names: list[str] = []
    matrices: dict[str, list[list[float]]] = {}
    for index, level in enumerate(levels_raw):
        if not isinstance(level, Mapping) or set(level) != {"name", "information"}:
            raise ValueError("managed internal bundle level metadata is invalid")
        name = _text(level["name"], name=f"bundle levels[{index}].name")
        info_raw = level["information"]
        if not isinstance(info_raw, list):
            raise ValueError("managed internal bundle information is invalid")
        info = tuple(_text(x, name="bundle information") for x in info_raw)
        raw_matrix = scores_raw.get(name)
        if not isinstance(raw_matrix, list) or len(raw_matrix) != len(refit_ids):
            raise ValueError(f"managed internal score matrix shape is invalid for {name}")
        matrix: list[list[float]] = []
        for r, row in enumerate(raw_matrix):
            if not isinstance(row, list) or len(row) != len(row_ids):
                raise ValueError(
                    f"managed internal score matrix row shape is invalid for {name}"
                )
            matrix.append(
                [
                    _safe_score(value, name=f"bundle score[{name},{r},{c}]")
                    for c, value in enumerate(row)
                ]
            )
        matrices[name] = matrix
        level_names.append(name)
        levels.append(
            RefitInformationLevelScores(name, info, matrix)
        )
    if set(scores_raw) != set(level_names):
        raise ValueError(
            "managed internal bundle level keys do not match level metadata"
        )

    canonical_tensor: list[dict[str, object]] = []
    for r, refit_id in enumerate(refit_ids):
        for c, row_id in enumerate(row_ids):
            canonical_tensor.append(
                {
                    "refit_id": refit_id,
                    "row_id": row_id,
                    "scores": {
                        level: _json_score(matrices[level][r][c])
                        for level in level_names
                    },
                }
            )
    tensor_sha = _canonical_sha256(canonical_tensor)
    if tensor_sha != _sha256_text(
        raw["canonical_score_tensor_sha256"],
        name="canonical_score_tensor_sha256",
    ):
        raise ValueError("managed internal score bundle tensor digest mismatch")
    return tuple(levels), row_ids, refit_ids, tensor_sha
