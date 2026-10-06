"""Pre-outcome held-out validation freeze for training-source process v0."""
from __future__ import annotations

from datetime import datetime, timezone
import json
from pathlib import Path
from typing import Mapping

from .confirmatory_environment_lock import (
    ENVIRONMENT_LOCK_ID,
    runtime_environment_snapshot_for_surface,
)
from .confirmatory_implementation_lock import (
    IMPLEMENTATION_LOCK_ID,
    implementation_source_snapshot_for_surface,
)
from .information_transfer_contract import _read_rows
from .training_process_freeze_manifest import _file_sha256
from .training_process_managed_generation import _runtime_snapshot
from .training_source_process_freeze_manifest import SOURCE_PROCESS_MANIFEST_TYPE
from .training_source_process_validation_helpers import (
    _canonical_sha256,
    _nested_model_artifact_snapshot,
    _normalize_certification,
    _normalize_levels,
    _normalize_score,
    _normalize_scoring,
    _text,
    _validation_design_rows,
    _verify_managed_nested_receipt,
)
from .training_source_process_validation_provenance import (
    audit_training_source_process_validation_frame_separation,
)


MANIFEST_TYPE = "odsp_training_source_process_v0_pre_internal_validation_freeze"
FREEZE_RECEIPT_TYPE = "odsp_training_source_process_v0_internal_validation_freeze_receipt"
MANAGED_SURFACE = (
    "odsp.training_source_process_managed_internal_v0."
    "run_managed_internal_training_source_process_v0"
)
_PLAN_FIELDS = {
    "schema_version",
    "validation_dataset_id",
    "row_identity_namespace",
    "roster",
    "source_process_manifest_path",
    "managed_nested_generation_receipt_path",
    "source_roster",
    "score",
    "levels",
    "certification",
    "scoring",
}
_ROSTER_FIELDS = {"path", "format"}
_SOURCE_ROSTER_FIELDS = {"path", "format", "unit_id_column", "stratum_column"}


def _load_json(path: Path, *, name: str) -> dict[str, object]:
    try:
        raw = json.loads(path.read_text(encoding="utf-8"))
    except json.JSONDecodeError as exc:
        raise ValueError(f"{name} is not valid JSON: {path}") from exc
    if not isinstance(raw, Mapping):
        raise ValueError(f"{name} must contain a JSON object")
    return dict(raw)


def _normalize_plan(raw: Mapping[str, object]) -> dict[str, object]:
    if set(raw) != _PLAN_FIELDS:
        raise ValueError(
            "source-v0 validation freeze plan fields mismatch: "
            f"{sorted(set(raw) ^ _PLAN_FIELDS)!r}"
        )
    if raw.get("schema_version") != 1 or isinstance(raw.get("schema_version"), bool):
        raise ValueError("source-v0 validation freeze schema_version must be 1")

    roster = raw["roster"]
    if not isinstance(roster, Mapping) or set(roster) != _ROSTER_FIELDS:
        raise ValueError("validation roster fields are invalid")
    roster_format = _text(roster["format"], name="roster.format").lower()
    if roster_format not in {"csv", "json"}:
        raise ValueError("roster.format must be csv or json")

    source_roster = raw["source_roster"]
    if (
        not isinstance(source_roster, Mapping)
        or set(source_roster) != _SOURCE_ROSTER_FIELDS
    ):
        raise ValueError("source_roster fields are invalid")
    source_format = _text(
        source_roster["format"], name="source_roster.format"
    ).lower()
    if source_format not in {"csv", "json"}:
        raise ValueError("source_roster.format must be csv or json")
    unit_column = _text(
        source_roster["unit_id_column"], name="source_roster.unit_id_column"
    )
    raw_stratum = source_roster["stratum_column"]
    stratum_column = (
        None
        if raw_stratum is None
        else _text(raw_stratum, name="source_roster.stratum_column")
    )
    if stratum_column == unit_column:
        raise ValueError("source roster unit and stratum columns must differ")

    return {
        "schema_version": 1,
        "validation_dataset_id": _text(
            raw["validation_dataset_id"], name="validation_dataset_id"
        ),
        "row_identity_namespace": _text(
            raw["row_identity_namespace"], name="row_identity_namespace"
        ),
        "roster": {
            "path": _text(roster["path"], name="roster.path"),
            "format": roster_format,
        },
        "source_process_manifest_path": _text(
            raw["source_process_manifest_path"], name="source_process_manifest_path"
        ),
        "managed_nested_generation_receipt_path": _text(
            raw["managed_nested_generation_receipt_path"],
            name="managed_nested_generation_receipt_path",
        ),
        "source_roster": {
            "path": _text(source_roster["path"], name="source_roster.path"),
            "format": source_format,
            "unit_id_column": unit_column,
            "stratum_column": stratum_column,
        },
        "score": _normalize_score(raw["score"]),
        "levels": _normalize_levels(raw["levels"]),
        "certification": _normalize_certification(raw["certification"]),
        "scoring": _normalize_scoring(raw["scoring"]),
    }


