"""Known-truth benchmark for block-aware uncertainty in transfer gains."""
from __future__ import annotations

import numpy as np

from .block_aware_transfer_uncertainty import audit_block_aware_transfer_uncertainty


def _grouped_block_rows(block_means_by_group: list[np.ndarray], rows_per_block: int):
    gains: list[float] = []
    groups: list[str] = []
    blocks: list[str] = []
    for group_index, block_means in enumerate(block_means_by_group):
        group_id = f"group-{group_index + 1:02d}"
        for block_index, block_mean in enumerate(block_means):
            block_id = f"{group_id}-block-{block_index + 1:02d}"
            gains.extend([float(block_mean)] * rows_per_block)
            groups.extend([group_id] * rows_per_block)
            blocks.extend([block_id] * rows_per_block)
    return np.asarray(gains, dtype=float), tuple(groups), tuple(blocks)


def run_block_aware_transfer_uncertainty_benchmark(
    *,
    seed: int = 20260906,
    bootstrap_draws: int = 2000,
    confidence_level: float = 0.95,
) -> dict[str, object]:
    group_count = 6
    blocks_per_group = 20
    rows_per_block = 25

    strong_blocks = [
        0.25 + np.linspace(-0.03, 0.03, blocks_per_group) + 0.002 * (group_index - 2.5)
        for group_index in range(group_count)
    ]
    strong_gain, strong_groups, strong_block_ids = _grouped_block_rows(strong_blocks, rows_per_block)
    strong = audit_block_aware_transfer_uncertainty(
        strong_gain,
        strong_groups,
        blocks=strong_block_ids,
        confidence_level=confidence_level,
        bootstrap_draws=bootstrap_draws,
        seed=seed,
        minimum_blocks_per_group=8,
    )

    weak_pattern = np.asarray([
        -0.25, -0.20, -0.15, -0.10, -0.08, -0.06, -0.04, -0.02, 0.00, 0.02,
        0.04, 0.06, 0.08, 0.10, 0.12, 0.14, 0.16, 0.18, 0.20, 0.22,
    ])
    weak_blocks = [weak_pattern + 0.001 * group_index for group_index in range(group_count)]
    weak_gain, weak_groups, weak_block_ids = _grouped_block_rows(weak_blocks, rows_per_block)
    weak = audit_block_aware_transfer_uncertainty(
        weak_gain,
        weak_groups,
        blocks=weak_block_ids,
        confidence_level=confidence_level,
        bootstrap_draws=bootstrap_draws,
        seed=seed,
        minimum_blocks_per_group=8,
    )

    negative_blocks = [
        -0.25 + np.linspace(-0.03, 0.03, blocks_per_group) + 0.002 * (group_index - 2.5)
        for group_index in range(group_count)
    ]
    negative_gain, negative_groups, negative_block_ids = _grouped_block_rows(negative_blocks, rows_per_block)
    negative = audit_block_aware_transfer_uncertainty(
        negative_gain,
        negative_groups,
        blocks=negative_block_ids,
        confidence_level=confidence_level,
        bootstrap_draws=bootstrap_draws,
        seed=seed,
        minimum_blocks_per_group=8,
    )

    pseudo_block_means = np.asarray([-0.20, -0.10, 0.00, 0.05, 0.10, 0.15, 0.20, 0.25])
    pseudo_gain = np.repeat(pseudo_block_means, 100)
    pseudo_groups = tuple(["pseudo"] * pseudo_gain.size)
    pseudo_blocks = tuple(
        block_id
        for block_index in range(pseudo_block_means.size)
        for block_id in [f"pseudo-block-{block_index + 1}"] * 100
    )
    pseudo_row = audit_block_aware_transfer_uncertainty(
        pseudo_gain,
        pseudo_groups,
        blocks=None,
        confidence_level=confidence_level,
        bootstrap_draws=bootstrap_draws,
        seed=seed,
        minimum_blocks_per_group=8,
    )
    pseudo_block = audit_block_aware_transfer_uncertainty(
        pseudo_gain,
        pseudo_groups,
        blocks=pseudo_blocks,
        confidence_level=confidence_level,
        bootstrap_draws=bootstrap_draws,
        seed=seed,
        minimum_blocks_per_group=8,
    )

    insufficient_gain = np.repeat(np.asarray([0.2, 0.25, 0.3, 0.35]), 50)
    insufficient_groups = tuple(["few-blocks"] * insufficient_gain.size)
    insufficient_blocks = tuple(
        block_id
        for block_index in range(4)
        for block_id in [f"few-{block_index + 1}"] * 50
    )
    insufficient = audit_block_aware_transfer_uncertainty(
        insufficient_gain,
        insufficient_groups,
        blocks=insufficient_blocks,
        confidence_level=confidence_level,
        bootstrap_draws=bootstrap_draws,
        seed=seed,
        minimum_blocks_per_group=8,
    )

    scaled = audit_block_aware_transfer_uncertainty(
        strong_gain * 100.0,
        strong_groups,
        blocks=strong_block_ids,
        confidence_level=confidence_level,
        bootstrap_draws=bootstrap_draws,
        seed=seed,
        minimum_blocks_per_group=8,
    )
    reverse = np.arange(strong_gain.size - 1, -1, -1)
    reordered = audit_block_aware_transfer_uncertainty(
        strong_gain[reverse],
        tuple(strong_groups[index] for index in reverse),
        blocks=tuple(strong_block_ids[index] for index in reverse),
        confidence_level=confidence_level,
        bootstrap_draws=bootstrap_draws,
        seed=seed,
        minimum_blocks_per_group=8,
    )

    pseudo_row_lower = pseudo_row.groups[0].lower_bound
    pseudo_block_lower = pseudo_block.groups[0].lower_bound
    obligations = {
        "strong_point_generalizing": strong.point_transfer_category == "generalizing",
        "strong_robust_generalizing": strong.robust_transfer_category == "robust_generalizing",
        "strong_all_lower_positive": all(row.lower_bound is not None and row.lower_bound > 0.0 for row in strong.groups),
        "weak_point_generalizing": weak.point_transfer_category == "generalizing",
        "weak_robust_uncertain": weak.robust_transfer_category == "uncertain",
        "negative_point_non_generalizing": negative.point_transfer_category == "non_generalizing",
        "negative_robust_non_generalizing": negative.robust_transfer_category == "robust_non_generalizing",
        "pseudoreplication_row_lower_positive": pseudo_row_lower is not None and pseudo_row_lower > 0.0,
        "pseudoreplication_block_lower_crosses_zero": pseudo_block_lower is not None and pseudo_block_lower <= 0.0,
        "pseudoreplication_block_uncertain": pseudo_block.robust_transfer_category == "uncertain",
        "insufficient_blocks_unavailable": insufficient.robust_transfer_category == "unavailable",
        "positive_scale_category_invariant": scaled.robust_transfer_category == strong.robust_transfer_category,
        "group_order_category_invariant": reordered.robust_transfer_category == strong.robust_transfer_category,
        "no_aggregate_confidence_score": all(
            audit.aggregate_confidence_score_emitted is False
            for audit in (strong, weak, negative, pseudo_row, pseudo_block, insufficient)
        ),
    }

    return {
        "seed": int(seed),
        "bootstrap_draws": int(bootstrap_draws),
        "confidence_level": float(confidence_level),
        "group_count": group_count,
        "blocks_per_group": blocks_per_group,
        "rows_per_block": rows_per_block,
        "strong_positive": strong.as_dict(),
        "weak_positive": weak.as_dict(),
        "negative": negative.as_dict(),
        "pseudoreplication_row_mode": pseudo_row.as_dict(),
        "pseudoreplication_block_mode": pseudo_block.as_dict(),
        "too_few_blocks": insufficient.as_dict(),
        "positive_scaled_strong": scaled.as_dict(),
        "group_reordered_strong": reordered.as_dict(),
        "checks": [{"name": name, "passed": bool(passed)} for name, passed in obligations.items()],
        "passed": bool(all(obligations.values())),
    }
