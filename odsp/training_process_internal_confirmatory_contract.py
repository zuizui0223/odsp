"""High-level internal confirmatory contract for training-process inference.

This is the only candidate surface intended for prospective primary internal
validation.  It verifies a pre-outcome freeze envelope and all bound provenance
before calling the qualified numerical training-process core.
"""
from __future__ import annotations

from dataclasses import dataclass
import json
import math
from pathlib import Path
from typing import Mapping, Sequence

import numpy as np

from .confirmatory_environment_lock import (
    ENVIRONMENT_LOCK_ID,
    normalize_runtime_environment_snapshot,
    runtime_environment_snapshot_for_surface,
)
from .confirmatory_implementation_lock import (
    IMPLEMENTATION_LOCK_ID,
    implementation_source_snapshot_for_surface,
)
from .information_transfer_contract import _validate_score_contract
from .refit_information_transfer import RefitInformationLevelScores
from .training_process_freeze_manifest import (
    PROCESS_MANIFEST_TYPE,
    _canonical_sha256,
    _file_sha256,
)
from .training_process_generation_receipt import GENERATION_RECEIPT_TYPE
from .training_process_positive_cv3two_iut import (
    TrainingProcessPositiveCV3TwoInformationCertification,
    certify_training_process_positive_information_cv3two_iut_v5,
)
from .training_process_validation_separation_receipt import (
    SEPARATION_RECEIPT_TYPE,
)
from .upstream_model_artifact_lock import (
    MODEL_ARTIFACT_LOCK_ID,
    verify_upstream_model_artifact_snapshot,
)


CANONICAL_SURFACE = (
    "odsp.training_process_internal_confirmatory_contract."
    "run_training_process_internal_confirmatory_contract_v1"
)
STATISTICAL_CORE = (
    "odsp.training_process_positive_cv3two_iut."
    "certify_training_process_positive_information_cv3two_iut_v5"
)
INTERNAL_FREEZE_MANIFEST_TYPE = (
    "odsp_training_process_internal_confirmatory_freeze_v1"
)
V5_QUALIFICATION_RECEIPT_TYPE = (
    "odsp_training_process_positive_cv3two_iut_v5_qualification_v1"
)
V5_METHOD_VERSION = "training_process_positive_cv3two_iut_v5"


@dataclass(frozen=True)
class TrainingProcessInternalConfirmatoryResult:
    schema_version: int
    receipt_type: str
    analysis_id: str
    training_process_id: str
    validation_dataset_id: str
    qualification_method_version: str
    governance_verified: bool
    process_manifest_content_verified: bool
    generation_receipt_content_verified: bool
    validation_separation_receipt_content_verified: bool
    qualification_receipt_content_verified: bool
    upstream_model_artifact_bytes_verified: bool
    validation_metadata_verified: bool
    information_filtration_settings_verified: bool
    implementation_source_identity_verified: bool
    runtime_environment_identity_verified: bool
    historical_fixed_set_results_reclassified: bool
    certification: TrainingProcessPositiveCV3TwoInformationCertification

    def as_dict(self) -> dict[str, object]:
        return {
            "schema_version": self.schema_version,
            "receipt_type": self.receipt_type,
            "analysis_id": self.analysis_id,
            "training_process_id": self.training_process_id,
            "validation_dataset_id": self.validation_dataset_id,
            "qualification_method_version": self.qualification_method_version,
            "governance_verified": self.governance_verified,
            "process_manifest_content_verified": self.process_manifest_content_verified,
            "generation_receipt_content_verified": self.generation_receipt_content_verified,
            "validation_separation_receipt_content_verified": self.validation_separation_receipt_content_verified,
            "qualification_receipt_content_verified": self.qualification_receipt_content_verified,
            "upstream_model_artifact_bytes_verified": self.upstream_model_artifact_bytes_verified,
            "validation_metadata_verified": self.validation_metadata_verified,
            "information_filtration_settings_verified": self.information_filtration_settings_verified,
            "implementation_source_identity_verified": self.implementation_source_identity_verified,
            "runtime_environment_identity_verified": self.runtime_environment_identity_verified,
            "historical_fixed_set_results_reclassified": self.historical_fixed_set_results_reclassified,
            "certification": self.certification.as_dict(),
        }


