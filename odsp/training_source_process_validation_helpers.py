"""Shared validation/provenance helpers for training-source process v0."""
from __future__ import annotations

import hashlib
import json
import math
from pathlib import Path
from typing import Mapping, Sequence

from .information_transfer_contract import _validate_score_contract
from .training_process_freeze_manifest import _file_sha256
from .training_source_process_managed_generation import RECEIPT_TYPE


def _text(value: object, *, name: str) -> str:
    if not isinstance(value, str) or not value.strip():
        raise ValueError(f"{name} must be non-empty text")
    return value.strip()


def _number(value: object, *, name: str) -> float:
    if isinstance(value, bool):
        raise ValueError(f"{name} must be numeric")
    try:
        result = float(value)
    except (TypeError, ValueError) as exc:
        raise ValueError(f"{name} must be numeric") from exc
    if not math.isfinite(result):
        raise ValueError(f"{name} must be finite")
    return result


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


def _normalize_score(raw: object) -> dict[str, object]:
    return _validate_score_contract(raw)


def _normalize_levels(raw: object) -> list[dict[str, object]]:
    if not isinstance(raw, list) or len(raw) != 3:
        raise ValueError("source-v0 levels must contain exactly three ordered levels")
    rows: list[dict[str, object]] = []
    seen: set[str] = set()
    for index, item in enumerate(raw):
        if not isinstance(item, Mapping) or set(item) != {"name", "information"}:
            raise ValueError(f"levels[{index}] fields are invalid")
        name = _text(item["name"], name=f"levels[{index}].name")
        if name in seen:
            raise ValueError("level names must be unique")
        seen.add(name)
        info = item["information"]
        if not isinstance(info, list):
            raise ValueError(f"levels[{index}].information must be a JSON array")
        values = [_text(x, name=f"levels[{index}].information") for x in info]
        if len(values) != len(set(values)):
            raise ValueError("information labels within a level must be unique")
        rows.append({"name": name, "information": values})
    for lower, upper in zip(rows, rows[1:]):
        if not set(lower["information"]).issubset(set(upper["information"])):
            raise ValueError("levels must form an ordered information filtration")
    return rows


def _normalize_certification(raw: object) -> dict[str, object]:
    fields = {
        "component_one_sided_alpha",
        "minimum_source_draws",
        "minimum_inner_refits_per_source",
        "minimum_blocks_per_group",
        "gain_tolerance",
    }
    if not isinstance(raw, Mapping) or set(raw) != fields:
        raise ValueError("source-v0 certification fields are invalid")
    alpha = _number(raw["component_one_sided_alpha"], name="component_one_sided_alpha")
    if not 0 < alpha < 0.5:
        raise ValueError("component_one_sided_alpha must lie in (0, 0.5)")
    tolerance = _number(raw["gain_tolerance"], name="gain_tolerance")
    if tolerance < 0:
        raise ValueError("gain_tolerance must be non-negative")
    return {
        "component_one_sided_alpha": alpha,
        "minimum_source_draws": _integer(
            raw["minimum_source_draws"], name="minimum_source_draws", minimum=8
        ),
        "minimum_inner_refits_per_source": _integer(
            raw["minimum_inner_refits_per_source"],
            name="minimum_inner_refits_per_source",
            minimum=8,
        ),
        "minimum_blocks_per_group": _integer(
            raw["minimum_blocks_per_group"],
            name="minimum_blocks_per_group",
            minimum=8,
        ),
        "gain_tolerance": tolerance,
    }


