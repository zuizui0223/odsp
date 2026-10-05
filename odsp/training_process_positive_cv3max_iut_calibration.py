"""Prospective null and power qualification panels for CV3max IUT v4."""
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
from .training_process_positive_power_calibration import _oracle_cell_standard_error
from .training_process_positive_cv3max_iut import (
    certify_training_process_positive_cv3max_iut_v4,
)


NULL_GENERATOR_VERSION = "crossed_training_process_cv3max_iut_component_null_c2_v4"
POWER_GENERATOR_VERSION = "crossed_training_process_cv3max_iut_standardized_power_c2_v4"


@dataclass(frozen=True)
class CV3MaxNullScenario:
    scenario_id: str
    distribution: str
    refit_count: int
    blocks_per_group: int
    contrast_count: int
    simulations: int
    component_false_positive_rates: tuple[float, ...]
    maximum_component_false_positive_rate: float
    minimum_component_false_positive_rate: float
    any_cell_false_positive_rate_diagnostic: float
    terminal_false_generalizing_rate_diagnostic: float
    maximum_accepted_component_rate: float
    acceptance_pass: bool

    def as_dict(self) -> dict[str, object]:
        payload = asdict(self)
        payload["component_false_positive_rates"] = list(
            self.component_false_positive_rates
        )
        return payload


@dataclass(frozen=True)
class CV3MaxNullCalibration:
    generator_version: str
    seed: int
    simulations_per_scenario: int
    group_count: int
    contrast_count: int
    component_one_sided_alpha: float
    scenarios: tuple[CV3MaxNullScenario, ...]
    qualification_pass: bool

    def as_dict(self) -> dict[str, object]:
        payload = asdict(self)
        payload["scenarios"] = [row.as_dict() for row in self.scenarios]
        return payload


@dataclass(frozen=True)
class CV3MaxPowerScenario:
    scenario_id: str
    distribution: str
    refit_count: int
    blocks_per_group: int
    contrast_count: int
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
class CV3MaxPowerCalibration:
    generator_version: str
    seed: int
    simulations_per_scenario: int
    group_count: int
    contrast_count: int
    component_one_sided_alpha: float
    moderate_standardized_shift: float
    strong_standardized_shift: float
    minimum_accepted_strong_terminal_power: float
    scenarios: tuple[CV3MaxPowerScenario, ...]
    qualification_pass: bool

    def as_dict(self) -> dict[str, object]:
        payload = asdict(self)
        payload["scenarios"] = [row.as_dict() for row in self.scenarios]
        return payload


def _run_world(world: np.ndarray):
    gains, groups, blocks = _flatten_world(world)
    return certify_training_process_positive_cv3max_iut_v4(
        gains,
        groups,
        blocks=blocks,
        refit_ids=tuple(f"refit-{i:03d}" for i in range(world.shape[0])),
        training_process_id="known-calibration-cv3max-v4",
        training_process_manifest_sha256=PROCESS_SHA,
        contrast_names=("pooled->coarse", "coarse->fine"),
        component_one_sided_alpha=0.05,
        minimum_refits=8,
        minimum_blocks_per_group=8,
    )


