"""Freeze a prospective independent training-resampling process.

The v1 process family is deliberately narrow: independent stratified bootstrap
samples of declared training units, with replacement and the original stratum
sample size. Ordinary unstratified bootstrap is represented by omitting the
stratum column.

Dependent refit constructions such as K-fold partitions, leave-one-out
jackknife sets, or hand-picked seed collections are not admitted to this process
route. They remain eligible for fixed-set sensitivity or intersection analyses.

The freeze generator reads training-unit metadata and hashes training and fitting
artifacts, derives independent resample and fit seeds for every declared refit,
and records a digest of the exact bootstrap membership implied by each seed.
It does not fit models and it does not read validation outcomes.
"""
from __future__ import annotations

from datetime import datetime, timezone
import hashlib
import json
import math
from pathlib import Path
from typing import Mapping, Sequence

import numpy as np

from .information_transfer_contract import (
    _mapping,
    _read_rows,
    _reject_unknown,
    _text,
    _value,
)


PROCESS_MANIFEST_TYPE = "odsp_training_process_freeze_v1"
PROCESS_KIND = "stratified_unit_bootstrap_with_replacement"
RNG_ALGORITHM = "numpy.default_rng.PCG64"

_PLAN_FIELDS = {
    "schema_version",
    "training_process_id",
    "training_roster",
    "training_data_artifacts",
    "implementation_artifacts",
    "fit_entrypoint",
    "fit_parameters",
    "refit_ids",
    "master_seed",
    "resampling",
}
_ROSTER_FIELDS = {
    "path",
    "format",
    "unit_id_column",
    "stratum_column",
}
_ARTIFACT_FIELDS = {"role", "path"}
_RESAMPLING_FIELDS = {
    "kind",
    "replacement",
    "within_stratum_draw_size",
}


def _file_sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def _canonical_sha256(value: object) -> str:
    payload = json.dumps(
        value,
        ensure_ascii=False,
        sort_keys=True,
        separators=(",", ":"),
        allow_nan=False,
    ) + "\n"
    return hashlib.sha256(payload.encode("utf-8")).hexdigest()


def _integer(value: object, *, name: str, minimum: int) -> int:
    if isinstance(value, bool) or not isinstance(value, int):
        raise ValueError(f"{name} must be an integer >= {minimum}")
    if value < minimum:
        raise ValueError(f"{name} must be an integer >= {minimum}")
    return int(value)


def _string_array(value: object, *, name: str) -> tuple[str, ...]:
    if not isinstance(value, list) or not value:
        raise ValueError(f"{name} must be a non-empty JSON array")
    rows = tuple(
        _text(item, name=f"{name}[{index}]")
        for index, item in enumerate(value)
    )
    if len(rows) != len(set(rows)):
        raise ValueError(f"{name} values must be unique")
    return rows


def _json_object(value: object, *, name: str) -> dict[str, object]:
    if not isinstance(value, Mapping):
        raise ValueError(f"{name} must be a JSON object")
    normalized = dict(value)
    try:
        json.dumps(
            normalized,
            ensure_ascii=False,
            sort_keys=True,
            allow_nan=False,
        )
    except (TypeError, ValueError) as exc:
        raise ValueError(
            f"{name} must contain only finite JSON-serializable values"
        ) from exc
    return normalized


def _artifact_declarations(
    value: object,
    *,
    name: str,
) -> tuple[dict[str, str], ...]:
    if not isinstance(value, list) or not value:
        raise ValueError(f"{name} must be a non-empty JSON array")
    rows: list[dict[str, str]] = []
    roles: set[str] = set()
    for index, raw in enumerate(value):
        item = _mapping(raw, name=f"{name}[{index}]")
        _reject_unknown(
            item,
            _ARTIFACT_FIELDS,
            name=f"{name}[{index}]",
        )
        role = _text(
            item.get("role"),
            name=f"{name}[{index}].role",
        )
        path = _text(
            item.get("path"),
            name=f"{name}[{index}].path",
        )
        if role in roles:
            raise ValueError(f"{name} artifact roles must be unique")
        roles.add(role)
        rows.append({"role": role, "path": path})
    return tuple(rows)


