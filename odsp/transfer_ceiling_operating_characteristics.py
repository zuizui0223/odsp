"""Mixed-truth operating characteristics for information-transfer ceilings.

Null familywise coverage answers whether a simultaneous interval overreaches
under a global null.  A transfer ceiling poses a different question: when an
ordered information filtration has a known mixture of positive, null or adverse
increments, does the non-skippable v2 rule stop at the correct level?

This benchmark simulates a three-level filtration

    pooled -> coarse -> fine

with six independent held-out groups.  The two adjacent row-wise gain increments
are correlated within each validation block and are scored jointly with the
prospective replicate-studentized bootstrap-t v2 engine.

The benchmark reports exact-ceiling recovery, overreach and underreach
separately.  It is methodological evidence only and never a biological endpoint.
"""
from __future__ import annotations

from dataclasses import asdict, dataclass
import math

import numpy as np

from .information_transfer import InformationLevelScore
from .information_transfer_v2 import certify_information_transfer_v2


GENERATOR_VERSION = "analytic_independent_group_two_step_mixed_truth_v1"
_LEVELS = ("pooled", "coarse", "fine")
_LEVEL_INDEX = {name: index for index, name in enumerate(_LEVELS)}


@dataclass(frozen=True)
class TransferCeilingScenario:
    scenario_id: str
    distribution: str
    blocks_per_group: int
    coarse_mean_gain: float
    fine_mean_gain: float
    truth_ceiling: str
    simulations: int
    exact_ceiling_recovery_rate: float
    overreach_rate: float
    underreach_rate: float
    full_ceiling_rate: float
    acceptance_rule: str
    acceptance_threshold: float | None
    acceptance_pass: bool

    def as_dict(self) -> dict[str, object]:
        return asdict(self)


@dataclass(frozen=True)
class TransferCeilingOperatingCharacteristics:
    generator_version: str
    seed: int
    simulations_per_scenario: int
    bootstrap_draws_per_interval: int
    group_count: int
    step_correlation: float
    noise_standard_deviation: float
    nominal_familywise_confidence_level: float
    scenarios: tuple[TransferCeilingScenario, ...]
    qualification_pass: bool

    def as_dict(self) -> dict[str, object]:
        payload = asdict(self)
        payload["scenarios"] = [row.as_dict() for row in self.scenarios]
        return payload


def _step_noise(
    rng: np.random.Generator,
    *,
    blocks: int,
    group_count: int,
    rho: float,
    sigma: float,
    distribution: str,
) -> np.ndarray:
    """Return blocks x groups x 2 correlated step noise without matrix factorization."""

    shared = rng.standard_normal((blocks, group_count, 1))
    cell = rng.standard_normal((blocks, group_count, 2))
    values = sigma * (math.sqrt(rho) * shared + math.sqrt(1.0 - rho) * cell)
    if distribution == "normal":
        return values
    if distribution == "student_t3":
        # One scale per validation block/group preserves correlation between the
        # adjacent transfer increments while producing heavy-tailed block noise.
        scale = np.sqrt(
            rng.chisquare(df=3, size=(blocks, group_count, 1)) / 3.0
        )
        return values / scale
    raise ValueError(f"unsupported distribution: {distribution}")


def _rows(
    increments: np.ndarray,
) -> tuple[tuple[InformationLevelScore, ...], tuple[str, ...], tuple[str, ...]]:
    block_count, group_count, step_count = increments.shape
    if step_count != 2:
        raise ValueError("increments must contain exactly two transfer steps")
    n = block_count * group_count
    coarse = np.empty(n, dtype=float)
    fine = np.empty(n, dtype=float)
    groups: list[str] = []
    block_ids: list[str] = []
    row = 0
    for group_index in range(group_count):
        for block_index in range(block_count):
            first = float(increments[block_index, group_index, 0])
            second = float(increments[block_index, group_index, 1])
            coarse[row] = first
            fine[row] = first + second
            groups.append(f"g{group_index:02d}")
            block_ids.append(f"g{group_index:02d}-b{block_index:03d}")
            row += 1
    levels = (
        InformationLevelScore("pooled", (), np.zeros(n, dtype=float)),
        InformationLevelScore("coarse", ("coarse_information",), coarse),
        InformationLevelScore(
            "fine",
            ("coarse_information", "fine_information"),
            fine,
        ),
    )
    return levels, tuple(groups), tuple(block_ids)


def _truth_ceiling(coarse_mean: float, fine_mean: float) -> str:
    if coarse_mean <= 0.0:
        return "pooled"
    if fine_mean <= 0.0:
        return "coarse"
    return "fine"


def _acceptance(
    scenario_id: str,
    *,
    exact_rate: float,
    overreach_rate: float,
    simulations: int,
) -> tuple[str, float | None, bool]:
    """Apply only prospectively declared scenario-specific qualification rules."""

    if scenario_id == "strong-full-normal-b20":
        threshold = 0.90
        return "exact_ceiling_recovery_rate >= 0.90", threshold, bool(exact_rate >= threshold)
    if scenario_id == "strong-full-normal-b50":
        threshold = 0.98
        return "exact_ceiling_recovery_rate >= 0.98", threshold, bool(exact_rate >= threshold)
    if scenario_id in {
        "coarse-null-normal-b20",
        "coarse-adverse-normal-b20",
        "coarse-null-t3-b20",
    }:
        alpha = 0.05
        threshold = float(
            alpha + 2.0 * math.sqrt(alpha * (1.0 - alpha) / simulations)
        )
        return (
            "overreach_rate <= alpha + 2*sqrt(alpha*(1-alpha)/simulation_count)",
            threshold,
            bool(overreach_rate <= threshold),
        )
    # Weak-positive power is intentionally descriptive: it maps the detection
    # frontier rather than serving as a post-hoc qualification requirement.
    return "descriptive_power_scenario_no_acceptance_threshold", None, True


