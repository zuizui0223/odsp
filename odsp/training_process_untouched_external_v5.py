"""Untouched-external endpoint for the qualified predeclared training-process v5 route."""
from __future__ import annotations

from dataclasses import asdict, dataclass
import json
from pathlib import Path
import numpy as np
from typing import Mapping, Sequence

from .confirmatory_environment_lock import (
    ENVIRONMENT_LOCK_ID,
    runtime_environment_snapshot_for_surface,
)
from .confirmatory_implementation_lock import (
    IMPLEMENTATION_LOCK_ID,
    implementation_source_snapshot_for_surface,
)
from .refit_information_transfer import RefitInformationLevelScores
from .training_process_managed_external_scoring import (
    MANAGED_SCORING_RECEIPT_TYPE,
    load_managed_external_score_bundle,
)
from .training_process_confirmatory_v5 import (
    TrainingProcessConfirmatoryV5Certification,
    _load_json,
    _manifest_schedule,
    _verify_managed_receipt,
    certify_predeclared_training_process_positive_information_v5,
)
from .training_process_external_freeze_v1 import (
    EXTERNAL_SURFACE,
    FREEZE_RECEIPT_TYPE,
    MANIFEST_TYPE,
    _canonical_sha256,
    _external_design_rows,
    _model_artifact_snapshot,
    build_internal_v5_route_snapshot,
)
from .training_process_freeze_manifest import _file_sha256


EXTERNAL_RECEIPT_TYPE = "odsp_untouched_external_training_process_v5_endpoint_v1"


@dataclass(frozen=True)
class UntouchedExternalTrainingProcessV5Certification:
    schema_version: int
    receipt_type: str
    external_dataset_id: str
    external_freeze_manifest_sha256: str
    external_freeze_receipt_sha256: str
    external_design_sha256: str
    external_row_count: int
    training_process_id: str
    training_process_manifest_sha256: str
    managed_generation_receipt_sha256: str
    managed_scoring_receipt_sha256: str
    score_bundle_sha256: str
    canonical_score_tensor_sha256: str
    freeze_manifest_semantics_verified: bool
    external_design_exact_match_verified: bool
    process_identity_exact_match_verified: bool
    generated_model_artifact_snapshot_verified: bool
    fit_environment_snapshot_verified: bool
    score_tensor_derived_by_managed_scoring: bool
    qualification_evidence_snapshot_verified: bool
    implementation_source_snapshot_verified: bool
    runtime_environment_snapshot_verified: bool
    training_source_frame_validation_disjoint: bool
    historical_no_prior_external_outcome_access_machine_proven: bool
    external_distribution_shift_robustness_claimed: bool
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


def _manifest_fields(manifest: Mapping[str, object]) -> None:
    required = {
        "schema_version",
        "manifest_type",
        "frozen_at_utc",
        "external_dataset_id",
        "row_identity_namespace",
        "external_design_sha256",
        "external_row_count",
        "external_group_count",
        "positive_block_count_by_group",
        "training_process_id",
        "training_process_manifest_sha256",
        "training_roster_spec",
        "managed_generation_receipt_sha256",
        "refit_ids",
        "generated_model_artifact_snapshot",
        "fit_environment_snapshot",
        "managed_scoring_plan",
        "training_source_frame_validation_disjoint",
        "training_source_frame_audit",
        "internal_qualified_route",
        "external_endpoint",
        "score",
        "levels",
        "certification",
        "boundaries",
    }
    if set(manifest) != required:
        raise ValueError(
            "external freeze manifest fields mismatch: "
            f"missing={sorted(required-set(manifest))!r}, "
            f"unknown={sorted(set(manifest)-required)!r}"
        )
    if manifest.get("schema_version") != 1 or isinstance(
        manifest.get("schema_version"), bool
    ):
        raise ValueError("external freeze manifest schema_version must be 1")
    if manifest.get("manifest_type") != MANIFEST_TYPE:
        raise ValueError("external freeze manifest_type is not recognized")


