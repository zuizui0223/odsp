"""Familywise gain certification for cross-group shared validation blocks.

Existing ODSP group-wise bootstrap layers resample validation blocks separately
within independent groups. That is appropriate only when those group-level
validation samples can be treated as independent.

This module handles a stricter paired design: every declared group must contain
the same set of positive-mass validation blocks. One bootstrap draw resamples
those shared block IDs once and reuses the same sampled block sequence across
all groups and all declared gain contrasts. This preserves empirical cross-group
and cross-contrast covariance induced by common sampling units such as years,
sites, camera days, or surveys.

The method is deliberately fail-closed. If shared block support is not exactly
balanced across groups, callers must not use this paired-block route.
"""
from __future__ import annotations

from dataclasses import asdict, dataclass
import hashlib
import math
from typing import Sequence

import numpy as np

from .predictive_resolution_certification import _cell_status, _step_category


@dataclass(frozen=True)
class SharedBlockGainCell:
    group: object
    contrast: str
    row_count: int
    shared_block_count: int
    total_weight: float
    mean_gain: float
    bootstrap_standard_error: float | None
    lower_bound: float | None
    upper_bound: float | None
    status: str
    estimable: bool

    def as_dict(self) -> dict[str, object]:
        return asdict(self)


@dataclass(frozen=True)
class SharedBlockContrastCertification:
    contrast: str
    category: str
    robust_positive_group_count: int
    robust_nonpositive_group_count: int
    uncertain_group_count: int
    unavailable_group_count: int
    groups: tuple[SharedBlockGainCell, ...]

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
class SharedBlockGainCertification:
    group_count: int
    contrast_count: int
    shared_block_count: int
    familywise_confidence_level: float
    bootstrap_draws: int
    seed: int
    minimum_shared_blocks: int
    gain_tolerance: float
    max_t_critical_value: float | None
    cell_count: int
    estimable_cell_count: int
    all_cells_estimable: bool
    exact_shared_block_support_validated: bool
    same_block_draw_shared_across_all_groups_and_contrasts: bool
    validation_group_independence_assumed: bool
    shared_block_exchangeability_assumed: bool
    contrasts: tuple[SharedBlockContrastCertification, ...]

    def as_dict(self) -> dict[str, object]:
        return {
            "group_count": self.group_count,
            "contrast_count": self.contrast_count,
            "shared_block_count": self.shared_block_count,
            "familywise_confidence_level": self.familywise_confidence_level,
            "bootstrap_draws": self.bootstrap_draws,
            "seed": self.seed,
            "minimum_shared_blocks": self.minimum_shared_blocks,
            "gain_tolerance": self.gain_tolerance,
            "max_t_critical_value": self.max_t_critical_value,
            "cell_count": self.cell_count,
            "estimable_cell_count": self.estimable_cell_count,
            "all_cells_estimable": self.all_cells_estimable,
            "exact_shared_block_support_validated": self.exact_shared_block_support_validated,
            "same_block_draw_shared_across_all_groups_and_contrasts": self.same_block_draw_shared_across_all_groups_and_contrasts,
            "validation_group_independence_assumed": self.validation_group_independence_assumed,
            "shared_block_exchangeability_assumed": self.shared_block_exchangeability_assumed,
            "contrasts": [row.as_dict() for row in self.contrasts],
        }


