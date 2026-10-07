"""Prospective operating-characteristic panel for future-refit success probability v1."""
from __future__ import annotations

from dataclasses import asdict, dataclass
import math

import numpy as np

from .training_process_future_refit_success_probability import (
    certify_future_refit_success_probability_v1,
)


GENERATOR_VERSION = (
    "future_refit_success_probability_known_p_boundary_failure_v1"
)
PROCESS_SHA = "7" * 64
COVERAGE_SCENARIOS = (
    ("p50-normal-r8-b8", "normal", 8, 8, 0.50),
    ("p80-normal-r8-b20", "normal", 8, 20, 0.80),
    ("p80-normal-r20-b8", "normal", 20, 8, 0.80),
    ("p95-normal-r20-b20", "normal", 20, 20, 0.95),
    ("p80-t3-r8-b20", "student_t3", 8, 20, 0.80),
    ("p50-t3-r20-b20", "student_t3", 20, 20, 0.50),
)
POWER_SCENARIOS = (
    ("all-success-r8-b8", "normal", 8, 8),
    ("all-success-r20-b8", "normal", 20, 8),
)


@dataclass(frozen=True)
class FutureRefitProbabilityCoverageScenario:
    scenario_id: str
    distribution: str
    refit_count: int
    blocks_per_group: int
    true_success_probability: float
    simulations: int
    strong_positive_shift_oracle_se: float
    overall_overclaim_rate: float
    validation_overcertification_rate: float
    mean_true_success_count: float
    mean_certified_success_count: float
    mean_reported_probability_lower_bound: float
    maximum_accepted_overall_overclaim_rate: float
    maximum_accepted_validation_overcertification_rate: float
    overall_acceptance_pass: bool
    validation_acceptance_pass: bool
    acceptance_pass: bool

    def as_dict(self) -> dict[str, object]:
        return asdict(self)


@dataclass(frozen=True)
class FutureRefitProbabilityPowerScenario:
    scenario_id: str
    distribution: str
    refit_count: int
    blocks_per_group: int
    simulations: int
    positive_shift_oracle_se: float
    all_refits_certified_power: float
    mean_certified_success_count: float
    mean_reported_probability_lower_bound: float
    maximum_possible_probability_lower_bound: float
    minimum_accepted_power: float
    acceptance_pass: bool

    def as_dict(self) -> dict[str, object]:
        return asdict(self)


@dataclass(frozen=True)
class FutureRefitProbabilityCalibration:
    schema_version: int
    generator_version: str
    seed: int
    simulations_per_scenario: int
    bootstrap_draws_per_interval: int
    group_count: int
    contrast_count: int
    validation_alpha: float
    process_alpha: float
    overall_alpha: float
    training_cross_refit_validation_noise_correlation: float
    contrast_correlation: float
    coverage_scenarios: tuple[FutureRefitProbabilityCoverageScenario, ...]
    power_scenarios: tuple[FutureRefitProbabilityPowerScenario, ...]
    qualification_pass: bool

    def as_dict(self) -> dict[str, object]:
        payload = asdict(self)
        payload["coverage_scenarios"] = [
            row.as_dict() for row in self.coverage_scenarios
        ]
        payload["power_scenarios"] = [
            row.as_dict() for row in self.power_scenarios
        ]
        return payload


def _primitive(
    rng: np.random.Generator,
    shape: tuple[int, ...],
    distribution: str,
) -> np.ndarray:
    if distribution == "normal":
        return rng.standard_normal(shape)
    if distribution == "student_t3":
        return rng.standard_t(3, size=shape) / math.sqrt(3.0)
    raise ValueError(f"unknown distribution: {distribution}")


def _correlated_contrasts(
    rng: np.random.Generator,
    leading_shape: tuple[int, ...],
    contrast_count: int,
    *,
    correlation: float,
    distribution: str,
) -> np.ndarray:
    shared = _primitive(rng, leading_shape + (1,), distribution)
    cell = _primitive(
        rng,
        leading_shape + (contrast_count,),
        distribution,
    )
    return (
        math.sqrt(correlation) * shared
        + math.sqrt(1.0 - correlation) * cell
    )


