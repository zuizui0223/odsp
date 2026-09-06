"""Known-truth benchmark for the high-level forecast trust dossier."""
from __future__ import annotations

import numpy as np

from .forecast_trust_dossier import build_forecast_trust_dossier
from .prediction_novelty import NoveltySummary
from .robust_trust_aware_model_selection import (
    compare_robust_trust_candidates,
    evaluate_robust_trust_candidate,
)


def _rows_from_blocks(patterns: list[np.ndarray], rows_per_block: int = 25):
    gain: list[float] = []
    groups: list[str] = []
    blocks: list[str] = []
    for gi, pattern in enumerate(patterns):
        gid = f"group-{gi + 1:02d}"
        for bi, value in enumerate(pattern):
            bid = f"{gid}-block-{bi + 1:02d}"
            gain.extend([float(value)] * rows_per_block)
            groups.extend([gid] * rows_per_block)
            blocks.extend([bid] * rows_per_block)
    return np.asarray(gain, dtype=float), tuple(groups), tuple(blocks)


def _covered(groups: tuple[str, ...], failed_group: str | None = None) -> np.ndarray:
    result = np.zeros(len(groups), dtype=bool)
    labels = tuple(dict.fromkeys(groups))
    arr = np.asarray(groups, dtype=object)
    for gid in labels:
        idx = np.flatnonzero(arr == gid)
        fraction = 0.60 if gid == failed_group else 0.90
        count = int(round(fraction * idx.size))
        result[idx[:count]] = True
    return result


def _candidate(
    name: str,
    gain: np.ndarray,
    groups: tuple[str, ...],
    blocks: tuple[str, ...],
    *,
    region_size: float,
    failed_coverage_group: str | None = None,
    bootstrap_draws: int = 2000,
    seed: int = 20260906,
):
    marginal = np.full(gain.size, -2.0, dtype=float)
    return evaluate_robust_trust_candidate(
        name,
        marginal + gain,
        marginal,
        _covered(groups, failed_group=failed_coverage_group),
        groups,
        blocks,
        region_size=np.full(gain.size, region_size),
        target_coverage=0.90,
        coverage_tolerance=0.03,
        confidence_level=0.95,
        bootstrap_draws=bootstrap_draws,
        seed=seed,
        minimum_blocks_per_group=8,
    )


def _novelty(category: str, ratio: float, row_index: int = 0) -> NoveltySummary:
    outside = (0,) if category == "strict_extrapolation" else ()
    return NoveltySummary(
        row_index=row_index,
        nearest_scaled_distance=float(ratio),
        reference_distance=1.0,
        novelty_ratio=float(ratio),
        outside_feature_count=len(outside),
        outside_feature_indices=outside,
        category=category,
    )


