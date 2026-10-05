"""Managed untouched-external scoring for the qualified training-process v5 route.

This layer operationally binds external score matrices to:
- the pre-outcome external freeze,
- the managed-generated model artifacts,
- a frozen scoring command and runtime,
- the outcome-bearing validation-data bytes.

It does not accept caller-supplied score matrices.
"""
from __future__ import annotations

from datetime import datetime, timezone
import json
import math
import os
from pathlib import Path
import subprocess
import sys
from typing import Mapping, Sequence

import numpy as np

from .information_transfer_contract import _read_rows
from .refit_information_transfer import RefitInformationLevelScores
from .training_process_confirmatory_v5 import _load_json
from .training_process_external_freeze_v1 import (
    FREEZE_RECEIPT_TYPE,
    MANIFEST_TYPE,
    _canonical_sha256,
    _external_design_rows,
)
from .training_process_freeze_manifest import _file_sha256
from .training_process_managed_generation import (
    _runtime_snapshot,
    _sha256_bytes,
)


MANAGED_SCORING_RECEIPT_TYPE = (
    "odsp_training_process_v5_managed_external_scoring_receipt_v1"
)
MANAGED_SCORE_BUNDLE_TYPE = (
    "odsp_training_process_v5_managed_external_score_bundle_v1"
)


def _text(value: object, *, name: str) -> str:
    if not isinstance(value, str) or not value.strip():
        raise ValueError(f"{name} must be non-empty text")
    return value.strip()


def _sha256_text(value: object, *, name: str) -> str:
    digest = _text(value, name=name).lower()
    if len(digest) != 64:
        raise ValueError(f"{name} must be lowercase SHA256")
    try:
        int(digest, 16)
    except ValueError as exc:
        raise ValueError(f"{name} must be lowercase SHA256") from exc
    return digest


def _safe_score(value: object, *, name: str) -> float:
    if isinstance(value, str):
        if value == "-inf":
            return -math.inf
        raise ValueError(f"{name} string score must be '-inf'")
    if isinstance(value, bool):
        raise ValueError(f"{name} must be numeric or '-inf'")
    try:
        score = float(value)
    except (TypeError, ValueError) as exc:
        raise ValueError(f"{name} must be numeric or '-inf'") from exc
    if math.isnan(score) or score == math.inf:
        raise ValueError(f"{name} must be finite or -inf")
    return score


def _json_score(value: float) -> float | str:
    return "-inf" if value == -math.inf else float(value)


def _freeze_inputs(
    freeze_manifest_path: Path,
    freeze_receipt_path: Path,
) -> tuple[dict[str, object], dict[str, object]]:
    manifest = _load_json(
        freeze_manifest_path, name="external freeze manifest"
    )
    if manifest.get("manifest_type") != MANIFEST_TYPE:
        raise ValueError("external freeze manifest_type is not recognized")
    if manifest.get("schema_version") != 1:
        raise ValueError("external freeze manifest schema_version must be 1")
    receipt = _load_json(
        freeze_receipt_path, name="external freeze receipt"
    )
    if receipt.get("receipt_type") != FREEZE_RECEIPT_TYPE:
        raise ValueError("external freeze receipt_type is not recognized")
    if receipt.get("manifest_sha256") != _file_sha256(freeze_manifest_path):
        raise ValueError("external freeze receipt manifest SHA256 mismatch")
    if receipt.get("external_design_sha256") != manifest.get(
        "external_design_sha256"
    ):
        raise ValueError("external freeze receipt design digest mismatch")
    if receipt.get("managed_generation_receipt_sha256") != manifest.get(
        "managed_generation_receipt_sha256"
    ):
        raise ValueError("external freeze receipt generation digest mismatch")
    return manifest, receipt


def _scoring_plan(manifest: Mapping[str, object]) -> dict[str, object]:
    raw = manifest.get("managed_scoring_plan")
    if not isinstance(raw, Mapping):
        raise ValueError("external freeze is missing managed_scoring_plan")
    required = {
        "working_directory",
        "command",
        "command_artifact_snapshot",
        "timeout_seconds",
        "environment_allowlist",
        "runtime_environment_snapshot",
    }
    if set(raw) != required:
        raise ValueError("managed_scoring_plan fields mismatch")
    command = raw["command"]
    artifacts = raw["command_artifact_snapshot"]
    allowlist = raw["environment_allowlist"]
    if not isinstance(command, list) or not command:
        raise ValueError("managed scoring command must be non-empty")
    if not isinstance(artifacts, list) or not artifacts:
        raise ValueError("managed scoring artifact snapshot must be non-empty")
    if not isinstance(allowlist, list):
        raise ValueError("managed scoring environment_allowlist must be a list")
    timeout = raw["timeout_seconds"]
    if isinstance(timeout, bool) or not isinstance(timeout, int) or timeout < 1:
        raise ValueError("managed scoring timeout_seconds is invalid")
    return dict(raw)


