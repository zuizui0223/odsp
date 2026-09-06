"""Deterministic known-truth benchmark for group-wise trust-aware model selection."""
from __future__ import annotations

import numpy as np

from .trust_aware_model_selection import (
    compare_trust_aware_candidates,
    evaluate_trust_aware_candidate,
)


def _groups(group_count: int = 20, rows_per_group: int = 1000) -> tuple[str, ...]:
    return tuple(
        label
        for index in range(group_count)
        for label in [f"group-{index + 1:02d}"] * rows_per_group
    )


def _covered_counts(counts: list[int], rows_per_group: int = 1000) -> np.ndarray:
    rows: list[np.ndarray] = []
    for count in counts:
        block = np.zeros(rows_per_group, dtype=bool)
        block[:count] = True
        rows.append(block)
    return np.concatenate(rows)


def _gain_by_group(values: list[float], rows_per_group: int = 1000) -> np.ndarray:
    return np.concatenate([np.full(rows_per_group, value, dtype=float) for value in values])


def run_trust_aware_model_selection_benchmark() -> dict[str, object]:
    group_count = 20
    rows_per_group = 1000
    n = group_count * rows_per_group
    groups = _groups(group_count, rows_per_group)
    marginal = np.full(n, -2.0, dtype=float)

    specs = {
        "balanced_trusted": {
            "gains": [0.25] * group_count,
            "coverage_counts": [900] * group_count,
            "region_size": 4.0,
        },
        "pooled_masked_coverage_failure": {
            "gains": [0.40] * group_count,
            "coverage_counts": [600] + [916] * (group_count - 1),
            "region_size": 3.0,
        },
        "mixed_transfer": {
            "gains": [-0.10] + [0.25] * (group_count - 1),
            "coverage_counts": [900] * group_count,
            "region_size": 4.0,
        },
        "broad_trusted": {
            "gains": [0.15] * group_count,
            "coverage_counts": [900] * group_count,
            "region_size": 7.0,
        },
        "overconfident": {
            "gains": [0.45] * group_count,
            "coverage_counts": [720] * group_count,
            "region_size": 1.5,
        },
    }

    scores = []
    for name, spec in specs.items():
        gain = _gain_by_group(spec["gains"], rows_per_group)
        covered = _covered_counts(spec["coverage_counts"], rows_per_group)
        score = evaluate_trust_aware_candidate(
            name,
            marginal + gain,
            marginal,
            covered,
            groups,
            region_size=np.full(n, spec["region_size"]),
            target_coverage=0.90,
            coverage_tolerance=0.03,
            gain_tolerance=1e-12,
        )
        scores.append(score)

    result = compare_trust_aware_candidates(
        scores,
        target_coverage=0.90,
        coverage_tolerance=0.03,
        gain_tolerance=1e-12,
    )
    by_name = {row.name: row for row in scores}

    reversed_result = compare_trust_aware_candidates(
        list(reversed(scores)),
        target_coverage=0.90,
        coverage_tolerance=0.03,
        gain_tolerance=1e-12,
    )
    order_invariant = (
        result.recommended_by_log_score == reversed_result.recommended_by_log_score
        and set(result.pareto_front_names) == set(reversed_result.pareto_front_names)
        and set(result.trusted_admissible_names) == set(reversed_result.trusted_admissible_names)
    )

    masked = by_name["pooled_masked_coverage_failure"]
    mixed = by_name["mixed_transfer"]
    broad = by_name["broad_trusted"]
    overconfident = by_name["overconfident"]
    balanced = by_name["balanced_trusted"]

    obligations = {
        "recommended_balanced": result.recommended_by_log_score == "balanced_trusted",
        "pareto_balanced_only": result.pareto_front_names == ("balanced_trusted",),
        "balanced_transfer_all_positive": balanced.groupwise_trust.transfer_category == "generalizing",
        "balanced_coverage_all_ok": balanced.groupwise_trust.coverage_category == "calibrated",
        "masked_pooled_coverage_passes": masked.forecast_score.coverage_ok is True,
        "masked_groupwise_coverage_mixed": masked.groupwise_trust.coverage_category == "mixed",
        "masked_not_trusted": masked.trusted_admissible is False,
        "mixed_pooled_gain_positive": mixed.forecast_score.mean_log_density_gain > 0.0,
        "mixed_transfer_category": mixed.groupwise_trust.transfer_category == "mixed",
        "mixed_not_trusted": mixed.trusted_admissible is False,
        "broad_is_trusted": broad.trusted_admissible is True,
        "broad_pareto_dominated": "broad_trusted" not in result.pareto_front_names,
        "overconfident_transfer_generalizing": overconfident.groupwise_trust.transfer_category == "generalizing",
        "overconfident_coverage_non_calibrated": overconfident.groupwise_trust.coverage_category == "non_calibrated",
        "overconfident_not_trusted": overconfident.trusted_admissible is False,
        "candidate_order_invariant": order_invariant,
        "no_aggregate_confidence_score": result.aggregate_confidence_score_emitted is False,
    }

    return {
        "target_coverage": 0.90,
        "coverage_tolerance": 0.03,
        "gain_tolerance": 1e-12,
        "group_count": group_count,
        "rows_per_group": rows_per_group,
        "selection": result.as_dict(),
        "candidate_order_invariant": bool(order_invariant),
        "checks": [
            {"name": name, "passed": bool(passed)}
            for name, passed in obligations.items()
        ],
        "passed": bool(all(obligations.values())),
    }
