"""Bind generated refit artifacts to a frozen training-process schedule.

The freeze manifest records what refits were planned. This module records what
artifact bytes are presented as the outputs of that plan and requires an exact
match to the frozen refit IDs, resample seeds, fit seeds, and bootstrap-membership
digests.

This is a provenance binding, not a proof that arbitrary fitting code truly
consumed the declared membership or seed. The receipt states that boundary
explicitly. Confirmatory use must additionally freeze the fitting implementation
and verify training/validation separation.
"""
from __future__ import annotations

from datetime import datetime, timezone
import json
from pathlib import Path
from typing import Mapping, Sequence

from .training_process_freeze_manifest import (
    PROCESS_MANIFEST_TYPE,
    _canonical_sha256,
    _file_sha256,
)
from .upstream_model_artifact_lock import (
    MODEL_ARTIFACT_LOCK_ID,
    snapshot_upstream_model_artifacts,
)


GENERATION_RECEIPT_TYPE = "odsp_training_process_generation_receipt_v1"
_DECLARATION_FIELDS = {
    "schema_version",
    "training_process_id",
    "refits",
}
_REFIT_FIELDS = {
    "refit_id",
    "resample_seed",
    "fit_seed",
    "bootstrap_membership_sha256",
    "model_artifacts",
}
_MODEL_ARTIFACT_FIELDS = {"artifact_id", "path"}


def _text(value: object, *, name: str) -> str:
    if not isinstance(value, str) or not value.strip():
        raise ValueError(f"{name} must be non-empty text")
    return value.strip()


def _integer(value: object, *, name: str) -> int:
    if isinstance(value, bool) or not isinstance(value, int) or value < 0:
        raise ValueError(f"{name} must be a non-negative integer")
    return int(value)


def _sha256(value: object, *, name: str) -> str:
    digest = _text(value, name=name).lower()
    if len(digest) != 64:
        raise ValueError(f"{name} must be lowercase SHA256 text")
    try:
        int(digest, 16)
    except ValueError as exc:
        raise ValueError(f"{name} must be lowercase SHA256 text") from exc
    return digest


def _load_json(path: Path, *, name: str) -> dict[str, object]:
    try:
        raw = json.loads(path.read_text(encoding="utf-8"))
    except json.JSONDecodeError as exc:
        raise ValueError(f"{name} is not valid JSON: {path}") from exc
    if not isinstance(raw, Mapping):
        raise ValueError(f"{name} must contain a JSON object")
    return dict(raw)


def _manifest_schedule(
    manifest: Mapping[str, object],
) -> tuple[str, tuple[dict[str, object], ...]]:
    if manifest.get("manifest_type") != PROCESS_MANIFEST_TYPE:
        raise ValueError("training process manifest_type is not recognized")
    process_id = _text(
        manifest.get("training_process_id"),
        name="manifest.training_process_id",
    )
    refit_ids_raw = manifest.get("refit_ids")
    schedule_raw = manifest.get("refit_schedule")
    if not isinstance(refit_ids_raw, list) or not refit_ids_raw:
        raise ValueError("manifest.refit_ids must be a non-empty JSON array")
    refit_ids = tuple(
        _text(value, name=f"manifest.refit_ids[{index}]")
        for index, value in enumerate(refit_ids_raw)
    )
    if len(refit_ids) != len(set(refit_ids)):
        raise ValueError("manifest.refit_ids must be unique")
    if not isinstance(schedule_raw, list) or len(schedule_raw) != len(refit_ids):
        raise ValueError("manifest.refit_schedule must contain one row per refit")

    rows: list[dict[str, object]] = []
    seen: set[str] = set()
    for index, raw in enumerate(schedule_raw):
        if not isinstance(raw, Mapping):
            raise ValueError(f"manifest.refit_schedule[{index}] must be an object")
        refit_id = _text(
            raw.get("refit_id"),
            name=f"manifest.refit_schedule[{index}].refit_id",
        )
        if refit_id in seen:
            raise ValueError("manifest.refit_schedule refit IDs must be unique")
        seen.add(refit_id)
        rows.append(
            {
                "refit_id": refit_id,
                "resample_seed": _integer(
                    raw.get("resample_seed"),
                    name=f"manifest.refit_schedule[{index}].resample_seed",
                ),
                "fit_seed": _integer(
                    raw.get("fit_seed"),
                    name=f"manifest.refit_schedule[{index}].fit_seed",
                ),
                "bootstrap_membership_sha256": _sha256(
                    raw.get("bootstrap_membership_sha256"),
                    name=(
                        f"manifest.refit_schedule[{index}]."
                        "bootstrap_membership_sha256"
                    ),
                ),
            }
        )
    if set(seen) != set(refit_ids):
        raise ValueError("manifest refit schedule must exactly cover manifest.refit_ids")
    rows.sort(key=lambda row: str(row["refit_id"]))
    return process_id, tuple(rows)


