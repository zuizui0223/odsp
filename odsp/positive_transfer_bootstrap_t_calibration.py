"""Known-null calibration for one-sided positive-transfer bootstrap-t.

The benchmark reuses the deterministic independent-group correlated-contrast
world generator from the two-sided multicontrast qualification panel.  Under the
global null every true gain is zero.  Familywise error is counted whenever at
least one one-sided simultaneous lower bound is strictly above zero.

This must be qualified before any claimed power advantage is used to justify the
directional procedure.
"""
from __future__ import annotations

from dataclasses import asdict, dataclass
import math

import numpy as np

from .multicontrast_bootstrap_t_calibration import _rows, _world
from .positive_transfer_bootstrap_t import (
    certify_independent_group_positive_transfer_v2,
)


GENERATOR_VERSION = "analytic_independent_group_equicorrelated_contrasts_one_sided_v1"


@dataclass(frozen=True)
class PositiveTransferNullScenario:
    scenario_id: str
    distribution: str
    blocks_per_group: int
    contrast_count: int
    simulations: int
    one_sided_familywise_false_positive_rate: float
    terminal_false_generalizing_rate: float
    monte_carlo_standard_error: float
    maximum_accepted_rate: float
    acceptance_pass: bool

    def as_dict(self) -> dict[str, object]:
        return asdict(self)


@dataclass(frozen=True)
class PositiveTransferNullCalibration:
    generator_version: str
    seed: int
    simulations_per_scenario: int
    bootstrap_draws_per_interval: int
    group_count: int
    contrast_correlation: float
    familywise_lower_confidence_level: float
    scenarios: tuple[PositiveTransferNullScenario, ...]
    qualification_pass: bool

    def as_dict(self) -> dict[str, object]:
        payload = asdict(self)
        payload["scenarios"] = [row.as_dict() for row in self.scenarios]
        return payload


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


def run_positive_transfer_null_calibration(
    *,
    seed: int = 20260915,
    simulations_per_scenario: int = 1000,
    bootstrap_draws: int = 500,
    group_count: int = 6,
    contrast_correlation: float = 0.5,
    confidence_level: float = 0.95,
) -> PositiveTransferNullCalibration:
    """Run the predeclared one-sided global-null qualification panel."""

    if simulations_per_scenario < 100:
        raise ValueError("simulations_per_scenario must be >= 100")
    if bootstrap_draws < 500:
        raise ValueError("bootstrap_draws must be >= 500")
    if group_count < 2:
        raise ValueError("group_count must be >= 2")
    if not 0.0 <= contrast_correlation < 1.0:
        raise ValueError("contrast_correlation must lie in [0, 1)")
    if not 0.0 < confidence_level < 1.0:
        raise ValueError("confidence_level must lie strictly between zero and one")

    scenario_defs = (
        ("one-sided-c2-normal-b8", "normal", 8, 2),
        ("one-sided-c2-normal-b20", "normal", 20, 2),
        ("one-sided-c2-normal-b50", "normal", 50, 2),
        ("one-sided-c4-normal-b20", "normal", 20, 4),
        ("one-sided-c4-t3-b20", "student_t3", 20, 4),
    )
    alpha = 1.0 - confidence_level
    maximum_rate = float(
        alpha
        + 2.0 * math.sqrt(alpha * (1.0 - alpha) / simulations_per_scenario)
    )
    rng = np.random.default_rng(seed)
    rows_out: list[PositiveTransferNullScenario] = []

    for scenario_index, (
        scenario_id,
        distribution,
        block_count,
        contrast_count,
    ) in enumerate(scenario_defs):
        false_positive = 0
        terminal_false = 0
        for simulation_index in range(simulations_per_scenario):
            values = _world(
                rng,
                blocks=block_count,
                group_count=group_count,
                contrast_count=contrast_count,
                contrast_rho=contrast_correlation,
                distribution=distribution,
            )
            gains, groups, block_ids = _rows(values)
            local_seed = (
                seed
                + 1000003 * (scenario_index + 1)
                + 10007 * (simulation_index + 1)
            )
            result = certify_independent_group_positive_transfer_v2(
                gains,
                groups,
                blocks=block_ids,
                contrast_names=[f"c{index}" for index in range(contrast_count)],
                familywise_lower_confidence_level=confidence_level,
                bootstrap_draws=bootstrap_draws,
                seed=local_seed,
                minimum_blocks_per_group=8,
            )
            false_positive += int(_any_false_positive(result))
            terminal_false += int(_terminal_false_generalizing(result))

        rate = float(false_positive / simulations_per_scenario)
        rows_out.append(
            PositiveTransferNullScenario(
                scenario_id=scenario_id,
                distribution=distribution,
                blocks_per_group=block_count,
                contrast_count=contrast_count,
                simulations=simulations_per_scenario,
                one_sided_familywise_false_positive_rate=rate,
                terminal_false_generalizing_rate=float(
                    terminal_false / simulations_per_scenario
                ),
                monte_carlo_standard_error=float(
                    math.sqrt(max(rate * (1.0 - rate), 0.0) / simulations_per_scenario)
                ),
                maximum_accepted_rate=maximum_rate,
                acceptance_pass=bool(rate <= maximum_rate),
            )
        )

    return PositiveTransferNullCalibration(
        generator_version=GENERATOR_VERSION,
        seed=seed,
        simulations_per_scenario=simulations_per_scenario,
        bootstrap_draws_per_interval=bootstrap_draws,
        group_count=group_count,
        contrast_correlation=float(contrast_correlation),
        familywise_lower_confidence_level=float(confidence_level),
        scenarios=tuple(rows_out),
        qualification_pass=all(row.acceptance_pass for row in rows_out),
    )
