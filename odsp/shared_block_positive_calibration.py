"""Known-global-null calibration for paired one-sided positive-transfer bootstrap-t."""
from __future__ import annotations

from dataclasses import asdict, dataclass
import math

import numpy as np

from .shared_block_bootstrap_t_calibration import _rows, _world
from .shared_block_positive_certification import certify_shared_block_positive_gains_v2


GENERATOR_VERSION = "analytic_separable_equicorrelation_common_factor_v1"


@dataclass(frozen=True)
class PairedPositiveCalibrationScenario:
    scenario_id: str
    distribution: str
    blocks_per_group: int
    simulations: int
    one_sided_familywise_false_positive_rate: float
    terminal_false_generalizing_rate: float
    monte_carlo_standard_error: float
    maximum_accepted_rate: float
    acceptance_pass: bool

    def as_dict(self) -> dict[str, object]:
        return asdict(self)


@dataclass(frozen=True)
class PairedPositiveCalibrationResult:
    generator_version: str
    seed: int
    simulations_per_scenario: int
    bootstrap_draws_per_interval: int
    group_count: int
    contrast_count: int
    group_correlation: float
    contrast_correlation: float
    familywise_lower_confidence_level: float
    scenarios: tuple[PairedPositiveCalibrationScenario, ...]
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


def _false_generalizing(result) -> bool:
    return bool(result.contrasts) and all(
        contrast.category == "robust_generalizing"
        for contrast in result.contrasts
    )


def run_paired_positive_null_calibration(
    *,
    seed: int = 20260915,
    simulations_per_scenario: int = 1000,
    bootstrap_draws: int = 500,
    group_count: int = 6,
    contrast_count: int = 2,
    group_correlation: float = 0.7,
    contrast_correlation: float = 0.5,
    confidence_level: float = 0.95,
) -> PairedPositiveCalibrationResult:
    """Run the predeclared paired shared-block one-sided global-null panel."""

    if simulations_per_scenario < 100:
        raise ValueError("simulations_per_scenario must be >= 100")
    if bootstrap_draws < 500:
        raise ValueError("bootstrap_draws must be >= 500")
    if group_count < 2 or contrast_count < 1:
        raise ValueError("group_count must be >= 2 and contrast_count >= 1")
    if not 0 <= group_correlation < 1 or not 0 <= contrast_correlation < 1:
        raise ValueError("correlations must lie in [0, 1)")
    if not 0 < confidence_level < 1:
        raise ValueError("confidence_level must lie strictly between zero and one")

    scenario_defs = (
        ("paired-one-sided-normal-b8", "normal", 8),
        ("paired-one-sided-normal-b20", "normal", 20),
        ("paired-one-sided-normal-b50", "normal", 50),
        ("paired-one-sided-t3-b20", "student_t3", 20),
    )
    alpha = 1.0 - confidence_level
    maximum_rate = float(
        alpha + 2.0 * math.sqrt(alpha * (1.0 - alpha) / simulations_per_scenario)
    )
    rng = np.random.default_rng(seed)
    rows: list[PairedPositiveCalibrationScenario] = []

    for scenario_index, (scenario_id, distribution, block_count) in enumerate(scenario_defs):
        false_positive = 0
        false_generalizing = 0
        for simulation_index in range(simulations_per_scenario):
            values = _world(
                rng,
                blocks=block_count,
                group_count=group_count,
                contrast_count=contrast_count,
                group_rho=group_correlation,
                contrast_rho=contrast_correlation,
                distribution=distribution,
            )
            gains, groups, blocks = _rows(values)
            local_seed = (
                seed
                + 1000003 * (scenario_index + 1)
                + 10007 * (simulation_index + 1)
            )
            result = certify_shared_block_positive_gains_v2(
                gains,
                groups,
                blocks,
                contrast_names=[f"c{index}" for index in range(contrast_count)],
                familywise_lower_confidence_level=confidence_level,
                bootstrap_draws=bootstrap_draws,
                seed=local_seed,
                minimum_shared_blocks=8,
            )
            false_positive += int(_any_false_positive(result))
            false_generalizing += int(_false_generalizing(result))

        rate = float(false_positive / simulations_per_scenario)
        rows.append(
            PairedPositiveCalibrationScenario(
                scenario_id=scenario_id,
                distribution=distribution,
                blocks_per_group=block_count,
                simulations=simulations_per_scenario,
                one_sided_familywise_false_positive_rate=rate,
                terminal_false_generalizing_rate=float(
                    false_generalizing / simulations_per_scenario
                ),
                monte_carlo_standard_error=float(
                    math.sqrt(max(rate * (1.0 - rate), 0.0) / simulations_per_scenario)
                ),
                maximum_accepted_rate=maximum_rate,
                acceptance_pass=bool(rate <= maximum_rate),
            )
        )

    scenario_rows = tuple(rows)
    return PairedPositiveCalibrationResult(
        generator_version=GENERATOR_VERSION,
        seed=seed,
        simulations_per_scenario=simulations_per_scenario,
        bootstrap_draws_per_interval=bootstrap_draws,
        group_count=group_count,
        contrast_count=contrast_count,
        group_correlation=float(group_correlation),
        contrast_correlation=float(contrast_correlation),
        familywise_lower_confidence_level=float(confidence_level),
        scenarios=scenario_rows,
        qualification_pass=all(row.acceptance_pass for row in scenario_rows),
    )
