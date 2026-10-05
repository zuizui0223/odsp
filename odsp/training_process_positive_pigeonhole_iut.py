"""Training-process positive transfer v3: centered pigeonhole bootstrap + IUT."""
from __future__ import annotations

from dataclasses import asdict, dataclass
import hashlib
import math
from typing import Sequence

import numpy as np

from .information_transfer import (
    InformationLevelScore,
    InformationTransferStep,
    validate_information_filtration,
)
from .refit_information_transfer import (
    RefitInformationLevelScores,
    _integer,
    _labels,
    _refit_ids,
    _score_matrices,
    _weights,
)
from .training_process_positive_transfer import _process_identity


@dataclass(frozen=True)
class TrainingProcessPigeonholeIUTCell:
    group: object
    contrast: str
    row_count: int
    block_count: int
    total_weight: float
    process_mean_gain: float | None
    bootstrap_displacement_critical_value: float | None
    lower_bound: float | None
    status: str
    estimable: bool

    def as_dict(self) -> dict[str, object]:
        return asdict(self)


@dataclass(frozen=True)
class TrainingProcessPigeonholeIUTContrast:
    contrast: str
    category: str
    robust_positive_group_count: int
    not_robust_positive_group_count: int
    unavailable_group_count: int
    groups: tuple[TrainingProcessPigeonholeIUTCell, ...]

    def as_dict(self) -> dict[str, object]:
        return {
            "contrast": self.contrast,
            "category": self.category,
            "robust_positive_group_count": self.robust_positive_group_count,
            "not_robust_positive_group_count": self.not_robust_positive_group_count,
            "unavailable_group_count": self.unavailable_group_count,
            "groups": [row.as_dict() for row in self.groups],
        }


@dataclass(frozen=True)
class TrainingProcessPositivePigeonholeIUTAudit:
    schema_version: int
    method_version: str
    training_process_id: str
    training_process_manifest_sha256: str
    inference_target: str
    refit_count: int
    refit_ids: tuple[str, ...]
    group_count: int
    contrast_count: int
    component_lower_confidence_level: float
    bootstrap_draws: int
    seed: int
    minimum_refits: int
    minimum_blocks_per_group: int
    gain_tolerance: float
    bootstrap_method: str
    alternative: str
    compound_intersection_union_test: bool
    all_required_components_must_reject: bool
    additional_component_multiplicity_correction_applied: bool
    component_test_independence_assumed: bool
    component_lower_bounds_are_simultaneous: bool
    arbitrary_any_cell_familywise_claim_allowed: bool
    studentization_used: bool
    centered_bootstrap_displacement_used: bool
    quantile_method: str
    training_refit_draws_resampled_per_replicate: int
    same_refit_resample_shared_across_all_cells: bool
    same_validation_block_draw_shared_across_contrasts_within_group: bool
    validation_blocks_redrawn_per_refit: bool
    training_and_validation_axes_resampled_independently: bool
    refits_assumed_exchangeable_draws_from_frozen_process: bool
    process_mean_target: bool
    fixed_set_intersection_used: bool
    cell_count: int
    estimable_cell_count: int
    all_cells_estimable: bool
    contrasts: tuple[TrainingProcessPigeonholeIUTContrast, ...]

    def as_dict(self) -> dict[str, object]:
        payload = asdict(self)
        payload["refit_ids"] = list(self.refit_ids)
        payload["contrasts"] = [row.as_dict() for row in self.contrasts]
        return payload


