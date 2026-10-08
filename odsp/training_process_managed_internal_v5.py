"""Managed-internal confirmatory endpoint for qualified training-process v5.

This endpoint closes the model-to-held-out-score provenance gap while delegating
all statistical inference to the already-qualified internal v5 wrapper.
"""
from __future__ import annotations

from dataclasses import asdict, dataclass
from datetime import datetime, timedelta
from pathlib import Path
from typing import Mapping, Sequence

import numpy as np

from .confirmatory_environment_lock import (
    ENVIRONMENT_LOCK_ID,
    runtime_environment_snapshot_for_surface,
)
from .confirmatory_implementation_lock import (
    IMPLEMENTATION_LOCK_ID,
    implementation_source_snapshot_for_surface,
)
from .refit_information_transfer import RefitInformationLevelScores
from .training_process_confirmatory_v5 import (
    TrainingProcessConfirmatoryV5Certification,
    _load_json,
    _manifest_schedule,
    _verify_managed_receipt,
    certify_predeclared_training_process_positive_information_v5,
)
from .training_process_internal_qualification_v5 import (
    build_internal_v5_qualification_snapshot,
)
from .training_process_validation_helpers import (
    _canonical_sha256,
    _model_artifact_snapshot,
    _validation_design_rows,
)
from .training_process_freeze_manifest import _file_sha256
from .training_process_internal_freeze_v1 import (
    FREEZE_RECEIPT_TYPE,
    MANAGED_INTERNAL_SURFACE,
    MANIFEST_TYPE,
)
from .training_process_managed_internal_scoring import (
    MANAGED_INTERNAL_SCORING_RECEIPT_TYPE,
    load_managed_internal_score_bundle,
)


MANAGED_INTERNAL_RECEIPT_TYPE = (
    "odsp_training_process_v5_managed_internal_endpoint_v1"
)


@dataclass(frozen=True)
class ManagedInternalTrainingProcessV5Certification:
    schema_version: int
    receipt_type: str
    validation_dataset_id: str
    internal_validation_freeze_manifest_sha256: str
    internal_validation_freeze_receipt_sha256: str
    validation_design_sha256: str
    validation_row_count: int
    validation_outcomes_first_accessed_at_utc: str
    freeze_precedes_declared_first_validation_outcome_access: bool
    managed_validation_data_first_read_by_odsp_at_utc: str
    managed_validation_read_after_freeze: bool
    declared_first_access_not_after_managed_validation_read: bool
    training_process_id: str
    training_process_manifest_sha256: str
    managed_generation_receipt_sha256: str
    managed_scoring_receipt_sha256: str
    score_bundle_sha256: str
    canonical_score_tensor_sha256: str
    freeze_manifest_semantics_verified: bool
    validation_design_exact_match_verified: bool
    process_identity_exact_match_verified: bool
    generated_model_artifact_snapshot_verified: bool
    fit_environment_snapshot_verified: bool
    score_tensor_derived_by_managed_scoring: bool
    semantic_use_of_model_and_validation_inputs_cryptographically_proven: bool
    implementation_source_snapshot_verified: bool
    runtime_environment_snapshot_verified: bool
    training_source_frame_validation_disjoint: bool
    historical_no_prior_validation_outcome_access_machine_proven: bool
    fixed_set_results_reclassified: bool
    certification: TrainingProcessConfirmatoryV5Certification

    def as_dict(self) -> dict[str, object]:
        payload = asdict(self)
        payload["certification"] = self.certification.as_dict()
        return payload


def _text(value: object, *, name: str) -> str:
    if not isinstance(value, str) or not value.strip():
        raise ValueError(f"{name} must be non-empty text")
    return value.strip()


def _utc_timestamp(value: object, *, name: str) -> tuple[str, datetime]:
    text = _text(value, name=name)
    parse_text = text[:-1] + "+00:00" if text.endswith("Z") else text
    try:
        stamp = datetime.fromisoformat(parse_text)
    except ValueError as exc:
        raise ValueError(f"{name} must be an ISO-8601 UTC timestamp") from exc
    if stamp.tzinfo is None or stamp.utcoffset() != timedelta(0):
        raise ValueError(f"{name} must include an explicit UTC offset")
    return stamp.isoformat().replace("+00:00", "Z"), stamp


