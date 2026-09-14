"""Prospective genuine bootstrap-t for paired cross-group validation blocks.

The historical shared-block certification keeps one sampled block sequence across
all groups and contrasts, preserving paired cross-group covariance, but it uses a
fixed outer-bootstrap scale.  This v2 route preserves the same paired resampling
and additionally recomputes the cluster ratio studentizer inside every bootstrap
replicate.

Historical v1 receipts remain unchanged.  New confirmatory paired-block analyses
should prefer this v2 method.
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
class SharedBlockBootstrapTCell:
    group: object
    contrast: str
    row_count: int
    shared_block_count: int
    total_weight: float
    mean_gain: float
    bootstrap_standard_error: float | None
    studentizing_standard_error: float | None
    lower_bound: float | None
    upper_bound: float | None
    status: str
    estimable: bool

    def as_dict(self) -> dict[str, object]:
        return asdict(self)


@dataclass(frozen=True)
class SharedBlockBootstrapTContrast:
    contrast: str
    category: str
    robust_positive_group_count: int
    robust_nonpositive_group_count: int
    uncertain_group_count: int
    unavailable_group_count: int
    groups: tuple[SharedBlockBootstrapTCell, ...]

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
class SharedBlockBootstrapTCertification:
    schema_version: int
    method: str
    group_count: int
    contrast_count: int
    shared_block_count: int
    familywise_confidence_level: float
    bootstrap_draws: int
    seed: int
    minimum_shared_blocks: int
    gain_tolerance: float
    bootstrap_t_critical_value: float | None
    cell_count: int
    estimable_cell_count: int
    all_cells_estimable: bool
    exact_shared_block_support_validated: bool
    same_block_draw_shared_across_all_groups_and_contrasts: bool
    replicate_studentization_recomputed: bool
    validation_group_independence_assumed: bool
    shared_block_exchangeability_assumed: bool
    legacy_fixed_se_standardization_used: bool
    contrasts: tuple[SharedBlockBootstrapTContrast, ...]

    def as_dict(self) -> dict[str, object]:
        return {
            "schema_version": self.schema_version,
            "method": self.method,
            "group_count": self.group_count,
            "contrast_count": self.contrast_count,
            "shared_block_count": self.shared_block_count,
            "familywise_confidence_level": self.familywise_confidence_level,
            "bootstrap_draws": self.bootstrap_draws,
            "seed": self.seed,
            "minimum_shared_blocks": self.minimum_shared_blocks,
            "gain_tolerance": self.gain_tolerance,
            "bootstrap_t_critical_value": self.bootstrap_t_critical_value,
            "cell_count": self.cell_count,
            "estimable_cell_count": self.estimable_cell_count,
            "all_cells_estimable": self.all_cells_estimable,
            "exact_shared_block_support_validated": self.exact_shared_block_support_validated,
            "same_block_draw_shared_across_all_groups_and_contrasts": self.same_block_draw_shared_across_all_groups_and_contrasts,
            "replicate_studentization_recomputed": self.replicate_studentization_recomputed,
            "validation_group_independence_assumed": self.validation_group_independence_assumed,
            "shared_block_exchangeability_assumed": self.shared_block_exchangeability_assumed,
            "legacy_fixed_se_standardization_used": self.legacy_fixed_se_standardization_used,
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
        f"{seed}|shared-block-bootstrap-t-v2|paired".encode("utf-8")
    ).digest()
    local_seed = int.from_bytes(digest[:8], "little", signed=False)
    return np.random.default_rng(local_seed).integers(
        0,
        block_count,
        size=(draws, block_count),
    )


def certify_shared_block_gains_v2(
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
) -> SharedBlockBootstrapTCertification:
    """Certify paired group-by-contrast gains using replicate-specific bootstrap-t.

    Every group must contain exactly the same set of positive-mass shared block
    IDs.  One sampled block sequence is reused across all groups and contrasts in
    every draw.  This preserves cross-group and cross-contrast covariance caused
    by the paired validation design while using a genuine replicate-specific
    cluster studentizer.
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

    if not math.isfinite(familywise_confidence_level) or not 0 < familywise_confidence_level < 1:
        raise ValueError(
            "familywise_confidence_level must lie strictly between zero and one"
        )
    if isinstance(bootstrap_draws, bool) or not isinstance(bootstrap_draws, int) or bootstrap_draws < 500:
        raise ValueError("bootstrap_draws must be an integer >= 500")
    if isinstance(seed, bool) or not isinstance(seed, int) or seed < 0:
        raise ValueError("seed must be a non-negative integer")
    if (
        isinstance(minimum_shared_blocks, bool)
        or not isinstance(minimum_shared_blocks, int)
        or minimum_shared_blocks < 2
    ):
        raise ValueError("minimum_shared_blocks must be an integer >= 2")
    if not math.isfinite(gain_tolerance) or gain_tolerance < 0:
        raise ValueError("gain_tolerance must be finite and non-negative")

    group_order = _canonical(group.tolist())
    positive_support: dict[object, tuple[object, ...]] = {}
    for group_value in group_order:
        mask = group == group_value
        local_positive = weight[mask] > 0
        if not np.any(local_positive):
            raise ValueError(f"group {group_value!r} has zero total positive weight")
        positive_support[group_value] = _canonical(
            block[mask][local_positive].tolist()
        )

    reference_support = positive_support[group_order[0]]
    for group_value in group_order[1:]:
        if positive_support[group_value] != reference_support:
            raise ValueError(
                "shared-block bootstrap-t requires identical positive-mass block "
                "support in every group; "
                f"reference={reference_support!r}, group={group_value!r}, "
                f"support={positive_support[group_value]!r}"
            )
    block_order = reference_support
    block_count = len(block_order)
    enough_blocks = block_count >= minimum_shared_blocks
    group_count = len(group_order)

    block_weight = np.empty((group_count, block_count), dtype=float)
    block_numerator = np.zeros(
        (group_count, block_count, contrast_count),
        dtype=float,
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
            np.isfinite(local_gain[local_positive]),
            axis=0,
        )
        for block_index, block_value in enumerate(block_order):
            block_mask = local_block == block_value
            mass = float(np.sum(local_weight[block_mask]))
            if mass <= 0:
                raise ValueError(
                    f"group {group_value!r} shared block {block_value!r} must have positive total weight"
                )
            block_weight[group_index, block_index] = mass
            if np.any(finite_cell[group_index]):
                selected = finite_cell[group_index]
                weighted = (
                    local_gain[block_mask][:, selected]
                    * local_weight[block_mask][:, None]
                )
                block_numerator[group_index, block_index, selected] = np.sum(
                    weighted,
                    axis=0,
                )

    sampled = _shared_draws(seed, bootstrap_draws, block_count)
    point = np.full((group_count, contrast_count), np.nan, dtype=float)
    point_se = np.full((group_count, contrast_count), np.nan, dtype=float)
    bootstrap_mean: dict[tuple[int, int], np.ndarray] = {}
    bootstrap_se: dict[tuple[int, int], np.ndarray] = {}
    bootstrap_sd: dict[tuple[int, int], float] = {}

    for group_index in range(group_count):
        selected = finite_cell[group_index]
        if not np.any(selected):
            continue
        local_point, local_se = ratio_mean_and_cluster_se(
            block_numerator[group_index][:, selected],
            block_weight[group_index],
        )
        point[group_index, selected] = local_point
        point_se[group_index, selected] = local_se
        local_boot_mean, local_boot_se = bootstrap_ratio_mean_and_cluster_se(
            block_numerator[group_index][:, selected],
            block_weight[group_index],
            sampled,
        )
        selected_indices = np.flatnonzero(selected)
        for local_index, contrast_index in enumerate(selected_indices):
            bootstrap_mean[(group_index, int(contrast_index))] = local_boot_mean[:, local_index]
            bootstrap_se[(group_index, int(contrast_index))] = local_boot_se[:, local_index]
            bootstrap_sd[(group_index, int(contrast_index))] = float(
                np.std(local_boot_mean[:, local_index], ddof=1)
            )

    records: list[list[dict[str, object]]] = [
        [] for _ in range(contrast_count)
    ]
    eligible: list[tuple[int, int, int, int]] = []
    cell_boot_mean: list[np.ndarray] = []
    cell_boot_se: list[np.ndarray] = []
    cell_point: list[float] = []
    cell_point_se: list[float] = []

    for contrast_index, contrast in enumerate(names):
        for group_index, group_value in enumerate(group_order):
            finite = bool(finite_cell[group_index, contrast_index])
            estimable = bool(finite and enough_blocks)
            record: dict[str, object] = {
                "group": group_value,
                "contrast": contrast,
                "row_count": int(row_count[group_index]),
                "shared_block_count": block_count,
                "total_weight": float(np.sum(block_weight[group_index])),
                "mean_gain": (
                    float(point[group_index, contrast_index])
                    if finite
                    else float("-inf")
                ),
                "bootstrap_standard_error": (
                    bootstrap_sd[(group_index, contrast_index)]
                    if finite
                    else None
                ),
                "studentizing_standard_error": (
                    float(point_se[group_index, contrast_index])
                    if finite
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
                eligible.append(
                    (contrast_index, record_index, group_index, contrast_index)
                )
                cell_boot_mean.append(
                    bootstrap_mean[(group_index, contrast_index)]
                )
                cell_boot_se.append(
                    bootstrap_se[(group_index, contrast_index)]
                )
                cell_point.append(float(point[group_index, contrast_index]))
                cell_point_se.append(float(point_se[group_index, contrast_index]))

    critical: float | None = None
    if cell_boot_mean:
        mean_matrix = np.column_stack(cell_boot_mean)
        se_matrix = np.column_stack(cell_boot_se)
        point_vector = np.asarray(cell_point, dtype=float)
        point_se_vector = np.asarray(cell_point_se, dtype=float)
        critical = studentized_max_t_critical_value(
            mean_matrix,
            se_matrix,
            point_vector,
            confidence_level=familywise_confidence_level,
        )
        lower, upper = simultaneous_bootstrap_t_bounds(
            point_vector,
            point_se_vector,
            critical,
        )
        for column, (contrast_index, record_index, _, _) in enumerate(eligible):
            lo = float(lower[column])
            hi = float(upper[column])
            records[contrast_index][record_index]["lower_bound"] = lo
            records[contrast_index][record_index]["upper_bound"] = hi
            records[contrast_index][record_index]["status"] = _cell_status(
                lo,
                hi,
                tolerance=gain_tolerance,
            )

    contrast_rows: list[SharedBlockBootstrapTContrast] = []
    for contrast_index, contrast in enumerate(names):
        cells = tuple(
            SharedBlockBootstrapTCell(**record)
            for record in records[contrast_index]
        )
        statuses = [cell.status for cell in cells]
        category = _step_category(statuses)
        contrast_rows.append(
            SharedBlockBootstrapTContrast(
                contrast=contrast,
                category=category,
                robust_positive_group_count=statuses.count("robust_positive"),
                robust_nonpositive_group_count=statuses.count("robust_nonpositive"),
                uncertain_group_count=statuses.count("uncertain"),
                unavailable_group_count=statuses.count("unavailable"),
                groups=cells,
            )
        )

    cell_count = group_count * contrast_count
    estimable_count = len(eligible)
    return SharedBlockBootstrapTCertification(
        schema_version=2,
        method="paired_shared_block_replicate_studentized_bootstrap_t_v2",
        group_count=group_count,
        contrast_count=contrast_count,
        shared_block_count=block_count,
        familywise_confidence_level=float(familywise_confidence_level),
        bootstrap_draws=bootstrap_draws,
        seed=seed,
        minimum_shared_blocks=minimum_shared_blocks,
        gain_tolerance=float(gain_tolerance),
        bootstrap_t_critical_value=critical,
        cell_count=cell_count,
        estimable_cell_count=estimable_count,
        all_cells_estimable=bool(estimable_count == cell_count),
        exact_shared_block_support_validated=True,
        same_block_draw_shared_across_all_groups_and_contrasts=True,
        replicate_studentization_recomputed=True,
        validation_group_independence_assumed=False,
        shared_block_exchangeability_assumed=True,
        legacy_fixed_se_standardization_used=False,
        contrasts=tuple(contrast_rows),
    )
