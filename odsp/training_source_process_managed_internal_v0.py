"""Managed held-out validation endpoint for training-source process v0."""
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
from .training_process_freeze_manifest import _file_sha256
from .training_source_process_freeze_manifest import SOURCE_PROCESS_MANIFEST_TYPE
from .training_source_process_internal_freeze_v0 import (
    FREEZE_RECEIPT_TYPE,
    MANAGED_SURFACE,
    MANIFEST_TYPE,
    _load_json,
)
from .training_source_process_managed_scoring import (
    SCORING_RECEIPT_TYPE as MANAGED_SCORING_RECEIPT_TYPE,
    load_managed_training_source_score_bundle,
)
from .training_source_process_validation_helpers import (
    _canonical_sha256,
    _nested_model_artifact_snapshot,
    _text,
    _validation_design_rows,
    _verify_managed_nested_receipt,
)
from .training_source_process_validation_provenance import (
    audit_training_source_process_validation_frame_separation,
)
from .training_source_process_v0 import (
    TrainingSourceProcessV0InformationEvaluation,
    evaluate_training_source_process_positive_information_v0,
)


MANAGED_INTERNAL_RECEIPT_TYPE = (
    "odsp_training_source_process_v0_managed_internal_certification"
)


@dataclass(frozen=True)
class ManagedInternalTrainingSourceProcessV0Certification:
    schema_version: int
    receipt_type: str
    validation_dataset_id: str
    validation_freeze_manifest_sha256: str
    validation_freeze_receipt_sha256: str
    validation_design_sha256: str
    validation_row_count: int
    validation_outcomes_first_accessed_at_utc: str
    freeze_precedes_declared_first_validation_outcome_access: bool
    managed_validation_data_first_read_by_odsp_at_utc: str
    managed_validation_read_after_freeze: bool
    declared_first_access_not_after_managed_validation_read: bool
    source_process_id: str
    source_process_manifest_sha256: str
    managed_nested_generation_receipt_sha256: str
    managed_scoring_receipt_sha256: str
    score_bundle_sha256: str
    canonical_score_tensor_sha256: str
    source_frame_validation_disjoint: bool
    nested_model_artifact_snapshot_verified: bool
    fit_environment_snapshot_verified: bool
    score_tensor_derived_by_managed_scoring: bool
    semantic_use_of_model_and_validation_inputs_cryptographically_proven: bool
    implementation_source_snapshot_verified: bool
    runtime_environment_snapshot_verified: bool
    historical_no_prior_validation_outcome_access_machine_proven: bool
    unknown_ecological_superpopulation_generalization_claimed: bool
    qualified_training_process_v5_reclassified: bool
    evaluation: TrainingSourceProcessV0InformationEvaluation

    def as_dict(self) -> dict[str, object]:
        payload = asdict(self)
        payload["evaluation"] = self.evaluation.as_dict()
        return payload


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


def _manifest_fields(manifest: Mapping[str, object]) -> None:
    required = {
        "schema_version",
        "manifest_type",
        "frozen_at_utc",
        "validation_dataset_id",
        "row_identity_namespace",
        "validation_design_sha256",
        "validation_row_count",
        "validation_group_count",
        "positive_block_count_by_group",
        "source_process_id",
        "source_process_manifest_sha256",
        "source_roster_spec",
        "managed_nested_generation_receipt_sha256",
        "source_draw_ids",
        "inner_refit_ids",
        "nested_model_artifact_snapshot",
        "fit_environment_snapshot",
        "source_frame_validation_disjoint",
        "source_frame_audit",
        "managed_internal_endpoint",
        "managed_scoring_plan",
        "score",
        "levels",
        "certification",
        "boundaries",
    }
    if set(manifest) != required:
        raise ValueError(
            "source-v0 validation freeze manifest fields mismatch: "
            f"missing={sorted(required-set(manifest))!r}, "
            f"unknown={sorted(set(manifest)-required)!r}"
        )
    if manifest.get("schema_version") != 1:
        raise ValueError("source-v0 validation freeze schema_version must be 1")
    if manifest.get("manifest_type") != MANIFEST_TYPE:
        raise ValueError("source-v0 validation freeze manifest_type is not recognized")