def validate_training_process_freeze_plan(
    raw: Mapping[str, object],
) -> dict[str, object]:
    """Validate the prospective process definition without generating draws."""

    plan = _mapping(raw, name="training process freeze plan")
    _reject_unknown(
        plan,
        _PLAN_FIELDS,
        name="training process freeze plan",
    )
    version = plan.get("schema_version")
    if isinstance(version, bool) or version != 1:
        raise ValueError("training process freeze plan schema_version must be 1")

    process_id = _text(
        plan.get("training_process_id"),
        name="training_process_id",
    )

    roster = _mapping(
        plan.get("training_roster"),
        name="training_roster",
    )
    _reject_unknown(roster, _ROSTER_FIELDS, name="training_roster")
    roster_path = _text(
        roster.get("path"),
        name="training_roster.path",
    )
    roster_format = _text(
        roster.get("format"),
        name="training_roster.format",
    ).lower()
    if roster_format not in {"csv", "json"}:
        raise ValueError("training_roster.format must be 'csv' or 'json'")
    unit_column = _text(
        roster.get("unit_id_column"),
        name="training_roster.unit_id_column",
    )
    raw_stratum = roster.get("stratum_column")
    if raw_stratum is None:
        stratum_column = None
    else:
        stratum_column = _text(
            raw_stratum,
            name="training_roster.stratum_column",
        )
        if stratum_column == unit_column:
            raise ValueError(
                "training roster unit and stratum columns must be distinct"
            )

    data_artifacts = _artifact_declarations(
        plan.get("training_data_artifacts"),
        name="training_data_artifacts",
    )
    implementation_artifacts = _artifact_declarations(
        plan.get("implementation_artifacts"),
        name="implementation_artifacts",
    )
    fit_entrypoint = _text(
        plan.get("fit_entrypoint"),
        name="fit_entrypoint",
    )
    fit_parameters = _json_object(
        plan.get("fit_parameters"),
        name="fit_parameters",
    )

    refit_ids = _string_array(plan.get("refit_ids"), name="refit_ids")
    if len(refit_ids) < 8:
        raise ValueError(
            "training-process v1 requires at least 8 independent refit draws"
        )
    master_seed = _integer(
        plan.get("master_seed"),
        name="master_seed",
        minimum=0,
    )

    resampling = _mapping(plan.get("resampling"), name="resampling")
    _reject_unknown(
        resampling,
        _RESAMPLING_FIELDS,
        name="resampling",
    )
    kind = _text(resampling.get("kind"), name="resampling.kind")
    if kind != PROCESS_KIND:
        raise ValueError(
            "training-process v1 admits only independent stratified "
            "unit bootstrap draws with replacement"
        )
    replacement = resampling.get("replacement")
    if replacement is not True:
        raise ValueError("resampling.replacement must be true")
    draw_size = _text(
        resampling.get("within_stratum_draw_size"),
        name="resampling.within_stratum_draw_size",
    )
    if draw_size != "original_stratum_size":
        raise ValueError(
            "resampling.within_stratum_draw_size must be "
            "'original_stratum_size'"
        )

    return {
        "schema_version": 1,
        "training_process_id": process_id,
        "training_roster": {
            "path": roster_path,
            "format": roster_format,
            "unit_id_column": unit_column,
            "stratum_column": stratum_column,
        },
        "training_data_artifacts": [
            dict(row) for row in data_artifacts
        ],
        "implementation_artifacts": [
            dict(row) for row in implementation_artifacts
        ],
        "fit_entrypoint": fit_entrypoint,
        "fit_parameters": fit_parameters,
        "refit_ids": list(refit_ids),
        "master_seed": master_seed,
        "resampling": {
            "kind": PROCESS_KIND,
            "replacement": True,
            "within_stratum_draw_size": "original_stratum_size",
        },
    }


def load_training_process_freeze_plan(
    path: str | Path,
) -> dict[str, object]:
    plan_path = Path(path)
    try:
        raw = json.loads(plan_path.read_text(encoding="utf-8"))
    except json.JSONDecodeError as exc:
        raise ValueError(
            f"training process freeze plan is not valid JSON: {plan_path}"
        ) from exc
    return validate_training_process_freeze_plan(
        _mapping(raw, name="training process freeze plan")
    )


