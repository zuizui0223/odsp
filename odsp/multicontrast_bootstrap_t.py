"""Prospective genuine bootstrap-t over an independent group x contrast family.

This is the multi-contrast version-2 inference core.  Each validation group is
resampled independently because this route assumes group independence.  Within a
group, one sampled block sequence is shared by every contrast so cross-contrast
covariance is retained.  Every bootstrap draw recomputes both each ratio-of-sums
contrast estimate and its cluster studentizer before one global max-t statistic
is formed over all estimable group x contrast cells.

For groups observed on the same exchangeable validation blocks, use the paired
shared-block route instead of this independent-group route.
"""
from __future__ import annotations

from dataclasses import asdict, dataclass
import hashlib
import math
from typing import Sequence

import numpy as np

from .bootstrap_t import (
    bootstrap_ratio_mean_and_cluster_se,
    ratio_mean_and_cluster_se,
    simultaneous_bootstrap_t_bounds,
    studentized_max_t_critical_value,
)
from .predictive_resolution_certification import _cell_status, _step_category


@dataclass(frozen=True)
class GroupContrastBootstrapTCell:
    group: object
    contrast: str
    row_count: int
    block_count: int
    total_weight: float
    mean_gain: float
    studentizing_standard_error: float | None
    lower_bound: float | None
    upper_bound: float | None
    status: str
    estimable: bool

    def as_dict(self) -> dict[str, object]:
        return asdict(self)


@dataclass(frozen=True)
class ContrastBootstrapTSummary:
    contrast: str
    category: str
    robust_positive_group_count: int
    robust_nonpositive_group_count: int
    uncertain_group_count: int
    unavailable_group_count: int
    groups: tuple[GroupContrastBootstrapTCell, ...]

    def as_dict(self) -> dict[str, object]:
        return {
            "contrast": self.contrast,
            "category": self.category,
            "robust_positive_group_count": self.robust_positive_group_count,
            "robust_nonpositive_group_count": self.robust_nonpositive_group_count,
            "uncertain_group_count": self.uncertain_group_count,
            "unavailable_group_count": self.unavailable_group_count,
            "groups": [row.as_dict() for row in self.groups],
        }


@dataclass(frozen=True)
class IndependentGroupContrastBootstrapTAudit:
    schema_version: int
    group_count: int
    contrast_count: int
    familywise_confidence_level: float
    bootstrap_draws: int
    seed: int
    minimum_blocks_per_group: int
    gain_tolerance: float
    row_independence_assumed: bool
    bootstrap_t_critical_value: float | None
    bootstrap_t_method: str
    replicate_studentization_recomputed: bool
    same_block_draw_shared_across_contrasts_within_group: bool
    validation_group_independence_assumed: bool
    cell_count: int
    estimable_cell_count: int
    all_cells_estimable: bool
    contrasts: tuple[ContrastBootstrapTSummary, ...]

    def as_dict(self) -> dict[str, object]:
        return {
            "schema_version": self.schema_version,
            "group_count": self.group_count,
            "contrast_count": self.contrast_count,
            "familywise_confidence_level": self.familywise_confidence_level,
            "bootstrap_draws": self.bootstrap_draws,
            "seed": self.seed,
            "minimum_blocks_per_group": self.minimum_blocks_per_group,
            "gain_tolerance": self.gain_tolerance,
            "row_independence_assumed": self.row_independence_assumed,
            "bootstrap_t_critical_value": self.bootstrap_t_critical_value,
            "bootstrap_t_method": self.bootstrap_t_method,
            "replicate_studentization_recomputed": self.replicate_studentization_recomputed,
            "same_block_draw_shared_across_contrasts_within_group": self.same_block_draw_shared_across_contrasts_within_group,
            "validation_group_independence_assumed": self.validation_group_independence_assumed,
            "cell_count": self.cell_count,
            "estimable_cell_count": self.estimable_cell_count,
            "all_cells_estimable": self.all_cells_estimable,
            "contrasts": [row.as_dict() for row in self.contrasts],
        }


def _labels(values: Sequence[object], n: int, *, name: str) -> np.ndarray:
    result = np.asarray(list(values), dtype=object)
    if result.shape != (n,):
        raise ValueError(f"{name} must contain one label per held-out row")
    for value in result.tolist():
        if value is None:
            raise ValueError(f"{name} labels may not be missing")
        try:
            hash(value)
        except TypeError as exc:
            raise ValueError(f"{name} labels must be hashable") from exc
    return result


def _weights(values: Sequence[float] | None, n: int) -> np.ndarray:
    if values is None:
        return np.ones(n, dtype=float)
    result = np.asarray(values, dtype=float)
    if result.shape != (n,):
        raise ValueError("sample_weight must contain one value per held-out row")
    if not np.isfinite(result).all() or np.any(result < 0) or not np.any(result > 0):
        raise ValueError(
            "sample_weight must be finite, non-negative, aligned and positive in total"
        )
    return result


