"""Directional training-process inference using an intersection-union test.

This v2 route targets a conjunction: every required group x information-step
process-mean gain must exceed the declared tolerance. For that global AND
alternative, the null is a union of component nulls. Therefore the global test
is an intersection-union test (IUT): each component is tested one-sided at
level alpha and the global claim passes only when every component rejects.

No additional multiplicity correction is required across the component axis for
that global conjunction. Consequently, the reported component lower bounds are
NOT simultaneous confidence bounds and must not be interpreted as such.

Within each component, uncertainty still crosses the frozen upstream
training-resampling process and the validation-block population. The crossed
bootstrap and conservative v1 two-way studentizer are retained unchanged.
"""
from __future__ import annotations

from dataclasses import asdict, dataclass
import math
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
from .training_process_positive_transfer import (
    _bootstrap_components,
    _crossed_components,
    _process_identity,
    _shared_process_refit_draws,
)


@dataclass(frozen=True)
class TrainingProcessIUTCell:
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
    cellwise_critical_value: float | None
    cellwise_lower_bound: float | None
    status: str
    estimable: bool

    def as_dict(self) -> dict[str, object]:
        return asdict(self)


@dataclass(frozen=True)
class TrainingProcessIUTContrast:
    contrast: str
    category: str
    robust_positive_group_count: int
    not_robust_positive_group_count: int
    unavailable_group_count: int
    groups: tuple[TrainingProcessIUTCell, ...]

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
class TrainingProcessIUTAudit:
    schema_version: int
    training_process_id: str
    training_process_manifest_sha256: str
    inference_target: str
    refit_count: int
    refit_ids: tuple[str, ...]
    group_count: int
    contrast_count: int
    cell_count: int
    estimable_cell_count: int
    all_cells_estimable: bool
    cellwise_lower_confidence_level: float
    global_intersection_union_alpha: float
    bootstrap_draws: int
    seed: int
    minimum_refits: int
    minimum_blocks_per_group: int
    gain_tolerance: float
    alternative: str
    composition_rule: str
    all_component_cells_must_reject: bool
    additional_component_axis_multiplicity_correction_applied: bool
    component_lower_bounds_are_simultaneous: bool
    component_lower_bounds_support_global_conjunction_only: bool
    training_refit_draws_resampled_per_replicate: int
    same_refit_resample_shared_across_all_cells: bool
    same_validation_block_draw_shared_across_contrasts_within_group: bool
    validation_blocks_redrawn_per_refit: bool
    training_and_validation_axes_resampled_independently: bool
    refits_assumed_exchangeable_draws_from_frozen_process: bool
    process_mean_target: bool
    fixed_set_intersection_used: bool
    individual_future_refit_success_probability_claimed: bool
    all_possible_refits_positive_claimed: bool
    crossed_interaction_retained_in_bootstrap_distribution: bool
    multiway_inclusion_exclusion_studentizer: bool
    max_one_way_variance_safeguard: bool
    global_category: str
    contrasts: tuple[TrainingProcessIUTContrast, ...]

    def as_dict(self) -> dict[str, object]:
        payload = asdict(self)
        payload["refit_ids"] = list(self.refit_ids)
        payload["contrasts"] = [row.as_dict() for row in self.contrasts]
        return payload


@dataclass(frozen=True)
class TrainingProcessIUTInformationTransferCertification:
    schema_version: int
    score_name: str
    levels: tuple[str, ...]
    steps: tuple[InformationTransferStep, ...]
    information_filtration_validated: bool
    training_process_id: str
    training_process_manifest_sha256: str
    process_mean_certified_transfer_ceiling: str
    process_audit: TrainingProcessIUTAudit
    alternative: str
    upstream_training_uncertainty_included: bool
    validation_sample_uncertainty_included: bool
    component_intersection_union_used: bool
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
            "component_intersection_union_used": self.component_intersection_union_used,
            "fixed_set_intersection_used": self.fixed_set_intersection_used,
            "historical_fixed_set_results_reclassified": self.historical_fixed_set_results_reclassified,
        }


def _category(statuses: Sequence[str]) -> str:
    values = tuple(statuses)
    if any(value == "unavailable" for value in values):
        return "unavailable"
    if values and all(value == "robust_positive" for value in values):
        return "robust_generalizing"
    return "not_robust_generalizing"


