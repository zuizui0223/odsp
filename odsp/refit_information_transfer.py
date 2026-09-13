"""Refit-aware familywise certification for information-transfer filtrations.

A fixed held-out score table quantifies validation-sample uncertainty conditional
on one fitted set of predictors. This module adds a second uncertainty source:
variation across an explicitly supplied ensemble of upstream refits.

Each nested Monte Carlo draw selects ONE refit index shared across every
independent group and every adjacent information step. Within each group it then
resamples caller-declared validation blocks, using the same block draw for all
information steps in that group. A single studentized max-t critical value is
formed over the full estimable group x information-step family.

ODSP still performs no fitting or model selection here. The supplied refits must
already be aligned to the same untouched validation rows and the same declared
information filtration.
"""
from __future__ import annotations

from dataclasses import asdict, dataclass
import hashlib
import math
from typing import Sequence

import numpy as np

from .information_transfer import (
    InformationLevelScore,
    InformationTransferCertification,
    InformationTransferStep,
    certify_information_transfer,
    decompose_information_transfer,
    validate_information_filtration,
)
from .predictive_resolution_certification import _cell_status, _step_category
from .transferability import classify_independent_gains


@dataclass(frozen=True)
class RefitInformationLevelScores:
    """One information level with an aligned [refit, held-out row] score matrix."""

    name: str
    information: tuple[str, ...]
    score: Sequence[Sequence[float]]

    def __post_init__(self) -> None:
        name = str(self.name).strip()
        if not name:
            raise ValueError("information-level name must be non-empty")
        information = tuple(str(value).strip() for value in self.information)
        if any(not value for value in information):
            raise ValueError("information labels must be non-empty")
        if len(set(information)) != len(information):
            raise ValueError(
                f"information labels must be unique within level {name!r}"
            )
        object.__setattr__(self, "name", name)
        object.__setattr__(self, "information", information)


@dataclass(frozen=True)
class RefitInformationTransferCell:
    """One independent-group x information-step refit-aware interval."""

    group: object
    lower_level: str
    upper_level: str
    row_count: int
    block_count: int
    total_weight: float
    ensemble_mean_gain: float | None
    reference_refit_gain: float | None
    refit_mean_gains: tuple[float, ...]
    positive_refit_count: int
    nonpositive_refit_count: int
    between_refit_standard_deviation: float | None
    nested_standard_error: float | None
    lower_bound: float | None
    upper_bound: float | None
    status: str
    estimable: bool

    def as_dict(self) -> dict[str, object]:
        return asdict(self)


@dataclass(frozen=True)
class RefitInformationTransferStepCertification:
    """All-group refit-aware status for one adjacent information step."""

    lower_level: str
    upper_level: str
    added_information: tuple[str, ...]
    ensemble_point_category: str
    refit_point_categories: tuple[str, ...]
    refit_category_stability: str
    refit_aware_category: str
    robust_positive_group_count: int
    robust_nonpositive_group_count: int
    uncertain_group_count: int
    unavailable_group_count: int
    groups: tuple[RefitInformationTransferCell, ...]

    def as_dict(self) -> dict[str, object]:
        payload = asdict(self)
        payload["added_information"] = list(self.added_information)
        payload["refit_point_categories"] = list(self.refit_point_categories)
        payload["groups"] = [row.as_dict() for row in self.groups]
        return payload


