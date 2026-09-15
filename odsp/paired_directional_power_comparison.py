"""Paired same-world comparison of two-sided and directional transfer ceilings.

The comparison is prospective: both methods receive the identical simulated
shared-block world and the identical bootstrap seed. Power differences are
reported only after null calibration of both methods. Qualification depends on
no dataset-level ceiling regression by the directional method and controlled
overreach under coarse-truth scenarios, not on achieving a desired power gain.
"""
from __future__ import annotations

from dataclasses import asdict, dataclass
import math

import numpy as np

from .shared_block_bootstrap_t_calibration import _rows, _world
from .shared_block_certification_v2 import certify_shared_block_gains_v2
from .shared_block_positive_certification import certify_shared_block_positive_gains_v2


COMPARISON_VERSION = "paired_shared_block_two_sided_vs_one_sided_same_world_v1"
_LEVELS = ("pooled", "coarse", "fine")
_LEVEL_INDEX = {name: index for index, name in enumerate(_LEVELS)}


@dataclass(frozen=True)
class PairedDirectionalPowerScenario:
    scenario_id: str
    distribution: str
    blocks_per_group: int
    coarse_mean_gain: float
    fine_mean_gain: float
    truth_ceiling: str
    simulations: int
    two_sided_exact_ceiling_recovery_rate: float
    one_sided_exact_ceiling_recovery_rate: float
    exact_recovery_rate_difference: float
    two_sided_overreach_rate: float
    one_sided_overreach_rate: float
    two_sided_underreach_rate: float
    one_sided_underreach_rate: float
    two_sided_full_ceiling_rate: float
    one_sided_full_ceiling_rate: float
    paired_dataset_ceiling_advance_count: int
    paired_dataset_ceiling_regression_count: int
    candidate_overreach_threshold: float | None
    candidate_acceptance_pass: bool

    def as_dict(self) -> dict[str, object]:
        return asdict(self)


@dataclass(frozen=True)
class PairedDirectionalPowerComparison:
    comparison_version: str
    seed: int
    simulations_per_scenario: int
    bootstrap_draws_per_interval: int
    group_count: int
    group_correlation: float
    step_correlation: float
    noise_standard_deviation: float
    familywise_confidence_level: float
    same_world_per_method: bool
    same_shared_block_bootstrap_seed_per_method: bool
    scenarios: tuple[PairedDirectionalPowerScenario, ...]
    qualification_pass: bool

    def as_dict(self) -> dict[str, object]:
        payload = asdict(self)
        payload["scenarios"] = [row.as_dict() for row in self.scenarios]
        return payload


def _truth_ceiling(coarse_mean: float, fine_mean: float) -> str:
    if coarse_mean <= 0.0:
        return "pooled"
    if fine_mean <= 0.0:
        return "coarse"
    return "fine"


def _certified_ceiling(categories: tuple[str, ...]) -> str:
    ceiling = "pooled"
    for index, category in enumerate(categories):
        if category != "robust_generalizing":
            break
        ceiling = _LEVELS[index + 1]
    return ceiling


