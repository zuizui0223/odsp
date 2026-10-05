"""Adversarial null support envelope for the frozen v5 CV3(2) process IUT."""
from __future__ import annotations

from dataclasses import asdict, dataclass
import math
import numpy as np

from .training_process_positive_calibration import PROCESS_SHA
from .training_process_positive_cv3two_iut import (
    certify_training_process_positive_cv3two_iut_v5,
)


GENERATOR_VERSION = "training_process_cv3two_v5_adversarial_support_v1"
SCENARIOS = (
    ("skewed-lognormal-r8-b8", "skewed_lognormal", 8, 8, 0.5, 0.5, 0.5, None),
    ("contaminated-normal-r8-b20", "contaminated_normal", 8, 20, 0.5, 0.5, 0.5, None),
    ("rademacher-r8-b8", "rademacher", 8, 8, 0.5, 0.5, 0.5, None),
    (
        "unequal-block-weight-normal-r8-b8",
        "normal",
        8,
        8,
        0.5,
        0.5,
        0.5,
        (0.5, 0.5, 1.0, 1.0, 2.0, 2.0, 4.0, 8.0),
    ),
    ("heteroskedastic-interaction-r8-b8", "heteroskedastic_interaction", 8, 8, 0.2, 0.2, 0.9, None),
)


@dataclass(frozen=True)
class V5SupportScenario:
    scenario_id: str
    distribution: str
    refit_count: int
    blocks_per_group: int
    simulations: int
    maximum_component_false_positive_rate: float
    minimum_component_false_positive_rate: float
    any_cell_false_positive_rate_diagnostic: float
    terminal_false_generalizing_rate_diagnostic: float
    maximum_accepted_component_rate: float
    acceptance_pass: bool

    def as_dict(self) -> dict[str, object]:
        return asdict(self)


@dataclass(frozen=True)
class V5SupportEnvelope:
    generator_version: str
    seed: int
    simulations_per_scenario: int
    group_count: int
    contrast_count: int
    scenarios: tuple[V5SupportScenario, ...]
    qualification_pass: bool

    def as_dict(self) -> dict[str, object]:
        payload = asdict(self)
        payload["scenarios"] = [row.as_dict() for row in self.scenarios]
        return payload


def _primitive(
    rng: np.random.Generator,
    shape: tuple[int, ...],
    distribution: str,
) -> np.ndarray:
    if distribution in {"normal", "heteroskedastic_interaction"}:
        return rng.standard_normal(shape)
    if distribution == "rademacher":
        return rng.choice(np.asarray([-1.0, 1.0]), size=shape)
    if distribution == "contaminated_normal":
        base = rng.standard_normal(shape)
        scale = np.where(rng.random(shape) < 0.05, 6.0, 1.0)
        return base * scale / math.sqrt(0.95 + 0.05 * 36.0)
    if distribution == "skewed_lognormal":
        sigma = 1.0
        raw = np.exp(sigma * rng.standard_normal(shape))
        mean = math.exp(0.5 * sigma * sigma)
        variance = (math.exp(sigma * sigma) - 1.0) * math.exp(sigma * sigma)
        return (raw - mean) / math.sqrt(variance)
    raise ValueError(f"unknown support distribution: {distribution}")


def _support_world(
    rng: np.random.Generator,
    *,
    distribution: str,
    refit_count: int,
    blocks_per_group: int,
    group_count: int,
    contrast_count: int,
    training_sd: float,
    validation_sd: float,
    interaction_sd: float,
    training_cross_cell_correlation: float = 0.35,
    contrast_correlation: float = 0.5,
) -> np.ndarray:
    shared_training = _primitive(
        rng, (refit_count, 1, 1), distribution
    )
    cell_training = _primitive(
        rng, (refit_count, group_count, contrast_count), distribution
    )
    training = training_sd * (
        math.sqrt(training_cross_cell_correlation) * shared_training
        + math.sqrt(1.0 - training_cross_cell_correlation) * cell_training
    )

    shared_validation = _primitive(
        rng, (group_count, blocks_per_group, 1), distribution
    )
    cell_validation = _primitive(
        rng, (group_count, blocks_per_group, contrast_count), distribution
    )
    validation = validation_sd * (
        math.sqrt(contrast_correlation) * shared_validation
        + math.sqrt(1.0 - contrast_correlation) * cell_validation
    )

    # Heteroskedastic interaction uses normal primitives but independent
    # lognormal row/column scale factors with unit second moment.
    shared_interaction = _primitive(
        rng, (refit_count, group_count, blocks_per_group, 1), distribution
    )
    cell_interaction = _primitive(
        rng, (refit_count, group_count, blocks_per_group, contrast_count), distribution
    )
    interaction = (
        math.sqrt(contrast_correlation) * shared_interaction
        + math.sqrt(1.0 - contrast_correlation) * cell_interaction
    )
    if distribution == "heteroskedastic_interaction":
        sigma = 0.8
        refit_scale = np.exp(
            sigma * rng.standard_normal((refit_count, 1, 1, 1))
            - sigma * sigma
        )
        block_scale = np.exp(
            sigma * rng.standard_normal((1, group_count, blocks_per_group, 1))
            - sigma * sigma
        )
        interaction = interaction * refit_scale * block_scale
    interaction = interaction_sd * interaction

    return training[:, :, None, :] + validation[None, :, :, :] + interaction