def _verify_freeze_receipt(
    receipt: Mapping[str, object],
    *,
    receipt_path: Path,
    manifest_path: Path,
    manifest: Mapping[str, object],
) -> None:
    if receipt.get("receipt_type") != FREEZE_RECEIPT_TYPE:
        raise ValueError("source-v0 validation freeze receipt_type is not recognized")
    if receipt.get("manifest_sha256") != _file_sha256(manifest_path):
        raise ValueError("source-v0 validation freeze receipt manifest mismatch")
    checks = {
        "validation_design_sha256": manifest.get("validation_design_sha256"),
        "source_process_manifest_sha256": manifest.get(
            "source_process_manifest_sha256"
        ),
        "managed_nested_generation_receipt_sha256": manifest.get(
            "managed_nested_generation_receipt_sha256"
        ),
        "source_process_id": manifest.get("source_process_id"),
        "validation_row_count": manifest.get("validation_row_count"),
    }
    for field, expected in checks.items():
        if receipt.get(field) != expected:
            raise ValueError(f"source-v0 validation freeze receipt {field} mismatch")
    _ = _file_sha256(receipt_path)


def _runtime_design(
    row_ids: Sequence[object],
    groups: Sequence[object],
    blocks: Sequence[object],
    sample_weight: Sequence[float],
) -> tuple[list[dict[str, object]], dict[str, int]]:
    n = len(row_ids)
    if len(groups) != n or len(blocks) != n or len(sample_weight) != n:
        raise ValueError(
            "validation_row_ids, groups, blocks and sample_weight must align"
        )
    return _validation_design_rows(
        [
            {
                "row_id": row_ids[i],
                "group_id": groups[i],
                "block_id": blocks[i],
                "sample_weight": sample_weight[i],
            }
            for i in range(n)
        ]
    )


