"""Pre-outcome semantic freeze for untouched external training-process v5 inference."""
from __future__ import annotations

from datetime import datetime, timezone
import json
import math
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
from .information_transfer import InformationLevelScore, validate_information_filtration
from .information_transfer_contract import _read_rows
from .training_process_confirmatory_v5 import (
    _load_json,
    _manifest_schedule,
    _sha256_text,
    _text,
    _verify_managed_receipt,
)
from .training_process_freeze_manifest import (
    _canonical_sha256,
    _file_sha256,
)
from .training_process_validation_provenance import (
    audit_training_process_validation_frame_separation,
)


EXTERNAL_FREEZE_MANIFEST_TYPE = "odsp_training_process_external_freeze_v1"
EXTERNAL_ENDPOINT_SURFACE = (
    "odsp.untouched_external_training_process_v1."
    "run_untouched_external_training_process_v1"
)
EXTERNAL_CONTRACT_ARTIFACT = (
    "ODSP_TRAINING_PROCESS_V5_UNTOUCHED_EXTERNAL_CONTRACT.json"
)
_REPOSITORY_ROOT = Path(__file__).resolve().parent.parent

_PLAN_FIELDS = {
    "schema_version",
    "external_dataset_id",
    "external_roster",
    "training_process",
    "score",
    "levels",
    "certification",
}
_ROSTER_FIELDS = {"path", "format"}
_PROCESS_FIELDS = {
    "manifest_path",
    "managed_generation_receipt_path",
    "training_roster_path",
    "row_identity_namespace",
    "training_roster_format",
    "unit_id_column",
    "stratum_column",
}
_SCORE_FIELDS = {
    "kind",
    "name",
    "orientation",
    "common_scoring_rule",
    "common_reference_measure",
}
_LEVEL_FIELDS = {"name", "information", "score_column"}
_CERT_FIELDS = {
    "alternative",
    "component_one_sided_alpha",
    "minimum_refits",
    "minimum_blocks_per_group",
    "gain_tolerance",
}


def _mapping(value: object, *, name: str) -> dict[str, object]:
    if not isinstance(value, Mapping):
        raise ValueError(f"{name} must be a JSON object")
    return dict(value)


def _reject_unknown(value: Mapping[str, object], allowed: set[str], *, name: str) -> None:
    unknown = sorted(set(value) - allowed)
    missing = sorted(allowed - set(value))
    if unknown or missing:
        raise ValueError(
            f"{name} fields mismatch: missing={missing!r}, unknown={unknown!r}"
        )


def _integer(value: object, *, name: str, minimum: int) -> int:
    if isinstance(value, bool) or not isinstance(value, int) or value < minimum:
        raise ValueError(f"{name} must be an integer >= {minimum}")
    return int(value)


def _number(value: object, *, name: str, nonnegative: bool = False) -> float:
    if isinstance(value, bool):
        raise ValueError(f"{name} must be numeric")
    try:
        result = float(value)
    except (TypeError, ValueError) as exc:
        raise ValueError(f"{name} must be numeric") from exc
    if not math.isfinite(result):
        raise ValueError(f"{name} must be finite")
    if nonnegative and result < 0:
        raise ValueError(f"{name} must be non-negative")
    return result


def _canonical_external_design(
    roster_path: Path,
    roster_format: str,
) -> tuple[list[dict[str, object]], str]:
    rows = _read_rows(roster_path, roster_format)
    if not rows:
        raise ValueError("external pre-outcome roster is empty")
    expected = {"row_id", "group_id", "block_id", "sample_weight"}
    canonical: list[dict[str, object]] = []
    seen_rows: set[str] = set()
    group_weight: dict[str, float] = {}
    block_weight: dict[tuple[str, str], float] = {}
    for index, row in enumerate(rows):
        if set(row) != expected:
            raise ValueError(
                "external pre-outcome roster must contain exactly "
                "row_id, group_id, block_id, sample_weight"
            )
        row_id = _text(row.get("row_id"), name=f"external roster row {index} row_id")
        group_id = _text(
            row.get("group_id"), name=f"external roster row {index} group_id"
        )
        block_id = _text(
            row.get("block_id"), name=f"external roster row {index} block_id"
        )
        if row_id in seen_rows:
            raise ValueError("external row IDs must be unique")
        seen_rows.add(row_id)
        weight = _number(
            row.get("sample_weight"),
            name=f"external roster row {index} sample_weight",
            nonnegative=True,
        )
        canonical.append(
            {
                "row_id": row_id,
                "group_id": group_id,
                "block_id": block_id,
                "sample_weight": weight,
            }
        )
        group_weight[group_id] = group_weight.get(group_id, 0.0) + weight
        block_key = (group_id, block_id)
        block_weight[block_key] = block_weight.get(block_key, 0.0) + weight

    if any(value <= 0 for value in group_weight.values()):
        raise ValueError("every external group must have positive total weight")
    if any(value <= 0 for value in block_weight.values()):
        raise ValueError(
            "every declared external group x block must have positive total weight"
        )
    canonical.sort(key=lambda row: str(row["row_id"]))
    return canonical, _canonical_sha256(canonical)


