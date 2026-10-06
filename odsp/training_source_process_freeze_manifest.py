"""Freeze a nested outer-source / inner-refit process for source-process v0.

The original empirical source roster is the sampling frame. Each outer source
draw is a stratified bootstrap from that roster. Each inner refit is then a
bootstrap from the empirical distribution of one outer source draw, implemented
by resampling a deterministic expanded slot list implied by the outer membership
counts.

Both outer and inner memberships are represented canonically as counts over the
original roster, including zero-count units. This module freezes the plan only;
it does not fit models or read validation outcomes.
"""
from __future__ import annotations

from datetime import datetime, timezone
import hashlib
import json
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
from .training_process_freeze_manifest import (
    _artifact_declarations,
    _canonical_sha256,
    _file_sha256,
    _integer,
    _json_object,
    _snapshot_artifacts,
    _string_array,
)


SOURCE_PROCESS_MANIFEST_TYPE = "odsp_training_source_process_freeze_v0"
OUTER_PROCESS_KIND = "stratified_unit_bootstrap_with_replacement"
INNER_PROCESS_KIND = "bootstrap_from_outer_source_empirical_distribution"
RNG_ALGORITHM = "numpy.default_rng.PCG64"

_PLAN_FIELDS = {
    "schema_version",
    "source_process_id",
    "source_roster",
    "source_data_artifacts",
    "source_generation_artifacts",
    "fit_implementation_artifacts",
    "fit_entrypoint",
    "fit_parameters",
    "source_draw_ids",
    "inner_refit_ids",
    "master_seed",
    "outer_resampling",
    "inner_resampling",
}
_ROSTER_FIELDS = {"path", "format", "unit_id_column", "stratum_column"}
_OUTER_FIELDS = {"kind", "replacement", "within_stratum_draw_size"}
_INNER_FIELDS = {"kind", "replacement", "draw_size"}


def _derive_seed(
    master_seed: int,
    process_id: str,
    source_id: str,
    *,
    domain: str,
    inner_refit_id: str | None = None,
) -> int:
    suffix = "" if inner_refit_id is None else f"|{inner_refit_id}"
    digest = hashlib.sha256(
        (
            f"{master_seed}|odsp-training-source-process-v0|{domain}|"
            f"{process_id}|{source_id}{suffix}"
        ).encode("utf-8")
    ).digest()
    return int.from_bytes(digest[:8], "little", signed=False)


def _canonical_roster_and_strata(
    roster_path: Path,
    *,
    roster_format: str,
    unit_column: str,
    stratum_column: str | None,
) -> tuple[list[dict[str, str]], dict[str, tuple[str, ...]]]:
    rows = _read_rows(roster_path, roster_format)
    if not rows:
        raise ValueError("source roster is empty")
    expected = {unit_column}
    if stratum_column is not None:
        expected.add(stratum_column)
    canonical: list[dict[str, str]] = []
    strata: dict[str, list[str]] = {}
    seen: set[str] = set()
    for index, row in enumerate(rows):
        if set(row) != expected:
            raise ValueError(
                "source roster must contain only unit and optional stratum columns"
            )
        unit = _text(
            _value(row, unit_column, row_index=index),
            name=f"row {index} unit_id",
        )
        if unit in seen:
            raise ValueError("source roster unit IDs must be unique")
        seen.add(unit)
        stratum = (
            "__all__"
            if stratum_column is None
            else _text(
                _value(row, stratum_column, row_index=index),
                name=f"row {index} stratum",
            )
        )
        canonical.append({"unit_id": unit, "stratum": stratum})
        strata.setdefault(stratum, []).append(unit)
    canonical.sort(key=lambda x: (x["stratum"], x["unit_id"]))
    normalized = {
        key: tuple(sorted(values))
        for key, values in sorted(strata.items())
    }
    return canonical, normalized


def _outer_membership_rows(
    strata: Mapping[str, Sequence[str]],
    *,
    seed: int,
) -> list[dict[str, object]]:
    rng = np.random.default_rng(seed)
    rows: list[dict[str, object]] = []
    for stratum in sorted(strata):
        units = tuple(sorted(str(x) for x in strata[stratum]))
        sampled = rng.integers(0, len(units), size=len(units))
        counts = np.bincount(sampled, minlength=len(units))
        for unit, count in zip(units, counts.tolist()):
            rows.append(
                {"stratum": stratum, "unit_id": unit, "count": int(count)}
            )
    return rows


