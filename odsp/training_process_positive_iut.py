"""Training-process positive transfer v2: component tests + intersection-union ceiling.

V1 used a simultaneous max-t lower bound over every group x information cell
and then required all cells to pass.  That controls the stronger question
"which individual cells may be called positive simultaneously", but it is not
necessary for the compound ODSP claim that *all required cells are positive*.

V2 keeps the crossed training-refit x validation-block resampling and two-way
studentizer unchanged.  It replaces the max-t composition with one level-alpha
one-sided bootstrap-t test per required cell.  A step, and therefore a reported
non-skippable ceiling, passes only when every required component rejects.

This is an intersection-union test (IUT): the null for the compound claim is the
union of component nulls.  If the compound null is true, at least one component
null is true, and falsely accepting the compound alternative requires rejecting
that true component null.  Therefore no additional multiplicity correction is
needed across components for the compound claim.  No independence among
component tests is assumed.

The component lower bounds are NOT simultaneous confidence bounds and may not
be used to make an arbitrary "any positive cell" familywise claim.
"""
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
from .training_process_positive_transfer import (
    _bootstrap_components,
    _crossed_components,
    _process_identity,
)


_EPS = 1e-15


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
    component_critical_value: float | None
    lower_bound: float | None
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
class TrainingProcessPositiveIUTAudit:
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
    bootstrap_t_method: str
    alternative: str
    compound_intersection_union_test: bool
    global_null_is_union_of_component_nulls: bool
    all_required_components_must_reject: bool
    additional_component_multiplicity_correction_applied: bool
    component_test_independence_assumed: bool
    component_lower_bounds_are_simultaneous: bool
    arbitrary_any_cell_familywise_claim_allowed: bool
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
    contrasts: tuple[TrainingProcessIUTContrast, ...]

    def as_dict(self) -> dict[str, object]:
        payload = asdict(self)
        payload["refit_ids"] = list(self.refit_ids)
        payload["contrasts"] = [row.as_dict() for row in self.contrasts]
        return payload


@dataclass(frozen=True)
class TrainingProcessPositiveIUTInformationCertification:
    schema_version: int
    method_version: str
    score_name: str
    levels: tuple[str, ...]
    steps: tuple[InformationTransferStep, ...]
    information_filtration_validated: bool
    training_process_id: str
    training_process_manifest_sha256: str
    process_mean_certified_transfer_ceiling: str
    process_audit: TrainingProcessPositiveIUTAudit
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


def _stable_group_seed_v2(seed: int, group: object) -> int:
    digest = hashlib.sha256(
        f"{seed}|training-process-positive-iut-v2|blocks|{group!r}".encode("utf-8")
    ).digest()
    return int.from_bytes(digest[:8], "little", signed=False)


def _shared_process_refit_draws_v2(seed: int, refit_count: int, draws: int) -> np.ndarray:
    digest = hashlib.sha256(
        f"{seed}|training-process-positive-iut-v2|refits".encode("utf-8")
    ).digest()
    local_seed = int.from_bytes(digest[:8], "little", signed=False)
    return np.random.default_rng(local_seed).integers(
        0, refit_count, size=(draws, refit_count)
    )


def _component_critical_values(
    bootstrap_mean: np.ndarray,
    bootstrap_se: np.ndarray,
    point_mean: np.ndarray,
    *,
    confidence_level: float,
) -> np.ndarray:
    means = np.asarray(bootstrap_mean, dtype=float)
    ses = np.asarray(bootstrap_se, dtype=float)
    point = np.asarray(point_mean, dtype=float)
    if means.ndim != 2 or ses.shape != means.shape:
        raise ValueError("bootstrap means and SEs must share draws x cells shape")
    if point.shape != (means.shape[1],):
        raise ValueError("point_mean must contain one value per component")
    if not np.isfinite(means).all() or not np.isfinite(ses).all() or np.any(ses < 0):
        raise ValueError("bootstrap means and SEs must be finite and SEs non-negative")
    if not np.isfinite(point).all():
        raise ValueError("point_mean must be finite")
    if not math.isfinite(confidence_level) or not 0 < confidence_level < 1:
        raise ValueError("confidence_level must lie strictly between zero and one")

    displacement = means - point[None, :]
    statistic = np.empty_like(displacement)
    positive = ses > _EPS
    statistic[positive] = displacement[positive] / ses[positive]
    stable = (~positive) & (np.abs(displacement) <= _EPS)
    moved_up = (~positive) & (displacement > _EPS)
    moved_down = (~positive) & (displacement < -_EPS)
    statistic[stable] = 0.0
    statistic[moved_up] = np.inf
    statistic[moved_down] = -np.inf
    critical = np.quantile(
        statistic,
        confidence_level,
        axis=0,
        method="higher",
    )
    return np.maximum(critical.astype(float), 0.0)