def _score_contract(raw: object) -> dict[str, object]:
    score = _mapping(raw, name="score")
    _reject_unknown(score, _SCORE_FIELDS, name="score")
    common_rule = score["common_scoring_rule"]
    common_reference = score["common_reference_measure"]
    if not isinstance(common_rule, bool) or not isinstance(common_reference, bool):
        raise ValueError(
            "score common_scoring_rule and common_reference_measure must be booleans"
        )
    if not common_rule or not common_reference:
        raise ValueError(
            "external process inference requires a common scoring rule and reference measure"
        )
    orientation = _text(score["orientation"], name="score.orientation")
    if orientation != "higher_is_better":
        raise ValueError("score.orientation must be 'higher_is_better'")
    return {
        "kind": _text(score["kind"], name="score.kind"),
        "name": _text(score["name"], name="score.name"),
        "orientation": orientation,
        "common_scoring_rule": True,
        "common_reference_measure": True,
    }


def _levels(raw: object) -> list[dict[str, object]]:
    if not isinstance(raw, list) or len(raw) != 3:
        raise ValueError(
            "training-process external v1 requires exactly three filtration levels"
        )
    levels: list[dict[str, object]] = []
    score_columns: set[str] = set()
    dummy = []
    for index, item in enumerate(raw):
        level = _mapping(item, name=f"levels[{index}]")
        _reject_unknown(level, _LEVEL_FIELDS, name=f"levels[{index}]")
        info_raw = level["information"]
        if not isinstance(info_raw, list):
            raise ValueError(f"levels[{index}].information must be a JSON array")
        information = tuple(
            _text(value, name=f"levels[{index}].information[{j}]")
            for j, value in enumerate(info_raw)
        )
        if len(information) != len(set(information)):
            raise ValueError(f"levels[{index}].information must be unique")
        column = _text(
            level["score_column"], name=f"levels[{index}].score_column"
        )
        if column in score_columns or column in {"row_id", "refit_id"}:
            raise ValueError("level score columns must be unique and reserved-name free")
        score_columns.add(column)
        name = _text(level["name"], name=f"levels[{index}].name")
        levels.append(
            {
                "name": name,
                "information": list(information),
                "score_column": column,
            }
        )
        dummy.append(InformationLevelScore(name, information, [0.0]))
    validate_information_filtration(dummy)
    return levels


def _certification(raw: object) -> dict[str, object]:
    cert = _mapping(raw, name="certification")
    _reject_unknown(cert, _CERT_FIELDS, name="certification")
    alternative = _text(cert["alternative"], name="certification.alternative")
    if alternative != "greater":
        raise ValueError("certification.alternative must be 'greater'")
    alpha = _number(
        cert["component_one_sided_alpha"],
        name="certification.component_one_sided_alpha",
    )
    if abs(alpha - 0.05) > 1e-15:
        raise ValueError(
            "external v1 is qualified only for component_one_sided_alpha == 0.05"
        )
    return {
        "alternative": "greater",
        "component_one_sided_alpha": alpha,
        "minimum_refits": _integer(
            cert["minimum_refits"],
            name="certification.minimum_refits",
            minimum=8,
        ),
        "minimum_blocks_per_group": _integer(
            cert["minimum_blocks_per_group"],
            name="certification.minimum_blocks_per_group",
            minimum=8,
        ),
        "gain_tolerance": _number(
            cert["gain_tolerance"],
            name="certification.gain_tolerance",
            nonnegative=True,
        ),
    }