def _verify_freeze_receipt(
    receipt: Mapping[str, object],
    *,
    receipt_path: Path,
    manifest_path: Path,
    manifest: Mapping[str, object],
) -> None:
    if receipt.get("receipt_type") != FREEZE_RECEIPT_TYPE:
        raise ValueError("internal validation freeze receipt_type is not recognized")
    if receipt.get("schema_version") != 1:
        raise ValueError("internal validation freeze receipt schema_version must be 1")
    if receipt.get("manifest_sha256") != _file_sha256(manifest_path):
        raise ValueError("internal validation freeze receipt manifest SHA256 mismatch")
    if receipt.get("frozen_at_utc") != manifest.get("frozen_at_utc"):
        raise ValueError("internal validation freeze receipt timestamp mismatch")
    if receipt.get("validation_design_sha256") != manifest.get(
        "validation_design_sha256"
    ):
        raise ValueError("internal validation freeze receipt design digest mismatch")
    if receipt.get("training_process_manifest_sha256") != manifest.get(
        "training_process_manifest_sha256"
    ):
        raise ValueError("internal validation freeze process-manifest mismatch")
    if receipt.get("managed_generation_receipt_sha256") != manifest.get(
        "managed_generation_receipt_sha256"
    ):
        raise ValueError("internal validation freeze generation-receipt mismatch")
    _ = _file_sha256(receipt_path)


def _runtime_design(
    validation_row_ids: Sequence[object],
    groups: Sequence[object],
    blocks: Sequence[object],
    sample_weight: Sequence[float],
) -> tuple[list[dict[str, object]], dict[str, int]]:
    n = len(validation_row_ids)
    if len(groups) != n or len(blocks) != n or len(sample_weight) != n:
        raise ValueError(
            "validation_row_ids, groups, blocks and sample_weight must have equal length"
        )
    return _validation_design_rows(
        [
            {
                "row_id": validation_row_ids[i],
                "group_id": groups[i],
                "block_id": blocks[i],
                "sample_weight": sample_weight[i],
            }
            for i in range(n)
        ]
    )


def _level_metadata(
    levels: Sequence[RefitInformationLevelScores],
) -> list[dict[str, object]]:
    rows: list[dict[str, object]] = []
    for index, level in enumerate(levels):
        name = _text(getattr(level, "name", None), name=f"levels[{index}].name")
        info = getattr(level, "information", None)
        if not isinstance(info, (tuple, list)):
            raise ValueError(f"levels[{index}].information must be a sequence")
        rows.append(
            {
                "name": name,
                "information": [
                    _text(value, name=f"levels[{index}].information")
                    for value in info
                ],
            }
        )
    return rows


