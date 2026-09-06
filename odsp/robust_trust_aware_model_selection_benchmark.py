"""Known-truth benchmark for robust trust-aware model selection v3."""
from __future__ import annotations

import numpy as np

from .robust_trust_aware_model_selection import (
    compare_robust_trust_candidates,
    evaluate_robust_trust_candidate,
)


def _block_rows(patterns: list[np.ndarray], rows_per_block: int = 25):
    gains: list[float] = []
    groups: list[str] = []
    blocks: list[str] = []
    for gi, pattern in enumerate(patterns):
        gid = f"group-{gi + 1:02d}"
        for bi, value in enumerate(pattern):
            bid = f"{gid}-block-{bi + 1:02d}"
            gains.extend([float(value)] * rows_per_block)
            groups.extend([gid] * rows_per_block)
            blocks.extend([bid] * rows_per_block)
    return np.asarray(gains, dtype=float), tuple(groups), tuple(blocks)


def _coverage(groups: tuple[str, ...], *, failed_group: str | None = None) -> np.ndarray:
    result = np.zeros(len(groups), dtype=bool)
    labels = tuple(dict.fromkeys(groups))
    for gid in labels:
        idx = np.flatnonzero(np.asarray(groups, dtype=object) == gid)
        count = 300 if gid == failed_group else int(round(0.90 * idx.size))
        result[idx[:count]] = True
    return result


def _candidate(
    name: str,
    gains: np.ndarray,
    groups: tuple[str, ...],
    blocks: tuple[str, ...],
    *,
    region_size: float,
    failed_coverage_group: str | None,
    bootstrap_draws: int,
    seed: int,
    minimum_blocks_per_group: int,
):
    marginal = np.full(gains.size, -2.0, dtype=float)
    conditional = marginal + gains
    return evaluate_robust_trust_candidate(
        name,
        conditional,
        marginal,
        _coverage(groups, failed_group=failed_coverage_group),
        groups,
        blocks,
        region_size=np.full(gains.size, region_size),
        target_coverage=0.90,
        coverage_tolerance=0.03,
        confidence_level=0.95,
        bootstrap_draws=bootstrap_draws,
        seed=seed,
        minimum_blocks_per_group=minimum_blocks_per_group,
    )