def _verify_freeze_receipt(
    receipt: Mapping[str, object],
    *,
    receipt_path: Path,
    manifest_path: Path,
    manifest: Mapping[str, object],
) -> None:
    if receipt.get("receipt_type") != FREEZE_RECEIPT_TYPE:
        raise ValueError("external freeze receipt_type is not recognized")
    if receipt.get("schema_version") != 1:
        raise ValueError("external freeze receipt schema_version must be 1")
    if receipt.get("manifest_sha256") != _file_sha256(manifest_path):
        raise ValueError("external freeze receipt manifest SHA256 mismatch")
    if receipt.get("frozen_at_utc") != manifest.get("frozen_at_utc"):
        raise ValueError("external freeze receipt timestamp mismatch")
    if receipt.get("external_design_sha256") != manifest.get(
        "external_design_sha256"
    ):
        raise ValueError("external freeze receipt design digest mismatch")
    if receipt.get("training_process_manifest_sha256") != manifest.get(
        "training_process_manifest_sha256"
    ):
        raise ValueError("external freeze receipt process manifest digest mismatch")
    if receipt.get("managed_generation_receipt_sha256") != manifest.get(
        "managed_generation_receipt_sha256"
    ):
        raise ValueError("external freeze receipt managed-generation digest mismatch")
    if receipt.get("training_process_id") != manifest.get("training_process_id"):
        raise ValueError("external freeze receipt process ID mismatch")
    if receipt.get("external_row_count") != manifest.get("external_row_count"):
        raise ValueError("external freeze receipt row-count mismatch")
    # Reading the receipt path here makes the exact receipt content identity
    # explicit in the endpoint output, even though local hashes cannot attest
    # historical non-access.
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
    rows = [
        {
            "row_id": validation_row_ids[i],
            "group_id": groups[i],
            "block_id": blocks[i],
            "sample_weight": sample_weight[i],
        }
        for i in range(n)
    ]
    return _external_design_rows(rows)


def _level_metadata(
    levels: Sequence[RefitInformationLevelScores],
) -> list[dict[str, object]]:
    rows: list[dict[str, object]] = []
    for i, level in enumerate(levels):
        name = _text(getattr(level, "name", None), name=f"levels[{i}].name")
        information = getattr(level, "information", None)
        if not isinstance(information, (tuple, list)):
            raise ValueError(f"levels[{i}].information must be a sequence")
        values = [
            _text(value, name=f"levels[{i}].information")
            for value in information
        ]
        rows.append({"name": name, "information": values})
    return rows


