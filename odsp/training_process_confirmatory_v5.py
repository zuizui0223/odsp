"""Fail-closed confirmatory wrapper for the qualified training-process v5 route.

The raw CV3(2) IUT numerical core is not itself the primary confirmatory surface.
This wrapper verifies the frozen training-process identity, managed-generation
receipt, exact refit schedule, and full training-source-frame separation from
validation rows before calling the v5 numerical core.
"""
from __future__ import annotations

from dataclasses import asdict, dataclass
import json
from pathlib import Path
from typing import Mapping, Sequence

from .refit_information_transfer import RefitInformationLevelScores
from .training_process_freeze_manifest import (
    PROCESS_MANIFEST_TYPE,
    _file_sha256,
)
from .training_process_managed_generation import (
    MANAGED_GENERATION_RECEIPT_TYPE,
)
from .training_process_positive_cv3two_iut import (
    TrainingProcessPositiveCV3TwoInformationCertification,
    certify_training_process_positive_information_cv3two_iut_v5,
)
from .training_process_validation_provenance import (
    TrainingProcessValidationFrameAudit,
    audit_training_process_validation_frame_separation,
)


CONFIRMATORY_PROCESS_V5_SURFACE_ID = "odsp-training-process-confirmatory-v5"


@dataclass(frozen=True)
class TrainingProcessConfirmatoryV5Certification:
    schema_version: int
    surface_id: str
    training_process_id: str
    training_process_manifest_sha256: str
    managed_generation_receipt_sha256: str
    process_manifest_verified: bool
    managed_generation_verified: bool
    exact_refit_schedule_verified: bool
    training_source_frame_validation_disjoint: bool
    entire_training_source_frame_checked: bool
    row_identity_namespace: str
    score_table_derivation_from_generated_models_independently_proven: bool
    fixed_set_results_reclassified: bool
    historical_empirical_endpoints_reclassified: bool
    frame_audit: TrainingProcessValidationFrameAudit
    certification: TrainingProcessPositiveCV3TwoInformationCertification

    def as_dict(self) -> dict[str, object]:
        payload = asdict(self)
        payload["frame_audit"] = self.frame_audit.as_dict()
        payload["certification"] = self.certification.as_dict()
        return payload


def _load_json(path: Path, *, name: str) -> dict[str, object]:
    try:
        raw = json.loads(path.read_text(encoding="utf-8"))
    except json.JSONDecodeError as exc:
        raise ValueError(f"{name} is not valid JSON: {path}") from exc
    if not isinstance(raw, Mapping):
        raise ValueError(f"{name} must contain a JSON object")
    return dict(raw)


def _text(value: object, *, name: str) -> str:
    if not isinstance(value, str) or not value.strip():
        raise ValueError(f"{name} must be non-empty text")
    return value.strip()


def _sha256_text(value: object, *, name: str) -> str:
    digest = _text(value, name=name).lower()
    if len(digest) != 64:
        raise ValueError(f"{name} must be lowercase SHA256 text")
    try:
        int(digest, 16)
    except ValueError as exc:
        raise ValueError(f"{name} must be lowercase SHA256 text") from exc
    return digest


def _manifest_schedule(
    manifest: Mapping[str, object],
) -> tuple[str, tuple[str, ...], dict[str, dict[str, object]]]:
    if manifest.get("manifest_type") != PROCESS_MANIFEST_TYPE:
        raise ValueError("training process manifest_type is not recognized")
    process_id = _text(
        manifest.get("training_process_id"),
        name="manifest.training_process_id",
    )
    ids_raw = manifest.get("refit_ids")
    schedule_raw = manifest.get("refit_schedule")
    if not isinstance(ids_raw, list) or not ids_raw:
        raise ValueError("manifest.refit_ids must be a non-empty JSON array")
    ids = tuple(
        _text(value, name=f"manifest.refit_ids[{index}]")
        for index, value in enumerate(ids_raw)
    )
    if len(ids) != len(set(ids)):
        raise ValueError("manifest.refit_ids must be unique")
    if not isinstance(schedule_raw, list) or len(schedule_raw) != len(ids):
        raise ValueError("manifest.refit_schedule must contain one row per refit")
    schedule: dict[str, dict[str, object]] = {}
    for index, raw in enumerate(schedule_raw):
        if not isinstance(raw, Mapping):
            raise ValueError(f"manifest.refit_schedule[{index}] must be an object")
        refit_id = _text(
            raw.get("refit_id"),
            name=f"manifest.refit_schedule[{index}].refit_id",
        )
        if refit_id in schedule:
            raise ValueError("manifest refit schedule IDs must be unique")
        resample_seed = raw.get("resample_seed")
        fit_seed = raw.get("fit_seed")
        if (
            isinstance(resample_seed, bool)
            or not isinstance(resample_seed, int)
            or resample_seed < 0
            or isinstance(fit_seed, bool)
            or not isinstance(fit_seed, int)
            or fit_seed < 0
        ):
            raise ValueError("manifest refit seeds must be non-negative integers")
        schedule[refit_id] = {
            "refit_id": refit_id,
            "resample_seed": int(resample_seed),
            "fit_seed": int(fit_seed),
            "bootstrap_membership_sha256": _sha256_text(
                raw.get("bootstrap_membership_sha256"),
                name=(
                    f"manifest.refit_schedule[{index}]."
                    "bootstrap_membership_sha256"
                ),
            ),
        }
    if set(schedule) != set(ids):
        raise ValueError("manifest refit schedule must exactly cover refit_ids")
    return process_id, tuple(sorted(ids)), schedule