@dataclass(frozen=True)
class RefitInformationTransferCertification:
    """Joint validation-block and upstream-refit sensitivity certification."""

    score_name: str
    levels: tuple[str, ...]
    information_filtration_validated: bool
    refit_count: int
    refit_ids: tuple[str, ...]
    reference_refit_id: str
    familywise_confidence_level: float
    nested_draws: int
    seed: int
    minimum_refits: int
    minimum_blocks_per_group: int
    gain_tolerance: float
    max_t_critical_value: float | None
    cell_count: int
    estimable_cell_count: int
    all_cells_estimable: bool
    ensemble_point_transfer_ceiling: str
    reference_fit_point_transfer_ceiling: str
    reference_fit_certified_transfer_ceiling: str
    refit_point_transfer_ceilings: tuple[str, ...]
    refit_ceiling_stability: str
    refit_aware_certified_transfer_ceiling: str
    selected_refit_draw_counts: tuple[int, ...]
    same_selected_refit_shared_across_all_group_step_cells: bool
    same_block_draw_shared_across_steps_within_group: bool
    automatic_refit_scheme_inference: bool
    reference_fit_can_override_refit_aware_failure: bool
    total_gain_can_override_failed_step: bool
    aggregate_confidence_score_emitted: bool
    steps: tuple[RefitInformationTransferStepCertification, ...]
    reference_fit_certification: InformationTransferCertification

    def as_dict(self) -> dict[str, object]:
        return {
            "score_name": self.score_name,
            "levels": list(self.levels),
            "information_filtration_validated": self.information_filtration_validated,
            "refit_count": self.refit_count,
            "refit_ids": list(self.refit_ids),
            "reference_refit_id": self.reference_refit_id,
            "familywise_confidence_level": self.familywise_confidence_level,
            "nested_draws": self.nested_draws,
            "seed": self.seed,
            "minimum_refits": self.minimum_refits,
            "minimum_blocks_per_group": self.minimum_blocks_per_group,
            "gain_tolerance": self.gain_tolerance,
            "max_t_critical_value": self.max_t_critical_value,
            "cell_count": self.cell_count,
            "estimable_cell_count": self.estimable_cell_count,
            "all_cells_estimable": self.all_cells_estimable,
            "ensemble_point_transfer_ceiling": self.ensemble_point_transfer_ceiling,
            "reference_fit_point_transfer_ceiling": self.reference_fit_point_transfer_ceiling,
            "reference_fit_certified_transfer_ceiling": self.reference_fit_certified_transfer_ceiling,
            "refit_point_transfer_ceilings": list(self.refit_point_transfer_ceilings),
            "refit_ceiling_stability": self.refit_ceiling_stability,
            "refit_aware_certified_transfer_ceiling": self.refit_aware_certified_transfer_ceiling,
            "selected_refit_draw_counts": list(self.selected_refit_draw_counts),
            "same_selected_refit_shared_across_all_group_step_cells": self.same_selected_refit_shared_across_all_group_step_cells,
            "same_block_draw_shared_across_steps_within_group": self.same_block_draw_shared_across_steps_within_group,
            "automatic_refit_scheme_inference": self.automatic_refit_scheme_inference,
            "reference_fit_can_override_refit_aware_failure": self.reference_fit_can_override_refit_aware_failure,
            "total_gain_can_override_failed_step": self.total_gain_can_override_failed_step,
            "aggregate_confidence_score_emitted": self.aggregate_confidence_score_emitted,
            "steps": [row.as_dict() for row in self.steps],
            "reference_fit_certification": self.reference_fit_certification.as_dict(),
        }


def _integer(value: int, *, name: str, minimum: int) -> int:
    if isinstance(value, bool) or not isinstance(value, (int, np.integer)):
        raise ValueError(f"{name} must be an integer >= {minimum}")
    if int(value) < minimum:
        raise ValueError(f"{name} must be an integer >= {minimum}")
    return int(value)


def _labels(values: Sequence[object], n: int, *, name: str) -> np.ndarray:
    rows = np.asarray(list(values), dtype=object)
    if rows.shape != (n,):
        raise ValueError(f"{name} must contain one value per held-out row")
    for value in rows.tolist():
        if value is None:
            raise ValueError(f"{name} labels may not be missing")
        try:
            hash(value)
        except TypeError as exc:
            raise ValueError(f"{name} labels must be hashable") from exc
    return rows


def _weights(values: Sequence[float] | None, n: int) -> np.ndarray:
    if values is None:
        return np.ones(n, dtype=float)
    weight = np.asarray(values, dtype=float)
    if weight.shape != (n,):
        raise ValueError("sample_weight must contain one value per held-out row")
    if not np.isfinite(weight).all() or np.any(weight < 0) or not np.any(weight > 0):
        raise ValueError(
            "sample_weight must be finite, non-negative, aligned and positive in total"
        )
    return weight


def _stable_group_seed(seed: int, group: object) -> int:
    digest = hashlib.sha256(
        f"{seed}|refit-information-transfer|blocks|{group!r}".encode("utf-8")
    ).digest()
    return int.from_bytes(digest[:8], "little", signed=False)


