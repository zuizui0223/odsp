"""Known-truth validation for forecast model comparison."""
from __future__ import annotations

from dataclasses import asdict, dataclass

import numpy as np

from .forecast_model_comparison import (
    ForecastCandidateScore,
    compare_forecast_candidates,
    evaluate_forecast_candidate,
)


@dataclass(frozen=True)
class ForecastModelComparisonCheck:
    name: str
    passed: bool

    def as_dict(self) -> dict[str, object]:
        return asdict(self)


@dataclass(frozen=True)
class ForecastModelComparisonBenchmarkResult:
    seed: int
    group_count: int
    rows_per_group: int
    target_coverage: float
    gain_tolerance: float
    candidates: tuple[ForecastCandidateScore, ...]
    recommended_candidate: str | None
    pareto_front_names: tuple[str, ...]
    checks: tuple[ForecastModelComparisonCheck, ...]
    aggregate_confidence_score_emitted: bool
    passed: bool

    def as_dict(self) -> dict[str, object]:
        return {
            "seed": self.seed,
            "group_count": self.group_count,
            "rows_per_group": self.rows_per_group,
            "target_coverage": self.target_coverage,
            "gain_tolerance": self.gain_tolerance,
            "candidates": [row.as_dict() for row in self.candidates],
            "recommended_candidate": self.recommended_candidate,
            "pareto_front_names": list(self.pareto_front_names),
            "checks": [row.as_dict() for row in self.checks],
            "aggregate_confidence_score_emitted": self.aggregate_confidence_score_emitted,
            "passed": self.passed,
        }


def _gain_vector(
    rng: np.random.Generator,
    group_means: list[float],
    rows_per_group: int,
) -> np.ndarray:
    pieces: list[np.ndarray] = []
    for mean in group_means:
        noise = rng.normal(scale=0.025, size=rows_per_group)
        noise -= float(np.mean(noise))
        pieces.append(mean + noise)
    return np.concatenate(pieces)


def _coverage_vector(group_count: int, rows_per_group: int, fraction: float) -> np.ndarray:
    covered_per_group = int(round(rows_per_group * fraction))
    if not np.isclose(covered_per_group / rows_per_group, fraction, atol=1e-12):
        raise ValueError("coverage fraction must be exactly representable by rows_per_group")
    rows: list[np.ndarray] = []
    for _ in range(group_count):
        values = np.zeros(rows_per_group, dtype=bool)
        values[:covered_per_group] = True
        rows.append(values)
    return np.concatenate(rows)


def run_forecast_model_comparison_benchmark(
    *,
    seed: int = 20260905,
    group_count: int = 6,
    rows_per_group: int = 500,
    target_coverage: float = 0.90,
    coverage_tolerance: float = 0.03,
    gain_tolerance: float = 1e-12,
) -> ForecastModelComparisonBenchmarkResult:
    if group_count != 6 or rows_per_group < 100:
        raise ValueError("the frozen benchmark uses six groups and at least 100 rows per group")
    rng = np.random.default_rng(seed)
    n = group_count * rows_per_group
    groups = np.repeat([f"group-{index+1}" for index in range(group_count)], rows_per_group)
    marginal = rng.normal(loc=-2.0, scale=0.12, size=n)
    covered_90 = _coverage_vector(group_count, rows_per_group, 0.90)
    covered_72 = _coverage_vector(group_count, rows_per_group, 0.72)

    specifications = (
        (
            "well_calibrated",
            [0.25, 0.30, 0.22, 0.27, 0.26, 0.24],
            covered_90,
            4.0,
        ),
        (
            "overconfident_high_gain",
            [0.44, 0.42, 0.46, 0.41, 0.45, 0.43],
            covered_72,
            1.5,
        ),
        (
            "marginal_only",
            [0.0, 0.0, 0.0, 0.0, 0.0, 0.0],
            covered_90,
            8.0,
        ),
        (
            "shifted_non_generalizing",
            [-0.28, -0.35, -0.31, -0.24, -0.30, -0.27],
            covered_90,
            4.0,
        ),
        (
            "mixed_despite_positive_pool",
            [0.60, 0.40, 0.40, 0.40, 0.40, -0.10],
            covered_90,
            4.0,
        ),
        (
            "broad_calibrated",
            [0.15, 0.18, 0.14, 0.17, 0.16, 0.15],
            covered_90,
            7.0,
        ),
    )

    scored: list[ForecastCandidateScore] = []
    for name, group_means, covered, region_size in specifications:
        gain = _gain_vector(rng, list(group_means), rows_per_group)
        scored.append(
            evaluate_forecast_candidate(
                name,
                marginal + gain,
                marginal,
                groups,
                covered=covered,
                target_coverage=target_coverage,
                region_size=np.full(n, region_size, dtype=float),
                coverage_tolerance=coverage_tolerance,
                gain_tolerance=gain_tolerance,
            )
        )

    comparison = compare_forecast_candidates(
        scored,
        coverage_tolerance=coverage_tolerance,
    )
    by_name = {row.name: row for row in scored}

    checks = (
        ForecastModelComparisonCheck(
            "well_calibrated_is_trusted_admissible",
            by_name["well_calibrated"].trusted_admissible,
        ),
        ForecastModelComparisonCheck(
            "overconfident_rejected_despite_larger_gain",
            bool(
                by_name["overconfident_high_gain"].mean_log_density_gain
                > by_name["well_calibrated"].mean_log_density_gain
                and by_name["overconfident_high_gain"].transfer_admissible
                and not by_name["overconfident_high_gain"].trusted_admissible
            ),
        ),
        ForecastModelComparisonCheck(
            "marginal_only_not_transfer_admissible",
            bool(
                not by_name["marginal_only"].transfer_admissible
                and by_name["marginal_only"].transfer_category == "non_generalizing"
            ),
        ),
        ForecastModelComparisonCheck(
            "shifted_is_non_generalizing",
            by_name["shifted_non_generalizing"].transfer_category == "non_generalizing",
        ),
        ForecastModelComparisonCheck(
            "mixed_positive_pool_remains_mixed",
            bool(
                by_name["mixed_despite_positive_pool"].mean_log_density_gain > 0
                and by_name["mixed_despite_positive_pool"].transfer_category == "mixed"
                and not by_name["mixed_despite_positive_pool"].transfer_admissible
            ),
        ),
        ForecastModelComparisonCheck(
            "broad_candidate_is_pareto_dominated",
            "broad_calibrated" not in comparison.pareto_front_names
            and "well_calibrated" in comparison.pareto_front_names,
        ),
        ForecastModelComparisonCheck(
            "well_calibrated_is_recommended",
            comparison.recommended_by_log_score == "well_calibrated",
        ),
        ForecastModelComparisonCheck(
            "no_aggregate_confidence_score",
            comparison.aggregate_confidence_score_emitted is False,
        ),
    )
    passed = bool(all(row.passed for row in checks))
    return ForecastModelComparisonBenchmarkResult(
        seed=int(seed),
        group_count=int(group_count),
        rows_per_group=int(rows_per_group),
        target_coverage=float(target_coverage),
        gain_tolerance=float(gain_tolerance),
        candidates=tuple(scored),
        recommended_candidate=comparison.recommended_by_log_score,
        pareto_front_names=comparison.pareto_front_names,
        checks=checks,
        aggregate_confidence_score_emitted=comparison.aggregate_confidence_score_emitted,
        passed=passed,
    )
