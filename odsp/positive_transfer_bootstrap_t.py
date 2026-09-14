"""One-sided familywise bootstrap-t for directional positive-transfer claims.

ODSP's prospective version-2 simultaneous intervals are two-sided.  That is the
right default when both positive and negative departures are scientific targets,
but the confirmatory transfer claim used by a non-skippable ceiling is
directional: every predeclared group x information contrast must have gain above
a non-negative tolerance.

This module therefore provides a separate one-sided lower-confidence procedure.
It does not alter or reinterpret the frozen two-sided v2 route.  Within each
independent validation group, one bootstrap block draw is shared across all
contrasts.  Every replicate recomputes both the ratio-of-sums estimate and its
cluster influence standard error.  The pivotal statistic is

    T*_bj = (theta*_bj - theta_hat_j) / SE*_bj,

and one common critical value is the requested quantile of ``max_j T*_bj`` over
the complete estimable group x contrast family.  Simultaneous lower bounds are

    L_j = theta_hat_j - c * SE_hat_j.

The route assumes validation-group independence.  Balanced groups observed on a
common exchangeable block set require a paired one-sided procedure instead.
"""
from __future__ import annotations

from dataclasses import asdict, dataclass
import math
from typing import Sequence

import numpy as np

from .bootstrap_t import (
    bootstrap_ratio_mean_and_cluster_se,
    ratio_mean_and_cluster_se,
)
from .multicontrast_bootstrap_t import (
    _contrast_names,
    _labels,
    _stable_group_seed,
    _weights,
)


_EPS = 1e-15


@dataclass(frozen=True)
class PositiveTransferCell:
    group: object
    contrast: str
    row_count: int
    block_count: int
    total_weight: float
    mean_gain: float
    studentizing_standard_error: float | None
    lower_bound: float | None
    status: str
    estimable: bool

    def as_dict(self) -> dict[str, object]:
        return asdict(self)


@dataclass(frozen=True)
class PositiveTransferContrastSummary:
    contrast: str
    category: str
    robust_positive_group_count: int
    not_robust_positive_group_count: int
    unavailable_group_count: int
    groups: tuple[PositiveTransferCell, ...]

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
class IndependentGroupPositiveTransferBootstrapTAudit:
    schema_version: int
    group_count: int
    contrast_count: int
    familywise_lower_confidence_level: float
    bootstrap_draws: int
    seed: int
    minimum_blocks_per_group: int
    gain_tolerance: float
    row_independence_assumed: bool
    bootstrap_t_critical_value: float | None
    bootstrap_t_method: str
    alternative: str
    replicate_studentization_recomputed: bool
    same_block_draw_shared_across_contrasts_within_group: bool
    validation_group_independence_assumed: bool
    cell_count: int
    estimable_cell_count: int
    all_cells_estimable: bool
    contrasts: tuple[PositiveTransferContrastSummary, ...]

    def as_dict(self) -> dict[str, object]:
        return {
            "schema_version": self.schema_version,
            "group_count": self.group_count,
            "contrast_count": self.contrast_count,
            "familywise_lower_confidence_level": self.familywise_lower_confidence_level,
            "bootstrap_draws": self.bootstrap_draws,
            "seed": self.seed,
            "minimum_blocks_per_group": self.minimum_blocks_per_group,
            "gain_tolerance": self.gain_tolerance,
            "row_independence_assumed": self.row_independence_assumed,
            "bootstrap_t_critical_value": self.bootstrap_t_critical_value,
            "bootstrap_t_method": self.bootstrap_t_method,
            "alternative": self.alternative,
            "replicate_studentization_recomputed": self.replicate_studentization_recomputed,
            "same_block_draw_shared_across_contrasts_within_group": self.same_block_draw_shared_across_contrasts_within_group,
            "validation_group_independence_assumed": self.validation_group_independence_assumed,
            "cell_count": self.cell_count,
            "estimable_cell_count": self.estimable_cell_count,
            "all_cells_estimable": self.all_cells_estimable,
            "contrasts": [row.as_dict() for row in self.contrasts],
        }