def _inner_membership_rows(
    strata: Mapping[str, Sequence[str]],
    outer_rows: Sequence[Mapping[str, object]],
    *,
    seed: int,
) -> list[dict[str, object]]:
    by_key = {
        (str(row["stratum"]), str(row["unit_id"])): int(row["count"])
        for row in outer_rows
    }
    rng = np.random.default_rng(seed)
    rows: list[dict[str, object]] = []
    for stratum in sorted(strata):
        units = tuple(sorted(str(x) for x in strata[stratum]))
        slots: list[str] = []
        for unit in units:
            count = by_key.get((stratum, unit))
            if count is None or count < 0:
                raise ValueError("outer membership is incomplete or invalid")
            slots.extend([unit] * count)
        if len(slots) != len(units):
            raise ValueError(
                "outer source draw must preserve original stratum draw size"
            )
        sampled = rng.integers(0, len(slots), size=len(slots))
        sampled_units = [slots[int(i)] for i in sampled.tolist()]
        counts = {unit: 0 for unit in units}
        for unit in sampled_units:
            counts[unit] += 1
        for unit in units:
            rows.append(
                {
                    "stratum": stratum,
                    "unit_id": unit,
                    "count": int(counts[unit]),
                }
            )
    return rows


def validate_training_source_process_freeze_plan(
    raw: Mapping[str, object],
) -> dict[str, object]:
    plan = _mapping(raw, name="training source process freeze plan")
    _reject_unknown(plan, _PLAN_FIELDS, name="training source process freeze plan")
    if plan.get("schema_version") != 1 or isinstance(plan.get("schema_version"), bool):
        raise ValueError("training source process freeze plan schema_version must be 1")

    process_id = _text(plan.get("source_process_id"), name="source_process_id")
    roster = _mapping(plan.get("source_roster"), name="source_roster")
    _reject_unknown(roster, _ROSTER_FIELDS, name="source_roster")
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

    source_draw_ids = _string_array(
        plan.get("source_draw_ids"), name="source_draw_ids"
    )
    inner_refit_ids = _string_array(
        plan.get("inner_refit_ids"), name="inner_refit_ids"
    )
    if len(source_draw_ids) < 8:
        raise ValueError("source-process v0 requires at least 8 outer source draws")
    if len(inner_refit_ids) < 8:
        raise ValueError("source-process v0 requires at least 8 inner refits per source")

    outer = _mapping(plan.get("outer_resampling"), name="outer_resampling")
    _reject_unknown(outer, _OUTER_FIELDS, name="outer_resampling")
    if _text(outer.get("kind"), name="outer_resampling.kind") != OUTER_PROCESS_KIND:
        raise ValueError("unsupported outer source-resampling kind")
    if outer.get("replacement") is not True:
        raise ValueError("outer_resampling.replacement must be true")
    if _text(
        outer.get("within_stratum_draw_size"),
        name="outer_resampling.within_stratum_draw_size",
    ) != "original_stratum_size":
        raise ValueError(
            "outer_resampling.within_stratum_draw_size must be original_stratum_size"
        )

    inner = _mapping(plan.get("inner_resampling"), name="inner_resampling")
    _reject_unknown(inner, _INNER_FIELDS, name="inner_resampling")
    if _text(inner.get("kind"), name="inner_resampling.kind") != INNER_PROCESS_KIND:
        raise ValueError("unsupported inner refit-resampling kind")
    if inner.get("replacement") is not True:
        raise ValueError("inner_resampling.replacement must be true")
    if _text(inner.get("draw_size"), name="inner_resampling.draw_size") != "outer_source_draw_size":
        raise ValueError("inner_resampling.draw_size must be outer_source_draw_size")

    return {
        "schema_version": 1,
        "source_process_id": process_id,
        "source_roster": {
            "path": _text(roster.get("path"), name="source_roster.path"),
            "format": roster_format,
            "unit_id_column": unit_column,
            "stratum_column": stratum_column,
        },
        "source_data_artifacts": [
            dict(x)
            for x in _artifact_declarations(
                plan.get("source_data_artifacts"), name="source_data_artifacts"
            )
        ],
        "source_generation_artifacts": [
            dict(x)
            for x in _artifact_declarations(
                plan.get("source_generation_artifacts"),
                name="source_generation_artifacts",
            )
        ],
        "fit_implementation_artifacts": [
            dict(x)
            for x in _artifact_declarations(
                plan.get("fit_implementation_artifacts"),
                name="fit_implementation_artifacts",
            )
        ],
        "fit_entrypoint": _text(plan.get("fit_entrypoint"), name="fit_entrypoint"),
        "fit_parameters": _json_object(plan.get("fit_parameters"), name="fit_parameters"),
        "source_draw_ids": list(source_draw_ids),
        "inner_refit_ids": list(inner_refit_ids),
        "master_seed": _integer(plan.get("master_seed"), name="master_seed", minimum=0),
        "outer_resampling": {
            "kind": OUTER_PROCESS_KIND,
            "replacement": True,
            "within_stratum_draw_size": "original_stratum_size",
        },
        "inner_resampling": {
            "kind": INNER_PROCESS_KIND,
            "replacement": True,
            "draw_size": "outer_source_draw_size",
        },
    }