def _known_probability_world(
    rng: np.random.Generator,
    *,
    refit_count: int,
    blocks_per_group: int,
    group_count: int,
    contrast_count: int,
    p_success: float,
    positive_shift_oracle_se: float,
    training_cross_refit_validation_noise_correlation: float,
    contrast_correlation: float,
    distribution: str,
) -> tuple[np.ndarray, np.ndarray]:
    """Generate a crossed validation world with known future-refit success p."""

    if not 0.0 <= p_success <= 1.0:
        raise ValueError("p_success must lie in [0, 1]")
    if positive_shift_oracle_se <= 0.0:
        raise ValueError("positive_shift_oracle_se must be positive")

    success = rng.random(refit_count) < p_success
    oracle_se = 1.0 / math.sqrt(float(blocks_per_group))
    strong_shift = positive_shift_oracle_se * oracle_se
    mean = np.full(
        (refit_count, group_count, contrast_count),
        strong_shift,
        dtype=float,
    )

    failure_refits = np.flatnonzero(~success)
    for refit_index in failure_refits.tolist():
        cell_index = int(rng.integers(0, group_count * contrast_count))
        group_index, contrast_index = divmod(cell_index, contrast_count)
        mean[refit_index, group_index, contrast_index] = 0.0

    common_validation = _correlated_contrasts(
        rng,
        (group_count, blocks_per_group),
        contrast_count,
        correlation=contrast_correlation,
        distribution=distribution,
    )
    refit_interaction = _correlated_contrasts(
        rng,
        (refit_count, group_count, blocks_per_group),
        contrast_count,
        correlation=contrast_correlation,
        distribution=distribution,
    )
    rho = training_cross_refit_validation_noise_correlation
    noise = (
        math.sqrt(rho) * common_validation[None, :, :, :]
        + math.sqrt(1.0 - rho) * refit_interaction
    )
    world = mean[:, :, None, :] + noise
    return world.astype(float), success.astype(bool)


def _flatten_world(
    world: np.ndarray,
) -> tuple[np.ndarray, tuple[str, ...], tuple[str, ...]]:
    refit_count, group_count, block_count, contrast_count = world.shape
    gain = np.empty(
        (refit_count, group_count * block_count, contrast_count),
        dtype=float,
    )
    groups: list[str] = []
    blocks: list[str] = []
    row = 0
    for group_index in range(group_count):
        for block_index in range(block_count):
            gain[:, row, :] = world[:, group_index, block_index, :]
            groups.append(f"g{group_index:02d}")
            blocks.append(f"g{group_index:02d}-b{block_index:03d}")
            row += 1
    return gain, tuple(groups), tuple(blocks)


def _run_world(
    world: np.ndarray,
    *,
    seed: int,
    bootstrap_draws: int,
    validation_alpha: float,
    process_alpha: float,
):
    gain, groups, blocks = _flatten_world(world)
    refit_count = world.shape[0]
    return certify_future_refit_success_probability_v1(
        gain,
        groups,
        blocks=blocks,
        refit_ids=tuple(f"refit-{index:03d}" for index in range(refit_count)),
        training_process_id="known-probability-calibration-v1",
        training_process_manifest_sha256=PROCESS_SHA,
        contrast_names=("pooled->coarse", "coarse->fine"),
        validation_alpha=validation_alpha,
        process_alpha=process_alpha,
        bootstrap_draws=bootstrap_draws,
        seed=seed,
        minimum_refits=8,
        minimum_blocks_per_group=8,
        gain_tolerance=0.0,
    )


