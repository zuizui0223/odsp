"""Generic frozen-validation helpers for training-process provenance layers.

This module is used by new managed-internal validation only.  Existing
untouched-external modules deliberately remain unchanged so their frozen source
identity is not rewritten.
"""
from __future__ import annotations

import hashlib
import json
import math
from pathlib import Path
from typing import Mapping, Sequence

from .information_transfer_contract import _validate_score_contract
from .training_process_confirmatory_v5 import _load_json
from .training_process_freeze_manifest import _file_sha256
from .training_process_managed_generation import (
    _relative_safe_path,
    _runtime_snapshot,
)


def _text(value: object, *, name: str) -> str:
    if not isinstance(value, str) or not value.strip():
        raise ValueError(f"{name} must be non-empty text")
    return value.strip()


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


def _integer(value: object, *, name: str, minimum: int) -> int:
    if isinstance(value, bool) or not isinstance(value, int) or value < minimum:
        raise ValueError(f"{name} must be an integer >= {minimum}")
    return int(value)


def _canonical_sha256(value: object) -> str:
    payload = (
        json.dumps(
            value,
            ensure_ascii=False,
            sort_keys=True,
            separators=(",", ":"),
            allow_nan=False,
        )
        + "\n"
    )
    return hashlib.sha256(payload.encode("utf-8")).hexdigest()


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


def _normalize_score(raw: object) -> dict[str, object]:
    return _validate_score_contract(raw)


def _normalize_levels(raw: object) -> list[dict[str, object]]:
    if not isinstance(raw, list) or len(raw) != 3:
        raise ValueError(
            "managed internal v5 levels must contain exactly three ordered levels"
        )
    levels: list[dict[str, object]] = []
    names: set[str] = set()
    for index, item in enumerate(raw):
        if not isinstance(item, Mapping) or set(item) != {"name", "information"}:
            raise ValueError(f"levels[{index}] fields are invalid")
        name = _text(item["name"], name=f"levels[{index}].name")
        if name in names:
            raise ValueError("level names must be unique")
        names.add(name)
        info_raw = item["information"]
        if not isinstance(info_raw, list):
            raise ValueError(f"levels[{index}].information must be a JSON array")
        info = [
            _text(value, name=f"levels[{index}].information")
            for value in info_raw
        ]
        if len(info) != len(set(info)):
            raise ValueError("information labels within a level must be unique")
        levels.append({"name": name, "information": info})
    for lower, upper in zip(levels, levels[1:]):
        if not set(lower["information"]).issubset(set(upper["information"])):
            raise ValueError("levels must form an ordered information filtration")
    return levels


def _normalize_certification(raw: object) -> dict[str, object]:
    required = {
        "component_one_sided_alpha",
        "minimum_refits",
        "minimum_blocks_per_group",
        "gain_tolerance",
    }
    if not isinstance(raw, Mapping) or set(raw) != required:
        raise ValueError("certification fields are invalid")
    alpha = _number(
        raw["component_one_sided_alpha"],
        name="component_one_sided_alpha",
    )
    if not 0.0 < alpha < 0.5:
        raise ValueError("component_one_sided_alpha must lie in (0, 0.5)")
    tolerance = _number(raw["gain_tolerance"], name="gain_tolerance")
    if tolerance < 0:
        raise ValueError("gain_tolerance must be non-negative")
    return {
        "component_one_sided_alpha": alpha,
        "minimum_refits": _integer(
            raw["minimum_refits"], name="minimum_refits", minimum=8
        ),
        "minimum_blocks_per_group": _integer(
            raw["minimum_blocks_per_group"],
            name="minimum_blocks_per_group",
            minimum=8,
        ),
        "gain_tolerance": tolerance,
    }


def _normalize_scoring(raw: object) -> dict[str, object]:
    required = {
        "working_directory",
        "command",
        "command_artifacts",
        "timeout_seconds",
        "environment_allowlist",
        "validation_data_format",
        "validation_row_id_column",
    }
    if not isinstance(raw, Mapping) or set(raw) != required:
        raise ValueError("scoring fields are invalid")
    working_directory = _text(
        raw["working_directory"], name="scoring.working_directory"
    )
    command_raw = raw["command"]
    if (
        not isinstance(command_raw, list)
        or not command_raw
        or any(not isinstance(value, str) or not value.strip() for value in command_raw)
    ):
        raise ValueError("scoring.command must be a non-empty JSON string array")
    command = [str(value) for value in command_raw]
    joined = "\n".join(command)
    for placeholder in (
        "{refit_id}",
        "{model_manifest_path}",
        "{validation_data_path}",
        "{scoring_spec_path}",
        "{output_path}",
    ):
        if placeholder not in joined:
            raise ValueError(
                f"scoring.command must contain required placeholder {placeholder}"
            )
    artifacts_raw = raw["command_artifacts"]
    if not isinstance(artifacts_raw, list) or not artifacts_raw:
        raise ValueError("scoring.command_artifacts must be non-empty")
    artifacts = [
        _relative_safe_path(
            value, name=f"scoring.command_artifacts[{index}]"
        )
        for index, value in enumerate(artifacts_raw)
    ]
    if len(artifacts) != len(set(artifacts)):
        raise ValueError("scoring.command_artifacts must be unique")
    timeout = raw["timeout_seconds"]
    if (
        isinstance(timeout, bool)
        or not isinstance(timeout, int)
        or not 1 <= timeout <= 86400
    ):
        raise ValueError("scoring.timeout_seconds must be an integer in [1, 86400]")
    format_name = _text(
        raw["validation_data_format"],
        name="scoring.validation_data_format",
    ).lower()
    if format_name not in {"csv", "json"}:
        raise ValueError("scoring.validation_data_format must be csv or json")
    row_id_column = _text(
        raw["validation_row_id_column"],
        name="scoring.validation_row_id_column",
    )
    allowlist_raw = raw["environment_allowlist"]
    if not isinstance(allowlist_raw, list):
        raise ValueError("scoring.environment_allowlist must be a JSON array")
    allowlist = [
        _text(value, name=f"scoring.environment_allowlist[{index}]")
        for index, value in enumerate(allowlist_raw)
    ]
    if len(allowlist) != len(set(allowlist)):
        raise ValueError("scoring.environment_allowlist must be unique")
    return {
        "working_directory": working_directory,
        "command": command,
        "command_artifacts": artifacts,
        "timeout_seconds": int(timeout),
        "environment_allowlist": allowlist,
        "validation_data_format": format_name,
        "validation_row_id_column": row_id_column,
    }


