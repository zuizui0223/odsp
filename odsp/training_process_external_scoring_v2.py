"""Managed untouched-external scoring for training-process v5 external v2.

A scoring plan is frozen before external outcomes are opened. It binds the
command template, scoring implementation artifacts, generated-model bytes, and
execution settings. After outcome access, ODSP invokes the frozen scoring command
once per refit with shell execution disabled, validates exact frozen row support,
and assembles one canonical score table whose bytes are bound to a receipt.
"""
from __future__ import annotations

from datetime import datetime, timezone
import csv
import hashlib
from importlib import metadata
import json
import os
from pathlib import Path
import subprocess
import sys
from typing import Mapping, Sequence

from .information_transfer_contract import _read_rows
from .training_process_freeze_manifest import _file_sha256


MANAGED_EXTERNAL_SCORING_PLAN_TYPE = "odsp_training_process_external_scoring_plan_v2"
MANAGED_EXTERNAL_SCORING_RECEIPT_TYPE = "odsp_training_process_external_scoring_receipt_v2"

_PLAN_FIELDS = {
    "schema_version",
    "generated_model_root",
    "working_directory",
    "command",
    "command_artifacts",
    "timeout_seconds",
    "environment_allowlist",
}
_REQUIRED_PLACEHOLDERS = {
    "{refit_id}",
    "{refit_model_dir}",
    "{external_data_path}",
    "{output_path}",
}


def _text(value: object, *, name: str) -> str:
    if not isinstance(value, str) or not value.strip():
        raise ValueError(f"{name} must be non-empty text")
    return value.strip()


def _safe_relative(value: object, *, name: str) -> str:
    text = _text(value, name=name)
    path = Path(text)
    if path.is_absolute() or ".." in path.parts:
        raise ValueError(f"{name} must be a safe relative path")
    return path.as_posix()


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


def validate_managed_external_scoring_plan(
    raw: Mapping[str, object],
) -> dict[str, object]:
    plan = dict(raw)
    missing = sorted(_PLAN_FIELDS - set(plan))
    extra = sorted(set(plan) - _PLAN_FIELDS)
    if missing or extra:
        raise ValueError(
            "managed external scoring plan fields mismatch: "
            f"missing={missing!r}, extra={extra!r}"
        )
    if plan["schema_version"] != 1 or isinstance(plan["schema_version"], bool):
        raise ValueError("managed external scoring plan schema_version must be 1")

    command_raw = plan["command"]
    if (
        not isinstance(command_raw, list)
        or not command_raw
        or any(not isinstance(x, str) or not x.strip() for x in command_raw)
    ):
        raise ValueError("command must be a non-empty array of non-empty strings")
    command = [str(x) for x in command_raw]
    joined = "\n".join(command)
    missing_placeholders = sorted(
        placeholder
        for placeholder in _REQUIRED_PLACEHOLDERS
        if placeholder not in joined
    )
    if missing_placeholders:
        raise ValueError(
            "managed scoring command is missing required placeholders: "
            f"{missing_placeholders!r}"
        )

    artifacts_raw = plan["command_artifacts"]
    if not isinstance(artifacts_raw, list) or not artifacts_raw:
        raise ValueError("command_artifacts must be a non-empty JSON array")
    artifacts = [
        _safe_relative(value, name=f"command_artifacts[{index}]")
        for index, value in enumerate(artifacts_raw)
    ]
    if len(artifacts) != len(set(artifacts)):
        raise ValueError("command_artifacts must be unique")

    timeout = plan["timeout_seconds"]
    if (
        isinstance(timeout, bool)
        or not isinstance(timeout, int)
        or not 1 <= timeout <= 86400
    ):
        raise ValueError("timeout_seconds must be an integer in [1, 86400]")

    env_raw = plan["environment_allowlist"]
    if not isinstance(env_raw, list):
        raise ValueError("environment_allowlist must be a JSON array")
    env = [
        _text(value, name=f"environment_allowlist[{index}]")
        for index, value in enumerate(env_raw)
    ]
    if len(env) != len(set(env)):
        raise ValueError("environment_allowlist must be unique")

    return {
        "schema_version": 1,
        "plan_type": MANAGED_EXTERNAL_SCORING_PLAN_TYPE,
        "generated_model_root": _text(
            plan["generated_model_root"], name="generated_model_root"
        ),
        "working_directory": _text(
            plan["working_directory"], name="working_directory"
        ),
        "command": command,
        "command_artifacts": artifacts,
        "timeout_seconds": int(timeout),
        "environment_allowlist": env,
    }


