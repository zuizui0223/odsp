"""Deterministic known-truth benchmark for group-wise coverage/trust audits."""
from __future__ import annotations

import numpy as np

from .groupwise_coverage_audit import (
    audit_groupwise_coverage,
    audit_groupwise_forecast_trust,
)


def _coverage_vector(n: int, covered_count: int) -> np.ndarray:
    values = np.zeros(n, dtype=bool)
    values[:covered_count] = True
    return values


def _masked_failure_case() -> tuple[np.ndarray, tuple[str, ...]]:
    blocks: list[np.ndarray] = []
    labels: list[str] = []
    for index in range(20):
        covered_count = 600 if index == 0 else 916
        blocks.append(_coverage_vector(1000, covered_count))
        labels.extend([f"group-{index + 1:02d}"] * 1000)
    return np.concatenate(blocks), tuple(labels)


def _all_calibrated_case() -> tuple[np.ndarray, tuple[str, ...]]:
    blocks = [_coverage_vector(1000, 900) for _ in range(20)]
    labels = tuple(
        label
        for index in range(20)
        for label in [f"group-{index + 1:02d}"] * 1000
    )
    return np.concatenate(blocks), labels


def run_groupwise_coverage_audit_benchmark() -> dict[str, object]:
    target = 0.90
    tolerance = 0.03

    masked_covered, masked_groups = _masked_failure_case()
    masked = audit_groupwise_coverage(
        masked_covered,
        masked_groups,
        target_coverage=target,
        tolerance=tolerance,
    )

    calibrated_covered, calibrated_groups = _all_calibrated_case()
    calibrated = audit_groupwise_coverage(
        calibrated_covered,
        calibrated_groups,
        target_coverage=target,
        tolerance=tolerance,
    )

    novelty_covered = np.concatenate(
        [
            _coverage_vector(3000, 2700),
            _coverage_vector(1000, 850),
            _coverage_vector(1000, 300),
        ]
    )
    novelty_labels = tuple(
        ["in_domain"] * 3000 + ["novel"] * 1000 + ["strict"] * 1000
    )
    novelty = audit_groupwise_coverage(
        novelty_covered,
        novelty_labels,
        target_coverage=target,
        tolerance=tolerance,
    )
    novelty_by_name = {row.group_id: row for row in novelty.groups}

    marginal = np.full(masked_covered.size, -2.0, dtype=float)
    positive_conditional = marginal + 0.20
    positive_transfer_bad_coverage = audit_groupwise_forecast_trust(
        positive_conditional,
        marginal,
        masked_covered,
        masked_groups,
        target_coverage=target,
        tolerance=tolerance,
    )

    gain_blocks: list[np.ndarray] = []
    for index in range(20):
        gain_blocks.append(np.full(1000, -0.10 if index == 0 else 0.20))
    mixed_gain = np.concatenate(gain_blocks)
    good_coverage_bad_transfer = audit_groupwise_forecast_trust(
        np.full(mixed_gain.size, -2.0) + mixed_gain,
        np.full(mixed_gain.size, -2.0),
        calibrated_covered,
        calibrated_groups,
        target_coverage=target,
        tolerance=tolerance,
    )

    reverse_order = list(range(masked_covered.size))[::-1]
    permuted = audit_groupwise_coverage(
        masked_covered[reverse_order],
        tuple(masked_groups[index] for index in reverse_order),
        target_coverage=target,
        tolerance=tolerance,
    )
    original_map = {row.group_id: row.empirical_coverage for row in masked.groups}
    permuted_map = {row.group_id: row.empirical_coverage for row in permuted.groups}
    permutation_error = max(
        abs(original_map[name] - permuted_map[name]) for name in original_map
    )

    obligations = {
        "masked_pooled_coverage_passes": masked.pooled_coverage_ok,
        "masked_pooled_error_small": masked.pooled_absolute_error <= 0.005,
        "masked_groupwise_mixed": masked.coverage_category == "mixed",
        "masked_exactly_one_failed_group": masked.failed_group_count == 1,
        "masked_first_group_low": masked.groups[0].empirical_coverage <= 0.61,
        "all_calibrated_passes": calibrated.coverage_category == "calibrated" and calibrated.failed_group_count == 0,
        "novelty_in_domain_good": novelty_by_name["in_domain"].empirical_coverage >= 0.89,
        "novelty_novel_degraded": novelty_by_name["novel"].empirical_coverage <= 0.86,
        "novelty_strict_degraded": novelty_by_name["strict"].empirical_coverage <= 0.35,
        "novelty_coverage_decreases": (
            novelty_by_name["in_domain"].empirical_coverage
            > novelty_by_name["novel"].empirical_coverage
            > novelty_by_name["strict"].empirical_coverage
        ),
        "positive_transfer_bad_coverage_not_trusted": (
            positive_transfer_bad_coverage.transfer_category == "generalizing"
            and positive_transfer_bad_coverage.coverage_category == "mixed"
            and positive_transfer_bad_coverage.trusted_admissible is False
        ),
        "good_coverage_bad_transfer_not_trusted": (
            good_coverage_bad_transfer.coverage_category == "calibrated"
            and good_coverage_bad_transfer.transfer_category == "mixed"
            and good_coverage_bad_transfer.trusted_admissible is False
        ),
        "group_permutation_invariant": permutation_error <= 1e-15,
        "no_aggregate_confidence_score": (
            masked.aggregate_confidence_score_emitted is False
            and positive_transfer_bad_coverage.aggregate_confidence_score_emitted is False
        ),
    }

    return {
        "target_coverage": target,
        "tolerance": tolerance,
        "masked_failure": masked.as_dict(),
        "all_calibrated": calibrated.as_dict(),
        "novelty_strata": novelty.as_dict(),
        "positive_transfer_bad_coverage": positive_transfer_bad_coverage.as_dict(),
        "good_coverage_bad_transfer": good_coverage_bad_transfer.as_dict(),
        "group_permutation_max_abs_error": float(permutation_error),
        "checks": [
            {"name": name, "passed": bool(passed)} for name, passed in obligations.items()
        ],
        "passed": bool(all(obligations.values())),
    }