def run_managed_internal_training_source_process_v0(
    validation_freeze_manifest_path: str | Path,
    validation_freeze_receipt_path: str | Path,
    managed_scoring_receipt_path: str | Path,
    score_bundle_path: str | Path,
    validation_data_path: str | Path,
    groups: Sequence[object],
    *,
    blocks: Sequence[object],
    validation_row_ids: Sequence[object],
    sample_weight: Sequence[float],
    source_process_manifest_path: str | Path,
    managed_nested_generation_receipt_path: str | Path,
    source_roster_path: str | Path,
    validation_outcomes_first_accessed_at_utc: object,
) -> ManagedInternalTrainingSourceProcessV0Certification:
    manifest_path = Path(validation_freeze_manifest_path)
    freeze_receipt_path = Path(validation_freeze_receipt_path)
    scoring_receipt_path = Path(managed_scoring_receipt_path)
    bundle_path = Path(score_bundle_path)
    validation_path = Path(validation_data_path)
    source_manifest_path = Path(source_process_manifest_path)
    managed_receipt_path = Path(managed_nested_generation_receipt_path)
    roster_path = Path(source_roster_path)
    for path in (
        manifest_path,
        freeze_receipt_path,
        scoring_receipt_path,
        bundle_path,
        validation_path,
        source_manifest_path,
        managed_receipt_path,
        roster_path,
    ):
        if not path.is_file():
            raise FileNotFoundError(path)

    manifest = _load_json(manifest_path, name="source-v0 validation freeze manifest")
    _manifest_fields(manifest)
    freeze_receipt = _load_json(
        freeze_receipt_path, name="source-v0 validation freeze receipt"
    )
    _verify_freeze_receipt(
        freeze_receipt,
        receipt_path=freeze_receipt_path,
        manifest_path=manifest_path,
        manifest=manifest,
    )

    freeze_text, freeze_time = _utc_timestamp(
        manifest.get("frozen_at_utc"),
        name="source-v0 validation freeze.frozen_at_utc",
    )
    access_text, access_time = _utc_timestamp(
        validation_outcomes_first_accessed_at_utc,
        name="validation_outcomes_first_accessed_at_utc",
    )
    if not freeze_time < access_time:
        raise ValueError(
            "source-v0 validation freeze must strictly predate declared "
            "first validation-outcome access"
        )

    design_rows, block_counts = _runtime_design(
        validation_row_ids, groups, blocks, sample_weight
    )
    design_sha = _canonical_sha256(design_rows)
    if design_sha != manifest["validation_design_sha256"]:
        raise ValueError("runtime validation design does not match source-v0 freeze")
    if len(design_rows) != manifest["validation_row_count"]:
        raise ValueError("runtime validation row count does not match source-v0 freeze")
    if block_counts != manifest["positive_block_count_by_group"]:
        raise ValueError("runtime validation block counts do not match source-v0 freeze")

    source_manifest_sha = _file_sha256(source_manifest_path)
    if source_manifest_sha != manifest["source_process_manifest_sha256"]:
        raise ValueError("source process manifest does not match validation freeze")
    source_manifest = _load_json(
        source_manifest_path, name="training source process manifest"
    )
    if source_manifest.get("manifest_type") != SOURCE_PROCESS_MANIFEST_TYPE:
        raise ValueError("source process manifest_type is not recognized")
    source_process_id = _text(
        source_manifest.get("source_process_id"), name="source_process_id"
    )
    if source_process_id != manifest["source_process_id"]:
        raise ValueError("source process ID does not match validation freeze")
    source_ids = tuple(str(x) for x in source_manifest.get("source_draw_ids", ()))
    inner_ids = tuple(str(x) for x in source_manifest.get("inner_refit_ids", ()))
    if source_ids != tuple(manifest["source_draw_ids"]):
        raise ValueError("source draw IDs do not match validation freeze")
    if inner_ids != tuple(manifest["inner_refit_ids"]):
        raise ValueError("inner refit IDs do not match validation freeze")

    managed_receipt_sha = _file_sha256(managed_receipt_path)
    if managed_receipt_sha != manifest[
        "managed_nested_generation_receipt_sha256"
    ]:
        raise ValueError("managed nested generation receipt does not match freeze")
    managed_receipt = _load_json(
        managed_receipt_path, name="managed nested generation receipt"
    )
    _verify_managed_nested_receipt(
        managed_receipt,
        receipt_sha256=managed_receipt_sha,
        source_process_id=source_process_id,
        manifest_sha256=source_manifest_sha,
        manifest=source_manifest,
    )
    if _nested_model_artifact_snapshot(managed_receipt) != manifest[
        "nested_model_artifact_snapshot"
    ]:
        raise ValueError("nested model artifact snapshot does not match freeze")
    if managed_receipt.get("fit_environment_snapshot") != manifest.get(
        "fit_environment_snapshot"
    ):
        raise ValueError("fit environment snapshot does not match freeze")

    roster_spec = manifest.get("source_roster_spec")
    if not isinstance(roster_spec, Mapping):
        raise ValueError("source_roster_spec is invalid")
    frame_audit = audit_training_source_process_validation_frame_separation(
        source_manifest_path,
        roster_path,
        validation_row_ids,
        row_identity_namespace=manifest["row_identity_namespace"],
        roster_format=str(roster_spec["format"]),
        unit_id_column=str(roster_spec["unit_id_column"]),
        stratum_column=roster_spec["stratum_column"],
    )
    if not frame_audit.source_frame_validation_disjoint:
        raise ValueError("source frame overlaps validation rows")
    if frame_audit.as_dict() != manifest["source_frame_audit"]:
        raise ValueError("runtime source-frame audit no longer matches freeze")

    endpoint = manifest.get("managed_internal_endpoint")
    if not isinstance(endpoint, Mapping):
        raise ValueError("managed_internal_endpoint is invalid")
    if endpoint.get("canonical_surface") != MANAGED_SURFACE:
        raise ValueError("source-v0 managed endpoint surface mismatch")
    if endpoint.get("implementation_lock_id") != IMPLEMENTATION_LOCK_ID:
        raise ValueError("source-v0 implementation lock mismatch")
    current_source = [
        dict(row) for row in implementation_source_snapshot_for_surface(MANAGED_SURFACE)
    ]
    if endpoint.get("implementation_source_snapshot") != current_source:
        raise ValueError("source-v0 implementation source snapshot mismatch")
    if endpoint.get("environment_lock_id") != ENVIRONMENT_LOCK_ID:
        raise ValueError("source-v0 environment lock mismatch")
    current_env = runtime_environment_snapshot_for_surface(MANAGED_SURFACE)
    if endpoint.get("runtime_environment_snapshot") != current_env:
        raise ValueError("source-v0 runtime environment mismatch")

    scoring_receipt = _load_json(
        scoring_receipt_path, name="source-v0 managed scoring receipt"
    )
    if scoring_receipt.get("receipt_type") != MANAGED_SCORING_RECEIPT_TYPE:
        raise ValueError("source-v0 managed scoring receipt_type is not recognized")
    managed_read_text, managed_read_time = _utc_timestamp(
        scoring_receipt.get("validation_data_first_read_by_odsp_at_utc"),
        name=(
            "source-v0 managed scoring receipt."
            "validation_data_first_read_by_odsp_at_utc"
        ),
    )
    if not freeze_time < managed_read_time:
        raise ValueError(
            "ODSP-managed validation-data read must occur after source-v0 validation freeze"
        )
    if access_time > managed_read_time:
        raise ValueError(
            "declared first validation-outcome access must not occur after "
            "ODSP-managed validation-data read"
        )

    validation_sha = _file_sha256(validation_path)
    bundle_sha = _file_sha256(bundle_path)
    checks = {
        "validation_freeze_manifest_sha256": _file_sha256(manifest_path),
        "validation_freeze_receipt_sha256": _file_sha256(freeze_receipt_path),
        "managed_nested_generation_receipt_sha256": managed_receipt_sha,
        "validation_data_sha256": validation_sha,
        "score_bundle_sha256": bundle_sha,
    }
    for field, expected in checks.items():
        if scoring_receipt.get(field) != expected:
            raise ValueError(f"source-v0 managed scoring receipt {field} mismatch")
    scoring_plan = manifest.get("managed_scoring_plan")
    if not isinstance(scoring_plan, Mapping):
        raise ValueError("source-v0 managed scoring plan is invalid")
    if scoring_receipt.get(
        "scoring_command_artifact_snapshot"
    ) != scoring_plan.get("command_artifact_snapshot"):
        raise ValueError("source-v0 scoring-code snapshot mismatch")
    if scoring_receipt.get(
        "scoring_runtime_environment_snapshot"
    ) != scoring_plan.get("runtime_environment_snapshot"):
        raise ValueError("source-v0 scoring runtime snapshot mismatch")
    if scoring_receipt.get(
        "nested_model_artifact_snapshot"
    ) != manifest["nested_model_artifact_snapshot"]:
        raise ValueError("source-v0 scoring model snapshot mismatch")
    boundaries = scoring_receipt.get("boundaries")
    if not isinstance(boundaries, Mapping):
        raise ValueError("source-v0 scoring receipt boundaries are invalid")
    if boundaries.get("score_tensor_derived_by_managed_scoring") is not True:
        raise ValueError("source-v0 score tensor was not managed-derived")
    if boundaries.get(
        "nested_model_artifacts_reverified_before_scoring"
    ) is not True:
        raise ValueError("source-v0 scoring did not reverify nested model artifacts")
    if boundaries.get("shell_used") is not False:
        raise ValueError("source-v0 managed scoring must report shell_used=false")
    expected_execution_count = len(source_ids) * len(inner_ids)
    if scoring_receipt.get("execution_count") != expected_execution_count:
        raise ValueError("source-v0 managed scoring execution count mismatch")
    if scoring_receipt.get("source_draw_count") != len(source_ids):
        raise ValueError("source-v0 managed scoring source count mismatch")
    if scoring_receipt.get("inner_refit_count_per_source") != len(inner_ids):
        raise ValueError("source-v0 managed scoring inner-refit count mismatch")
    if scoring_receipt.get("row_count") != len(design_rows):
        raise ValueError("source-v0 managed scoring row count mismatch")

    frozen_level_names = [
        str(row["name"])
        for row in manifest.get("levels", ())
        if isinstance(row, Mapping)
    ]
    if scoring_receipt.get("level_names") != frozen_level_names:
        raise ValueError("source-v0 managed scoring level names mismatch")

    executions = scoring_receipt.get("executions")
    if not isinstance(executions, list) or len(executions) != expected_execution_count:
        raise ValueError("source-v0 managed scoring execution coverage mismatch")
    expected_pairs = [
        (source_id, refit_id)
        for source_id in source_ids
        for refit_id in inner_ids
    ]
    observed_pairs: list[tuple[str, str]] = []
    for execution in executions:
        if not isinstance(execution, Mapping):
            raise ValueError("source-v0 managed scoring execution must be an object")
        observed_pairs.append(
            (
                _text(execution.get("source_draw_id"), name="scoring source_draw_id"),
                _text(execution.get("inner_refit_id"), name="scoring inner_refit_id"),
            )
        )
        if execution.get("return_code") != 0:
            raise ValueError("source-v0 managed scoring execution has nonzero return code")
        digest = execution.get("score_output_sha256")
        if not isinstance(digest, str) or len(digest) != 64:
            raise ValueError("source-v0 managed scoring output SHA256 is invalid")
    if observed_pairs != expected_pairs:
        raise ValueError("source-v0 managed scoring source-inner coverage mismatch")

    bundle, tensor = load_managed_training_source_score_bundle(
        bundle_path,
        expected_bundle_sha256=bundle_sha,
        expected_validation_freeze_manifest_sha256=_file_sha256(manifest_path),
        expected_managed_nested_generation_receipt_sha256=managed_receipt_sha,
        expected_validation_data_sha256=validation_sha,
    )
    bundle_source_ids = tuple(str(x) for x in bundle["source_draw_ids"])
    bundle_inner_ids = tuple(str(x) for x in bundle["inner_refit_ids"])
    bundle_row_ids = tuple(str(x) for x in bundle["row_ids"])
    if bundle_source_ids != source_ids:
        raise ValueError("source-v0 bundle source IDs mismatch")
    if bundle_inner_ids != inner_ids:
        raise ValueError("source-v0 bundle inner refit IDs mismatch")
    tensor_sha = str(bundle["canonical_score_tensor_sha256"])
    if tensor_sha != scoring_receipt.get("canonical_score_tensor_sha256"):
        raise ValueError("source-v0 managed score tensor digest mismatch")
    if bundle.get("levels") != manifest["levels"]:
        raise ValueError("source-v0 bundle level metadata mismatch")

    runtime_row_ids = tuple(
        _text(x, name="validation_row_id") for x in validation_row_ids
    )
    if len(runtime_row_ids) != len(set(runtime_row_ids)):
        raise ValueError("runtime validation row IDs must be unique")
    if set(bundle_row_ids) != set(runtime_row_ids):
        raise ValueError("source-v0 managed score rows do not match validation rows")
    row_index = {row_id: i for i, row_id in enumerate(bundle_row_ids)}
    reorder = [row_index[row_id] for row_id in runtime_row_ids]
    aligned = np.asarray(tensor, dtype=float)[:, :, reorder, :]

    nested_levels: list[tuple[RefitInformationLevelScores, ...]] = []
    for source_index in range(len(source_ids)):
        source_levels: list[RefitInformationLevelScores] = []
        for level_index, meta in enumerate(manifest["levels"]):
            if not isinstance(meta, Mapping):
                raise ValueError("source-v0 frozen level metadata is invalid")
            source_levels.append(
                RefitInformationLevelScores(
                    str(meta["name"]),
                    tuple(str(x) for x in meta["information"]),
                    aligned[source_index, :, :, level_index],
                )
            )
        nested_levels.append(tuple(source_levels))

    certification = manifest.get("certification")
    score = manifest.get("score")
    if not isinstance(certification, Mapping) or not isinstance(score, Mapping):
        raise ValueError("source-v0 frozen certification/score metadata is invalid")
    result = evaluate_training_source_process_positive_information_v0(
        tuple(nested_levels),
        groups,
        blocks=blocks,
        source_draw_ids=source_ids,
        inner_refit_ids_by_source=tuple(
            tuple(inner_ids) for _ in source_ids
        ),
        source_process_id=source_process_id,
        source_process_manifest_sha256=source_manifest_sha,
        score_name=str(score["name"]),
        sample_weight=sample_weight,
        component_one_sided_alpha=float(
            certification["component_one_sided_alpha"]
        ),
        minimum_source_draws=int(certification["minimum_source_draws"]),
        minimum_inner_refits_per_source=int(
            certification["minimum_inner_refits_per_source"]
        ),
        minimum_blocks_per_group=int(
            certification["minimum_blocks_per_group"]
        ),
        gain_tolerance=float(certification["gain_tolerance"]),
    )

    return ManagedInternalTrainingSourceProcessV0Certification(
        schema_version=1,
        receipt_type=MANAGED_INTERNAL_RECEIPT_TYPE,
        validation_dataset_id=str(manifest["validation_dataset_id"]),
        validation_freeze_manifest_sha256=_file_sha256(manifest_path),
        validation_freeze_receipt_sha256=_file_sha256(freeze_receipt_path),
        validation_design_sha256=design_sha,
        validation_row_count=len(design_rows),
        validation_outcomes_first_accessed_at_utc=access_text,
        freeze_precedes_declared_first_validation_outcome_access=True,
        managed_validation_data_first_read_by_odsp_at_utc=managed_read_text,
        managed_validation_read_after_freeze=True,
        declared_first_access_not_after_managed_validation_read=True,
        source_process_id=source_process_id,
        source_process_manifest_sha256=source_manifest_sha,
        managed_nested_generation_receipt_sha256=managed_receipt_sha,
        managed_scoring_receipt_sha256=_file_sha256(scoring_receipt_path),
        score_bundle_sha256=bundle_sha,
        canonical_score_tensor_sha256=tensor_sha,
        source_frame_validation_disjoint=True,
        nested_model_artifact_snapshot_verified=True,
        fit_environment_snapshot_verified=True,
        score_tensor_derived_by_managed_scoring=True,
        semantic_use_of_model_and_validation_inputs_cryptographically_proven=False,
        implementation_source_snapshot_verified=True,
        runtime_environment_snapshot_verified=True,
        historical_no_prior_validation_outcome_access_machine_proven=False,
        unknown_ecological_superpopulation_generalization_claimed=False,
        qualified_training_process_v5_reclassified=False,
        evaluation=result,
    )
