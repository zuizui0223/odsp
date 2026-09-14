"""Known-null calibration benchmark for paired shared-block bootstrap-t v2.

The simulated validation design deliberately induces strong cross-group and
cross-contrast correlation through shared blocks. The exact same synthetic
world is evaluated by historical paired v1 fixed-scale standardization and by
prospective paired v2 replicate-specific bootstrap-t.

Synthetic worlds use an analytic common-factor construction for the separable
Kronecker equicorrelation target. This avoids numerical eigendecomposition or
Cholesky choices in ``numpy.random.multivariate_normal`` so a frozen seed maps
to the same simulated worlds across BLAS/LAPACK implementations.

This is a methodological operating-characteristics benchmark, not biological
evidence.
"""
from __future__ import annotations

from dataclasses import asdict, dataclass
import math

import numpy as np

from .shared_block_certification import certify_shared_block_gains
from .shared_block_certification_v2 import certify_shared_block_gains_v2


GENERATOR_VERSION = "analytic_separable_equicorrelation_common_factor_v1"


@dataclass(frozen=True)
class SharedBlockCalibrationScenario:
    scenario_id: str
    distribution: str
    blocks_per_group: int
    simulations: int
    v1_two_sided_familywise_noncoverage_rate: float
    v2_two_sided_familywise_noncoverage_rate: float
    v1_terminal_false_generalizing_rate: float
    v2_terminal_false_generalizing_rate: float
    v2_monte_carlo_standard_error: float
    maximum_accepted_rate: float
    v2_acceptance_pass: bool

    def as_dict(self) -> dict[str, object]:
        return asdict(self)


@dataclass(frozen=True)
class SharedBlockCalibrationResult:
    generator_version: str
    seed: int
    simulations_per_scenario: int
    bootstrap_draws_per_interval: int
    group_count: int
    contrast_count: int
    group_correlation: float
    contrast_correlation: float
    nominal_familywise_confidence_level: float
    scenarios: tuple[SharedBlockCalibrationScenario, ...]
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
    group_rho: float,
    contrast_rho: float,
    distribution: str,
) -> np.ndarray:
    """Generate one separably correlated block world without matrix factorization.

    For group indices g,g' and contrast indices c,c', the construction gives

        Cov(X_gc, X_g'c')
          = (rho_g + (1-rho_g) I[g=g'])
            * (rho_c + (1-rho_c) I[c=c']).

    This is exactly the Kronecker product of the two equicorrelation matrices.
    Only ``Generator.standard_normal`` and scalar square roots are used, so the
    seeded world does not depend on a linear-algebra factorization convention.
    """

    rg = float(group_rho)
    rc = float(contrast_rho)
    global_term = rng.standard_normal((blocks, 1, 1))
    contrast_term = rng.standard_normal((blocks, 1, contrast_count))
    group_term = rng.standard_normal((blocks, group_count, 1))
    cell_term = rng.standard_normal((blocks, group_count, contrast_count))

    values = (
        math.sqrt(rg * rc) * global_term
        + math.sqrt(rg * (1.0 - rc)) * contrast_term
        + math.sqrt((1.0 - rg) * rc) * group_term
        + math.sqrt((1.0 - rg) * (1.0 - rc)) * cell_term
    )
    if distribution == "normal":
        return values
    if distribution == "student_t3":
        scale = np.sqrt(rng.chisquare(df=3, size=blocks) / 3.0)
        return values / scale[:, None, None]
    raise ValueError(f"unsupported distribution: {distribution}")


def _rows(values: np.ndarray) -> tuple[np.ndarray, tuple[str, ...], tuple[str, ...]]:
    block_count, group_count, contrast_count = values.shape
    row_gain = np.empty((group_count * block_count, contrast_count), dtype=float)
    groups: list[str] = []
    blocks: list[str] = []
    row = 0
    for group_index in range(group_count):
        for block_index in range(block_count):
            row_gain[row, :] = values[block_index, group_index, :]
            groups.append(f"g{group_index:02d}")
            blocks.append(f"b{block_index:03d}")
            row += 1
    return row_gain, tuple(groups), tuple(blocks)