def run_untouched_external_training_process_v5(
    external_freeze_manifest_path: str | Path,
    external_freeze_receipt_path: str | Path,
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
) -> UntouchedExternalTrainingProcessV5Certification:
    """Run untouched external v5 only after exact pre-outcome semantic verification."""

    freeze_manifest_path = Path(external_freeze_manifest_path)
    freeze_receipt_path = Path(external_freeze_receipt_path)
    process_manifest_path = Path(training_process_manifest_path)
    managed_receipt_path = Path(managed_generation_receipt_path)
    scoring_receipt_path = Path(managed_scoring_receipt_path)
    bundle_path = Path(score_bundle_path)
    validation_path = Path(validation_data_path)
    roster_path = Path(training_roster_path)
    for path in (
        freeze_manifest_path,
        freeze_receipt_path,
        process_manifest_path,
        managed_receipt_path,
        scoring_receipt_path,
        bundle_path,
        validation_path,
        roster_path,
    ):
        if not path.is_file():
            raise FileNotFoundError(path)

    manifest = _load_json(
        freeze_manifest_path, name="external freeze manifest"
    )
    _manifest_fields(manifest)
    freeze_receipt = _load_json(
        freeze_receipt_path, name="external freeze receipt"
    )
    _verify_freeze_receipt(
        freeze_receipt,
        receipt_path=freeze_receipt_path,
        manifest_path=freeze_manifest_path,
        manifest=manifest,
    )

    design_rows, block_counts = _runtime_design(
        validation_row_ids,
        groups,
        blocks,
        sample_weight,
    )
    design_sha = _canonical_sha256(design_rows)
    if design_sha != manifest["external_design_sha256"]:
        raise ValueError(
            "runtime external row/group/block/weight design does not match freeze"
        )
    if len(design_rows) != manifest["external_row_count"]:
        raise ValueError("runtime external row count does not match freeze")
    if block_counts != manifest["positive_block_count_by_group"]:
        raise ValueError("runtime positive block counts do not match freeze")

    process_manifest_sha = _file_sha256(process_manifest_path)
    if process_manifest_sha != manifest["training_process_manifest_sha256"]:
        raise ValueError("runtime training process manifest does not match freeze")
    process_manifest = _load_json(
        process_manifest_path, name="training process manifest"
    )
    process_id, frozen_refits, schedule = _manifest_schedule(process_manifest)
    if process_id != manifest["training_process_id"]:
        raise ValueError("runtime training process ID does not match freeze")
    supplied_refits = tuple(
        sorted(_text(value, name="refit_id") for value in refit_ids)
    )
    if supplied_refits != tuple(manifest["refit_ids"]) or supplied_refits != frozen_refits:
        raise ValueError("runtime refit IDs do not match external freeze")

    managed_receipt_sha = _file_sha256(managed_receipt_path)
    if managed_receipt_sha != manifest["managed_generation_receipt_sha256"]:
        raise ValueError("runtime managed-generation receipt does not match freeze")
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
    if _model_artifact_snapshot(managed_receipt) != manifest[
        "generated_model_artifact_snapshot"
    ]:
        raise ValueError("generated model artifact snapshot does not match freeze")
    if managed_receipt.get("fit_environment_snapshot") != manifest.get(
        "fit_environment_snapshot"
    ):
        raise ValueError("managed fit environment snapshot does not match freeze")

    expected_route = build_internal_v5_route_snapshot()
    if manifest["internal_qualified_route"] != expected_route:
        raise ValueError("frozen internal v5 qualification route no longer matches")

    endpoint = manifest["external_endpoint"]
    if not isinstance(endpoint, Mapping):
        raise ValueError("external_endpoint must be an object")
    if endpoint.get("canonical_surface") != EXTERNAL_SURFACE:
        raise ValueError("external endpoint surface mismatch")
    if endpoint.get("implementation_lock_id") != IMPLEMENTATION_LOCK_ID:
        raise ValueError("external endpoint implementation lock mismatch")
    current_source = [
        dict(row) for row in implementation_source_snapshot_for_surface(EXTERNAL_SURFACE)
    ]
    if endpoint.get("implementation_source_snapshot") != current_source:
        raise ValueError("external endpoint source snapshot mismatch")
    if endpoint.get("environment_lock_id") != ENVIRONMENT_LOCK_ID:
        raise ValueError("external endpoint environment lock mismatch")
    current_env = runtime_environment_snapshot_for_surface(EXTERNAL_SURFACE)
    if endpoint.get("runtime_environment_snapshot") != current_env:
        raise ValueError("external endpoint runtime environment mismatch")

    scoring_receipt = _load_json(
        scoring_receipt_path, name="managed scoring receipt"
    )
    if scoring_receipt.get("receipt_type") != MANAGED_SCORING_RECEIPT_TYPE:
        raise ValueError("managed scoring receipt_type is not recognized")
    freeze_manifest_sha = _file_sha256(freeze_manifest_path)
    freeze_receipt_sha = _file_sha256(freeze_receipt_path)
    validation_sha = _file_sha256(validation_path)
    bundle_sha = _file_sha256(bundle_path)
    scoring_checks = {
        "external_freeze_manifest_sha256": freeze_manifest_sha,
        "external_freeze_receipt_sha256": freeze_receipt_sha,
        "managed_generation_receipt_sha256": managed_receipt_sha,
        "validation_data_sha256": validation_sha,
        "score_bundle_sha256": bundle_sha,
    }
    for field, expected in scoring_checks.items():
        if scoring_receipt.get(field) != expected:
            raise ValueError(f"managed scoring receipt {field} mismatch")
    scoring_plan = manifest.get("managed_scoring_plan")
    if not isinstance(scoring_plan, Mapping):
        raise ValueError("frozen managed_scoring_plan is invalid")
    if scoring_receipt.get("scoring_command_artifact_snapshot") != scoring_plan.get(
        "command_artifact_snapshot"
    ):
        raise ValueError("managed scoring command artifact snapshot mismatch")
    if scoring_receipt.get(
        "scoring_runtime_environment_snapshot"
    ) != scoring_plan.get("runtime_environment_snapshot"):
        raise ValueError("managed scoring runtime environment snapshot mismatch")
    if scoring_receipt.get(
        "generated_model_artifact_snapshot"
    ) != manifest.get("generated_model_artifact_snapshot"):
        raise ValueError("managed scoring model artifact snapshot mismatch")
    boundaries = scoring_receipt.get("boundaries")
    if not isinstance(boundaries, Mapping):
        raise ValueError("managed scoring receipt boundaries are invalid")
    if boundaries.get("score_tensor_derived_by_managed_scoring") is not True:
        raise ValueError("managed scoring receipt does not prove managed score derivation")
    if boundaries.get(
        "generated_model_artifacts_reverified_before_scoring"
    ) is not True:
        raise ValueError("managed scoring receipt did not reverify model artifacts")
    if boundaries.get("shell_used") is not False:
        raise ValueError("managed scoring receipt must report shell_used=false")
    if scoring_receipt.get("refit_count") != len(supplied_refits):
        raise ValueError("managed scoring receipt refit_count mismatch")
    if scoring_receipt.get("row_count") != len(design_rows):
        raise ValueError("managed scoring receipt row_count mismatch")
    frozen_level_names = [str(row["name"]) for row in manifest["levels"]]
    if scoring_receipt.get("level_names") != frozen_level_names:
        raise ValueError("managed scoring receipt level names mismatch")
    executions = scoring_receipt.get("executions")
    if not isinstance(executions, list) or len(executions) != len(supplied_refits):
        raise ValueError("managed scoring execution coverage mismatch")
    execution_ids: list[str] = []
    for execution in executions:
        if not isinstance(execution, Mapping):
            raise ValueError("managed scoring execution must be an object")
        execution_ids.append(
            _text(execution.get("refit_id"), name="managed scoring execution refit_id")
        )
        if execution.get("return_code") != 0:
            raise ValueError("managed scoring execution has nonzero return code")
        digest = execution.get("score_output_sha256")
        if not isinstance(digest, str) or len(digest) != 64:
            raise ValueError("managed scoring output SHA256 is invalid")
    if tuple(execution_ids) != supplied_refits:
        raise ValueError("managed scoring execution refit order mismatch")

    levels, bundle_row_ids, bundle_refit_ids, tensor_sha = (
        load_managed_external_score_bundle(
            bundle_path,
            expected_bundle_sha256=bundle_sha,
            expected_external_freeze_manifest_sha256=freeze_manifest_sha,
            expected_managed_generation_receipt_sha256=managed_receipt_sha,
            expected_validation_data_sha256=validation_sha,
        )
    )
    if tensor_sha != scoring_receipt.get("canonical_score_tensor_sha256"):
        raise ValueError("managed scoring tensor digest mismatch")
    if _level_metadata(levels) != manifest["levels"]:
        raise ValueError("managed score levels do not match external freeze")
    if tuple(bundle_refit_ids) != supplied_refits:
        raise ValueError("managed score refit IDs do not match frozen process")
    runtime_row_ids = tuple(
        _text(value, name="validation_row_id") for value in validation_row_ids
    )
    if len(runtime_row_ids) != len(set(runtime_row_ids)):
        raise ValueError("runtime validation row IDs must be unique")
    if set(bundle_row_ids) != set(runtime_row_ids):
        raise ValueError("managed score row IDs do not match runtime external rows")
    bundle_index = {row_id: index for index, row_id in enumerate(bundle_row_ids)}
    reorder = [bundle_index[row_id] for row_id in runtime_row_ids]
    aligned_levels = tuple(
        RefitInformationLevelScores(
            level.name,
            level.information,
            np.asarray(level.score, dtype=float)[:, reorder],
        )
        for level in levels
    )

    score = manifest["score"]
    if not isinstance(score, Mapping):
        raise ValueError("frozen score must be an object")
    certification = manifest["certification"]
    if not isinstance(certification, Mapping):
        raise ValueError("frozen certification must be an object")
    roster_spec = manifest["training_roster_spec"]
    if not isinstance(roster_spec, Mapping):
        raise ValueError("training_roster_spec must be an object")

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
        roster_format=roster_spec["format"],
        unit_id_column=roster_spec["unit_id_column"],
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

    return UntouchedExternalTrainingProcessV5Certification(
        schema_version=1,
        receipt_type=EXTERNAL_RECEIPT_TYPE,
        external_dataset_id=str(manifest["external_dataset_id"]),
        external_freeze_manifest_sha256=_file_sha256(freeze_manifest_path),
        external_freeze_receipt_sha256=_file_sha256(freeze_receipt_path),
        external_design_sha256=design_sha,
        external_row_count=len(design_rows),
        training_process_id=process_id,
        training_process_manifest_sha256=process_manifest_sha,
        managed_generation_receipt_sha256=managed_receipt_sha,
        managed_scoring_receipt_sha256=_file_sha256(scoring_receipt_path),
        score_bundle_sha256=bundle_sha,
        canonical_score_tensor_sha256=tensor_sha,
        freeze_manifest_semantics_verified=True,
        external_design_exact_match_verified=True,
        process_identity_exact_match_verified=True,
        generated_model_artifact_snapshot_verified=True,
        fit_environment_snapshot_verified=True,
        score_tensor_derived_by_managed_scoring=True,
        qualification_evidence_snapshot_verified=True,
        implementation_source_snapshot_verified=True,
        runtime_environment_snapshot_verified=True,
        training_source_frame_validation_disjoint=True,
        historical_no_prior_external_outcome_access_machine_proven=False,
        external_distribution_shift_robustness_claimed=False,
        fixed_set_results_reclassified=False,
        certification=result,
    )