def _shared_refit_draws(seed: int, refit_count: int, draws: int) -> np.ndarray:
    digest = hashlib.sha256(
        f"{seed}|refit-information-transfer|shared-refit".encode("utf-8")
    ).digest()
    local_seed = int.from_bytes(digest[:8], "little", signed=False)
    return np.random.default_rng(local_seed).integers(0, refit_count, size=draws)


def _score_matrices(
    levels: Sequence[RefitInformationLevelScores],
) -> tuple[tuple[RefitInformationLevelScores, ...], tuple[np.ndarray, ...]]:
    rows = tuple(levels)
    if len(rows) < 2:
        raise ValueError("information filtration must contain at least two levels")
    # Validate scientific nesting independently of the numeric refit matrices.
    validate_information_filtration(
        [
            InformationLevelScore(
                name=row.name,
                information=row.information,
                score=[0.0],
            )
            for row in rows
        ]
    )
    matrices: list[np.ndarray] = []
    shape: tuple[int, int] | None = None
    for index, row in enumerate(rows):
        matrix = np.asarray(row.score, dtype=float)
        if matrix.ndim != 2 or 0 in matrix.shape:
            raise ValueError(
                f"score matrix for level {row.name!r} must be non-empty [refit, row]"
            )
        if shape is None:
            shape = (int(matrix.shape[0]), int(matrix.shape[1]))
        elif matrix.shape != shape:
            raise ValueError("all information levels must share the same refit and row axes")
        if np.isnan(matrix).any() or np.isposinf(matrix).any():
            raise ValueError(
                f"score matrix for level {row.name!r} may contain finite values or -inf, but not NaN or +inf"
            )
        # Every level except the richest is a comparator and cannot have zero
        # predictive support on a scored row. Positive-weight filtering happens
        # later because zero-weight rows are permitted.
        matrices.append(matrix)
    return rows, tuple(matrices)


def _refit_ids(
    values: Sequence[object] | None,
    count: int,
) -> tuple[tuple[str, ...], np.ndarray]:
    if values is None:
        ids = tuple(f"refit-{index:09d}" for index in range(count))
    else:
        if len(values) != count:
            raise ValueError("refit_ids must contain one ID per refit")
        ids = tuple(str(value).strip() for value in values)
        if any(not value for value in ids):
            raise ValueError("refit_ids must be non-empty")
    if len(set(ids)) != count:
        raise ValueError("refit_ids must be unique")
    order = np.argsort(np.asarray(ids), kind="stable")
    return tuple(ids[int(index)] for index in order), order


def _ceiling(levels: tuple[str, ...], categories: Sequence[str], *, robust: bool) -> str:
    required = "robust_generalizing" if robust else "generalizing"
    ceiling = levels[0]
    for index, category in enumerate(categories):
        if category != required:
            break
        ceiling = levels[index + 1]
    return ceiling


