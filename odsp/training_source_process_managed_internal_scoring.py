"""Managed held-out scoring for training-source process v0.

This provenance layer derives a source x inner-refit x validation-row x level
score tensor from the exact managed-generated nested model artifacts under a
pre-outcome validation freeze.  It does not change source-v0 statistics.
"""
from __future__ import annotations

from datetime import datetime, timezone
import json
from pathlib import Path
import subprocess
import sys
from typing import Mapping

import numpy as np

from .information_transfer_contract import _read_rows
from .refit_information_transfer import RefitInformationLevelScores
from .training_process_freeze_manifest import _file_sha256
from .training_source_process_internal_freeze_v0 import (
    FREEZE_RECEIPT_TYPE,
    MANIFEST_TYPE,
)
from .training_source_process_managed_generation import _sha256_bytes
from .training_source_process_validation_helpers import (
    _canonical_sha256,
    _json_score,
    _load_json,
    _safe_score,
    _scoring_plan,
    _sha256_text,
    _text,
    _validate_nested_scoring_output,
    _validation_design_rows,
    _verify_nested_generated_models,
    _verify_scoring_identity,
)


MANAGED_SCORING_RECEIPT_TYPE = (
    "odsp_training_source_process_v0_managed_internal_scoring_receipt"
)
MANAGED_SCORE_BUNDLE_TYPE = (
    "odsp_training_source_process_v0_managed_internal_score_bundle"
)


def _freeze_inputs(
    manifest_path: Path,
    receipt_path: Path,
) -> tuple[dict[str, object], dict[str, object]]:
    manifest = _load_json(manifest_path, name="source-v0 validation freeze manifest")
    if manifest.get("manifest_type") != MANIFEST_TYPE:
        raise ValueError("source-v0 validation freeze manifest_type is invalid")
    if manifest.get("schema_version") != 1:
        raise ValueError("source-v0 validation freeze schema_version must be 1")
    receipt = _load_json(receipt_path, name="source-v0 validation freeze receipt")
    if receipt.get("receipt_type") != FREEZE_RECEIPT_TYPE:
        raise ValueError("source-v0 validation freeze receipt_type is invalid")
    if receipt.get("manifest_sha256") != _file_sha256(manifest_path):
        raise ValueError("source-v0 validation freeze manifest SHA256 mismatch")
    if receipt.get("validation_design_sha256") != manifest.get(
        "validation_design_sha256"
    ):
        raise ValueError("source-v0 validation freeze design digest mismatch")
    if receipt.get("managed_nested_generation_receipt_sha256") != manifest.get(
        "managed_nested_generation_receipt_sha256"
    ):
        raise ValueError("source-v0 validation freeze generation digest mismatch")
    return manifest, receipt


def _validation_design(
    roster_path: Path,
    *,
    format_name: str,
    manifest: Mapping[str, object],
) -> list[dict[str, object]]:
    canonical, block_counts = _validation_design_rows(
        _read_rows(roster_path, format_name)
    )
    if _canonical_sha256(canonical) != manifest.get("validation_design_sha256"):
        raise ValueError("validation roster design does not match source-v0 freeze")
    if len(canonical) != manifest.get("validation_row_count"):
        raise ValueError("validation roster row count does not match source-v0 freeze")
    if block_counts != manifest.get("positive_block_count_by_group"):
        raise ValueError("validation roster block counts do not match source-v0 freeze")
    return canonical


