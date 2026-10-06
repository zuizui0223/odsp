"""Managed held-out scoring for training-source process v0."""
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
from .training_process_freeze_manifest import _file_sha256
from .training_process_managed_generation import _runtime_snapshot, _sha256_bytes
from .training_source_process_internal_freeze_v0 import (
    FREEZE_RECEIPT_TYPE,
    MANIFEST_TYPE,
    _load_json,
)
from .training_source_process_validation_helpers import (
    _canonical_sha256,
    _nested_model_artifact_snapshot,
    _sha256_text,
    _text,
    _validation_design_rows,
)


SCORING_RECEIPT_TYPE = "odsp_training_source_process_v0_managed_scoring_receipt"
SCORE_BUNDLE_TYPE = "odsp_training_source_process_v0_managed_score_bundle"


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
    manifest_path: Path,
    receipt_path: Path,
) -> tuple[dict[str, object], dict[str, object]]:
    manifest = _load_json(manifest_path, name="source-v0 validation freeze manifest")
    if manifest.get("manifest_type") != MANIFEST_TYPE:
        raise ValueError("source-v0 validation freeze manifest_type is not recognized")
    if manifest.get("schema_version") != 1:
        raise ValueError("source-v0 validation freeze schema_version must be 1")
    receipt = _load_json(receipt_path, name="source-v0 validation freeze receipt")
    if receipt.get("receipt_type") != FREEZE_RECEIPT_TYPE:
        raise ValueError("source-v0 validation freeze receipt_type is not recognized")
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


def _scoring_plan(manifest: Mapping[str, object]) -> dict[str, object]:
    raw = manifest.get("managed_scoring_plan")
    if not isinstance(raw, Mapping):
        raise ValueError("source-v0 freeze is missing managed_scoring_plan")
    required = {
        "working_directory",
        "command",
        "command_artifact_snapshot",
        "timeout_seconds",
        "environment_allowlist",
        "validation_data_format",
        "validation_row_id_column",
        "runtime_environment_snapshot",
    }
    if set(raw) != required:
        raise ValueError("source-v0 managed_scoring_plan fields mismatch")
    return dict(raw)


def _verify_scoring_identity(
    plan: Mapping[str, object],
) -> tuple[Path, dict[str, object]]:
    working = Path(str(plan["working_directory"]))
    if not working.is_dir():
        raise FileNotFoundError(working)
    current_artifacts: list[dict[str, str]] = []
    artifacts = plan["command_artifact_snapshot"]
    if not isinstance(artifacts, list) or not artifacts:
        raise ValueError("source-v0 scoring artifact snapshot is invalid")
    for item in artifacts:
        if not isinstance(item, Mapping) or set(item) != {"path", "sha256"}:
            raise ValueError("source-v0 scoring artifact row is invalid")
        relative = _text(item["path"], name="scoring artifact path")
        path = working / relative
        if path.is_symlink() or not path.is_file():
            raise ValueError(f"scoring artifact must be a regular file: {path}")
        current_artifacts.append(
            {"path": relative, "sha256": _file_sha256(path)}
        )
    if current_artifacts != artifacts:
        raise ValueError("source-v0 scoring code bytes do not match freeze")
    runtime = _runtime_snapshot(plan["environment_allowlist"])
    if runtime != plan["runtime_environment_snapshot"]:
        raise ValueError("source-v0 scoring runtime does not match freeze")
    return working, runtime


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