@dataclass(frozen=True)
class TrainingProcessPositivePigeonholeIUTInformationCertification:
    schema_version: int
    method_version: str
    score_name: str
    levels: tuple[str, ...]
    steps: tuple[InformationTransferStep, ...]
    information_filtration_validated: bool
    training_process_id: str
    training_process_manifest_sha256: str
    process_mean_certified_transfer_ceiling: str
    process_audit: TrainingProcessPositivePigeonholeIUTAudit
    alternative: str
    upstream_training_uncertainty_included: bool
    validation_sample_uncertainty_included: bool
    compound_intersection_union_test: bool
    fixed_set_intersection_used: bool
    historical_fixed_set_results_reclassified: bool

    def as_dict(self) -> dict[str, object]:
        return {
            "schema_version": self.schema_version,
            "method_version": self.method_version,
            "score_name": self.score_name,
            "levels": list(self.levels),
            "steps": [row.as_dict() for row in self.steps],
            "information_filtration_validated": self.information_filtration_validated,
            "training_process_id": self.training_process_id,
            "training_process_manifest_sha256": self.training_process_manifest_sha256,
            "process_mean_certified_transfer_ceiling": self.process_mean_certified_transfer_ceiling,
            "process_audit": self.process_audit.as_dict(),
            "alternative": self.alternative,
            "upstream_training_uncertainty_included": self.upstream_training_uncertainty_included,
            "validation_sample_uncertainty_included": self.validation_sample_uncertainty_included,
            "compound_intersection_union_test": self.compound_intersection_union_test,
            "fixed_set_intersection_used": self.fixed_set_intersection_used,
            "historical_fixed_set_results_reclassified": self.historical_fixed_set_results_reclassified,
        }


def _stable_group_seed_v3(seed: int, group: object) -> int:
    digest = hashlib.sha256(
        f"{seed}|training-process-pigeonhole-iut-v3|blocks|{group!r}".encode("utf-8")
    ).digest()
    return int.from_bytes(digest[:8], "little", signed=False)


def _shared_refit_draws_v3(seed: int, refit_count: int, draws: int) -> np.ndarray:
    digest = hashlib.sha256(
        f"{seed}|training-process-pigeonhole-iut-v3|refits".encode("utf-8")
    ).digest()
    local_seed = int.from_bytes(digest[:8], "little", signed=False)
    return np.random.default_rng(local_seed).integers(
        0, refit_count, size=(draws, refit_count)
    )


