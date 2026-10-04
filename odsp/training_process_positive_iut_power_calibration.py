"""Prospective power qualification for IUT training-process transfer v2."""
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
from .training_process_positive_power_calibration import (
    _oracle_cell_standard_error,
)
from .training_process_positive_transfer_v2 import (
    certify_training_process_positive_transfer_v2,
)


GENERATOR_VERSION = "crossed_training_process_iut_standardized_power_c2_v2"


@dataclass(frozen=True)
class TrainingProcessIUTPowerScenario:
    scenario_id: str
    distribution: str
    refit_count: int
    blocks_per_group: int
    simulations: int
    oracle_cell_standard_error: float
    carryover_standardized_shift: float
    carryover_gain_shift: float
    carryover_terminal_power: float
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
class TrainingProcessIUTPowerCalibration:
    generator_version: str
    seed: int
    simulations_per_scenario: int
    bootstrap_draws_per_interval: int
    carryover_standardized_shift: float
    strong_standardized_shift: float
    minimum_accepted_strong_terminal_power: float
    scenarios: tuple[TrainingProcessIUTPowerScenario, ...]
    qualification_pass: bool

    def as_dict(self) -> dict[str, object]:
        payload=asdict(self)
        payload["scenarios"]=[row.as_dict() for row in self.scenarios]
        return payload


def _minimum_lower(result) -> float:
    values=[
        cell.cellwise_lower_bound
        for contrast in result.contrasts
        for cell in contrast.groups
    ]
    if not values or any(value is None for value in values):
        raise ValueError("power panel requires every component to be estimable")
    return float(min(float(value) for value in values))


def run_training_process_iut_power_calibration(
    *,
    seed: int = 20261014,
    simulations_per_scenario: int = 1000,
    bootstrap_draws: int = 500,
    carryover_standardized_shift: float = 5.0,
    strong_standardized_shift: float = 6.0,
    minimum_accepted_strong_terminal_power: float = 0.80,
) -> TrainingProcessIUTPowerCalibration:
    if simulations_per_scenario < 100:
        raise ValueError("simulations_per_scenario must be >= 100")
    if bootstrap_draws < 500:
        raise ValueError("bootstrap_draws must be >= 500")
    if not 0.0 < carryover_standardized_shift < strong_standardized_shift:
        raise ValueError("standardized shifts must satisfy 0 < carryover < strong")
    if not 0.0 < minimum_accepted_strong_terminal_power < 1.0:
        raise ValueError("minimum accepted strong terminal power must lie in (0, 1)")

    rng=np.random.default_rng(seed)
    rows=[]
    for scenario_index,(
        scenario_id,distribution,refit_count,block_count,
        training_sd,validation_sd,interaction_sd,
    ) in enumerate(SCENARIOS):
        oracle_se=_oracle_cell_standard_error(
            distribution=distribution,
            refit_count=refit_count,
            blocks_per_group=block_count,
            training_sd=training_sd,
            validation_sd=validation_sd,
            interaction_sd=interaction_sd,
        )
        carry_shift=float(carryover_standardized_shift*oracle_se)
        strong_shift=float(strong_standardized_shift*oracle_se)
        carry_success=0
        strong_success=0

        for simulation_index in range(simulations_per_scenario):
            world=_crossed_null_world(
                rng,
                refit_count=refit_count,
                blocks_per_group=block_count,
                group_count=6,
                contrast_count=2,
                training_sd=training_sd,
                validation_sd=validation_sd,
                interaction_sd=interaction_sd,
                training_cross_cell_correlation=0.35,
                contrast_correlation=0.5,
                distribution=distribution,
            )
            gains,groups,blocks=_flatten_world(world)
            local_seed=(
                seed
                +1000003*(scenario_index+1)
                +10007*(simulation_index+1)
            )
            result=certify_training_process_positive_transfer_v2(
                gains,
                groups,
                blocks=blocks,
                refit_ids=tuple(
                    f"refit-{index:03d}" for index in range(refit_count)
                ),
                training_process_id="known-power-iut-process-v2",
                training_process_manifest_sha256=PROCESS_SHA,
                contrast_names=("pooled->coarse","coarse->fine"),
                cellwise_lower_confidence_level=0.95,
                bootstrap_draws=bootstrap_draws,
                seed=local_seed,
                minimum_refits=8,
                minimum_blocks_per_group=8,
            )
            minimum_lower=_minimum_lower(result)
            carry_success += int(minimum_lower+carry_shift>0.0)
            strong_success += int(minimum_lower+strong_shift>0.0)

        carry_power=float(carry_success/simulations_per_scenario)
        strong_power=float(strong_success/simulations_per_scenario)
        monotonic=bool(strong_power>=carry_power)
        rows.append(
            TrainingProcessIUTPowerScenario(
                scenario_id=scenario_id,
                distribution=distribution,
                refit_count=refit_count,
                blocks_per_group=block_count,
                simulations=simulations_per_scenario,
                oracle_cell_standard_error=oracle_se,
                carryover_standardized_shift=float(carryover_standardized_shift),
                carryover_gain_shift=carry_shift,
                carryover_terminal_power=carry_power,
                strong_standardized_shift=float(strong_standardized_shift),
                strong_gain_shift=strong_shift,
                strong_terminal_power=strong_power,
                strong_power_monte_carlo_standard_error=float(
                    math.sqrt(
                        max(strong_power*(1.0-strong_power),0.0)
                        /simulations_per_scenario
                    )
                ),
                minimum_accepted_strong_terminal_power=float(
                    minimum_accepted_strong_terminal_power
                ),
                monotonic_power=monotonic,
                acceptance_pass=bool(
                    monotonic
                    and strong_power>=minimum_accepted_strong_terminal_power
                ),
            )
        )

    return TrainingProcessIUTPowerCalibration(
        generator_version=GENERATOR_VERSION,
        seed=seed,
        simulations_per_scenario=simulations_per_scenario,
        bootstrap_draws_per_interval=bootstrap_draws,
        carryover_standardized_shift=float(carryover_standardized_shift),
        strong_standardized_shift=float(strong_standardized_shift),
        minimum_accepted_strong_terminal_power=float(
            minimum_accepted_strong_terminal_power
        ),
        scenarios=tuple(rows),
        qualification_pass=all(row.acceptance_pass for row in rows),
    )
