"""Untouched-external endpoint for the qualified training-process v5 route."""
from __future__ import annotations

from dataclasses import dataclass
import json
import math
from pathlib import Path
from typing import Mapping

import numpy as np

from .confirmatory_environment_lock import (
    ENVIRONMENT_LOCK_ID,
    runtime_environment_snapshot_for_surface,
)
from .confirmatory_implementation_lock import (
    IMPLEMENTATION_LOCK_ID,
    implementation_source_snapshot_for_surface,
)
from .information_transfer_contract import _read_rows
from .refit_information_transfer import RefitInformationLevelScores
from .training_process_confirmatory_v5 import (
    TrainingProcessConfirmatoryV5Certification,
    certify_predeclared_training_process_positive_information_v5,
)
from .training_process_external_freeze_v1 import (
    EXTERNAL_ENDPOINT_SURFACE,
    EXTERNAL_FREEZE_MANIFEST_TYPE,
    _canonical_external_design,
    _load_json,
    _prospective_external_evidence_snapshot,
    _sha256_text,
    _text,
)
from .training_process_freeze_manifest import _file_sha256


_RUNTIME_FIELDS = {
    "schema_version",
    "freeze_manifest",
    "score_table",
    "training_process_runtime",
}
_FREEZE_FIELDS = {"path", "sha256", "frozen_at_utc"}
_SCORE_TABLE_FIELDS = {"path", "format"}
_PROCESS_RUNTIME_FIELDS = {
    "manifest_path",
    "managed_generation_receipt_path",
    "training_roster_path",
    "training_roster_format",
    "unit_id_column",
    "stratum_column",
}


@dataclass(frozen=True)
class UntouchedExternalTrainingProcessV1Receipt:
    receipt_type: str
    external_dataset_id: str
    freeze_manifest_sha256: str
    external_design_sha256: str
    external_row_count: int
    refit_count: int
    training_process_id: str
    freeze_manifest_semantics_verified: bool
    external_row_refit_cartesian_product_verified: bool
    external_group_block_weight_design_from_freeze_only: bool
    qualification_evidence_snapshot_verified: bool
    implementation_source_snapshot_verified: bool
    runtime_environment_snapshot_verified: bool
    training_process_provenance_verified: bool
    historical_no_prior_external_outcome_access_machine_proven: bool
    score_table_derivation_from_generated_models_independently_proven: bool
    certification: TrainingProcessConfirmatoryV5Certification

    def as_dict(self) -> dict[str, object]:
        return {
            "receipt_type": self.receipt_type,
            "external_dataset_id": self.external_dataset_id,
            "freeze_manifest_sha256": self.freeze_manifest_sha256,
            "external_design_sha256": self.external_design_sha256,
            "external_row_count": self.external_row_count,
            "refit_count": self.refit_count,
            "training_process_id": self.training_process_id,
            "freeze_manifest_semantics_verified": self.freeze_manifest_semantics_verified,
            "external_row_refit_cartesian_product_verified": self.external_row_refit_cartesian_product_verified,
            "external_group_block_weight_design_from_freeze_only": self.external_group_block_weight_design_from_freeze_only,
            "qualification_evidence_snapshot_verified": self.qualification_evidence_snapshot_verified,
            "implementation_source_snapshot_verified": self.implementation_source_snapshot_verified,
            "runtime_environment_snapshot_verified": self.runtime_environment_snapshot_verified,
            "training_process_provenance_verified": self.training_process_provenance_verified,
            "historical_no_prior_external_outcome_access_machine_proven": self.historical_no_prior_external_outcome_access_machine_proven,
            "score_table_derivation_from_generated_models_independently_proven": self.score_table_derivation_from_generated_models_independently_proven,
            "certification": self.certification.as_dict(),
        }


def _mapping(value: object, *, name: str) -> dict[str, object]:
    if not isinstance(value, Mapping):
        raise ValueError(f"{name} must be a JSON object")
    return dict(value)


def _exact_fields(
    value: Mapping[str, object],
    expected: set[str],
    *,
    name: str,
) -> None:
    missing = sorted(expected - set(value))
    extra = sorted(set(value) - expected)
    if missing or extra:
        raise ValueError(
            f"{name} fields mismatch: missing={missing!r}, extra={extra!r}"
        )


def _score_value(value: object, *, name: str) -> float:
    if isinstance(value, bool):
        raise ValueError(f"{name} must be numeric")
    try:
        number = float(value)
    except (TypeError, ValueError) as exc:
        raise ValueError(f"{name} must be numeric") from exc
    if math.isnan(number) or number == math.inf:
        raise ValueError(f"{name} may be finite or -inf, but not NaN or +inf")
    return number


