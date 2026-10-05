"""Training-process positive transfer v4: CV3max jackknife + IUT.

This candidate applies the scalar two-way cluster-jackknife max-SE construction
to ODSP's crossed weighted-ratio process-mean estimator.  It is a separate
prospective route and does not alter fixed-set refit inference.
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
from .training_process_positive_transfer import _process_identity


@dataclass(frozen=True)
class TrainingProcessCV3MaxCell:
    group: object
    contrast: str
    row_count: int
    block_count: int
    total_weight: float
    process_mean_gain: float | None
    training_jackknife_variance: float | None
    validation_jackknife_variance: float | None
    intersection_jackknife_variance: float | None
    three_term_jackknife_variance: float | None
    cv3max_variance: float | None
    cv3max_standard_error: float | None
    cv3max_variance_source: str | None
    t_degrees_of_freedom: int | None
    one_sided_t_critical_value: float | None
    lower_bound: float | None
    status: str
    estimable: bool

    def as_dict(self) -> dict[str, object]:
        return asdict(self)


@dataclass(frozen=True)
class TrainingProcessCV3MaxContrast:
    contrast: str
    category: str
    robust_positive_group_count: int
    not_robust_positive_group_count: int
    unavailable_group_count: int
    groups: tuple[TrainingProcessCV3MaxCell, ...]

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
class TrainingProcessPositiveCV3MaxIUTAudit:
    schema_version: int
    method_version: str
    training_process_id: str
    training_process_manifest_sha256: str
    inference_target: str
    refit_count: int
    refit_ids: tuple[str, ...]
    group_count: int
    contrast_count: int
    component_one_sided_alpha: float
    minimum_refits: int
    minimum_blocks_per_group: int
    gain_tolerance: float
    variance_method: str
    critical_value_method: str
    alternative: str
    compound_intersection_union_test: bool
    all_required_components_must_reject: bool
    additional_component_multiplicity_correction_applied: bool
    component_test_independence_assumed: bool
    component_lower_bounds_are_simultaneous: bool
    arbitrary_any_cell_familywise_claim_allowed: bool
    cv3_delete_one_center_is_full_estimate: bool
    cv3max_uses_max_of_three_term_and_two_one_way_variances: bool
    t_degrees_of_freedom_rule: str
    refits_assumed_exchangeable_draws_from_frozen_process: bool
    process_mean_target: bool
    fixed_set_intersection_used: bool
    cell_count: int
    estimable_cell_count: int
    all_cells_estimable: bool
    contrasts: tuple[TrainingProcessCV3MaxContrast, ...]

    def as_dict(self) -> dict[str, object]:
        payload = asdict(self)
        payload["refit_ids"] = list(self.refit_ids)
        payload["contrasts"] = [row.as_dict() for row in self.contrasts]
        return payload


@dataclass(frozen=True)
class TrainingProcessPositiveCV3MaxInformationCertification:
    schema_version: int
    method_version: str
    score_name: str
    levels: tuple[str, ...]
    steps: tuple[InformationTransferStep, ...]
    information_filtration_validated: bool
    training_process_id: str
    training_process_manifest_sha256: str
    process_mean_certified_transfer_ceiling: str
    process_audit: TrainingProcessPositiveCV3MaxIUTAudit
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


def _beta_continued_fraction(a: float, b: float, x: float) -> float:
    max_iterations = 300
    epsilon = 3e-14
    tiny = 1e-300
    qab = a + b
    qap = a + 1.0
    qam = a - 1.0
    c = 1.0
    d = 1.0 - qab * x / qap
    if abs(d) < tiny:
        d = tiny
    d = 1.0 / d
    h = d
    for m in range(1, max_iterations + 1):
        m2 = 2 * m
        aa = m * (b - m) * x / ((qam + m2) * (a + m2))
        d = 1.0 + aa * d
        if abs(d) < tiny:
            d = tiny
        c = 1.0 + aa / c
        if abs(c) < tiny:
            c = tiny
        d = 1.0 / d
        h *= d * c

        aa = -(a + m) * (qab + m) * x / ((a + m2) * (qap + m2))
        d = 1.0 + aa * d
        if abs(d) < tiny:
            d = tiny
        c = 1.0 + aa / c
        if abs(c) < tiny:
            c = tiny
        d = 1.0 / d
        delta = d * c
        h *= delta
        if abs(delta - 1.0) <= epsilon:
            return float(h)
    raise RuntimeError("incomplete-beta continued fraction did not converge")


def _regularized_incomplete_beta(x: float, a: float, b: float) -> float:
    if not 0.0 <= x <= 1.0:
        raise ValueError("x must lie in [0, 1]")
    if a <= 0.0 or b <= 0.0:
        raise ValueError("beta shape parameters must be positive")
    if x == 0.0:
        return 0.0
    if x == 1.0:
        return 1.0
    log_bt = (
        math.lgamma(a + b)
        - math.lgamma(a)
        - math.lgamma(b)
        + a * math.log(x)
        + b * math.log1p(-x)
    )
    bt = math.exp(log_bt)
    if x < (a + 1.0) / (a + b + 2.0):
        return float(bt * _beta_continued_fraction(a, b, x) / a)
    return float(
        1.0
        - bt
        * _beta_continued_fraction(b, a, 1.0 - x)
        / b
    )


def _student_t_cdf(value: float, degrees_of_freedom: int) -> float:
    if (
        isinstance(degrees_of_freedom, bool)
        or not isinstance(degrees_of_freedom, int)
        or degrees_of_freedom < 1
    ):
        raise ValueError("degrees_of_freedom must be a positive integer")
    x = float(value)
    if math.isnan(x):
        raise ValueError("value must not be NaN")
    if x == math.inf:
        return 1.0
    if x == -math.inf:
        return 0.0
    if x == 0.0:
        return 0.5
    nu = float(degrees_of_freedom)
    z = nu / (nu + x * x)
    ib = _regularized_incomplete_beta(z, nu / 2.0, 0.5)
    if x > 0.0:
        return float(1.0 - 0.5 * ib)
    return float(0.5 * ib)


def _student_t_ppf(probability: float, degrees_of_freedom: int) -> float:
    p = float(probability)
    if not math.isfinite(p) or not 0.0 < p < 1.0:
        raise ValueError("probability must lie strictly between zero and one")
    if p == 0.5:
        return 0.0
    if p < 0.5:
        return -_student_t_ppf(1.0 - p, degrees_of_freedom)

    lower = 0.0
    upper = 1.0
    while _student_t_cdf(upper, degrees_of_freedom) < p:
        upper *= 2.0
        if upper > 1e8:
            raise RuntimeError("could not bracket Student-t quantile")
    for _ in range(100):
        midpoint = 0.5 * (lower + upper)
        if _student_t_cdf(midpoint, degrees_of_freedom) < p:
            lower = midpoint
        else:
            upper = midpoint
    return float(0.5 * (lower + upper))


def _cv3max_components(
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
    """Return point and CV3max variance components for each contrast."""

    numerator = np.asarray(block_numerator, dtype=float)
    weight = np.asarray(block_weight, dtype=float)
    if numerator.ndim != 3:
        raise ValueError("block_numerator must be refit x block x contrast")
    if not np.isfinite(numerator).all():
        raise ValueError("block_numerator must be finite")
    refit_count, block_count, contrast_count = numerator.shape
    if refit_count < 2 or block_count < 2:
        raise ValueError("CV3max requires at least two refits and two blocks")
    if weight.shape != (block_count,):
        raise ValueError("block_weight must contain one value per block")
    if not np.isfinite(weight).all() or np.any(weight <= 0):
        raise ValueError("block weights must be finite and strictly positive")

    total_weight = float(np.sum(weight))
    total_numerator = np.sum(numerator, axis=(0, 1))
    full_denominator = float(refit_count) * total_weight
    point = total_numerator / full_denominator

    row_numerator = np.sum(numerator, axis=1)
    row_delete = (
        total_numerator[None, :] - row_numerator
    ) / (float(refit_count - 1) * total_weight)
    row_variance = (
        float(refit_count - 1) / float(refit_count)
    ) * np.sum((row_delete - point[None, :]) ** 2, axis=0)

    block_numerator_sum = np.sum(numerator, axis=0)
    block_denominator = (
        float(refit_count) * (total_weight - weight)
    )
    if np.any(block_denominator <= 0):
        raise ValueError("delete-one validation block leaves zero mass")
    block_delete = (
        total_numerator[None, :] - block_numerator_sum
    ) / block_denominator[:, None]
    block_variance = (
        float(block_count - 1) / float(block_count)
    ) * np.sum((block_delete - point[None, :]) ** 2, axis=0)

    intersection_count = refit_count * block_count
    intersection_denominator = (
        full_denominator - weight[None, :]
    )
    if np.any(intersection_denominator <= 0):
        raise ValueError("delete-one intersection leaves zero mass")
    intersection_delete = (
        total_numerator[None, None, :] - numerator
    ) / intersection_denominator[:, :, None]
    intersection_variance = (
        float(intersection_count - 1) / float(intersection_count)
    ) * np.sum(
        (intersection_delete - point[None, None, :]) ** 2,
        axis=(0, 1),
    )

    three_term = row_variance + block_variance - intersection_variance
    cv3max = np.maximum.reduce([three_term, row_variance, block_variance])

    sources: list[str] = []
    for index in range(contrast_count):
        if (
            three_term[index] >= row_variance[index]
            and three_term[index] >= block_variance[index]
        ):
            sources.append("three_term")
        elif row_variance[index] >= block_variance[index]:
            sources.append("training_one_way")
        else:
            sources.append("validation_one_way")

    return (
        point.astype(float),
        row_variance.astype(float),
        block_variance.astype(float),
        intersection_variance.astype(float),
        cv3max.astype(float),
        tuple(sources),
    )


def _directional_category(statuses: Sequence[str]) -> str:
    values = tuple(statuses)
    if any(value == "unavailable" for value in values):
        return "unavailable"
    if values and all(value == "robust_positive" for value in values):
        return "robust_generalizing"
    return "not_robust_generalizing"


def certify_training_process_positive_cv3max_iut_v4(
    row_gain_by_refit: Sequence[Sequence[Sequence[float]]] | np.ndarray,
    groups: Sequence[object],
    *,
    blocks: Sequence[object],
    refit_ids: Sequence[object],
    training_process_id: object,
    training_process_manifest_sha256: object,
    contrast_names: Sequence[object] | None = None,
    sample_weight: Sequence[float] | None = None,
    component_one_sided_alpha: float = 0.05,
    minimum_refits: int = 8,
    minimum_blocks_per_group: int = 8,
    gain_tolerance: float = 0.0,
) -> TrainingProcessPositiveCV3MaxIUTAudit:
    """Test the compound positive process-mean claim with CV3max components."""

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
    minimum_refits = _integer(minimum_refits, name="minimum_refits", minimum=2)
    minimum_blocks_per_group = _integer(
        minimum_blocks_per_group, name="minimum_blocks_per_group", minimum=2
    )
    if not math.isfinite(component_one_sided_alpha) or not 0 < component_one_sided_alpha < 0.5:
        raise ValueError("component_one_sided_alpha must lie strictly between 0 and 0.5")
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
    enough_refits = refit_count >= minimum_refits
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

        point = np.full(contrast_count, np.nan)
        vr = np.full(contrast_count, np.nan)
        vb = np.full(contrast_count, np.nan)
        vi = np.full(contrast_count, np.nan)
        vthree = np.full(contrast_count, np.nan)
        vmax = np.full(contrast_count, np.nan)
        sources: list[str | None] = [None] * contrast_count

        enough_blocks = block_count >= minimum_blocks_per_group
        if np.any(finite):
            (
                finite_point,
                finite_vr,
                finite_vb,
                finite_vi,
                finite_vmax,
                finite_sources,
            ) = _cv3max_components(
                block_numerator[:, :, finite],
                block_weight,
            )
            point[finite] = finite_point
            vr[finite] = finite_vr
            vb[finite] = finite_vb
            vi[finite] = finite_vi
            vthree[finite] = finite_vr + finite_vb - finite_vi
            vmax[finite] = finite_vmax
            for local_index, contrast_index in enumerate(np.flatnonzero(finite)):
                sources[int(contrast_index)] = finite_sources[local_index]

        df = min(refit_count, block_count) - 1
        critical = (
            _student_t_ppf(1.0 - component_one_sided_alpha, df)
            if enough_refits and enough_blocks
            else None
        )

        for contrast_index, contrast in enumerate(names):
            is_finite = bool(finite[contrast_index])
            estimable = bool(is_finite and enough_refits and enough_blocks)
            se = (
                float(math.sqrt(max(float(vmax[contrast_index]), 0.0)))
                if estimable
                else None
            )
            lower = (
                float(point[contrast_index] - float(critical) * se)
                if estimable and se is not None and critical is not None
                else None
            )
            records[contrast_index].append(
                {
                    "group": group_value,
                    "contrast": contrast,
                    "row_count": int(np.count_nonzero(mask)),
                    "block_count": block_count,
                    "total_weight": float(np.sum(local_weight[positive])),
                    "process_mean_gain": float(point[contrast_index]) if is_finite else None,
                    "training_jackknife_variance": float(vr[contrast_index]) if is_finite else None,
                    "validation_jackknife_variance": float(vb[contrast_index]) if is_finite else None,
                    "intersection_jackknife_variance": float(vi[contrast_index]) if is_finite else None,
                    "three_term_jackknife_variance": float(vthree[contrast_index]) if is_finite else None,
                    "cv3max_variance": float(vmax[contrast_index]) if is_finite else None,
                    "cv3max_standard_error": se,
                    "cv3max_variance_source": sources[contrast_index] if is_finite else None,
                    "t_degrees_of_freedom": int(df) if estimable else None,
                    "one_sided_t_critical_value": float(critical) if estimable and critical is not None else None,
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

    contrast_rows: list[TrainingProcessCV3MaxContrast] = []
    estimable_cells = 0
    for contrast_index, contrast in enumerate(names):
        cells = tuple(TrainingProcessCV3MaxCell(**row) for row in records[contrast_index])
        statuses = [cell.status for cell in cells]
        estimable_cells += sum(cell.estimable for cell in cells)
        contrast_rows.append(
            TrainingProcessCV3MaxContrast(
                contrast=contrast,
                category=_directional_category(statuses),
                robust_positive_group_count=statuses.count("robust_positive"),
                not_robust_positive_group_count=statuses.count("not_robust_positive"),
                unavailable_group_count=statuses.count("unavailable"),
                groups=cells,
            )
        )

    cell_count = len(group_order) * contrast_count
    return TrainingProcessPositiveCV3MaxIUTAudit(
        schema_version=4,
        method_version="training_process_positive_cv3max_iut_v4",
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
        component_one_sided_alpha=float(component_one_sided_alpha),
        minimum_refits=minimum_refits,
        minimum_blocks_per_group=minimum_blocks_per_group,
        gain_tolerance=float(gain_tolerance),
        variance_method="two_way_cluster_jackknife_cv3max",
        critical_value_method="student_t_min_refit_block_minus_one",
        alternative="greater",
        compound_intersection_union_test=True,
        all_required_components_must_reject=True,
        additional_component_multiplicity_correction_applied=False,
        component_test_independence_assumed=False,
        component_lower_bounds_are_simultaneous=False,
        arbitrary_any_cell_familywise_claim_allowed=False,
        cv3_delete_one_center_is_full_estimate=True,
        cv3max_uses_max_of_three_term_and_two_one_way_variances=True,
        t_degrees_of_freedom_rule="min(refit_count, block_count)-1",
        refits_assumed_exchangeable_draws_from_frozen_process=True,
        process_mean_target=True,
        fixed_set_intersection_used=False,
        cell_count=cell_count,
        estimable_cell_count=int(estimable_cells),
        all_cells_estimable=bool(estimable_cells == cell_count),
        contrasts=tuple(contrast_rows),
    )


def certify_training_process_positive_information_cv3max_iut_v4(
    levels: Sequence[RefitInformationLevelScores],
    groups: Sequence[object],
    *,
    blocks: Sequence[object],
    refit_ids: Sequence[object],
    training_process_id: object,
    training_process_manifest_sha256: object,
    score_name: str = "log",
    sample_weight: Sequence[float] | None = None,
    component_one_sided_alpha: float = 0.05,
    minimum_refits: int = 8,
    minimum_blocks_per_group: int = 8,
    gain_tolerance: float = 0.0,
) -> TrainingProcessPositiveCV3MaxInformationCertification:
    """Return the deepest non-skippable v4 process-mean IUT ceiling."""

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
    audit = certify_training_process_positive_cv3max_iut_v4(
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
        component_one_sided_alpha=component_one_sided_alpha,
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
    return TrainingProcessPositiveCV3MaxInformationCertification(
        schema_version=4,
        method_version="training_process_positive_cv3max_iut_v4",
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