def _prospective_external_evidence_snapshot() -> dict[str, object]:
    internal = route_confirmatory_method(
        alternative="greater",
        validation_design="independent_groups",
        information_structure="filtration",
        upstream_refits="predeclared_training_process",
        external_validation="none",
        contrast_count=2,
    )
    if internal.role != "primary_confirmatory" or not internal.qualification_key:
        raise ValueError("internal training-process v5 route is not qualified")
    artifacts = [
        dict(row)
        for row in qualification_evidence_artifacts_for_route_key(
            internal.qualification_key
        )
    ]
    contract_path = _REPOSITORY_ROOT / EXTERNAL_CONTRACT_ARTIFACT
    if not contract_path.is_file():
        raise FileNotFoundError(contract_path)
    artifacts.append(
        {
            "artifact": EXTERNAL_CONTRACT_ARTIFACT,
            "sha256": _file_sha256(contract_path),
        }
    )
    return {
        "internal_qualification_key": internal.qualification_key,
        "evidence": [row["artifact"] for row in artifacts],
        "evidence_artifacts": artifacts,
    }


def validate_training_process_external_freeze_plan(
    raw: Mapping[str, object],
) -> dict[str, object]:
    plan = _mapping(raw, name="external freeze plan")
    _reject_unknown(plan, _PLAN_FIELDS, name="external freeze plan")
    if plan["schema_version"] != 1 or isinstance(plan["schema_version"], bool):
        raise ValueError("external freeze plan schema_version must be 1")

    roster = _mapping(plan["external_roster"], name="external_roster")
    _reject_unknown(roster, _ROSTER_FIELDS, name="external_roster")
    roster_format = _text(roster["format"], name="external_roster.format").lower()
    if roster_format not in {"csv", "json"}:
        raise ValueError("external_roster.format must be 'csv' or 'json'")

    process = _mapping(plan["training_process"], name="training_process")
    _reject_unknown(process, _PROCESS_FIELDS, name="training_process")
    roster_format_training = _text(
        process["training_roster_format"],
        name="training_process.training_roster_format",
    ).lower()
    if roster_format_training not in {"csv", "json"}:
        raise ValueError("training_process.training_roster_format must be csv or json")
    stratum = process["stratum_column"]
    if stratum is not None:
        stratum = _text(stratum, name="training_process.stratum_column")

    return {
        "schema_version": 1,
        "external_dataset_id": _text(
            plan["external_dataset_id"], name="external_dataset_id"
        ),
        "external_roster": {
            "path": _text(roster["path"], name="external_roster.path"),
            "format": roster_format,
        },
        "training_process": {
            "manifest_path": _text(
                process["manifest_path"], name="training_process.manifest_path"
            ),
            "managed_generation_receipt_path": _text(
                process["managed_generation_receipt_path"],
                name="training_process.managed_generation_receipt_path",
            ),
            "training_roster_path": _text(
                process["training_roster_path"],
                name="training_process.training_roster_path",
            ),
            "row_identity_namespace": _text(
                process["row_identity_namespace"],
                name="training_process.row_identity_namespace",
            ),
            "training_roster_format": roster_format_training,
            "unit_id_column": _text(
                process["unit_id_column"], name="training_process.unit_id_column"
            ),
            "stratum_column": stratum,
        },
        "score": _score_contract(plan["score"]),
        "levels": _levels(plan["levels"]),
        "certification": _certification(plan["certification"]),
    }


