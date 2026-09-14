"""Known-null operating characteristics for independent-group multicontrast v2.

This benchmark targets the inference family introduced by
:func:`certify_independent_group_contrasts_v2`: multiple held-out groups are
independent sampling units at the group level, while multiple contrasts within a
group are correlated because they are evaluated on the same validation blocks.

Synthetic worlds are generated analytically, without matrix factorization, so a
frozen seed maps to the same Gaussian draws across BLAS/LAPACK implementations.
The benchmark is methodological evidence only, never biological evidence.
"""
from __future__ import annotations

from dataclasses import asdict, dataclass
import math

import numpy as np

from .multicontrast_bootstrap_t import certify_independent_group_contrasts_v2


GENERATOR_VERSION = "analytic_independent_group_equicorrelated_contrasts_v1"


@dataclass(frozen=True)
class MulticontrastCalibrationScenario:
    scenario_id: str
    distribution: str
    blocks_per_group: int
    contrast_count: int
    simulations: int
    v2_two_sided_familywise_noncoverage_rate: float
    v2_terminal_false_generalizing_rate: float
    v2_monte_carlo_standard_error: float
    maximum_accepted_rate: float
    v2_acceptance_pass: bool

    def as_dict(self) -> dict[str, object]:
        return asdict(self)


@dataclass(frozen=True)
class MulticontrastCalibrationResult:
    generator_version: str
    seed: int
    simulations_per_scenario: int
    bootstrap_draws_per_interval: int
    group_count: int
    contrast_correlation: float
    nominal_familywise_confidence_level: float
    scenarios: tuple[MulticontrastCalibrationScenario, ...]
    qualification_pass: bool

    def as_dict(self) -> dict[str, object]:
        payload = asdict(self)
        payload["scenarios"] = [row.as_dict() for row in self.scenarios]
        return payload


def _world(
    rng: np.random.Generator,
    *,
    blocks: int,
    group_count: int,
    contrast_count: int,
    contrast_rho: float,
    distribution: str,
) -> np.ndarray:
    """Return blocks x groups x contrasts with independent groups.

    Within a group/block, contrasts have equicorrelation ``contrast_rho``.
    Different groups use independent latent terms, matching the inference route's
    validation-group independence assumption.
    """

    rho = float(contrast_rho)
    shared = rng.standard_normal((blocks, group_count, 1))
    cell = rng.standard_normal((blocks, group_count, contrast_count))
    values = math.sqrt(rho) * shared + math.sqrt(1.0 - rho) * cell
    if distribution == "normal":
        return values
    if distribution == "student_t3":
        scale = np.sqrt(
            rng.chisquare(df=3, size=(blocks, group_count, 1)) / 3.0
        )
        return values / scale
    raise ValueError(f"unsupported distribution: {distribution}")


def _rows(values: np.ndarray) -> tuple[np.ndarray, tuple[str, ...], tuple[str, ...]]:
    block_count, group_count, contrast_count = values.shape
    gains = np.empty((group_count * block_count, contrast_count), dtype=float)
    groups: list[str] = []
    block_ids: list[str] = []
    row = 0
    for group_index in range(group_count):
        for block_index in range(block_count):
            gains[row, :] = values[block_index, group_index, :]
            groups.append(f"g{group_index:02d}")
            block_ids.append(f"g{group_index:02d}-b{block_index:03d}")
            row += 1
    return gains, tuple(groups), tuple(block_ids)


def _reject(result) -> bool:
    return any(
        cell.status != "uncertain"
        for contrast in result.contrasts
        for cell in contrast.groups
    )


def _false_generalizing(result) -> bool:
    return bool(result.contrasts) and all(
        contrast.category == "robust_generalizing"
        for contrast in result.contrasts
    )


def run_multicontrast_bootstrap_t_calibration(
    *,
    seed: int = 20260915,
    simulations_per_scenario: int = 1000,
    bootstrap_draws: int = 500,
    group_count: int = 6,
    contrast_correlation: float = 0.5,
    confidence_level: float = 0.95,
) -> MulticontrastCalibrationResult:
    """Run the predeclared independent-group global-null calibration panel."""

    if simulations_per_scenario < 100:
        raise ValueError("simulations_per_scenario must be >= 100")
    if bootstrap_draws < 500:
        raise ValueError("bootstrap_draws must be >= 500")
    if group_count < 2:
        raise ValueError("group_count must be >= 2")
    if not 0 <= contrast_correlation < 1:
        raise ValueError("contrast_correlation must lie in [0, 1)")
    if not 0 < confidence_level < 1:
        raise ValueError("confidence_level must lie strictly between zero and one")

    scenario_defs = (
        ("independent-c2-normal-b8", "normal", 8, 2),
        ("independent-c2-normal-b20", "normal", 20, 2),
        ("independent-c2-normal-b50", "normal", 50, 2),
        ("independent-c4-normal-b20", "normal", 20, 4),
        ("independent-c4-t3-b20", "student_t3", 20, 4),
    )
    alpha = 1.0 - confidence_level
    maximum_rate = float(
        alpha
        + 2.0
        * math.sqrt(alpha * (1.0 - alpha) / simulations_per_scenario)
    )
    rng = np.random.default_rng(seed)
    scenarios: list[MulticontrastCalibrationScenario] = []

    for scenario_index, (
        scenario_id,
        distribution,
        block_count,
        contrast_count,
    ) in enumerate(scenario_defs):
        rejects = 0
        false_generalizing = 0
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
            result = certify_independent_group_contrasts_v2(
                gains,
                groups,
                blocks=block_ids,
                contrast_names=[f"c{index}" for index in range(contrast_count)],
                familywise_confidence_level=confidence_level,
                bootstrap_draws=bootstrap_draws,
                seed=local_seed,
                minimum_blocks_per_group=8,
            )
            rejects += int(_reject(result))
            false_generalizing += int(_false_generalizing(result))

        rate = float(rejects / simulations_per_scenario)
        scenarios.append(
            MulticontrastCalibrationScenario(
                scenario_id=scenario_id,
                distribution=distribution,
                blocks_per_group=block_count,
                contrast_count=contrast_count,
                simulations=simulations_per_scenario,
                v2_two_sided_familywise_noncoverage_rate=rate,
                v2_terminal_false_generalizing_rate=float(
                    false_generalizing / simulations_per_scenario
                ),
                v2_monte_carlo_standard_error=float(
                    math.sqrt(max(rate * (1.0 - rate), 0.0) / simulations_per_scenario)
                ),
                maximum_accepted_rate=maximum_rate,
                v2_acceptance_pass=bool(rate <= maximum_rate),
            )
        )

    return MulticontrastCalibrationResult(
        generator_version=GENERATOR_VERSION,
        seed=seed,
        simulations_per_scenario=simulations_per_scenario,
        bootstrap_draws_per_interval=bootstrap_draws,
        group_count=group_count,
        contrast_correlation=float(contrast_correlation),
        nominal_familywise_confidence_level=float(confidence_level),
        scenarios=tuple(scenarios),
        qualification_pass=all(row.v2_acceptance_pass for row in scenarios),
    )