def _verify_nested_models(
    managed_receipt: Mapping[str, object],
    *,
    generated_model_root: Path,
    frozen_snapshot: object,
) -> dict[tuple[str, str], list[dict[str, str]]]:
    if not isinstance(frozen_snapshot, list) or not frozen_snapshot:
        raise ValueError("frozen nested model artifact snapshot is invalid")
    expected: dict[tuple[str, str], list[dict[str, str]]] = {}
    for item in frozen_snapshot:
        if not isinstance(item, Mapping):
            raise ValueError("frozen nested model artifact must be an object")
        key = (
            _text(item.get("source_draw_id"), name="source_draw_id"),
            _text(item.get("inner_refit_id"), name="inner_refit_id"),
        )
        expected.setdefault(key, []).append(
            {
                "artifact_id": _text(item.get("artifact_id"), name="artifact_id"),
                "sha256": _sha256_text(item.get("sha256"), name="artifact sha256"),
            }
        )

    sources = managed_receipt.get("sources")
    if not isinstance(sources, list) or not sources:
        raise ValueError("managed nested generation sources are invalid")
    current: dict[tuple[str, str], list[dict[str, str]]] = {}
    for source in sources:
        if not isinstance(source, Mapping):
            raise ValueError("managed nested source must be an object")
        source_id = _text(source.get("source_draw_id"), name="source_draw_id")
        executions = source.get("inner_executions")
        if not isinstance(executions, list):
            raise ValueError("managed nested executions are invalid")
        for execution in executions:
            if not isinstance(execution, Mapping):
                raise ValueError("managed nested execution must be an object")
            refit_id = _text(
                execution.get("inner_refit_id"), name="inner_refit_id"
            )
            artifacts = execution.get("artifacts")
            if not isinstance(artifacts, list) or not artifacts:
                raise ValueError("managed nested model artifacts are missing")
            rows: list[dict[str, str]] = []
            for artifact in artifacts:
                if not isinstance(artifact, Mapping):
                    raise ValueError("managed nested model artifact must be an object")
                artifact_id = _text(artifact.get("artifact_id"), name="artifact_id")
                relative = _text(
                    artifact.get("relative_path"), name="artifact relative_path"
                )
                frozen_sha = _sha256_text(
                    artifact.get("sha256"), name="artifact sha256"
                )
                path = generated_model_root / source_id / refit_id / relative
                if path.is_symlink() or not path.is_file():
                    raise FileNotFoundError(path)
                current_sha = _file_sha256(path)
                if current_sha != frozen_sha:
                    raise ValueError(
                        f"nested model bytes changed for {source_id}/{refit_id}/{artifact_id}"
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
            current[(source_id, refit_id)] = rows

    if set(current) != set(expected):
        raise ValueError("nested generated-model coverage does not match freeze")
    for key in sorted(expected):
        frozen = sorted(expected[key], key=lambda row: row["artifact_id"])
        observed = [
            {"artifact_id": row["artifact_id"], "sha256": row["sha256"]}
            for row in current[key]
        ]
        if observed != frozen:
            raise ValueError(
                f"nested generated-model identity mismatch for {key[0]}/{key[1]}"
            )
    return current


def _validate_scoring_output(
    path: Path,
    *,
    expected_source_id: str,
    expected_refit_id: str,
    expected_row_ids: Sequence[str],
    level_names: Sequence[str],
) -> dict[str, dict[str, float]]:
    raw = _load_json(path, name="source-v0 managed scoring output")
    if set(raw) != {"source_draw_id", "inner_refit_id", "rows"}:
        raise ValueError("source-v0 scoring output top-level fields are invalid")
    if _text(raw["source_draw_id"], name="source_draw_id") != expected_source_id:
        raise ValueError("source-v0 scoring output source_draw_id mismatch")
    if _text(raw["inner_refit_id"], name="inner_refit_id") != expected_refit_id:
        raise ValueError("source-v0 scoring output inner_refit_id mismatch")
    rows = raw["rows"]
    if not isinstance(rows, list) or len(rows) != len(expected_row_ids):
        raise ValueError("source-v0 scoring output row coverage is incomplete")
    expected_set = set(expected_row_ids)
    seen: set[str] = set()
    scores: dict[str, dict[str, float]] = {}
    for index, item in enumerate(rows):
        if not isinstance(item, Mapping) or set(item) != {"row_id", "scores"}:
            raise ValueError(f"source-v0 scoring rows[{index}] is invalid")
        row_id = _text(item["row_id"], name=f"row {index} row_id")
        if row_id in seen or row_id not in expected_set:
            raise ValueError("source-v0 scoring output row IDs are invalid")
        seen.add(row_id)
        raw_scores = item["scores"]
        if not isinstance(raw_scores, Mapping) or set(raw_scores) != set(level_names):
            raise ValueError("source-v0 scoring level keys do not match freeze")
        scores[row_id] = {
            level: _safe_score(
                raw_scores[level],
                name=f"score[{expected_source_id},{expected_refit_id},{row_id},{level}]",
            )
            for level in level_names
        }
    if seen != expected_set:
        raise ValueError("source-v0 scoring output does not exactly cover frozen rows")
    return scores


def run_managed_training_source_process_scoring_v0(
    validation_freeze_manifest_path: str | Path,
    validation_freeze_receipt_path: str | Path,
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
    manifest_path = Path(validation_freeze_manifest_path)
    freeze_receipt_path = Path(validation_freeze_receipt_path)
    roster_path = Path(validation_roster_path)
    managed_receipt_path = Path(managed_nested_generation_receipt_path)
    model_root = Path(generated_model_root)
    validation_path = Path(validation_data_path)
    for path in (
        manifest_path,
        freeze_receipt_path,
        roster_path,
        managed_receipt_path,
        validation_path,
    ):
        if not path.is_file():
            raise FileNotFoundError(path)
    if not model_root.is_dir():
        raise FileNotFoundError(model_root)

    manifest, _ = _freeze_inputs(manifest_path, freeze_receipt_path)
    managed_receipt_sha = _file_sha256(managed_receipt_path)
    if managed_receipt_sha != manifest.get(
        "managed_nested_generation_receipt_sha256"
    ):
        raise ValueError("managed nested generation receipt does not match freeze")
    managed_receipt = _load_json(
        managed_receipt_path, name="managed nested generation receipt"
    )

    fmt = _text(validation_roster_format, name="validation_roster_format").lower()
    if fmt not in {"csv", "json"}:
        raise ValueError("validation_roster_format must be csv or json")
    design = _validation_design(roster_path, format_name=fmt, manifest=manifest)
    row_ids = [str(row["row_id"]) for row in design]

    scoring_plan = _scoring_plan(manifest)
    validation_format = _text(
        scoring_plan["validation_data_format"], name="validation_data_format"
    ).lower()
    validation_row_id_column = _text(
        scoring_plan["validation_row_id_column"], name="validation_row_id_column"
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
        raise ValueError("validation data row IDs do not match frozen validation roster")

    levels = manifest.get("levels")
    if not isinstance(levels, list) or len(levels) != 3:
        raise ValueError("source-v0 frozen levels are invalid")
    level_names = [
        _text(level.get("name"), name=f"levels[{index}].name")
        for index, level in enumerate(levels)
        if isinstance(level, Mapping)
    ]
    if len(level_names) != 3:
        raise ValueError("source-v0 frozen level metadata is invalid")

    source_ids = manifest.get("source_draw_ids")
    inner_ids = manifest.get("inner_refit_ids")
    if not isinstance(source_ids, list) or not source_ids:
        raise ValueError("source-v0 source_draw_ids are invalid")
    if not isinstance(inner_ids, list) or not inner_ids:
        raise ValueError("source-v0 inner_refit_ids are invalid")
    source_ids = [_text(x, name="source_draw_id") for x in source_ids]
    inner_ids = [_text(x, name="inner_refit_id") for x in inner_ids]

    working, runtime = _verify_scoring_identity(scoring_plan)
    models = _verify_nested_models(
        managed_receipt,
        generated_model_root=model_root,
        frozen_snapshot=manifest.get("nested_model_artifact_snapshot"),
    )

    output_root = Path(output_root)
    bundle_path = Path(score_bundle_out)
    receipt_path = Path(scoring_receipt_out)
    for path in (output_root, bundle_path, receipt_path):
        if path.exists():
            raise FileExistsError(f"source-v0 managed scoring output exists: {path}")
    output_root.mkdir(parents=True)
    bundle_path.parent.mkdir(parents=True, exist_ok=True)
    receipt_path.parent.mkdir(parents=True, exist_ok=True)

    scoring_spec_path = output_root / "scoring_spec.json"
    scoring_spec = {
        "schema_version": 1,
        "source_process_id": manifest["source_process_id"],
        "row_identity_namespace": manifest["row_identity_namespace"],
        "validation_row_id_column": validation_row_id_column,
        "score": manifest["score"],
        "levels": levels,
    }
    scoring_spec_path.write_text(
        json.dumps(scoring_spec, indent=2, sort_keys=True, allow_nan=False) + "\n",
        encoding="utf-8",
    )

    env = {name: value for name, value in runtime["environment"].items()}
    command = scoring_plan["command"]
    timeout = int(scoring_plan["timeout_seconds"])
    tensor = np.empty(
        (len(source_ids), len(inner_ids), len(row_ids), len(level_names)),
        dtype=float,
    )
    executions: list[dict[str, object]] = []

    for source_index, source_id in enumerate(source_ids):
        for refit_index, refit_id in enumerate(inner_ids):
            key = (source_id, refit_id)
            artifacts = models.get(key)
            if artifacts is None:
                raise ValueError(f"missing nested model for {source_id}/{refit_id}")
            pair_dir = output_root / source_id / refit_id
            pair_dir.mkdir(parents=True)
            model_manifest_path = pair_dir / "model_manifest.json"
            model_manifest_path.write_text(
                json.dumps(
                    {
                        "schema_version": 1,
                        "source_draw_id": source_id,
                        "inner_refit_id": refit_id,
                        "artifacts": artifacts,
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
            for token in command:
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
                timeout=timeout,
                check=False,
            )
            if completed.returncode != 0:
                raise RuntimeError(
                    f"source-v0 scoring failed for {source_id}/{refit_id} "
                    f"with return code {completed.returncode}"
                )
            if not output_path.is_file():
                raise FileNotFoundError(output_path)
            score_rows = _validate_scoring_output(
                output_path,
                expected_source_id=source_id,
                expected_refit_id=refit_id,
                expected_row_ids=row_ids,
                level_names=level_names,
            )
            for row_index, row_id in enumerate(row_ids):
                for level_index, level_name in enumerate(level_names):
                    tensor[source_index, refit_index, row_index, level_index] = (
                        score_rows[row_id][level_name]
                    )
            executions.append(
                {
                    "source_draw_id": source_id,
                    "inner_refit_id": refit_id,
                    "argv": argv,
                    "stdout_sha256": _sha256_bytes(completed.stdout),
                    "stderr_sha256": _sha256_bytes(completed.stderr),
                    "return_code": int(completed.returncode),
                    "score_output_sha256": _file_sha256(output_path),
                }
            )

    canonical_rows: list[dict[str, object]] = []
    for si, source_id in enumerate(source_ids):
        for ri, refit_id in enumerate(inner_ids):
            for row_index, row_id in enumerate(row_ids):
                canonical_rows.append(
                    {
                        "source_draw_id": source_id,
                        "inner_refit_id": refit_id,
                        "row_id": row_id,
                        "scores": {
                            level_name: _json_score(
                                float(tensor[si, ri, row_index, level_index])
                            )
                            for level_index, level_name in enumerate(level_names)
                        },
                    }
                )
    tensor_sha = _canonical_sha256(canonical_rows)
    bundle = {
        "schema_version": 1,
        "bundle_type": SCORE_BUNDLE_TYPE,
        "source_process_id": manifest["source_process_id"],
        "validation_freeze_manifest_sha256": _file_sha256(manifest_path),
        "managed_nested_generation_receipt_sha256": managed_receipt_sha,
        "validation_data_sha256": _file_sha256(validation_path),
        "source_draw_ids": source_ids,
        "inner_refit_ids": inner_ids,
        "row_ids": row_ids,
        "levels": levels,
        "scores": [
            [
                [
                    [
                        _json_score(float(tensor[si, ri, row_index, li]))
                        for li in range(len(level_names))
                    ]
                    for row_index in range(len(row_ids))
                ]
                for ri in range(len(inner_ids))
            ]
            for si in range(len(source_ids))
        ],
        "canonical_score_tensor_sha256": tensor_sha,
    }
    bundle_path.write_text(
        json.dumps(bundle, indent=2, sort_keys=True, allow_nan=False) + "\n",
        encoding="utf-8",
    )
    receipt = {
        "schema_version": 1,
        "receipt_type": SCORING_RECEIPT_TYPE,
        "created_at_utc": (
            datetime.now(timezone.utc)
            .replace(microsecond=0)
            .isoformat()
            .replace("+00:00", "Z")
        ),
        "validation_freeze_manifest_sha256": _file_sha256(manifest_path),
        "validation_freeze_receipt_sha256": _file_sha256(freeze_receipt_path),
        "managed_nested_generation_receipt_sha256": managed_receipt_sha,
        "validation_data_sha256": _file_sha256(validation_path),
        "score_bundle_sha256": _file_sha256(bundle_path),
        "canonical_score_tensor_sha256": tensor_sha,
        "scoring_command_artifact_snapshot": scoring_plan["command_artifact_snapshot"],
        "scoring_runtime_environment_snapshot": runtime,
        "nested_model_artifact_snapshot": manifest["nested_model_artifact_snapshot"],
        "source_draw_count": len(source_ids),
        "inner_refit_count_per_source": len(inner_ids),
        "row_count": len(row_ids),
        "level_names": level_names,
        "execution_count": len(executions),
        "executions": executions,
        "boundaries": {
            "score_tensor_derived_by_managed_scoring": True,
            "nested_model_artifacts_reverified_before_scoring": True,
            "shell_used": False,
            "semantic_correctness_of_scoring_code_cryptographically_proven": False,
        },
    }
    receipt_path.write_text(
        json.dumps(receipt, indent=2, sort_keys=True, allow_nan=False) + "\n",
        encoding="utf-8",
    )
    return {
        "score_bundle_path": str(bundle_path),
        "score_bundle_sha256": _file_sha256(bundle_path),
        "scoring_receipt_path": str(receipt_path),
        "scoring_receipt_sha256": _file_sha256(receipt_path),
        "canonical_score_tensor_sha256": tensor_sha,
        "receipt": receipt,
    }


def load_managed_training_source_score_bundle(
    path: str | Path,
    *,
    expected_bundle_sha256: str,
    expected_validation_freeze_manifest_sha256: str,
    expected_managed_nested_generation_receipt_sha256: str,
    expected_validation_data_sha256: str,
) -> tuple[dict[str, object], np.ndarray]:
    bundle_path = Path(path)
    if _file_sha256(bundle_path) != expected_bundle_sha256:
        raise ValueError("source-v0 score bundle SHA256 mismatch")
    bundle = _load_json(bundle_path, name="source-v0 score bundle")
    if bundle.get("bundle_type") != SCORE_BUNDLE_TYPE:
        raise ValueError("source-v0 score bundle_type is not recognized")
    checks = {
        "validation_freeze_manifest_sha256": expected_validation_freeze_manifest_sha256,
        "managed_nested_generation_receipt_sha256": expected_managed_nested_generation_receipt_sha256,
        "validation_data_sha256": expected_validation_data_sha256,
    }
    for field, expected in checks.items():
        if bundle.get(field) != expected:
            raise ValueError(f"source-v0 score bundle {field} mismatch")
    source_ids = bundle.get("source_draw_ids")
    inner_ids = bundle.get("inner_refit_ids")
    row_ids = bundle.get("row_ids")
    levels = bundle.get("levels")
    scores = bundle.get("scores")
    if not isinstance(source_ids, list) or not isinstance(inner_ids, list):
        raise ValueError("source-v0 score bundle process IDs are invalid")
    if not isinstance(row_ids, list) or not isinstance(levels, list):
        raise ValueError("source-v0 score bundle metadata is invalid")
    array = np.empty(
        (len(source_ids), len(inner_ids), len(row_ids), len(levels)), dtype=float
    )
    if not isinstance(scores, list) or len(scores) != len(source_ids):
        raise ValueError("source-v0 score bundle source axis is invalid")
    canonical_rows: list[dict[str, object]] = []
    level_names = [_text(x["name"], name="level name") for x in levels if isinstance(x, Mapping)]
    if len(level_names) != len(levels):
        raise ValueError("source-v0 score bundle level metadata is invalid")
    for si, source_rows in enumerate(scores):
        if not isinstance(source_rows, list) or len(source_rows) != len(inner_ids):
            raise ValueError("source-v0 score bundle inner axis is invalid")
        for ri, refit_rows in enumerate(source_rows):
            if not isinstance(refit_rows, list) or len(refit_rows) != len(row_ids):
                raise ValueError("source-v0 score bundle row axis is invalid")
            for row_index, raw_scores in enumerate(refit_rows):
                if not isinstance(raw_scores, list) or len(raw_scores) != len(levels):
                    raise ValueError("source-v0 score bundle level axis is invalid")
                score_map: dict[str, float | str] = {}
                for li, raw_score in enumerate(raw_scores):
                    value = _safe_score(
                        raw_score,
                        name=f"bundle score[{si},{ri},{row_index},{li}]",
                    )
                    array[si, ri, row_index, li] = value
                    score_map[level_names[li]] = _json_score(value)
                canonical_rows.append(
                    {
                        "source_draw_id": str(source_ids[si]),
                        "inner_refit_id": str(inner_ids[ri]),
                        "row_id": str(row_ids[row_index]),
                        "scores": score_map,
                    }
                )
    tensor_sha = _canonical_sha256(canonical_rows)
    if tensor_sha != bundle.get("canonical_score_tensor_sha256"):
        raise ValueError("source-v0 score bundle tensor digest mismatch")
    return bundle, array
