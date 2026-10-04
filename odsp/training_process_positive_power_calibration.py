"""Prospective power calibration for training-process positive transfer.

The power panel uses the same crossed random-effects worlds as the frozen null
panel.  A common positive location shift is added conceptually to every
group-by-contrast cell.  Because the process-mean estimator, crossed
studentizer, and centered bootstrap-t statistic are exactly translation
invariant to such a shift, each simulated world needs only one bootstrap fit:
the shifted lower bound equals the null-world lower bound plus the declared
shift.
"""
from __future__ import annotations

from dataclasses import asdict, dataclass
import math

import numpy as np

from .training_process_positive_calibration import (
    PROCESS_SHA,
    SCENARIOS,
    _crossed_null_world,
    _flatten_world,
)
from .training_process_positive_transfer import (
    certify_training_process_positive_transfer_v1,
)


GENERATOR_VERSION = "crossed_training_refit_validation_standardized_power_c2_v1"


@dataclass(frozen=True)
class TrainingProcessPowerScenario:
    scenario_id: str
    distribution: str
    refit_count: int
    blocks_per_group: int
    contrast_count: int
    training_sd: float
    validation_sd: float
    interaction_sd: float
    simulations: int
    oracle_cell_standard_error: float
    moderate_standardized_shift: float
    moderate_gain_shift: float
    moderate_terminal_power: float
    strong_standardized_shift: float
    strong_gain_shift: float
    strong_terminal_power: float
    strong_power_monte_carlo_standard_error: float
    minimum_accepted_strong_terminal_power: float
    monotonic_power: bool
    acceptance_pass: bool

    def as_dict(self) -> dict[str, object]:
        return asdict(self)


@dataclass(frozen=True)
class TrainingProcessPowerCalibration:
    generator_version: str
    seed: int
    simulations_per_scenario: int
    bootstrap_draws_per_interval: int
    group_count: int
    contrast_count: int
    training_cross_cell_correlation: float
    contrast_correlation: float
    familywise_lower_confidence_level: float
    moderate_standardized_shift: float
    strong_standardized_shift: float
    minimum_accepted_strong_terminal_power: float
    scenarios: tuple[TrainingProcessPowerScenario, ...]
    qualification_pass: bool

    def as_dict(self) -> dict[str, object]:
        payload = asdict(self)
        payload["scenarios"] = [row.as_dict() for row in self.scenarios]
        return payload


def _oracle_cell_standard_error(
    *,
    distribution: str,
    refit_count: int,
    blocks_per_group: int,
    training_sd: float,
    validation_sd: float,
    interaction_sd: float,
) -> float:
    variance_multiplier = 3.0 if distribution == "student_t3" else 1.0
    variance = variance_multiplier * (
        training_sd**2 / refit_count
        + validation_sd**2 / blocks_per_group
        + interaction_sd**2 / (refit_count * blocks_per_group)
    )
    return float(math.sqrt(variance))


def _minimum_lower_bound(result) -> float:
    lowers = [
        cell.lower_bound
        for contrast in result.contrasts
        for cell in contrast.groups
    ]
    if not lowers or any(value is None for value in lowers):
        raise ValueError("power calibration requires every cell to be estimable")
    return float(min(float(value) for value in lowers))


