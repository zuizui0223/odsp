"""Directional transfer inference over a predeclared training-resampling process.

This module is intentionally separate from fixed-set all-refit robustness.
Its estimand is the mean held-out gain for a refit drawn from one frozen
training-resampling process, averaged over the validation population.

Every bootstrap replicate resamples R upstream refit draws with replacement and,
independently, resamples validation blocks once per validation group. The same
refit resample is shared across every group and contrast. Within a validation
group the same block resample is shared across contrasts and across refits.
Validation blocks are never redrawn separately for each refit.

This numeric core cannot prove that supplied refits are exchangeable draws from
the declared process. A prospective process-manifest and provenance layer must
establish that condition before confirmatory use.
"""
from __future__ import annotations

from dataclasses import asdict, dataclass
import hashlib
import math
import re
from typing import Sequence

import numpy as np

from .information_transfer import (
    InformationLevelScore,
    InformationTransferStep,
    validate_information_filtration,
)
from .positive_transfer_bootstrap_t import (
    _stable_group_seed,
    one_sided_lower_bounds,
    one_sided_lower_max_t_critical_value,
)
from .refit_information_transfer import (
    RefitInformationLevelScores,
    _integer,
    _labels,
    _refit_ids,
    _score_matrices,
    _weights,
)


_SHA256_RE = re.compile(r"^[0-9a-f]{64}$")


@dataclass(frozen=True)
class TrainingProcessPositiveTransferCell:
    group: object
    contrast: str
    row_count: int
    block_count: int
    total_weight: float
    process_mean_gain: float | None
    training_process_standard_error: float | None
    validation_block_standard_error: float | None
    intersection_cell_standard_error: float | None
    crossed_studentizing_standard_error: float | None
    studentizer_variance_source: str | None
    lower_bound: float | None
    status: str
    estimable: bool

    def as_dict(self) -> dict[str, object]:
        return asdict(self)


@dataclass(frozen=True)
class TrainingProcessPositiveTransferContrast:
    contrast: str
    category: str
    robust_positive_group_count: int
    not_robust_positive_group_count: int
    unavailable_group_count: int
    groups: tuple[TrainingProcessPositiveTransferCell, ...]

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
class TrainingProcessPositiveTransferAudit:
    schema_version: int
    training_process_id: str
    training_process_manifest_sha256: str
    inference_target: str
    refit_count: int
    refit_ids: tuple[str, ...]
    group_count: int
    contrast_count: int
    familywise_lower_confidence_level: float
    bootstrap_draws: int
    seed: int
    minimum_refits: int
    minimum_blocks_per_group: int
    gain_tolerance: float
    bootstrap_t_critical_value: float | None
    bootstrap_t_method: str
    alternative: str
    training_refit_draws_resampled_per_replicate: int
    same_refit_resample_shared_across_all_cells: bool
    same_validation_block_draw_shared_across_contrasts_within_group: bool
    validation_blocks_redrawn_per_refit: bool
    training_and_validation_axes_resampled_independently: bool
    refits_assumed_exchangeable_draws_from_frozen_process: bool
    fixed_set_intersection_used: bool
    process_mean_target: bool
    individual_future_refit_success_probability_claimed: bool
    all_possible_refits_positive_claimed: bool
    crossed_interaction_retained_in_bootstrap_distribution: bool
    crossed_interaction_separately_identified_in_studentizer: bool
    multiway_inclusion_exclusion_studentizer: bool
    max_one_way_variance_safeguard: bool
    cell_count: int
    estimable_cell_count: int
    all_cells_estimable: bool
    contrasts: tuple[TrainingProcessPositiveTransferContrast, ...]

    def as_dict(self) -> dict[str, object]:
        payload = asdict(self)
        payload["refit_ids"] = list(self.refit_ids)
        payload["contrasts"] = [row.as_dict() for row in self.contrasts]
        return payload