def run_robust_trust_aware_model_selection_benchmark(
    *,
    seed: int = 20260906,
    bootstrap_draws: int = 2000,
) -> dict[str, object]:
    group_count = 6
    blocks_per_group = 20
    rows_per_block = 25

    strong = [
        0.25 + np.linspace(-0.03, 0.03, blocks_per_group) + 0.002 * (gi - 2.5)
        for gi in range(group_count)
    ]
    balanced_gain, groups, blocks = _block_rows(strong, rows_per_block)

    weak_pattern = np.asarray([
        -0.25, -0.20, -0.15, -0.10, -0.08, -0.06, -0.04, -0.02, 0.00, 0.02,
        0.04, 0.06, 0.08, 0.10, 0.12, 0.14, 0.16, 0.18, 0.20, 0.22,
    ])
    fragile = [weak_pattern + 0.001 * gi for gi in range(group_count)]
    fragile_gain, fragile_groups, fragile_blocks = _block_rows(fragile, rows_per_block)

    broad = [
        0.15 + np.linspace(-0.02, 0.02, blocks_per_group) + 0.001 * (gi - 2.5)
        for gi in range(group_count)
    ]
    broad_gain, broad_groups, broad_blocks = _block_rows(broad, rows_per_block)

    high = [
        0.40 + np.linspace(-0.02, 0.02, blocks_per_group) + 0.001 * (gi - 2.5)
        for gi in range(group_count)
    ]
    coverage_gain, coverage_groups, coverage_blocks = _block_rows(high, rows_per_block)

    # Same positive point signal but only four independent blocks per group.
    few_gain: list[float] = []
    few_groups: list[str] = []
    few_blocks: list[str] = []
    for gi in range(group_count):
        gid = f"group-{gi + 1:02d}"
        for bi in range(4):
            bid = f"{gid}-few-{bi + 1}"
            few_gain.extend([0.25 + 0.002 * gi] * 125)
            few_groups.extend([gid] * 125)
            few_blocks.extend([bid] * 125)
    few_gain_arr = np.asarray(few_gain, dtype=float)

    balanced = _candidate(
        "robust_balanced", balanced_gain, groups, blocks,
        region_size=4.0, failed_coverage_group=None,
        bootstrap_draws=bootstrap_draws, seed=seed,
        minimum_blocks_per_group=8,
    )
    fragile_candidate = _candidate(
        "fragile_point_positive", fragile_gain, fragile_groups, fragile_blocks,
        region_size=3.0, failed_coverage_group=None,
        bootstrap_draws=bootstrap_draws, seed=seed,
        minimum_blocks_per_group=8,
    )
    broad_candidate = _candidate(
        "robust_broad", broad_gain, broad_groups, broad_blocks,
        region_size=7.0, failed_coverage_group=None,
        bootstrap_draws=bootstrap_draws, seed=seed,
        minimum_blocks_per_group=8,
    )
    coverage_failure = _candidate(
        "coverage_failure", coverage_gain, coverage_groups, coverage_blocks,
        region_size=2.0, failed_coverage_group="group-01",
        bootstrap_draws=bootstrap_draws, seed=seed,
        minimum_blocks_per_group=8,
    )
    insufficient = _candidate(
        "too_few_blocks", few_gain_arr, tuple(few_groups), tuple(few_blocks),
        region_size=4.0, failed_coverage_group=None,
        bootstrap_draws=bootstrap_draws, seed=seed,
        minimum_blocks_per_group=8,
    )

    candidates = (balanced, fragile_candidate, broad_candidate, coverage_failure, insufficient)
    comparison = compare_robust_trust_candidates(
        candidates,
        target_coverage=0.90,
        coverage_tolerance=0.03,
        confidence_level=0.95,
        bootstrap_draws=bootstrap_draws,
        minimum_blocks_per_group=8,
    )
    reversed_comparison = compare_robust_trust_candidates(
        tuple(reversed(candidates)),
        target_coverage=0.90,
        coverage_tolerance=0.03,
        confidence_level=0.95,
        bootstrap_draws=bootstrap_draws,
        minimum_blocks_per_group=8,
    )

    obligations = {
        "balanced_robust_trusted": balanced.robust_trusted_admissible,
        "fragile_legacy_v2_trusted": fragile_candidate.point_and_coverage.trusted_admissible,
        "fragile_v3_rejected": not fragile_candidate.robust_trusted_admissible,
        "fragile_uncertain": fragile_candidate.transfer_uncertainty.robust_transfer_category == "uncertain",
        "broad_robust_trusted": broad_candidate.robust_trusted_admissible,
        "coverage_failure_robust_transfer": coverage_failure.transfer_uncertainty.robust_admissible,
        "coverage_failure_rejected": not coverage_failure.robust_trusted_admissible,
        "too_few_unavailable": insufficient.transfer_uncertainty.robust_transfer_category == "unavailable",
        "too_few_rejected": not insufficient.robust_trusted_admissible,
        "recommended_balanced": comparison.recommended_by_log_score == "robust_balanced",
        "pareto_balanced_only": comparison.pareto_front_names == ("robust_balanced",),
        "candidate_order_invariant": (
            comparison.recommended_by_log_score == reversed_comparison.recommended_by_log_score
            and set(comparison.pareto_front_names) == set(reversed_comparison.pareto_front_names)
            and set(comparison.robust_trusted_names) == set(reversed_comparison.robust_trusted_names)
        ),
        "no_aggregate_confidence": comparison.aggregate_confidence_score_emitted is False,
    }

    return {
        "seed": int(seed),
        "bootstrap_draws": int(bootstrap_draws),
        "group_count": group_count,
        "blocks_per_group": blocks_per_group,
        "rows_per_block": rows_per_block,
        "comparison": comparison.as_dict(),
        "candidates": {row.name: row.as_dict() for row in candidates},
        "checks": [{"name": key, "passed": bool(value)} for key, value in obligations.items()],
        "passed": bool(all(obligations.values())),
    }