def one_sided_lower_max_t_critical_value(
    bootstrap_mean: np.ndarray,
    bootstrap_se: np.ndarray,
    point_mean: np.ndarray,
    *,
    confidence_level: float,
    epsilon: float = _EPS,
) -> float:
    """Return a conservative one-sided max-t critical value.

    A zero replicate SE with a positive displacement contributes ``+inf`` and
    therefore fails closed.  A zero SE with no displacement contributes zero; a
    negative displacement contributes ``-inf`` because it cannot threaten a
    simultaneous lower confidence bound.  The empirical quantile uses
    ``method='higher'`` and is floored at zero so lower bounds never exceed their
    point estimates merely because every realized bootstrap t statistic is
    negative.
    """

    means = np.asarray(bootstrap_mean, dtype=float)
    ses = np.asarray(bootstrap_se, dtype=float)
    point = np.asarray(point_mean, dtype=float)
    if means.ndim != 2 or ses.shape != means.shape:
        raise ValueError("bootstrap_mean and bootstrap_se must share draws x cells shape")
    if point.shape != (means.shape[1],):
        raise ValueError("point_mean must contain one value per bootstrap cell")
    if not np.isfinite(means).all() or not np.isfinite(ses).all() or np.any(ses < 0):
        raise ValueError("bootstrap means and standard errors must be finite and SEs non-negative")
    if not np.isfinite(point).all():
        raise ValueError("point_mean must be finite")
    if not math.isfinite(confidence_level) or not 0.0 < confidence_level < 1.0:
        raise ValueError("confidence_level must lie strictly between zero and one")
    if not math.isfinite(epsilon) or epsilon <= 0:
        raise ValueError("epsilon must be finite and positive")

    displacement = means - point[None, :]
    statistic = np.empty_like(displacement)
    positive_se = ses > epsilon
    statistic[positive_se] = displacement[positive_se] / ses[positive_se]
    stable = (~positive_se) & (np.abs(displacement) <= epsilon)
    moved_up = (~positive_se) & (displacement > epsilon)
    moved_down = (~positive_se) & (displacement < -epsilon)
    statistic[stable] = 0.0
    statistic[moved_up] = np.inf
    statistic[moved_down] = -np.inf
    maxima = np.max(statistic, axis=1)
    critical = float(np.quantile(maxima, confidence_level, method="higher"))
    return max(0.0, critical)


def one_sided_lower_bounds(
    point_mean: np.ndarray,
    point_se: np.ndarray,
    critical_value: float,
) -> np.ndarray:
    mean = np.asarray(point_mean, dtype=float)
    se = np.asarray(point_se, dtype=float)
    if mean.ndim != 1 or se.shape != mean.shape:
        raise ValueError("point_mean and point_se must be aligned one-dimensional vectors")
    if not np.isfinite(mean).all() or not np.isfinite(se).all() or np.any(se < 0):
        raise ValueError("point means and standard errors must be finite and SEs non-negative")
    if math.isnan(critical_value) or critical_value < 0:
        raise ValueError("critical_value must be non-negative")
    if math.isinf(critical_value):
        lower = np.full_like(mean, -np.inf)
        lower[se <= _EPS] = mean[se <= _EPS]
        return lower
    return mean - critical_value * se


def _directional_category(statuses: Sequence[str]) -> str:
    values = tuple(statuses)
    if any(value == "unavailable" for value in values):
        return "unavailable"
    if values and all(value == "robust_positive" for value in values):
        return "robust_generalizing"
    return "not_robust_generalizing"