def _generation_declaration(
    raw: Mapping[str, object],
) -> tuple[str, tuple[dict[str, object], ...]]:
    if set(raw) != _DECLARATION_FIELDS:
        raise ValueError(
            "generation declaration fields must be exactly "
            "['refits', 'schema_version', 'training_process_id']"
        )
    if raw.get("schema_version") != 1 or isinstance(raw.get("schema_version"), bool):
        raise ValueError("generation declaration schema_version must be 1")
    process_id = _text(
        raw.get("training_process_id"),
        name="generation.training_process_id",
    )
    refits_raw = raw.get("refits")
    if not isinstance(refits_raw, list) or not refits_raw:
        raise ValueError("generation.refits must be a non-empty JSON array")

    rows: list[dict[str, object]] = []
    seen: set[str] = set()
    for index, item in enumerate(refits_raw):
        if not isinstance(item, Mapping) or set(item) != _REFIT_FIELDS:
            raise ValueError(
                f"generation.refits[{index}] must contain exactly "
                "bootstrap_membership_sha256, fit_seed, model_artifacts, "
                "refit_id, resample_seed"
            )
        refit_id = _text(
            item.get("refit_id"),
            name=f"generation.refits[{index}].refit_id",
        )
        if refit_id in seen:
            raise ValueError("generation refit IDs must be unique")
        seen.add(refit_id)

        artifacts_raw = item.get("model_artifacts")
        if not isinstance(artifacts_raw, list) or not artifacts_raw:
            raise ValueError(
                f"generation.refits[{index}].model_artifacts must be non-empty"
            )
        artifacts: list[dict[str, str]] = []
        artifact_ids: set[str] = set()
        for artifact_index, artifact in enumerate(artifacts_raw):
            if (
                not isinstance(artifact, Mapping)
                or set(artifact) != _MODEL_ARTIFACT_FIELDS
            ):
                raise ValueError(
                    f"generation.refits[{index}].model_artifacts[{artifact_index}] "
                    "must contain exactly artifact_id and path"
                )
            artifact_id = _text(
                artifact.get("artifact_id"),
                name=(
                    f"generation.refits[{index}].model_artifacts"
                    f"[{artifact_index}].artifact_id"
                ),
            )
            if artifact_id in artifact_ids:
                raise ValueError(
                    f"duplicate artifact_id within refit {refit_id!r}"
                )
            artifact_ids.add(artifact_id)
            artifacts.append(
                {
                    "artifact_id": artifact_id,
                    "path": _text(
                        artifact.get("path"),
                        name=(
                            f"generation.refits[{index}].model_artifacts"
                            f"[{artifact_index}].path"
                        ),
                    ),
                }
            )
        artifacts.sort(key=lambda row: row["artifact_id"])
        rows.append(
            {
                "refit_id": refit_id,
                "resample_seed": _integer(
                    item.get("resample_seed"),
                    name=f"generation.refits[{index}].resample_seed",
                ),
                "fit_seed": _integer(
                    item.get("fit_seed"),
                    name=f"generation.refits[{index}].fit_seed",
                ),
                "bootstrap_membership_sha256": _sha256(
                    item.get("bootstrap_membership_sha256"),
                    name=(
                        f"generation.refits[{index}]."
                        "bootstrap_membership_sha256"
                    ),
                ),
                "model_artifacts": artifacts,
            }
        )
    rows.sort(key=lambda row: str(row["refit_id"]))
    return process_id, tuple(rows)