def _runtime_contract(path: Path) -> dict[str, object]:
    raw = _load_json(path, name="external runtime contract")
    _exact_fields(raw, _RUNTIME_FIELDS, name="external runtime contract")
    if raw["schema_version"] != 1 or isinstance(raw["schema_version"], bool):
        raise ValueError("external runtime contract schema_version must be 1")

    freeze = _mapping(raw["freeze_manifest"], name="freeze_manifest")
    _exact_fields(freeze, _FREEZE_FIELDS, name="freeze_manifest")
    score = _mapping(raw["score_table"], name="score_table")
    _exact_fields(score, _SCORE_TABLE_FIELDS, name="score_table")
    fmt = _text(score["format"], name="score_table.format").lower()
    if fmt not in {"csv", "json"}:
        raise ValueError("score_table.format must be csv or json")

    process = _mapping(
        raw["training_process_runtime"], name="training_process_runtime"
    )
    _exact_fields(
        process,
        _PROCESS_RUNTIME_FIELDS,
        name="training_process_runtime",
    )
    roster_format = _text(
        process["training_roster_format"],
        name="training_process_runtime.training_roster_format",
    ).lower()
    if roster_format not in {"csv", "json"}:
        raise ValueError("training_process_runtime.training_roster_format must be csv or json")
    stratum = process["stratum_column"]
    if stratum is not None:
        stratum = _text(
            stratum, name="training_process_runtime.stratum_column"
        )

    return {
        "schema_version": 1,
        "freeze_manifest": {
            "path": _text(freeze["path"], name="freeze_manifest.path"),
            "sha256": _sha256_text(
                freeze["sha256"], name="freeze_manifest.sha256"
            ),
            "frozen_at_utc": _text(
                freeze["frozen_at_utc"],
                name="freeze_manifest.frozen_at_utc",
            ),
        },
        "score_table": {
            "path": _text(score["path"], name="score_table.path"),
            "format": fmt,
        },
        "training_process_runtime": {
            "manifest_path": _text(
                process["manifest_path"],
                name="training_process_runtime.manifest_path",
            ),
            "managed_generation_receipt_path": _text(
                process["managed_generation_receipt_path"],
                name="training_process_runtime.managed_generation_receipt_path",
            ),
            "training_roster_path": _text(
                process["training_roster_path"],
                name="training_process_runtime.training_roster_path",
            ),
            "training_roster_format": roster_format,
            "unit_id_column": _text(
                process["unit_id_column"],
                name="training_process_runtime.unit_id_column",
            ),
            "stratum_column": stratum,
        },
    }


def _resolve(base: Path, value: str) -> Path:
    path = Path(value)
    return path if path.is_absolute() else base / path


def _normalize_manifest(raw: object) -> dict[str, object]:
    manifest = _mapping(raw, name="external freeze manifest")
    if manifest.get("schema_version") != 1:
        raise ValueError("external freeze manifest schema_version must be 1")
    if manifest.get("manifest_type") != EXTERNAL_FREEZE_MANIFEST_TYPE:
        raise ValueError("external freeze manifest_type is not recognized")
    return manifest


