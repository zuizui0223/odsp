"""Prospective component-size calibration for training-process IUT v2."""
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
from .training_process_positive_iut import certify_training_process_positive_iut_v2


GENERATOR_VERSION = "crossed_training_process_iut_component_null_c2_v2"


@dataclass(frozen=True)
class TrainingProcessIUTNullScenario:
    scenario_id: str
    distribution: str
    refit_count: int
    blocks_per_group: int
    contrast_count: int
    simulations: int
    component_names: tuple[str, ...]
    component_false_positive_rates: tuple[float, ...]
    maximum_component_false_positive_rate: float
    minimum_component_false_positive_rate: float
    any_cell_false_positive_rate_diagnostic: float
    terminal_false_generalizing_rate_diagnostic: float
    maximum_accepted_component_rate: float
    acceptance_pass: bool

    def as_dict(self) -> dict[str, object]:
        payload = asdict(self)
        payload["component_names"] = list(self.component_names)
        payload["component_false_positive_rates"] = list(
            self.component_false_positive_rates
        )
        return payload


@dataclass(frozen=True)
class TrainingProcessIUTNullCalibration:
    generator_version: str
    seed: int
    simulations_per_scenario: int
    bootstrap_draws_per_interval: int
    group_count: int
    contrast_count: int
    component_lower_confidence_level: float
    training_cross_cell_correlation: float
    contrast_correlation: float
    scenarios: tuple[TrainingProcessIUTNullScenario, ...]
    qualification_pass: bool

    def as_dict(self) -> dict[str, object]:
        payload = asdict(self)
        payload["scenarios"] = [row.as_dict() for row in self.scenarios]
        return payload


def _ordered_cells(result):
    return tuple(
        cell
        for contrast in result.contrasts
        for cell in contrast.groups
    )


def run_training_process_positive_iut_null_calibration(
    *,
    seed: int = 20261007,
    simulations_per_scenario: int = 1000,
    bootstrap_draws: int = 500,
    group_count: int = 6,
    contrast_count: int = 2,
    training_cross_cell_correlation: float = 0.35,
    contrast_correlation: float = 0.50,
    confidence_level: float = 0.95,
) -> TrainingProcessIUTNullCalibration:
    if simulations_per_scenario < 100:
        raise ValueError("simulations_per_scenario must be >= 100")
    if bootstrap_draws < 500:
        raise ValueError("bootstrap_draws must be >= 500")
    if group_count < 2:
        raise ValueError("group_count must be >= 2")
    if contrast_count != 2:
        raise ValueError("v2 qualification is frozen to contrast_count == 2")
    if not 0 <= training_cross_cell_correlation < 1:
        raise ValueError("training_cross_cell_correlation must lie in [0, 1)")
    if not 0 <= contrast_correlation < 1:
        raise ValueError("contrast_correlation must lie in [0, 1)")
    if not 0 < confidence_level < 1:
        raise ValueError("confidence_level must lie strictly between zero and one")

    alpha = 1.0 - confidence_level
    maximum_rate = float(
        alpha + 2.0 * math.sqrt(alpha * (1.0 - alpha) / simulations_per_scenario)
    )
    rng = np.random.default_rng(seed)
    rows: list[TrainingProcessIUTNullScenario] = []

    for scenario_index, (
        scenario_id,
        distribution,
        refit_count,
        block_count,
        training_sd,
        validation_sd,
        interaction_sd,
    ) in enumerate(SCENARIOS):
        component_counts = np.zeros(group_count * contrast_count, dtype=int)
        any_count = 0
        terminal_count = 0
        component_names: tuple[str, ...] | None = None

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
            result = certify_training_process_positive_iut_v2(
                gains,
                groups,
                blocks=blocks,
                refit_ids=tuple(f"refit-{i:03d}" for i in range(refit_count)),
                training_process_id="known-null-iut-v2",
                training_process_manifest_sha256=PROCESS_SHA,
                contrast_names=("pooled->coarse", "coarse->fine"),
                component_lower_confidence_level=confidence_level,
                bootstrap_draws=bootstrap_draws,
                seed=local_seed,
                minimum_refits=8,
                minimum_blocks_per_group=8,
            )
            cells = _ordered_cells(result)
            if component_names is None:
                component_names = tuple(
                    f"{cell.contrast}:{cell.group}" for cell in cells
                )
            positive = np.asarray(
                [cell.status == "robust_positive" for cell in cells],
                dtype=bool,
            )
            component_counts += positive.astype(int)
            any_count += int(np.any(positive))
            terminal_count += int(np.all(positive))

        rates = component_counts.astype(float) / simulations_per_scenario
        assert component_names is not None
        rows.append(
            TrainingProcessIUTNullScenario(
                scenario_id=scenario_id,
                distribution=distribution,
                refit_count=refit_count,
                blocks_per_group=block_count,
                contrast_count=contrast_count,
                simulations=simulations_per_scenario,
                component_names=component_names,
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

    return TrainingProcessIUTNullCalibration(
        generator_version=GENERATOR_VERSION,
        seed=seed,
        simulations_per_scenario=simulations_per_scenario,
        bootstrap_draws_per_interval=bootstrap_draws,
        group_count=group_count,
        contrast_count=contrast_count,
        component_lower_confidence_level=float(confidence_level),
        training_cross_cell_correlation=float(training_cross_cell_correlation),
        contrast_correlation=float(contrast_correlation),
        scenarios=tuple(rows),
        qualification_pass=all(row.acceptance_pass for row in rows),
    )