def create_training_process_external_freeze_manifest_v1(
    plan_path: str | Path,
    manifest_out: str | Path,
) -> dict[str, object]:
    """Create the non-overwriting pre-outcome external semantic freeze."""

    plan_path = Path(plan_path)
    plan = validate_training_process_external_freeze_plan(
        _load_json(plan_path, name="external freeze plan")
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
        external_path, str(external_spec["format"])
    )

    process = plan["training_process"]
    assert isinstance(process, Mapping)
    manifest_path = Path(str(process["manifest_path"]))
    receipt_path = Path(str(process["managed_generation_receipt_path"]))
    training_roster_path = Path(str(process["training_roster_path"]))
    if not manifest_path.is_absolute():
        manifest_path = base_dir / manifest_path
    if not receipt_path.is_absolute():
        receipt_path = base_dir / receipt_path
    if not training_roster_path.is_absolute():
        training_roster_path = base_dir / training_roster_path
    for path in (manifest_path, receipt_path, training_roster_path):
        if not path.is_file():
            raise FileNotFoundError(path)

    process_manifest = _load_json(
        manifest_path, name="training process manifest"
    )
    process_id, frozen_refits, schedule = _manifest_schedule(process_manifest)
    process_manifest_sha = _file_sha256(manifest_path)
    managed_receipt_sha = _file_sha256(receipt_path)
    managed_receipt = _load_json(
        receipt_path, name="managed generation receipt"
    )
    _verify_managed_receipt(
        managed_receipt,
        expected_receipt_sha256=managed_receipt_sha,
        actual_receipt_sha256=managed_receipt_sha,
        process_id=process_id,
        manifest_sha256=process_manifest_sha,
        refit_ids=frozen_refits,
        schedule=schedule,
    )

    frame = audit_training_process_validation_frame_separation(
        manifest_path,
        training_roster_path,
        [row["row_id"] for row in design_rows],
        row_identity_namespace=process["row_identity_namespace"],
        roster_format=process["training_roster_format"],
        unit_id_column=process["unit_id_column"],
        stratum_column=process["stratum_column"],
    )
    if not frame.training_source_frame_validation_disjoint:
        raise ValueError(
            "training source frame overlaps the external validation roster"
        )

    cert = plan["certification"]
    assert isinstance(cert, Mapping)
    group_blocks: dict[str, set[str]] = {}
    for row in design_rows:
        group_blocks.setdefault(str(row["group_id"]), set()).add(
            str(row["block_id"])
        )
    minimum_blocks = int(cert["minimum_blocks_per_group"])
    too_small = {
        group: len(blocks)
        for group, blocks in group_blocks.items()
        if len(blocks) < minimum_blocks
    }
    if too_small:
        raise ValueError(
            "external groups do not meet frozen minimum block support: "
            f"{too_small!r}"
        )
    if len(frozen_refits) < int(cert["minimum_refits"]):
        raise ValueError(
            "frozen training process does not meet minimum_refits"
        )

    qualification = _prospective_external_evidence_snapshot()
    implementation_snapshot = implementation_source_snapshot_for_surface(
        EXTERNAL_ENDPOINT_SURFACE
    )
    environment_snapshot = runtime_environment_snapshot_for_surface(
        EXTERNAL_ENDPOINT_SURFACE
    )
    frozen_at = (
        datetime.now(timezone.utc)
        .replace(microsecond=0)
        .isoformat()
        .replace("+00:00", "Z")
    )
    manifest = {
        "schema_version": 1,
        "manifest_type": EXTERNAL_FREEZE_MANIFEST_TYPE,
        "frozen_at_utc": frozen_at,
        "external_dataset_id": plan["external_dataset_id"],
        "external_design_sha256": design_sha,
        "external_design_rows": design_rows,
        "external_row_count": len(design_rows),
        "training_process": {
            "training_process_id": process_id,
            "training_process_manifest_sha256": process_manifest_sha,
            "managed_generation_receipt_sha256": managed_receipt_sha,
            "refit_ids": list(frozen_refits),
            "row_identity_namespace": process["row_identity_namespace"],
            "training_roster_file_sha256": _file_sha256(training_roster_path),
            "training_roster_semantic_sha256": frame.training_source_unit_count
            and str(process_manifest["training_roster"]["semantic_sha256"]),
        },
        "score": plan["score"],
        "levels": plan["levels"],
        "certification": plan["certification"],
        "qualification": qualification,
        "implementation": {
            "canonical_surface": EXTERNAL_ENDPOINT_SURFACE,
            "implementation_lock_id": IMPLEMENTATION_LOCK_ID,
            "implementation_source_snapshot": [
                dict(row) for row in implementation_snapshot
            ],
            "environment_lock_id": ENVIRONMENT_LOCK_ID,
            "runtime_environment_snapshot": environment_snapshot,
        },
        "boundaries": {
            "external_scores_read_by_freeze_generator": False,
            "external_group_block_weight_design_frozen_before_scores": True,
            "training_source_frame_validation_disjoint": True,
            "managed_generation_receipt_verified": True,
            "historical_no_prior_external_outcome_access_machine_proven": False,
        },
    }

    out = Path(manifest_out)
    if out.exists():
        raise FileExistsError(
            f"external process freeze manifest already exists: {out}"
        )
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(
        json.dumps(manifest, indent=2, sort_keys=True, allow_nan=False) + "\n",
        encoding="utf-8",
    )
    return {
        "receipt_type": "odsp_training_process_external_freeze_receipt_v1",
        "manifest_path": str(out),
        "manifest_sha256": _file_sha256(out),
        "frozen_at_utc": frozen_at,
        "external_dataset_id": plan["external_dataset_id"],
        "external_design_sha256": design_sha,
        "external_row_count": len(design_rows),
        "training_process_id": process_id,
        "training_process_manifest_sha256": process_manifest_sha,
        "managed_generation_receipt_sha256": managed_receipt_sha,
        "refit_count": len(frozen_refits),
        "boundaries": dict(manifest["boundaries"]),
    }