def _labels(values: Sequence[object], n: int, *, name: str) -> np.ndarray:
    result = np.asarray(list(values), dtype=object)
    if result.shape != (n,):
        raise ValueError(f"{name} must contain one value per gain row")
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
        raise ValueError("sample_weight must contain one value per gain row")
    if not np.isfinite(result).all() or np.any(result < 0) or not np.any(result > 0):
        raise ValueError(
            "sample_weight must be finite, non-negative and positive in total"
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


def _canonical(values: Sequence[object]) -> tuple[object, ...]:
    return tuple(
        sorted(
            set(values),
            key=lambda value: (type(value).__name__, repr(value)),
        )
    )


def _shared_draws(seed: int, draws: int, block_count: int) -> np.ndarray:
    digest = hashlib.sha256(
        f"{seed}|shared-block-gain-certification|paired".encode("utf-8")
    ).digest()
    local_seed = int.from_bytes(digest[:8], "little", signed=False)
    return np.random.default_rng(local_seed).integers(
        0, block_count, size=(draws, block_count)
    )


def certify_shared_block_gains(
    row_gain: Sequence[Sequence[float]] | np.ndarray,
    groups: Sequence[object],
    shared_blocks: Sequence[object],
    *,
    contrast_names: Sequence[object] | None = None,
    sample_weight: Sequence[float] | None = None,
    familywise_confidence_level: float = 0.95,
    bootstrap_draws: int = 4000,
    seed: int = 20260914,
    minimum_shared_blocks: int = 8,
    gain_tolerance: float = 0.0,
) -> SharedBlockGainCertification:
    """Certify group-by-contrast gains under a paired shared-block design.

    Every group must contain exactly the same set of positive-mass shared block
    IDs. The same sampled block sequence is reused across all groups and all
    gain contrasts. Cells containing non-finite positive-weight row gains are
    marked unavailable and cannot be rescued by other groups or contrasts.
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
    block = _labels(shared_blocks, n, name="shared_blocks")
    weight = _weights(sample_weight, n)

    if (
        not math.isfinite(familywise_confidence_level)
        or not 0.0 < familywise_confidence_level < 1.0
    ):
        raise ValueError(
            "familywise_confidence_level must lie strictly between zero and one"
        )
    if (
        isinstance(bootstrap_draws, bool)
        or not isinstance(bootstrap_draws, (int, np.integer))
        or int(bootstrap_draws) < 500
    ):
        raise ValueError("bootstrap_draws must be an integer >= 500")
    if (
        isinstance(seed, bool)
        or not isinstance(seed, (int, np.integer))
        or int(seed) < 0
    ):
        raise ValueError("seed must be a non-negative integer")
    if (
        isinstance(minimum_shared_blocks, bool)
        or not isinstance(minimum_shared_blocks, (int, np.integer))
        or int(minimum_shared_blocks) < 2
    ):
        raise ValueError("minimum_shared_blocks must be an integer >= 2")
    if not math.isfinite(gain_tolerance) or gain_tolerance < 0:
        raise ValueError("gain_tolerance must be finite and non-negative")

    bootstrap_draws = int(bootstrap_draws)
    seed = int(seed)
    minimum_shared_blocks = int(minimum_shared_blocks)
    group_order = _canonical(group.tolist())

    positive_support: dict[object, tuple[object, ...]] = {}
    for group_value in group_order:
        mask = group == group_value
        local_positive = weight[mask] > 0
        if not np.any(local_positive):
            raise ValueError(f"group {group_value!r} has zero total positive weight")
        local_blocks = block[mask][local_positive].tolist()
        positive_support[group_value] = _canonical(local_blocks)

    reference_support = positive_support[group_order[0]]
    for group_value in group_order[1:]:
        if positive_support[group_value] != reference_support:
            raise ValueError(
                "shared-block certification requires identical positive-mass "
                "block support in every group; "
                f"reference={reference_support!r}, "
                f"group={group_value!r}, support={positive_support[group_value]!r}"
            )
    block_order = reference_support
    enough_blocks = len(block_order) >= minimum_shared_blocks

    group_count = len(group_order)
    block_count = len(block_order)
    block_weight = np.empty((group_count, block_count), dtype=float)
    block_numerator = np.zeros(
        (group_count, block_count, contrast_count), dtype=float
    )
    finite_cell = np.ones((group_count, contrast_count), dtype=bool)
    row_count = np.empty(group_count, dtype=int)

    for group_index, group_value in enumerate(group_order):
        group_mask = group == group_value
        row_count[group_index] = int(np.count_nonzero(group_mask))
        local_gain = gain[group_mask]
        local_weight = weight[group_mask]
        local_block = block[group_mask]
        local_positive = local_weight > 0
        finite_cell[group_index, :] = np.all(
            np.isfinite(local_gain[local_positive]), axis=0
        )

        for block_index, block_value in enumerate(block_order):
            block_mask = local_block == block_value
            bw = float(np.sum(local_weight[block_mask]))
            if bw <= 0:
                raise ValueError(
                    f"group {group_value!r} shared block {block_value!r} "
                    "must have positive total weight"
                )
            block_weight[group_index, block_index] = bw
            if np.any(finite_cell[group_index]):
                weighted = (
                    local_gain[block_mask][:, finite_cell[group_index]]
                    * local_weight[block_mask][:, None]
                )
                block_numerator[
                    group_index, block_index, finite_cell[group_index]
                ] = np.sum(weighted, axis=0)

    total_weight = np.sum(block_weight, axis=1)
    point = np.full((group_count, contrast_count), np.nan, dtype=float)
    for group_index in range(group_count):
        if np.any(finite_cell[group_index]):
            point[group_index, finite_cell[group_index]] = (
                np.sum(
                    block_numerator[
                        group_index, :, finite_cell[group_index]
                    ],
                    axis=0,
                )
                / total_weight[group_index]
            )

    sampled = _shared_draws(seed, bootstrap_draws, block_count)
    denominator = np.stack(
        [
            np.sum(block_weight[group_index, sampled], axis=1)
            for group_index in range(group_count)
        ],
        axis=1,
    )

    records: list[list[dict[str, object]]] = [
        [] for _ in range(contrast_count)
    ]
    eligible: list[tuple[int, int]] = []
    sample_columns: list[np.ndarray] = []
    sample_points: list[float] = []
    sample_ses: list[float] = []

    for contrast_index, contrast in enumerate(names):
        for group_index, group_value in enumerate(group_order):
            finite = bool(finite_cell[group_index, contrast_index])
            estimable = bool(finite and enough_blocks)
            record = {
                "group": group_value,
                "contrast": contrast,
                "row_count": int(row_count[group_index]),
                "shared_block_count": block_count,
                "total_weight": float(total_weight[group_index]),
                "mean_gain": (
                    float(point[group_index, contrast_index])
                    if finite
                    else float("-inf")
                ),
                "bootstrap_standard_error": None,
                "lower_bound": None,
                "upper_bound": None,
                "status": "unavailable",
                "estimable": estimable,
            }
            record_index = len(records[contrast_index])
            records[contrast_index].append(record)
            if estimable:
                numerator = np.sum(
                    block_numerator[
                        group_index, sampled, contrast_index
                    ],
                    axis=1,
                )
                samples = numerator / denominator[:, group_index]
                if not np.isfinite(samples).all():
                    raise ValueError(
                        "shared-block resampling produced non-finite gain samples"
                    )
                se = float(np.std(samples, ddof=1))
                record["bootstrap_standard_error"] = se
                eligible.append((contrast_index, record_index))
                sample_columns.append(samples)
                sample_points.append(float(point[group_index, contrast_index]))
                sample_ses.append(se)

    critical: float | None = None
    if sample_columns:
        sample_matrix = np.column_stack(sample_columns)
        points = np.asarray(sample_points, dtype=float)
        ses = np.asarray(sample_ses, dtype=float)
        standardized = np.zeros_like(sample_matrix)
        nonzero = ses > 1e-15
        standardized[:, nonzero] = (
            np.abs(sample_matrix[:, nonzero] - points[nonzero])
            / ses[nonzero]
        )
        critical = float(
            np.quantile(
                np.max(standardized, axis=1),
                familywise_confidence_level,
            )
        )
        for column, (contrast_index, record_index) in enumerate(eligible):
            lower = float(points[column] - critical * ses[column])
            upper = float(points[column] + critical * ses[column])
            records[contrast_index][record_index]["lower_bound"] = lower
            records[contrast_index][record_index]["upper_bound"] = upper
            records[contrast_index][record_index]["status"] = _cell_status(
                lower, upper, tolerance=gain_tolerance
            )

    contrast_rows: list[SharedBlockContrastCertification] = []
    for contrast_index, contrast in enumerate(names):
        cells = tuple(
            SharedBlockGainCell(**record)
            for record in records[contrast_index]
        )
        statuses = [cell.status for cell in cells]
        category = _step_category(statuses)
        contrast_rows.append(
            SharedBlockContrastCertification(
                contrast=contrast,
                category=category,
                robust_positive_group_count=statuses.count("robust_positive"),
                robust_nonpositive_group_count=statuses.count(
                    "robust_nonpositive"
                ),
                uncertain_group_count=statuses.count("uncertain"),
                unavailable_group_count=statuses.count("unavailable"),
                groups=cells,
            )
        )

    cell_count = group_count * contrast_count
    estimable_cell_count = len(eligible)
    return SharedBlockGainCertification(
        group_count=group_count,
        contrast_count=contrast_count,
        shared_block_count=block_count,
        familywise_confidence_level=float(familywise_confidence_level),
        bootstrap_draws=bootstrap_draws,
        seed=seed,
        minimum_shared_blocks=minimum_shared_blocks,
        gain_tolerance=float(gain_tolerance),
        max_t_critical_value=critical,
        cell_count=cell_count,
        estimable_cell_count=estimable_cell_count,
        all_cells_estimable=bool(estimable_cell_count == cell_count),
        exact_shared_block_support_validated=True,
        same_block_draw_shared_across_all_groups_and_contrasts=True,
        validation_group_independence_assumed=False,
        shared_block_exchangeability_assumed=True,
        contrasts=tuple(contrast_rows),
    )
