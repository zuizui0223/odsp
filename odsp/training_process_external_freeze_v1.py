"""Pre-outcome semantic freeze for untouched external training-process v5 inference."""
from __future__ import annotations

from datetime import datetime, timezone
import hashlib
import json
import math
from pathlib import Path
from typing import Mapping, Sequence

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
    QUALIFICATION_EVIDENCE_REGISTRY_ID,
    qualification_evidence_artifacts_for_route_key,
)
from .information_transfer_contract import _read_rows
from .training_process_confirmatory_v5 import (
    _load_json,
    _manifest_schedule,
    _verify_managed_receipt,
)
from .training_process_freeze_manifest import _file_sha256
from .training_process_managed_generation import (
    _relative_safe_path,
    _runtime_snapshot,
)
from .training_process_validation_provenance import (
    audit_training_process_validation_frame_separation,
)


MANIFEST_TYPE = "odsp_training_process_v5_pre_external_outcome_freeze_v1"
FREEZE_RECEIPT_TYPE = "odsp_training_process_v5_external_freeze_receipt_v1"
INTERNAL_SURFACE = (
    "odsp.training_process_confirmatory_v5."
    "certify_predeclared_training_process_positive_information_v5"
)
EXTERNAL_SURFACE = (
    "odsp.training_process_untouched_external_v5."
    "run_untouched_external_training_process_v5"
)
_PLAN_FIELDS = {
    "schema_version",
    "external_dataset_id",
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
_SCORE_FIELDS = {
    "kind",
    "name",
    "orientation",
    "common_scoring_rule",
    "common_reference_measure",
}
_SCORING_FIELDS = {
    "working_directory",
    "command",
    "command_artifacts",
    "timeout_seconds",
    "environment_allowlist",
}
_CERT_FIELDS = {
    "component_one_sided_alpha",
    "minimum_refits",
    "minimum_blocks_per_group",
    "gain_tolerance",
}


def _text(value: object, *, name: str) -> str:
    if not isinstance(value, str) or not value.strip():
        raise ValueError(f"{name} must be non-empty text")
    return value.strip()


def _number(value: object, *, name: str) -> float:
    if isinstance(value, bool):
        raise ValueError(f"{name} must be numeric")
    try:
        number = float(value)
    except (TypeError, ValueError) as exc:
        raise ValueError(f"{name} must be numeric") from exc
    if not math.isfinite(number):
        raise ValueError(f"{name} must be finite")
    return number


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


def _normalize_score(raw: object) -> dict[str, object]:
    if not isinstance(raw, Mapping) or set(raw) != _SCORE_FIELDS:
        raise ValueError("score fields are invalid")
    common_rule = raw["common_scoring_rule"]
    common_reference = raw["common_reference_measure"]
    if not isinstance(common_rule, bool) or not isinstance(common_reference, bool):
        raise ValueError(
            "score common_scoring_rule/common_reference_measure must be booleans"
        )
    if not common_rule or not common_reference:
        raise ValueError(
            "external confirmatory score requires common scoring rule and reference measure"
        )
    return {
        "kind": _text(raw["kind"], name="score.kind"),
        "name": _text(raw["name"], name="score.name"),
        "orientation": _text(raw["orientation"], name="score.orientation"),
        "common_scoring_rule": True,
        "common_reference_measure": True,
    }


def _normalize_levels(raw: object) -> list[dict[str, object]]:
    if not isinstance(raw, list) or len(raw) != 3:
        raise ValueError("v5 external levels must contain exactly three ordered levels")
    levels: list[dict[str, object]] = []
    names: set[str] = set()
    for i, item in enumerate(raw):
        if not isinstance(item, Mapping) or set(item) != {"name", "information"}:
            raise ValueError(f"levels[{i}] fields are invalid")
        name = _text(item["name"], name=f"levels[{i}].name")
        if name in names:
            raise ValueError("level names must be unique")
        names.add(name)
        information = item["information"]
        if not isinstance(information, list):
            raise ValueError(f"levels[{i}].information must be a JSON array")
        vals = [_text(x, name=f"levels[{i}].information") for x in information]
        if len(vals) != len(set(vals)):
            raise ValueError("information labels within a level must be unique")
        levels.append({"name": name, "information": vals})
    for lower, upper in zip(levels, levels[1:]):
        if not set(lower["information"]).issubset(set(upper["information"])):
            raise ValueError("levels must form an ordered information filtration")
    return levels


def _normalize_certification(raw: object) -> dict[str, object]:
    if not isinstance(raw, Mapping) or set(raw) != _CERT_FIELDS:
        raise ValueError("certification fields are invalid")
    alpha = _number(raw["component_one_sided_alpha"], name="component_one_sided_alpha")
    if not 0.0 < alpha < 0.5:
        raise ValueError("component_one_sided_alpha must lie in (0, 0.5)")
    gain_tolerance = _number(raw["gain_tolerance"], name="gain_tolerance")
    if gain_tolerance < 0:
        raise ValueError("gain_tolerance must be non-negative")
    return {
        "component_one_sided_alpha": alpha,
        "minimum_refits": _integer(raw["minimum_refits"], name="minimum_refits", minimum=8),
        "minimum_blocks_per_group": _integer(
            raw["minimum_blocks_per_group"],
            name="minimum_blocks_per_group",
            minimum=8,
        ),
        "gain_tolerance": gain_tolerance,
    }


def _normalize_scoring(raw: object) -> dict[str, object]:
    if not isinstance(raw, Mapping) or set(raw) != _SCORING_FIELDS:
        raise ValueError("scoring fields are invalid")
    working_directory = _text(
        raw["working_directory"], name="scoring.working_directory"
    )
    command_raw = raw["command"]
    if (
        not isinstance(command_raw, list)
        or not command_raw
        or any(not isinstance(x, str) or not x.strip() for x in command_raw)
    ):
        raise ValueError("scoring.command must be a non-empty JSON string array")
    command = [str(x) for x in command_raw]
    joined = "\n".join(command)
    for placeholder in (
        "{refit_id}",
        "{model_manifest_path}",
        "{validation_data_path}",
        "{scoring_spec_path}",
        "{output_path}",
    ):
        if placeholder not in joined:
            raise ValueError(
                f"scoring.command must contain required placeholder {placeholder}"
            )
    artifacts_raw = raw["command_artifacts"]
    if not isinstance(artifacts_raw, list) or not artifacts_raw:
        raise ValueError("scoring.command_artifacts must be non-empty")
    artifacts = [
        _relative_safe_path(
            value, name=f"scoring.command_artifacts[{index}]"
        )
        for index, value in enumerate(artifacts_raw)
    ]
    if len(artifacts) != len(set(artifacts)):
        raise ValueError("scoring.command_artifacts must be unique")
    timeout = raw["timeout_seconds"]
    if isinstance(timeout, bool) or not isinstance(timeout, int) or not 1 <= timeout <= 86400:
        raise ValueError("scoring.timeout_seconds must be an integer in [1, 86400]")
    allowlist_raw = raw["environment_allowlist"]
    if not isinstance(allowlist_raw, list):
        raise ValueError("scoring.environment_allowlist must be a JSON array")
    allowlist = [
        _text(value, name=f"scoring.environment_allowlist[{index}]")
        for index, value in enumerate(allowlist_raw)
    ]
    if len(allowlist) != len(set(allowlist)):
        raise ValueError("scoring.environment_allowlist must be unique")
    return {
        "working_directory": working_directory,
        "command": command,
        "command_artifacts": artifacts,
        "timeout_seconds": int(timeout),
        "environment_allowlist": allowlist,
    }


def _normalize_plan(raw: Mapping[str, object]) -> dict[str, object]:
    if set(raw) != _PLAN_FIELDS:
        raise ValueError(
            f"external freeze plan fields mismatch: {sorted(set(raw) ^ _PLAN_FIELDS)!r}"
        )
    if raw.get("schema_version") != 1 or isinstance(raw.get("schema_version"), bool):
        raise ValueError("external freeze plan schema_version must be 1")
    roster = raw["roster"]
    if not isinstance(roster, Mapping) or set(roster) != _ROSTER_FIELDS:
        raise ValueError("roster fields are invalid")
    roster_format = _text(roster["format"], name="roster.format").lower()
    if roster_format not in {"csv", "json"}:
        raise ValueError("roster.format must be csv or json")

    tr = raw["training_roster"]
    if not isinstance(tr, Mapping) or set(tr) != _TRAINING_ROSTER_FIELDS:
        raise ValueError("training_roster fields are invalid")
    tr_format = _text(tr["format"], name="training_roster.format").lower()
    if tr_format not in {"csv", "json"}:
        raise ValueError("training_roster.format must be csv or json")
    stratum = tr["stratum_column"]
    stratum_column = None if stratum is None else _text(
        stratum, name="training_roster.stratum_column"
    )
    unit_col = _text(tr["unit_id_column"], name="training_roster.unit_id_column")
    if stratum_column == unit_col:
        raise ValueError("training unit and stratum columns must differ")

    return {
        "schema_version": 1,
        "external_dataset_id": _text(
            raw["external_dataset_id"], name="external_dataset_id"
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
            "path": _text(tr["path"], name="training_roster.path"),
            "format": tr_format,
            "unit_id_column": unit_col,
            "stratum_column": stratum_column,
        },
        "score": _normalize_score(raw["score"]),
        "levels": _normalize_levels(raw["levels"]),
        "certification": _normalize_certification(raw["certification"]),
        "scoring": _normalize_scoring(raw["scoring"]),
    }


def _external_design_rows(
    rows: Sequence[Mapping[str, object]],
) -> tuple[list[dict[str, object]], dict[str, int]]:
    expected = {"row_id", "group_id", "block_id", "sample_weight"}
    canonical: list[dict[str, object]] = []
    seen: set[str] = set()
    positive_blocks: dict[str, set[str]] = {}
    positive_group_mass: dict[str, float] = {}
    for i, row in enumerate(rows):
        if set(row) != expected:
            raise ValueError(
                "pre-outcome external roster must contain exactly "
                "row_id, group_id, block_id, sample_weight"
            )
        row_id = _text(row["row_id"], name=f"roster row {i} row_id")
        group_id = _text(row["group_id"], name=f"roster row {i} group_id")
        block_id = _text(row["block_id"], name=f"roster row {i} block_id")
        if row_id in seen:
            raise ValueError("external row IDs must be unique")
        seen.add(row_id)
        weight = _number(row["sample_weight"], name=f"roster row {i} sample_weight")
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
            positive_group_mass[group_id] = positive_group_mass.get(group_id, 0.0) + weight
    if not canonical:
        raise ValueError("external roster must not be empty")
    if not positive_group_mass:
        raise ValueError("external roster has no positive-weight support")
    canonical.sort(key=lambda row: row["row_id"])
    block_counts = {g: len(positive_blocks[g]) for g in sorted(positive_blocks)}
    return canonical, block_counts


def _model_artifact_snapshot(receipt: Mapping[str, object]) -> list[dict[str, str]]:
    executions = receipt.get("executions")
    if not isinstance(executions, list) or not executions:
        raise ValueError("managed receipt executions must be non-empty")
    rows: list[dict[str, str]] = []
    for execution in executions:
        if not isinstance(execution, Mapping):
            raise ValueError("managed execution must be an object")
        refit_id = _text(execution.get("refit_id"), name="managed refit_id")
        artifacts = execution.get("artifacts")
        if not isinstance(artifacts, list) or not artifacts:
            raise ValueError("managed execution artifacts must be non-empty")
        for artifact in artifacts:
            if not isinstance(artifact, Mapping):
                raise ValueError("managed artifact must be an object")
            artifact_id = _text(artifact.get("artifact_id"), name="artifact_id")
            digest = _text(artifact.get("sha256"), name="artifact sha256")
            if len(digest) != 64 or digest.lower() != digest:
                raise ValueError("artifact sha256 must be lowercase SHA256")
            int(digest, 16)
            rows.append(
                {
                    "refit_id": refit_id,
                    "artifact_id": artifact_id,
                    "sha256": digest,
                }
            )
    rows.sort(key=lambda x: (x["refit_id"], x["artifact_id"]))
    return rows


def build_internal_v5_route_snapshot() -> dict[str, object]:
    decision = route_confirmatory_method(
        alternative="greater",
        validation_design="independent_groups",
        information_structure="filtration",
        upstream_refits="predeclared_training_process",
        external_validation="none",
        contrast_count=2,
    )
    if decision.role != "primary_confirmatory" or decision.canonical_surface != INTERNAL_SURFACE:
        raise ValueError("internal training-process v5 route is not qualified")
    if not decision.qualification_key:
        raise ValueError("internal v5 route has no qualification key")
    artifacts = qualification_evidence_artifacts_for_route_key(
        decision.qualification_key
    )
    if not artifacts:
        raise ValueError("internal v5 route has no frozen evidence artifact snapshot")
    return {
        "role": decision.role,
        "canonical_surface": decision.canonical_surface,
        "qualification_key": decision.qualification_key,
        "qualification_registry_id": QUALIFICATION_EVIDENCE_REGISTRY_ID,
        "qualification_evidence": list(decision.qualification_evidence),
        "qualification_evidence_artifacts": [dict(row) for row in artifacts],
    }


def create_training_process_v5_external_freeze(
    plan_path: str | Path,
    manifest_out: str | Path,
    receipt_out: str | Path,
) -> dict[str, object]:
    """Create non-overwriting outcome-free external freeze manifest and receipt."""

    plan_path = Path(plan_path)
    plan = _normalize_plan(_load_json(plan_path, name="external freeze plan"))
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

    raw_roster = _read_rows(roster_path, plan["roster"]["format"])
    design_rows, block_counts = _external_design_rows(raw_roster)
    minimum_blocks = int(plan["certification"]["minimum_blocks_per_group"])
    if any(count < minimum_blocks for count in block_counts.values()):
        raise ValueError(
            "every positive-weight validation group must meet minimum_blocks_per_group"
        )
    row_ids = [row["row_id"] for row in design_rows]

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
        raise ValueError("training source frame overlaps frozen external roster")

    scoring = plan["scoring"]
    scoring_working_dir = Path(str(scoring["working_directory"]))
    if not scoring_working_dir.is_absolute():
        scoring_working_dir = base / scoring_working_dir
    if not scoring_working_dir.is_dir():
        raise FileNotFoundError(scoring_working_dir)
    scoring_command_artifacts: list[dict[str, str]] = []
    for declared_path in scoring["command_artifacts"]:
        artifact_path = scoring_working_dir / str(declared_path)
        if artifact_path.is_symlink() or not artifact_path.is_file():
            raise ValueError(
                f"scoring command artifact must be a regular non-symlink file: {artifact_path}"
            )
        scoring_command_artifacts.append(
            {
                "path": str(declared_path),
                "sha256": _file_sha256(artifact_path),
            }
        )
    scoring_runtime = _runtime_snapshot(scoring["environment_allowlist"])

    internal_route = build_internal_v5_route_snapshot()
    external_impl = implementation_source_snapshot_for_surface(EXTERNAL_SURFACE)
    external_env = runtime_environment_snapshot_for_surface(EXTERNAL_SURFACE)

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
        "external_dataset_id": plan["external_dataset_id"],
        "row_identity_namespace": plan["row_identity_namespace"],
        "external_design_sha256": _canonical_sha256(design_rows),
        "external_row_count": len(design_rows),
        "external_group_count": len(block_counts),
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
        "internal_qualified_route": internal_route,
        "external_endpoint": {
            "canonical_surface": EXTERNAL_SURFACE,
            "implementation_lock_id": IMPLEMENTATION_LOCK_ID,
            "implementation_source_snapshot": [dict(row) for row in external_impl],
            "environment_lock_id": ENVIRONMENT_LOCK_ID,
            "runtime_environment_snapshot": external_env,
        },
        "managed_scoring_plan": {
            "working_directory": plan["scoring"]["working_directory"],
            "command": list(plan["scoring"]["command"]),
            "command_artifact_snapshot": scoring_command_artifacts,
            "timeout_seconds": int(plan["scoring"]["timeout_seconds"]),
            "environment_allowlist": list(plan["scoring"]["environment_allowlist"]),
            "runtime_environment_snapshot": scoring_runtime,
        },
        "score": plan["score"],
        "levels": plan["levels"],
        "certification": plan["certification"],
        "boundaries": {
            "external_outcomes_read_by_freeze_generator": False,
            "external_predictions_read_by_freeze_generator": False,
            "validation_outcome_bytes_read_by_freeze_generator": False,
            "scoring_command_artifact_bytes_frozen": True,
            "scoring_runtime_environment_frozen": True,
            "caller_supplied_freeze_timestamp_allowed": False,
            "manifest_overwrite_allowed": False,
            "historical_no_prior_outcome_access_machine_proven": False,
        },
    }

    manifest_path = Path(manifest_out)
    receipt_path = Path(receipt_out)
    if manifest_path.exists():
        raise FileExistsError(f"external freeze manifest already exists: {manifest_path}")
    if receipt_path.exists():
        raise FileExistsError(f"external freeze receipt already exists: {receipt_path}")
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
        "manifest_path": str(manifest_path),
        "manifest_sha256": _file_sha256(manifest_path),
        "freeze_plan_sha256": _file_sha256(plan_path),
        "external_roster_file_sha256": _file_sha256(roster_path),
        "external_design_sha256": manifest["external_design_sha256"],
        "external_row_count": len(design_rows),
        "training_process_id": process_id,
        "training_process_manifest_sha256": process_manifest_sha,
        "managed_generation_receipt_sha256": managed_receipt_sha,
        "boundaries": manifest["boundaries"],
    }
    receipt_path.write_text(
        json.dumps(receipt, indent=2, sort_keys=True, allow_nan=False) + "\n",
        encoding="utf-8",
    )
    return {
        "manifest": manifest,
        "receipt": receipt,
        "receipt_path": str(receipt_path),
        "receipt_sha256": _file_sha256(receipt_path),
    }
