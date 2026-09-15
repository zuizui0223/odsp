"""Public paired bootstrap-t v2 API with an explicit insufficient-block guard.

The calibrated two-or-more-block implementation is preserved verbatim in
:mod:`odsp._shared_block_certification_v2_impl`.  This wrapper only intercepts
the degenerate one-shared-block design so it returns an unavailable audit rather
than reaching a cluster-SE calculation that necessarily requires at least two
exchangeable blocks.
"""
from __future__ import annotations

import math
from typing import Sequence

import numpy as np

from ._shared_block_certification_v2_impl import (
    SharedBlockBootstrapTCell,
    SharedBlockBootstrapTContrast,
    SharedBlockBootstrapTCertification,
    _canonical,
    _contrast_names,
    _labels,
    _shared_draws,
    _weights,
    certify_shared_block_gains_v2 as _certify_shared_block_gains_v2_impl,
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
    """Certify paired gains, failing closed when only one shared block exists."""

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

    # The preserved implementation is already calibrated for every admissible
    # design with at least two blocks.  Do not perturb that path.
    if len(reference_support) >= 2:
        return _certify_shared_block_gains_v2_impl(
            gain,
            groups,
            shared_blocks,
            contrast_names=names,
            sample_weight=sample_weight,
            familywise_confidence_level=familywise_confidence_level,
            bootstrap_draws=bootstrap_draws,
            seed=seed,
            minimum_shared_blocks=minimum_shared_blocks,
            gain_tolerance=gain_tolerance,
        )

    # Exactly one positive-mass shared block is scientifically insufficient for
    # a cluster studentizer.  Preserve point summaries but make every cell
    # unavailable and form no bootstrap critical value.
    block_count = len(reference_support)
    contrast_rows: list[SharedBlockBootstrapTContrast] = []
    for contrast_index, contrast in enumerate(names):
        cells: list[SharedBlockBootstrapTCell] = []
        for group_value in group_order:
            mask = group == group_value
            positive = (weight[mask] > 0)
            local_gain = gain[mask, contrast_index]
            local_weight = weight[mask]
            finite = bool(np.all(np.isfinite(local_gain[positive])))
            total_weight = float(np.sum(local_weight[positive]))
            if finite:
                mean_gain = float(
                    np.sum(local_gain[positive] * local_weight[positive]) / total_weight
                )
            else:
                mean_gain = float("-inf")
            cells.append(
                SharedBlockBootstrapTCell(
                    group=group_value,
                    contrast=contrast,
                    row_count=int(np.count_nonzero(mask)),
                    shared_block_count=block_count,
                    total_weight=total_weight,
                    mean_gain=mean_gain,
                    bootstrap_standard_error=None,
                    studentizing_standard_error=None,
                    lower_bound=None,
                    upper_bound=None,
                    status="unavailable",
                    estimable=False,
                )
            )
        contrast_rows.append(
            SharedBlockBootstrapTContrast(
                contrast=contrast,
                category="unavailable",
                robust_positive_group_count=0,
                robust_nonpositive_group_count=0,
                uncertain_group_count=0,
                unavailable_group_count=len(cells),
                groups=tuple(cells),
            )
        )

    cell_count = len(group_order) * contrast_count
    return SharedBlockBootstrapTCertification(
        schema_version=2,
        method="paired_shared_block_replicate_studentized_bootstrap_t_v2",
        group_count=len(group_order),
        contrast_count=contrast_count,
        shared_block_count=block_count,
        familywise_confidence_level=float(familywise_confidence_level),
        bootstrap_draws=bootstrap_draws,
        seed=seed,
        minimum_shared_blocks=minimum_shared_blocks,
        gain_tolerance=float(gain_tolerance),
        bootstrap_t_critical_value=None,
        cell_count=cell_count,
        estimable_cell_count=0,
        all_cells_estimable=False,
        exact_shared_block_support_validated=True,
        same_block_draw_shared_across_all_groups_and_contrasts=True,
        replicate_studentization_recomputed=True,
        validation_group_independence_assumed=False,
        shared_block_exchangeability_assumed=True,
        legacy_fixed_se_standardization_used=False,
        contrasts=tuple(contrast_rows),
    )


__all__ = [
    "SharedBlockBootstrapTCell",
    "SharedBlockBootstrapTContrast",
    "SharedBlockBootstrapTCertification",
    "certify_shared_block_gains_v2",
]