def _pigeonhole_bootstrap_means(
    block_numerator: np.ndarray,
    block_weight: np.ndarray,
    refit_draws: np.ndarray,
    block_draws: np.ndarray,
) -> np.ndarray:
    numerator = np.asarray(block_numerator, dtype=float)
    weight = np.asarray(block_weight, dtype=float)
    if numerator.ndim != 3:
        raise ValueError("block_numerator must be refit x block x contrast")
    draws, resampled_refits = refit_draws.shape
    if block_draws.shape[0] != draws:
        raise ValueError("refit and block bootstrap draws must align")
    resampled_blocks = block_draws.shape[1]
    contrast_count = numerator.shape[2]
    result = np.empty((draws, contrast_count), dtype=float)

    cells_per_draw = max(resampled_refits * resampled_blocks * contrast_count, 1)
    chunk_size = max(1, min(draws, 2_000_000 // cells_per_draw))
    for start in range(0, draws, chunk_size):
        end = min(start + chunk_size, draws)
        local_refit = refit_draws[start:end]
        local_block = block_draws[start:end]
        sampled = numerator[
            local_refit[:, :, None],
            local_block[:, None, :],
            :,
        ]
        sampled_weight = weight[local_block]
        denominator = (
            float(resampled_refits) * np.sum(sampled_weight, axis=1)
        )
        result[start:end] = (
            np.sum(sampled, axis=(1, 2)) / denominator[:, None]
        )
    if not np.isfinite(result).all():
        raise ValueError("pigeonhole bootstrap produced non-finite means")
    return result


def _directional_category(statuses: Sequence[str]) -> str:
    values = tuple(statuses)
    if any(value == "unavailable" for value in values):
        return "unavailable"
    if values and all(value == "robust_positive" for value in values):
        return "robust_generalizing"
    return "not_robust_generalizing"


def certify_training_process_positive_pigeonhole_iut_v3(
    row_gain_by_refit: Sequence[Sequence[Sequence[float]]] | np.ndarray,
    groups: Sequence[object],
    *,
    blocks: Sequence[object],
    refit_ids: Sequence[object],
    training_process_id: object,
    training_process_manifest_sha256: object,
    contrast_names: Sequence[object] | None = None,
    sample_weight: Sequence[float] | None = None,
    component_lower_confidence_level: float = 0.95,
    bootstrap_draws: int = 4000,
    seed: int = 20261009,
    minimum_refits: int = 8,
    minimum_blocks_per_group: int = 8,
    gain_tolerance: float = 0.0,
) -> TrainingProcessPositivePigeonholeIUTAudit:
    """Test the compound process-mean claim using centered pigeonhole bootstrap."""

    process_id, process_sha = _process_identity(
        training_process_id, training_process_manifest_sha256
    )
    gain = np.asarray(row_gain_by_refit, dtype=float)
    if gain.ndim == 2:
        gain = gain[:, :, None]
    if gain.ndim != 3 or 0 in gain.shape:
        raise ValueError("row_gain_by_refit must be non-empty refit x row x contrast")
    if np.isnan(gain).any() or np.isposinf(gain).any():
        raise ValueError("row gains may contain finite values or -inf, but not NaN or +inf")

    refit_count, n, contrast_count = gain.shape
    ids, order = _refit_ids(refit_ids, refit_count)
    gain = gain[order]
    group = _labels(groups, n, name="groups")
    block = _labels(blocks, n, name="blocks")
    weight = _weights(sample_weight, n)
    bootstrap_draws = _integer(bootstrap_draws, name="bootstrap_draws", minimum=500)
    minimum_refits = _integer(minimum_refits, name="minimum_refits", minimum=2)
    minimum_blocks_per_group = _integer(
        minimum_blocks_per_group, name="minimum_blocks_per_group", minimum=2
    )
    seed = _integer(seed, name="seed", minimum=0)
    if (
        not math.isfinite(component_lower_confidence_level)
        or not 0 < component_lower_confidence_level < 1
    ):
        raise ValueError(
            "component_lower_confidence_level must lie strictly between zero and one"
        )
    if not math.isfinite(gain_tolerance) or gain_tolerance < 0:
        raise ValueError("gain_tolerance must be finite and non-negative")

    if contrast_names is None:
        names = tuple(f"contrast-{index:03d}" for index in range(contrast_count))
    else:
        if len(contrast_names) != contrast_count:
            raise ValueError("contrast_names must contain one name per contrast")
        names = tuple(str(value).strip() for value in contrast_names)
        if any(not value for value in names) or len(set(names)) != len(names):
            raise ValueError("contrast_names must be non-empty and unique")

    group_order = tuple(
        sorted(set(group.tolist()), key=lambda value: (type(value).__name__, repr(value)))
    )
    refit_draws = _shared_refit_draws_v3(seed, refit_count, bootstrap_draws)
    enough_refits = refit_count >= minimum_refits
    alpha_quantile = float(component_lower_confidence_level)

    records: list[list[dict[str, object]]] = [[] for _ in range(contrast_count)]

    for group_value in group_order:
        mask = group == group_value
        local_gain = gain[:, mask, :]
        local_weight = weight[mask]
        local_block = block[mask]
        positive = local_weight > 0
        if not np.any(positive):
            raise ValueError(f"group {group_value!r} has zero positive score weight")

        block_order = tuple(
            sorted(
                set(local_block[positive].tolist()),
                key=lambda value: (type(value).__name__, repr(value)),
            )
        )
        block_count = len(block_order)
        finite = np.all(np.isfinite(local_gain[:, positive, :]), axis=(0, 1))
        block_weight = np.empty(block_count, dtype=float)
        block_numerator = np.zeros(
            (refit_count, block_count, contrast_count), dtype=float
        )
        for block_index, block_value in enumerate(block_order):
            block_mask = (local_block == block_value) & positive
            mass = float(np.sum(local_weight[block_mask]))
            if mass <= 0:
                raise ValueError("every declared positive-support block must have positive mass")
            block_weight[block_index] = mass
            if np.any(finite):
                values = local_gain[:, block_mask, :][:, :, finite]
                block_numerator[:, block_index, finite] = np.sum(
                    values * local_weight[block_mask][None, :, None], axis=1
                )

        point = np.full(contrast_count, np.nan, dtype=float)
        critical = np.full(contrast_count, np.nan, dtype=float)
        lower = np.full(contrast_count, np.nan, dtype=float)
        if np.any(finite):
            denominator = float(refit_count) * float(np.sum(block_weight))
            point[finite] = np.sum(
                block_numerator[:, :, finite], axis=(0, 1)
            ) / denominator

            if enough_refits and block_count >= minimum_blocks_per_group:
                rng = np.random.default_rng(_stable_group_seed_v3(seed, group_value))
                block_draws = rng.integers(
                    0, block_count, size=(bootstrap_draws, block_count)
                )
                bootstrap_mean = _pigeonhole_bootstrap_means(
                    block_numerator[:, :, finite],
                    block_weight,
                    refit_draws,
                    block_draws,
                )
                displacement = bootstrap_mean - point[finite][None, :]
                critical[finite] = np.quantile(
                    displacement,
                    alpha_quantile,
                    axis=0,
                    method="higher",
                )
                lower[finite] = point[finite] - critical[finite]

        for contrast_index, contrast in enumerate(names):
            is_finite = bool(finite[contrast_index])
            estimable = bool(
                is_finite
                and enough_refits
                and block_count >= minimum_blocks_per_group
            )
            lo = float(lower[contrast_index]) if estimable else None
            records[contrast_index].append(
                {
                    "group": group_value,
                    "contrast": contrast,
                    "row_count": int(np.count_nonzero(mask)),
                    "block_count": block_count,
                    "total_weight": float(np.sum(local_weight[positive])),
                    "process_mean_gain": (
                        float(point[contrast_index]) if is_finite else None
                    ),
                    "bootstrap_displacement_critical_value": (
                        float(critical[contrast_index]) if estimable else None
                    ),
                    "lower_bound": lo,
                    "status": (
                        "robust_positive"
                        if estimable and lo is not None and lo > gain_tolerance
                        else "not_robust_positive"
                        if estimable
                        else "unavailable"
                    ),
                    "estimable": estimable,
                }
            )

    contrast_rows: list[TrainingProcessPigeonholeIUTContrast] = []
    estimable_cells = 0
    for contrast_index, contrast in enumerate(names):
        cells = tuple(
            TrainingProcessPigeonholeIUTCell(**record)
            for record in records[contrast_index]
        )
        statuses = [cell.status for cell in cells]
        estimable_cells += sum(cell.estimable for cell in cells)
        contrast_rows.append(
            TrainingProcessPigeonholeIUTContrast(
                contrast=contrast,
                category=_directional_category(statuses),
                robust_positive_group_count=statuses.count("robust_positive"),
                not_robust_positive_group_count=statuses.count("not_robust_positive"),
                unavailable_group_count=statuses.count("unavailable"),
                groups=cells,
            )
        )

    cell_count = len(group_order) * contrast_count
    return TrainingProcessPositivePigeonholeIUTAudit(
        schema_version=3,
        method_version="training_process_positive_pigeonhole_iut_v3",
        training_process_id=process_id,
        training_process_manifest_sha256=process_sha,
        inference_target=(
            "mean held-out directional gain over the frozen training-resampling "
            "process and declared validation population"
        ),
        refit_count=refit_count,
        refit_ids=ids,
        group_count=len(group_order),
        contrast_count=contrast_count,
        component_lower_confidence_level=float(component_lower_confidence_level),
        bootstrap_draws=bootstrap_draws,
        seed=seed,
        minimum_refits=minimum_refits,
        minimum_blocks_per_group=minimum_blocks_per_group,
        gain_tolerance=float(gain_tolerance),
        bootstrap_method="centered_pigeonhole_basic_one_sided_iut_v3",
        alternative="greater",
        compound_intersection_union_test=True,
        all_required_components_must_reject=True,
        additional_component_multiplicity_correction_applied=False,
        component_test_independence_assumed=False,
        component_lower_bounds_are_simultaneous=False,
        arbitrary_any_cell_familywise_claim_allowed=False,
        studentization_used=False,
        centered_bootstrap_displacement_used=True,
        quantile_method="higher",
        training_refit_draws_resampled_per_replicate=refit_count,
        same_refit_resample_shared_across_all_cells=True,
        same_validation_block_draw_shared_across_contrasts_within_group=True,
        validation_blocks_redrawn_per_refit=False,
        training_and_validation_axes_resampled_independently=True,
        refits_assumed_exchangeable_draws_from_frozen_process=True,
        process_mean_target=True,
        fixed_set_intersection_used=False,
        cell_count=cell_count,
        estimable_cell_count=int(estimable_cells),
        all_cells_estimable=bool(estimable_cells == cell_count),
        contrasts=tuple(contrast_rows),
    )


def certify_training_process_positive_information_pigeonhole_iut_v3(
    levels: Sequence[RefitInformationLevelScores],
    groups: Sequence[object],
    *,
    blocks: Sequence[object],
    refit_ids: Sequence[object],
    training_process_id: object,
    training_process_manifest_sha256: object,
    score_name: str = "log",
    sample_weight: Sequence[float] | None = None,
    component_lower_confidence_level: float = 0.95,
    bootstrap_draws: int = 4000,
    seed: int = 20261009,
    minimum_refits: int = 8,
    minimum_blocks_per_group: int = 8,
    gain_tolerance: float = 0.0,
) -> TrainingProcessPositivePigeonholeIUTInformationCertification:
    """Return the deepest non-skippable v3 process-mean IUT ceiling."""

    name = str(score_name).strip()
    if not name:
        raise ValueError("score_name must be non-empty")
    rows, matrices = _score_matrices(levels)
    refit_count, n = matrices[0].shape
    ids, order = _refit_ids(refit_ids, refit_count)
    matrices = tuple(matrix[order] for matrix in matrices)
    weight = _weights(sample_weight, n)
    positive = weight > 0
    for row, matrix in zip(rows[:-1], matrices[:-1]):
        if not np.isfinite(matrix[:, positive]).all():
            raise ValueError(
                f"comparator level {row.name!r} must be finite on every "
                "positive-weight row for every refit"
            )

    steps = validate_information_filtration(
        [InformationLevelScore(row.name, row.information, [0.0]) for row in rows]
    )
    gains = np.stack(
        [matrices[index + 1] - matrices[index] for index in range(len(steps))],
        axis=2,
    )
    audit = certify_training_process_positive_pigeonhole_iut_v3(
        gains,
        groups,
        blocks=blocks,
        refit_ids=ids,
        training_process_id=training_process_id,
        training_process_manifest_sha256=training_process_manifest_sha256,
        contrast_names=tuple(
            f"{step.lower_level}->{step.upper_level}" for step in steps
        ),
        sample_weight=weight,
        component_lower_confidence_level=component_lower_confidence_level,
        bootstrap_draws=bootstrap_draws,
        seed=seed,
        minimum_refits=minimum_refits,
        minimum_blocks_per_group=minimum_blocks_per_group,
        gain_tolerance=gain_tolerance,
    )

    ceiling = rows[0].name
    for index, summary in enumerate(audit.contrasts):
        if summary.category != "robust_generalizing":
            break
        ceiling = rows[index + 1].name

    process_id, process_sha = _process_identity(
        training_process_id, training_process_manifest_sha256
    )
    return TrainingProcessPositivePigeonholeIUTInformationCertification(
        schema_version=3,
        method_version="training_process_positive_pigeonhole_iut_v3",
        score_name=name,
        levels=tuple(row.name for row in rows),
        steps=steps,
        information_filtration_validated=True,
        training_process_id=process_id,
        training_process_manifest_sha256=process_sha,
        process_mean_certified_transfer_ceiling=ceiling,
        process_audit=audit,
        alternative="greater",
        upstream_training_uncertainty_included=True,
        validation_sample_uncertainty_included=True,
        compound_intersection_union_test=True,
        fixed_set_intersection_used=False,
        historical_fixed_set_results_reclassified=False,
    )
