"""High-level provenance gate for frozen training-process IUT v2 inference.

This endpoint binds the numerical IUT core to:
- a content-locked training-process freeze manifest,
- a generation receipt that exactly matches the frozen refit schedule,
- runtime model artifact bytes matching the generation receipt, and
- explicit training/validation row separation for every generated refit.

It does not itself prove the wall-clock fact that validation outcomes were
unseen before the process freeze. That temporal access boundary remains a
separate governance requirement before primary confirmatory routing.
"""
from __future__ import annotations

from dataclasses import dataclass
import json
from pathlib import Path
from typing import Mapping, Sequence

from .refit_information_transfer import RefitInformationLevelScores
from .refit_training_validation_provenance import (
    RefitTrainingValidationProvenanceAudit,
    audit_refit_training_validation_provenance,
)
from .training_process_freeze_manifest import (
    PROCESS_MANIFEST_TYPE,
    _file_sha256,
)
from .training_process_generation_receipt import GENERATION_RECEIPT_TYPE
from .training_process_positive_transfer_v2 import (
    TrainingProcessIUTInformationTransferCertification,
    certify_training_process_positive_information_transfer_v2,
)
from .upstream_model_artifact_lock import (
    MODEL_ARTIFACT_LOCK_ID,
    normalize_upstream_model_artifact_snapshot,
    verify_upstream_model_artifact_snapshot,
)


@dataclass(frozen=True)
class FrozenTrainingProcessIUTCertification:
    schema_version: int
    training_process_id: str
    process_manifest_sha256: str
    generation_receipt_sha256: str
    process_manifest_verified: bool
    generation_receipt_verified: bool
    model_artifact_bytes_verified: bool
    training_validation_separated: bool
    process_freeze_preceded_validation_outcome_access_verified_here: bool
    historical_fixed_set_results_reclassified: bool
    training_validation_provenance: RefitTrainingValidationProvenanceAudit
    certification: TrainingProcessIUTInformationTransferCertification

    def as_dict(self) -> dict[str, object]:
        return {
            "schema_version": self.schema_version,
            "training_process_id": self.training_process_id,
            "process_manifest_sha256": self.process_manifest_sha256,
            "generation_receipt_sha256": self.generation_receipt_sha256,
            "process_manifest_verified": self.process_manifest_verified,
            "generation_receipt_verified": self.generation_receipt_verified,
            "model_artifact_bytes_verified": self.model_artifact_bytes_verified,
            "training_validation_separated": self.training_validation_separated,
            "process_freeze_preceded_validation_outcome_access_verified_here": self.process_freeze_preceded_validation_outcome_access_verified_here,
            "historical_fixed_set_results_reclassified": self.historical_fixed_set_results_reclassified,
            "training_validation_provenance": self.training_validation_provenance.as_dict(),
            "certification": self.certification.as_dict(),
        }


def _load(path: Path, *, name: str) -> dict[str, object]:
    try:
        raw=json.loads(path.read_text(encoding="utf-8"))
    except json.JSONDecodeError as exc:
        raise ValueError(f"{name} is not valid JSON: {path}") from exc
    if not isinstance(raw, Mapping):
        raise ValueError(f"{name} must be a JSON object")
    return dict(raw)


def _text(value: object, *, name: str) -> str:
    if not isinstance(value,str) or not value.strip():
        raise ValueError(f"{name} must be non-empty text")
    return value.strip()


def _refit_ids(manifest: Mapping[str, object]) -> tuple[str, ...]:
    raw=manifest.get("refit_ids")
    if not isinstance(raw,list) or not raw:
        raise ValueError("manifest.refit_ids must be a non-empty JSON array")
    ids=tuple(_text(value,name=f"manifest.refit_ids[{i}]") for i,value in enumerate(raw))
    if len(ids)!=len(set(ids)):
        raise ValueError("manifest.refit_ids must be unique")
    return tuple(sorted(ids))


