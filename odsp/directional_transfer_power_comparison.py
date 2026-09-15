"""Paired operating-characteristics comparison of two-sided and directional ceilings.

Each simulated validation world is evaluated twice with the same held-out rows,
validation blocks and bootstrap seed: once by the frozen two-sided v2
information-transfer ceiling and once by the qualified one-sided directional
positive-transfer ceiling. This isolates the inferential-tail choice from world
variation.
"""
from __future__ import annotations

from dataclasses import asdict, dataclass
import math

import numpy as np

from .information_transfer_positive_v2 import certify_positive_information_transfer_v2
from .information_transfer_v2 import certify_information_transfer_v2
from .transfer_ceiling_operating_characteristics import (
    GENERATOR_VERSION as REFERENCE_GENERATOR_VERSION,
    _LEVEL_INDEX,
    _rows,
    _step_noise,
    _truth_ceiling,
)


COMPARISON_VERSION = "paired_two_sided_vs_one_sided_same_world_v1"


@dataclass(frozen=True)
class DirectionalPowerComparisonScenario:
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
    paired_dataset_ceiling_regression_count: int
    paired_dataset_ceiling_advance_count: int
    candidate_overreach_threshold: float | None
    candidate_acceptance_pass: bool

    def as_dict(self) -> dict[str, object]:
        return asdict(self)


@dataclass(frozen=True)
class DirectionalTransferPowerComparison:
    comparison_version: str
    reference_generator_version: str
    seed: int
    simulations_per_scenario: int
    bootstrap_draws_per_interval: int
    group_count: int
    step_correlation: float
    noise_standard_deviation: float
    familywise_confidence_level: float
    same_world_per_method: bool
    same_bootstrap_seed_per_method: bool
    scenarios: tuple[DirectionalPowerComparisonScenario, ...]
    qualification_pass: bool

    def as_dict(self) -> dict[str, object]:
        payload = asdict(self)
        payload["scenarios"] = [row.as_dict() for row in self.scenarios]
        return payload


def _scenario_definitions() -> tuple[tuple[str, str, int, float, float], ...]:
    return (
        ("strong-full-normal-b20", "normal", 20, 0.45, 0.30),
        ("strong-full-normal-b50", "normal", 50, 0.45, 0.30),
        ("weak-full-normal-b20", "normal", 20, 0.45, 0.15),
        ("coarse-null-normal-b20", "normal", 20, 0.45, 0.0),
        ("coarse-adverse-normal-b20", "normal", 20, 0.45, -0.10),
        ("coarse-null-t3-b20", "student_t3", 20, 0.45, 0.0),
    )