def run_future_refit_success_probability_v1_calibration(
    *,
    seed: int = 20261016,
    simulations_per_scenario: int = 1000,
    bootstrap_draws: int = 500,
    group_count: int = 6,
    contrast_count: int = 2,
    validation_alpha: float = 0.025,
    process_alpha: float = 0.025,
    training_cross_refit_validation_noise_correlation: float = 0.35,
    contrast_correlation: float = 0.50,
    coverage_positive_shift_oracle_se: float = 6.0,
    power_positive_shift_oracle_se: float = 8.0,
    minimum_accepted_power: float = 0.80,
) -> FutureRefitProbabilityCalibration:
    """Run the frozen coverage and strong-signal power panels."""

    if simulations_per_scenario < 100:
        raise ValueError("simulations_per_scenario must be >= 100")
    if bootstrap_draws < 500:
        raise ValueError("bootstrap_draws must be >= 500")
    if group_count != 6:
        raise ValueError("v1 calibration is frozen to group_count == 6")
    if contrast_count != 2:
        raise ValueError("v1 calibration is frozen to contrast_count == 2")
    if not 0.0 < validation_alpha < 1.0:
        raise ValueError("validation_alpha must lie in (0, 1)")
    if not 0.0 < process_alpha < 1.0:
        raise ValueError("process_alpha must lie in (0, 1)")
    if not math.isclose(
        validation_alpha + process_alpha,
        0.05,
        rel_tol=0.0,
        abs_tol=1e-15,
    ):
        raise ValueError("frozen v1 calibration requires total alpha == 0.05")
    if not 0.0 <= training_cross_refit_validation_noise_correlation < 1.0:
        raise ValueError(
            "training_cross_refit_validation_noise_correlation must lie in [0,1)"
        )
    if not 0.0 <= contrast_correlation < 1.0:
        raise ValueError("contrast_correlation must lie in [0,1)")
    if coverage_positive_shift_oracle_se != 6.0:
        raise ValueError(
            "coverage panel is frozen to a 6-oracle-SE positive shift"
        )
    if power_positive_shift_oracle_se != 8.0:
        raise ValueError(
            "power panel is frozen to an 8-oracle-SE positive shift"
        )
    if minimum_accepted_power != 0.80:
        raise ValueError("power gate is frozen to 0.80")

    overall_alpha = validation_alpha + process_alpha
    max_overall_rate = float(
        overall_alpha
        + 2.0
        * math.sqrt(
            overall_alpha
            * (1.0 - overall_alpha)
            / simulations_per_scenario
        )
    )
    max_validation_rate = float(
        validation_alpha
        + 2.0
        * math.sqrt(
            validation_alpha
            * (1.0 - validation_alpha)
            / simulations_per_scenario
        )
    )

    rng = np.random.default_rng(seed)
    coverage_rows: list[FutureRefitProbabilityCoverageScenario] = []

    for scenario_index, (
        scenario_id,
        distribution,
        refit_count,
        blocks_per_group,
        p_success,
    ) in enumerate(COVERAGE_SCENARIOS):
        overclaim = 0
        overcertification = 0
        true_counts: list[int] = []
        certified_counts: list[int] = []
        lower_bounds: list[float] = []

        for simulation_index in range(simulations_per_scenario):
            world, true_success = _known_probability_world(
                rng,
                refit_count=refit_count,
                blocks_per_group=blocks_per_group,
                group_count=group_count,
                contrast_count=contrast_count,
                p_success=p_success,
                positive_shift_oracle_se=coverage_positive_shift_oracle_se,
                training_cross_refit_validation_noise_correlation=(
                    training_cross_refit_validation_noise_correlation
                ),
                contrast_correlation=contrast_correlation,
                distribution=distribution,
            )
            result = _run_world(
                world,
                seed=(
                    seed
                    + 1_000_003 * (scenario_index + 1)
                    + 10_007 * (simulation_index + 1)
                ),
                bootstrap_draws=bootstrap_draws,
                validation_alpha=validation_alpha,
                process_alpha=process_alpha,
            )
            true_count = int(np.count_nonzero(true_success))
            certified = int(result.certified_success_count)
            lower = float(
                result.future_refit_success_probability_lower_bound
            )
            true_counts.append(true_count)
            certified_counts.append(certified)
            lower_bounds.append(lower)
            overcertification += int(certified > true_count)
            overclaim += int(lower > p_success + 1e-12)

        overall_rate = float(overclaim / simulations_per_scenario)
        validation_rate = float(
            overcertification / simulations_per_scenario
        )
        overall_pass = bool(overall_rate <= max_overall_rate)
        validation_pass = bool(validation_rate <= max_validation_rate)
        coverage_rows.append(
            FutureRefitProbabilityCoverageScenario(
                scenario_id=scenario_id,
                distribution=distribution,
                refit_count=refit_count,
                blocks_per_group=blocks_per_group,
                true_success_probability=float(p_success),
                simulations=simulations_per_scenario,
                strong_positive_shift_oracle_se=float(
                    coverage_positive_shift_oracle_se
                ),
                overall_overclaim_rate=overall_rate,
                validation_overcertification_rate=validation_rate,
                mean_true_success_count=float(np.mean(true_counts)),
                mean_certified_success_count=float(
                    np.mean(certified_counts)
                ),
                mean_reported_probability_lower_bound=float(
                    np.mean(lower_bounds)
                ),
                maximum_accepted_overall_overclaim_rate=max_overall_rate,
                maximum_accepted_validation_overcertification_rate=(
                    max_validation_rate
                ),
                overall_acceptance_pass=overall_pass,
                validation_acceptance_pass=validation_pass,
                acceptance_pass=bool(overall_pass and validation_pass),
            )
        )

    power_rows: list[FutureRefitProbabilityPowerScenario] = []
    for scenario_index, (
        scenario_id,
        distribution,
        refit_count,
        blocks_per_group,
    ) in enumerate(POWER_SCENARIOS):
        all_certified = 0
        counts: list[int] = []
        lower_bounds: list[float] = []
        maximum_bound: float | None = None

        for simulation_index in range(simulations_per_scenario):
            world, true_success = _known_probability_world(
                rng,
                refit_count=refit_count,
                blocks_per_group=blocks_per_group,
                group_count=group_count,
                contrast_count=contrast_count,
                p_success=1.0,
                positive_shift_oracle_se=power_positive_shift_oracle_se,
                training_cross_refit_validation_noise_correlation=(
                    training_cross_refit_validation_noise_correlation
                ),
                contrast_correlation=contrast_correlation,
                distribution=distribution,
            )
            if not bool(np.all(true_success)):
                raise AssertionError("p_success=1 power world produced a failure")
            result = _run_world(
                world,
                seed=(
                    seed
                    + 20_000_033
                    + 1_000_003 * (scenario_index + 1)
                    + 10_007 * (simulation_index + 1)
                ),
                bootstrap_draws=bootstrap_draws,
                validation_alpha=validation_alpha,
                process_alpha=process_alpha,
            )
            certified = int(result.certified_success_count)
            counts.append(certified)
            lower_bounds.append(
                float(result.future_refit_success_probability_lower_bound)
            )
            all_certified += int(certified == refit_count)
            if maximum_bound is None:
                maximum_bound = float(
                    result.maximum_possible_lower_bound_if_all_observed_refits_certified
                )

        power = float(all_certified / simulations_per_scenario)
        assert maximum_bound is not None
        power_rows.append(
            FutureRefitProbabilityPowerScenario(
                scenario_id=scenario_id,
                distribution=distribution,
                refit_count=refit_count,
                blocks_per_group=blocks_per_group,
                simulations=simulations_per_scenario,
                positive_shift_oracle_se=float(
                    power_positive_shift_oracle_se
                ),
                all_refits_certified_power=power,
                mean_certified_success_count=float(np.mean(counts)),
                mean_reported_probability_lower_bound=float(
                    np.mean(lower_bounds)
                ),
                maximum_possible_probability_lower_bound=maximum_bound,
                minimum_accepted_power=float(minimum_accepted_power),
                acceptance_pass=bool(power >= minimum_accepted_power),
            )
        )

    qualification = all(row.acceptance_pass for row in coverage_rows) and all(
        row.acceptance_pass for row in power_rows
    )
    return FutureRefitProbabilityCalibration(
        schema_version=1,
        generator_version=GENERATOR_VERSION,
        seed=seed,
        simulations_per_scenario=simulations_per_scenario,
        bootstrap_draws_per_interval=bootstrap_draws,
        group_count=group_count,
        contrast_count=contrast_count,
        validation_alpha=float(validation_alpha),
        process_alpha=float(process_alpha),
        overall_alpha=float(overall_alpha),
        training_cross_refit_validation_noise_correlation=float(
            training_cross_refit_validation_noise_correlation
        ),
        contrast_correlation=float(contrast_correlation),
        coverage_scenarios=tuple(coverage_rows),
        power_scenarios=tuple(power_rows),
        qualification_pass=bool(qualification),
    )
