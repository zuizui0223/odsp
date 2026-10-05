"""Managed execution of frozen training-process refits.

The runner reconstructs each bootstrap membership from the frozen process
manifest, verifies its precommitted digest, invokes an argv-array command with
shell execution disabled, and binds the produced artifact bytes to an execution
and environment receipt. Validation outcomes are not inputs.
"""
from __future__ import annotations

from datetime import datetime, timezone
import hashlib
from importlib import metadata
import json
import os
from pathlib import Path
import subprocess
import sys
from typing import Mapping, Sequence

import numpy as np

from .information_transfer_contract import _read_rows
from .training_process_freeze_manifest import (
    PROCESS_MANIFEST_TYPE,
    _canonical_sha256,
    _file_sha256,
)


MANAGED_GENERATION_RECEIPT_TYPE = "odsp_training_process_managed_generation_receipt_v1"
_PLAN_FIELDS = {
    "schema_version",
    "training_process_id",
    "manifest_path",
    "training_roster",
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
        value = json.loads(path.read_text(encoding="utf-8"))
    except json.JSONDecodeError as exc:
        raise ValueError(f"{name} is not valid JSON: {path}") from exc
    if not isinstance(value, Mapping):
        raise ValueError(f"{name} must contain a JSON object")
    return dict(value)


def _relative_safe_path(value: object, *, name: str) -> str:
    text = _text(value, name=name)
    path = Path(text)
    if path.is_absolute() or ".." in path.parts:
        raise ValueError(f"{name} must be a safe relative path")
    return path.as_posix()


def validate_managed_generation_plan(raw: Mapping[str, object]) -> dict[str, object]:
    plan = dict(raw)
    if set(plan) != _PLAN_FIELDS:
        raise ValueError(
            "managed generation plan fields must be exactly "
            + repr(sorted(_PLAN_FIELDS))
        )
    if plan.get("schema_version") != 1 or isinstance(plan.get("schema_version"), bool):
        raise ValueError("managed generation plan schema_version must be 1")
    process_id = _text(plan.get("training_process_id"), name="training_process_id")
    manifest_path = _text(plan.get("manifest_path"), name="manifest_path")

    roster = plan.get("training_roster")
    if not isinstance(roster, Mapping) or set(roster) != _ROSTER_FIELDS:
        raise ValueError("training_roster fields are invalid")
    roster_path = _text(roster.get("path"), name="training_roster.path")
    roster_format = _text(roster.get("format"), name="training_roster.format").lower()
    if roster_format not in {"csv", "json"}:
        raise ValueError("training_roster.format must be 'csv' or 'json'")
    unit_id_column = _text(
        roster.get("unit_id_column"), name="training_roster.unit_id_column"
    )
    stratum_raw = roster.get("stratum_column")
    stratum_column = (
        None
        if stratum_raw is None
        else _text(stratum_raw, name="training_roster.stratum_column")
    )
    if stratum_column == unit_id_column:
        raise ValueError("unit and stratum columns must differ")

    working_directory = _text(
        plan.get("working_directory"), name="working_directory"
    )

    command_raw = plan.get("command")
    if (
        not isinstance(command_raw, list)
        or not command_raw
        or any(not isinstance(x, str) or not x.strip() for x in command_raw)
    ):
        raise ValueError("command must be a non-empty JSON array of non-empty strings")
    command = [str(x) for x in command_raw]
    joined = "\n".join(command)
    for placeholder in (
        "{refit_id}",
        "{membership_path}",
        "{fit_seed}",
        "{output_dir}",
    ):
        if placeholder not in joined:
            raise ValueError(f"command must contain required placeholder {placeholder}")

    artifacts_raw = plan.get("command_artifacts")
    if not isinstance(artifacts_raw, list) or not artifacts_raw:
        raise ValueError("command_artifacts must be a non-empty JSON array")
    command_artifacts = [
        _relative_safe_path(x, name=f"command_artifacts[{i}]")
        for i, x in enumerate(artifacts_raw)
    ]
    if len(command_artifacts) != len(set(command_artifacts)):
        raise ValueError("command_artifacts must be unique")

    timeout = plan.get("timeout_seconds")
    if isinstance(timeout, bool) or not isinstance(timeout, int) or not 1 <= timeout <= 86400:
        raise ValueError("timeout_seconds must be an integer in [1, 86400]")

    env_raw = plan.get("environment_allowlist")
    if not isinstance(env_raw, list):
        raise ValueError("environment_allowlist must be a JSON array")
    env = [_text(x, name=f"environment_allowlist[{i}]") for i, x in enumerate(env_raw)]
    if len(env) != len(set(env)):
        raise ValueError("environment_allowlist must be unique")

    outputs_raw = plan.get("output_artifacts")
    if not isinstance(outputs_raw, list) or not outputs_raw:
        raise ValueError("output_artifacts must be a non-empty JSON array")
    outputs: list[dict[str, str]] = []
    seen_output_ids: set[str] = set()
    for i, raw_output in enumerate(outputs_raw):
        if not isinstance(raw_output, Mapping) or set(raw_output) != _OUTPUT_FIELDS:
            raise ValueError(f"output_artifacts[{i}] fields are invalid")
        artifact_id = _text(
            raw_output.get("artifact_id"), name=f"output_artifacts[{i}].artifact_id"
        )
        if artifact_id in seen_output_ids:
            raise ValueError("output artifact IDs must be unique")
        seen_output_ids.add(artifact_id)
        outputs.append(
            {
                "artifact_id": artifact_id,
                "relative_path": _relative_safe_path(
                    raw_output.get("relative_path"),
                    name=f"output_artifacts[{i}].relative_path",
                ),
            }
        )

    return {
        "schema_version": 1,
        "training_process_id": process_id,
        "manifest_path": manifest_path,
        "training_roster": {
            "path": roster_path,
            "format": roster_format,
            "unit_id_column": unit_id_column,
            "stratum_column": stratum_column,
        },
        "working_directory": working_directory,
        "command": command,
        "command_artifacts": command_artifacts,
        "timeout_seconds": int(timeout),
        "environment_allowlist": env,
        "output_artifacts": outputs,
    }


def _runtime_snapshot(allowlist: Sequence[str]) -> dict[str, object]:
    distributions: list[dict[str, str]] = []
    for dist in metadata.distributions():
        name = str(dist.metadata.get("Name") or "").strip().lower().replace("_", "-")
        if not name:
            continue
        distributions.append(
            {"name": name, "version": str(dist.version).strip()}
        )
    unique: dict[str, str] = {}
    for row in distributions:
        unique[row["name"]] = row["version"]
    env = {
        name: os.environ[name]
        for name in sorted(set(allowlist) | {"PATH"})
        if name in os.environ
    }
    return {
        "python": {
            "implementation": str(sys.implementation.name),
            "major": int(sys.version_info.major),
            "minor": int(sys.version_info.minor),
            "micro": int(sys.version_info.micro),
            "executable_sha256": _file_sha256(Path(sys.executable)),
        },
        "distributions": [
            {"name": name, "version": unique[name]}
            for name in sorted(unique)
        ],
        "environment": env,
    }


def _roster_strata(
    roster_path: Path,
    roster_spec: Mapping[str, object],
    frozen_snapshot: Mapping[str, object],
) -> dict[str, tuple[str, ...]]:
    if _file_sha256(roster_path) != str(frozen_snapshot.get("file_sha256")):
        raise ValueError("training roster file bytes do not match frozen manifest")
    rows = _read_rows(roster_path, str(roster_spec["format"]))
    unit_column = str(roster_spec["unit_id_column"])
    stratum_column = roster_spec["stratum_column"]
    expected = {unit_column}
    if stratum_column is not None:
        expected.add(str(stratum_column))
    canonical: list[dict[str, str]] = []
    strata: dict[str, list[str]] = {}
    seen: set[str] = set()
    for index, row in enumerate(rows):
        if set(row) != expected:
            raise ValueError("training roster contains unexpected columns")
        unit = _text(row.get(unit_column), name=f"roster row {index} unit")
        if unit in seen:
            raise ValueError("training roster unit IDs must be unique")
        seen.add(unit)
        stratum = (
            "__all__"
            if stratum_column is None
            else _text(
                row.get(str(stratum_column)),
                name=f"roster row {index} stratum",
            )
        )
        canonical.append({"unit_id": unit, "stratum": stratum})
        strata.setdefault(stratum, []).append(unit)
    canonical.sort(key=lambda x: (x["stratum"], x["unit_id"]))
    if _canonical_sha256(canonical) != str(frozen_snapshot.get("semantic_sha256")):
        raise ValueError("training roster semantics do not match frozen manifest")
    return {
        key: tuple(sorted(values))
        for key, values in sorted(strata.items())
    }


def _membership_rows(
    strata: Mapping[str, Sequence[str]],
    *,
    seed: int,
) -> list[dict[str, object]]:
    rng = np.random.default_rng(seed)
    rows: list[dict[str, object]] = []
    for stratum in sorted(strata):
        units = tuple(strata[stratum])
        sampled = rng.integers(0, len(units), size=len(units))
        counts = np.bincount(sampled, minlength=len(units))
        for unit, count in zip(units, counts.tolist()):
            rows.append(
                {
                    "stratum": stratum,
                    "unit_id": str(unit),
                    "count": int(count),
                }
            )
    return rows


def run_managed_training_process_generation(
    plan_path: str | Path,
    output_root: str | Path,
    receipt_out: str | Path,
) -> dict[str, object]:
    """Execute every frozen refit under the predeclared managed-generation plan."""

    plan_path = Path(plan_path)
    raw_plan = _load_json(plan_path, name="managed generation plan")
    plan = validate_managed_generation_plan(raw_plan)
    base_dir = plan_path.parent

    manifest_path = Path(str(plan["manifest_path"]))
    if not manifest_path.is_absolute():
        manifest_path = base_dir / manifest_path
    manifest = _load_json(manifest_path, name="training process manifest")
    if manifest.get("manifest_type") != PROCESS_MANIFEST_TYPE:
        raise ValueError("training process manifest_type is not recognized")
    if str(manifest.get("training_process_id")) != str(plan["training_process_id"]):
        raise ValueError("managed plan process ID does not match manifest")

    roster_spec = plan["training_roster"]
    assert isinstance(roster_spec, Mapping)
    roster_path = Path(str(roster_spec["path"]))
    if not roster_path.is_absolute():
        roster_path = base_dir / roster_path
    frozen_roster = manifest.get("training_roster")
    if not isinstance(frozen_roster, Mapping):
        raise ValueError("manifest.training_roster must be an object")
    strata = _roster_strata(roster_path, roster_spec, frozen_roster)

    working_dir = Path(str(plan["working_directory"]))
    if not working_dir.is_absolute():
        working_dir = base_dir / working_dir
    if not working_dir.is_dir():
        raise FileNotFoundError(working_dir)

    command_artifacts: list[dict[str, str]] = []
    for raw_path in plan["command_artifacts"]:
        path = working_dir / str(raw_path)
        if path.is_symlink() or not path.is_file():
            raise ValueError(f"command artifact must be a regular non-symlink file: {path}")
        command_artifacts.append(
            {"path": str(raw_path), "sha256": _file_sha256(path)}
        )

    schedule = manifest.get("refit_schedule")
    if not isinstance(schedule, list) or not schedule:
        raise ValueError("manifest.refit_schedule must be non-empty")
    output_root = Path(output_root)
    if output_root.exists():
        raise FileExistsError(
            f"managed generation output root already exists: {output_root}"
        )
    receipt_path = Path(receipt_out)
    if receipt_path.exists():
        raise FileExistsError(
            f"managed generation receipt already exists: {receipt_path}"
        )
    output_root.mkdir(parents=True)

    runtime = _runtime_snapshot(plan["environment_allowlist"])
    executions: list[dict[str, object]] = []
    env = {
        name: value
        for name, value in runtime["environment"].items()
    }

    try:
        for index, raw in enumerate(schedule):
            if not isinstance(raw, Mapping):
                raise ValueError(f"manifest refit_schedule[{index}] must be an object")
            refit_id = _text(raw.get("refit_id"), name=f"schedule[{index}].refit_id")
            resample_seed = int(raw.get("resample_seed"))
            fit_seed = int(raw.get("fit_seed"))
            frozen_membership_sha = _text(
                raw.get("bootstrap_membership_sha256"),
                name=f"schedule[{index}].bootstrap_membership_sha256",
            )
            rows = _membership_rows(strata, seed=resample_seed)
            membership_sha = _canonical_sha256(rows)
            if membership_sha != frozen_membership_sha:
                raise ValueError(
                    f"materialized membership does not match frozen digest for {refit_id}"
                )

            refit_dir = output_root / refit_id
            refit_dir.mkdir()
            membership_path = refit_dir / "membership.json"
            membership_path.write_text(
                json.dumps(rows, indent=2, sort_keys=True, allow_nan=False) + "\n",
                encoding="utf-8",
            )

            replacements = {
                "{refit_id}": refit_id,
                "{membership_path}": str(membership_path.resolve()),
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
                    f"managed fit failed for {refit_id} with return code {completed.returncode}"
                )

            artifacts: list[dict[str, str]] = []
            for output in plan["output_artifacts"]:
                path = refit_dir / str(output["relative_path"])
                if path.is_symlink() or not path.is_file():
                    raise FileNotFoundError(path)
                artifacts.append(
                    {
                        "artifact_id": str(output["artifact_id"]),
                        "relative_path": str(output["relative_path"]),
                        "sha256": _file_sha256(path),
                    }
                )
            executions.append(
                {
                    "refit_id": refit_id,
                    "resample_seed": resample_seed,
                    "fit_seed": fit_seed,
                    "membership_semantic_sha256": membership_sha,
                    "membership_file_sha256": _file_sha256(membership_path),
                    "argv": argv,
                    "stdout_sha256": _sha256_bytes(completed.stdout),
                    "stderr_sha256": _sha256_bytes(completed.stderr),
                    "return_code": int(completed.returncode),
                    "artifacts": artifacts,
                }
            )
    except Exception:
        # Preserve the output directory for forensic inspection, but never emit
        # a success receipt for a partial run.
        raise

    created_at = (
        datetime.now(timezone.utc)
        .replace(microsecond=0)
        .isoformat()
        .replace("+00:00", "Z")
    )
    receipt = {
        "schema_version": 1,
        "receipt_type": MANAGED_GENERATION_RECEIPT_TYPE,
        "created_at_utc": created_at,
        "training_process_id": plan["training_process_id"],
        "training_process_manifest_sha256": _file_sha256(manifest_path),
        "managed_generation_plan_sha256": _file_sha256(plan_path),
        "command_artifact_snapshot": command_artifacts,
        "fit_environment_snapshot": runtime,
        "refit_count": len(executions),
        "executions": executions,
        "boundaries": {
            "validation_outcomes_read": False,
            "shell_used": False,
            "exact_membership_digest_verified_before_each_fit": True,
            "exact_command_invocation_recorded": True,
            "output_artifact_bytes_bound": True,
            "semantic_use_of_arguments_cryptographically_proven": False,
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
