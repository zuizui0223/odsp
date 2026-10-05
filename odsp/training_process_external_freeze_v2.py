"""Pre-outcome untouched-external freeze v2 with managed scoring provenance."""
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
from .confirmatory_method_routing import route_confirmatory_method
from .confirmatory_route_evidence import (
    qualification_evidence_artifacts_for_route_key,
)
from .training_process_confirmatory_v5 import (
    _load_json,
    _manifest_schedule,
    _verify_managed_receipt,
)
from .training_process_external_freeze_v1 import (
    _canonical_external_design,
    validate_training_process_external_freeze_plan,
)
from .training_process_external_scoring_v2 import (
    snapshot_managed_external_scoring_plan_v2,
)
from .training_process_freeze_manifest import _file_sha256
from .training_process_validation_provenance import (
    audit_training_process_validation_frame_separation,
)


EXTERNAL_FREEZE_MANIFEST_TYPE_V2 = "odsp_training_process_external_freeze_v2"
EXTERNAL_ENDPOINT_SURFACE_V2 = (
    "odsp.untouched_external_training_process_v2."
    "run_untouched_external_training_process_v2"
)
EXTERNAL_CONTRACT_ARTIFACT_V2 = (
    "ODSP_TRAINING_PROCESS_V5_UNTOUCHED_EXTERNAL_CONTRACT_V2.json"
)
_REPOSITORY_ROOT = Path(__file__).resolve().parent.parent

_V2_PLAN_FIELDS = {
    "schema_version",
    "external_dataset_id",
    "external_roster",
    "training_process",
    "score",
    "levels",
    "certification",
    "managed_scoring",
}
_SCORING_FIELDS = {
    "plan_path",
    "external_data_format",
    "external_row_id_column",
}


def _mapping(value: object, *, name: str) -> dict[str, object]:
    if not isinstance(value, Mapping):
        raise ValueError(f"{name} must be a JSON object")
    return dict(value)


def _text(value: object, *, name: str) -> str:
    if not isinstance(value, str) or not value.strip():
        raise ValueError(f"{name} must be non-empty text")
    return value.strip()


def validate_training_process_external_freeze_plan_v2(
    raw: Mapping[str, object],
) -> dict[str, object]:
    plan = dict(raw)
    missing = sorted(_V2_PLAN_FIELDS - set(plan))
    extra = sorted(set(plan) - _V2_PLAN_FIELDS)
    if missing or extra:
        raise ValueError(
            "external freeze v2 plan fields mismatch: "
            f"missing={missing!r}, extra={extra!r}"
        )
    if plan["schema_version"] != 2 or isinstance(plan["schema_version"], bool):
        raise ValueError("external freeze v2 plan schema_version must be 2")

    base_raw = {
        key: value
        for key, value in plan.items()
        if key != "managed_scoring"
    }
    base_raw["schema_version"] = 1
    validated = validate_training_process_external_freeze_plan(base_raw)

    scoring = _mapping(plan["managed_scoring"], name="managed_scoring")
    if set(scoring) != _SCORING_FIELDS:
        raise ValueError(
            "managed_scoring fields must be exactly "
            "external_data_format, external_row_id_column, plan_path"
        )
    data_format = _text(
        scoring["external_data_format"],
        name="managed_scoring.external_data_format",
    ).lower()
    if data_format not in {"csv", "json"}:
        raise ValueError(
            "managed_scoring.external_data_format must be csv or json"
        )
    validated["schema_version"] = 2
    validated["managed_scoring"] = {
        "plan_path": _text(
            scoring["plan_path"], name="managed_scoring.plan_path"
        ),
        "external_data_format": data_format,
        "external_row_id_column": _text(
            scoring["external_row_id_column"],
            name="managed_scoring.external_row_id_column",
        ),
    }
    return validated