def _verify_managed_receipt(
    receipt: Mapping[str, object],
    *,
    expected_receipt_sha256: str,
    actual_receipt_sha256: str,
    process_id: str,
    manifest_sha256: str,
    refit_ids: tuple[str, ...],
    schedule: Mapping[str, Mapping[str, object]],
) -> None:
    if actual_receipt_sha256 != expected_receipt_sha256:
        raise ValueError(
            "managed generation receipt bytes do not match declared SHA256"
        )
    if receipt.get("receipt_type") != MANAGED_GENERATION_RECEIPT_TYPE:
        raise ValueError("managed generation receipt_type is not recognized")
    if _text(
        receipt.get("training_process_id"),
        name="managed receipt.training_process_id",
    ) != process_id:
        raise ValueError("managed generation process ID does not match manifest")
    if _sha256_text(
        receipt.get("training_process_manifest_sha256"),
        name="managed receipt.training_process_manifest_sha256",
    ) != manifest_sha256:
        raise ValueError("managed generation receipt is bound to another manifest")

    executions_raw = receipt.get("executions")
    if not isinstance(executions_raw, list) or not executions_raw:
        raise ValueError("managed generation receipt executions must be non-empty")
    executions: dict[str, Mapping[str, object]] = {}
    for index, raw in enumerate(executions_raw):
        if not isinstance(raw, Mapping):
            raise ValueError(f"managed receipt executions[{index}] must be an object")
        refit_id = _text(
            raw.get("refit_id"),
            name=f"managed receipt executions[{index}].refit_id",
        )
        if refit_id in executions:
            raise ValueError("managed generation execution refit IDs must be unique")
        executions[refit_id] = raw

    if tuple(sorted(executions)) != refit_ids:
        raise ValueError(
            "managed generation receipt must exactly cover frozen refit IDs"
        )

    for refit_id in refit_ids:
        row = executions[refit_id]
        frozen = schedule[refit_id]
        if row.get("resample_seed") != frozen["resample_seed"]:
            raise ValueError(f"managed resample seed mismatch for {refit_id}")
        if row.get("fit_seed") != frozen["fit_seed"]:
            raise ValueError(f"managed fit seed mismatch for {refit_id}")
        if _sha256_text(
            row.get("membership_semantic_sha256"),
            name=f"managed receipt {refit_id} membership digest",
        ) != frozen["bootstrap_membership_sha256"]:
            raise ValueError(
                f"managed bootstrap membership mismatch for {refit_id}"
            )
        if row.get("return_code") != 0:
            raise ValueError(f"managed generation did not succeed for {refit_id}")
        artifacts = row.get("artifacts")
        if not isinstance(artifacts, list) or not artifacts:
            raise ValueError(f"managed generation artifacts missing for {refit_id}")
        for artifact_index, artifact in enumerate(artifacts):
            if not isinstance(artifact, Mapping):
                raise ValueError("managed generation artifact must be an object")
            _text(
                artifact.get("artifact_id"),
                name=f"{refit_id} artifact[{artifact_index}].artifact_id",
            )
            _sha256_text(
                artifact.get("sha256"),
                name=f"{refit_id} artifact[{artifact_index}].sha256",
            )

    boundaries = receipt.get("boundaries")
    if not isinstance(boundaries, Mapping):
        raise ValueError("managed receipt boundaries must be an object")
    required_true = (
        "exact_membership_digest_verified_before_each_fit",
        "exact_command_invocation_recorded",
        "output_artifact_bytes_bound",
    )
    for key in required_true:
        if boundaries.get(key) is not True:
            raise ValueError(f"managed receipt boundary must be true: {key}")
    if boundaries.get("validation_outcomes_read") is not False:
        raise ValueError("managed generation receipt must report no validation outcomes read")
    if boundaries.get("shell_used") is not False:
        raise ValueError("managed generation receipt must report shell_used=false")