def _verify_scoring_identity(
    plan: Mapping[str, object],
    *,
    freeze_base: Path,
) -> tuple[Path, dict[str, object]]:
    working = Path(str(plan["working_directory"]))
    if not working.is_absolute():
        working = freeze_base / working
    if not working.is_dir():
        raise FileNotFoundError(working)

    current_artifacts: list[dict[str, str]] = []
    for index, item in enumerate(plan["command_artifact_snapshot"]):
        if not isinstance(item, Mapping) or set(item) != {"path", "sha256"}:
            raise ValueError(
                f"managed scoring command_artifact_snapshot[{index}] is invalid"
            )
        relative = _text(item["path"], name="scoring artifact path")
        path = working / relative
        if path.is_symlink() or not path.is_file():
            raise ValueError(
                f"scoring artifact must be a regular non-symlink file: {path}"
            )
        current_artifacts.append(
            {"path": relative, "sha256": _file_sha256(path)}
        )
    if current_artifacts != plan["command_artifact_snapshot"]:
        raise ValueError("scoring command artifact bytes do not match freeze")

    runtime = _runtime_snapshot(plan["environment_allowlist"])
    if runtime != plan["runtime_environment_snapshot"]:
        raise ValueError("scoring runtime environment does not match freeze")
    return working, runtime


def _external_design(
    roster_path: Path,
    *,
    format_name: str,
    manifest: Mapping[str, object],
) -> list[dict[str, object]]:
    rows = _read_rows(roster_path, format_name)
    canonical, block_counts = _external_design_rows(rows)
    if _canonical_sha256(canonical) != manifest.get("external_design_sha256"):
        raise ValueError("external roster design does not match freeze")
    if len(canonical) != manifest.get("external_row_count"):
        raise ValueError("external roster row count does not match freeze")
    if block_counts != manifest.get("positive_block_count_by_group"):
        raise ValueError("external roster block counts do not match freeze")
    return canonical


def _verify_generated_models(
    managed_receipt: Mapping[str, object],
    *,
    generated_model_root: Path,
    frozen_snapshot: object,
) -> dict[str, list[dict[str, str]]]:
    if not isinstance(frozen_snapshot, list) or not frozen_snapshot:
        raise ValueError("frozen generated-model artifact snapshot is invalid")
    expected_by_refit: dict[str, list[dict[str, str]]] = {}
    for item in frozen_snapshot:
        if not isinstance(item, Mapping):
            raise ValueError("frozen generated-model artifact must be an object")
        refit_id = _text(item.get("refit_id"), name="frozen refit_id")
        artifact_id = _text(item.get("artifact_id"), name="frozen artifact_id")
        digest = _sha256_text(item.get("sha256"), name="frozen artifact sha256")
        expected_by_refit.setdefault(refit_id, []).append(
            {
                "artifact_id": artifact_id,
                "sha256": digest,
            }
        )

    executions = managed_receipt.get("executions")
    if not isinstance(executions, list) or not executions:
        raise ValueError("managed generation receipt executions are invalid")
    current: dict[str, list[dict[str, str]]] = {}
    for execution in executions:
        if not isinstance(execution, Mapping):
            raise ValueError("managed generation execution must be an object")
        refit_id = _text(execution.get("refit_id"), name="managed refit_id")
        artifacts = execution.get("artifacts")
        if not isinstance(artifacts, list) or not artifacts:
            raise ValueError("managed model artifacts must be non-empty")
        rows: list[dict[str, str]] = []
        for artifact in artifacts:
            if not isinstance(artifact, Mapping):
                raise ValueError("managed model artifact must be an object")
            artifact_id = _text(
                artifact.get("artifact_id"), name="managed artifact_id"
            )
            relative = _text(
                artifact.get("relative_path"), name="managed artifact relative_path"
            )
            frozen_sha = _sha256_text(
                artifact.get("sha256"), name="managed artifact sha256"
            )
            path = generated_model_root / refit_id / relative
            if path.is_symlink() or not path.is_file():
                raise FileNotFoundError(path)
            current_sha = _file_sha256(path)
            if current_sha != frozen_sha:
                raise ValueError(
                    f"generated model artifact bytes changed for {refit_id}/{artifact_id}"
                )
            rows.append(
                {
                    "artifact_id": artifact_id,
                    "relative_path": relative,
                    "path": str(path.resolve()),
                    "sha256": current_sha,
                }
            )
        rows.sort(key=lambda row: row["artifact_id"])
        current[refit_id] = rows

    expected_ids = set(expected_by_refit)
    if set(current) != expected_ids:
        raise ValueError("generated model refit coverage does not match freeze")
    for refit_id in sorted(expected_ids):
        frozen = sorted(
            expected_by_refit[refit_id], key=lambda row: row["artifact_id"]
        )
        observed = [
            {"artifact_id": row["artifact_id"], "sha256": row["sha256"]}
            for row in current[refit_id]
        ]
        if observed != frozen:
            raise ValueError(
                f"generated model artifact identity mismatch for {refit_id}"
            )
    return current