def _snapshot_artifacts(
    declarations: Sequence[Mapping[str, str]],
    *,
    base_dir: Path,
) -> tuple[dict[str, object], ...]:
    rows: list[dict[str, object]] = []
    for item in declarations:
        declared = Path(str(item["path"]))
        path = declared if declared.is_absolute() else base_dir / declared
        if not path.is_file():
            raise FileNotFoundError(path)
        rows.append(
            {
                "role": str(item["role"]),
                "declared_path": str(item["path"]),
                "size_bytes": path.stat().st_size,
                "sha256": _file_sha256(path),
            }
        )
    rows.sort(key=lambda row: str(row["role"]))
    return tuple(rows)


def _derive_seed(
    master_seed: int,
    process_id: str,
    refit_id: str,
    *,
    domain: str,
) -> int:
    digest = hashlib.sha256(
        (
            f"{master_seed}|odsp-training-process-v1|{domain}|"
            f"{process_id}|{refit_id}"
        ).encode("utf-8")
    ).digest()
    return int.from_bytes(digest[:8], "little", signed=False)


def _membership_sha256(
    strata: Mapping[str, Sequence[str]],
    *,
    seed: int,
) -> str:
    rng = np.random.default_rng(seed)
    rows: list[dict[str, object]] = []
    for stratum in sorted(strata):
        units = tuple(sorted(str(value) for value in strata[stratum]))
        sampled = rng.integers(0, len(units), size=len(units))
        counts = np.bincount(sampled, minlength=len(units))
        for unit, count in zip(units, counts.tolist()):
            rows.append(
                {
                    "stratum": stratum,
                    "unit_id": unit,
                    "count": int(count),
                }
            )
    return _canonical_sha256(rows)


