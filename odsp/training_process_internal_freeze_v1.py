"""Pre-outcome freeze for managed internal validation under training-process v5.

This is a provenance layer only.  It reuses the already-qualified internal v5
statistical wrapper and freezes how held-out validation scores will be derived
from the managed-generated model artifacts.
"""
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
from .training_process_confirmatory_v5 import (
    _load_json,
    _manifest_schedule,
    _verify_managed_receipt,
)
from .training_process_internal_qualification_v5 import (
    build_internal_v5_qualification_snapshot,
)
from .training_process_validation_helpers import (
    _canonical_sha256,
    _model_artifact_snapshot,
    _normalize_certification,
    _normalize_levels,
    _normalize_score,
    _normalize_scoring,
    _validation_design_rows,
)
from .training_process_freeze_manifest import _file_sha256
from .training_process_managed_generation import _runtime_snapshot
from .training_process_validation_provenance import (
    audit_training_process_validation_frame_separation,
)


MANIFEST_TYPE = "odsp_training_process_v5_pre_internal_validation_freeze_v1"
FREEZE_RECEIPT_TYPE = "odsp_training_process_v5_internal_validation_freeze_receipt_v1"
MANAGED_INTERNAL_SURFACE = (
    "odsp.training_process_managed_internal_v5."
    "run_managed_internal_training_process_v5"
)
_PLAN_FIELDS = {
    "schema_version",
    "validation_dataset_id",
    "row_identity_namespace",
    "roster",
    "training_process_manifest_path",
    "managed_generation_receipt_path",
    "training_roster",
    "score",
    "levels",
    "certification",
    "scoring",
}
_ROSTER_FIELDS = {"path", "format"}
_TRAINING_ROSTER_FIELDS = {"path", "format", "unit_id_column", "stratum_column"}


def _text(value: object, *, name: str) -> str:
    if not isinstance(value, str) or not value.strip():
        raise ValueError(f"{name} must be non-empty text")
    return value.strip()


def _normalize_plan(raw: Mapping[str, object]) -> dict[str, object]:
    if set(raw) != _PLAN_FIELDS:
        raise ValueError(
            "internal validation freeze plan fields mismatch: "
            f"{sorted(set(raw) ^ _PLAN_FIELDS)!r}"
        )
    if raw.get("schema_version") != 1 or isinstance(raw.get("schema_version"), bool):
        raise ValueError("internal validation freeze schema_version must be 1")

    roster = raw["roster"]
    if not isinstance(roster, Mapping) or set(roster) != _ROSTER_FIELDS:
        raise ValueError("internal validation roster fields are invalid")
    roster_format = _text(roster["format"], name="roster.format").lower()
    if roster_format not in {"csv", "json"}:
        raise ValueError("roster.format must be csv or json")

    training = raw["training_roster"]
    if (
        not isinstance(training, Mapping)
        or set(training) != _TRAINING_ROSTER_FIELDS
    ):
        raise ValueError("training_roster fields are invalid")
    training_format = _text(
        training["format"], name="training_roster.format"
    ).lower()
    if training_format not in {"csv", "json"}:
        raise ValueError("training_roster.format must be csv or json")
    unit_column = _text(
        training["unit_id_column"], name="training_roster.unit_id_column"
    )
    stratum_raw = training["stratum_column"]
    stratum_column = (
        None
        if stratum_raw is None
        else _text(stratum_raw, name="training_roster.stratum_column")
    )
    if stratum_column == unit_column:
        raise ValueError("training unit and stratum columns must differ")

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
        "training_process_manifest_path": _text(
            raw["training_process_manifest_path"],
            name="training_process_manifest_path",
        ),
        "managed_generation_receipt_path": _text(
            raw["managed_generation_receipt_path"],
            name="managed_generation_receipt_path",
        ),
        "training_roster": {
            "path": _text(training["path"], name="training_roster.path"),
            "format": training_format,
            "unit_id_column": unit_column,
            "stratum_column": stratum_column,
        },
        "score": _normalize_score(raw["score"]),
        "levels": _normalize_levels(raw["levels"]),
        "certification": _normalize_certification(raw["certification"]),
        "scoring": _normalize_scoring(raw["scoring"]),
    }