def _validate_scoring_output(
    path: Path,
    *,
    expected_refit_id: str,
    expected_row_ids: Sequence[str],
    level_names: Sequence[str],
) -> dict[str, dict[str, float]]:
    raw = _load_json(path, name="managed scoring output")
    if set(raw) != {"refit_id", "rows"}:
        raise ValueError("managed scoring output top-level fields are invalid")
    if _text(raw["refit_id"], name="scoring output refit_id") != expected_refit_id:
        raise ValueError("managed scoring output refit_id mismatch")
    rows = raw["rows"]
    if not isinstance(rows, list) or len(rows) != len(expected_row_ids):
        raise ValueError("managed scoring output row coverage is incomplete")
    expected_set = set(expected_row_ids)
    seen: set[str] = set()
    scores: dict[str, dict[str, float]] = {}
    for index, item in enumerate(rows):
        if not isinstance(item, Mapping) or set(item) != {"row_id", "scores"}:
            raise ValueError(f"managed scoring output rows[{index}] is invalid")
        row_id = _text(item["row_id"], name=f"scoring row {index} row_id")
        if row_id in seen:
            raise ValueError("managed scoring output row IDs must be unique")
        seen.add(row_id)
        if row_id not in expected_set:
            raise ValueError("managed scoring output contains unknown row ID")
        raw_scores = item["scores"]
        if not isinstance(raw_scores, Mapping):
            raise ValueError("managed scoring row scores must be an object")
        if set(raw_scores) != set(level_names):
            raise ValueError("managed scoring level keys do not match freeze")
        scores[row_id] = {
            level: _safe_score(
                raw_scores[level],
                name=f"score[{expected_refit_id},{row_id},{level}]",
            )
            for level in level_names
        }
    if seen != expected_set:
        raise ValueError("managed scoring output does not exactly cover frozen rows")
    return scores