def run_forecast_trust_dossier_benchmark(
    *,
    seed: int = 20260906,
    bootstrap_draws: int = 2000,
) -> dict[str, object]:
    group_count = 6
    blocks_per_group = 20
    rows_per_block = 25

    strong_patterns = [
        0.25 + np.linspace(-0.03, 0.03, blocks_per_group) + 0.002 * (gi - 2.5)
        for gi in range(group_count)
    ]
    strong_gain, groups, blocks = _rows_from_blocks(strong_patterns, rows_per_block)

    weak_pattern = np.asarray([
        -0.25, -0.20, -0.15, -0.10, -0.08, -0.06, -0.04, -0.02, 0.00, 0.02,
        0.04, 0.06, 0.08, 0.10, 0.12, 0.14, 0.16, 0.18, 0.20, 0.22,
    ])
    weak_patterns = [weak_pattern + 0.001 * gi for gi in range(group_count)]
    weak_gain, weak_groups, weak_blocks = _rows_from_blocks(weak_patterns, rows_per_block)

    broad_patterns = [
        0.15 + np.linspace(-0.02, 0.02, blocks_per_group) + 0.001 * (gi - 2.5)
        for gi in range(group_count)
    ]
    broad_gain, broad_groups, broad_blocks = _rows_from_blocks(broad_patterns, rows_per_block)

    robust = _candidate(
        "robust_balanced", strong_gain, groups, blocks,
        region_size=4.0, bootstrap_draws=bootstrap_draws, seed=seed,
    )
    fragile = _candidate(
        "fragile_point_positive", weak_gain, weak_groups, weak_blocks,
        region_size=3.0, bootstrap_draws=bootstrap_draws, seed=seed,
    )
    coverage_failed = _candidate(
        "coverage_failed", strong_gain + 0.10, groups, blocks,
        region_size=3.0, failed_coverage_group="group-01",
        bootstrap_draws=bootstrap_draws, seed=seed,
    )
    broad = _candidate(
        "robust_broad", broad_gain, broad_groups, broad_blocks,
        region_size=7.0, bootstrap_draws=bootstrap_draws, seed=seed,
    )

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
    too_few = _candidate(
        "too_few_blocks",
        np.asarray(few_gain, dtype=float),
        tuple(few_groups),
        tuple(few_blocks),
        region_size=4.0,
        bootstrap_draws=bootstrap_draws,
        seed=seed,
    )

    selection = compare_robust_trust_candidates(
        (robust, broad, fragile, coverage_failed, too_few),
        target_coverage=0.90,
        coverage_tolerance=0.03,
        confidence_level=0.95,
        bootstrap_draws=bootstrap_draws,
        minimum_blocks_per_group=8,
    )

    in_domain = tuple(_novelty("in_domain", 0.5, i) for i in range(4))
    strict = (
        _novelty("in_domain", 0.4, 0),
        _novelty("strict_extrapolation", 3.5, 1),
        _novelty("novel", 1.4, 2),
    )

    dossiers = {
        "robust_in_domain": build_forecast_trust_dossier(
            robust, deployment_novelty_rows=in_domain, selection=selection
        ),
        "fragile_in_domain": build_forecast_trust_dossier(
            fragile, deployment_novelty_rows=in_domain, selection=selection
        ),
        "coverage_failed_in_domain": build_forecast_trust_dossier(
            coverage_failed, deployment_novelty_rows=in_domain, selection=selection
        ),
        "robust_strict_extrapolation": build_forecast_trust_dossier(
            robust, deployment_novelty_rows=strict, selection=selection
        ),
        "too_few_blocks": build_forecast_trust_dossier(
            too_few, deployment_novelty_rows=in_domain, selection=selection
        ),
    }

    robust_d = dossiers["robust_in_domain"]
    fragile_d = dossiers["fragile_in_domain"]
    coverage_d = dossiers["coverage_failed_in_domain"]
    strict_d = dossiers["robust_strict_extrapolation"]
    few_d = dossiers["too_few_blocks"]

    checks = {
        "robust_in_domain_admitted": robust_d.validation.robust_validation_status == "admitted",
        "robust_in_domain_no_blockers": robust_d.validation.blocking_reasons == (),
        "robust_in_domain_no_warnings": robust_d.deployment.warnings == (),
        "fragile_blocked": fragile_d.validation.robust_validation_status == "blocked",
        "fragile_uncertainty_blocker": "transfer_uncertain" in fragile_d.validation.blocking_reasons,
        "coverage_blocked": coverage_d.validation.robust_validation_status == "blocked",
        "coverage_failure_blocker": "groupwise_coverage_failure" in coverage_d.validation.blocking_reasons,
        "strict_keeps_validation_admitted": strict_d.validation.robust_validation_status == "admitted",
        "strict_is_deployment_warning": strict_d.deployment.status == "strict_extrapolation_warning",
        "strict_warning_not_blocker": "strict_extrapolation" in strict_d.deployment.warnings and strict_d.validation.blocking_reasons == (),
        "too_few_unavailable": few_d.validation.robust_validation_status == "unavailable",
        "selection_recommended_preserved": robust_d.selection.status == "recommended",
        "no_aggregate_confidence": all(not dossier.aggregate_confidence_score_emitted for dossier in dossiers.values()),
    }

    return {
        "seed": int(seed),
        "bootstrap_draws": int(bootstrap_draws),
        "dossiers": {name: dossier.as_dict() for name, dossier in dossiers.items()},
        "checks": [{"name": name, "passed": bool(value)} for name, value in checks.items()],
        "passed": bool(all(checks.values())),
    }
