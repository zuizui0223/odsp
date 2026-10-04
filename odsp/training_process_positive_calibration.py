"""Prospective known-null calibration for training-process positive transfer.

The generator has two crossed stochastic axes: upstream refit draws and
validation blocks. Training-process effects are shared jointly across validation
groups because the same refit identity is evaluated everywhere. Validation
blocks remain independent between groups. Interaction noise varies on the
refit-by-validation-block cells.

This panel is restricted to a two-step information filtration. It is
methodological qualification evidence only and never a biological endpoint.
"""
from __future__ import annotations

from dataclasses import asdict, dataclass
import math

import numpy as np

from .training_process_positive_transfer import (
    certify_training_process_positive_transfer_v1,
)


GENERATOR_VERSION = "crossed_training_refit_validation_known_null_c2_v1"
PROCESS_SHA = "0" * 64


@dataclass(frozen=True)
class TrainingProcessNullScenario:
    scenario_id: str
    distribution: str
    refit_count: int
    blocks_per_group: int
    contrast_count: int
    training_sd: float
    validation_sd: float
    interaction_sd: float
    simulations: int
    one_sided_familywise_false_positive_rate: float
    terminal_false_generalizing_rate: float
    infinite_critical_value_rate: float
    monte_carlo_standard_error: float
    maximum_accepted_rate: float
    acceptance_pass: bool

    def as_dict(self) -> dict[str, object]:
        return asdict(self)


@dataclass(frozen=True)
class TrainingProcessNullCalibration:
    generator_version: str
    seed: int
    simulations_per_scenario: int
    bootstrap_draws_per_interval: int
    group_count: int
    contrast_count: int
    training_cross_cell_correlation: float
    contrast_correlation: float
    familywise_lower_confidence_level: float
    scenarios: tuple[TrainingProcessNullScenario, ...]
    qualification_pass: bool

    def as_dict(self) -> dict[str, object]:
        payload = asdict(self)
        payload["scenarios"] = [row.as_dict() for row in self.scenarios]
        return payload


SCENARIOS = (
    ("balanced-normal-r8-b8", "normal", 8, 8, 0.50, 0.50, 0.50),
    ("training-dominant-normal-r8-b20", "normal", 8, 20, 0.80, 0.20, 0.50),
    ("validation-dominant-normal-r20-b8", "normal", 20, 8, 0.20, 0.80, 0.50),
    ("interaction-dominant-normal-r8-b8", "normal", 8, 8, 0.10, 0.10, 1.00),
    ("balanced-t3-r8-b20", "student_t3", 8, 20, 0.50, 0.50, 0.50),
    ("balanced-normal-r20-b20", "normal", 20, 20, 0.50, 0.50, 0.50),
)


def _crossed_null_world(
    rng: np.random.Generator,
    *,
    refit_count: int,
    blocks_per_group: int,
    group_count: int,
    contrast_count: int,
    training_sd: float,
    validation_sd: float,
    interaction_sd: float,
    training_cross_cell_correlation: float,
    contrast_correlation: float,
    distribution: str,
) -> np.ndarray:
    """Return refit x group x block x contrast zero-mean gains."""

    shared_training = rng.standard_normal((refit_count, 1, 1))
    cell_training = rng.standard_normal(
        (refit_count, group_count, contrast_count)
    )
    training = training_sd * (
        math.sqrt(training_cross_cell_correlation) * shared_training
        + math.sqrt(1.0 - training_cross_cell_correlation) * cell_training
    )

    shared_validation = rng.standard_normal(
        (group_count, blocks_per_group, 1)
    )
    cell_validation = rng.standard_normal(
        (group_count, blocks_per_group, contrast_count)
    )
    validation = validation_sd * (
        math.sqrt(contrast_correlation) * shared_validation
        + math.sqrt(1.0 - contrast_correlation) * cell_validation
    )

    shared_interaction = rng.standard_normal(
        (refit_count, group_count, blocks_per_group, 1)
    )
    cell_interaction = rng.standard_normal(
        (refit_count, group_count, blocks_per_group, contrast_count)
    )
    interaction = interaction_sd * (
        math.sqrt(contrast_correlation) * shared_interaction
        + math.sqrt(1.0 - contrast_correlation) * cell_interaction
    )

    if distribution == "student_t3":
        training = training / np.sqrt(
            rng.chisquare(3, size=(refit_count, 1, 1)) / 3.0
        )
        validation = validation / np.sqrt(
            rng.chisquare(
                3,
                size=(group_count, blocks_per_group, 1),
            )
            / 3.0
        )
        interaction = interaction / np.sqrt(
            rng.chisquare(
                3,
                size=(refit_count, group_count, blocks_per_group, 1),
            )
            / 3.0
        )
    elif distribution != "normal":
        raise ValueError(f"unsupported distribution: {distribution}")

    return (
        training[:, :, None, :]
        + validation[None, :, :, :]
        + interaction
    )