def run_managed_external_scoring_v1(
    external_freeze_manifest_path: str | Path,
    external_freeze_receipt_path: str | Path,
    external_roster_path: str | Path,
    *,
    external_roster_format: str,
    managed_generation_receipt_path: str | Path,
    generated_model_root: str | Path,
    validation_data_path: str | Path,
    output_root: str | Path,
    score_bundle_out: str | Path,
    scoring_receipt_out: str | Path,
) -> dict[str, object]:
    """Execute frozen scoring code for every refit and emit a bound score bundle."""

    freeze_manifest_path = Path(external_freeze_manifest_path)
    freeze_receipt_path = Path(external_freeze_receipt_path)
    roster_path = Path(external_roster_path)
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
        if not path.is_file() and path != model_root:
            raise FileNotFoundError(path)
    if not model_root.is_dir():
        raise FileNotFoundError(model_root)

    manifest, _ = _freeze_inputs(
        freeze_manifest_path, freeze_receipt_path
    )
    managed_receipt_sha = _file_sha256(managed_receipt_path)
    if managed_receipt_sha != manifest.get("managed_generation_receipt_sha256"):
        raise ValueError("managed generation receipt does not match external freeze")
    managed_receipt = _load_json(
        managed_receipt_path, name="managed generation receipt"
    )

    format_name = _text(
        external_roster_format, name="external_roster_format"
    ).lower()
    if format_name not in {"csv", "json"}:
        raise ValueError("external_roster_format must be csv or json")
    design = _external_design(
        roster_path, format_name=format_name, manifest=manifest
    )
    row_ids = [str(row["row_id"]) for row in design]

    levels = manifest.get("levels")
    if not isinstance(levels, list) or len(levels) != 3:
        raise ValueError("external freeze levels are invalid")
    level_names = [
        _text(level.get("name"), name=f"levels[{index}].name")
        for index, level in enumerate(levels)
        if isinstance(level, Mapping)
    ]
    if len(level_names) != 3:
        raise ValueError("external freeze level metadata is invalid")

    refit_ids_raw = manifest.get("refit_ids")
    if not isinstance(refit_ids_raw, list) or not refit_ids_raw:
        raise ValueError("external freeze refit_ids are invalid")
    refit_ids = [
        _text(value, name="external freeze refit_id")
        for value in refit_ids_raw
    ]
    models = _verify_generated_models(
        managed_receipt,
        generated_model_root=model_root,
        frozen_snapshot=manifest.get("generated_model_artifact_snapshot"),
    )

    plan = _scoring_plan(manifest)
    working, runtime = _verify_scoring_identity(
        plan, freeze_base=freeze_manifest_path.parent
    )

    output_dir = Path(output_root)
    bundle_path = Path(score_bundle_out)
    receipt_path = Path(scoring_receipt_out)
    if output_dir.exists():
        raise FileExistsError(f"managed scoring output root already exists: {output_dir}")
    if bundle_path.exists():
        raise FileExistsError(f"score bundle already exists: {bundle_path}")
    if receipt_path.exists():
        raise FileExistsError(f"scoring receipt already exists: {receipt_path}")
    output_dir.mkdir(parents=True)
    bundle_path.parent.mkdir(parents=True, exist_ok=True)
    receipt_path.parent.mkdir(parents=True, exist_ok=True)

    scoring_spec = {
        "schema_version": 1,
        "external_dataset_id": manifest.get("external_dataset_id"),
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
    all_scores: dict[str, dict[str, dict[str, float]]] = {}
    executions: list[dict[str, object]] = []

    for refit_id in refit_ids:
        if refit_id not in models:
            raise ValueError(f"generated model missing frozen refit {refit_id}")
        refit_dir = output_dir / refit_id
        refit_dir.mkdir()
        model_manifest_path = refit_dir / "model-manifest.json"
        model_manifest = {
            "schema_version": 1,
            "refit_id": refit_id,
            "artifacts": models[refit_id],
        }
        model_manifest_path.write_text(
            json.dumps(
                model_manifest, indent=2, sort_keys=True, allow_nan=False
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
        for token in plan["command"]:
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
            timeout=int(plan["timeout_seconds"]),
            check=False,
        )
        if completed.returncode != 0:
            raise RuntimeError(
                f"managed external scoring failed for {refit_id} "
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
        "bundle_type": MANAGED_SCORE_BUNDLE_TYPE,
        "external_freeze_manifest_sha256": _file_sha256(freeze_manifest_path),
        "managed_generation_receipt_sha256": managed_receipt_sha,
        "validation_data_sha256": validation_sha,
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
        "receipt_type": MANAGED_SCORING_RECEIPT_TYPE,
        "created_at_utc": created_at,
        "external_freeze_manifest_sha256": _file_sha256(freeze_manifest_path),
        "external_freeze_receipt_sha256": _file_sha256(freeze_receipt_path),
        "managed_generation_receipt_sha256": managed_receipt_sha,
        "validation_data_sha256": validation_sha,
        "external_roster_file_sha256": _file_sha256(roster_path),
        "scoring_spec_sha256": scoring_spec_sha,
        "scoring_command_artifact_snapshot": plan["command_artifact_snapshot"],
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
            "historical_no_prior_external_outcome_access_machine_proven": False,
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


def load_managed_external_score_bundle(
    score_bundle_path: str | Path,
    *,
    expected_bundle_sha256: object,
    expected_external_freeze_manifest_sha256: object,
    expected_managed_generation_receipt_sha256: object,
    expected_validation_data_sha256: object,
) -> tuple[
    tuple[RefitInformationLevelScores, ...],
    tuple[str, ...],
    tuple[str, ...],
    str,
]:
    """Load a managed score bundle and reconstruct v5 level matrices."""

    path = Path(score_bundle_path)
    if not path.is_file():
        raise FileNotFoundError(path)
    if _file_sha256(path) != _sha256_text(
        expected_bundle_sha256, name="expected_bundle_sha256"
    ):
        raise ValueError("managed score bundle SHA256 mismatch")
    raw = _load_json(path, name="managed score bundle")
    required = {
        "schema_version",
        "bundle_type",
        "external_freeze_manifest_sha256",
        "managed_generation_receipt_sha256",
        "validation_data_sha256",
        "refit_ids",
        "row_ids",
        "levels",
        "scores_by_level",
        "canonical_score_tensor_sha256",
    }
    if set(raw) != required:
        raise ValueError("managed score bundle fields mismatch")
    if raw["schema_version"] != 1 or raw["bundle_type"] != MANAGED_SCORE_BUNDLE_TYPE:
        raise ValueError("managed score bundle identity is invalid")
    checks = (
        (
            "external_freeze_manifest_sha256",
            expected_external_freeze_manifest_sha256,
        ),
        (
            "managed_generation_receipt_sha256",
            expected_managed_generation_receipt_sha256,
        ),
        ("validation_data_sha256", expected_validation_data_sha256),
    )
    for field, expected in checks:
        if raw[field] != _sha256_text(expected, name=f"expected {field}"):
            raise ValueError(f"managed score bundle {field} mismatch")

    refit_ids_raw = raw["refit_ids"]
    row_ids_raw = raw["row_ids"]
    levels_raw = raw["levels"]
    scores_raw = raw["scores_by_level"]
    if not isinstance(refit_ids_raw, list) or not refit_ids_raw:
        raise ValueError("managed score bundle refit_ids are invalid")
    if not isinstance(row_ids_raw, list) or not row_ids_raw:
        raise ValueError("managed score bundle row_ids are invalid")
    if not isinstance(levels_raw, list) or len(levels_raw) != 3:
        raise ValueError("managed score bundle levels are invalid")
    if not isinstance(scores_raw, Mapping):
        raise ValueError("managed score bundle scores_by_level is invalid")
    refit_ids = tuple(_text(x, name="bundle refit_id") for x in refit_ids_raw)
    row_ids = tuple(_text(x, name="bundle row_id") for x in row_ids_raw)
    if len(refit_ids) != len(set(refit_ids)) or len(row_ids) != len(set(row_ids)):
        raise ValueError("managed score bundle IDs must be unique")

    levels: list[RefitInformationLevelScores] = []
    level_names: list[str] = []
    canonical_tensor: list[dict[str, object]] = []
    matrix_by_level: dict[str, np.ndarray] = {}

    for index, level in enumerate(levels_raw):
        if not isinstance(level, Mapping) or set(level) != {"name", "information"}:
            raise ValueError("managed score bundle level metadata is invalid")
        name = _text(level["name"], name=f"bundle levels[{index}].name")
        information = level["information"]
        if not isinstance(information, list):
            raise ValueError("managed score bundle information is invalid")
        info = tuple(_text(x, name="bundle information") for x in information)
        raw_matrix = scores_raw.get(name)
        if (
            not isinstance(raw_matrix, list)
            or len(raw_matrix) != len(refit_ids)
        ):
            raise ValueError(f"managed score matrix shape is invalid for {name}")
        matrix = np.empty((len(refit_ids), len(row_ids)), dtype=float)
        for r, row in enumerate(raw_matrix):
            if not isinstance(row, list) or len(row) != len(row_ids):
                raise ValueError(f"managed score matrix row shape is invalid for {name}")
            for c, value in enumerate(row):
                matrix[r, c] = _safe_score(
                    value, name=f"bundle score[{name},{r},{c}]"
                )
        matrix_by_level[name] = matrix
        level_names.append(name)
        levels.append(
            RefitInformationLevelScores(name, info, matrix)
        )

    if set(scores_raw) != set(level_names):
        raise ValueError("managed score bundle level keys do not match level metadata")

    for r, refit_id in enumerate(refit_ids):
        for c, row_id in enumerate(row_ids):
            canonical_tensor.append(
                {
                    "refit_id": refit_id,
                    "row_id": row_id,
                    "scores": {
                        level: _json_score(matrix_by_level[level][r, c])
                        for level in level_names
                    },
                }
            )
    tensor_sha = _canonical_sha256(canonical_tensor)
    if tensor_sha != _sha256_text(
        raw["canonical_score_tensor_sha256"],
        name="canonical_score_tensor_sha256",
    ):
        raise ValueError("managed score bundle canonical tensor digest mismatch")
    return tuple(levels), row_ids, refit_ids, tensor_sha
