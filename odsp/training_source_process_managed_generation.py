"""Managed nested execution for training-source process v0.

For every frozen outer source draw, reconstruct and verify the outer membership.
For every nested inner refit, reconstruct and verify the inner membership before
invoking one frozen fit argv with shell=False. The success receipt preserves the
source -> inner-refit hierarchy and binds all output artifact bytes.
"""
from __future__ import annotations

from datetime import datetime, timezone
import hashlib
import json
import os
from pathlib import Path
import subprocess
import sys
from typing import Mapping

from .training_process_freeze_manifest import _file_sha256
from .training_process_managed_generation import (
    _relative_safe_path,
    _runtime_snapshot,
)
from .training_source_process_freeze_manifest import (
    SOURCE_PROCESS_MANIFEST_TYPE,
    _canonical_roster_and_strata,
    _inner_membership_rows,
    _outer_membership_rows,
)
from .training_process_freeze_manifest import _canonical_sha256


RECEIPT_TYPE = "odsp_training_source_process_managed_generation_receipt_v0"
_PLAN_FIELDS = {
    "schema_version",
    "source_process_id",
    "manifest_path",
    "source_roster",
    "working_directory",
    "command",
    "command_artifacts",
    "timeout_seconds",
    "environment_allowlist",
    "output_artifacts",
}
_ROSTER_FIELDS = {"path", "format", "unit_id_column", "stratum_column"}
_OUTPUT_FIELDS = {"artifact_id", "relative_path"}


def _text(value: object, *, name: str) -> str:
    if not isinstance(value, str) or not value.strip():
        raise ValueError(f"{name} must be non-empty text")
    return value.strip()


def _sha256_bytes(value: bytes) -> str:
    return hashlib.sha256(value).hexdigest()


def _load_json(path: Path, *, name: str) -> dict[str, object]:
    try:
        raw = json.loads(path.read_text(encoding="utf-8"))
    except json.JSONDecodeError as exc:
        raise ValueError(f"{name} is not valid JSON: {path}") from exc
    if not isinstance(raw, Mapping):
        raise ValueError(f"{name} must contain a JSON object")
    return dict(raw)


def validate_training_source_managed_generation_plan(
    raw: Mapping[str, object],
) -> dict[str, object]:
    plan = dict(raw)
    if set(plan) != _PLAN_FIELDS:
        raise ValueError(
            "managed nested-generation plan fields must be exactly "
            + repr(sorted(_PLAN_FIELDS))
        )
    if plan.get("schema_version") != 1 or isinstance(plan.get("schema_version"), bool):
        raise ValueError("managed nested-generation schema_version must be 1")

    roster = plan.get("source_roster")
    if not isinstance(roster, Mapping) or set(roster) != _ROSTER_FIELDS:
        raise ValueError("source_roster fields are invalid")
    roster_format = _text(roster.get("format"), name="source_roster.format").lower()
    if roster_format not in {"csv", "json"}:
        raise ValueError("source_roster.format must be csv or json")
    unit_column = _text(
        roster.get("unit_id_column"), name="source_roster.unit_id_column"
    )
    raw_stratum = roster.get("stratum_column")
    stratum_column = (
        None
        if raw_stratum is None
        else _text(raw_stratum, name="source_roster.stratum_column")
    )
    if stratum_column == unit_column:
        raise ValueError("source roster unit and stratum columns must differ")

    command_raw = plan.get("command")
    if (
        not isinstance(command_raw, list)
        or not command_raw
        or any(not isinstance(x, str) or not x.strip() for x in command_raw)
    ):
        raise ValueError("command must be a non-empty string array")
    command = [str(x) for x in command_raw]
    joined = "\n".join(command)
    for placeholder in (
        "{source_draw_id}",
        "{outer_membership_path}",
        "{inner_refit_id}",
        "{inner_membership_path}",
        "{fit_seed}",
        "{output_dir}",
    ):
        if placeholder not in joined:
            raise ValueError(f"command must contain required placeholder {placeholder}")

    artifacts_raw = plan.get("command_artifacts")
    if not isinstance(artifacts_raw, list) or not artifacts_raw:
        raise ValueError("command_artifacts must be a non-empty array")
    command_artifacts = [
        _relative_safe_path(x, name=f"command_artifacts[{i}]")
        for i, x in enumerate(artifacts_raw)
    ]
    if len(command_artifacts) != len(set(command_artifacts)):
        raise ValueError("command_artifacts must be unique")

    timeout = plan.get("timeout_seconds")
    if isinstance(timeout, bool) or not isinstance(timeout, int) or not 1 <= timeout <= 86400:
        raise ValueError("timeout_seconds must be an integer in [1, 86400]")

    allow_raw = plan.get("environment_allowlist")
    if not isinstance(allow_raw, list):
        raise ValueError("environment_allowlist must be an array")
    allow = [_text(x, name=f"environment_allowlist[{i}]") for i, x in enumerate(allow_raw)]
    if len(allow) != len(set(allow)):
        raise ValueError("environment_allowlist must be unique")

    outputs_raw = plan.get("output_artifacts")
    if not isinstance(outputs_raw, list) or not outputs_raw:
        raise ValueError("output_artifacts must be a non-empty array")
    outputs: list[dict[str, str]] = []
    seen: set[str] = set()
    for i, item in enumerate(outputs_raw):
        if not isinstance(item, Mapping) or set(item) != _OUTPUT_FIELDS:
            raise ValueError(f"output_artifacts[{i}] fields are invalid")
        artifact_id = _text(
            item.get("artifact_id"), name=f"output_artifacts[{i}].artifact_id"
        )
        if artifact_id in seen:
            raise ValueError("output artifact IDs must be unique")
        seen.add(artifact_id)
        outputs.append(
            {
                "artifact_id": artifact_id,
                "relative_path": _relative_safe_path(
                    item.get("relative_path"),
                    name=f"output_artifacts[{i}].relative_path",
                ),
            }
        )

    return {
        "schema_version": 1,
        "source_process_id": _text(
            plan.get("source_process_id"), name="source_process_id"
        ),
        "manifest_path": _text(plan.get("manifest_path"), name="manifest_path"),
        "source_roster": {
            "path": _text(roster.get("path"), name="source_roster.path"),
            "format": roster_format,
            "unit_id_column": unit_column,
            "stratum_column": stratum_column,
        },
        "working_directory": _text(
            plan.get("working_directory"), name="working_directory"
        ),
        "command": command,
        "command_artifacts": command_artifacts,
        "timeout_seconds": int(timeout),
        "environment_allowlist": allow,
        "output_artifacts": outputs,
    }