def _directional_category(statuses: Sequence[str]) -> str:
    values = tuple(statuses)
    if any(value == "unavailable" for value in values):
        return "unavailable"
    if values and all(value == "robust_positive" for value in values):
        return "robust_generalizing"
    return "not_robust_generalizing"


def certify_training_process_positive_iut_v2(
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
    seed: int = 20261007,
    minimum_refits: int = 8,
    minimum_blocks_per_group: int = 8,
    gain_tolerance: float = 0.0,
) -> TrainingProcessPositiveIUTAudit:
    """Test the compound positive process-mean claim by intersection-union."""

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
    refit_draws = _shared_process_refit_draws_v2(seed, refit_count, bootstrap_draws)
    enough_refits = refit_count >= minimum_refits

    records: list[list[dict[str, object]]] = [[] for _ in range(contrast_count)]
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
        block_numerator = np.zeros((refit_count, block_count, contrast_count), dtype=float)

        for block_index, block_value in enumerate(block_order):
            block_mask = (local_block == block_value) & positive
            mass = float(np.sum(local_weight[block_mask]))
            if mass <= 0:
                raise ValueError("every declared positive-support block must have positive mass")
            block_weight[block_index] = mass
            if np.any(finite):
                values = local_gain[:, block_mask, :][:, :, finite]
                block_numerator[:, block_index, finite] = np.sum(
                    values * local_weight[block_mask][None, :, None],
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
            ) = _crossed_components(block_numerator[:, :, finite], block_weight)
            local_point[finite] = point
            local_training_se[finite] = train_se
            local_validation_se[finite] = valid_se
            local_intersection_se[finite] = intersection_se
            local_crossed_se[finite] = crossed_se
            for local_index, contrast_index in enumerate(finite_positions.tolist()):
                local_variance_source[int(contrast_index)] = variance_sources[local_index]

            if enough_refits and block_count >= minimum_blocks_per_group:
                rng = np.random.default_rng(_stable_group_seed_v2(seed, group_value))
                block_draws = rng.integers(
                    0, block_count, size=(bootstrap_draws, block_count)
                )
                sampled_means, sampled_ses = _bootstrap_components(
                    block_numerator[:, :, finite],
                    block_weight,
                    refit_draws,
                    block_draws,
                )

        finite_position_map = {
            int(contrast_index): local_index
            for local_index, contrast_index in enumerate(finite_positions.tolist())
        }
        for contrast_index, contrast in enumerate(names):
            is_finite = bool(finite[contrast_index])
            estimable = bool(
                is_finite and enough_refits and block_count >= minimum_blocks_per_group
            )
            record: dict[str, object] = {
                "group": group_value,
                "contrast": contrast,
                "row_count": int(np.count_nonzero(mask)),
                "block_count": block_count,
                "total_weight": float(np.sum(local_weight[positive])),
                "process_mean_gain": float(local_point[contrast_index]) if is_finite else None,
                "training_process_standard_error": (
                    float(local_training_se[contrast_index]) if is_finite else None
                ),
                "validation_block_standard_error": (
                    float(local_validation_se[contrast_index]) if is_finite else None
                ),
                "intersection_cell_standard_error": (
                    float(local_intersection_se[contrast_index]) if is_finite else None
                ),
                "crossed_studentizing_standard_error": (
                    float(local_crossed_se[contrast_index]) if is_finite else None
                ),
                "studentizer_variance_source": (
                    local_variance_source[contrast_index] if is_finite else None
                ),
                "component_critical_value": None,
                "lower_bound": None,
                "status": "unavailable",
                "estimable": estimable,
            }
            record_index = len(records[contrast_index])
            records[contrast_index].append(record)
            if estimable:
                assert sampled_means is not None and sampled_ses is not None
                local_index = finite_position_map[contrast_index]
                eligible.append((contrast_index, record_index))
                sample_mean_columns.append(sampled_means[:, local_index])
                sample_se_columns.append(sampled_ses[:, local_index])
                point_means.append(float(local_point[contrast_index]))
                point_ses.append(float(local_crossed_se[contrast_index]))

    if sample_mean_columns:
        bootstrap_mean = np.column_stack(sample_mean_columns)
        bootstrap_se = np.column_stack(sample_se_columns)
        point_mean = np.asarray(point_means, dtype=float)
        point_se = np.asarray(point_ses, dtype=float)
        critical = _component_critical_values(
            bootstrap_mean,
            bootstrap_se,
            point_mean,
            confidence_level=component_lower_confidence_level,
        )
        lower = np.empty_like(point_mean)
        finite_critical = np.isfinite(critical)
        lower[finite_critical] = (
            point_mean[finite_critical]
            - critical[finite_critical] * point_se[finite_critical]
        )
        infinite_critical = ~finite_critical
        lower[infinite_critical] = -np.inf
        stable_infinite = infinite_critical & (point_se <= _EPS)
        lower[stable_infinite] = point_mean[stable_infinite]
        for column, (contrast_index, record_index) in enumerate(eligible):
            lo = float(lower[column])
            records[contrast_index][record_index]["component_critical_value"] = float(
                critical[column]
            )
            records[contrast_index][record_index]["lower_bound"] = lo
            records[contrast_index][record_index]["status"] = (
                "robust_positive" if lo > gain_tolerance else "not_robust_positive"
            )

    contrast_rows: list[TrainingProcessIUTContrast] = []
    for contrast_index, contrast in enumerate(names):
        cells = tuple(TrainingProcessIUTCell(**row) for row in records[contrast_index])
        statuses = [cell.status for cell in cells]
        contrast_rows.append(
            TrainingProcessIUTContrast(
                contrast=contrast,
                category=_directional_category(statuses),
                robust_positive_group_count=statuses.count("robust_positive"),
                not_robust_positive_group_count=statuses.count("not_robust_positive"),
                unavailable_group_count=statuses.count("unavailable"),
                groups=cells,
            )
        )

    cell_count = len(group_order) * contrast_count
    return TrainingProcessPositiveIUTAudit(
        schema_version=2,
        method_version="training_process_positive_iut_v2",
        training_process_id=process_id,
        training_process_manifest_sha256=process_sha,
        inference_target=(
            "compound claim that every required group x contrast process-mean "
            "held-out directional gain exceeds the declared tolerance"
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
        bootstrap_t_method=(
            "cellwise_one_sided_crossed_training_refit_validation_block_"
            "replicate_studentized_bootstrap_t_iut_v2"
        ),
        alternative="greater",
        compound_intersection_union_test=True,
        global_null_is_union_of_component_nulls=True,
        all_required_components_must_reject=True,
        additional_component_multiplicity_correction_applied=False,
        component_test_independence_assumed=False,
        component_lower_bounds_are_simultaneous=False,
        arbitrary_any_cell_familywise_claim_allowed=False,
        training_refit_draws_resampled_per_replicate=refit_count,
        same_refit_resample_shared_across_all_cells=True,
        same_validation_block_draw_shared_across_contrasts_within_group=True,
        validation_blocks_redrawn_per_refit=False,
        training_and_validation_axes_resampled_independently=True,
        refits_assumed_exchangeable_draws_from_frozen_process=True,
        process_mean_target=True,
        fixed_set_intersection_used=False,
        cell_count=cell_count,
        estimable_cell_count=len(eligible),
        all_cells_estimable=bool(len(eligible) == cell_count),
        contrasts=tuple(contrast_rows),
    )


def certify_training_process_positive_information_iut_v2(
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
    seed: int = 20261007,
    minimum_refits: int = 8,
    minimum_blocks_per_group: int = 8,
    gain_tolerance: float = 0.0,
) -> TrainingProcessPositiveIUTInformationCertification:
    """Return the deepest non-skippable process-mean IUT ceiling."""

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
    audit = certify_training_process_positive_iut_v2(
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
    return TrainingProcessPositiveIUTInformationCertification(
        schema_version=2,
        method_version="training_process_positive_iut_v2",
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