def _external_v2_evidence_snapshot() -> dict[str, object]:
    route = route_confirmatory_method(
        alternative="greater",
        validation_design="independent_groups",
        information_structure="filtration",
        upstream_refits="predeclared_training_process",
        external_validation="none",
        contrast_count=2,
    )
    if route.role != "primary_confirmatory" or not route.qualification_key:
        raise ValueError("internal training-process v5 route is not qualified")
    artifacts = [
        dict(row)
        for row in qualification_evidence_artifacts_for_route_key(
            route.qualification_key
        )
    ]
    contract = _REPOSITORY_ROOT / EXTERNAL_CONTRACT_ARTIFACT_V2
    if not contract.is_file():
        raise FileNotFoundError(contract)
    artifacts.append(
        {
            "artifact": EXTERNAL_CONTRACT_ARTIFACT_V2,
            "sha256": _file_sha256(contract),
        }
    )
    return {
        "internal_qualification_key": route.qualification_key,
        "evidence": [row["artifact"] for row in artifacts],
        "evidence_artifacts": artifacts,
    }


def create_training_process_external_freeze_manifest_v2(
    plan_path: str | Path,
    manifest_out: str | Path,
) -> dict[str, object]:
    """Freeze external design, process, model, scorer, and endpoint identity."""

    plan_path = Path(plan_path)
    plan = validate_training_process_external_freeze_plan_v2(
        _load_json(plan_path, name="external freeze v2 plan")
    )
    base_dir = plan_path.parent

    external_spec = plan["external_roster"]
    assert isinstance(external_spec, Mapping)
    external_path = Path(str(external_spec["path"]))
    if not external_path.is_absolute():
        external_path = base_dir / external_path
    if not external_path.is_file():
        raise FileNotFoundError(external_path)
    design_rows, design_sha = _canonical_external_design(
        external_path,
        str(external_spec["format"]),
    )

    process = plan["training_process"]
    assert isinstance(process, Mapping)
    process_manifest_path = Path(str(process["manifest_path"]))
    managed_receipt_path = Path(
        str(process["managed_generation_receipt_path"])
    )
    training_roster_path = Path(str(process["training_roster_path"]))
    if not process_manifest_path.is_absolute():
        process_manifest_path = base_dir / process_manifest_path
    if not managed_receipt_path.is_absolute():
        managed_receipt_path = base_dir / managed_receipt_path
    if not training_roster_path.is_absolute():
        training_roster_path = base_dir / training_roster_path
    for path in (
        process_manifest_path,
        managed_receipt_path,
        training_roster_path,
    ):
        if not path.is_file():
            raise FileNotFoundError(path)

    process_manifest = _load_json(
        process_manifest_path, name="training process manifest"
    )
    process_id, refit_ids, schedule = _manifest_schedule(process_manifest)
    process_manifest_sha = _file_sha256(process_manifest_path)
    managed_receipt_sha = _file_sha256(managed_receipt_path)
    managed_receipt = _load_json(
        managed_receipt_path, name="managed-generation receipt"
    )
    _verify_managed_receipt(
        managed_receipt,
        expected_receipt_sha256=managed_receipt_sha,
        actual_receipt_sha256=managed_receipt_sha,
        process_id=process_id,
        manifest_sha256=process_manifest_sha,
        refit_ids=refit_ids,
        schedule=schedule,
    )

    frame = audit_training_process_validation_frame_separation(
        process_manifest_path,
        training_roster_path,
        [row["row_id"] for row in design_rows],
        row_identity_namespace=process["row_identity_namespace"],
        roster_format=process["training_roster_format"],
        unit_id_column=process["unit_id_column"],
        stratum_column=process["stratum_column"],
    )
    if not frame.training_source_frame_validation_disjoint:
        raise ValueError(
            "training source frame overlaps external validation rows"
        )

    cert = plan["certification"]
    assert isinstance(cert, Mapping)
    group_blocks: dict[str, set[str]] = {}
    for row in design_rows:
        group_blocks.setdefault(str(row["group_id"]), set()).add(
            str(row["block_id"])
        )
    minimum_blocks = int(cert["minimum_blocks_per_group"])
    insufficient = {
        group: len(blocks)
        for group, blocks in group_blocks.items()
        if len(blocks) < minimum_blocks
    }
    if insufficient:
        raise ValueError(
            "external groups do not meet frozen minimum block support: "
            f"{insufficient!r}"
        )
    if len(refit_ids) < int(cert["minimum_refits"]):
        raise ValueError("frozen process does not meet minimum_refits")

    scoring = plan["managed_scoring"]
    assert isinstance(scoring, Mapping)
    scoring_plan_path = Path(str(scoring["plan_path"]))
    if not scoring_plan_path.is_absolute():
        scoring_plan_path = base_dir / scoring_plan_path
    if not scoring_plan_path.is_file():
        raise FileNotFoundError(scoring_plan_path)
    scoring_snapshot = snapshot_managed_external_scoring_plan_v2(
        scoring_plan_path,
        managed_receipt_path,
    )
    if tuple(scoring_snapshot["refit_ids"]) != refit_ids:
        raise ValueError(
            "managed scoring plan refit set does not match frozen process"
        )

    qualification = _external_v2_evidence_snapshot()
    implementation_snapshot = implementation_source_snapshot_for_surface(
        EXTERNAL_ENDPOINT_SURFACE_V2
    )
    runtime_snapshot = runtime_environment_snapshot_for_surface(
        EXTERNAL_ENDPOINT_SURFACE_V2
    )
    frozen_at = (
        datetime.now(timezone.utc)
        .replace(microsecond=0)
        .isoformat()
        .replace("+00:00", "Z")
    )

    manifest = {
        "schema_version": 2,
        "manifest_type": EXTERNAL_FREEZE_MANIFEST_TYPE_V2,
        "frozen_at_utc": frozen_at,
        "external_dataset_id": plan["external_dataset_id"],
        "external_design_sha256": design_sha,
        "external_design_rows": design_rows,
        "external_row_count": len(design_rows),
        "training_process": {
            "training_process_id": process_id,
            "training_process_manifest_sha256": process_manifest_sha,
            "managed_generation_receipt_sha256": managed_receipt_sha,
            "refit_ids": list(refit_ids),
            "row_identity_namespace": process["row_identity_namespace"],
            "training_roster_file_sha256": _file_sha256(
                training_roster_path
            ),
            "training_roster_semantic_sha256": str(
                process_manifest["training_roster"]["semantic_sha256"]
            ),
        },
        "score": plan["score"],
        "levels": plan["levels"],
        "certification": plan["certification"],
        "managed_scoring": {
            "scoring_plan_sha256": _file_sha256(scoring_plan_path),
            "external_data_format": scoring["external_data_format"],
            "external_row_id_column": scoring["external_row_id_column"],
            "frozen_scoring_snapshot": scoring_snapshot,
        },
        "qualification": qualification,
        "implementation": {
            "canonical_surface": EXTERNAL_ENDPOINT_SURFACE_V2,
            "implementation_lock_id": IMPLEMENTATION_LOCK_ID,
            "implementation_source_snapshot": [
                dict(row) for row in implementation_snapshot
            ],
            "environment_lock_id": ENVIRONMENT_LOCK_ID,
            "runtime_environment_snapshot": runtime_snapshot,
        },
        "boundaries": {
            "external_scores_or_outcomes_read_by_freeze_generator": False,
            "external_group_block_weight_design_frozen_before_outcomes": True,
            "training_source_frame_validation_disjoint": True,
            "managed_generation_receipt_verified": True,
            "generated_model_bytes_verified_for_scoring_freeze": True,
            "scoring_command_artifact_bytes_frozen": True,
            "historical_no_prior_external_outcome_access_machine_proven": False,
        },
    }

    output = Path(manifest_out)
    if output.exists():
        raise FileExistsError(
            f"external v2 freeze manifest already exists: {output}"
        )
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(
        json.dumps(manifest, indent=2, sort_keys=True, allow_nan=False)
        + "\n",
        encoding="utf-8",
    )
    return {
        "receipt_type": "odsp_training_process_external_freeze_receipt_v2",
        "manifest_path": str(output),
        "manifest_sha256": _file_sha256(output),
        "frozen_at_utc": frozen_at,
        "external_dataset_id": plan["external_dataset_id"],
        "external_design_sha256": design_sha,
        "external_row_count": len(design_rows),
        "training_process_id": process_id,
        "training_process_manifest_sha256": process_manifest_sha,
        "managed_generation_receipt_sha256": managed_receipt_sha,
        "managed_scoring_plan_sha256": _file_sha256(scoring_plan_path),
        "refit_count": len(refit_ids),
        "boundaries": dict(manifest["boundaries"]),
    }
