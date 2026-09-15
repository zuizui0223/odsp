"""One-sided familywise bootstrap-t for paired shared validation blocks.

This route is for a predeclared directional claim: every estimable group x
contrast gain must exceed a non-negative tolerance. Every group must have exactly
the same positive-mass shared-block support. One sampled shared-block sequence is
reused across every group and contrast, preserving paired cross-group and
cross-contrast covariance. The cluster ratio studentizer is recomputed inside
every bootstrap replicate.

Use the independent-group positive-transfer route when groups do not share a
common exchangeable block set. Use the two-sided paired v2 route when positive
and negative departures are both simultaneous inferential targets.
"""
from __future__ import annotations

from dataclasses import asdict, dataclass
import math
from typing import Sequence

import numpy as np

from .bootstrap_t import bootstrap_ratio_mean_and_cluster_se, ratio_mean_and_cluster_se
from .positive_transfer_bootstrap_t import (
    _directional_category,
    one_sided_lower_bounds,
    one_sided_lower_max_t_critical_value,
)
from .shared_block_certification_v2 import (
    _canonical,
    _contrast_names,
    _labels,
    _shared_draws,
    _weights,
)


@dataclass(frozen=True)
class SharedBlockPositiveCell:
    group: object
    contrast: str
    row_count: int
    shared_block_count: int
    total_weight: float
    mean_gain: float
    bootstrap_standard_error: float | None
    studentizing_standard_error: float | None
    lower_bound: float | None
    status: str
    estimable: bool

    def as_dict(self) -> dict[str, object]:
        return asdict(self)


@dataclass(frozen=True)
class SharedBlockPositiveContrast:
    contrast: str
    category: str
    robust_positive_group_count: int
    not_robust_positive_group_count: int
    unavailable_group_count: int
    groups: tuple[SharedBlockPositiveCell, ...]

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
class SharedBlockPositiveCertification:
    schema_version: int
    method: str
    alternative: str
    group_count: int
    contrast_count: int
    shared_block_count: int
    familywise_lower_confidence_level: float
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
    contrasts: tuple[SharedBlockPositiveContrast, ...]

    def as_dict(self) -> dict[str, object]:
        payload = asdict(self)
        payload["contrasts"] = [row.as_dict() for row in self.contrasts]
        return payload