def _contrast_names(values: Sequence[object] | None, count: int) -> tuple[str, ...]:
    if values is None:
        names = tuple(f"contrast-{index:03d}" for index in range(count))
    else:
        if len(values) != count:
            raise ValueError("contrast_names must contain one name per gain column")
        names = tuple(str(value).strip() for value in values)
        if any(not value for value in names):
            raise ValueError("contrast_names must be non-empty")
    if len(set(names)) != count:
        raise ValueError("contrast_names must be unique")
    return names


def _stable_group_seed(seed: int, group: object) -> int:
    digest = hashlib.sha256(
        f"{seed}|multicontrast-bootstrap-t-v2|{group!r}".encode("utf-8")
    ).digest()
    return int.from_bytes(digest[:8], "little", signed=False)


def certify_independent_group_contrasts_v2(
    row_gain: Sequence[Sequence[float]] | np.ndarray,
    groups: Sequence[object],
    *,
    blocks: Sequence[object] | None = None,
    contrast_names: Sequence[object] | None = None,
    sample_weight: Sequence[float] | None = None,
    familywise_confidence_level: float = 0.95,
    bootstrap_draws: int = 4000,
    seed: int = 20260914,
    minimum_blocks_per_group: int = 8,
    gain_tolerance: float = 0.0,
) -> IndependentGroupContrastBootstrapTAudit:
    """Genuine bootstrap-t certification over all group x contrast cells.

    Non-finite gains in one cell make that cell unavailable but do not erase
    unrelated contrasts.  If ``blocks`` is omitted, every positive-weight row is
    treated as its own exchangeable block and the assumption is recorded.
    """

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

    if not math.isfinite(familywise_confidence_level) or not 0 < familywise_confidence_level < 1:
        raise ValueError("familywise_confidence_level must lie strictly between zero and one")
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

    group_order = tuple(sorted(set(group.tolist()), key=lambda value: (type(value).__name__, repr(value))))
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
            block_mask = local_block == block_value
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
        if np.any(finite) and block_count >= 2:
            values, ses = ratio_mean_and_cluster_se(
                block_numerator[:, finite],
                block_weight,
            )
            local_point[finite] = values
            local_se[finite] = ses

        sampled_means: np.ndarray | None = None
        sampled_ses: np.ndarray | None = None
        if np.any(finite) and block_count >= minimum_blocks_per_group:
            rng = np.random.default_rng(_stable_group_seed(seed, group_value))
            sampled = rng.integers(
                0,
                block_count,
                size=(bootstrap_draws, block_count),
            )
            sampled_means, sampled_ses = bootstrap_ratio_mean_and_cluster_se(
                block_numerator[:, finite],
                block_weight,
                sampled,
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
                "total_weight": float(np.sum(local_weight)),
                "mean_gain": (
                    float(local_point[contrast_index])
                    if is_finite and block_count >= 2
                    else float("-inf")
                ),
                "studentizing_standard_error": (
                    float(local_se[contrast_index])
                    if is_finite and block_count >= 2
                    else None
                ),
                "lower_bound": None,
                "upper_bound": None,
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
        critical = studentized_max_t_critical_value(
            bootstrap_mean,
            bootstrap_se,
            point_mean,
            confidence_level=familywise_confidence_level,
        )
        lower, upper = simultaneous_bootstrap_t_bounds(
            point_mean,
            point_se,
            critical,
        )
        for column, (contrast_index, record_index) in enumerate(eligible):
            lo = float(lower[column])
            hi = float(upper[column])
            records[contrast_index][record_index]["lower_bound"] = lo
            records[contrast_index][record_index]["upper_bound"] = hi
            records[contrast_index][record_index]["status"] = _cell_status(
                lo,
                hi,
                tolerance=gain_tolerance,
            )

    contrast_rows: list[ContrastBootstrapTSummary] = []
    for contrast_index, contrast in enumerate(names):
        cells = tuple(
            GroupContrastBootstrapTCell(**record)
            for record in records[contrast_index]
        )
        statuses = [cell.status for cell in cells]
        contrast_rows.append(
            ContrastBootstrapTSummary(
                contrast=contrast,
                category=_step_category(statuses),
                robust_positive_group_count=statuses.count("robust_positive"),
                robust_nonpositive_group_count=statuses.count("robust_nonpositive"),
                uncertain_group_count=statuses.count("uncertain"),
                unavailable_group_count=statuses.count("unavailable"),
                groups=cells,
            )
        )

    cell_count = len(group_order) * contrast_count
    return IndependentGroupContrastBootstrapTAudit(
        schema_version=2,
        group_count=len(group_order),
        contrast_count=contrast_count,
        familywise_confidence_level=float(familywise_confidence_level),
        bootstrap_draws=bootstrap_draws,
        seed=seed,
        minimum_blocks_per_group=minimum_blocks_per_group,
        gain_tolerance=float(gain_tolerance),
        row_independence_assumed=row_independence,
        bootstrap_t_critical_value=critical,
        bootstrap_t_method="replicate_studentized_cluster_ratio_max_t",
        replicate_studentization_recomputed=True,
        same_block_draw_shared_across_contrasts_within_group=True,
        validation_group_independence_assumed=True,
        cell_count=cell_count,
        estimable_cell_count=len(eligible),
        all_cells_estimable=bool(len(eligible) == cell_count),
        contrasts=tuple(contrast_rows),
    )