@dataclass(frozen=True)
class TrainingProcessPositiveInformationTransferCertification:
    schema_version: int
    score_name: str
    levels: tuple[str, ...]
    steps: tuple[InformationTransferStep, ...]
    information_filtration_validated: bool
    training_process_id: str
    training_process_manifest_sha256: str
    process_mean_certified_transfer_ceiling: str
    process_audit: TrainingProcessPositiveTransferAudit
    alternative: str
    upstream_training_uncertainty_included: bool
    validation_sample_uncertainty_included: bool
    fixed_set_intersection_used: bool
    historical_fixed_set_results_reclassified: bool

    def as_dict(self) -> dict[str, object]:
        return {
            "schema_version": self.schema_version,
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
            "fixed_set_intersection_used": self.fixed_set_intersection_used,
            "historical_fixed_set_results_reclassified": self.historical_fixed_set_results_reclassified,
        }


def _process_identity(process_id: object, manifest_sha256: object) -> tuple[str, str]:
    name = str(process_id).strip()
    if not name:
        raise ValueError("training_process_id must be non-empty")
    digest = str(manifest_sha256).strip().lower()
    if not _SHA256_RE.fullmatch(digest):
        raise ValueError(
            "training_process_manifest_sha256 must be a lowercase SHA256 hex digest"
        )
    return name, digest


def _shared_process_refit_draws(
    seed: int,
    refit_count: int,
    draws: int,
) -> np.ndarray:
    digest = hashlib.sha256(
        f"{seed}|training-process-positive-v1|refits".encode("utf-8")
    ).digest()
    local_seed = int.from_bytes(digest[:8], "little", signed=False)
    return np.random.default_rng(local_seed).integers(
        0,
        refit_count,
        size=(draws, refit_count),
    )


def _directional_category(statuses: Sequence[str]) -> str:
    values = tuple(statuses)
    if any(value == "unavailable" for value in values):
        return "unavailable"
    if values and all(value == "robust_positive" for value in values):
        return "robust_generalizing"
    return "not_robust_generalizing"


def _crossed_components(
    block_numerator: np.ndarray,
    block_weight: np.ndarray,
) -> tuple[
    np.ndarray,
    np.ndarray,
    np.ndarray,
    np.ndarray,
    np.ndarray,
    tuple[str, ...],
]:
    """Return the process mean and two-way cluster-robust components.

    The ratio influence residual for refit r and validation block b is
    N_rb - mean * W_b. The variance uses the two-way inclusion-exclusion
    construction: refit clustering plus validation-block clustering minus the
    refit-by-block intersection term.

    In finite samples the raw inclusion-exclusion variance can fall below a
    one-way component. The final scalar variance is therefore the maximum of
    the raw two-way variance and the two one-way variances. This fail-closed
    safeguard prevents a second uncertainty axis from making the reported
    standard error smaller.
    """

    numerator = np.asarray(block_numerator, dtype=float)
    weight = np.asarray(block_weight, dtype=float)
    if numerator.ndim != 3:
        raise ValueError("block_numerator must be refit x block x contrast")
    refit_count, block_count, contrast_count = numerator.shape
    if refit_count < 2 or block_count < 2 or contrast_count < 1:
        raise ValueError(
            "crossed studentization requires at least two refits and two blocks"
        )
    if weight.shape != (block_count,):
        raise ValueError("block_weight must contain one value per block")
    if not np.isfinite(numerator).all():
        raise ValueError("block_numerator must be finite")
    if not np.isfinite(weight).all() or np.any(weight <= 0):
        raise ValueError("block_weight must be finite and strictly positive")

    block_mass = float(np.sum(weight))
    denominator = float(refit_count) * block_mass
    mean = np.sum(numerator, axis=(0, 1)) / denominator
    residual = numerator - weight[None, :, None] * mean[None, None, :]

    refit_cluster = np.sum(residual, axis=1)
    refit_variance = (
        float(refit_count) / float(refit_count - 1)
    ) * np.sum(refit_cluster * refit_cluster, axis=0) / (denominator ** 2)

    block_cluster = np.sum(residual, axis=0)
    block_variance = (
        float(block_count) / float(block_count - 1)
    ) * np.sum(block_cluster * block_cluster, axis=0) / (denominator ** 2)

    cell_count = refit_count * block_count
    cell_variance = (
        float(cell_count) / float(cell_count - 1)
    ) * np.sum(residual * residual, axis=(0, 1)) / (denominator ** 2)

    raw_two_way = refit_variance + block_variance - cell_variance
    safe_variance = np.maximum.reduce(
        [
            raw_two_way,
            refit_variance,
            block_variance,
            np.zeros(contrast_count, dtype=float),
        ]
    )

    sources: list[str] = []
    for index in range(contrast_count):
        if (
            raw_two_way[index] >= refit_variance[index]
            and raw_two_way[index] >= block_variance[index]
            and raw_two_way[index] >= 0.0
        ):
            sources.append("two_way_inclusion_exclusion")
        elif refit_variance[index] >= block_variance[index]:
            sources.append("training_one_way_safeguard")
        else:
            sources.append("validation_one_way_safeguard")

    return (
        mean.astype(float),
        np.sqrt(np.maximum(refit_variance, 0.0)),
        np.sqrt(np.maximum(block_variance, 0.0)),
        np.sqrt(np.maximum(cell_variance, 0.0)),
        np.sqrt(np.maximum(safe_variance, 0.0)),
        tuple(sources),
    )


