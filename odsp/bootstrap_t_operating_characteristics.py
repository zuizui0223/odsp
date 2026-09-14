"""Known-null operating characteristics for ODSP simultaneous intervals.

This module compares the frozen version-1 fixed-scale standardized max-deviation
interval with the prospective version-2 genuine block bootstrap-t interval under
known global-null simulations.  It is a method benchmark, not an empirical
endpoint and not evidence about any biological dataset.

The benchmark intentionally calls the public ODSP audit functions so it tests the
actual shipped inference surfaces rather than a reimplementation of their math.
"""
from __future__ import annotations

from dataclasses import asdict, dataclass
import math
from typing import Literal, Sequence

import numpy as np

from .simultaneous_group_certification import audit_simultaneous_group_certification
from .simultaneous_group_certification_v2 import (
    audit_simultaneous_group_certification_v2,
)


Distribution = Literal["normal", "student_t3"]


@dataclass(frozen=True)
class NullCalibrationScenario:
    scenario_id: str
    distribution: str
    group_count: int
    blocks_per_group: int
    simulations: int
    bootstrap_draws: int
    nominal_familywise_confidence_level: float
    v1_two_sided_familywise_noncoverage_rate: float
    v2_two_sided_familywise_noncoverage_rate: float
    v1_any_false_positive_cell_rate: float
    v2_any_false_positive_cell_rate: float
    v1_any_false_negative_cell_rate: float
    v2_any_false_negative_cell_rate: float
    v1_terminal_false_generalizing_rate: float
    v2_terminal_false_generalizing_rate: float
    v1_infinite_critical_rate: float
    v2_infinite_critical_rate: float
    v2_monte_carlo_standard_error: float

    def as_dict(self) -> dict[str, object]:
        return asdict(self)


@dataclass(frozen=True)
class BootstrapTOperatingCharacteristics:
    seed: int
    scenarios: tuple[NullCalibrationScenario, ...]
    benchmark_type: str
    empirical_endpoint: bool
    frozen_endpoint_reclassified: bool

    def as_dict(self) -> dict[str, object]:
        return {
            "seed": self.seed,
            "scenarios": [scenario.as_dict() for scenario in self.scenarios],
            "benchmark_type": self.benchmark_type,
            "empirical_endpoint": self.empirical_endpoint,
            "frozen_endpoint_reclassified": self.frozen_endpoint_reclassified,
        }


def _draw_null(
    rng: np.random.Generator,
    *,
    group_count: int,
    blocks_per_group: int,
    distribution: Distribution,
) -> np.ndarray:
    if distribution == "normal":
        return rng.normal(size=(group_count, blocks_per_group))
    if distribution == "student_t3":
        # t_3 has variance 3.  Rescale to unit variance so tail shape, not scale,
        # distinguishes this scenario from the Gaussian null.
        return rng.standard_t(df=3, size=(group_count, blocks_per_group)) / math.sqrt(3.0)
    raise ValueError(f"unknown null distribution: {distribution!r}")


def _interval_failure(bounds: Sequence[tuple[float | None, float | None]]) -> tuple[bool, bool, bool]:
    any_noncoverage = False
    any_positive = False
    any_negative = False
    for lower, upper in bounds:
        if lower is None or upper is None:
            raise ValueError("calibration scenario unexpectedly produced an unavailable interval")
        if lower > 0.0:
            any_noncoverage = True
            any_positive = True
        if upper < 0.0:
            any_noncoverage = True
            any_negative = True
    return any_noncoverage, any_positive, any_negative