def certify_refit_information_transfer(
    levels: Sequence[RefitInformationLevelScores],
    groups: Sequence[object],
    *,
    blocks: Sequence[object],
    refit_ids: Sequence[object] | None = None,
    reference_refit_id: object | None = None,
    score_name: str = "log",
    sample_weight: Sequence[float] | None = None,
    familywise_confidence_level: float = 0.95,
    nested_draws: int = 4000,
    seed: int = 20260913,
    minimum_refits: int = 8,
    minimum_blocks_per_group: int = 8,
    gain_tolerance: float = 0.0,
) -> RefitInformationTransferCertification:
    """Certify an information-transfer ceiling under refit and block uncertainty.

    The supplied score matrices must be aligned as ``[refit, held-out row]`` at
    every information level. One selected refit is shared across the full
    group-by-step family in each Monte Carlo draw. Validation blocks are sampled
    independently between groups but the same block indices are shared across all
    information steps within a group.

    This estimates sensitivity to the empirical supplied refit ensemble. It does
    not infer a refit scheme or turn dependent refits into independent samples.
    """

    name = str(score_name).strip()
    if not name:
        raise ValueError("score_name must be non-empty")
    rows, matrices = _score_matrices(levels)
    refit_count, n = matrices[0].shape
    nested_draws = _integer(nested_draws, name="nested_draws", minimum=500)
    minimum_refits = _integer(minimum_refits, name="minimum_refits", minimum=2)
    minimum_blocks_per_group = _integer(
        minimum_blocks_per_group,
        name="minimum_blocks_per_group",
        minimum=2,
    )
    seed = _integer(seed, name="seed", minimum=0)
    if not math.isfinite(familywise_confidence_level) or not 0 < familywise_confidence_level < 1:
        raise ValueError(
            "familywise_confidence_level must lie strictly between zero and one"
        )
    if not math.isfinite(gain_tolerance) or gain_tolerance < 0:
        raise ValueError("gain_tolerance must be finite and non-negative")

    group = _labels(groups, n, name="groups")
    block = _labels(blocks, n, name="blocks")
    weight = _weights(sample_weight, n)
    ids, refit_order = _refit_ids(refit_ids, refit_count)
    matrices = tuple(matrix[refit_order] for matrix in matrices)
    reference_id = ids[0] if reference_refit_id is None else str(reference_refit_id).strip()
    if reference_id not in ids:
        raise ValueError("reference_refit_id must identify one supplied refit")
    reference_index = ids.index(reference_id)

    positive = weight > 0
    for row, matrix in zip(rows[:-1], matrices[:-1]):
        if not np.isfinite(matrix[:, positive]).all():
            raise ValueError(
                f"comparator level {row.name!r} must be finite on every positive-weight row for every refit"
            )

    step_defs: tuple[InformationTransferStep, ...] = validate_information_filtration(
        [
            InformationLevelScore(
                name=row.name,
                information=row.information,
                score=[0.0],
            )
            for row in rows
        ]
    )
    level_names = tuple(row.name for row in rows)
    step_count = len(step_defs)
    gains = np.stack(
        [matrices[index + 1] - matrices[index] for index in range(step_count)],
        axis=1,
    )  # [refit, step, row]

    # Point ceilings for each supplied refit establish refit sensitivity without
    # averaging the models into a synthetic predictor.
    refit_point_ceilings: list[str] = []
    refit_step_categories: list[list[str]] = [[] for _ in range(step_count)]
    for refit_index in range(refit_count):
        point = decompose_information_transfer(
            [
                InformationLevelScore(
                    name=row.name,
                    information=row.information,
                    score=matrices[level_index][refit_index],
                )
                for level_index, row in enumerate(rows)
            ],
            group,
            score_name=name,
            sample_weight=weight,
            gain_tolerance=gain_tolerance,
        )
        predictive = point.predictive_result
        refit_point_ceilings.append(predictive.all_group_point_transfer_ceiling)
        for step_index, (_, _, category) in enumerate(
            predictive.increment_categories
        ):
            refit_step_categories[step_index].append(category)

    reference_levels = [
        InformationLevelScore(
            name=row.name,
            information=row.information,
            score=matrices[level_index][reference_index],
        )
        for level_index, row in enumerate(rows)
    ]
    reference_point = decompose_information_transfer(
        reference_levels,
        group,
        score_name=name,
        sample_weight=weight,
        gain_tolerance=gain_tolerance,
    )
    reference_certification = certify_information_transfer(
        reference_levels,
        group,
        score_name=name,
        blocks=block,
        sample_weight=weight,
        familywise_confidence_level=familywise_confidence_level,
        bootstrap_draws=nested_draws,
        seed=seed,
        minimum_blocks_per_group=minimum_blocks_per_group,
        gain_tolerance=gain_tolerance,
    )

    selected_refits = _shared_refit_draws(seed, refit_count, nested_draws)
    enough_refits = refit_count >= minimum_refits
    group_order = tuple(dict.fromkeys(group.tolist()))

    records: list[list[dict[str, object]]] = [
        [] for _ in range(step_count)
    ]
    eligible: list[tuple[int, int]] = []
    sample_columns: list[np.ndarray] = []
    sample_points: list[float] = []
    sample_ses: list[float] = []

    for group_value in group_order:
        mask = group == group_value
        local_weight = weight[mask]
        local_block = block[mask]
        if not float(np.sum(local_weight)) > 0:
            raise ValueError(f"group {group_value!r} has zero total score weight")
        ordered_blocks = tuple(sorted(set(local_block.tolist()), key=str))
        block_weights = np.empty(len(ordered_blocks), dtype=float)
        block_numerators = np.zeros(
            (refit_count, len(ordered_blocks), step_count), dtype=float
        )
        local_gain = gains[:, :, mask]
        local_positive = local_weight > 0
        finite_step = np.all(
            np.isfinite(local_gain[:, :, local_positive]), axis=(0, 2)
        )

        for block_index, block_value in enumerate(ordered_blocks):
            block_mask = local_block == block_value
            bw = float(np.sum(local_weight[block_mask]))
            if bw <= 0:
                raise ValueError("every declared resampling block must have positive total weight")
            block_weights[block_index] = bw
            if np.any(finite_step):
                weighted = (
                    local_gain[:, finite_step, :][:, :, block_mask]
                    * local_weight[block_mask][None, None, :]
                )
                block_numerators[:, block_index, finite_step] = np.sum(
                    weighted, axis=2
                )

        total_weight = float(np.sum(block_weights))
        refit_means = np.full((refit_count, step_count), np.nan, dtype=float)
        if np.any(finite_step):
            refit_means[:, finite_step] = (
                np.sum(block_numerators[:, :, finite_step], axis=1) / total_weight
            )

        rng = np.random.default_rng(_stable_group_seed(seed, group_value))
        sampled_blocks = rng.integers(
            0,
            len(ordered_blocks),
            size=(nested_draws, len(ordered_blocks)),
        )
        sampled_denominator = np.sum(block_weights[sampled_blocks], axis=1)

        for step_index, step in enumerate(step_defs):
            finite = bool(finite_step[step_index])
            means = (
                tuple(float(value) for value in refit_means[:, step_index])
                if finite
                else ()
            )
            ensemble_mean = float(np.mean(refit_means[:, step_index])) if finite else None
            reference_gain = (
                float(refit_means[reference_index, step_index]) if finite else None
            )
            estimable = bool(
                finite
                and enough_refits
                and len(ordered_blocks) >= minimum_blocks_per_group
            )
            record: dict[str, object] = {
                "group": group_value,
                "lower_level": step.lower_level,
                "upper_level": step.upper_level,
                "row_count": int(np.count_nonzero(mask)),
                "block_count": len(ordered_blocks),
                "total_weight": total_weight,
                "ensemble_mean_gain": ensemble_mean,
                "reference_refit_gain": reference_gain,
                "refit_mean_gains": means,
                "positive_refit_count": (
                    int(np.count_nonzero(refit_means[:, step_index] > gain_tolerance))
                    if finite
                    else 0
                ),
                "nonpositive_refit_count": (
                    int(refit_count - np.count_nonzero(refit_means[:, step_index] > gain_tolerance))
                    if finite
                    else 0
                ),
                "between_refit_standard_deviation": (
                    float(np.std(refit_means[:, step_index], ddof=0)) if finite else None
                ),
                "nested_standard_error": None,
                "lower_bound": None,
                "upper_bound": None,
                "status": "unavailable",
                "estimable": estimable,
            }
            record_index = len(records[step_index])
            records[step_index].append(record)
            if estimable:
                numerator = np.sum(
                    block_numerators[
                        selected_refits[:, None], sampled_blocks, step_index
                    ],
                    axis=1,
                )
                samples = numerator / sampled_denominator
                if not np.isfinite(samples).all():
                    raise ValueError("nested refit/block resampling produced non-finite gains")
                se = float(np.std(samples, ddof=1))
                record["nested_standard_error"] = se
                eligible.append((step_index, record_index))
                sample_columns.append(samples)
                sample_points.append(float(ensemble_mean))
                sample_ses.append(se)

    critical: float | None = None
    if sample_columns:
        sample_matrix = np.column_stack(sample_columns)
        points = np.asarray(sample_points, dtype=float)
        ses = np.asarray(sample_ses, dtype=float)
        standardized = np.zeros_like(sample_matrix)
        nonzero = ses > 1e-15
        standardized[:, nonzero] = (
            np.abs(sample_matrix[:, nonzero] - points[nonzero]) / ses[nonzero]
        )
        critical = float(
            np.quantile(
                np.max(standardized, axis=1),
                familywise_confidence_level,
            )
        )
        for column, (step_index, record_index) in enumerate(eligible):
            lower = float(points[column] - critical * ses[column])
            upper = float(points[column] + critical * ses[column])
            records[step_index][record_index]["lower_bound"] = lower
            records[step_index][record_index]["upper_bound"] = upper
            records[step_index][record_index]["status"] = _cell_status(
                lower,
                upper,
                tolerance=gain_tolerance,
            )

    step_rows: list[RefitInformationTransferStepCertification] = []
    refit_aware_categories: list[str] = []
    ensemble_categories: list[str] = []
    for step_index, step in enumerate(step_defs):
        cells = tuple(
            RefitInformationTransferCell(**record)
            for record in records[step_index]
        )
        statuses = [cell.status for cell in cells]
        refit_aware_category = _step_category(statuses)
        refit_aware_categories.append(refit_aware_category)
        finite_ensemble = [
            cell.ensemble_mean_gain
            for cell in cells
            if cell.ensemble_mean_gain is not None
        ]
        if len(finite_ensemble) != len(cells):
            ensemble_category = "unavailable"
        else:
            ensemble_category = classify_independent_gains(
                [float(value) for value in finite_ensemble],
                tolerance=gain_tolerance,
            )
        ensemble_categories.append(ensemble_category)
        per_refit = tuple(refit_step_categories[step_index])
        stability = "stable" if len(set(per_refit)) == 1 else "refit_sensitive"
        step_rows.append(
            RefitInformationTransferStepCertification(
                lower_level=step.lower_level,
                upper_level=step.upper_level,
                added_information=step.added_information,
                ensemble_point_category=ensemble_category,
                refit_point_categories=per_refit,
                refit_category_stability=stability,
                refit_aware_category=refit_aware_category,
                robust_positive_group_count=statuses.count("robust_positive"),
                robust_nonpositive_group_count=statuses.count("robust_nonpositive"),
                uncertain_group_count=statuses.count("uncertain"),
                unavailable_group_count=statuses.count("unavailable"),
                groups=cells,
            )
        )

    ensemble_ceiling = _ceiling(
        level_names,
        ensemble_categories,
        robust=False,
    )
    refit_aware_ceiling = _ceiling(
        level_names,
        refit_aware_categories,
        robust=True,
    )
    refit_ceiling_tuple = tuple(refit_point_ceilings)
    refit_ceiling_stability = (
        "stable" if len(set(refit_ceiling_tuple)) == 1 else "refit_sensitive"
    )
    cell_count = len(group_order) * step_count
    estimable_cell_count = len(eligible)

    return RefitInformationTransferCertification(
        score_name=name,
        levels=level_names,
        information_filtration_validated=True,
        refit_count=refit_count,
        refit_ids=ids,
        reference_refit_id=reference_id,
        familywise_confidence_level=float(familywise_confidence_level),
        nested_draws=nested_draws,
        seed=seed,
        minimum_refits=minimum_refits,
        minimum_blocks_per_group=minimum_blocks_per_group,
        gain_tolerance=float(gain_tolerance),
        max_t_critical_value=critical,
        cell_count=cell_count,
        estimable_cell_count=estimable_cell_count,
        all_cells_estimable=bool(estimable_cell_count == cell_count),
        ensemble_point_transfer_ceiling=ensemble_ceiling,
        reference_fit_point_transfer_ceiling=(
            reference_point.predictive_result.all_group_point_transfer_ceiling
        ),
        reference_fit_certified_transfer_ceiling=(
            reference_certification.certification.certified_transfer_ceiling
        ),
        refit_point_transfer_ceilings=refit_ceiling_tuple,
        refit_ceiling_stability=refit_ceiling_stability,
        refit_aware_certified_transfer_ceiling=refit_aware_ceiling,
        selected_refit_draw_counts=tuple(
            int(value)
            for value in np.bincount(selected_refits, minlength=refit_count)
        ) if enough_refits else (),
        same_selected_refit_shared_across_all_group_step_cells=True,
        same_block_draw_shared_across_steps_within_group=True,
        automatic_refit_scheme_inference=False,
        reference_fit_can_override_refit_aware_failure=False,
        total_gain_can_override_failed_step=False,
        aggregate_confidence_score_emitted=False,
        steps=tuple(step_rows),
        reference_fit_certification=reference_certification,
    )