def _cellwise_lower(
    bootstrap_mean: np.ndarray,
    bootstrap_se: np.ndarray,
    point_mean: float,
    point_se: float,
    *,
    confidence_level: float,
) -> tuple[float, float]:
    critical = one_sided_lower_max_t_critical_value(
        np.asarray(bootstrap_mean, dtype=float)[:, None],
        np.asarray(bootstrap_se, dtype=float)[:, None],
        np.asarray([point_mean], dtype=float),
        confidence_level=confidence_level,
    )
    lower = one_sided_lower_bounds(
        np.asarray([point_mean], dtype=float),
        np.asarray([point_se], dtype=float),
        critical,
    )
    return float(critical), float(lower[0])


def certify_training_process_positive_transfer_v2(
    row_gain_by_refit: Sequence[Sequence[Sequence[float]]] | np.ndarray,
    groups: Sequence[object],
    *,
    blocks: Sequence[object],
    refit_ids: Sequence[object],
    training_process_id: object,
    training_process_manifest_sha256: object,
    contrast_names: Sequence[object] | None = None,
    sample_weight: Sequence[float] | None = None,
    cellwise_lower_confidence_level: float = 0.95,
    bootstrap_draws: int = 4000,
    seed: int = 20261012,
    minimum_refits: int = 8,
    minimum_blocks_per_group: int = 8,
    gain_tolerance: float = 0.0,
) -> TrainingProcessIUTAudit:
    """Test the all-cell positive process-mean conjunction by IUT."""

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
        bootstrap_draws, name="bootstrap_draws", minimum=500
    )
    minimum_refits = _integer(
        minimum_refits, name="minimum_refits", minimum=2
    )
    minimum_blocks_per_group = _integer(
        minimum_blocks_per_group,
        name="minimum_blocks_per_group",
        minimum=2,
    )
    seed = _integer(seed, name="seed", minimum=0)
    if (
        not math.isfinite(cellwise_lower_confidence_level)
        or not 0.0 < cellwise_lower_confidence_level < 1.0
    ):
        raise ValueError(
            "cellwise_lower_confidence_level must lie strictly between zero and one"
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
        sorted(
            set(group.tolist()),
            key=lambda value: (type(value).__name__, repr(value)),
        )
    )
    refit_draws = _shared_process_refit_draws(
        seed, refit_count, bootstrap_draws
    )
    enough_refits = refit_count >= minimum_refits
    records: list[list[dict[str, object]]] = [
        [] for _ in range(contrast_count)
    ]

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
            (refit_count, block_count, contrast_count), dtype=float
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

        local_point = np.full(contrast_count, np.nan)
        local_train_se = np.full(contrast_count, np.nan)
        local_valid_se = np.full(contrast_count, np.nan)
        local_intersection_se = np.full(contrast_count, np.nan)
        local_crossed_se = np.full(contrast_count, np.nan)
        local_source: list[str | None] = [None] * contrast_count
        local_bootstrap_mean: np.ndarray | None = None
        local_bootstrap_se: np.ndarray | None = None
        finite_positions = np.flatnonzero(finite)

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
            local_train_se[finite] = train_se
            local_valid_se[finite] = valid_se
            local_intersection_se[finite] = intersection_se
            local_crossed_se[finite] = crossed_se
            for local_index, contrast_index in enumerate(
                finite_positions.tolist()
            ):
                local_source[int(contrast_index)] = variance_sources[local_index]

            if enough_refits and block_count >= minimum_blocks_per_group:
                rng = np.random.default_rng(
                    _stable_group_seed(seed, group_value)
                )
                block_draws = rng.integers(
                    0, block_count, size=(bootstrap_draws, block_count)
                )
                local_bootstrap_mean, local_bootstrap_se = _bootstrap_components(
                    block_numerator[:, :, finite],
                    block_weight,
                    refit_draws,
                    block_draws,
                )

        finite_map = {
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
            critical = None
            lower = None
            status = "unavailable"
            if estimable:
                assert local_bootstrap_mean is not None
                assert local_bootstrap_se is not None
                local_index = finite_map[contrast_index]
                critical, lower = _cellwise_lower(
                    local_bootstrap_mean[:, local_index],
                    local_bootstrap_se[:, local_index],
                    float(local_point[contrast_index]),
                    float(local_crossed_se[contrast_index]),
                    confidence_level=cellwise_lower_confidence_level,
                )
                status = (
                    "robust_positive"
                    if lower > gain_tolerance
                    else "not_robust_positive"
                )
            records[contrast_index].append(
                {
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
                        float(local_train_se[contrast_index])
                        if is_finite
                        else None
                    ),
                    "validation_block_standard_error": (
                        float(local_valid_se[contrast_index])
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
                        local_source[contrast_index] if is_finite else None
                    ),
                    "cellwise_critical_value": critical,
                    "cellwise_lower_bound": lower,
                    "status": status,
                    "estimable": estimable,
                }
            )

    contrasts: list[TrainingProcessIUTContrast] = []
    for contrast_index, contrast in enumerate(names):
        cells = tuple(
            TrainingProcessIUTCell(**row)
            for row in records[contrast_index]
        )
        statuses = [cell.status for cell in cells]
        contrasts.append(
            TrainingProcessIUTContrast(
                contrast=contrast,
                category=_category(statuses),
                robust_positive_group_count=statuses.count("robust_positive"),
                not_robust_positive_group_count=statuses.count(
                    "not_robust_positive"
                ),
                unavailable_group_count=statuses.count("unavailable"),
                groups=cells,
            )
        )

    contrast_categories = tuple(row.category for row in contrasts)
    global_category = (
        "unavailable"
        if any(value == "unavailable" for value in contrast_categories)
        else "robust_generalizing"
        if contrast_categories
        and all(value == "robust_generalizing" for value in contrast_categories)
        else "not_robust_generalizing"
    )
    cell_count = len(group_order) * contrast_count
    estimable_count = sum(
        cell.estimable
        for contrast in contrasts
        for cell in contrast.groups
    )
    return TrainingProcessIUTAudit(
        schema_version=2,
        training_process_id=process_id,
        training_process_manifest_sha256=process_sha,
        inference_target=(
            "all required group x contrast process-mean held-out gains "
            "strictly exceed the declared tolerance"
        ),
        refit_count=refit_count,
        refit_ids=ids,
        group_count=len(group_order),
        contrast_count=contrast_count,
        cell_count=cell_count,
        estimable_cell_count=int(estimable_count),
        all_cells_estimable=bool(estimable_count == cell_count),
        cellwise_lower_confidence_level=float(
            cellwise_lower_confidence_level
        ),
        global_intersection_union_alpha=float(
            1.0 - cellwise_lower_confidence_level
        ),
        bootstrap_draws=bootstrap_draws,
        seed=seed,
        minimum_refits=minimum_refits,
        minimum_blocks_per_group=minimum_blocks_per_group,
        gain_tolerance=float(gain_tolerance),
        alternative="greater",
        composition_rule="intersection_union_all_component_cells_must_reject",
        all_component_cells_must_reject=True,
        additional_component_axis_multiplicity_correction_applied=False,
        component_lower_bounds_are_simultaneous=False,
        component_lower_bounds_support_global_conjunction_only=True,
        training_refit_draws_resampled_per_replicate=refit_count,
        same_refit_resample_shared_across_all_cells=True,
        same_validation_block_draw_shared_across_contrasts_within_group=True,
        validation_blocks_redrawn_per_refit=False,
        training_and_validation_axes_resampled_independently=True,
        refits_assumed_exchangeable_draws_from_frozen_process=True,
        process_mean_target=True,
        fixed_set_intersection_used=False,
        individual_future_refit_success_probability_claimed=False,
        all_possible_refits_positive_claimed=False,
        crossed_interaction_retained_in_bootstrap_distribution=True,
        multiway_inclusion_exclusion_studentizer=True,
        max_one_way_variance_safeguard=True,
        global_category=global_category,
        contrasts=tuple(contrasts),
    )