def certify_independent_group_positive_transfer_v2(
    row_gain: Sequence[Sequence[float]] | np.ndarray,
    groups: Sequence[object],
    *,
    blocks: Sequence[object] | None = None,
    contrast_names: Sequence[object] | None = None,
    sample_weight: Sequence[float] | None = None,
    familywise_lower_confidence_level: float = 0.95,
    bootstrap_draws: int = 4000,
    seed: int = 20260915,
    minimum_blocks_per_group: int = 8,
    gain_tolerance: float = 0.0,
) -> IndependentGroupPositiveTransferBootstrapTAudit:
    """Certify directional positive transfer over all group x contrast cells."""

    gain = np.asarray(row_gain, dtype=float)
    if gain.ndim == 1:
        gain = gain[:, None]
    if gain.ndim != 2 or gain.shape[0] == 0 or gain.shape[1] == 0:
        raise ValueError("row_gain must be a non-empty rows x contrasts matrix")
    if np.isnan(gain).any() or np.isposinf(gain).any():
        raise ValueError("row_gain may contain finite values or -inf, but not NaN or +inf")
    n, contrast_count = gain.shape
    names = _contrast_names(contrast_names, contrast_count)
    group = _labels(groups, n, name="groups")
    weight = _weights(sample_weight, n)
    if blocks is None:
        block = np.asarray([f"row-{index:09d}" for index in range(n)], dtype=object)
        row_independence = True
    else:
        block = _labels(blocks, n, name="blocks")
        row_independence = False

    if (
        not math.isfinite(familywise_lower_confidence_level)
        or not 0.0 < familywise_lower_confidence_level < 1.0
    ):
        raise ValueError("familywise_lower_confidence_level must lie strictly between zero and one")
    if isinstance(bootstrap_draws, bool) or not isinstance(bootstrap_draws, int) or bootstrap_draws < 500:
        raise ValueError("bootstrap_draws must be an integer >= 500")
    if isinstance(seed, bool) or not isinstance(seed, int) or seed < 0:
        raise ValueError("seed must be a non-negative integer")
    if (
        isinstance(minimum_blocks_per_group, bool)
        or not isinstance(minimum_blocks_per_group, int)
        or minimum_blocks_per_group < 2
    ):
        raise ValueError("minimum_blocks_per_group must be an integer >= 2")
    if not math.isfinite(gain_tolerance) or gain_tolerance < 0:
        raise ValueError("gain_tolerance must be finite and non-negative")

    group_order = tuple(
        sorted(
            set(group.tolist()),
            key=lambda value: (type(value).__name__, repr(value)),
        )
    )
    records: list[list[dict[str, object]]] = [[] for _ in range(contrast_count)]
    eligible: list[tuple[int, int]] = []
    sample_mean_columns: list[np.ndarray] = []
    sample_se_columns: list[np.ndarray] = []
    point_means: list[float] = []
    point_ses: list[float] = []

    for group_value in group_order:
        mask = group == group_value
        local_gain = gain[mask]
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
        finite = np.all(np.isfinite(local_gain[positive]), axis=0)
        block_weight = np.empty(block_count, dtype=float)
        block_numerator = np.zeros((block_count, contrast_count), dtype=float)
        for block_index, block_value in enumerate(block_order):
            block_mask = (local_block == block_value) & positive
            mass = float(np.sum(local_weight[block_mask]))
            if mass <= 0:
                raise ValueError("every declared positive-support block must have positive mass")
            block_weight[block_index] = mass
            if np.any(finite):
                block_numerator[block_index, finite] = np.sum(
                    local_gain[block_mask][:, finite]
                    * local_weight[block_mask][:, None],
                    axis=0,
                )

        local_point = np.full(contrast_count, np.nan, dtype=float)
        local_se = np.full(contrast_count, np.nan, dtype=float)
        if np.any(finite):
            values, ses = ratio_mean_and_cluster_se(
                block_numerator[:, finite], block_weight
            )
            local_point[finite] = values
            local_se[finite] = ses

        sampled_means: np.ndarray | None = None
        sampled_ses: np.ndarray | None = None
        if np.any(finite) and block_count >= minimum_blocks_per_group:
            rng = np.random.default_rng(_stable_group_seed(seed, group_value))
            sampled = rng.integers(0, block_count, size=(bootstrap_draws, block_count))
            sampled_means, sampled_ses = bootstrap_ratio_mean_and_cluster_se(
                block_numerator[:, finite], block_weight, sampled
            )

        finite_positions = np.flatnonzero(finite)
        finite_position_map = {
            int(contrast_index): local_index
            for local_index, contrast_index in enumerate(finite_positions.tolist())
        }
        for contrast_index, contrast in enumerate(names):
            is_finite = bool(finite[contrast_index])
            estimable = bool(is_finite and block_count >= minimum_blocks_per_group)
            record: dict[str, object] = {
                "group": group_value,
                "contrast": contrast,
                "row_count": int(np.count_nonzero(mask)),
                "block_count": block_count,
                "total_weight": float(np.sum(local_weight[positive])),
                "mean_gain": float(local_point[contrast_index]) if is_finite else float("-inf"),
                "studentizing_standard_error": (
                    float(local_se[contrast_index]) if is_finite and block_count >= 2 else None
                ),
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
                point_ses.append(float(local_se[contrast_index]))

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
        lower = one_sided_lower_bounds(point_mean, point_se, critical)
        for column, (contrast_index, record_index) in enumerate(eligible):
            lo = float(lower[column])
            records[contrast_index][record_index]["lower_bound"] = lo
            records[contrast_index][record_index]["status"] = (
                "robust_positive" if lo > gain_tolerance else "not_robust_positive"
            )

    contrast_rows: list[PositiveTransferContrastSummary] = []
    for contrast_index, contrast in enumerate(names):
        cells = tuple(PositiveTransferCell(**record) for record in records[contrast_index])
        statuses = [cell.status for cell in cells]
        contrast_rows.append(
            PositiveTransferContrastSummary(
                contrast=contrast,
                category=_directional_category(statuses),
                robust_positive_group_count=statuses.count("robust_positive"),
                not_robust_positive_group_count=statuses.count("not_robust_positive"),
                unavailable_group_count=statuses.count("unavailable"),
                groups=cells,
            )
        )

    cell_count = len(group_order) * contrast_count
    return IndependentGroupPositiveTransferBootstrapTAudit(
        schema_version=1,
        group_count=len(group_order),
        contrast_count=contrast_count,
        familywise_lower_confidence_level=float(familywise_lower_confidence_level),
        bootstrap_draws=bootstrap_draws,
        seed=seed,
        minimum_blocks_per_group=minimum_blocks_per_group,
        gain_tolerance=float(gain_tolerance),
        row_independence_assumed=row_independence,
        bootstrap_t_critical_value=critical,
        bootstrap_t_method="one_sided_replicate_studentized_cluster_ratio_max_t",
        alternative="greater",
        replicate_studentization_recomputed=True,
        same_block_draw_shared_across_contrasts_within_group=True,
        validation_group_independence_assumed=True,
        cell_count=cell_count,
        estimable_cell_count=len(eligible),
        all_cells_estimable=bool(len(eligible) == cell_count),
        contrasts=tuple(contrast_rows),
    )