def run_paired_directional_power_comparison(
    *,
    seed: int = 20260915,
    simulations_per_scenario: int = 1000,
    bootstrap_draws: int = 500,
    group_count: int = 6,
    group_correlation: float = 0.7,
    step_correlation: float = 0.4,
    noise_standard_deviation: float = 0.2,
    confidence_level: float = 0.95,
) -> PairedDirectionalPowerComparison:
    """Run the predeclared paired same-world mixed-truth comparison."""

    if simulations_per_scenario < 100:
        raise ValueError("simulations_per_scenario must be >= 100")
    if bootstrap_draws < 500:
        raise ValueError("bootstrap_draws must be >= 500")
    if group_count < 2:
        raise ValueError("group_count must be >= 2")
    if not 0.0 <= group_correlation < 1.0 or not 0.0 <= step_correlation < 1.0:
        raise ValueError("correlations must lie in [0, 1)")
    if not math.isfinite(noise_standard_deviation) or noise_standard_deviation <= 0:
        raise ValueError("noise_standard_deviation must be finite and positive")
    if not 0.0 < confidence_level < 1.0:
        raise ValueError("confidence_level must lie strictly between zero and one")

    scenario_defs = (
        ("paired-strong-full-normal-b20", "normal", 20, 0.45, 0.30),
        ("paired-strong-full-normal-b50", "normal", 50, 0.45, 0.30),
        ("paired-weak-full-normal-b20", "normal", 20, 0.45, 0.15),
        ("paired-coarse-null-normal-b20", "normal", 20, 0.45, 0.0),
        ("paired-coarse-adverse-normal-b20", "normal", 20, 0.45, -0.10),
        ("paired-coarse-null-t3-b20", "student_t3", 20, 0.45, 0.0),
    )
    alpha = 1.0 - confidence_level
    overreach_limit = float(
        alpha + 2.0 * math.sqrt(alpha * (1.0 - alpha) / simulations_per_scenario)
    )
    rng = np.random.default_rng(seed)
    scenario_rows: list[PairedDirectionalPowerScenario] = []

    for scenario_index, (
        scenario_id,
        distribution,
        block_count,
        coarse_mean,
        fine_mean,
    ) in enumerate(scenario_defs):
        truth = _truth_ceiling(coarse_mean, fine_mean)
        truth_index = _LEVEL_INDEX[truth]
        two_exact = one_exact = 0
        two_over = one_over = 0
        two_under = one_under = 0
        two_full = one_full = 0
        advances = regressions = 0

        for simulation_index in range(simulations_per_scenario):
            noise = noise_standard_deviation * _world(
                rng,
                blocks=block_count,
                group_count=group_count,
                contrast_count=2,
                group_rho=group_correlation,
                contrast_rho=step_correlation,
                distribution=distribution,
            )
            values = noise + np.asarray([coarse_mean, fine_mean])[None, None, :]
            gains, groups, blocks = _rows(values)
            local_seed = (
                seed
                + 1000003 * (scenario_index + 1)
                + 10007 * (simulation_index + 1)
            )
            names = ("pooled->coarse", "coarse->fine")
            two = certify_shared_block_gains_v2(
                gains,
                groups,
                blocks,
                contrast_names=names,
                familywise_confidence_level=confidence_level,
                bootstrap_draws=bootstrap_draws,
                seed=local_seed,
                minimum_shared_blocks=8,
            )
            one = certify_shared_block_positive_gains_v2(
                gains,
                groups,
                blocks,
                contrast_names=names,
                familywise_lower_confidence_level=confidence_level,
                bootstrap_draws=bootstrap_draws,
                seed=local_seed,
                minimum_shared_blocks=8,
            )
            two_ceiling = _certified_ceiling(tuple(row.category for row in two.contrasts))
            one_ceiling = _certified_ceiling(tuple(row.category for row in one.contrasts))
            two_index = _LEVEL_INDEX[two_ceiling]
            one_index = _LEVEL_INDEX[one_ceiling]

            two_exact += int(two_index == truth_index)
            one_exact += int(one_index == truth_index)
            two_over += int(two_index > truth_index)
            one_over += int(one_index > truth_index)
            two_under += int(two_index < truth_index)
            one_under += int(one_index < truth_index)
            two_full += int(two_ceiling == "fine")
            one_full += int(one_ceiling == "fine")
            advances += int(one_index > two_index)
            regressions += int(one_index < two_index)

        two_exact_rate = float(two_exact / simulations_per_scenario)
        one_exact_rate = float(one_exact / simulations_per_scenario)
        one_over_rate = float(one_over / simulations_per_scenario)
        threshold = overreach_limit if truth == "coarse" else None
        candidate_pass = bool(
            regressions == 0
            and (threshold is None or one_over_rate <= threshold)
        )
        scenario_rows.append(
            PairedDirectionalPowerScenario(
                scenario_id=scenario_id,
                distribution=distribution,
                blocks_per_group=block_count,
                coarse_mean_gain=float(coarse_mean),
                fine_mean_gain=float(fine_mean),
                truth_ceiling=truth,
                simulations=simulations_per_scenario,
                two_sided_exact_ceiling_recovery_rate=two_exact_rate,
                one_sided_exact_ceiling_recovery_rate=one_exact_rate,
                exact_recovery_rate_difference=float(one_exact_rate - two_exact_rate),
                two_sided_overreach_rate=float(two_over / simulations_per_scenario),
                one_sided_overreach_rate=one_over_rate,
                two_sided_underreach_rate=float(two_under / simulations_per_scenario),
                one_sided_underreach_rate=float(one_under / simulations_per_scenario),
                two_sided_full_ceiling_rate=float(two_full / simulations_per_scenario),
                one_sided_full_ceiling_rate=float(one_full / simulations_per_scenario),
                paired_dataset_ceiling_advance_count=advances,
                paired_dataset_ceiling_regression_count=regressions,
                candidate_overreach_threshold=threshold,
                candidate_acceptance_pass=candidate_pass,
            )
        )

    scenarios = tuple(scenario_rows)
    return PairedDirectionalPowerComparison(
        comparison_version=COMPARISON_VERSION,
        seed=seed,
        simulations_per_scenario=simulations_per_scenario,
        bootstrap_draws_per_interval=bootstrap_draws,
        group_count=group_count,
        group_correlation=float(group_correlation),
        step_correlation=float(step_correlation),
        noise_standard_deviation=float(noise_standard_deviation),
        familywise_confidence_level=float(confidence_level),
        same_world_per_method=True,
        same_shared_block_bootstrap_seed_per_method=True,
        scenarios=scenarios,
        qualification_pass=all(row.candidate_acceptance_pass for row in scenarios),
    )