def run_null_calibration_scenario(
    *,
    scenario_id: str,
    distribution: Distribution,
    group_count: int,
    blocks_per_group: int,
    simulations: int,
    bootstrap_draws: int,
    seed: int,
    familywise_confidence_level: float = 0.95,
) -> NullCalibrationScenario:
    """Estimate simultaneous-interval operating characteristics under global null."""

    if group_count < 2:
        raise ValueError("group_count must be >= 2")
    if blocks_per_group < 8:
        raise ValueError("blocks_per_group must be >= 8")
    if simulations < 50:
        raise ValueError("simulations must be >= 50")
    if bootstrap_draws < 500:
        raise ValueError("bootstrap_draws must be >= 500")
    if not 0.0 < familywise_confidence_level < 1.0:
        raise ValueError("familywise_confidence_level must lie strictly between zero and one")

    rng = np.random.default_rng(seed)
    groups = [
        f"g{group_index:02d}"
        for group_index in range(group_count)
        for _ in range(blocks_per_group)
    ]
    blocks = [
        f"g{group_index:02d}-b{block_index:03d}"
        for group_index in range(group_count)
        for block_index in range(blocks_per_group)
    ]

    v1_noncoverage = 0
    v2_noncoverage = 0
    v1_positive = 0
    v2_positive = 0
    v1_negative = 0
    v2_negative = 0
    v1_terminal_positive = 0
    v2_terminal_positive = 0
    v1_infinite = 0
    v2_infinite = 0

    for simulation in range(simulations):
        matrix = _draw_null(
            rng,
            group_count=group_count,
            blocks_per_group=blocks_per_group,
            distribution=distribution,
        )
        row_gain = matrix.reshape(-1).tolist()
        local_seed = seed + 100_003 + simulation * 97
        legacy = audit_simultaneous_group_certification(
            row_gain,
            groups,
            blocks=blocks,
            familywise_confidence_level=familywise_confidence_level,
            bootstrap_draws=bootstrap_draws,
            seed=local_seed,
            minimum_blocks_per_group=8,
        )
        prospective = audit_simultaneous_group_certification_v2(
            row_gain,
            groups,
            blocks=blocks,
            familywise_confidence_level=familywise_confidence_level,
            bootstrap_draws=bootstrap_draws,
            seed=local_seed,
            minimum_blocks_per_group=8,
        )

        old_bounds = [
            (row.max_t_lower_bound, row.max_t_upper_bound)
            for row in legacy.groups
        ]
        new_bounds = [
            (row.bootstrap_t_lower_bound, row.bootstrap_t_upper_bound)
            for row in prospective.groups
        ]
        old_any, old_pos, old_neg = _interval_failure(old_bounds)
        new_any, new_pos, new_neg = _interval_failure(new_bounds)
        v1_noncoverage += int(old_any)
        v2_noncoverage += int(new_any)
        v1_positive += int(old_pos)
        v2_positive += int(new_pos)
        v1_negative += int(old_neg)
        v2_negative += int(new_neg)
        v1_terminal_positive += int(legacy.simultaneous_admissible)
        v2_terminal_positive += int(prospective.simultaneous_admissible)
        v1_infinite += int(
            legacy.max_t_critical_value is not None
            and math.isinf(float(legacy.max_t_critical_value))
        )
        v2_infinite += int(
            prospective.bootstrap_t_critical_value is not None
            and math.isinf(float(prospective.bootstrap_t_critical_value))
        )

    denom = float(simulations)
    v2_rate = v2_noncoverage / denom
    return NullCalibrationScenario(
        scenario_id=scenario_id,
        distribution=distribution,
        group_count=group_count,
        blocks_per_group=blocks_per_group,
        simulations=simulations,
        bootstrap_draws=bootstrap_draws,
        nominal_familywise_confidence_level=float(familywise_confidence_level),
        v1_two_sided_familywise_noncoverage_rate=v1_noncoverage / denom,
        v2_two_sided_familywise_noncoverage_rate=v2_rate,
        v1_any_false_positive_cell_rate=v1_positive / denom,
        v2_any_false_positive_cell_rate=v2_positive / denom,
        v1_any_false_negative_cell_rate=v1_negative / denom,
        v2_any_false_negative_cell_rate=v2_negative / denom,
        v1_terminal_false_generalizing_rate=v1_terminal_positive / denom,
        v2_terminal_false_generalizing_rate=v2_terminal_positive / denom,
        v1_infinite_critical_rate=v1_infinite / denom,
        v2_infinite_critical_rate=v2_infinite / denom,
        v2_monte_carlo_standard_error=float(
            math.sqrt(max(v2_rate * (1.0 - v2_rate), 0.0) / denom)
        ),
    )


def run_bootstrap_t_operating_characteristics(
    *,
    seed: int = 20260914,
    simulations: int = 200,
    bootstrap_draws: int = 500,
) -> BootstrapTOperatingCharacteristics:
    """Run a compact deterministic calibration panel for CI and method audit."""

    specifications = (
        ("normal-b8", "normal", 8),
        ("normal-b20", "normal", 20),
        ("normal-b50", "normal", 50),
        ("t3-b20", "student_t3", 20),
    )
    scenarios = tuple(
        run_null_calibration_scenario(
            scenario_id=scenario_id,
            distribution=distribution,
            group_count=6,
            blocks_per_group=blocks,
            simulations=simulations,
            bootstrap_draws=bootstrap_draws,
            seed=seed + index * 1_000_003,
        )
        for index, (scenario_id, distribution, blocks) in enumerate(specifications)
    )
    return BootstrapTOperatingCharacteristics(
        seed=seed,
        scenarios=scenarios,
        benchmark_type="known_global_null_familywise_coverage",
        empirical_endpoint=False,
        frozen_endpoint_reclassified=False,
    )