def certify_training_process_positive_information_transfer_v2(
    levels: Sequence[RefitInformationLevelScores],
    groups: Sequence[object],
    *,
    blocks: Sequence[object],
    refit_ids: Sequence[object],
    training_process_id: object,
    training_process_manifest_sha256: object,
    score_name: str = "log",
    sample_weight: Sequence[float] | None = None,
    cellwise_lower_confidence_level: float = 0.95,
    bootstrap_draws: int = 4000,
    seed: int = 20261012,
    minimum_refits: int = 8,
    minimum_blocks_per_group: int = 8,
    gain_tolerance: float = 0.0,
) -> TrainingProcessIUTInformationTransferCertification:
    """Certify a non-skippable process-mean filtration by component IUT."""

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
            InformationLevelScore(row.name, row.information, [0.0])
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
        f"{step.lower_level}->{step.upper_level}" for step in steps
    )
    audit = certify_training_process_positive_transfer_v2(
        gains,
        groups,
        blocks=blocks,
        refit_ids=ids,
        training_process_id=training_process_id,
        training_process_manifest_sha256=training_process_manifest_sha256,
        contrast_names=contrast_names,
        sample_weight=weight,
        cellwise_lower_confidence_level=cellwise_lower_confidence_level,
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
    return TrainingProcessIUTInformationTransferCertification(
        schema_version=2,
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
        component_intersection_union_used=True,
        fixed_set_intersection_used=False,
        historical_fixed_set_results_reclassified=False,
    )