def _normalize_scoring(raw: object) -> dict[str, object]:
    fields = {
        "working_directory",
        "command",
        "command_artifacts",
        "timeout_seconds",
        "environment_allowlist",
        "validation_data_format",
        "validation_row_id_column",
    }
    if not isinstance(raw, Mapping) or set(raw) != fields:
        raise ValueError("source-v0 scoring fields are invalid")
    command = raw["command"]
    if (
        not isinstance(command, list)
        or not command
        or any(not isinstance(x, str) or not x.strip() for x in command)
    ):
        raise ValueError("scoring.command must be a non-empty string array")
    joined = "\n".join(command)
    for placeholder in (
        "{source_draw_id}",
        "{inner_refit_id}",
        "{model_manifest_path}",
        "{validation_data_path}",
        "{scoring_spec_path}",
        "{output_path}",
    ):
        if placeholder not in joined:
            raise ValueError(f"scoring.command must contain {placeholder}")
    artifacts = raw["command_artifacts"]
    if not isinstance(artifacts, list) or not artifacts:
        raise ValueError("scoring.command_artifacts must be non-empty")
    artifact_names = [_text(x, name="scoring.command_artifact") for x in artifacts]
    if len(artifact_names) != len(set(artifact_names)):
        raise ValueError("scoring.command_artifacts must be unique")
    timeout = _integer(raw["timeout_seconds"], name="timeout_seconds", minimum=1)
    if timeout > 86400:
        raise ValueError("timeout_seconds must be <= 86400")
    allow = raw["environment_allowlist"]
    if not isinstance(allow, list):
        raise ValueError("environment_allowlist must be a JSON array")
    allow_names = [_text(x, name="environment_allowlist") for x in allow]
    if len(allow_names) != len(set(allow_names)):
        raise ValueError("environment_allowlist must be unique")
    fmt = _text(raw["validation_data_format"], name="validation_data_format").lower()
    if fmt not in {"csv", "json"}:
        raise ValueError("validation_data_format must be csv or json")
    return {
        "working_directory": _text(
            raw["working_directory"], name="scoring.working_directory"
        ),
        "command": [str(x) for x in command],
        "command_artifacts": artifact_names,
        "timeout_seconds": timeout,
        "environment_allowlist": allow_names,
        "validation_data_format": fmt,
        "validation_row_id_column": _text(
            raw["validation_row_id_column"], name="validation_row_id_column"
        ),
    }