def certify_predeclared_training_process_positive_information_v5(
    levels: Sequence[RefitInformationLevelScores],
    groups: Sequence[object],
    *,
    blocks: Sequence[object],
    validation_row_ids: Sequence[object],
    refit_ids: Sequence[object],
    training_process_manifest_path: str | Path,
    managed_generation_receipt_path: str | Path,
    managed_generation_receipt_sha256: object,
    training_roster_path: str | Path,
    row_identity_namespace: object,
    roster_format: str,
    unit_id_column: str,
    stratum_column: str | None = None,
    score_name: str = "log",
    sample_weight: Sequence[float] | None = None,
    component_one_sided_alpha: float = 0.05,
    minimum_refits: int = 8,
    minimum_blocks_per_group: int = 8,
    gain_tolerance: float = 0.0,
) -> TrainingProcessConfirmatoryV5Certification:
    """Run the qualified process-mean route only after provenance verification."""

    manifest_path = Path(training_process_manifest_path)
    receipt_path = Path(managed_generation_receipt_path)
    if not manifest_path.is_file():
        raise FileNotFoundError(manifest_path)
    if not receipt_path.is_file():
        raise FileNotFoundError(receipt_path)

    manifest_sha = _file_sha256(manifest_path)
    manifest = _load_json(manifest_path, name="training process manifest")
    process_id, frozen_refits, schedule = _manifest_schedule(manifest)

    supplied_refits = tuple(sorted(_text(x, name="refit_id") for x in refit_ids))
    if len(supplied_refits) != len(set(supplied_refits)):
        raise ValueError("refit_ids must be unique")
    if supplied_refits != frozen_refits:
        raise ValueError("runtime refit IDs do not match frozen training process")

    expected_receipt_sha = _sha256_text(
        managed_generation_receipt_sha256,
        name="managed_generation_receipt_sha256",
    )
    receipt_sha = _file_sha256(receipt_path)
    receipt = _load_json(receipt_path, name="managed generation receipt")
    _verify_managed_receipt(
        receipt,
        expected_receipt_sha256=expected_receipt_sha,
        actual_receipt_sha256=receipt_sha,
        process_id=process_id,
        manifest_sha256=manifest_sha,
        refit_ids=frozen_refits,
        schedule=schedule,
    )

    # Validation identities are checked against the complete source frame.
    frame_audit = audit_training_process_validation_frame_separation(
        manifest_path,
        training_roster_path,
        validation_row_ids,
        row_identity_namespace=row_identity_namespace,
        roster_format=roster_format,
        unit_id_column=unit_id_column,
        stratum_column=stratum_column,
    )
    if not frame_audit.training_source_frame_validation_disjoint:
        raise ValueError(
            "training source frame overlaps validation rows; "
            "training-process inference is not admissible"
        )

    certification = certify_training_process_positive_information_cv3two_iut_v5(
        levels,
        groups,
        blocks=blocks,
        refit_ids=refit_ids,
        training_process_id=process_id,
        training_process_manifest_sha256=manifest_sha,
        score_name=score_name,
        sample_weight=sample_weight,
        component_one_sided_alpha=component_one_sided_alpha,
        minimum_refits=minimum_refits,
        minimum_blocks_per_group=minimum_blocks_per_group,
        gain_tolerance=gain_tolerance,
    )

    return TrainingProcessConfirmatoryV5Certification(
        schema_version=1,
        surface_id=CONFIRMATORY_PROCESS_V5_SURFACE_ID,
        training_process_id=process_id,
        training_process_manifest_sha256=manifest_sha,
        managed_generation_receipt_sha256=receipt_sha,
        process_manifest_verified=True,
        managed_generation_verified=True,
        exact_refit_schedule_verified=True,
        training_source_frame_validation_disjoint=True,
        entire_training_source_frame_checked=True,
        row_identity_namespace=frame_audit.row_identity_namespace,
        score_table_derivation_from_generated_models_independently_proven=False,
        fixed_set_results_reclassified=False,
        historical_empirical_endpoints_reclassified=False,
        frame_audit=frame_audit,
        certification=certification,
    )