def _validation_design_rows(
    rows: Sequence[Mapping[str, object]],
) -> tuple[list[dict[str, object]], dict[str, int]]:
    expected = {"row_id", "group_id", "block_id", "sample_weight"}
    canonical: list[dict[str, object]] = []
    seen: set[str] = set()
    positive_blocks: dict[str, set[str]] = {}
    positive_group_mass: dict[str, float] = {}
    for index, row in enumerate(rows):
        if set(row) != expected:
            raise ValueError(
                "pre-outcome validation roster must contain exactly "
                "row_id, group_id, block_id, sample_weight"
            )
        row_id = _text(row["row_id"], name=f"roster row {index} row_id")
        group_id = _text(row["group_id"], name=f"roster row {index} group_id")
        block_id = _text(row["block_id"], name=f"roster row {index} block_id")
        if row_id in seen:
            raise ValueError("validation row IDs must be unique")
        seen.add(row_id)
        weight = _number(
            row["sample_weight"], name=f"roster row {index} sample_weight"
        )
        if weight < 0:
            raise ValueError("sample weights must be non-negative")
        canonical.append(
            {
                "row_id": row_id,
                "group_id": group_id,
                "block_id": block_id,
                "sample_weight": weight,
            }
        )
        if weight > 0:
            positive_blocks.setdefault(group_id, set()).add(block_id)
            positive_group_mass[group_id] = (
                positive_group_mass.get(group_id, 0.0) + weight
            )
    if not canonical:
        raise ValueError("validation roster must not be empty")
    if not positive_group_mass:
        raise ValueError("validation roster has no positive-weight support")
    canonical.sort(key=lambda row: str(row["row_id"]))
    block_counts = {
        group: len(positive_blocks[group])
        for group in sorted(positive_blocks)
    }
    return canonical, block_counts


def _model_artifact_snapshot(
    receipt: Mapping[str, object],
) -> list[dict[str, str]]:
    executions = receipt.get("executions")
    if not isinstance(executions, list) or not executions:
        raise ValueError("managed receipt executions must be non-empty")
    rows: list[dict[str, str]] = []
    for execution in executions:
        if not isinstance(execution, Mapping):
            raise ValueError("managed execution must be an object")
        refit_id = _text(execution.get("refit_id"), name="managed refit_id")
        artifacts = execution.get("artifacts")
        if not isinstance(artifacts, list) or not artifacts:
            raise ValueError("managed execution artifacts must be non-empty")
        for artifact in artifacts:
            if not isinstance(artifact, Mapping):
                raise ValueError("managed artifact must be an object")
            artifact_id = _text(
                artifact.get("artifact_id"), name="artifact_id"
            )
            digest = _sha256_text(
                artifact.get("sha256"), name="artifact sha256"
            )
            rows.append(
                {
                    "refit_id": refit_id,
                    "artifact_id": artifact_id,
                    "sha256": digest,
                }
            )
    rows.sort(key=lambda row: (row["refit_id"], row["artifact_id"]))
    return rows


def _scoring_plan(manifest: Mapping[str, object]) -> dict[str, object]:
    raw = manifest.get("managed_scoring_plan")
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
    if not isinstance(raw, Mapping) or set(raw) != required:
        raise ValueError("managed_scoring_plan fields mismatch")
    if not isinstance(raw["command"], list) or not raw["command"]:
        raise ValueError("managed scoring command must be non-empty")
    if (
        not isinstance(raw["command_artifact_snapshot"], list)
        or not raw["command_artifact_snapshot"]
    ):
        raise ValueError("managed scoring artifact snapshot must be non-empty")
    if not isinstance(raw["environment_allowlist"], list):
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


def _verify_generated_models(
    managed_receipt: Mapping[str, object],
    *,
    generated_model_root: Path,
    frozen_snapshot: object,
) -> dict[str, list[dict[str, str]]]:
    if not isinstance(frozen_snapshot, list) or not frozen_snapshot:
        raise ValueError("frozen generated-model artifact snapshot is invalid")
    expected: dict[str, list[dict[str, str]]] = {}
    for item in frozen_snapshot:
        if not isinstance(item, Mapping):
            raise ValueError("frozen generated-model artifact must be an object")
        refit_id = _text(item.get("refit_id"), name="frozen refit_id")
        artifact_id = _text(item.get("artifact_id"), name="frozen artifact_id")
        digest = _sha256_text(
            item.get("sha256"), name="frozen artifact sha256"
        )
        expected.setdefault(refit_id, []).append(
            {"artifact_id": artifact_id, "sha256": digest}
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
                artifact.get("relative_path"),
                name="managed artifact relative_path",
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
                    "generated model artifact bytes changed for "
                    f"{refit_id}/{artifact_id}"
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

    if set(current) != set(expected):
        raise ValueError("generated model refit coverage does not match freeze")
    for refit_id in sorted(expected):
        frozen = sorted(expected[refit_id], key=lambda row: row["artifact_id"])
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