def create_training_process_freeze_manifest(
    plan_path: str | Path,
    manifest_out: str | Path,
) -> dict[str, object]:
    """Create a non-overwriting process manifest and return its receipt."""

    plan_path = Path(plan_path)
    plan = load_training_process_freeze_plan(plan_path)
    roster_spec = plan["training_roster"]
    assert isinstance(roster_spec, Mapping)
    roster_path = Path(str(roster_spec["path"]))
    if not roster_path.is_absolute():
        roster_path = plan_path.parent / roster_path
    if not roster_path.is_file():
        raise FileNotFoundError(roster_path)

    roster_rows = _read_rows(
        roster_path,
        str(roster_spec["format"]),
    )
    if not roster_rows:
        raise ValueError("training unit roster is empty")

    unit_column = str(roster_spec["unit_id_column"])
    raw_stratum_column = roster_spec["stratum_column"]
    stratum_column = (
        None
        if raw_stratum_column is None
        else str(raw_stratum_column)
    )
    expected = {unit_column}
    if stratum_column is not None:
        expected.add(stratum_column)

    canonical_roster: list[dict[str, str]] = []
    seen_units: set[str] = set()
    strata: dict[str, list[str]] = {}
    for index, row in enumerate(roster_rows):
        keys = set(row)
        if keys != expected:
            extra = sorted(keys - expected)
            missing = sorted(expected - keys)
            raise ValueError(
                "training process roster must contain only unit and optional "
                f"stratum metadata; row={index}, missing={missing!r}, "
                f"extra={extra!r}"
            )
        unit = _text(
            _value(row, unit_column, row_index=index),
            name=f"row {index} unit_id",
        )
        if unit in seen_units:
            raise ValueError("training process unit IDs must be unique")
        seen_units.add(unit)
        stratum = (
            "__all__"
            if stratum_column is None
            else _text(
                _value(row, stratum_column, row_index=index),
                name=f"row {index} stratum",
            )
        )
        canonical_roster.append(
            {"unit_id": unit, "stratum": stratum}
        )
        strata.setdefault(stratum, []).append(unit)

    canonical_roster.sort(
        key=lambda row: (row["stratum"], row["unit_id"])
    )
    roster_semantic_sha = _canonical_sha256(canonical_roster)
    base_dir = plan_path.parent
    data_snapshot = _snapshot_artifacts(
        plan["training_data_artifacts"],
        base_dir=base_dir,
    )
    implementation_snapshot = _snapshot_artifacts(
        plan["implementation_artifacts"],
        base_dir=base_dir,
    )

    schedule: list[dict[str, object]] = []
    for refit_id in plan["refit_ids"]:
        resample_seed = _derive_seed(
            int(plan["master_seed"]),
            str(plan["training_process_id"]),
            str(refit_id),
            domain="resample",
        )
        fit_seed = _derive_seed(
            int(plan["master_seed"]),
            str(plan["training_process_id"]),
            str(refit_id),
            domain="fit",
        )
        schedule.append(
            {
                "refit_id": str(refit_id),
                "resample_seed": resample_seed,
                "fit_seed": fit_seed,
                "bootstrap_membership_sha256": _membership_sha256(
                    strata,
                    seed=resample_seed,
                ),
            }
        )

    frozen_at = (
        datetime.now(timezone.utc)
        .replace(microsecond=0)
        .isoformat()
        .replace("+00:00", "Z")
    )
    manifest = {
        "schema_version": 1,
        "manifest_type": PROCESS_MANIFEST_TYPE,
        "frozen_at_utc": frozen_at,
        "training_process_id": plan["training_process_id"],
        "process_kind": PROCESS_KIND,
        "rng_algorithm": RNG_ALGORITHM,
        "master_seed": plan["master_seed"],
        "refit_count": len(plan["refit_ids"]),
        "refit_ids": list(plan["refit_ids"]),
        "training_roster": {
            "row_count": len(canonical_roster),
            "stratum_count": len(strata),
            "stratum_sizes": {
                key: len(strata[key]) for key in sorted(strata)
            },
            "semantic_sha256": roster_semantic_sha,
            "file_sha256": _file_sha256(roster_path),
        },
        "training_data_artifact_snapshot": [
            dict(row) for row in data_snapshot
        ],
        "implementation_artifact_snapshot": [
            dict(row) for row in implementation_snapshot
        ],
        "fit_entrypoint": plan["fit_entrypoint"],
        "fit_parameters": plan["fit_parameters"],
        "resampling": dict(plan["resampling"]),
        "refit_schedule": schedule,
        "assumptions": {
            "refit_draws_independent_by_construction": True,
            "refit_draws_exchangeable_under_declared_process": True,
            "training_units_exchangeable_within_declared_strata": True,
            "validation_outcomes_read_by_freeze_generator": False,
            "dependent_kfold_or_jackknife_refit_set_admitted": False,
        },
    }

    output_path = Path(manifest_out)
    if output_path.exists():
        raise FileExistsError(
            "training process freeze manifest already exists and will not "
            f"be overwritten: {output_path}"
        )
    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_text(
        json.dumps(
            manifest,
            indent=2,
            sort_keys=True,
            allow_nan=False,
        )
        + "\n",
        encoding="utf-8",
    )

    return {
        "receipt_type": "odsp_training_process_freeze_receipt_v1",
        "manifest_path": str(output_path),
        "manifest_sha256": _file_sha256(output_path),
        "freeze_plan_sha256": _file_sha256(plan_path),
        "training_roster_file_sha256": _file_sha256(roster_path),
        "training_roster_semantic_sha256": roster_semantic_sha,
        "frozen_at_utc": frozen_at,
        "training_process_id": plan["training_process_id"],
        "process_kind": PROCESS_KIND,
        "rng_algorithm": RNG_ALGORITHM,
        "refit_count": len(schedule),
        "refit_schedule_sha256": _canonical_sha256(schedule),
        "boundaries": {
            "caller_supplied_freeze_timestamp_allowed": False,
            "manifest_overwrite_allowed": False,
            "validation_outcomes_read_by_freeze_generator": False,
            "training_outcomes_used_to_select_resample_draws": False,
            "independent_refit_draws_required": True,
            "dependent_kfold_or_jackknife_sets_qualified": False,
            "arbitrary_supplied_refit_set_reinterpreted_as_process_sample": False,
        },
    }