def load_managed_external_scoring_plan(
    path: str | Path,
) -> dict[str, object]:
    path = Path(path)
    return validate_managed_external_scoring_plan(
        _load_json(path, name="managed external scoring plan")
    )


def _runtime_snapshot(allowlist: Sequence[str]) -> dict[str, object]:
    distributions: dict[str, str] = {}
    for dist in metadata.distributions():
        name = str(dist.metadata.get("Name") or "").strip().lower().replace("_", "-")
        if name:
            distributions[name] = str(dist.version).strip()
    environment = {
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
            {"name": name, "version": distributions[name]}
            for name in sorted(distributions)
        ],
        "environment": environment,
    }


def _managed_receipt_executions(
    receipt: Mapping[str, object],
) -> tuple[tuple[str, ...], dict[str, Mapping[str, object]]]:
    executions_raw = receipt.get("executions")
    if not isinstance(executions_raw, list) or not executions_raw:
        raise ValueError("managed-generation receipt executions must be non-empty")
    executions: dict[str, Mapping[str, object]] = {}
    for index, raw in enumerate(executions_raw):
        if not isinstance(raw, Mapping):
            raise ValueError(
                f"managed-generation executions[{index}] must be an object"
            )
        refit_id = _text(
            raw.get("refit_id"),
            name=f"managed-generation executions[{index}].refit_id",
        )
        if refit_id in executions:
            raise ValueError("managed-generation receipt refit IDs must be unique")
        if raw.get("return_code") != 0:
            raise ValueError(
                f"managed-generation receipt records failed fit for {refit_id}"
            )
        artifacts = raw.get("artifacts")
        if not isinstance(artifacts, list) or not artifacts:
            raise ValueError(
                f"managed-generation receipt artifacts missing for {refit_id}"
            )
        executions[refit_id] = raw
    return tuple(sorted(executions)), executions