def run_managed_training_source_process_scoring_v0(
    internal_freeze_manifest_path: str | Path,
    internal_freeze_receipt_path: str | Path,
    validation_roster_path: str | Path,
    *,
    validation_roster_format: str,
    managed_nested_generation_receipt_path: str | Path,
    generated_model_root: str | Path,
    validation_data_path: str | Path,
    output_root: str | Path,
    score_bundle_out: str | Path,
    scoring_receipt_out: str | Path,
) -> dict[str, object]:
    """Derive the frozen nested score tensor from generated model bytes."""

    freeze_manifest_path = Path(internal_freeze_manifest_path)
    freeze_receipt_path = Path(internal_freeze_receipt_path)
    roster_path = Path(validation_roster_path)
    generation_receipt_path = Path(managed_nested_generation_receipt_path)
    model_root = Path(generated_model_root)
    validation_path = Path(validation_data_path)
    for path in (
        freeze_manifest_path,
        freeze_receipt_path,
        roster_path,
        generation_receipt_path,
        validation_path,
    ):
        if not path.is_file():
            raise FileNotFoundError(path)
    if not model_root.is_dir():
        raise FileNotFoundError(model_root)

    manifest, _ = _freeze_inputs(freeze_manifest_path, freeze_receipt_path)
    generation_receipt_sha = _file_sha256(generation_receipt_path)
    if generation_receipt_sha != manifest.get(
        "managed_nested_generation_receipt_sha256"
    ):
        raise ValueError("managed nested-generation receipt does not match freeze")
    generation_receipt = _load_json(
        generation_receipt_path, name="managed nested-generation receipt"
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
    row_id_column = _text(
        scoring_plan["validation_row_id_column"],
        name="managed_scoring_plan.validation_row_id_column",
    )
    validation_data_first_read_by_odsp_at_utc = (
        datetime.now(timezone.utc).isoformat().replace("+00:00", "Z")
    )
    validation_rows = _read_rows(validation_path, validation_format)
    validation_ids: list[str] = []
    for index, row in enumerate(validation_rows):
        if row_id_column not in row:
            raise ValueError(
                f"validation data row {index} is missing frozen row-ID column"
            )
        validation_ids.append(
            _text(row[row_id_column], name=f"validation data row {index} row ID")
        )
    if len(validation_ids) != len(set(validation_ids)):
        raise ValueError("validation data row IDs must be unique")
    if set(validation_ids) != set(row_ids):
        raise ValueError(
            "validation data row IDs do not exactly match frozen validation roster"
        )

    levels = manifest.get("levels")
    if not isinstance(levels, list) or len(levels) != 3:
        raise ValueError("source-v0 frozen level metadata is invalid")
    level_names = [
        _text(level.get("name"), name=f"levels[{index}].name")
        for index, level in enumerate(levels)
        if isinstance(level, Mapping)
    ]
    if len(level_names) != 3:
        raise ValueError("source-v0 frozen level metadata is invalid")

    source_ids_raw = manifest.get("source_draw_ids")
    inner_ids_raw = manifest.get("inner_refit_ids")
    if not isinstance(source_ids_raw, list) or not source_ids_raw:
        raise ValueError("source-v0 source_draw_ids are invalid")
    if not isinstance(inner_ids_raw, list) or not inner_ids_raw:
        raise ValueError("source-v0 inner_refit_ids are invalid")
    source_ids = [_text(x, name="source_draw_id") for x in source_ids_raw]
    inner_ids = [_text(x, name="inner_refit_id") for x in inner_ids_raw]

    models = _verify_nested_generated_models(
        generation_receipt,
        generated_model_root=model_root,
        frozen_snapshot=manifest.get("nested_model_artifact_snapshot"),
    )
    working, runtime = _verify_scoring_identity(
        scoring_plan, freeze_base=freeze_manifest_path.parent
    )

    output_dir = Path(output_root)
    bundle_path = Path(score_bundle_out)
    receipt_path = Path(scoring_receipt_out)
    if output_dir.exists():
        raise FileExistsError(
            f"managed source-v0 scoring output root already exists: {output_dir}"
        )
    if bundle_path.exists():
        raise FileExistsError(f"source-v0 score bundle already exists: {bundle_path}")
    if receipt_path.exists():
        raise FileExistsError(
            f"source-v0 scoring receipt already exists: {receipt_path}"
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
        name: value
        for name, value in runtime["environment"].items()
    }

    all_scores: dict[
        tuple[str, str], dict[str, dict[str, float]]
    ] = {}
    executions: list[dict[str, object]] = []

    for source_id in source_ids:
        for refit_id in inner_ids:
            key = (source_id, refit_id)
            if key not in models:
                raise ValueError(
                    f"generated model missing frozen pair {source_id}/{refit_id}"
                )
            pair_dir = output_dir / source_id / refit_id
            pair_dir.mkdir(parents=True)
            model_manifest_path = pair_dir / "model-manifest.json"
            model_manifest_path.write_text(
                json.dumps(
                    {
                        "schema_version": 1,
                        "source_draw_id": source_id,
                        "inner_refit_id": refit_id,
                        "artifacts": models[key],
                    },
                    indent=2,
                    sort_keys=True,
                    allow_nan=False,
                )
                + "\n",
                encoding="utf-8",
            )
            output_path = pair_dir / "scores.json"
            replacements = {
                "{source_draw_id}": source_id,
                "{inner_refit_id}": refit_id,
                "{model_manifest_path}": str(model_manifest_path.resolve()),
                "{validation_data_path}": str(validation_path.resolve()),
                "{scoring_spec_path}": str(scoring_spec_path.resolve()),
                "{output_path}": str(output_path.resolve()),
                "{python_executable}": str(Path(sys.executable).resolve()),
            }
            argv: list[str] = []
            for token in scoring_plan["command"]:
                value = str(token)
                for placeholder, replacement in replacements.items():
                    value = value.replace(placeholder, replacement)
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
                    "managed source-v0 scoring failed for "
                    f"{source_id}/{refit_id} with return code "
                    f"{completed.returncode}"
                )
            if output_path.is_symlink() or not output_path.is_file():
                raise FileNotFoundError(output_path)
            scores = _validate_nested_scoring_output(
                output_path,
                expected_source_draw_id=source_id,
                expected_inner_refit_id=refit_id,
                expected_row_ids=row_ids,
                level_names=level_names,
            )
            all_scores[key] = scores
            executions.append(
                {
                    "source_draw_id": source_id,
                    "inner_refit_id": refit_id,
                    "model_manifest_sha256": _file_sha256(model_manifest_path),
                    "argv": argv,
                    "stdout_sha256": _sha256_bytes(completed.stdout),
                    "stderr_sha256": _sha256_bytes(completed.stderr),
                    "return_code": int(completed.returncode),
                    "score_output_sha256": _file_sha256(output_path),
                }
            )

    canonical_tensor: list[dict[str, object]] = []
    for source_id in source_ids:
        for refit_id in inner_ids:
            for row_id in row_ids:
                canonical_tensor.append(
                    {
                        "source_draw_id": source_id,
                        "inner_refit_id": refit_id,
                        "row_id": row_id,
                        "scores": {
                            level: _json_score(
                                all_scores[(source_id, refit_id)][row_id][level]
                            )
                            for level in level_names
                        },
                    }
                )
    tensor_sha = _canonical_sha256(canonical_tensor)

    matrices: dict[str, list[list[list[float | str]]]] = {}
    for level in level_names:
        matrices[level] = [
            [
                [
                    _json_score(
                        all_scores[(source_id, refit_id)][row_id][level]
                    )
                    for row_id in row_ids
                ]
                for refit_id in inner_ids
            ]
            for source_id in source_ids
        ]

    bundle = {
        "schema_version": 1,
        "bundle_type": MANAGED_SCORE_BUNDLE_TYPE,
        "internal_validation_freeze_manifest_sha256": _file_sha256(
            freeze_manifest_path
        ),
        "managed_nested_generation_receipt_sha256": generation_receipt_sha,
        "validation_data_sha256": validation_sha,
        "source_draw_ids": source_ids,
        "inner_refit_ids": inner_ids,
        "row_ids": row_ids,
        "levels": levels,
        "scores_by_level": matrices,
        "canonical_source_inner_row_level_tensor_sha256": tensor_sha,
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
        "receipt_type": MANAGED_SCORING_RECEIPT_TYPE,
        "created_at_utc": created_at,
        "validation_data_first_read_by_odsp_at_utc": (
            validation_data_first_read_by_odsp_at_utc
        ),
        "internal_validation_freeze_manifest_sha256": _file_sha256(
            freeze_manifest_path
        ),
        "internal_validation_freeze_receipt_sha256": _file_sha256(
            freeze_receipt_path
        ),
        "managed_nested_generation_receipt_sha256": generation_receipt_sha,
        "validation_data_sha256": validation_sha,
        "validation_roster_file_sha256": _file_sha256(roster_path),
        "scoring_spec_sha256": scoring_spec_sha,
        "scoring_command_artifact_snapshot": scoring_plan[
            "command_artifact_snapshot"
        ],
        "scoring_runtime_environment_snapshot": runtime,
        "nested_generated_model_artifact_snapshot": manifest.get(
            "nested_model_artifact_snapshot"
        ),
        "score_bundle_sha256": _file_sha256(bundle_path),
        "canonical_source_inner_row_level_tensor_sha256": tensor_sha,
        "source_draw_count": len(source_ids),
        "inner_refit_count_per_source": len(inner_ids),
        "fit_score_execution_count": len(source_ids) * len(inner_ids),
        "row_count": len(row_ids),
        "level_names": level_names,
        "executions": executions,
        "boundaries": {
            "score_tensor_derived_by_managed_scoring": True,
            "nested_generated_model_artifacts_reverified_before_scoring": True,
            "source_inner_nesting_preserved": True,
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


def load_managed_training_source_process_score_bundle_v0(
    score_bundle_path: str | Path,
    *,
    expected_bundle_sha256: object,
    expected_internal_validation_freeze_manifest_sha256: object,
    expected_managed_nested_generation_receipt_sha256: object,
    expected_validation_data_sha256: object,
) -> tuple[
    tuple[tuple[RefitInformationLevelScores, ...], ...],
    tuple[str, ...],
    tuple[str, ...],
    tuple[str, ...],
    str,
]:
    """Load a managed source-v0 bundle and reconstruct nested score matrices."""

    path = Path(score_bundle_path)
    if not path.is_file():
        raise FileNotFoundError(path)
    if _file_sha256(path) != _sha256_text(
        expected_bundle_sha256, name="expected_bundle_sha256"
    ):
        raise ValueError("managed source-v0 score bundle SHA256 mismatch")
    raw = _load_json(path, name="managed source-v0 score bundle")
    required = {
        "schema_version",
        "bundle_type",
        "internal_validation_freeze_manifest_sha256",
        "managed_nested_generation_receipt_sha256",
        "validation_data_sha256",
        "source_draw_ids",
        "inner_refit_ids",
        "row_ids",
        "levels",
        "scores_by_level",
        "canonical_source_inner_row_level_tensor_sha256",
    }
    if set(raw) != required:
        raise ValueError("managed source-v0 score bundle fields mismatch")
    if raw["schema_version"] != 1 or raw["bundle_type"] != MANAGED_SCORE_BUNDLE_TYPE:
        raise ValueError("managed source-v0 score bundle identity is invalid")

    checks = (
        (
            "internal_validation_freeze_manifest_sha256",
            expected_internal_validation_freeze_manifest_sha256,
        ),
        (
            "managed_nested_generation_receipt_sha256",
            expected_managed_nested_generation_receipt_sha256,
        ),
        ("validation_data_sha256", expected_validation_data_sha256),
    )
    for field, expected in checks:
        if raw[field] != _sha256_text(expected, name=f"expected {field}"):
            raise ValueError(f"managed source-v0 score bundle {field} mismatch")

    source_raw = raw["source_draw_ids"]
    inner_raw = raw["inner_refit_ids"]
    row_raw = raw["row_ids"]
    levels_raw = raw["levels"]
    scores_raw = raw["scores_by_level"]
    if not isinstance(source_raw, list) or not source_raw:
        raise ValueError("managed source-v0 source_draw_ids are invalid")
    if not isinstance(inner_raw, list) or not inner_raw:
        raise ValueError("managed source-v0 inner_refit_ids are invalid")
    if not isinstance(row_raw, list) or not row_raw:
        raise ValueError("managed source-v0 row_ids are invalid")
    if not isinstance(levels_raw, list) or len(levels_raw) != 3:
        raise ValueError("managed source-v0 levels are invalid")
    if not isinstance(scores_raw, Mapping):
        raise ValueError("managed source-v0 scores_by_level is invalid")

    source_ids = tuple(_text(x, name="source_draw_id") for x in source_raw)
    inner_ids = tuple(_text(x, name="inner_refit_id") for x in inner_raw)
    row_ids = tuple(_text(x, name="row_id") for x in row_raw)
    if len(set(source_ids)) != len(source_ids):
        raise ValueError("managed source-v0 source_draw_ids must be unique")
    if len(set(inner_ids)) != len(inner_ids):
        raise ValueError("managed source-v0 inner_refit_ids must be unique")
    if len(set(row_ids)) != len(row_ids):
        raise ValueError("managed source-v0 row_ids must be unique")

    levels_meta: list[tuple[str, tuple[str, ...]]] = []
    for index, item in enumerate(levels_raw):
        if not isinstance(item, Mapping) or set(item) != {"name", "information"}:
            raise ValueError(f"managed source-v0 levels[{index}] is invalid")
        name = _text(item["name"], name=f"levels[{index}].name")
        info_raw = item["information"]
        if not isinstance(info_raw, list):
            raise ValueError("managed source-v0 information metadata is invalid")
        info = tuple(_text(x, name="information") for x in info_raw)
        levels_meta.append((name, info))

    expected_shape = (len(source_ids), len(inner_ids), len(row_ids))
    levels_by_source: list[tuple[RefitInformationLevelScores, ...]] = []
    arrays_by_level: dict[str, np.ndarray] = {}
    for level_name, _ in levels_meta:
        matrix = scores_raw.get(level_name)
        try:
            array = np.asarray(
                [
                    [
                        [
                            _safe_score(
                                value,
                                name=(
                                    f"scores[{level_name},{si},{ri},{vi}]"
                                ),
                            )
                            for vi, value in enumerate(refit_rows)
                        ]
                        for ri, refit_rows in enumerate(source_rows)
                    ]
                    for si, source_rows in enumerate(matrix)
                ],
                dtype=float,
            )
        except TypeError as exc:
            raise ValueError("managed source-v0 score matrix is malformed") from exc
        if array.shape != expected_shape:
            raise ValueError(
                f"managed source-v0 score matrix {level_name!r} has wrong shape"
            )
        arrays_by_level[level_name] = array

    canonical: list[dict[str, object]] = []
    for si, source_id in enumerate(source_ids):
        for ri, refit_id in enumerate(inner_ids):
            for vi, row_id in enumerate(row_ids):
                canonical.append(
                    {
                        "source_draw_id": source_id,
                        "inner_refit_id": refit_id,
                        "row_id": row_id,
                        "scores": {
                            name: _json_score(arrays_by_level[name][si, ri, vi])
                            for name, _ in levels_meta
                        },
                    }
                )
    tensor_sha = _canonical_sha256(canonical)
    if tensor_sha != _sha256_text(
        raw["canonical_source_inner_row_level_tensor_sha256"],
        name="canonical tensor sha256",
    ):
        raise ValueError("managed source-v0 canonical score tensor digest mismatch")

    for si in range(len(source_ids)):
        levels_by_source.append(
            tuple(
                RefitInformationLevelScores(
                    name,
                    info,
                    arrays_by_level[name][si],
                )
                for name, info in levels_meta
            )
        )
    return (
        tuple(levels_by_source),
        row_ids,
        source_ids,
        inner_ids,
        tensor_sha,
    )