def _flatten_world(
    world: np.ndarray,
) -> tuple[np.ndarray, tuple[str, ...], tuple[str, ...]]:
    refit_count, group_count, block_count, contrast_count = world.shape
    n = group_count * block_count
    gain = np.empty((refit_count, n, contrast_count), dtype=float)
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


def _any_false_positive(result) -> bool:
    return any(
        cell.status == "robust_positive"
        for contrast in result.contrasts
        for cell in contrast.groups
    )


def _terminal_false_generalizing(result) -> bool:
    return bool(result.contrasts) and all(
        contrast.category == "robust_generalizing"
        for contrast in result.contrasts
    )


def run_training_process_positive_null_calibration(
    *,
    seed: int = 20261005,
    simulations_per_scenario: int = 1000,
    bootstrap_draws: int = 500,
    group_count: int = 6,
    contrast_count: int = 2,
    training_cross_cell_correlation: float = 0.35,
    contrast_correlation: float = 0.50,
    confidence_level: float = 0.95,
) -> TrainingProcessNullCalibration:
    """Run the frozen crossed-process global-null qualification panel."""

    if simulations_per_scenario < 100:
        raise ValueError("simulations_per_scenario must be >= 100")
    if bootstrap_draws < 500:
        raise ValueError("bootstrap_draws must be >= 500")
    if group_count < 2:
        raise ValueError("group_count must be >= 2")
    if contrast_count != 2:
        raise ValueError("v1 qualification is frozen to contrast_count == 2")
    if not 0.0 <= training_cross_cell_correlation < 1.0:
        raise ValueError(
            "training_cross_cell_correlation must lie in [0, 1)"
        )
    if not 0.0 <= contrast_correlation < 1.0:
        raise ValueError("contrast_correlation must lie in [0, 1)")
    if not 0.0 < confidence_level < 1.0:
        raise ValueError(
            "confidence_level must lie strictly between zero and one"
        )

    alpha = 1.0 - confidence_level
    maximum_rate = float(
        alpha
        + 2.0
        * math.sqrt(
            alpha * (1.0 - alpha) / simulations_per_scenario
        )
    )
    rng = np.random.default_rng(seed)
    rows: list[TrainingProcessNullScenario] = []

    for scenario_index, (
        scenario_id,
        distribution,
        refit_count,
        block_count,
        training_sd,
        validation_sd,
        interaction_sd,
    ) in enumerate(SCENARIOS):
        false_positive = 0
        terminal_false = 0
        infinite_critical = 0

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
                training_cross_cell_correlation=(
                    training_cross_cell_correlation
                ),
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
                    f"refit-{index:03d}"
                    for index in range(refit_count)
                ),
                training_process_id="known-null-training-process",
                training_process_manifest_sha256=PROCESS_SHA,
                contrast_names=(
                    "pooled->coarse",
                    "coarse->fine",
                ),
                familywise_lower_confidence_level=confidence_level,
                bootstrap_draws=bootstrap_draws,
                seed=local_seed,
                minimum_refits=8,
                minimum_blocks_per_group=8,
            )
            false_positive += int(_any_false_positive(result))
            terminal_false += int(
                _terminal_false_generalizing(result)
            )
            infinite_critical += int(
                result.bootstrap_t_critical_value is not None
                and math.isinf(result.bootstrap_t_critical_value)
            )

        rate = float(false_positive / simulations_per_scenario)
        rows.append(
            TrainingProcessNullScenario(
                scenario_id=scenario_id,
                distribution=distribution,
                refit_count=refit_count,
                blocks_per_group=block_count,
                contrast_count=contrast_count,
                training_sd=training_sd,
                validation_sd=validation_sd,
                interaction_sd=interaction_sd,
                simulations=simulations_per_scenario,
                one_sided_familywise_false_positive_rate=rate,
                terminal_false_generalizing_rate=float(
                    terminal_false / simulations_per_scenario
                ),
                infinite_critical_value_rate=float(
                    infinite_critical / simulations_per_scenario
                ),
                monte_carlo_standard_error=float(
                    math.sqrt(
                        max(rate * (1.0 - rate), 0.0)
                        / simulations_per_scenario
                    )
                ),
                maximum_accepted_rate=maximum_rate,
                acceptance_pass=bool(rate <= maximum_rate),
            )
        )

    return TrainingProcessNullCalibration(
        generator_version=GENERATOR_VERSION,
        seed=seed,
        simulations_per_scenario=simulations_per_scenario,
        bootstrap_draws_per_interval=bootstrap_draws,
        group_count=group_count,
        contrast_count=contrast_count,
        training_cross_cell_correlation=float(
            training_cross_cell_correlation
        ),
        contrast_correlation=float(contrast_correlation),
        familywise_lower_confidence_level=float(confidence_level),
        scenarios=tuple(rows),
        qualification_pass=all(row.acceptance_pass for row in rows),
    )