def run_untouched_external_training_process_v1(
    runtime_contract_path: str | Path,
) -> UntouchedExternalTrainingProcessV1Receipt:
    """Verify the pre-outcome freeze, then run v5 on untouched external scores."""

    runtime_contract_path = Path(runtime_contract_path)
    contract = _runtime_contract(runtime_contract_path)
    base_dir = runtime_contract_path.parent

    freeze_spec = contract["freeze_manifest"]
    assert isinstance(freeze_spec, Mapping)
    freeze_path = _resolve(base_dir, str(freeze_spec["path"]))
    if not freeze_path.is_file():
        raise FileNotFoundError(freeze_path)
    freeze_sha = _file_sha256(freeze_path)
    if freeze_sha != freeze_spec["sha256"]:
        raise ValueError("external freeze manifest SHA256 mismatch")
    manifest = _normalize_manifest(
        _load_json(freeze_path, name="external freeze manifest")
    )
    if manifest.get("frozen_at_utc") != freeze_spec["frozen_at_utc"]:
        raise ValueError("external freeze timestamp mismatch")

    design_rows = manifest.get("external_design_rows")
    if not isinstance(design_rows, list) or not design_rows:
        raise ValueError("external freeze manifest design rows are missing")
    # Recompute canonical semantics from the manifest itself.
    normalized_design = []
    for index, raw in enumerate(design_rows):
        row = _mapping(raw, name=f"external_design_rows[{index}]")
        _exact_fields(
            row,
            {"row_id", "group_id", "block_id", "sample_weight"},
            name=f"external_design_rows[{index}]",
        )
        weight = float(row["sample_weight"])
        if not math.isfinite(weight) or weight < 0:
            raise ValueError("frozen external sample weights must be finite non-negative")
        normalized_design.append(
            {
                "row_id": _text(row["row_id"], name="frozen row_id"),
                "group_id": _text(row["group_id"], name="frozen group_id"),
                "block_id": _text(row["block_id"], name="frozen block_id"),
                "sample_weight": weight,
            }
        )
    normalized_design.sort(key=lambda row: row["row_id"])
    from .training_process_freeze_manifest import _canonical_sha256

    design_sha = _canonical_sha256(normalized_design)
    if design_sha != manifest.get("external_design_sha256"):
        raise ValueError("external freeze design semantic hash mismatch")
    if len(normalized_design) != manifest.get("external_row_count"):
        raise ValueError("external freeze row count mismatch")

    qualification = _prospective_external_evidence_snapshot()
    if qualification != manifest.get("qualification"):
        raise ValueError("external freeze qualification evidence snapshot mismatch")

    implementation = _mapping(
        manifest.get("implementation"), name="external freeze implementation"
    )
    if implementation.get("canonical_surface") != EXTERNAL_ENDPOINT_SURFACE:
        raise ValueError("external freeze canonical surface mismatch")
    if implementation.get("implementation_lock_id") != IMPLEMENTATION_LOCK_ID:
        raise ValueError("external freeze implementation lock ID mismatch")
    current_source = [
        dict(row)
        for row in implementation_source_snapshot_for_surface(
            EXTERNAL_ENDPOINT_SURFACE
        )
    ]
    if current_source != implementation.get("implementation_source_snapshot"):
        raise ValueError("external endpoint implementation source snapshot mismatch")
    if implementation.get("environment_lock_id") != ENVIRONMENT_LOCK_ID:
        raise ValueError("external freeze runtime environment lock ID mismatch")
    current_environment = runtime_environment_snapshot_for_surface(
        EXTERNAL_ENDPOINT_SURFACE
    )
    if current_environment != implementation.get("runtime_environment_snapshot"):
        raise ValueError("external endpoint runtime environment snapshot mismatch")

    process_frozen = _mapping(
        manifest.get("training_process"),
        name="external freeze training_process",
    )
    process_runtime = contract["training_process_runtime"]
    assert isinstance(process_runtime, Mapping)
    process_manifest_path = _resolve(
        base_dir, str(process_runtime["manifest_path"])
    )
    managed_receipt_path = _resolve(
        base_dir, str(process_runtime["managed_generation_receipt_path"])
    )
    training_roster_path = _resolve(
        base_dir, str(process_runtime["training_roster_path"])
    )
    if _file_sha256(process_manifest_path) != process_frozen.get(
        "training_process_manifest_sha256"
    ):
        raise ValueError("runtime training-process manifest bytes changed")
    if _file_sha256(managed_receipt_path) != process_frozen.get(
        "managed_generation_receipt_sha256"
    ):
        raise ValueError("runtime managed-generation receipt bytes changed")
    if _file_sha256(training_roster_path) != process_frozen.get(
        "training_roster_file_sha256"
    ):
        raise ValueError("runtime training roster bytes changed")

    refit_ids_raw = process_frozen.get("refit_ids")
    if not isinstance(refit_ids_raw, list) or not refit_ids_raw:
        raise ValueError("external freeze refit_ids must be non-empty")
    refit_ids = tuple(sorted(_text(x, name="frozen refit_id") for x in refit_ids_raw))
    if len(refit_ids) != len(set(refit_ids)):
        raise ValueError("external freeze refit_ids must be unique")

    levels_raw = manifest.get("levels")
    if not isinstance(levels_raw, list) or len(levels_raw) != 3:
        raise ValueError("external freeze levels must contain exactly three levels")
    levels = []
    score_columns = []
    for index, raw in enumerate(levels_raw):
        level = _mapping(raw, name=f"external freeze levels[{index}]")
        column = _text(
            level.get("score_column"),
            name=f"external freeze levels[{index}].score_column",
        )
        score_columns.append(column)
        info_raw = level.get("information")
        if not isinstance(info_raw, list):
            raise ValueError("frozen level information must be a list")
        levels.append(
            {
                "name": _text(level.get("name"), name="frozen level name"),
                "information": tuple(
                    _text(x, name="frozen information") for x in info_raw
                ),
                "score_column": column,
            }
        )

    score_spec = contract["score_table"]
    assert isinstance(score_spec, Mapping)
    score_path = _resolve(base_dir, str(score_spec["path"]))
    if not score_path.is_file():
        raise FileNotFoundError(score_path)
    score_rows = _read_rows(score_path, str(score_spec["format"]))
    expected_columns = {"row_id", "refit_id", *score_columns}
    expected_row_ids = tuple(row["row_id"] for row in normalized_design)
    expected_row_set = set(expected_row_ids)
    expected_pairs = {
        (row_id, refit_id)
        for row_id in expected_row_ids
        for refit_id in refit_ids
    }
    observed: dict[tuple[str, str], dict[str, float]] = {}
    for index, raw in enumerate(score_rows):
        if set(raw) != expected_columns:
            raise ValueError(
                "external score table columns do not exactly match frozen semantics"
            )
        row_id = _text(raw.get("row_id"), name=f"score row {index} row_id")
        refit_id = _text(
            raw.get("refit_id"), name=f"score row {index} refit_id"
        )
        if row_id not in expected_row_set:
            raise ValueError("external score table contains an unfrozen row ID")
        if refit_id not in refit_ids:
            raise ValueError("external score table contains an unfrozen refit ID")
        key = (row_id, refit_id)
        if key in observed:
            raise ValueError("external score table contains duplicate row x refit cells")
        observed[key] = {
            column: _score_value(
                raw.get(column), name=f"score row {index} {column}"
            )
            for column in score_columns
        }
    if set(observed) != expected_pairs:
        missing = len(expected_pairs - set(observed))
        extra = len(set(observed) - expected_pairs)
        raise ValueError(
            "external score table must contain the exact frozen row x refit "
            f"Cartesian product; missing={missing}, extra={extra}"
        )

    matrices = []
    for level in levels:
        matrix = np.empty((len(refit_ids), len(expected_row_ids)), dtype=float)
        for r_index, refit_id in enumerate(refit_ids):
            for row_index, row_id in enumerate(expected_row_ids):
                matrix[r_index, row_index] = observed[(row_id, refit_id)][
                    level["score_column"]
                ]
        matrices.append(
            RefitInformationLevelScores(
                level["name"],
                level["information"],
                matrix,
            )
        )

    cert = _mapping(manifest.get("certification"), name="external freeze certification")
    groups = tuple(row["group_id"] for row in normalized_design)
    blocks = tuple(row["block_id"] for row in normalized_design)
    weights = tuple(float(row["sample_weight"]) for row in normalized_design)

    result = certify_predeclared_training_process_positive_information_v5(
        tuple(matrices),
        groups,
        blocks=blocks,
        validation_row_ids=expected_row_ids,
        refit_ids=refit_ids,
        training_process_manifest_path=process_manifest_path,
        managed_generation_receipt_path=managed_receipt_path,
        managed_generation_receipt_sha256=process_frozen[
            "managed_generation_receipt_sha256"
        ],
        training_roster_path=training_roster_path,
        row_identity_namespace=process_frozen["row_identity_namespace"],
        roster_format=process_runtime["training_roster_format"],
        unit_id_column=process_runtime["unit_id_column"],
        stratum_column=process_runtime["stratum_column"],
        score_name=str(_mapping(manifest.get("score"), name="score")["name"]),
        sample_weight=weights,
        component_one_sided_alpha=float(cert["component_one_sided_alpha"]),
        minimum_refits=int(cert["minimum_refits"]),
        minimum_blocks_per_group=int(cert["minimum_blocks_per_group"]),
        gain_tolerance=float(cert["gain_tolerance"]),
    )

    return UntouchedExternalTrainingProcessV1Receipt(
        receipt_type="odsp_untouched_external_training_process_v1",
        external_dataset_id=_text(
            manifest.get("external_dataset_id"),
            name="external_dataset_id",
        ),
        freeze_manifest_sha256=freeze_sha,
        external_design_sha256=design_sha,
        external_row_count=len(expected_row_ids),
        refit_count=len(refit_ids),
        training_process_id=result.training_process_id,
        freeze_manifest_semantics_verified=True,
        external_row_refit_cartesian_product_verified=True,
        external_group_block_weight_design_from_freeze_only=True,
        qualification_evidence_snapshot_verified=True,
        implementation_source_snapshot_verified=True,
        runtime_environment_snapshot_verified=True,
        training_process_provenance_verified=True,
        historical_no_prior_external_outcome_access_machine_proven=False,
        score_table_derivation_from_generated_models_independently_proven=False,
        certification=result,
    )