def _reject_v1(result) -> bool:
    return any(
        cell.status != "uncertain"
        for contrast in result.contrasts
        for cell in contrast.groups
    )


def _reject_v2(result) -> bool:
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


def run_shared_block_bootstrap_t_calibration(
    *,
    seed: int = 20260914,
    simulations_per_scenario: int = 1000,
    bootstrap_draws: int = 500,
    group_count: int = 6,
    contrast_count: int = 2,
    group_correlation: float = 0.7,
    contrast_correlation: float = 0.5,
    confidence_level: float = 0.95,
) -> SharedBlockCalibrationResult:
    """Run predeclared paired-block global-null calibration scenarios."""

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
        ("paired-normal-b8", "normal", 8),
        ("paired-normal-b20", "normal", 20),
        ("paired-normal-b50", "normal", 50),
        ("paired-t3-b20", "student_t3", 20),
    )
    alpha = 1.0 - confidence_level
    maximum_rate = float(
        alpha
        + 2.0
        * math.sqrt(alpha * (1.0 - alpha) / simulations_per_scenario)
    )
    rng = np.random.default_rng(seed)
    scenario_rows: list[SharedBlockCalibrationScenario] = []

    for scenario_index, (scenario_id, distribution, block_count) in enumerate(
        scenario_defs
    ):
        v1_reject = 0
        v2_reject = 0
        v1_false_generalizing = 0
        v2_false_generalizing = 0
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
            v1 = certify_shared_block_gains(
                gains,
                groups,
                blocks,
                contrast_names=[f"c{index}" for index in range(contrast_count)],
                familywise_confidence_level=confidence_level,
                bootstrap_draws=bootstrap_draws,
                seed=local_seed,
                minimum_shared_blocks=8,
            )
            v2 = certify_shared_block_gains_v2(
                gains,
                groups,
                blocks,
                contrast_names=[f"c{index}" for index in range(contrast_count)],
                familywise_confidence_level=confidence_level,
                bootstrap_draws=bootstrap_draws,
                seed=local_seed,
                minimum_shared_blocks=8,
            )
            v1_reject += int(_reject_v1(v1))
            v2_reject += int(_reject_v2(v2))
            v1_false_generalizing += int(_false_generalizing(v1))
            v2_false_generalizing += int(_false_generalizing(v2))

        v1_rate = float(v1_reject / simulations_per_scenario)
        v2_rate = float(v2_reject / simulations_per_scenario)
        scenario_rows.append(
            SharedBlockCalibrationScenario(
                scenario_id=scenario_id,
                distribution=distribution,
                blocks_per_group=block_count,
                simulations=simulations_per_scenario,
                v1_two_sided_familywise_noncoverage_rate=v1_rate,
                v2_two_sided_familywise_noncoverage_rate=v2_rate,
                v1_terminal_false_generalizing_rate=float(
                    v1_false_generalizing / simulations_per_scenario
                ),
                v2_terminal_false_generalizing_rate=float(
                    v2_false_generalizing / simulations_per_scenario
                ),
                v2_monte_carlo_standard_error=float(
                    math.sqrt(max(v2_rate * (1.0 - v2_rate), 0.0) / simulations_per_scenario)
                ),
                maximum_accepted_rate=maximum_rate,
                v2_acceptance_pass=bool(v2_rate <= maximum_rate),
            )
        )

    return SharedBlockCalibrationResult(
        generator_version=GENERATOR_VERSION,
        seed=seed,
        simulations_per_scenario=simulations_per_scenario,
        bootstrap_draws_per_interval=bootstrap_draws,
        group_count=group_count,
        contrast_count=contrast_count,
        group_correlation=float(group_correlation),
        contrast_correlation=float(contrast_correlation),
        nominal_familywise_confidence_level=float(confidence_level),
        scenarios=tuple(scenario_rows),
        qualification_pass=all(row.v2_acceptance_pass for row in scenario_rows),
    )