def certify_shared_block_positive_gains_v2(
    row_gain: Sequence[Sequence[float]] | np.ndarray,
    groups: Sequence[object],
    shared_blocks: Sequence[object],
    *,
    contrast_names: Sequence[object] | None = None,
    sample_weight: Sequence[float] | None = None,
    familywise_lower_confidence_level: float = 0.95,
    bootstrap_draws: int = 4000,
    seed: int = 20260915,
    minimum_shared_blocks: int = 8,
    gain_tolerance: float = 0.0,
) -> SharedBlockPositiveCertification:
    """Certify directional positive gains in a paired shared-block design."""

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
        not math.isfinite(familywise_lower_confidence_level)
        or not 0.0 < familywise_lower_confidence_level < 1.0
    ):
        raise ValueError(
            "familywise_lower_confidence_level must lie strictly between zero and one"
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
        positive = weight[mask] > 0
        if not np.any(positive):
            raise ValueError(f"group {group_value!r} has zero total positive weight")
        positive_support[group_value] = _canonical(block[mask][positive].tolist())

    reference_support = positive_support[group_order[0]]
    for group_value in group_order[1:]:
        if positive_support[group_value] != reference_support:
            raise ValueError(
                "paired one-sided bootstrap-t requires identical positive-mass block "
                "support in every group; "
                f"reference={reference_support!r}, group={group_value!r}, "
                f"support={positive_support[group_value]!r}"
            )

    block_order = reference_support
    block_count = len(block_order)
    enough_blocks = block_count >= minimum_shared_blocks
    group_count = len(group_order)
    block_weight = np.empty((group_count, block_count), dtype=float)
    block_numerator = np.zeros((group_count, block_count, contrast_count), dtype=float)
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
            mass = float(np.sum(local_weight[block_mask]))
            if mass <= 0:
                raise ValueError(
                    f"group {group_value!r} shared block {block_value!r} must have positive total weight"
                )
            block_weight[group_index, block_index] = mass
            selected = finite_cell[group_index]
            if np.any(selected):
                block_numerator[group_index, block_index, selected] = np.sum(
                    local_gain[block_mask][:, selected]
                    * local_weight[block_mask][:, None],
                    axis=0,
                )

    sampled = _shared_draws(seed, bootstrap_draws, block_count) if enough_blocks else None
    point = np.full((group_count, contrast_count), np.nan, dtype=float)
    point_se = np.full((group_count, contrast_count), np.nan, dtype=float)
    bootstrap_mean: dict[tuple[int, int], np.ndarray] = {}
    bootstrap_se: dict[tuple[int, int], np.ndarray] = {}
    bootstrap_sd: dict[tuple[int, int], float] = {}

    for group_index in range(group_count):
        selected = finite_cell[group_index]
        if not np.any(selected):
            continue
        denominator = float(np.sum(block_weight[group_index]))
        point[group_index, selected] = (
            np.sum(block_numerator[group_index][:, selected], axis=0) / denominator
        )
        if block_count >= 2:
            local_point, local_se = ratio_mean_and_cluster_se(
                block_numerator[group_index][:, selected],
                block_weight[group_index],
            )
            if not np.allclose(
                local_point, point[group_index, selected], rtol=0.0, atol=1e-12
            ):
                raise AssertionError("paired ratio point estimate disagrees with aggregate mean")
            point_se[group_index, selected] = local_se
        if enough_blocks:
            assert sampled is not None
            local_boot_mean, local_boot_se = bootstrap_ratio_mean_and_cluster_se(
                block_numerator[group_index][:, selected],
                block_weight[group_index],
                sampled,
            )
            for local_index, contrast_index in enumerate(np.flatnonzero(selected)):
                key = (group_index, int(contrast_index))
                bootstrap_mean[key] = local_boot_mean[:, local_index]
                bootstrap_se[key] = local_boot_se[:, local_index]
                bootstrap_sd[key] = float(np.std(local_boot_mean[:, local_index], ddof=1))

    records: list[list[dict[str, object]]] = [[] for _ in range(contrast_count)]
    eligible: list[tuple[int, int, int, int]] = []
    cell_boot_mean: list[np.ndarray] = []
    cell_boot_se: list[np.ndarray] = []
    cell_point: list[float] = []
    cell_point_se: list[float] = []

    for contrast_index, contrast in enumerate(names):
        for group_index, group_value in enumerate(group_order):
            finite = bool(finite_cell[group_index, contrast_index])
            estimable = bool(finite and enough_blocks)
            key = (group_index, contrast_index)
            record: dict[str, object] = {
                "group": group_value,
                "contrast": contrast,
                "row_count": int(row_count[group_index]),
                "shared_block_count": block_count,
                "total_weight": float(np.sum(block_weight[group_index])),
                "mean_gain": float(point[group_index, contrast_index]) if finite else float("-inf"),
                "bootstrap_standard_error": bootstrap_sd.get(key) if finite else None,
                "studentizing_standard_error": (
                    float(point_se[group_index, contrast_index])
                    if finite and block_count >= 2
                    else None
                ),
                "lower_bound": None,
                "status": "unavailable",
                "estimable": estimable,
            }
            record_index = len(records[contrast_index])
            records[contrast_index].append(record)
            if estimable:
                eligible.append((contrast_index, record_index, group_index, contrast_index))
                cell_boot_mean.append(bootstrap_mean[key])
                cell_boot_se.append(bootstrap_se[key])
                cell_point.append(float(point[group_index, contrast_index]))
                cell_point_se.append(float(point_se[group_index, contrast_index]))

    critical: float | None = None
    if cell_boot_mean:
        mean_matrix = np.column_stack(cell_boot_mean)
        se_matrix = np.column_stack(cell_boot_se)
        point_vector = np.asarray(cell_point, dtype=float)
        point_se_vector = np.asarray(cell_point_se, dtype=float)
        critical = one_sided_lower_max_t_critical_value(
            mean_matrix,
            se_matrix,
            point_vector,
            confidence_level=familywise_lower_confidence_level,
        )
        lower = one_sided_lower_bounds(point_vector, point_se_vector, critical)
        for column, (contrast_index, record_index, _, _) in enumerate(eligible):
            lo = float(lower[column])
            records[contrast_index][record_index]["lower_bound"] = lo
            records[contrast_index][record_index]["status"] = (
                "robust_positive" if lo > gain_tolerance else "not_robust_positive"
            )

    contrast_rows: list[SharedBlockPositiveContrast] = []
    for contrast_index, contrast in enumerate(names):
        cells = tuple(SharedBlockPositiveCell(**record) for record in records[contrast_index])
        statuses = [cell.status for cell in cells]
        contrast_rows.append(
            SharedBlockPositiveContrast(
                contrast=contrast,
                category=_directional_category(statuses),
                robust_positive_group_count=statuses.count("robust_positive"),
                not_robust_positive_group_count=statuses.count("not_robust_positive"),
                unavailable_group_count=statuses.count("unavailable"),
                groups=cells,
            )
        )

    cell_count = group_count * contrast_count
    return SharedBlockPositiveCertification(
        schema_version=1,
        method="paired_one_sided_replicate_studentized_cluster_ratio_max_t",
        alternative="greater",
        group_count=group_count,
        contrast_count=contrast_count,
        shared_block_count=block_count,
        familywise_lower_confidence_level=float(familywise_lower_confidence_level),
        bootstrap_draws=bootstrap_draws,
        seed=seed,
        minimum_shared_blocks=minimum_shared_blocks,
        gain_tolerance=float(gain_tolerance),
        bootstrap_t_critical_value=critical,
        cell_count=cell_count,
        estimable_cell_count=len(eligible),
        all_cells_estimable=bool(len(eligible) == cell_count),
        exact_shared_block_support_validated=True,
        same_block_draw_shared_across_all_groups_and_contrasts=True,
        replicate_studentization_recomputed=True,
        validation_group_independence_assumed=False,
        shared_block_exchangeability_assumed=True,
        contrasts=tuple(contrast_rows),
    )