def _validation_design_rows(
    rows: Sequence[Mapping[str, object]],
) -> tuple[list[dict[str, object]], dict[str, int]]:
    expected = {"row_id", "group_id", "block_id", "sample_weight"}
    canonical: list[dict[str, object]] = []
    seen: set[str] = set()
    positive_blocks: dict[str, set[str]] = {}
    positive_mass: dict[str, float] = {}
    for index, row in enumerate(rows):
        if set(row) != expected:
            raise ValueError(
                "validation roster must contain exactly row_id, group_id, "
                "block_id, sample_weight"
            )
        row_id = _text(row["row_id"], name=f"validation row {index} row_id")
        group_id = _text(row["group_id"], name=f"validation row {index} group_id")
        block_id = _text(row["block_id"], name=f"validation row {index} block_id")
        if row_id in seen:
            raise ValueError("validation row IDs must be unique")
        seen.add(row_id)
        weight = _number(
            row["sample_weight"], name=f"validation row {index} sample_weight"
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
            positive_mass[group_id] = positive_mass.get(group_id, 0.0) + weight
    if not canonical:
        raise ValueError("validation roster must not be empty")
    if not positive_mass:
        raise ValueError("validation roster has no positive-weight support")
    canonical.sort(key=lambda row: str(row["row_id"]))
    return canonical, {
        group: len(positive_blocks[group]) for group in sorted(positive_blocks)
    }


def _verify_managed_nested_receipt(
    receipt: Mapping[str, object],
    *,
    receipt_sha256: str,
    source_process_id: str,
    manifest_sha256: str,
    manifest: Mapping[str, object],
) -> None:
    if receipt.get("receipt_type") != RECEIPT_TYPE:
        raise ValueError("managed nested generation receipt_type is not recognized")
    if receipt.get("source_process_id") != source_process_id:
        raise ValueError("managed nested generation source_process_id mismatch")
    if receipt.get("source_process_manifest_sha256") != manifest_sha256:
        raise ValueError("managed nested generation manifest digest mismatch")
    source_ids = manifest.get("source_draw_ids")
    inner_ids = manifest.get("inner_refit_ids")
    schedule = manifest.get("nested_schedule")
    if not isinstance(source_ids, list) or not isinstance(inner_ids, list):
        raise ValueError("source-process manifest IDs are invalid")
    if not isinstance(schedule, list) or len(schedule) != len(source_ids):
        raise ValueError("source-process manifest schedule is invalid")
    if receipt.get("source_draw_count") != len(source_ids):
        raise ValueError("managed nested generation source count mismatch")
    if receipt.get("inner_refit_count_per_source") != len(inner_ids):
        raise ValueError("managed nested generation inner count mismatch")
    sources = receipt.get("sources")
    if not isinstance(sources, list) or len(sources) != len(source_ids):
        raise ValueError("managed nested generation source coverage mismatch")
    if receipt.get("fit_execution_count") != len(source_ids) * len(inner_ids):
        raise ValueError("managed nested generation execution count mismatch")

    for frozen_source, observed_source in zip(schedule, sources):
        if not isinstance(frozen_source, Mapping) or not isinstance(observed_source, Mapping):
            raise ValueError("nested source schedule/receipt row must be an object")
        for field in ("source_draw_id", "outer_resample_seed"):
            if observed_source.get(field) != frozen_source.get(field):
                raise ValueError(f"managed nested generation {field} mismatch")
        if observed_source.get("outer_membership_semantic_sha256") != frozen_source.get(
            "outer_membership_sha256"
        ):
            raise ValueError("managed nested outer membership digest mismatch")
        inner_schedule = frozen_source.get("inner_refit_schedule")
        executions = observed_source.get("inner_executions")
        if not isinstance(inner_schedule, list) or not isinstance(executions, list):
            raise ValueError("nested inner schedule/receipt is invalid")
        if len(executions) != len(inner_ids):
            raise ValueError("managed nested inner execution coverage mismatch")
        for frozen_inner, observed_inner in zip(inner_schedule, executions):
            if not isinstance(frozen_inner, Mapping) or not isinstance(observed_inner, Mapping):
                raise ValueError("nested inner row must be an object")
            for field in ("inner_refit_id", "inner_resample_seed", "fit_seed"):
                if observed_inner.get(field) != frozen_inner.get(field):
                    raise ValueError(f"managed nested generation {field} mismatch")
            if observed_inner.get(
                "inner_membership_semantic_sha256"
            ) != frozen_inner.get("inner_membership_sha256"):
                raise ValueError("managed nested inner membership digest mismatch")
            if observed_inner.get("return_code") != 0:
                raise ValueError("managed nested fit has nonzero return code")
            artifacts = observed_inner.get("artifacts")
            if not isinstance(artifacts, list) or not artifacts:
                raise ValueError("managed nested model artifacts are missing")
            for artifact in artifacts:
                if not isinstance(artifact, Mapping):
                    raise ValueError("managed nested model artifact must be an object")
                _text(artifact.get("artifact_id"), name="artifact_id")
                _text(artifact.get("relative_path"), name="artifact relative_path")
                _sha256_text(artifact.get("sha256"), name="artifact sha256")

    boundaries = receipt.get("boundaries")
    if not isinstance(boundaries, Mapping):
        raise ValueError("managed nested generation boundaries are invalid")
    if boundaries.get("shell_used") is not False:
        raise ValueError("managed nested generation must report shell_used=false")
    if boundaries.get("outer_membership_verified_before_inner_generation") is not True:
        raise ValueError("outer membership was not verified before nested generation")
    if boundaries.get("inner_membership_verified_before_fit") is not True:
        raise ValueError("inner membership was not verified before fit")
    _sha256_text(receipt_sha256, name="managed nested receipt sha256")


def _nested_model_artifact_snapshot(
    receipt: Mapping[str, object],
) -> list[dict[str, str]]:
    sources = receipt.get("sources")
    if not isinstance(sources, list) or not sources:
        raise ValueError("managed nested generation sources are invalid")
    rows: list[dict[str, str]] = []
    for source in sources:
        if not isinstance(source, Mapping):
            raise ValueError("managed nested source must be an object")
        source_id = _text(source.get("source_draw_id"), name="source_draw_id")
        executions = source.get("inner_executions")
        if not isinstance(executions, list):
            raise ValueError("managed nested inner executions are invalid")
        for execution in executions:
            if not isinstance(execution, Mapping):
                raise ValueError("managed nested execution must be an object")
            refit_id = _text(execution.get("inner_refit_id"), name="inner_refit_id")
            artifacts = execution.get("artifacts")
            if not isinstance(artifacts, list):
                raise ValueError("managed nested artifacts are invalid")
            for artifact in artifacts:
                if not isinstance(artifact, Mapping):
                    raise ValueError("managed nested artifact must be an object")
                rows.append(
                    {
                        "source_draw_id": source_id,
                        "inner_refit_id": refit_id,
                        "artifact_id": _text(
                            artifact.get("artifact_id"), name="artifact_id"
                        ),
                        "sha256": _sha256_text(
                            artifact.get("sha256"), name="artifact sha256"
                        ),
                    }
                )
    rows.sort(
        key=lambda row: (
            row["source_draw_id"],
            row["inner_refit_id"],
            row["artifact_id"],
        )
    )
    return rows


def _file_digest(path: str | Path) -> str:
    return _file_sha256(Path(path))