def run_transfer_ceiling_operating_characteristics(
    *,
    seed: int = 20260915,
    simulations_per_scenario: int = 1000,
    bootstrap_draws: int = 500,
    group_count: int = 6,
    step_correlation: float = 0.4,
    noise_standard_deviation: float = 0.2,
    confidence_level: float = 0.95,
) -> TransferCeilingOperatingCharacteristics:
    """Run the predeclared mixed-truth transfer-ceiling simulation panel."""

    if simulations_per_scenario < 100:
        raise ValueError("simulations_per_scenario must be >= 100")
    if bootstrap_draws < 500:
        raise ValueError("bootstrap_draws must be >= 500")
    if group_count < 2:
        raise ValueError("group_count must be >= 2")
    if not 0.0 <= step_correlation < 1.0:
        raise ValueError("step_correlation must lie in [0, 1)")
    if not math.isfinite(noise_standard_deviation) or noise_standard_deviation <= 0:
        raise ValueError("noise_standard_deviation must be finite and positive")
    if not 0.0 < confidence_level < 1.0:
        raise ValueError("confidence_level must lie strictly between zero and one")

    scenario_defs = (
        # Strong effects test whether conservatism makes the method practically
        # unusable when both information increments truly transfer.
        ("strong-full-normal-b20", "normal", 20, 0.45, 0.30),
        ("strong-full-normal-b50", "normal", 50, 0.45, 0.30),
        # Weak fine transfer maps power but is not used as a qualification gate.
        ("weak-full-normal-b20", "normal", 20, 0.45, 0.15),
        # Null/adverse fine increments test the non-skippable hard stop.
        ("coarse-null-normal-b20", "normal", 20, 0.45, 0.0),
        ("coarse-adverse-normal-b20", "normal", 20, 0.45, -0.10),
        ("coarse-null-t3-b20", "student_t3", 20, 0.45, 0.0),
    )
    rng = np.random.default_rng(seed)
    rows: list[TransferCeilingScenario] = []

    for scenario_index, (
        scenario_id,
        distribution,
        block_count,
        coarse_mean,
        fine_mean,
    ) in enumerate(scenario_defs):
        truth = _truth_ceiling(coarse_mean, fine_mean)
        truth_index = _LEVEL_INDEX[truth]
        exact = 0
        over = 0
        under = 0
        full = 0
        for simulation_index in range(simulations_per_scenario):
            noise = _step_noise(
                rng,
                blocks=block_count,
                group_count=group_count,
                rho=step_correlation,
                sigma=noise_standard_deviation,
                distribution=distribution,
            )
            increments = noise + np.asarray([coarse_mean, fine_mean])[None, None, :]
            levels, groups, block_ids = _rows(increments)
            local_seed = (
                seed
                + 1000003 * (scenario_index + 1)
                + 10007 * (simulation_index + 1)
            )
            result = certify_information_transfer_v2(
                levels,
                groups,
                blocks=block_ids,
                familywise_confidence_level=confidence_level,
                bootstrap_draws=bootstrap_draws,
                seed=local_seed,
                minimum_blocks_per_group=8,
            )
            observed = result.certified_transfer_ceiling
            observed_index = _LEVEL_INDEX[observed]
            exact += int(observed_index == truth_index)
            over += int(observed_index > truth_index)
            under += int(observed_index < truth_index)
            full += int(observed == "fine")

        exact_rate = float(exact / simulations_per_scenario)
        over_rate = float(over / simulations_per_scenario)
        under_rate = float(under / simulations_per_scenario)
        rule, threshold, passed = _acceptance(
            scenario_id,
            exact_rate=exact_rate,
            overreach_rate=over_rate,
            simulations=simulations_per_scenario,
        )
        rows.append(
            TransferCeilingScenario(
                scenario_id=scenario_id,
                distribution=distribution,
                blocks_per_group=block_count,
                coarse_mean_gain=coarse_mean,
                fine_mean_gain=fine_mean,
                truth_ceiling=truth,
                simulations=simulations_per_scenario,
                exact_ceiling_recovery_rate=exact_rate,
                overreach_rate=over_rate,
                underreach_rate=under_rate,
                full_ceiling_rate=float(full / simulations_per_scenario),
                acceptance_rule=rule,
                acceptance_threshold=threshold,
                acceptance_pass=passed,
            )
        )

    return TransferCeilingOperatingCharacteristics(
        generator_version=GENERATOR_VERSION,
        seed=seed,
        simulations_per_scenario=simulations_per_scenario,
        bootstrap_draws_per_interval=bootstrap_draws,
        group_count=group_count,
        step_correlation=float(step_correlation),
        noise_standard_deviation=float(noise_standard_deviation),
        nominal_familywise_confidence_level=float(confidence_level),
        scenarios=tuple(rows),
        qualification_pass=all(row.acceptance_pass for row in rows),
    )