def run_managed_internal_training_process_v5(
    internal_validation_freeze_manifest_path: str | Path,
    internal_validation_freeze_receipt_path: str | Path,
    managed_scoring_receipt_path: str | Path,
    score_bundle_path: str | Path,
    validation_data_path: str | Path,
    groups: Sequence[object],
    *,
    blocks: Sequence[object],
    validation_row_ids: Sequence[object],
    sample_weight: Sequence[float],
    refit_ids: Sequence[object],
    training_process_manifest_path: str | Path,
    managed_generation_receipt_path: str | Path,
    training_roster_path: str | Path,
    validation_outcomes_first_accessed_at_utc: object,
) -> ManagedInternalTrainingProcessV5Certification:
    """Verify managed held-out score provenance, then call qualified internal v5."""

    freeze_manifest_path = Path(internal_validation_freeze_manifest_path)
    freeze_receipt_path = Path(internal_validation_freeze_receipt_path)
    scoring_receipt_path = Path(managed_scoring_receipt_path)
    bundle_path = Path(score_bundle_path)
    validation_path = Path(validation_data_path)
    process_manifest_path = Path(training_process_manifest_path)
    managed_receipt_path = Path(managed_generation_receipt_path)
    roster_path = Path(training_roster_path)
    for path in (
        freeze_manifest_path,
        freeze_receipt_path,
        scoring_receipt_path,
        bundle_path,
        validation_path,
        process_manifest_path,
        managed_receipt_path,
        roster_path,
    ):
        if not path.is_file():
            raise FileNotFoundError(path)

    manifest = _load_json(
        freeze_manifest_path, name="internal validation freeze manifest"
    )
    if manifest.get("manifest_type") != MANIFEST_TYPE:
        raise ValueError("internal validation freeze manifest_type is not recognized")
    if manifest.get("schema_version") != 1:
        raise ValueError("internal validation freeze schema_version must be 1")
    freeze_receipt = _load_json(
        freeze_receipt_path, name="internal validation freeze receipt"
    )
    _verify_freeze_receipt(
        freeze_receipt,
        receipt_path=freeze_receipt_path,
        manifest_path=freeze_manifest_path,
        manifest=manifest,
    )

    freeze_text, freeze_time = _utc_timestamp(
        manifest.get("frozen_at_utc"),
        name="internal validation freeze.frozen_at_utc",
    )
    access_text, first_access = _utc_timestamp(
        validation_outcomes_first_accessed_at_utc,
        name="validation_outcomes_first_accessed_at_utc",
    )
    if not freeze_time < first_access:
        raise ValueError(
            "internal validation freeze must strictly predate declared first "
            "validation-outcome access"
        )

    design_rows, block_counts = _runtime_design(
        validation_row_ids,
        groups,
        blocks,
        sample_weight,
    )
    design_sha = _canonical_sha256(design_rows)
    if design_sha != manifest.get("validation_design_sha256"):
        raise ValueError("runtime validation design does not match freeze")
    if len(design_rows) != manifest.get("validation_row_count"):
        raise ValueError("runtime validation row count does not match freeze")
    if block_counts != manifest.get("positive_block_count_by_group"):
        raise ValueError("runtime validation block counts do not match freeze")

    process_manifest_sha = _file_sha256(process_manifest_path)
    if process_manifest_sha != manifest.get("training_process_manifest_sha256"):
        raise ValueError("training process manifest does not match internal freeze")
    process_manifest = _load_json(
        process_manifest_path, name="training process manifest"
    )
    process_id, frozen_refits, schedule = _manifest_schedule(process_manifest)
    if process_id != manifest.get("training_process_id"):
        raise ValueError("training process ID does not match internal freeze")
    supplied_refits = tuple(
        sorted(_text(x, name="refit_id") for x in refit_ids)
    )
    if supplied_refits != frozen_refits or supplied_refits != tuple(
        manifest.get("refit_ids", ())
    ):
        raise ValueError("runtime refit IDs do not match internal validation freeze")

    managed_receipt_sha = _file_sha256(managed_receipt_path)
    if managed_receipt_sha != manifest.get("managed_generation_receipt_sha256"):
        raise ValueError("managed generation receipt does not match internal freeze")
    managed_receipt = _load_json(
        managed_receipt_path, name="managed generation receipt"
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
    if _model_artifact_snapshot(managed_receipt) != manifest.get(
        "generated_model_artifact_snapshot"
    ):
        raise ValueError("generated model artifact snapshot does not match freeze")
    if managed_receipt.get("fit_environment_snapshot") != manifest.get(
        "fit_environment_snapshot"
    ):
        raise ValueError("fit environment snapshot does not match internal freeze")

    if manifest.get("internal_qualified_route") != build_internal_v5_qualification_snapshot():
        raise ValueError("frozen internal v5 qualification route no longer matches")

    endpoint = manifest.get("managed_internal_endpoint")
    if not isinstance(endpoint, Mapping):
        raise ValueError("managed_internal_endpoint is invalid")
    if endpoint.get("canonical_surface") != MANAGED_INTERNAL_SURFACE:
        raise ValueError("managed internal endpoint surface mismatch")
    if endpoint.get("implementation_lock_id") != IMPLEMENTATION_LOCK_ID:
        raise ValueError("managed internal implementation lock mismatch")
    current_source = [
        dict(row)
        for row in implementation_source_snapshot_for_surface(
            MANAGED_INTERNAL_SURFACE
        )
    ]
    if endpoint.get("implementation_source_snapshot") != current_source:
        raise ValueError("managed internal source snapshot mismatch")
    if endpoint.get("environment_lock_id") != ENVIRONMENT_LOCK_ID:
        raise ValueError("managed internal environment lock mismatch")
    current_env = runtime_environment_snapshot_for_surface(
        MANAGED_INTERNAL_SURFACE
    )
    if endpoint.get("runtime_environment_snapshot") != current_env:
        raise ValueError("managed internal runtime environment mismatch")

    scoring_receipt = _load_json(
        scoring_receipt_path, name="managed internal scoring receipt"
    )
    if scoring_receipt.get(
        "receipt_type"
    ) != MANAGED_INTERNAL_SCORING_RECEIPT_TYPE:
        raise ValueError("managed internal scoring receipt_type is not recognized")
    managed_read_text, managed_read_time = _utc_timestamp(
        scoring_receipt.get("validation_data_first_read_by_odsp_at_utc"),
        name="managed internal scoring receipt.validation_data_first_read_by_odsp_at_utc",
    )
    if not freeze_time < managed_read_time:
        raise ValueError(
            "ODSP-managed validation-data read must occur after internal validation freeze"
        )
    if first_access > managed_read_time:
        raise ValueError(
            "declared first validation-outcome access must not occur after "
            "ODSP-managed validation-data read"
        )
    freeze_manifest_sha = _file_sha256(freeze_manifest_path)
    validation_sha = _file_sha256(validation_path)
    bundle_sha = _file_sha256(bundle_path)
    checks = {
        "internal_validation_freeze_manifest_sha256": freeze_manifest_sha,
        "internal_validation_freeze_receipt_sha256": _file_sha256(
            freeze_receipt_path
        ),
        "managed_generation_receipt_sha256": managed_receipt_sha,
        "validation_data_sha256": validation_sha,
        "score_bundle_sha256": bundle_sha,
    }
    for field, expected in checks.items():
        if scoring_receipt.get(field) != expected:
            raise ValueError(f"managed internal scoring receipt {field} mismatch")
    scoring_plan = manifest.get("managed_scoring_plan")
    if not isinstance(scoring_plan, Mapping):
        raise ValueError("managed_scoring_plan is invalid")
    if scoring_receipt.get(
        "scoring_command_artifact_snapshot"
    ) != scoring_plan.get("command_artifact_snapshot"):
        raise ValueError("managed internal scoring-code snapshot mismatch")
    if scoring_receipt.get(
        "scoring_runtime_environment_snapshot"
    ) != scoring_plan.get("runtime_environment_snapshot"):
        raise ValueError("managed internal scoring runtime mismatch")
    if scoring_receipt.get(
        "generated_model_artifact_snapshot"
    ) != manifest.get("generated_model_artifact_snapshot"):
        raise ValueError("managed internal scoring model snapshot mismatch")
    boundaries = scoring_receipt.get("boundaries")
    if not isinstance(boundaries, Mapping):
        raise ValueError("managed internal scoring boundaries are invalid")
    if boundaries.get("score_tensor_derived_by_managed_scoring") is not True:
        raise ValueError("internal score tensor was not managed-derived")
    if boundaries.get(
        "generated_model_artifacts_reverified_before_scoring"
    ) is not True:
        raise ValueError("internal scoring did not reverify generated models")
    if boundaries.get("shell_used") is not False:
        raise ValueError("managed internal scoring must report shell_used=false")
    if scoring_receipt.get("refit_count") != len(supplied_refits):
        raise ValueError("managed internal scoring refit_count mismatch")
    if scoring_receipt.get("row_count") != len(design_rows):
        raise ValueError("managed internal scoring row_count mismatch")
    frozen_level_names = [
        str(row["name"]) for row in manifest.get("levels", ())
        if isinstance(row, Mapping)
    ]
    if scoring_receipt.get("level_names") != frozen_level_names:
        raise ValueError("managed internal scoring level names mismatch")
    executions = scoring_receipt.get("executions")
    if not isinstance(executions, list) or len(executions) != len(supplied_refits):
        raise ValueError("managed internal scoring execution coverage mismatch")
    execution_ids: list[str] = []
    for execution in executions:
        if not isinstance(execution, Mapping):
            raise ValueError("managed internal scoring execution must be an object")
        execution_ids.append(
            _text(execution.get("refit_id"), name="managed scoring execution refit_id")
        )
        if execution.get("return_code") != 0:
            raise ValueError("managed internal scoring execution has nonzero return code")
        digest = execution.get("score_output_sha256")
        if not isinstance(digest, str) or len(digest) != 64:
            raise ValueError("managed internal scoring output SHA256 is invalid")
    if tuple(execution_ids) != supplied_refits:
        raise ValueError("managed internal scoring execution refit order mismatch")

    levels, bundle_row_ids, bundle_refit_ids, tensor_sha = (
        load_managed_internal_score_bundle(
            bundle_path,
            expected_bundle_sha256=bundle_sha,
            expected_internal_validation_freeze_manifest_sha256=freeze_manifest_sha,
            expected_managed_generation_receipt_sha256=managed_receipt_sha,
            expected_validation_data_sha256=validation_sha,
        )
    )
    if tensor_sha != scoring_receipt.get("canonical_score_tensor_sha256"):
        raise ValueError("managed internal tensor digest mismatch")
    if _level_metadata(levels) != manifest.get("levels"):
        raise ValueError("managed internal score levels do not match freeze")
    if tuple(bundle_refit_ids) != supplied_refits:
        raise ValueError("managed internal score refit IDs do not match process")

    runtime_row_ids = tuple(
        _text(value, name="validation_row_id") for value in validation_row_ids
    )
    if len(runtime_row_ids) != len(set(runtime_row_ids)):
        raise ValueError("runtime validation row IDs must be unique")
    if set(bundle_row_ids) != set(runtime_row_ids):
        raise ValueError("managed internal score rows do not match validation rows")
    index = {row_id: i for i, row_id in enumerate(bundle_row_ids)}
    reorder = [index[row_id] for row_id in runtime_row_ids]
    aligned_levels = tuple(
        RefitInformationLevelScores(
            level.name,
            level.information,
            np.asarray(level.score, dtype=float)[:, reorder],
        )
        for level in levels
    )

    score = manifest.get("score")
    certification = manifest.get("certification")
    roster_spec = manifest.get("training_roster_spec")
    if not isinstance(score, Mapping):
        raise ValueError("frozen score metadata is invalid")
    if not isinstance(certification, Mapping):
        raise ValueError("frozen certification settings are invalid")
    if not isinstance(roster_spec, Mapping):
        raise ValueError("training_roster_spec is invalid")

    result = certify_predeclared_training_process_positive_information_v5(
        aligned_levels,
        groups,
        blocks=blocks,
        validation_row_ids=validation_row_ids,
        refit_ids=refit_ids,
        training_process_manifest_path=process_manifest_path,
        managed_generation_receipt_path=managed_receipt_path,
        managed_generation_receipt_sha256=managed_receipt_sha,
        training_roster_path=roster_path,
        row_identity_namespace=manifest["row_identity_namespace"],
        roster_format=str(roster_spec["format"]),
        unit_id_column=str(roster_spec["unit_id_column"]),
        stratum_column=roster_spec["stratum_column"],
        score_name=str(score["name"]),
        sample_weight=sample_weight,
        component_one_sided_alpha=float(
            certification["component_one_sided_alpha"]
        ),
        minimum_refits=int(certification["minimum_refits"]),
        minimum_blocks_per_group=int(
            certification["minimum_blocks_per_group"]
        ),
        gain_tolerance=float(certification["gain_tolerance"]),
    )
    if not result.training_source_frame_validation_disjoint:
        raise AssertionError("qualified wrapper returned non-disjoint source frame")

    return ManagedInternalTrainingProcessV5Certification(
        schema_version=1,
        receipt_type=MANAGED_INTERNAL_RECEIPT_TYPE,
        validation_dataset_id=str(manifest["validation_dataset_id"]),
        internal_validation_freeze_manifest_sha256=freeze_manifest_sha,
        internal_validation_freeze_receipt_sha256=_file_sha256(
            freeze_receipt_path
        ),
        validation_design_sha256=design_sha,
        validation_row_count=len(design_rows),
        validation_outcomes_first_accessed_at_utc=access_text,
        freeze_precedes_declared_first_validation_outcome_access=True,
        managed_validation_data_first_read_by_odsp_at_utc=managed_read_text,
        managed_validation_read_after_freeze=True,
        declared_first_access_not_after_managed_validation_read=True,
        training_process_id=process_id,
        training_process_manifest_sha256=process_manifest_sha,
        managed_generation_receipt_sha256=managed_receipt_sha,
        managed_scoring_receipt_sha256=_file_sha256(scoring_receipt_path),
        score_bundle_sha256=bundle_sha,
        canonical_score_tensor_sha256=tensor_sha,
        freeze_manifest_semantics_verified=True,
        validation_design_exact_match_verified=True,
        process_identity_exact_match_verified=True,
        generated_model_artifact_snapshot_verified=True,
        fit_environment_snapshot_verified=True,
        score_tensor_derived_by_managed_scoring=True,
        semantic_use_of_model_and_validation_inputs_cryptographically_proven=False,
        implementation_source_snapshot_verified=True,
        runtime_environment_snapshot_verified=True,
        training_source_frame_validation_disjoint=True,
        historical_no_prior_validation_outcome_access_machine_proven=False,
        fixed_set_results_reclassified=False,
        certification=result,
    )