def create_training_source_process_v0_internal_validation_freeze(
    plan_path: str | Path,
    manifest_out: str | Path,
    receipt_out: str | Path,
) -> dict[str, object]:
    plan_path = Path(plan_path)
    plan = _normalize_plan(_load_json(plan_path, name="source-v0 validation freeze plan"))
    base = plan_path.parent

    def resolved(value: str) -> Path:
        path = Path(value)
        return path if path.is_absolute() else base / path

    roster_path = resolved(plan["roster"]["path"])
    source_manifest_path = resolved(plan["source_process_manifest_path"])
    managed_receipt_path = resolved(plan["managed_nested_generation_receipt_path"])
    source_roster_path = resolved(plan["source_roster"]["path"])
    for path in (roster_path, source_manifest_path, managed_receipt_path, source_roster_path):
        if not path.is_file():
            raise FileNotFoundError(path)

    design_rows, block_counts = _validation_design_rows(
        _read_rows(roster_path, plan["roster"]["format"])
    )
    minimum_blocks = int(plan["certification"]["minimum_blocks_per_group"])
    if any(count < minimum_blocks for count in block_counts.values()):
        raise ValueError(
            "every positive-weight validation group must meet minimum_blocks_per_group"
        )
    row_ids = [str(row["row_id"]) for row in design_rows]

    source_manifest = _load_json(
        source_manifest_path, name="training source process manifest"
    )
    if source_manifest.get("manifest_type") != SOURCE_PROCESS_MANIFEST_TYPE:
        raise ValueError("training source process manifest_type is not recognized")
    source_process_id = _text(
        source_manifest.get("source_process_id"), name="source_process_id"
    )
    source_manifest_sha = _file_sha256(source_manifest_path)

    managed_receipt = _load_json(
        managed_receipt_path, name="managed nested generation receipt"
    )
    managed_receipt_sha = _file_sha256(managed_receipt_path)
    _verify_managed_nested_receipt(
        managed_receipt,
        receipt_sha256=managed_receipt_sha,
        source_process_id=source_process_id,
        manifest_sha256=source_manifest_sha,
        manifest=source_manifest,
    )

    frame_audit = audit_training_source_process_validation_frame_separation(
        source_manifest_path,
        source_roster_path,
        row_ids,
        row_identity_namespace=plan["row_identity_namespace"],
        roster_format=plan["source_roster"]["format"],
        unit_id_column=plan["source_roster"]["unit_id_column"],
        stratum_column=plan["source_roster"]["stratum_column"],
    )
    if not frame_audit.source_frame_validation_disjoint:
        raise ValueError("original training source frame overlaps validation roster")

    scoring = plan["scoring"]
    working = Path(str(scoring["working_directory"]))
    if not working.is_absolute():
        working = base / working
    if not working.is_dir():
        raise FileNotFoundError(working)
    command_snapshot: list[dict[str, str]] = []
    for rel in scoring["command_artifacts"]:
        path = working / str(rel)
        if path.is_symlink() or not path.is_file():
            raise ValueError(f"scoring artifact must be a regular file: {path}")
        command_snapshot.append({"path": str(rel), "sha256": _file_sha256(path)})
    scoring_runtime = _runtime_snapshot(scoring["environment_allowlist"])

    candidate_impl = implementation_source_snapshot_for_surface(MANAGED_SURFACE)
    candidate_env = runtime_environment_snapshot_for_surface(MANAGED_SURFACE)
    frozen_at = (
        datetime.now(timezone.utc)
        .replace(microsecond=0)
        .isoformat()
        .replace("+00:00", "Z")
    )

    manifest = {
        "schema_version": 1,
        "manifest_type": MANIFEST_TYPE,
        "frozen_at_utc": frozen_at,
        "validation_dataset_id": plan["validation_dataset_id"],
        "row_identity_namespace": plan["row_identity_namespace"],
        "validation_design_sha256": _canonical_sha256(design_rows),
        "validation_row_count": len(design_rows),
        "validation_group_count": len(block_counts),
        "positive_block_count_by_group": block_counts,
        "source_process_id": source_process_id,
        "source_process_manifest_sha256": source_manifest_sha,
        "source_roster_spec": dict(plan["source_roster"]),
        "managed_nested_generation_receipt_sha256": managed_receipt_sha,
        "source_draw_ids": list(source_manifest["source_draw_ids"]),
        "inner_refit_ids": list(source_manifest["inner_refit_ids"]),
        "nested_model_artifact_snapshot": _nested_model_artifact_snapshot(
            managed_receipt
        ),
        "fit_environment_snapshot": managed_receipt.get("fit_environment_snapshot"),
        "source_frame_validation_disjoint": True,
        "source_frame_audit": frame_audit.as_dict(),
        "managed_internal_endpoint": {
            "canonical_surface": MANAGED_SURFACE,
            "implementation_lock_id": IMPLEMENTATION_LOCK_ID,
            "implementation_source_snapshot": [dict(row) for row in candidate_impl],
            "environment_lock_id": ENVIRONMENT_LOCK_ID,
            "runtime_environment_snapshot": candidate_env,
        },
        "managed_scoring_plan": {
            "working_directory": str(working.resolve()),
            "command": list(scoring["command"]),
            "command_artifact_snapshot": command_snapshot,
            "timeout_seconds": int(scoring["timeout_seconds"]),
            "environment_allowlist": list(scoring["environment_allowlist"]),
            "validation_data_format": scoring["validation_data_format"],
            "validation_row_id_column": scoring["validation_row_id_column"],
            "runtime_environment_snapshot": scoring_runtime,
        },
        "score": plan["score"],
        "levels": plan["levels"],
        "certification": plan["certification"],
        "boundaries": {
            "validation_outcomes_read_at_freeze": False,
            "score_tensor_available_at_freeze": False,
            "raw_caller_supplied_score_tensor_primary": False,
            "statistical_method_changed": False,
            "unknown_ecological_superpopulation_generalization_claimed": False,
        },
    }

    manifest_path = Path(manifest_out)
    receipt_path = Path(receipt_out)
    if manifest_path.exists():
        raise FileExistsError(f"source-v0 validation freeze manifest exists: {manifest_path}")
    if receipt_path.exists():
        raise FileExistsError(f"source-v0 validation freeze receipt exists: {receipt_path}")
    manifest_path.parent.mkdir(parents=True, exist_ok=True)
    receipt_path.parent.mkdir(parents=True, exist_ok=True)
    manifest_path.write_text(
        json.dumps(manifest, indent=2, sort_keys=True, allow_nan=False) + "\n",
        encoding="utf-8",
    )
    receipt = {
        "schema_version": 1,
        "receipt_type": FREEZE_RECEIPT_TYPE,
        "frozen_at_utc": frozen_at,
        "manifest_sha256": _file_sha256(manifest_path),
        "validation_dataset_id": plan["validation_dataset_id"],
        "validation_design_sha256": manifest["validation_design_sha256"],
        "validation_row_count": len(design_rows),
        "source_process_id": source_process_id,
        "source_process_manifest_sha256": source_manifest_sha,
        "managed_nested_generation_receipt_sha256": managed_receipt_sha,
        "boundaries": {
            "validation_outcomes_read": False,
            "score_tensor_read": False,
            "non_overwriting": True,
        },
    }
    receipt_path.write_text(
        json.dumps(receipt, indent=2, sort_keys=True, allow_nan=False) + "\n",
        encoding="utf-8",
    )
    return {
        "manifest_path": str(manifest_path),
        "manifest_sha256": _file_sha256(manifest_path),
        "receipt_path": str(receipt_path),
        "receipt_sha256": _file_sha256(receipt_path),
        "manifest": manifest,
        "receipt": receipt,
    }