def run_directional_transfer_power_comparison(
    *,
    seed: int = 20260915,
    simulations_per_scenario: int = 1000,
    bootstrap_draws: int = 500,
    group_count: int = 6,
    step_correlation: float = 0.4,
    noise_standard_deviation: float = 0.2,
    confidence_level: float = 0.95,
) -> DirectionalTransferPowerComparison:
    """Run the predeclared same-world two-sided versus one-sided comparison."""

    if simulations_per_scenario < 100:
        raise ValueError("simulations_per_scenario must be >= 100")
    if bootstrap_draws < 500:
        raise ValueError("bootstrap_draws must be >= 500")
    if group_count < 2:
        raise ValueError("group_count must be >= 2")
    if not 0.0 <= step_correlation < 1.0:
        raise ValueError("step_correlation must lie in [0, 1)")
    if not math.isfinite(noise_standard_deviation) or noise_standard_deviation <= 0:
        raise ValueError("noise_standard_deviation must be finite and positive")
    if not 0.0 < confidence_level < 1.0:
        raise ValueError("confidence_level must lie strictly between zero and one")

    rng = np.random.default_rng(seed)
    scenario_rows: list[DirectionalPowerComparisonScenario] = []
    alpha = 1.0 - confidence_level
    coarse_truth_overreach_threshold = float(
        alpha + 2.0 * math.sqrt(alpha * (1.0 - alpha) / simulations_per_scenario)
    )

    for scenario_index, (
        scenario_id,
        distribution,
        block_count,
        coarse_mean,
        fine_mean,
    ) in enumerate(_scenario_definitions()):
        truth = _truth_ceiling(coarse_mean, fine_mean)
        truth_index = _LEVEL_INDEX[truth]
        two_exact = 0
        one_exact = 0
        two_over = 0
        one_over = 0
        two_under = 0
        one_under = 0
        two_full = 0
        one_full = 0
        regressions = 0
        advances = 0

        for simulation_index in range(simulations_per_scenario):
            noise = _step_noise(
                rng,
                blocks=block_count,
                group_count=group_count,
                rho=step_correlation,
                sigma=noise_standard_deviation,
                distribution=distribution,
            )
            increments = noise + np.asarray([coarse_mean, fine_mean])[None, None, :]
            levels, groups, block_ids = _rows(increments)
            local_seed = (
                seed
                + 1000003 * (scenario_index + 1)
                + 10007 * (simulation_index + 1)
            )

            two_sided = certify_information_transfer_v2(
                levels,
                groups,
                blocks=block_ids,
                familywise_confidence_level=confidence_level,
                bootstrap_draws=bootstrap_draws,
                seed=local_seed,
                minimum_blocks_per_group=8,
            )
            one_sided = certify_positive_information_transfer_v2(
                levels,
                groups,
                blocks=block_ids,
                familywise_lower_confidence_level=confidence_level,
                bootstrap_draws=bootstrap_draws,
                seed=local_seed,
                minimum_blocks_per_group=8,
            )

            two_index = _LEVEL_INDEX[two_sided.certified_transfer_ceiling]
            one_index = _LEVEL_INDEX[one_sided.certified_transfer_ceiling]
            two_exact += int(two_index == truth_index)
            one_exact += int(one_index == truth_index)
            two_over += int(two_index > truth_index)
            one_over += int(one_index > truth_index)
            two_under += int(two_index < truth_index)
            one_under += int(one_index < truth_index)
            two_full += int(two_sided.certified_transfer_ceiling == "fine")
            one_full += int(one_sided.certified_transfer_ceiling == "fine")
            regressions += int(one_index < two_index)
            advances += int(one_index > two_index)

        denominator = float(simulations_per_scenario)
        two_exact_rate = float(two_exact / denominator)
        one_exact_rate = float(one_exact / denominator)
        two_over_rate = float(two_over / denominator)
        one_over_rate = float(one_over / denominator)
        two_under_rate = float(two_under / denominator)
        one_under_rate = float(one_under / denominator)
        two_full_rate = float(two_full / denominator)
        one_full_rate = float(one_full / denominator)

        threshold = coarse_truth_overreach_threshold if truth == "coarse" else None
        acceptance = regressions == 0
        if threshold is not None:
            acceptance = bool(acceptance and one_over_rate <= threshold)

        scenario_rows.append(
            DirectionalPowerComparisonScenario(
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
                two_sided_overreach_rate=two_over_rate,
                one_sided_overreach_rate=one_over_rate,
                two_sided_underreach_rate=two_under_rate,
                one_sided_underreach_rate=one_under_rate,
                two_sided_full_ceiling_rate=two_full_rate,
                one_sided_full_ceiling_rate=one_full_rate,
                paired_dataset_ceiling_regression_count=regressions,
                paired_dataset_ceiling_advance_count=advances,
                candidate_overreach_threshold=threshold,
                candidate_acceptance_pass=acceptance,
            )
        )

    return DirectionalTransferPowerComparison(
        comparison_version=COMPARISON_VERSION,
        reference_generator_version=REFERENCE_GENERATOR_VERSION,
        seed=seed,
        simulations_per_scenario=simulations_per_scenario,
        bootstrap_draws_per_interval=bootstrap_draws,
        group_count=group_count,
        step_correlation=float(step_correlation),
        noise_standard_deviation=float(noise_standard_deviation),
        familywise_confidence_level=float(confidence_level),
        same_world_per_method=True,
        same_bootstrap_seed_per_method=True,
        scenarios=tuple(scenario_rows),
        qualification_pass=all(row.candidate_acceptance_pass for row in scenario_rows),
    )