def run_managed_training_source_process_generation(
    plan_path: str | Path,
    output_root: str | Path,
    receipt_out: str | Path,
) -> dict[str, object]:
    plan_path = Path(plan_path)
    plan = validate_training_source_managed_generation_plan(
        _load_json(plan_path, name="managed nested-generation plan")
    )
    base = plan_path.parent

    manifest_path = Path(str(plan["manifest_path"]))
    if not manifest_path.is_absolute():
        manifest_path = base / manifest_path
    manifest = _load_json(manifest_path, name="training source process manifest")
    if manifest.get("manifest_type") != SOURCE_PROCESS_MANIFEST_TYPE:
        raise ValueError("training source process manifest_type is not recognized")
    if manifest.get("source_process_id") != plan["source_process_id"]:
        raise ValueError("managed plan source_process_id does not match manifest")

    roster_spec = plan["source_roster"]
    assert isinstance(roster_spec, Mapping)
    roster_path = Path(str(roster_spec["path"]))
    if not roster_path.is_absolute():
        roster_path = base / roster_path
    if _file_sha256(roster_path) != manifest["source_roster"]["file_sha256"]:
        raise ValueError("source roster bytes do not match frozen manifest")
    canonical_roster, strata = _canonical_roster_and_strata(
        roster_path,
        roster_format=str(roster_spec["format"]),
        unit_column=str(roster_spec["unit_id_column"]),
        stratum_column=(
            None
            if roster_spec["stratum_column"] is None
            else str(roster_spec["stratum_column"])
        ),
    )
    if _canonical_sha256(canonical_roster) != manifest["source_roster"]["semantic_sha256"]:
        raise ValueError("source roster semantics do not match frozen manifest")

    working_dir = Path(str(plan["working_directory"]))
    if not working_dir.is_absolute():
        working_dir = base / working_dir
    if not working_dir.is_dir():
        raise FileNotFoundError(working_dir)

    command_snapshot: list[dict[str, str]] = []
    for rel in plan["command_artifacts"]:
        path = working_dir / str(rel)
        if path.is_symlink() or not path.is_file():
            raise ValueError(f"command artifact must be a regular file: {path}")
        command_snapshot.append({"path": str(rel), "sha256": _file_sha256(path)})

    output_root = Path(output_root)
    receipt_path = Path(receipt_out)
    if output_root.exists():
        raise FileExistsError(f"managed nested output root already exists: {output_root}")
    if receipt_path.exists():
        raise FileExistsError(f"managed nested receipt already exists: {receipt_path}")
    output_root.mkdir(parents=True)

    runtime = _runtime_snapshot(plan["environment_allowlist"])
    env = {name: value for name, value in runtime["environment"].items()}
    source_receipts: list[dict[str, object]] = []

    schedule = manifest.get("nested_schedule")
    if not isinstance(schedule, list) or len(schedule) != manifest.get("source_draw_count"):
        raise ValueError("manifest nested_schedule is invalid")

    for source_row in schedule:
        if not isinstance(source_row, Mapping):
            raise ValueError("source schedule row must be an object")
        source_id = _text(source_row.get("source_draw_id"), name="source_draw_id")
        outer_seed = int(source_row.get("outer_resample_seed"))
        outer_rows = _outer_membership_rows(strata, seed=outer_seed)
        outer_sha = _canonical_sha256(outer_rows)
        if outer_sha != source_row.get("outer_membership_sha256"):
            raise ValueError(f"outer membership digest mismatch for {source_id}")

        source_dir = output_root / source_id
        source_dir.mkdir()
        outer_path = source_dir / "outer_membership.json"
        outer_path.write_text(
            json.dumps(outer_rows, indent=2, sort_keys=True, allow_nan=False) + "\n",
            encoding="utf-8",
        )

        inner_schedule = source_row.get("inner_refit_schedule")
        if (
            not isinstance(inner_schedule, list)
            or len(inner_schedule) != manifest.get("inner_refit_count_per_source")
        ):
            raise ValueError(f"inner refit schedule is invalid for {source_id}")
        executions: list[dict[str, object]] = []
        for inner_row in inner_schedule:
            if not isinstance(inner_row, Mapping):
                raise ValueError("inner refit schedule row must be an object")
            refit_id = _text(inner_row.get("inner_refit_id"), name="inner_refit_id")
            inner_seed = int(inner_row.get("inner_resample_seed"))
            fit_seed = int(inner_row.get("fit_seed"))
            inner_rows = _inner_membership_rows(
                strata, outer_rows, seed=inner_seed
            )
            inner_sha = _canonical_sha256(inner_rows)
            if inner_sha != inner_row.get("inner_membership_sha256"):
                raise ValueError(
                    f"inner membership digest mismatch for {source_id}/{refit_id}"
                )

            refit_dir = source_dir / refit_id
            refit_dir.mkdir()
            inner_path = refit_dir / "inner_membership.json"
            inner_path.write_text(
                json.dumps(inner_rows, indent=2, sort_keys=True, allow_nan=False) + "\n",
                encoding="utf-8",
            )

            replacements = {
                "{source_draw_id}": source_id,
                "{outer_membership_path}": str(outer_path.resolve()),
                "{inner_refit_id}": refit_id,
                "{inner_membership_path}": str(inner_path.resolve()),
                "{fit_seed}": str(fit_seed),
                "{output_dir}": str(refit_dir.resolve()),
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
                cwd=working_dir,
                env=env,
                shell=False,
                capture_output=True,
                timeout=int(plan["timeout_seconds"]),
                check=False,
            )
            if completed.returncode != 0:
                raise RuntimeError(
                    f"fit failed for {source_id}/{refit_id} with return code "
                    f"{completed.returncode}"
                )

            artifacts: list[dict[str, str]] = []
            for spec in plan["output_artifacts"]:
                path = refit_dir / str(spec["relative_path"])
                if path.is_symlink() or not path.is_file():
                    raise FileNotFoundError(path)
                artifacts.append(
                    {
                        "artifact_id": str(spec["artifact_id"]),
                        "relative_path": str(spec["relative_path"]),
                        "sha256": _file_sha256(path),
                    }
                )
            executions.append(
                {
                    "inner_refit_id": refit_id,
                    "inner_resample_seed": inner_seed,
                    "fit_seed": fit_seed,
                    "inner_membership_semantic_sha256": inner_sha,
                    "inner_membership_file_sha256": _file_sha256(inner_path),
                    "argv": argv,
                    "stdout_sha256": _sha256_bytes(completed.stdout),
                    "stderr_sha256": _sha256_bytes(completed.stderr),
                    "return_code": int(completed.returncode),
                    "artifacts": artifacts,
                }
            )

        source_receipts.append(
            {
                "source_draw_id": source_id,
                "outer_resample_seed": outer_seed,
                "outer_membership_semantic_sha256": outer_sha,
                "outer_membership_file_sha256": _file_sha256(outer_path),
                "inner_refit_count": len(executions),
                "inner_executions": executions,
            }
        )

    created_at = (
        datetime.now(timezone.utc)
        .replace(microsecond=0)
        .isoformat()
        .replace("+00:00", "Z")
    )
    receipt = {
        "schema_version": 1,
        "receipt_type": RECEIPT_TYPE,
        "created_at_utc": created_at,
        "source_process_id": plan["source_process_id"],
        "source_process_manifest_sha256": _file_sha256(manifest_path),
        "managed_nested_generation_plan_sha256": _file_sha256(plan_path),
        "source_roster_file_sha256": _file_sha256(roster_path),
        "command_artifact_snapshot": command_snapshot,
        "fit_environment_snapshot": runtime,
        "source_draw_count": len(source_receipts),
        "inner_refit_count_per_source": int(manifest["inner_refit_count_per_source"]),
        "fit_execution_count": sum(
            int(row["inner_refit_count"]) for row in source_receipts
        ),
        "sources": source_receipts,
        "boundaries": {
            "validation_rows_read": False,
            "validation_outcomes_read": False,
            "shell_used": False,
            "outer_membership_verified_before_inner_generation": True,
            "inner_membership_verified_before_fit": True,
            "source_draws_equally_weighted_in_statistical_target": True,
            "unknown_ecological_superpopulation_inference_claimed": False,
            "semantic_use_of_fit_arguments_cryptographically_proven": False,
        },
    }
    receipt_path.parent.mkdir(parents=True, exist_ok=True)
    receipt_path.write_text(
        json.dumps(receipt, indent=2, sort_keys=True, allow_nan=False) + "\n",
        encoding="utf-8",
    )
    return {
        "receipt_path": str(receipt_path),
        "receipt_sha256": _file_sha256(receipt_path),
        "receipt": receipt,
    }