def _load_json(path: str | Path, *, name: str) -> dict[str, object]:
    target = Path(path)
    try:
        raw = json.loads(target.read_text(encoding="utf-8"))
    except json.JSONDecodeError as exc:
        raise ValueError(f"{name} is not valid JSON: {target}") from exc
    if not isinstance(raw, Mapping):
        raise ValueError(f"{name} must contain a JSON object")
    return dict(raw)


def _text(value: object, *, name: str) -> str:
    if not isinstance(value, str) or not value.strip():
        raise ValueError(f"{name} must be non-empty text")
    return value.strip()


def _string_ids(
    values: Sequence[object],
    *,
    name: str,
) -> tuple[str, ...]:
    rows = tuple(
        _text(value, name=f"{name}[{index}]")
        for index, value in enumerate(values)
    )
    if not rows:
        raise ValueError(f"{name} must not be empty")
    if len(rows) != len(set(rows)):
        raise ValueError(f"{name} must be unique")
    return rows


def validation_row_id_semantic_sha256(
    row_ids: Sequence[object],
) -> str:
    ids = tuple(sorted(_string_ids(row_ids, name="row_ids")))
    return _canonical_sha256(
        [{"validation_row_id": value} for value in ids]
    )


def validation_metadata_sha256(
    row_ids: Sequence[object],
    groups: Sequence[object],
    blocks: Sequence[object],
    sample_weight: Sequence[float] | None,
) -> str:
    ids = _string_ids(row_ids, name="row_ids")
    n = len(ids)
    if len(groups) != n or len(blocks) != n:
        raise ValueError(
            "row_ids, groups and blocks must contain one aligned value per row"
        )
    group_labels = tuple(
        _text(value, name=f"groups[{index}]")
        for index, value in enumerate(groups)
    )
    block_labels = tuple(
        _text(value, name=f"blocks[{index}]")
        for index, value in enumerate(blocks)
    )
    if sample_weight is None:
        weights = np.ones(n, dtype=float)
    else:
        weights = np.asarray(sample_weight, dtype=float)
        if weights.shape != (n,):
            raise ValueError(
                "sample_weight must contain one aligned value per row"
            )
        if (
            not np.isfinite(weights).all()
            or np.any(weights < 0)
            or not np.any(weights > 0)
        ):
            raise ValueError(
                "sample_weight must be finite, non-negative and positive in total"
            )
    records = [
        {
            "row_id": ids[index],
            "group": group_labels[index],
            "block": block_labels[index],
            "weight": float(weights[index]),
        }
        for index in range(n)
    ]
    records.sort(key=lambda row: row["row_id"])
    return _canonical_sha256(records)


def _levels_structure(
    levels: Sequence[RefitInformationLevelScores],
) -> list[dict[str, object]]:
    return [
        {
            "name": row.name,
            "information": list(row.information),
        }
        for row in levels
    ]


def _require_v5_qualification_receipt(
    receipt: Mapping[str, object],
) -> None:
    if receipt.get("receipt_type") != V5_QUALIFICATION_RECEIPT_TYPE:
        raise ValueError(
            "training-process qualification receipt type is not the frozen v5 type"
        )
    if receipt.get("method_version") != V5_METHOD_VERSION:
        raise ValueError(
            "training-process qualification receipt method_version mismatch"
        )
    null_run = receipt.get("null_run")
    power_run = receipt.get("power_run")
    summary = receipt.get("summary")
    if not isinstance(null_run, Mapping) or not isinstance(power_run, Mapping):
        raise ValueError(
            "training-process qualification receipt must contain null_run and power_run"
        )
    if not isinstance(summary, Mapping):
        raise ValueError(
            "training-process qualification receipt must contain summary"
        )
    if null_run.get("qualification_pass") is not True:
        raise ValueError("v5 null qualification did not pass")
    if power_run.get("qualification_pass") is not True:
        raise ValueError("v5 power qualification did not pass")
    if summary.get("qualification_pass") is not True:
        raise ValueError("v5 combined qualification did not pass")