def _bootstrap_components(
    block_numerator: np.ndarray,
    block_weight: np.ndarray,
    refit_draws: np.ndarray,
    block_draws: np.ndarray,
) -> tuple[np.ndarray, np.ndarray]:
    """Cross-resample process refits and validation blocks with shared axes."""

    draws, _ = refit_draws.shape
    contrast_count = block_numerator.shape[2]
    means = np.empty((draws, contrast_count), dtype=float)
    ses = np.empty((draws, contrast_count), dtype=float)

    for draw_index in range(draws):
        refit_index = refit_draws[draw_index]
        block_index = block_draws[draw_index]
        local_weight = block_weight[block_index]
        local_numerator = block_numerator[refit_index][:, block_index, :]
        mean, _, _, _, se, _ = _crossed_components(
            local_numerator,
            local_weight,
        )
        means[draw_index] = mean
        ses[draw_index] = se

    return means, ses


def certify_training_process_positive_transfer_v1(
    row_gain_by_refit: Sequence[Sequence[Sequence[float]]] | np.ndarray,
    groups: Sequence[object],
    *,
    blocks: Sequence[object],
    refit_ids: Sequence[object],
    training_process_id: object,
    training_process_manifest_sha256: object,
    contrast_names: Sequence[object] | None = None,
    sample_weight: Sequence[float] | None = None,
    familywise_lower_confidence_level: float = 0.95,
    bootstrap_draws: int = 4000,
    seed: int = 20261004,
    minimum_refits: int = 8,
    minimum_blocks_per_group: int = 8,
    gain_tolerance: float = 0.0,
) -> TrainingProcessPositiveTransferAudit:
    """Audit positive process-mean gains over crossed training/validation axes."""

    process_id, process_sha = _process_identity(
        training_process_id,
        training_process_manifest_sha256,
    )
    gain = np.asarray(row_gain_by_refit, dtype=float)
    if gain.ndim == 2:
        gain = gain[:, :, None]
    if gain.ndim != 3 or 0 in gain.shape:
        raise ValueError(
            "row_gain_by_refit must be non-empty refit x row x contrast"
        )
    if np.isnan(gain).any() or np.isposinf(gain).any():
        raise ValueError(
            "row gains may contain finite values or -inf, but not NaN or +inf"
        )

    refit_count, n, contrast_count = gain.shape
    ids, order = _refit_ids(refit_ids, refit_count)
    gain = gain[order]
    group = _labels(groups, n, name="groups")
    block = _labels(blocks, n, name="blocks")
    weight = _weights(sample_weight, n)

    bootstrap_draws = _integer(
        bootstrap_draws,
        name="bootstrap_draws",
        minimum=500,
    )
    minimum_refits = _integer(
        minimum_refits,
        name="minimum_refits",
        minimum=2,
    )
    minimum_blocks_per_group = _integer(
        minimum_blocks_per_group,
        name="minimum_blocks_per_group",
        minimum=2,
    )
    seed = _integer(seed, name="seed", minimum=0)
    if (
        not math.isfinite(familywise_lower_confidence_level)
        or not 0 < familywise_lower_confidence_level < 1
    ):
        raise ValueError(
            "familywise_lower_confidence_level must lie strictly between zero and one"
        )
    if not math.isfinite(gain_tolerance) or gain_tolerance < 0:
        raise ValueError("gain_tolerance must be finite and non-negative")

    if contrast_names is None:
        names = tuple(f"contrast-{i:03d}" for i in range(contrast_count))
    else:
        if len(contrast_names) != contrast_count:
            raise ValueError("contrast_names must contain one name per contrast")
        names = tuple(str(value).strip() for value in contrast_names)
        if any(not value for value in names) or len(set(names)) != len(names):
            raise ValueError("contrast_names must be non-empty and unique")

    group_order = tuple(
        sorted(
            set(group.tolist()),
            key=lambda value: (type(value).__name__, repr(value)),
        )
    )
    refit_draws = _shared_process_refit_draws(
        seed,
        refit_count,
        bootstrap_draws,
    )
    enough_refits = refit_count >= minimum_refits

    records: list[list[dict[str, object]]] = [
        [] for _ in range(contrast_count)
    ]
    eligible: list[tuple[int, int]] = []
    sample_mean_columns: list[np.ndarray] = []
    sample_se_columns: list[np.ndarray] = []
    point_means: list[float] = []
    point_ses: list[float] = []

    for group_value in group_order:
        mask = group == group_value
        local_gain = gain[:, mask, :]
        local_weight = weight[mask]
        local_block = block[mask]
        positive = local_weight > 0
        if not np.any(positive):
            raise ValueError(
                f"group {group_value!r} has zero positive score weight"
            )

        block_order = tuple(
            sorted(
                set(local_block[positive].tolist()),
                key=lambda value: (type(value).__name__, repr(value)),
            )
        )
        block_count = len(block_order)
        finite = np.all(
            np.isfinite(local_gain[:, positive, :]),
            axis=(0, 1),
        )
        block_weight = np.empty(block_count, dtype=float)
        block_numerator = np.zeros(
            (refit_count, block_count, contrast_count),
            dtype=float,
        )

        for block_index, block_value in enumerate(block_order):
            block_mask = (local_block == block_value) & positive
            mass = float(np.sum(local_weight[block_mask]))
            if mass <= 0:
                raise ValueError(
                    "every declared positive-support block must have positive mass"
                )
            block_weight[block_index] = mass
            if np.any(finite):
                values = local_gain[:, block_mask, :][:, :, finite]
                block_numerator[:, block_index, finite] = np.sum(
                    values
                    * local_weight[block_mask][None, :, None],
                    axis=1,
                )

        local_point = np.full(contrast_count, np.nan, dtype=float)
        local_training_se = np.full(contrast_count, np.nan, dtype=float)
        local_validation_se = np.full(contrast_count, np.nan, dtype=float)
        local_intersection_se = np.full(contrast_count, np.nan, dtype=float)
        local_crossed_se = np.full(contrast_count, np.nan, dtype=float)
        local_variance_source: list[str | None] = [None] * contrast_count
        finite_positions = np.flatnonzero(finite)
        sampled_means = None
        sampled_ses = None

        if finite_positions.size:
            (
                point,
                train_se,
                valid_se,
                intersection_se,
                crossed_se,
                variance_sources,
            ) = _crossed_components(
                block_numerator[:, :, finite],
                block_weight,
            )
            local_point[finite] = point
            local_training_se[finite] = train_se
            local_validation_se[finite] = valid_se
            local_intersection_se[finite] = intersection_se
            local_crossed_se[finite] = crossed_se
            for local_index, contrast_index in enumerate(
                finite_positions.tolist()
            ):
                local_variance_source[int(contrast_index)] = (
                    variance_sources[local_index]
                )

            if enough_refits and block_count >= minimum_blocks_per_group:
                rng = np.random.default_rng(
                    _stable_group_seed(seed, group_value)
                )
                block_draws = rng.integers(
                    0,
                    block_count,
                    size=(bootstrap_draws, block_count),
                )
                sampled_means, sampled_ses = _bootstrap_components(
                    block_numerator[:, :, finite],
                    block_weight,
                    refit_draws,
                    block_draws,
                )

        finite_position_map = {
            int(contrast_index): local_index
            for local_index, contrast_index in enumerate(
                finite_positions.tolist()
            )
        }

        for contrast_index, contrast in enumerate(names):
            is_finite = bool(finite[contrast_index])
            estimable = bool(
                is_finite
                and enough_refits
                and block_count >= minimum_blocks_per_group
            )
            record: dict[str, object] = {
                "group": group_value,
                "contrast": contrast,
                "row_count": int(np.count_nonzero(mask)),
                "block_count": block_count,
                "total_weight": float(np.sum(local_weight[positive])),
                "process_mean_gain": (
                    float(local_point[contrast_index])
                    if is_finite
                    else None
                ),
                "training_process_standard_error": (
                    float(local_training_se[contrast_index])
                    if is_finite
                    else None
                ),
                "validation_block_standard_error": (
                    float(local_validation_se[contrast_index])
                    if is_finite
                    else None
                ),
                "intersection_cell_standard_error": (
                    float(local_intersection_se[contrast_index])
                    if is_finite
                    else None
                ),
                "crossed_studentizing_standard_error": (
                    float(local_crossed_se[contrast_index])
                    if is_finite
                    else None
                ),
                "studentizer_variance_source": (
                    local_variance_source[contrast_index]
                    if is_finite
                    else None
                ),
                "lower_bound": None,
                "status": "unavailable",
                "estimable": estimable,
            }
            record_index = len(records[contrast_index])
            records[contrast_index].append(record)
            if estimable:
                assert sampled_means is not None
                assert sampled_ses is not None
                local_index = finite_position_map[contrast_index]
                eligible.append((contrast_index, record_index))
                sample_mean_columns.append(
                    sampled_means[:, local_index]
                )
                sample_se_columns.append(
                    sampled_ses[:, local_index]
                )
                point_means.append(
                    float(local_point[contrast_index])
                )
                point_ses.append(
                    float(local_crossed_se[contrast_index])
                )

    critical: float | None = None
    if sample_mean_columns:
        bootstrap_mean = np.column_stack(sample_mean_columns)
        bootstrap_se = np.column_stack(sample_se_columns)
        point_mean = np.asarray(point_means, dtype=float)
        point_se = np.asarray(point_ses, dtype=float)

        critical = one_sided_lower_max_t_critical_value(
            bootstrap_mean,
            bootstrap_se,
            point_mean,
            confidence_level=familywise_lower_confidence_level,
        )
        lower = one_sided_lower_bounds(
            point_mean,
            point_se,
            critical,
        )
        for column, (contrast_index, record_index) in enumerate(eligible):
            lo = float(lower[column])
            records[contrast_index][record_index]["lower_bound"] = lo
            records[contrast_index][record_index]["status"] = (
                "robust_positive"
                if lo > gain_tolerance
                else "not_robust_positive"
            )

    contrast_rows: list[TrainingProcessPositiveTransferContrast] = []
    for contrast_index, contrast in enumerate(names):
        cells = tuple(
            TrainingProcessPositiveTransferCell(**record)
            for record in records[contrast_index]
        )
        statuses = [cell.status for cell in cells]
        contrast_rows.append(
            TrainingProcessPositiveTransferContrast(
                contrast=contrast,
                category=_directional_category(statuses),
                robust_positive_group_count=statuses.count(
                    "robust_positive"
                ),
                not_robust_positive_group_count=statuses.count(
                    "not_robust_positive"
                ),
                unavailable_group_count=statuses.count("unavailable"),
                groups=cells,
            )
        )

    cell_count = len(group_order) * contrast_count
    return TrainingProcessPositiveTransferAudit(
        schema_version=1,
        training_process_id=process_id,
        training_process_manifest_sha256=process_sha,
        inference_target=(
            "mean held-out directional gain over the frozen "
            "training-resampling process and validation population"
        ),
        refit_count=refit_count,
        refit_ids=ids,
        group_count=len(group_order),
        contrast_count=contrast_count,
        familywise_lower_confidence_level=float(
            familywise_lower_confidence_level
        ),
        bootstrap_draws=bootstrap_draws,
        seed=seed,
        minimum_refits=minimum_refits,
        minimum_blocks_per_group=minimum_blocks_per_group,
        gain_tolerance=float(gain_tolerance),
        bootstrap_t_critical_value=critical,
        bootstrap_t_method=(
            "one_sided_crossed_training_refit_validation_block_"
            "replicate_studentized_max_t_v1"
        ),
        alternative="greater",
        training_refit_draws_resampled_per_replicate=refit_count,
        same_refit_resample_shared_across_all_cells=True,
        same_validation_block_draw_shared_across_contrasts_within_group=True,
        validation_blocks_redrawn_per_refit=False,
        training_and_validation_axes_resampled_independently=True,
        refits_assumed_exchangeable_draws_from_frozen_process=True,
        fixed_set_intersection_used=False,
        process_mean_target=True,
        individual_future_refit_success_probability_claimed=False,
        all_possible_refits_positive_claimed=False,
        crossed_interaction_retained_in_bootstrap_distribution=True,
        crossed_interaction_separately_identified_in_studentizer=True,
        multiway_inclusion_exclusion_studentizer=True,
        max_one_way_variance_safeguard=True,
        cell_count=cell_count,
        estimable_cell_count=len(eligible),
        all_cells_estimable=bool(len(eligible) == cell_count),
        contrasts=tuple(contrast_rows),
    )