def create_training_process_generation_receipt(
    manifest_path: str | Path,
    generation_declaration_path: str | Path,
    receipt_out: str | Path,
) -> dict[str, object]:
    """Create a non-overwriting receipt binding generated model bytes to a freeze."""

    manifest_path = Path(manifest_path)
    declaration_path = Path(generation_declaration_path)
    manifest = _load_json(manifest_path, name="training process manifest")
    declaration = _load_json(
        declaration_path,
        name="training process generation declaration",
    )

    process_id, frozen_schedule = _manifest_schedule(manifest)
    declared_process_id, generated = _generation_declaration(declaration)
    if declared_process_id != process_id:
        raise ValueError(
            "generation declaration training_process_id does not match manifest"
        )

    generated_schedule = tuple(
        {
            "refit_id": row["refit_id"],
            "resample_seed": row["resample_seed"],
            "fit_seed": row["fit_seed"],
            "bootstrap_membership_sha256": row["bootstrap_membership_sha256"],
        }
        for row in generated
    )
    if generated_schedule != frozen_schedule:
        raise ValueError(
            "generation declaration refit schedule does not exactly match "
            "the frozen process manifest"
        )

    refit_ids = tuple(str(row["refit_id"]) for row in frozen_schedule)
    artifact_declarations: list[dict[str, str]] = []
    for row in generated:
        for artifact in row["model_artifacts"]:
            artifact_declarations.append(
                {
                    "refit_id": str(row["refit_id"]),
                    "artifact_id": str(artifact["artifact_id"]),
                    "path": str(artifact["path"]),
                }
            )
    artifact_snapshot = snapshot_upstream_model_artifacts(
        artifact_declarations,
        base_dir=declaration_path.parent,
        refit_ids=refit_ids,
    )

    receipt_path = Path(receipt_out)
    if receipt_path.exists():
        raise FileExistsError(
            "training process generation receipt already exists and will not "
            f"be overwritten: {receipt_path}"
        )

    created_at = (
        datetime.now(timezone.utc)
        .replace(microsecond=0)
        .isoformat()
        .replace("+00:00", "Z")
    )
    receipt = {
        "schema_version": 1,
        "receipt_type": GENERATION_RECEIPT_TYPE,
        "created_at_utc": created_at,
        "training_process_id": process_id,
        "process_manifest_sha256": _file_sha256(manifest_path),
        "generation_declaration_sha256": _file_sha256(declaration_path),
        "refit_count": len(refit_ids),
        "refit_ids": list(refit_ids),
        "refit_schedule_sha256": _canonical_sha256(list(frozen_schedule)),
        "upstream_model_artifact_lock_id": MODEL_ARTIFACT_LOCK_ID,
        "upstream_model_artifact_snapshot": [
            dict(row) for row in artifact_snapshot
        ],
        "checks": {
            "process_identity_matches_manifest": True,
            "exact_refit_coverage": True,
            "resample_seed_matches_manifest": True,
            "fit_seed_matches_manifest": True,
            "bootstrap_membership_digest_matches_manifest": True,
            "model_artifact_bytes_bound": True,
        },
        "boundaries": {
            "receipt_proves_artifact_identity": True,
            "receipt_proves_schedule_record_consistency": True,
            "receipt_cryptographically_proves_fitting_code_consumed_declared_membership": False,
            "receipt_cryptographically_proves_fitting_code_consumed_declared_fit_seed": False,
            "training_validation_separation_verified_here": False,
            "validation_outcomes_read_here": False,
            "historical_fixed_set_refits_reinterpreted_as_process_draws": False,
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