def snapshot_managed_external_scoring_plan_v2(
    plan_path: str | Path,
    managed_generation_receipt_path: str | Path,
) -> dict[str, object]:
    """Freeze scoring command, model bytes, and runtime settings without outcomes."""

    plan_path = Path(plan_path)
    plan = load_managed_external_scoring_plan(plan_path)
    base_dir = plan_path.parent

    receipt_path = Path(managed_generation_receipt_path)
    if not receipt_path.is_absolute():
        receipt_path = base_dir / receipt_path
    receipt = _load_json(
        receipt_path, name="managed-generation receipt"
    )
    refit_ids, executions = _managed_receipt_executions(receipt)

    working_dir = Path(str(plan["working_directory"]))
    if not working_dir.is_absolute():
        working_dir = base_dir / working_dir
    if not working_dir.is_dir():
        raise FileNotFoundError(working_dir)

    model_root = Path(str(plan["generated_model_root"]))
    if not model_root.is_absolute():
        model_root = base_dir / model_root
    if not model_root.is_dir():
        raise FileNotFoundError(model_root)

    command_artifacts: list[dict[str, str]] = []
    for declared in plan["command_artifacts"]:
        path = working_dir / str(declared)
        if path.is_symlink() or not path.is_file():
            raise ValueError(
                f"scoring command artifact must be a regular non-symlink file: {path}"
            )
        command_artifacts.append(
            {
                "path": str(declared),
                "sha256": _file_sha256(path),
            }
        )

    model_snapshot: list[dict[str, str]] = []
    for refit_id in refit_ids:
        execution = executions[refit_id]
        artifacts = execution["artifacts"]
        assert isinstance(artifacts, list)
        for index, artifact in enumerate(artifacts):
            if not isinstance(artifact, Mapping):
                raise ValueError(
                    f"managed-generation artifact {refit_id}[{index}] must be an object"
                )
            artifact_id = _text(
                artifact.get("artifact_id"),
                name=f"{refit_id} artifact_id",
            )
            relative = _safe_relative(
                artifact.get("relative_path"),
                name=f"{refit_id} artifact relative_path",
            )
            expected_sha = _text(
                artifact.get("sha256"),
                name=f"{refit_id} artifact sha256",
            ).lower()
            path = model_root / refit_id / relative
            if path.is_symlink() or not path.is_file():
                raise ValueError(
                    f"generated model artifact must be a regular non-symlink file: {path}"
                )
            observed_sha = _file_sha256(path)
            if observed_sha != expected_sha:
                raise ValueError(
                    f"generated model bytes do not match managed receipt for {refit_id}/{artifact_id}"
                )
            model_snapshot.append(
                {
                    "refit_id": refit_id,
                    "artifact_id": artifact_id,
                    "relative_path": relative,
                    "sha256": observed_sha,
                }
            )
    model_snapshot.sort(
        key=lambda row: (
            row["refit_id"],
            row["artifact_id"],
            row["relative_path"],
        )
    )

    return {
        "plan_type": MANAGED_EXTERNAL_SCORING_PLAN_TYPE,
        "plan_sha256": _file_sha256(plan_path),
        "managed_generation_receipt_sha256": _file_sha256(receipt_path),
        "refit_ids": list(refit_ids),
        "command": list(plan["command"]),
        "command_artifact_snapshot": command_artifacts,
        "model_artifact_snapshot": model_snapshot,
        "timeout_seconds": int(plan["timeout_seconds"]),
        "environment_allowlist": list(plan["environment_allowlist"]),
        "runtime_snapshot": _runtime_snapshot(
            plan["environment_allowlist"]
        ),
        "boundaries": {
            "external_outcomes_read": False,
            "model_artifact_bytes_verified": True,
            "scoring_command_artifact_bytes_verified": True,
            "shell_execution_planned": False,
        },
    }


def _verify_snapshot_against_runtime(
    snapshot: Mapping[str, object],
    plan_path: Path,
    managed_generation_receipt_path: Path,
) -> dict[str, object]:
    observed = snapshot_managed_external_scoring_plan_v2(
        plan_path,
        managed_generation_receipt_path,
    )
    # Runtime environment is allowed to be compared exactly because v2 freezes it.
    if observed != dict(snapshot):
        raise ValueError(
            "managed external scoring plan/model/runtime snapshot mismatch"
        )
    return observed


def _external_row_ids(
    external_data_path: Path,
    *,
    data_format: str,
    row_id_column: str,
) -> tuple[str, ...]:
    rows = _read_rows(external_data_path, data_format)
    if not rows:
        raise ValueError("external outcome-bearing data are empty")
    ids: list[str] = []
    for index, row in enumerate(rows):
        if row_id_column not in row:
            raise ValueError(
                f"external data row {index} is missing row ID column {row_id_column!r}"
            )
        ids.append(
            _text(
                row.get(row_id_column),
                name=f"external data row {index} row ID",
            )
        )
    if len(ids) != len(set(ids)):
        raise ValueError("external outcome-bearing row IDs must be unique")
    return tuple(sorted(ids))


