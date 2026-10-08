"""Provenance-verifying wrapper for future-refit success probability v1.

This wrapper is deliberately separate from the qualified process-mean v5
surface.  It reuses the same frozen-process provenance requirements without
modifying the v5 source closure, then invokes the experimental
future-refit-success-probability numerical core.

The wrapper is not primary confirmatory merely because it exists.  Promotion
requires the separate prospective operating-characteristic panel to pass and
its own implementation/evidence identity to be frozen.
"""
from __future__ import annotations

from dataclasses import asdict, dataclass
from pathlib import Path
from typing import Sequence

from .refit_information_transfer import RefitInformationLevelScores
from .training_process_confirmatory_v5 import (
    _load_json,
    _manifest_schedule,
    _sha256_text,
    _text,
    _verify_managed_receipt,
)
from .training_process_freeze_manifest import _file_sha256
from .training_process_future_refit_success_probability import (
    PROCESS_ALPHA,
    VALIDATION_ALPHA,
    FutureRefitSuccessProbabilityInformationCertification,
    certify_training_process_future_refit_success_probability_v1,
)
from .training_process_validation_provenance import (
    TrainingProcessValidationFrameAudit,
    audit_training_process_validation_frame_separation,
)


SURFACE_ID = "odsp-training-process-future-refit-success-probability-v1"


@dataclass(frozen=True)
class TrainingProcessFutureRefitSuccessProbabilityV1Certification:
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
    process_mean_v5_results_reclassified: bool
    historical_empirical_endpoints_reclassified: bool
    frame_audit: TrainingProcessValidationFrameAudit
    certification: FutureRefitSuccessProbabilityInformationCertification

    def as_dict(self) -> dict[str, object]:
        payload = asdict(self)
        payload["frame_audit"] = self.frame_audit.as_dict()
        payload["certification"] = self.certification.as_dict()
        return payload


def certify_predeclared_training_process_future_refit_success_probability_v1(
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
    validation_alpha: float = VALIDATION_ALPHA,
    process_alpha: float = PROCESS_ALPHA,
    bootstrap_draws: int = 4000,
    seed: int = 20261016,
    minimum_refits: int = 8,
    minimum_blocks_per_group: int = 8,
    gain_tolerance: float = 0.0,
) -> TrainingProcessFutureRefitSuccessProbabilityV1Certification:
    """Run the probability candidate only after frozen-process provenance checks."""

    manifest_path = Path(training_process_manifest_path)
    receipt_path = Path(managed_generation_receipt_path)
    if not manifest_path.is_file():
        raise FileNotFoundError(manifest_path)
    if not receipt_path.is_file():
        raise FileNotFoundError(receipt_path)

    manifest_sha = _file_sha256(manifest_path)
    manifest = _load_json(manifest_path, name="training process manifest")
    process_id, frozen_refits, schedule = _manifest_schedule(manifest)

    supplied_refits = tuple(
        sorted(_text(value, name="refit_id") for value in refit_ids)
    )
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
            "future-refit probability inference is not admissible"
        )

    certification = (
        certify_training_process_future_refit_success_probability_v1(
            levels,
            groups,
            blocks=blocks,
            refit_ids=refit_ids,
            training_process_id=process_id,
            training_process_manifest_sha256=manifest_sha,
            score_name=score_name,
            sample_weight=sample_weight,
            validation_alpha=validation_alpha,
            process_alpha=process_alpha,
            bootstrap_draws=bootstrap_draws,
            seed=seed,
            minimum_refits=minimum_refits,
            minimum_blocks_per_group=minimum_blocks_per_group,
            gain_tolerance=gain_tolerance,
        )
    )

    return TrainingProcessFutureRefitSuccessProbabilityV1Certification(
        schema_version=1,
        surface_id=SURFACE_ID,
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
        process_mean_v5_results_reclassified=False,
        historical_empirical_endpoints_reclassified=False,
        frame_audit=frame_audit,
        certification=certification,
    )