def certify_frozen_training_process_positive_information_transfer_v2(
    levels: Sequence[RefitInformationLevelScores],
    groups: Sequence[object],
    *,
    blocks: Sequence[object],
    score_refit_ids: Sequence[object],
    validation_row_ids: Sequence[object],
    training_row_ids_by_refit: Mapping[object, Sequence[object]],
    process_manifest_path: str | Path,
    generation_receipt_path: str | Path,
    upstream_model_artifacts: Sequence[Mapping[str, object]],
    score_name: str = "log",
    sample_weight: Sequence[float] | None = None,
    cellwise_lower_confidence_level: float = 0.95,
    bootstrap_draws: int = 4000,
    seed: int = 20261012,
    minimum_blocks_per_group: int = 8,
    gain_tolerance: float = 0.0,
) -> FrozenTrainingProcessIUTCertification:
    manifest_path=Path(process_manifest_path)
    receipt_path=Path(generation_receipt_path)
    manifest=_load(manifest_path,name="training process manifest")
    receipt=_load(receipt_path,name="training process generation receipt")

    if manifest.get("manifest_type")!=PROCESS_MANIFEST_TYPE:
        raise ValueError("unrecognized training process manifest_type")
    if receipt.get("receipt_type")!=GENERATION_RECEIPT_TYPE:
        raise ValueError("unrecognized training process generation receipt_type")

    process_id=_text(
        manifest.get("training_process_id"),
        name="manifest.training_process_id",
    )
    if _text(receipt.get("training_process_id"),name="receipt.training_process_id")!=process_id:
        raise ValueError("generation receipt process identity does not match manifest")

    manifest_sha=_file_sha256(manifest_path)
    if receipt.get("process_manifest_sha256")!=manifest_sha:
        raise ValueError("generation receipt is not bound to the supplied process manifest bytes")

    frozen_ids=_refit_ids(manifest)
    receipt_ids=receipt.get("refit_ids")
    if not isinstance(receipt_ids,list) or tuple(receipt_ids)!=frozen_ids:
        raise ValueError("generation receipt refit IDs do not exactly match the frozen manifest")

    score_ids=tuple(str(value).strip() for value in score_refit_ids)
    if len(score_ids)!=len(frozen_ids) or set(score_ids)!=set(frozen_ids):
        raise ValueError("score_refit_ids must exactly cover the frozen process refits")

    lock_id=receipt.get("upstream_model_artifact_lock_id")
    if lock_id!=MODEL_ARTIFACT_LOCK_ID:
        raise ValueError("generation receipt model artifact lock ID is not recognized")
    snapshot=normalize_upstream_model_artifact_snapshot(
        receipt.get("upstream_model_artifact_snapshot"),
        refit_ids=frozen_ids,
    )
    verify_upstream_model_artifact_snapshot(
        snapshot,
        upstream_model_artifacts,
        base_dir=receipt_path.parent,
        refit_ids=frozen_ids,
    )

    normalized_training={
        str(key).strip(): tuple(values)
        for key,values in training_row_ids_by_refit.items()
    }
    if set(normalized_training)!=set(frozen_ids):
        raise ValueError(
            "training_row_ids_by_refit must exactly cover the frozen process refits"
        )
    provenance=audit_refit_training_validation_provenance(
        validation_row_ids,
        {"frozen_training_process": normalized_training},
        expected_refit_ids_by_scheme={
            "frozen_training_process": frozen_ids,
        },
    )
    if not provenance.training_validation_separated:
        raise ValueError("training/validation leakage detected for frozen training process")

    certification=certify_training_process_positive_information_transfer_v2(
        levels,
        groups,
        blocks=blocks,
        refit_ids=score_ids,
        training_process_id=process_id,
        training_process_manifest_sha256=manifest_sha,
        score_name=score_name,
        sample_weight=sample_weight,
        cellwise_lower_confidence_level=cellwise_lower_confidence_level,
        bootstrap_draws=bootstrap_draws,
        seed=seed,
        minimum_refits=len(frozen_ids),
        minimum_blocks_per_group=minimum_blocks_per_group,
        gain_tolerance=gain_tolerance,
    )
    return FrozenTrainingProcessIUTCertification(
        schema_version=2,
        training_process_id=process_id,
        process_manifest_sha256=manifest_sha,
        generation_receipt_sha256=_file_sha256(receipt_path),
        process_manifest_verified=True,
        generation_receipt_verified=True,
        model_artifact_bytes_verified=True,
        training_validation_separated=True,
        process_freeze_preceded_validation_outcome_access_verified_here=False,
        historical_fixed_set_results_reclassified=False,
        training_validation_provenance=provenance,
        certification=certification,
    )