def _flatten(
    world: np.ndarray,
    block_weights: tuple[float, ...] | None,
) -> tuple[np.ndarray, tuple[str, ...], tuple[str, ...], np.ndarray]:
    r, g, b, c = world.shape
    gain = np.empty((r, g * b, c))
    groups: list[str] = []
    blocks: list[str] = []
    weight: list[float] = []
    row = 0
    local_weight = (
        np.ones(b, dtype=float)
        if block_weights is None
        else np.asarray(block_weights, dtype=float)
    )
    if local_weight.shape != (b,) or np.any(local_weight <= 0):
        raise ValueError("support block weights must be positive and aligned")
    for gi in range(g):
        for bi in range(b):
            gain[:, row, :] = world[:, gi, bi, :]
            groups.append(f"g{gi:02d}")
            blocks.append(f"g{gi:02d}-b{bi:03d}")
            weight.append(float(local_weight[bi]))
            row += 1
    return gain, tuple(groups), tuple(blocks), np.asarray(weight)


def run_training_process_cv3two_v5_support_envelope(
    *,
    seed: int = 20261015,
    simulations_per_scenario: int = 1000,
    group_count: int = 6,
    contrast_count: int = 2,
) -> V5SupportEnvelope:
    if simulations_per_scenario < 100:
        raise ValueError("simulations_per_scenario must be >= 100")
    if group_count != 6:
        raise ValueError("support envelope is frozen to group_count == 6")
    if contrast_count != 2:
        raise ValueError("support envelope is frozen to contrast_count == 2")

    alpha = 0.05
    maximum_rate = float(
        alpha + 2.0 * math.sqrt(alpha * (1.0 - alpha) / simulations_per_scenario)
    )
    rng = np.random.default_rng(seed)
    results: list[V5SupportScenario] = []

    for (
        scenario_id,
        distribution,
        refit_count,
        blocks_per_group,
        training_sd,
        validation_sd,
        interaction_sd,
        block_weights,
    ) in SCENARIOS:
        component_counts = np.zeros(group_count * contrast_count, dtype=int)
        any_count = 0
        terminal_count = 0
        for _ in range(simulations_per_scenario):
            world = _support_world(
                rng,
                distribution=distribution,
                refit_count=refit_count,
                blocks_per_group=blocks_per_group,
                group_count=group_count,
                contrast_count=contrast_count,
                training_sd=training_sd,
                validation_sd=validation_sd,
                interaction_sd=interaction_sd,
            )
            gain, groups, blocks, weights = _flatten(world, block_weights)
            audit = certify_training_process_positive_cv3two_iut_v5(
                gain,
                groups,
                blocks=blocks,
                refit_ids=tuple(f"r{i:03d}" for i in range(refit_count)),
                training_process_id="known-support-v5",
                training_process_manifest_sha256=PROCESS_SHA,
                contrast_names=("pooled->coarse", "coarse->fine"),
                sample_weight=weights,
                component_one_sided_alpha=0.05,
                minimum_refits=8,
                minimum_blocks_per_group=8,
            )
            positive = np.asarray(
                [
                    cell.status == "robust_positive"
                    for contrast in audit.contrasts
                    for cell in contrast.groups
                ],
                dtype=bool,
            )
            component_counts += positive.astype(int)
            any_count += int(np.any(positive))
            terminal_count += int(np.all(positive))
        rates = component_counts.astype(float) / simulations_per_scenario
        results.append(
            V5SupportScenario(
                scenario_id=scenario_id,
                distribution=distribution,
                refit_count=refit_count,
                blocks_per_group=blocks_per_group,
                simulations=simulations_per_scenario,
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

    return V5SupportEnvelope(
        generator_version=GENERATOR_VERSION,
        seed=seed,
        simulations_per_scenario=simulations_per_scenario,
        group_count=group_count,
        contrast_count=contrast_count,
        scenarios=tuple(results),
        qualification_pass=all(row.acceptance_pass for row in results),
    )
