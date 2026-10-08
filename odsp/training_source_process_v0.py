"""Experimental training-source process v0.

Target: E_source E_refit_given_source E_validation D.

Inner refits are nested within outer source-process draws. They are averaged
within source before outer inference, so R inner refits do not become R
independent source samples. The resulting source-draw by validation-block array
uses the same two-term CV3(2) scalar jackknife primitive as qualified v5, but
this new endpoint is not qualified merely by reusing that primitive.
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
from .refit_information_transfer import (
    RefitInformationLevelScores,
    _integer,
    _labels,
    _refit_ids,
    _score_matrices,
    _weights,
)
from .training_process_positive_cv3max_iut import _student_t_ppf
from .training_process_positive_cv3two_iut import _cv3two_components
from .training_process_positive_transfer import _process_identity


@dataclass(frozen=True)
class TrainingSourceProcessV0Cell:
    group: object
    contrast: str
    row_count: int
    block_count: int
    source_draw_count: int
    inner_refit_count_per_source: int
    total_weight: float
    source_process_mean_gain: float | None
    source_jackknife_variance: float | None
    validation_jackknife_variance: float | None
    cv3two_variance: float | None
    cv3two_standard_error: float | None
    t_degrees_of_freedom: int | None
    one_sided_t_critical_value: float | None
    lower_bound: float | None
    status: str
    estimable: bool

    def as_dict(self) -> dict[str, object]:
        return asdict(self)


@dataclass(frozen=True)
class TrainingSourceProcessV0Contrast:
    contrast: str
    category: str
    robust_positive_group_count: int
    not_robust_positive_group_count: int
    unavailable_group_count: int
    groups: tuple[TrainingSourceProcessV0Cell, ...]

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
class TrainingSourceProcessV0Audit:
    schema_version: int
    method_version: str
    qualification_status: str
    primary_confirmatory: bool
    source_process_id: str
    source_process_manifest_sha256: str
    inference_target: str
    source_draw_count: int
    source_draw_ids: tuple[str, ...]
    inner_refit_count_per_source: int
    group_count: int
    contrast_count: int
    component_one_sided_alpha: float
    minimum_source_draws: int
    minimum_inner_refits_per_source: int
    minimum_blocks_per_group: int
    gain_tolerance: float
    variance_method: str
    critical_value_method: str
    inner_refits_nested_within_source: bool
    inner_refits_pooled_as_independent_source_draws: bool
    source_draws_equally_weighted: bool
    effective_training_cluster_count: int
    compound_intersection_union_test: bool
    fixed_set_results_reclassified: bool
    qualified_v5_results_reclassified: bool
    original_source_superpopulation_generalization_claimed: bool
    cell_count: int
    estimable_cell_count: int
    all_cells_estimable: bool
    contrasts: tuple[TrainingSourceProcessV0Contrast, ...]

    def as_dict(self) -> dict[str, object]:
        payload = asdict(self)
        payload["source_draw_ids"] = list(self.source_draw_ids)
        payload["contrasts"] = [row.as_dict() for row in self.contrasts]
        return payload


@dataclass(frozen=True)
class TrainingSourceProcessV0InformationEvaluation:
    schema_version: int
    method_version: str
    qualification_status: str
    score_name: str
    levels: tuple[str, ...]
    steps: tuple[InformationTransferStep, ...]
    information_filtration_validated: bool
    source_process_mean_transfer_ceiling: str
    process_audit: TrainingSourceProcessV0Audit
    fixed_set_results_reclassified: bool
    qualified_v5_results_reclassified: bool

    def as_dict(self) -> dict[str, object]:
        return {
            "schema_version": self.schema_version,
            "method_version": self.method_version,
            "qualification_status": self.qualification_status,
            "score_name": self.score_name,
            "levels": list(self.levels),
            "steps": [row.as_dict() for row in self.steps],
            "information_filtration_validated": self.information_filtration_validated,
            "source_process_mean_transfer_ceiling": self.source_process_mean_transfer_ceiling,
            "process_audit": self.process_audit.as_dict(),
            "fixed_set_results_reclassified": self.fixed_set_results_reclassified,
            "qualified_v5_results_reclassified": self.qualified_v5_results_reclassified,
        }


def _nested_refit_ids(
    values: Sequence[Sequence[object]],
    *,
    source_count: int,
    inner_count: int,
) -> tuple[tuple[str, ...], ...]:
    if len(values) != source_count:
        raise ValueError("inner_refit_ids_by_source must contain one sequence per source")
    rows: list[tuple[str, ...]] = []
    for source_index, raw in enumerate(values):
        if len(raw) != inner_count:
            raise ValueError(
                "every source draw must contain the same frozen inner-refit count"
            )
        ids = tuple(str(x).strip() for x in raw)
        if any(not x for x in ids):
            raise ValueError("inner refit IDs must be non-empty")
        if len(set(ids)) != len(ids):
            raise ValueError(
                f"inner refit IDs must be unique within source draw {source_index}"
            )
        rows.append(ids)
    return tuple(rows)


def _category(statuses: Sequence[str]) -> str:
    vals = tuple(statuses)
    if any(x == "unavailable" for x in vals):
        return "unavailable"
    if vals and all(x == "robust_positive" for x in vals):
        return "robust_generalizing"
    return "not_robust_generalizing"


def evaluate_training_source_process_positive_iut_v0(
    row_gain_by_source_refit: np.ndarray | Sequence,
    groups: Sequence[object],
    *,
    blocks: Sequence[object],
    source_draw_ids: Sequence[object],
    inner_refit_ids_by_source: Sequence[Sequence[object]],
    source_process_id: object,
    source_process_manifest_sha256: object,
    contrast_names: Sequence[object] | None = None,
    sample_weight: Sequence[float] | None = None,
    component_one_sided_alpha: float = 0.05,
    minimum_source_draws: int = 8,
    minimum_inner_refits_per_source: int = 8,
    minimum_blocks_per_group: int = 8,
    gain_tolerance: float = 0.0,
) -> TrainingSourceProcessV0Audit:
    """Evaluate the frozen v0 candidate without granting confirmatory status."""

    process_id, process_sha = _process_identity(
        source_process_id, source_process_manifest_sha256
    )
    gain = np.asarray(row_gain_by_source_refit, dtype=float)
    if gain.ndim == 3:
        gain = gain[:, :, :, None]
    if gain.ndim != 4 or 0 in gain.shape:
        raise ValueError(
            "row_gain_by_source_refit must be non-empty source x inner_refit x row x contrast"
        )
    if np.isnan(gain).any() or np.isposinf(gain).any():
        raise ValueError("gains may contain finite values or -inf, but not NaN or +inf")

    source_count, inner_count, n, contrast_count = gain.shape
    source_ids, source_order = _refit_ids(source_draw_ids, source_count)
    gain = gain[source_order]
    nested_ids_raw = _nested_refit_ids(
        inner_refit_ids_by_source,
        source_count=source_count,
        inner_count=inner_count,
    )
    _ = tuple(nested_ids_raw[index] for index in source_order.tolist())

    group = _labels(groups, n, name="groups")
    block = _labels(blocks, n, name="blocks")
    weight = _weights(sample_weight, n)

    minimum_source_draws = _integer(
        minimum_source_draws, name="minimum_source_draws", minimum=2
    )
    minimum_inner_refits_per_source = _integer(
        minimum_inner_refits_per_source,
        name="minimum_inner_refits_per_source",
        minimum=2,
    )
    minimum_blocks_per_group = _integer(
        minimum_blocks_per_group, name="minimum_blocks_per_group", minimum=2
    )
    if not math.isfinite(component_one_sided_alpha) or not 0 < component_one_sided_alpha < 0.5:
        raise ValueError("component_one_sided_alpha must lie strictly between 0 and 0.5")
    if not math.isfinite(gain_tolerance) or gain_tolerance < 0:
        raise ValueError("gain_tolerance must be finite and non-negative")

    if contrast_names is None:
        names = tuple(f"contrast-{i:03d}" for i in range(contrast_count))
    else:
        if len(contrast_names) != contrast_count:
            raise ValueError("contrast_names must contain one name per contrast")
        names = tuple(str(x).strip() for x in contrast_names)
        if any(not x for x in names) or len(set(names)) != len(names):
            raise ValueError("contrast_names must be non-empty and unique")

    group_order = tuple(
        sorted(set(group.tolist()), key=lambda x: (type(x).__name__, repr(x)))
    )
    enough_sources = source_count >= minimum_source_draws
    enough_inner = inner_count >= minimum_inner_refits_per_source
    records: list[list[dict[str, object]]] = [[] for _ in range(contrast_count)]

    for group_value in group_order:
        mask = group == group_value
        local_gain = gain[:, :, mask, :]
        local_weight = weight[mask]
        local_block = block[mask]
        positive = local_weight > 0
        if not np.any(positive):
            raise ValueError(f"group {group_value!r} has zero positive score weight")

        block_order = tuple(
            sorted(
                set(local_block[positive].tolist()),
                key=lambda x: (type(x).__name__, repr(x)),
            )
        )
        block_count = len(block_order)
        finite = np.all(np.isfinite(local_gain[:, :, positive, :]), axis=(0, 1, 2))
        block_weight = np.empty(block_count, dtype=float)
        nested_block_numerator = np.zeros(
            (source_count, inner_count, block_count, contrast_count),
            dtype=float,
        )

        for block_index, block_value in enumerate(block_order):
            block_mask = (local_block == block_value) & positive
            mass = float(np.sum(local_weight[block_mask]))
            if mass <= 0:
                raise ValueError("every positive-support block must have positive mass")
            block_weight[block_index] = mass
            if np.any(finite):
                values = local_gain[:, :, block_mask, :][:, :, :, finite]
                nested_block_numerator[:, :, block_index, finite] = np.sum(
                    values * local_weight[block_mask][None, None, :, None],
                    axis=2,
                )

        point = np.full(contrast_count, np.nan)
        v_source = np.full(contrast_count, np.nan)
        v_validation = np.full(contrast_count, np.nan)
        v_two = np.full(contrast_count, np.nan)

        if np.any(finite):
            source_block_numerator = np.mean(
                nested_block_numerator[:, :, :, finite],
                axis=1,
            )
            p, vs, vv, vt = _cv3two_components(
                source_block_numerator,
                block_weight,
            )
            point[finite] = p
            v_source[finite] = vs
            v_validation[finite] = vv
            v_two[finite] = vt

        enough_blocks = block_count >= minimum_blocks_per_group
        estimable_axis = enough_sources and enough_inner and enough_blocks
        df = min(source_count, block_count) - 1
        critical = (
            _student_t_ppf(1.0 - component_one_sided_alpha, df)
            if estimable_axis
            else None
        )

        for contrast_index, contrast in enumerate(names):
            is_finite = bool(finite[contrast_index])
            estimable = bool(is_finite and estimable_axis)
            se = (
                float(math.sqrt(max(float(v_two[contrast_index]), 0.0)))
                if estimable
                else None
            )
            lower = (
                float(point[contrast_index] - float(critical) * se)
                if estimable and critical is not None and se is not None
                else None
            )
            records[contrast_index].append(
                {
                    "group": group_value,
                    "contrast": contrast,
                    "row_count": int(np.count_nonzero(mask)),
                    "block_count": block_count,
                    "source_draw_count": source_count,
                    "inner_refit_count_per_source": inner_count,
                    "total_weight": float(np.sum(local_weight[positive])),
                    "source_process_mean_gain": (
                        float(point[contrast_index]) if is_finite else None
                    ),
                    "source_jackknife_variance": (
                        float(v_source[contrast_index]) if is_finite else None
                    ),
                    "validation_jackknife_variance": (
                        float(v_validation[contrast_index]) if is_finite else None
                    ),
                    "cv3two_variance": (
                        float(v_two[contrast_index]) if is_finite else None
                    ),
                    "cv3two_standard_error": se,
                    "t_degrees_of_freedom": int(df) if estimable else None,
                    "one_sided_t_critical_value": (
                        float(critical) if estimable and critical is not None else None
                    ),
                    "lower_bound": lower,
                    "status": (
                        "robust_positive"
                        if estimable and lower is not None and lower > gain_tolerance
                        else "not_robust_positive"
                        if estimable
                        else "unavailable"
                    ),
                    "estimable": estimable,
                }
            )

    contrast_rows: list[TrainingSourceProcessV0Contrast] = []
    estimable_cells = 0
    for contrast_index, contrast in enumerate(names):
        cells = tuple(
            TrainingSourceProcessV0Cell(**row)
            for row in records[contrast_index]
        )
        statuses = [cell.status for cell in cells]
        estimable_cells += sum(cell.estimable for cell in cells)
        contrast_rows.append(
            TrainingSourceProcessV0Contrast(
                contrast=contrast,
                category=_category(statuses),
                robust_positive_group_count=statuses.count("robust_positive"),
                not_robust_positive_group_count=statuses.count("not_robust_positive"),
                unavailable_group_count=statuses.count("unavailable"),
                groups=cells,
            )
        )

    cell_count = len(group_order) * contrast_count
    return TrainingSourceProcessV0Audit(
        schema_version=1,
        method_version="training_source_process_positive_iut_v0",
        qualification_status="statistically_qualified",
        primary_confirmatory=False,
        source_process_id=process_id,
        source_process_manifest_sha256=process_sha,
        inference_target=(
            "mean held-out directional gain over a predeclared outer source-resampling "
            "process, its nested inner training-refit process, and the validation population"
        ),
        source_draw_count=source_count,
        source_draw_ids=source_ids,
        inner_refit_count_per_source=inner_count,
        group_count=len(group_order),
        contrast_count=contrast_count,
        component_one_sided_alpha=float(component_one_sided_alpha),
        minimum_source_draws=minimum_source_draws,
        minimum_inner_refits_per_source=minimum_inner_refits_per_source,
        minimum_blocks_per_group=minimum_blocks_per_group,
        gain_tolerance=float(gain_tolerance),
        variance_method="outer_source_x_validation_cv3two_after_inner_refit_mean",
        critical_value_method="student_t_min_source_block_minus_one",
        inner_refits_nested_within_source=True,
        inner_refits_pooled_as_independent_source_draws=False,
        source_draws_equally_weighted=True,
        effective_training_cluster_count=source_count,
        compound_intersection_union_test=True,
        fixed_set_results_reclassified=False,
        qualified_v5_results_reclassified=False,
        original_source_superpopulation_generalization_claimed=False,
        cell_count=cell_count,
        estimable_cell_count=int(estimable_cells),
        all_cells_estimable=bool(estimable_cells == cell_count),
        contrasts=tuple(contrast_rows),
    )


def evaluate_training_source_process_positive_information_v0(
    levels: Sequence[Sequence[RefitInformationLevelScores]],
    groups: Sequence[object],
    *,
    blocks: Sequence[object],
    source_draw_ids: Sequence[object],
    inner_refit_ids_by_source: Sequence[Sequence[object]],
    source_process_id: object,
    source_process_manifest_sha256: object,
    score_name: str = "log",
    sample_weight: Sequence[float] | None = None,
    component_one_sided_alpha: float = 0.05,
    minimum_source_draws: int = 8,
    minimum_inner_refits_per_source: int = 8,
    minimum_blocks_per_group: int = 8,
    gain_tolerance: float = 0.0,
) -> TrainingSourceProcessV0InformationEvaluation:
    """Evaluate an ordered filtration under the experimental source-process v0."""

    score_label = str(score_name).strip()
    if not score_label:
        raise ValueError("score_name must be non-empty")
    if not levels:
        raise ValueError("levels must contain at least one source draw")

    source_count = len(levels)
    if len(source_draw_ids) != source_count:
        raise ValueError("source_draw_ids must align with source-level score collections")

    template_rows, template_matrices = _score_matrices(levels[0])
    inner_count, n = template_matrices[0].shape
    matrices_by_source: list[tuple[np.ndarray, ...]] = [template_matrices]

    for source_index in range(1, source_count):
        rows, matrices = _score_matrices(levels[source_index])
        if tuple((r.name, r.information) for r in rows) != tuple(
            (r.name, r.information) for r in template_rows
        ):
            raise ValueError("every source draw must use identical ordered level metadata")
        if any(matrix.shape != (inner_count, n) for matrix in matrices):
            raise ValueError("every source draw must use balanced inner-refit x row score matrices")
        matrices_by_source.append(matrices)

    steps = validate_information_filtration(
        [InformationLevelScore(row.name, row.information, [0.0]) for row in template_rows]
    )
    weight = _weights(sample_weight, n)
    positive = weight > 0

    for source_index, matrices in enumerate(matrices_by_source):
        for row, matrix in zip(template_rows[:-1], matrices[:-1]):
            if not np.isfinite(matrix[:, positive]).all():
                raise ValueError(
                    f"source {source_index} comparator level {row.name!r} must be finite"
                )

    gains = np.empty((source_count, inner_count, n, len(steps)), dtype=float)
    for source_index, matrices in enumerate(matrices_by_source):
        for step_index in range(len(steps)):
            gains[source_index, :, :, step_index] = (
                matrices[step_index + 1] - matrices[step_index]
            )

    audit = evaluate_training_source_process_positive_iut_v0(
        gains,
        groups,
        blocks=blocks,
        source_draw_ids=source_draw_ids,
        inner_refit_ids_by_source=inner_refit_ids_by_source,
        source_process_id=source_process_id,
        source_process_manifest_sha256=source_process_manifest_sha256,
        contrast_names=tuple(
            f"{step.lower_level}->{step.upper_level}" for step in steps
        ),
        sample_weight=weight,
        component_one_sided_alpha=component_one_sided_alpha,
        minimum_source_draws=minimum_source_draws,
        minimum_inner_refits_per_source=minimum_inner_refits_per_source,
        minimum_blocks_per_group=minimum_blocks_per_group,
        gain_tolerance=gain_tolerance,
    )

    ceiling = template_rows[0].name
    for index, summary in enumerate(audit.contrasts):
        if summary.category != "robust_generalizing":
            break
        ceiling = template_rows[index + 1].name

    return TrainingSourceProcessV0InformationEvaluation(
        schema_version=1,
        method_version="training_source_process_positive_iut_v0",
        qualification_status="statistically_qualified",
        score_name=score_label,
        levels=tuple(row.name for row in template_rows),
        steps=steps,
        information_filtration_validated=True,
        source_process_mean_transfer_ceiling=ceiling,
        process_audit=audit,
        fixed_set_results_reclassified=False,
        qualified_v5_results_reclassified=False,
    )