def certify_training_process_positive_information_transfer_v1(
    levels: Sequence[RefitInformationLevelScores],
    groups: Sequence[object],
    *,
    blocks: Sequence[object],
    refit_ids: Sequence[object],
    training_process_id: object,
    training_process_manifest_sha256: object,
    score_name: str = "log",
    sample_weight: Sequence[float] | None = None,
    familywise_lower_confidence_level: float = 0.95,
    bootstrap_draws: int = 4000,
    seed: int = 20261004,
    minimum_refits: int = 8,
    minimum_blocks_per_group: int = 8,
    gain_tolerance: float = 0.0,
) -> TrainingProcessPositiveInformationTransferCertification:
    """Certify a non-skippable process-mean information-transfer ceiling."""

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
        [
            InformationLevelScore(
                row.name,
                row.information,
                [0.0],
            )
            for row in rows
        ]
    )
    gains = np.stack(
        [
            matrices[index + 1] - matrices[index]
            for index in range(len(steps))
        ],
        axis=2,
    )
    contrast_names = tuple(
        f"{step.lower_level}->{step.upper_level}"
        for step in steps
    )
    audit = certify_training_process_positive_transfer_v1(
        gains,
        groups,
        blocks=blocks,
        refit_ids=ids,
        training_process_id=training_process_id,
        training_process_manifest_sha256=training_process_manifest_sha256,
        contrast_names=contrast_names,
        sample_weight=weight,
        familywise_lower_confidence_level=familywise_lower_confidence_level,
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
        training_process_id,
        training_process_manifest_sha256,
    )
    return TrainingProcessPositiveInformationTransferCertification(
        schema_version=1,
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
        fixed_set_intersection_used=False,
        historical_fixed_set_results_reclassified=False,
    )