def run_training_process_positive_power_calibration(
    *,
    seed: int = 20261006,
    simulations_per_scenario: int = 1000,
    bootstrap_draws: int = 500,
    group_count: int = 6,
    contrast_count: int = 2,
    training_cross_cell_correlation: float = 0.35,
    contrast_correlation: float = 0.50,
    confidence_level: float = 0.95,
    moderate_standardized_shift: float = 3.0,
    strong_standardized_shift: float = 5.0,
    minimum_accepted_strong_terminal_power: float = 0.80,
) -> TrainingProcessPowerCalibration:
    """Run the frozen standardized-alternative process power panel."""

    if simulations_per_scenario < 100:
        raise ValueError("simulations_per_scenario must be >= 100")
    if bootstrap_draws < 500:
        raise ValueError("bootstrap_draws must be >= 500")
    if group_count < 2:
        raise ValueError("group_count must be >= 2")
    if contrast_count != 2:
        raise ValueError("v1 power qualification is frozen to contrast_count == 2")
    if not 0.0 <= training_cross_cell_correlation < 1.0:
        raise ValueError("training_cross_cell_correlation must lie in [0, 1)")
    if not 0.0 <= contrast_correlation < 1.0:
        raise ValueError("contrast_correlation must lie in [0, 1)")
    if not 0.0 < confidence_level < 1.0:
        raise ValueError("confidence_level must lie strictly between zero and one")
    if not 0.0 < moderate_standardized_shift < strong_standardized_shift:
        raise ValueError("standardized shifts must satisfy 0 < moderate < strong")
    if not 0.0 < minimum_accepted_strong_terminal_power < 1.0:
        raise ValueError("minimum accepted strong power must lie in (0, 1)")

    rng = np.random.default_rng(seed)
    rows: list[TrainingProcessPowerScenario] = []

    for scenario_index, (
        scenario_id,
        distribution,
        refit_count,
        block_count,
        training_sd,
        validation_sd,
        interaction_sd,
    ) in enumerate(SCENARIOS):
        oracle_se = _oracle_cell_standard_error(
            distribution=distribution,
            refit_count=refit_count,
            blocks_per_group=block_count,
            training_sd=training_sd,
            validation_sd=validation_sd,
            interaction_sd=interaction_sd,
        )
        moderate_shift = float(moderate_standardized_shift * oracle_se)
        strong_shift = float(strong_standardized_shift * oracle_se)
        moderate_success = 0
        strong_success = 0

        for simulation_index in range(simulations_per_scenario):
            world = _crossed_null_world(
                rng,
                refit_count=refit_count,
                blocks_per_group=block_count,
                group_count=group_count,
                contrast_count=contrast_count,
                training_sd=training_sd,
                validation_sd=validation_sd,
                interaction_sd=interaction_sd,
                training_cross_cell_correlation=training_cross_cell_correlation,
                contrast_correlation=contrast_correlation,
                distribution=distribution,
            )
            gains, groups, blocks = _flatten_world(world)
            local_seed = (
                seed
                + 1000003 * (scenario_index + 1)
                + 10007 * (simulation_index + 1)
            )
            result = certify_training_process_positive_transfer_v1(
                gains,
                groups,
                blocks=blocks,
                refit_ids=tuple(
                    f"refit-{index:03d}" for index in range(refit_count)
                ),
                training_process_id="known-power-training-process",
                training_process_manifest_sha256=PROCESS_SHA,
                contrast_names=("pooled->coarse", "coarse->fine"),
                familywise_lower_confidence_level=confidence_level,
                bootstrap_draws=bootstrap_draws,
                seed=local_seed,
                minimum_refits=8,
                minimum_blocks_per_group=8,
            )
            minimum_lower = _minimum_lower_bound(result)
            moderate_success += int(minimum_lower + moderate_shift > 0.0)
            strong_success += int(minimum_lower + strong_shift > 0.0)

        moderate_power = float(moderate_success / simulations_per_scenario)
        strong_power = float(strong_success / simulations_per_scenario)
        monotonic = bool(strong_power >= moderate_power)
        accepted = bool(
            monotonic
            and strong_power >= minimum_accepted_strong_terminal_power
        )
        rows.append(
            TrainingProcessPowerScenario(
                scenario_id=scenario_id,
                distribution=distribution,
                refit_count=refit_count,
                blocks_per_group=block_count,
                contrast_count=contrast_count,
                training_sd=training_sd,
                validation_sd=validation_sd,
                interaction_sd=interaction_sd,
                simulations=simulations_per_scenario,
                oracle_cell_standard_error=oracle_se,
                moderate_standardized_shift=float(moderate_standardized_shift),
                moderate_gain_shift=moderate_shift,
                moderate_terminal_power=moderate_power,
                strong_standardized_shift=float(strong_standardized_shift),
                strong_gain_shift=strong_shift,
                strong_terminal_power=strong_power,
                strong_power_monte_carlo_standard_error=float(
                    math.sqrt(
                        max(strong_power * (1.0 - strong_power), 0.0)
                        / simulations_per_scenario
                    )
                ),
                minimum_accepted_strong_terminal_power=float(
                    minimum_accepted_strong_terminal_power
                ),
                monotonic_power=monotonic,
                acceptance_pass=accepted,
            )
        )

    return TrainingProcessPowerCalibration(
        generator_version=GENERATOR_VERSION,
        seed=seed,
        simulations_per_scenario=simulations_per_scenario,
        bootstrap_draws_per_interval=bootstrap_draws,
        group_count=group_count,
        contrast_count=contrast_count,
        training_cross_cell_correlation=float(training_cross_cell_correlation),
        contrast_correlation=float(contrast_correlation),
        familywise_lower_confidence_level=float(confidence_level),
        moderate_standardized_shift=float(moderate_standardized_shift),
        strong_standardized_shift=float(strong_standardized_shift),
        minimum_accepted_strong_terminal_power=float(
            minimum_accepted_strong_terminal_power
        ),
        scenarios=tuple(rows),
        qualification_pass=all(row.acceptance_pass for row in rows),
    )