def create_training_process_v5_internal_validation_freeze(
    plan_path: str | Path,
    manifest_out: str | Path,
    receipt_out: str | Path,
) -> dict[str, object]:
    """Freeze internal validation design and score derivation before outcomes."""

    plan_path = Path(plan_path)
    plan = _normalize_plan(_load_json(plan_path, name="internal validation freeze plan"))
    base = plan_path.parent

    def resolved(value: str) -> Path:
        path = Path(value)
        return path if path.is_absolute() else base / path

    roster_path = resolved(plan["roster"]["path"])
    process_manifest_path = resolved(plan["training_process_manifest_path"])
    managed_receipt_path = resolved(plan["managed_generation_receipt_path"])
    training_roster_path = resolved(plan["training_roster"]["path"])
    for path in (
        roster_path,
        process_manifest_path,
        managed_receipt_path,
        training_roster_path,
    ):
        if not path.is_file():
            raise FileNotFoundError(path)

    design_rows, block_counts = _validation_design_rows(
        _read_rows(roster_path, plan["roster"]["format"])
    )
    minimum_blocks = int(plan["certification"]["minimum_blocks_per_group"])
    if any(count < minimum_blocks for count in block_counts.values()):
        raise ValueError(
            "every positive-weight validation group must meet "
            "minimum_blocks_per_group"
        )
    row_ids = [str(row["row_id"]) for row in design_rows]

    process_manifest = _load_json(
        process_manifest_path, name="training process manifest"
    )
    process_id, frozen_refits, schedule = _manifest_schedule(process_manifest)
    process_manifest_sha = _file_sha256(process_manifest_path)

    managed_receipt = _load_json(
        managed_receipt_path, name="managed generation receipt"
    )
    managed_receipt_sha = _file_sha256(managed_receipt_path)
    _verify_managed_receipt(
        managed_receipt,
        expected_receipt_sha256=managed_receipt_sha,
        actual_receipt_sha256=managed_receipt_sha,
        process_id=process_id,
        manifest_sha256=process_manifest_sha,
        refit_ids=frozen_refits,
        schedule=schedule,
    )

    frame_audit = audit_training_process_validation_frame_separation(
        process_manifest_path,
        training_roster_path,
        row_ids,
        row_identity_namespace=plan["row_identity_namespace"],
        roster_format=plan["training_roster"]["format"],
        unit_id_column=plan["training_roster"]["unit_id_column"],
        stratum_column=plan["training_roster"]["stratum_column"],
    )
    if not frame_audit.training_source_frame_validation_disjoint:
        raise ValueError("training source frame overlaps frozen validation roster")

    scoring = plan["scoring"]
    scoring_working_dir = Path(str(scoring["working_directory"]))
    if not scoring_working_dir.is_absolute():
        scoring_working_dir = base / scoring_working_dir
    if not scoring_working_dir.is_dir():
        raise FileNotFoundError(scoring_working_dir)
    command_snapshot: list[dict[str, str]] = []
    for declared_path in scoring["command_artifacts"]:
        artifact_path = scoring_working_dir / str(declared_path)
        if artifact_path.is_symlink() or not artifact_path.is_file():
            raise ValueError(
                "scoring command artifact must be a regular non-symlink file: "
                f"{artifact_path}"
            )
        command_snapshot.append(
            {
                "path": str(declared_path),
                "sha256": _file_sha256(artifact_path),
            }
        )
    scoring_runtime = _runtime_snapshot(scoring["environment_allowlist"])

    candidate_impl = implementation_source_snapshot_for_surface(
        MANAGED_INTERNAL_SURFACE
    )
    candidate_env = runtime_environment_snapshot_for_surface(
        MANAGED_INTERNAL_SURFACE
    )
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
        "training_process_id": process_id,
        "training_process_manifest_sha256": process_manifest_sha,
        "training_roster_spec": {
            "format": plan["training_roster"]["format"],
            "unit_id_column": plan["training_roster"]["unit_id_column"],
            "stratum_column": plan["training_roster"]["stratum_column"],
        },
        "managed_generation_receipt_sha256": managed_receipt_sha,
        "refit_ids": list(frozen_refits),
        "generated_model_artifact_snapshot": _model_artifact_snapshot(
            managed_receipt
        ),
        "fit_environment_snapshot": managed_receipt.get(
            "fit_environment_snapshot"
        ),
        "training_source_frame_validation_disjoint": True,
        "training_source_frame_audit": frame_audit.as_dict(),
        "internal_qualified_route": build_internal_v5_qualification_snapshot(),
        "managed_internal_endpoint": {
            "canonical_surface": MANAGED_INTERNAL_SURFACE,
            "implementation_lock_id": IMPLEMENTATION_LOCK_ID,
            "implementation_source_snapshot": [
                dict(row) for row in candidate_impl
            ],
            "environment_lock_id": ENVIRONMENT_LOCK_ID,
            "runtime_environment_snapshot": candidate_env,
        },
        "managed_scoring_plan": {
            "working_directory": str(scoring_working_dir.resolve()),
            "command": list(scoring["command"]),
            "command_artifact_snapshot": command_snapshot,
            "timeout_seconds": scoring["timeout_seconds"],
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
            "training_source_frame_validation_disjoint": True,
            "statistical_method_changed": False,
            "fixed_set_results_reclassified": False,
        },
    }

    manifest_path = Path(manifest_out)
    receipt_path = Path(receipt_out)
    if manifest_path.exists():
        raise FileExistsError(
            f"internal validation freeze manifest already exists: {manifest_path}"
        )
    if receipt_path.exists():
        raise FileExistsError(
            f"internal validation freeze receipt already exists: {receipt_path}"
        )
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
        "training_process_id": process_id,
        "training_process_manifest_sha256": process_manifest_sha,
        "managed_generation_receipt_sha256": managed_receipt_sha,
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