def create_training_source_process_freeze_manifest(
    plan_path: str | Path,
    manifest_out: str | Path,
) -> dict[str, object]:
    plan_path = Path(plan_path)
    raw = json.loads(plan_path.read_text(encoding="utf-8"))
    plan = validate_training_source_process_freeze_plan(
        _mapping(raw, name="training source process freeze plan")
    )
    roster_spec = plan["source_roster"]
    roster_path = Path(str(roster_spec["path"]))
    if not roster_path.is_absolute():
        roster_path = plan_path.parent / roster_path
    if not roster_path.is_file():
        raise FileNotFoundError(roster_path)

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
    base = plan_path.parent
    schedule: list[dict[str, object]] = []

    for source_id in plan["source_draw_ids"]:
        outer_seed = _derive_seed(
            int(plan["master_seed"]),
            str(plan["source_process_id"]),
            str(source_id),
            domain="outer-source-resample",
        )
        outer_rows = _outer_membership_rows(strata, seed=outer_seed)
        inner_schedule: list[dict[str, object]] = []
        for refit_id in plan["inner_refit_ids"]:
            inner_seed = _derive_seed(
                int(plan["master_seed"]),
                str(plan["source_process_id"]),
                str(source_id),
                domain="inner-refit-resample",
                inner_refit_id=str(refit_id),
            )
            fit_seed = _derive_seed(
                int(plan["master_seed"]),
                str(plan["source_process_id"]),
                str(source_id),
                domain="fit",
                inner_refit_id=str(refit_id),
            )
            inner_rows = _inner_membership_rows(
                strata, outer_rows, seed=inner_seed
            )
            inner_schedule.append(
                {
                    "inner_refit_id": str(refit_id),
                    "inner_resample_seed": inner_seed,
                    "fit_seed": fit_seed,
                    "inner_membership_sha256": _canonical_sha256(inner_rows),
                }
            )
        schedule.append(
            {
                "source_draw_id": str(source_id),
                "outer_resample_seed": outer_seed,
                "outer_membership_sha256": _canonical_sha256(outer_rows),
                "inner_refit_schedule": inner_schedule,
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
        "manifest_type": SOURCE_PROCESS_MANIFEST_TYPE,
        "frozen_at_utc": frozen_at,
        "source_process_id": plan["source_process_id"],
        "rng_algorithm": RNG_ALGORITHM,
        "master_seed": plan["master_seed"],
        "source_draw_count": len(plan["source_draw_ids"]),
        "source_draw_ids": list(plan["source_draw_ids"]),
        "inner_refit_count_per_source": len(plan["inner_refit_ids"]),
        "inner_refit_ids": list(plan["inner_refit_ids"]),
        "source_roster": {
            "row_count": len(canonical_roster),
            "stratum_count": len(strata),
            "stratum_sizes": {k: len(v) for k, v in strata.items()},
            "semantic_sha256": _canonical_sha256(canonical_roster),
            "file_sha256": _file_sha256(roster_path),
        },
        "source_data_artifact_snapshot": [
            dict(x)
            for x in _snapshot_artifacts(
                plan["source_data_artifacts"], base_dir=base
            )
        ],
        "source_generation_artifact_snapshot": [
            dict(x)
            for x in _snapshot_artifacts(
                plan["source_generation_artifacts"], base_dir=base
            )
        ],
        "fit_implementation_artifact_snapshot": [
            dict(x)
            for x in _snapshot_artifacts(
                plan["fit_implementation_artifacts"], base_dir=base
            )
        ],
        "fit_entrypoint": plan["fit_entrypoint"],
        "fit_parameters": plan["fit_parameters"],
        "outer_resampling": dict(plan["outer_resampling"]),
        "inner_resampling": dict(plan["inner_resampling"]),
        "nested_schedule": schedule,
        "assumptions": {
            "outer_source_draws_exchangeable_under_declared_process": True,
            "inner_refits_nested_within_source_draw": True,
            "inner_refits_are_not_independent_outer_source_draws": True,
            "source_units_exchangeable_within_declared_strata": True,
            "validation_outcomes_read_by_freeze_generator": False,
            "unknown_ecological_superpopulation_inference_claimed": False,
        },
    }

    output = Path(manifest_out)
    if output.exists():
        raise FileExistsError(
            f"training source process manifest already exists: {output}"
        )
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(
        json.dumps(manifest, indent=2, sort_keys=True, allow_nan=False) + "\n",
        encoding="utf-8",
    )
    return {
        "receipt_type": "odsp_training_source_process_freeze_receipt_v0",
        "manifest_path": str(output),
        "manifest_sha256": _file_sha256(output),
        "freeze_plan_sha256": _file_sha256(plan_path),
        "source_roster_file_sha256": _file_sha256(roster_path),
        "source_roster_semantic_sha256": _canonical_sha256(canonical_roster),
        "nested_schedule_sha256": _canonical_sha256(schedule),
        "source_process_id": plan["source_process_id"],
        "source_draw_count": len(plan["source_draw_ids"]),
        "inner_refit_count_per_source": len(plan["inner_refit_ids"]),
        "frozen_at_utc": frozen_at,
        "boundaries": {
            "manifest_overwrite_allowed": False,
            "validation_outcomes_read": False,
            "outer_source_draw_claimed_as_new_ecological_sample": False,
            "unknown_ecological_superpopulation_inference_claimed": False,
            "managed_nested_generation_still_required": True,
        },
    }
