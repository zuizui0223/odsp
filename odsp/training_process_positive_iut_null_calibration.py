"""Prospective null qualification for IUT training-process transfer v2.

The v2 global claim is a conjunction of component alternatives. Its size is
therefore governed by the one-sided size of each component test, not by the
probability that any component rejects under a global null.

The crossed generator is symmetric over group labels and over the two contrast
labels. The primary qualification metric is a predeclared sentinel component
(g00, first contrast). Rejection rates for every other component and the
all-component terminal false-generalizing rate are retained as diagnostics.
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
from .training_process_positive_transfer_v2 import (
    certify_training_process_positive_transfer_v2,
)


GENERATOR_VERSION = "crossed_training_process_iut_component_null_c2_v2"


@dataclass(frozen=True)
class TrainingProcessIUTNullScenario:
    scenario_id: str
    distribution: str
    refit_count: int
    blocks_per_group: int
    simulations: int
    sentinel_component_false_positive_rate: float
    mean_component_false_positive_rate: float
    maximum_component_false_positive_rate: float
    terminal_false_generalizing_rate: float
    sentinel_monte_carlo_standard_error: float
    maximum_accepted_sentinel_rate: float
    acceptance_pass: bool

    def as_dict(self) -> dict[str, object]:
        return asdict(self)


@dataclass(frozen=True)
class TrainingProcessIUTNullCalibration:
    generator_version: str
    seed: int
    simulations_per_scenario: int
    bootstrap_draws_per_interval: int
    group_count: int
    contrast_count: int
    cellwise_lower_confidence_level: float
    sentinel_group: str
    sentinel_contrast: str
    scenarios: tuple[TrainingProcessIUTNullScenario, ...]
    qualification_pass: bool

    def as_dict(self) -> dict[str, object]:
        payload=asdict(self)
        payload["scenarios"]=[row.as_dict() for row in self.scenarios]
        return payload


def _cells(result):
    return [
        cell
        for contrast in result.contrasts
        for cell in contrast.groups
    ]


def run_training_process_iut_null_calibration(
    *,
    seed: int = 20261013,
    simulations_per_scenario: int = 1000,
    bootstrap_draws: int = 500,
    confidence_level: float = 0.95,
) -> TrainingProcessIUTNullCalibration:
    if simulations_per_scenario < 100:
        raise ValueError("simulations_per_scenario must be >= 100")
    if bootstrap_draws < 500:
        raise ValueError("bootstrap_draws must be >= 500")
    if not 0.0 < confidence_level < 1.0:
        raise ValueError("confidence_level must lie in (0, 1)")

    alpha=1.0-confidence_level
    maximum_rate=float(
        alpha+2.0*math.sqrt(alpha*(1.0-alpha)/simulations_per_scenario)
    )
    rng=np.random.default_rng(seed)
    rows=[]

    for scenario_index,(
        scenario_id,distribution,refit_count,block_count,
        training_sd,validation_sd,interaction_sd,
    ) in enumerate(SCENARIOS):
        sentinel=0
        terminal=0
        component_counts=np.zeros(12,dtype=int)

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
                training_process_id="known-null-iut-process-v2",
                training_process_manifest_sha256=PROCESS_SHA,
                contrast_names=("pooled->coarse","coarse->fine"),
                cellwise_lower_confidence_level=confidence_level,
                bootstrap_draws=bootstrap_draws,
                seed=local_seed,
                minimum_refits=8,
                minimum_blocks_per_group=8,
            )
            cells=_cells(result)
            rejected=np.asarray(
                [cell.status=="robust_positive" for cell in cells],
                dtype=bool,
            )
            component_counts += rejected.astype(int)
            sentinel += int(result.contrasts[0].groups[0].status=="robust_positive")
            terminal += int(result.global_category=="robust_generalizing")

        component_rates=component_counts/simulations_per_scenario
        sentinel_rate=float(sentinel/simulations_per_scenario)
        rows.append(
            TrainingProcessIUTNullScenario(
                scenario_id=scenario_id,
                distribution=distribution,
                refit_count=refit_count,
                blocks_per_group=block_count,
                simulations=simulations_per_scenario,
                sentinel_component_false_positive_rate=sentinel_rate,
                mean_component_false_positive_rate=float(np.mean(component_rates)),
                maximum_component_false_positive_rate=float(np.max(component_rates)),
                terminal_false_generalizing_rate=float(
                    terminal/simulations_per_scenario
                ),
                sentinel_monte_carlo_standard_error=float(
                    math.sqrt(
                        max(sentinel_rate*(1.0-sentinel_rate),0.0)
                        /simulations_per_scenario
                    )
                ),
                maximum_accepted_sentinel_rate=maximum_rate,
                acceptance_pass=bool(sentinel_rate<=maximum_rate),
            )
        )

    return TrainingProcessIUTNullCalibration(
        generator_version=GENERATOR_VERSION,
        seed=seed,
        simulations_per_scenario=simulations_per_scenario,
        bootstrap_draws_per_interval=bootstrap_draws,
        group_count=6,
        contrast_count=2,
        cellwise_lower_confidence_level=float(confidence_level),
        sentinel_group="g00",
        sentinel_contrast="pooled->coarse",
        scenarios=tuple(rows),
        qualification_pass=all(row.acceptance_pass for row in rows),
    )