def run_managed_external_scoring_v2(
    *,
    frozen_scoring_snapshot: Mapping[str, object],
    scoring_plan_path: str | Path,
    managed_generation_receipt_path: str | Path,
    external_data_path: str | Path,
    external_data_format: str,
    external_row_id_column: str,
    frozen_external_row_ids: Sequence[object],
    score_columns: Sequence[object],
    output_root: str | Path,
    score_table_out: str | Path,
    receipt_out: str | Path,
) -> dict[str, object]:
    """Execute the pre-frozen scorer and assemble a canonical score table."""

    plan_path = Path(scoring_plan_path)
    receipt_path = Path(managed_generation_receipt_path)
    external_path = Path(external_data_path)
    output_root = Path(output_root)
    score_table_path = Path(score_table_out)
    scoring_receipt_path = Path(receipt_out)

    if output_root.exists():
        raise FileExistsError(
            f"managed scoring output root already exists: {output_root}"
        )
    if score_table_path.exists():
        raise FileExistsError(
            f"managed score table already exists: {score_table_path}"
        )
    if scoring_receipt_path.exists():
        raise FileExistsError(
            f"managed scoring receipt already exists: {scoring_receipt_path}"
        )
    if not external_path.is_file():
        raise FileNotFoundError(external_path)

    plan = load_managed_external_scoring_plan(plan_path)
    snapshot = _verify_snapshot_against_runtime(
        frozen_scoring_snapshot,
        plan_path,
        receipt_path,
    )

    fmt = _text(external_data_format, name="external_data_format").lower()
    if fmt not in {"csv", "json"}:
        raise ValueError("external_data_format must be csv or json")
    row_id_column = _text(
        external_row_id_column, name="external_row_id_column"
    )
    frozen_rows = tuple(
        sorted(
            _text(value, name=f"frozen_external_row_ids[{index}]")
            for index, value in enumerate(frozen_external_row_ids)
        )
    )
    if len(frozen_rows) != len(set(frozen_rows)):
        raise ValueError("frozen external row IDs must be unique")
    runtime_rows = _external_row_ids(
        external_path,
        data_format=fmt,
        row_id_column=row_id_column,
    )
    if runtime_rows != frozen_rows:
        raise ValueError(
            "external outcome-bearing data row roster does not match frozen external rows"
        )

    columns = tuple(
        _text(value, name=f"score_columns[{index}]")
        for index, value in enumerate(score_columns)
    )
    if not columns or len(columns) != len(set(columns)):
        raise ValueError("score_columns must be non-empty and unique")
    if row_id_column in columns or "refit_id" in columns:
        raise ValueError("score_columns may not use row/refit identity names")

    base_dir = plan_path.parent
    working_dir = Path(str(plan["working_directory"]))
    if not working_dir.is_absolute():
        working_dir = base_dir / working_dir
    model_root = Path(str(plan["generated_model_root"]))
    if not model_root.is_absolute():
        model_root = base_dir / model_root
    refit_ids = tuple(str(value) for value in snapshot["refit_ids"])

    # Recheck the managed-generation receipt at execution time.
    managed_receipt = _load_json(
        receipt_path, name="managed-generation receipt"
    )
    current_refits, _ = _managed_receipt_executions(managed_receipt)
    if current_refits != refit_ids:
        raise ValueError(
            "managed-generation receipt refit set changed after scoring freeze"
        )

    runtime = snapshot["runtime_snapshot"]
    if not isinstance(runtime, Mapping):
        raise ValueError("frozen scoring runtime snapshot must be an object")
    env_raw = runtime.get("environment")
    if not isinstance(env_raw, Mapping):
        raise ValueError("frozen scoring environment snapshot must be an object")
    env = {str(key): str(value) for key, value in env_raw.items()}

    output_root.mkdir(parents=True)
    assembled: list[dict[str, object]] = []
    executions: list[dict[str, object]] = []
    expected_output_columns = {row_id_column, *columns}

    for refit_id in refit_ids:
        refit_dir = model_root / refit_id
        if not refit_dir.is_dir():
            raise FileNotFoundError(refit_dir)
        run_dir = output_root / refit_id
        run_dir.mkdir()
        output_path = run_dir / "scores.csv"

        replacements = {
            "{refit_id}": refit_id,
            "{refit_model_dir}": str(refit_dir.resolve()),
            "{external_data_path}": str(external_path.resolve()),
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
            cwd=working_dir,
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

        rows = _read_rows(output_path, "csv")
        observed_rows: dict[str, dict[str, float]] = {}
        for index, row in enumerate(rows):
            if set(row) != expected_output_columns:
                raise ValueError(
                    f"managed scorer output columns mismatch for {refit_id}"
                )
            row_id = _text(
                row.get(row_id_column),
                name=f"{refit_id} scorer row {index} row ID",
            )
            if row_id in observed_rows:
                raise ValueError(
                    f"managed scorer output has duplicate row ID for {refit_id}"
                )
            scores: dict[str, float] = {}
            for column in columns:
                raw = row.get(column)
                try:
                    number = float(raw)
                except (TypeError, ValueError) as exc:
                    raise ValueError(
                        f"managed scorer output {refit_id}/{row_id}/{column} is non-numeric"
                    ) from exc
                if number != number or number == float("inf"):
                    raise ValueError(
                        "managed scorer output may be finite or -inf, but not NaN or +inf"
                    )
                scores[column] = number
            observed_rows[row_id] = scores

        if tuple(sorted(observed_rows)) != frozen_rows:
            raise ValueError(
                f"managed scorer output row roster mismatch for {refit_id}"
            )
        for row_id in frozen_rows:
            assembled.append(
                {
                    "row_id": row_id,
                    "refit_id": refit_id,
                    **observed_rows[row_id],
                }
            )
        executions.append(
            {
                "refit_id": refit_id,
                "argv": argv,
                "stdout_sha256": _sha256_bytes(completed.stdout),
                "stderr_sha256": _sha256_bytes(completed.stderr),
                "return_code": int(completed.returncode),
                "per_refit_score_sha256": _file_sha256(output_path),
            }
        )

    score_table_path.parent.mkdir(parents=True, exist_ok=True)
    with score_table_path.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(
            handle,
            fieldnames=["row_id", "refit_id", *columns],
            lineterminator="\n",
        )
        writer.writeheader()
        for row in assembled:
            writer.writerow(row)

    created_at = (
        datetime.now(timezone.utc)
        .replace(microsecond=0)
        .isoformat()
        .replace("+00:00", "Z")
    )
    receipt = {
        "schema_version": 2,
        "receipt_type": MANAGED_EXTERNAL_SCORING_RECEIPT_TYPE,
        "created_at_utc": created_at,
        "scoring_plan_sha256": _file_sha256(plan_path),
        "managed_generation_receipt_sha256": _file_sha256(receipt_path),
        "external_data_sha256": _file_sha256(external_path),
        "external_row_count": len(frozen_rows),
        "refit_count": len(refit_ids),
        "refit_ids": list(refit_ids),
        "score_columns": list(columns),
        "score_table_sha256": _file_sha256(score_table_path),
        "frozen_scoring_snapshot": dict(snapshot),
        "executions": executions,
        "boundaries": {
            "shell_used": False,
            "runtime_model_bytes_match_frozen_snapshot": True,
            "external_row_roster_matches_preoutcome_freeze": True,
            "score_table_assembled_by_odsp": True,
            "score_table_derivation_operationally_bound_to_frozen_models_and_scorer": True,
            "semantic_use_of_model_arguments_cryptographically_proven": False,
        },
    }
    scoring_receipt_path.parent.mkdir(parents=True, exist_ok=True)
    scoring_receipt_path.write_text(
        json.dumps(receipt, indent=2, sort_keys=True, allow_nan=False) + "\n",
        encoding="utf-8",
    )
    return {
        "receipt_path": str(scoring_receipt_path),
        "receipt_sha256": _file_sha256(scoring_receipt_path),
        "score_table_path": str(score_table_path),
        "score_table_sha256": receipt["score_table_sha256"],
        "receipt": receipt,
    }