def _require_generation_receipt(
    receipt: Mapping[str, object],
    *,
    process_manifest_sha256: str,
    training_process_id: str,
    refit_ids: tuple[str, ...],
) -> tuple[dict[str, str], ...]:
    if receipt.get("receipt_type") != GENERATION_RECEIPT_TYPE:
        raise ValueError("training-process generation receipt type mismatch")
    if receipt.get("training_process_id") != training_process_id:
        raise ValueError("generation receipt process identity mismatch")
    if receipt.get("process_manifest_sha256") != process_manifest_sha256:
        raise ValueError("generation receipt process-manifest digest mismatch")
    frozen_ids_raw = receipt.get("refit_ids")
    if not isinstance(frozen_ids_raw, list):
        raise ValueError("generation receipt refit_ids must be an array")
    frozen_ids = tuple(str(value) for value in frozen_ids_raw)
    if tuple(sorted(frozen_ids)) != tuple(sorted(refit_ids)):
        raise ValueError("generation receipt refit coverage mismatch")
    if receipt.get("upstream_model_artifact_lock_id") != MODEL_ARTIFACT_LOCK_ID:
        raise ValueError("generation receipt model-artifact lock mismatch")
    checks = receipt.get("checks")
    if not isinstance(checks, Mapping) or not checks:
        raise ValueError("generation receipt checks are missing")
    if not all(value is True for value in checks.values()):
        raise ValueError("generation receipt contains a failed provenance check")
    snapshot = receipt.get("upstream_model_artifact_snapshot")
    if not isinstance(snapshot, list) or not snapshot:
        raise ValueError("generation receipt model-artifact snapshot is missing")
    return tuple(dict(row) for row in snapshot if isinstance(row, Mapping))


def _require_separation_receipt(
    receipt: Mapping[str, object],
    *,
    process_manifest_sha256: str,
    training_process_id: str,
    validation_row_semantic_sha256: str,
) -> None:
    if receipt.get("receipt_type") != SEPARATION_RECEIPT_TYPE:
        raise ValueError(
            "training-process validation-separation receipt type mismatch"
        )
    if receipt.get("training_process_id") != training_process_id:
        raise ValueError("validation-separation process identity mismatch")
    if receipt.get("process_manifest_sha256") != process_manifest_sha256:
        raise ValueError(
            "validation-separation process-manifest digest mismatch"
        )
    if receipt.get("validation_row_id_semantic_sha256") != (
        validation_row_semantic_sha256
    ):
        raise ValueError(
            "validation-separation receipt row support differs from runtime validation"
        )
    if receipt.get("training_source_frame_validation_disjoint") is not True:
        raise ValueError(
            "full training-process source frame is not validation-disjoint"
        )
    if receipt.get("overlapping_unit_count") != 0:
        raise ValueError(
            "validation-separation receipt contains positive overlap"
        )