def run_training_process_positive_cv3max_iut_v4_null_calibration(
    *,
    seed: int = 20261011,
    simulations_per_scenario: int = 1000,
    group_count: int = 6,
    contrast_count: int = 2,
    training_cross_cell_correlation: float = 0.35,
    contrast_correlation: float = 0.50,
) -> CV3MaxNullCalibration:
    if simulations_per_scenario < 100:
        raise ValueError("simulations_per_scenario must be >= 100")
    if group_count < 2:
        raise ValueError("group_count must be >= 2")
    if contrast_count != 2:
        raise ValueError("v4 qualification is frozen to contrast_count == 2")
    if not 0 <= training_cross_cell_correlation < 1:
        raise ValueError("training_cross_cell_correlation must lie in [0, 1)")
    if not 0 <= contrast_correlation < 1:
        raise ValueError("contrast_correlation must lie in [0, 1)")

    alpha = 0.05
    maximum_rate = float(
        alpha + 2.0 * math.sqrt(alpha * (1.0 - alpha) / simulations_per_scenario)
    )
    rng = np.random.default_rng(seed)
    rows: list[CV3MaxNullScenario] = []

    for (
        scenario_id,
        distribution,
        refit_count,
        block_count,
        training_sd,
        validation_sd,
        interaction_sd,
    ) in SCENARIOS:
        component_counts = np.zeros(group_count * contrast_count, dtype=int)
        any_count = 0
        terminal_count = 0
        for _ in range(simulations_per_scenario):
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
            result = _run_world(world)
            positive = np.asarray(
                [
                    cell.status == "robust_positive"
                    for contrast in result.contrasts
                    for cell in contrast.groups
                ],
                dtype=bool,
            )
            component_counts += positive.astype(int)
            any_count += int(np.any(positive))
            terminal_count += int(np.all(positive))

        rates = component_counts.astype(float) / simulations_per_scenario
        rows.append(
            CV3MaxNullScenario(
                scenario_id=scenario_id,
                distribution=distribution,
                refit_count=refit_count,
                blocks_per_group=block_count,
                contrast_count=contrast_count,
                simulations=simulations_per_scenario,
                component_false_positive_rates=tuple(float(x) for x in rates),
                maximum_component_false_positive_rate=float(np.max(rates)),
                minimum_component_false_positive_rate=float(np.min(rates)),
                any_cell_false_positive_rate_diagnostic=float(
                    any_count / simulations_per_scenario
                ),
                terminal_false_generalizing_rate_diagnostic=float(
                    terminal_count / simulations_per_scenario
                ),
                maximum_accepted_component_rate=maximum_rate,
                acceptance_pass=bool(np.max(rates) <= maximum_rate),
            )
        )

    return CV3MaxNullCalibration(
        generator_version=NULL_GENERATOR_VERSION,
        seed=seed,
        simulations_per_scenario=simulations_per_scenario,
        group_count=group_count,
        contrast_count=contrast_count,
        component_one_sided_alpha=alpha,
        scenarios=tuple(rows),
        qualification_pass=all(row.acceptance_pass for row in rows),
    )


def run_training_process_positive_cv3max_iut_v4_power_calibration(
    *,
    seed: int = 20261012,
    simulations_per_scenario: int = 1000,
    group_count: int = 6,
    contrast_count: int = 2,
    training_cross_cell_correlation: float = 0.35,
    contrast_correlation: float = 0.50,
    moderate_standardized_shift: float = 3.0,
    strong_standardized_shift: float = 5.0,
    minimum_accepted_strong_terminal_power: float = 0.80,
) -> CV3MaxPowerCalibration:
    if simulations_per_scenario < 100:
        raise ValueError("simulations_per_scenario must be >= 100")
    if group_count < 2:
        raise ValueError("group_count must be >= 2")
    if contrast_count != 2:
        raise ValueError("v4 power qualification is frozen to contrast_count == 2")
    if not 0 < moderate_standardized_shift < strong_standardized_shift:
        raise ValueError("standardized shifts must satisfy 0 < moderate < strong")
    if not 0 < minimum_accepted_strong_terminal_power < 1:
        raise ValueError("minimum accepted power must lie in (0, 1)")

    rng = np.random.default_rng(seed)
    rows: list[CV3MaxPowerScenario] = []

    for (
        scenario_id,
        distribution,
        refit_count,
        block_count,
        training_sd,
        validation_sd,
        interaction_sd,
    ) in SCENARIOS:
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

        for _ in range(simulations_per_scenario):
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
            result = _run_world(world)
            lowers = [
                cell.lower_bound
                for contrast in result.contrasts
                for cell in contrast.groups
            ]
            if any(value is None for value in lowers):
                raise ValueError("power calibration requires every cell estimable")
            minimum_lower = min(float(value) for value in lowers)
            moderate_success += int(minimum_lower + moderate_shift > 0.0)
            strong_success += int(minimum_lower + strong_shift > 0.0)

        moderate_power = float(moderate_success / simulations_per_scenario)
        strong_power = float(strong_success / simulations_per_scenario)
        monotonic = bool(strong_power >= moderate_power)
        rows.append(
            CV3MaxPowerScenario(
                scenario_id=scenario_id,
                distribution=distribution,
                refit_count=refit_count,
                blocks_per_group=block_count,
                contrast_count=contrast_count,
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
                acceptance_pass=bool(
                    monotonic and strong_power >= minimum_accepted_strong_terminal_power
                ),
            )
        )

    return CV3MaxPowerCalibration(
        generator_version=POWER_GENERATOR_VERSION,
        seed=seed,
        simulations_per_scenario=simulations_per_scenario,
        group_count=group_count,
        contrast_count=contrast_count,
        component_one_sided_alpha=0.05,
        moderate_standardized_shift=float(moderate_standardized_shift),
        strong_standardized_shift=float(strong_standardized_shift),
        minimum_accepted_strong_terminal_power=float(
            minimum_accepted_strong_terminal_power
        ),
        scenarios=tuple(rows),
        qualification_pass=all(row.acceptance_pass for row in rows),
    )