def run_training_process_internal_confirmatory_contract_v1(
    levels: Sequence[RefitInformationLevelScores],
    row_ids: Sequence[object],
    groups: Sequence[object],
    blocks: Sequence[object],
    *,
    freeze_manifest_path: str | Path,
    process_manifest_path: str | Path,
    generation_receipt_path: str | Path,
    validation_separation_receipt_path: str | Path,
    qualification_receipt_path: str | Path,
    upstream_model_artifacts: object,
    model_artifact_base_dir: str | Path,
    refit_ids: Sequence[object],
    score_contract: object,
    sample_weight: Sequence[float] | None = None,
) -> TrainingProcessInternalConfirmatoryResult:
    """Verify the frozen envelope and then run the v5 process-mean core."""

    freeze_path = Path(freeze_manifest_path)
    manifest = _load_json(freeze_path, name="internal confirmatory freeze")
    if manifest.get("manifest_type") != INTERNAL_FREEZE_MANIFEST_TYPE:
        raise ValueError("internal confirmatory freeze manifest_type mismatch")
    if manifest.get("schema_version") != 1:
        raise ValueError("internal confirmatory freeze schema_version must be 1")
    if manifest.get("canonical_surface") != CANONICAL_SURFACE:
        raise ValueError("internal confirmatory canonical surface mismatch")
    if manifest.get("statistical_core") != STATISTICAL_CORE:
        raise ValueError("internal confirmatory statistical core mismatch")

    analysis_id = _text(
        manifest.get("analysis_id"),
        name="freeze.analysis_id",
    )
    process = manifest.get("process")
    validation = manifest.get("validation")
    qualification = manifest.get("qualification")
    if not isinstance(process, Mapping):
        raise ValueError("freeze.process must be an object")
    if not isinstance(validation, Mapping):
        raise ValueError("freeze.validation must be an object")
    if not isinstance(qualification, Mapping):
        raise ValueError("freeze.qualification must be an object")

    process_manifest_file = Path(process_manifest_path)
    process_manifest_sha = _file_sha256(process_manifest_file)
    if process_manifest_sha != process.get("process_manifest_sha256"):
        raise ValueError("runtime process manifest bytes differ from freeze")
    process_manifest = _load_json(
        process_manifest_file,
        name="training process manifest",
    )
    if process_manifest.get("manifest_type") != PROCESS_MANIFEST_TYPE:
        raise ValueError("runtime training process manifest_type mismatch")
    process_id = _text(
        process_manifest.get("training_process_id"),
        name="training process manifest.training_process_id",
    )
    if process_id != process.get("training_process_id"):
        raise ValueError("runtime training process identity differs from freeze")

    runtime_refit_ids = _string_ids(refit_ids, name="refit_ids")
    frozen_refit_ids_raw = process.get("refit_ids")
    if not isinstance(frozen_refit_ids_raw, list):
        raise ValueError("freeze.process.refit_ids must be an array")
    frozen_refit_ids = tuple(str(value) for value in frozen_refit_ids_raw)
    if tuple(sorted(runtime_refit_ids)) != tuple(sorted(frozen_refit_ids)):
        raise ValueError("runtime refit IDs differ from frozen process route")

    generation_path = Path(generation_receipt_path)
    if _file_sha256(generation_path) != process.get(
        "generation_receipt_sha256"
    ):
        raise ValueError("generation receipt bytes differ from freeze")
    generation = _load_json(
        generation_path,
        name="training process generation receipt",
    )
    frozen_model_snapshot = _require_generation_receipt(
        generation,
        process_manifest_sha256=process_manifest_sha,
        training_process_id=process_id,
        refit_ids=runtime_refit_ids,
    )
    verify_upstream_model_artifact_snapshot(
        frozen_model_snapshot,
        upstream_model_artifacts,
        base_dir=model_artifact_base_dir,
        refit_ids=runtime_refit_ids,
    )

    runtime_row_semantic_sha = validation_row_id_semantic_sha256(row_ids)
    separation_path = Path(validation_separation_receipt_path)
    if _file_sha256(separation_path) != process.get(
        "validation_separation_receipt_sha256"
    ):
        raise ValueError(
            "validation-separation receipt bytes differ from freeze"
        )
    separation = _load_json(
        separation_path,
        name="training process validation-separation receipt",
    )
    _require_separation_receipt(
        separation,
        process_manifest_sha256=process_manifest_sha,
        training_process_id=process_id,
        validation_row_semantic_sha256=runtime_row_semantic_sha,
    )

    qualification_path = Path(qualification_receipt_path)
    if _file_sha256(qualification_path) != qualification.get(
        "receipt_sha256"
    ):
        raise ValueError("v5 qualification receipt bytes differ from freeze")
    qualification_receipt = _load_json(
        qualification_path,
        name="v5 qualification receipt",
    )
    _require_v5_qualification_receipt(qualification_receipt)

    runtime_metadata_sha = validation_metadata_sha256(
        row_ids,
        groups,
        blocks,
        sample_weight,
    )
    if runtime_metadata_sha != validation.get("metadata_sha256"):
        raise ValueError(
            "runtime validation row/group/block/weight metadata differ from freeze"
        )
    if runtime_row_semantic_sha != validation.get(
        "row_id_semantic_sha256"
    ):
        raise ValueError("runtime validation row support differs from freeze")

    runtime_score = _validate_score_contract(score_contract)
    if runtime_score != manifest.get("score"):
        raise ValueError("runtime score semantics differ from freeze")
    runtime_levels = _levels_structure(levels)
    if runtime_levels != manifest.get("levels"):
        raise ValueError("runtime information filtration differs from freeze")

    certification = manifest.get("certification")
    if not isinstance(certification, Mapping):
        raise ValueError("freeze.certification must be an object")
    component_alpha = float(certification.get("component_one_sided_alpha"))
    minimum_refits = int(certification.get("minimum_refits"))
    minimum_blocks = int(certification.get("minimum_blocks_per_group"))
    gain_tolerance = float(certification.get("gain_tolerance"))
    if component_alpha != 0.05:
        raise ValueError("frozen component alpha is outside v1 envelope scope")
    if minimum_refits != 8 or minimum_blocks != 8:
        raise ValueError("frozen minimum-count settings are outside v1 scope")
    if not math.isfinite(gain_tolerance) or gain_tolerance < 0:
        raise ValueError("frozen gain_tolerance must be finite and non-negative")

    if manifest.get("implementation_lock_id") != IMPLEMENTATION_LOCK_ID:
        raise ValueError("freeze implementation lock ID mismatch")
    current_sources = [
        dict(row)
        for row in implementation_source_snapshot_for_surface(
            CANONICAL_SURFACE
        )
    ]
    if current_sources != manifest.get("implementation_source_snapshot"):
        raise ValueError(
            "runtime confirmatory implementation source differs from freeze"
        )

    if manifest.get("runtime_environment_lock_id") != ENVIRONMENT_LOCK_ID:
        raise ValueError("freeze runtime environment lock ID mismatch")
    frozen_environment = normalize_runtime_environment_snapshot(
        manifest.get("runtime_environment_snapshot")
    )
    current_environment = runtime_environment_snapshot_for_surface(
        CANONICAL_SURFACE
    )
    if current_environment != frozen_environment:
        raise ValueError(
            "runtime confirmatory environment differs from freeze"
        )

    result = certify_training_process_positive_information_cv3two_iut_v5(
        levels,
        groups,
        blocks=blocks,
        refit_ids=runtime_refit_ids,
        training_process_id=process_id,
        training_process_manifest_sha256=process_manifest_sha,
        score_name=str(runtime_score["name"]),
        sample_weight=sample_weight,
        component_one_sided_alpha=component_alpha,
        minimum_refits=minimum_refits,
        minimum_blocks_per_group=minimum_blocks,
        gain_tolerance=gain_tolerance,
    )
    return TrainingProcessInternalConfirmatoryResult(
        schema_version=1,
        receipt_type="odsp_training_process_internal_confirmatory_result_v1",
        analysis_id=analysis_id,
        training_process_id=process_id,
        validation_dataset_id=_text(
            validation.get("dataset_id"),
            name="freeze.validation.dataset_id",
        ),
        qualification_method_version=V5_METHOD_VERSION,
        governance_verified=True,
        process_manifest_content_verified=True,
        generation_receipt_content_verified=True,
        validation_separation_receipt_content_verified=True,
        qualification_receipt_content_verified=True,
        upstream_model_artifact_bytes_verified=True,
        validation_metadata_verified=True,
        information_filtration_settings_verified=True,
        implementation_source_identity_verified=True,
        runtime_environment_identity_verified=True,
        historical_fixed_set_results_reclassified=False,
        certification=result,
    )
