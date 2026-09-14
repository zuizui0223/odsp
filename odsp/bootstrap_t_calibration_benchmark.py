"""Known-null operating-characteristic benchmark for simultaneous bootstrap-t.

This benchmark is methodological, not an empirical endpoint.  It simulates
exchangeable validation blocks under an exact zero-gain null and compares the
historical fixed-SE standardized max-deviation interval (v1) with the prospective
replicate-studentized cluster bootstrap-t interval (v2).

The benchmark is deliberately modest enough for CI.  Its purpose is not to
estimate a publication-grade rejection probability to three decimals; it is to
catch gross anti-conservatism and regressions in the studentization logic.
"""
from __future__ import annotations

from dataclasses import asdict, dataclass

import numpy as np

from .simultaneous_group_certification import audit_simultaneous_group_certification
from .simultaneous_group_certification_v2 import (
    audit_simultaneous_group_certification_v2,
)


@dataclass(frozen=True)
class BootstrapTCalibrationResult:
    seed: int
    simulation_count: int
    group_count: int
    blocks_per_group: int
    bootstrap_draws: int
    confidence_level: float
    v1_familywise_rejection_count: int
    v2_familywise_rejection_count: int
    v1_familywise_rejection_rate: float
    v2_familywise_rejection_rate: float
    v2_within_ci_guardrail: bool
    v2_not_materially_worse_than_v1: bool

    def as_dict(self) -> dict[str, object]:
        return asdict(self)


def run_bootstrap_t_calibration_benchmark(
    *,
    seed: int = 20260914,
    simulation_count: int = 160,
    group_count: int = 3,
    blocks_per_group: int = 20,
    bootstrap_draws: int = 500,
    confidence_level: float = 0.95,
) -> BootstrapTCalibrationResult:
    """Estimate familywise false-positive rates under an exact Gaussian null.

    Each group contains one row per exchangeable validation block.  Block gains
    are iid N(0, 1) within and between groups, matching the independent-group
    assumptions of both compared procedures.  A familywise rejection occurs when
    any simultaneous interval excludes zero in either direction.
    """

    if simulation_count < 50:
        raise ValueError("simulation_count must be >= 50")
    if group_count < 2:
        raise ValueError("group_count must be >= 2")
    if blocks_per_group < 8:
        raise ValueError("blocks_per_group must be >= 8")
    if bootstrap_draws < 500:
        raise ValueError("bootstrap_draws must be >= 500")

    rng = np.random.default_rng(seed)
    groups = tuple(
        f"g{group_index}"
        for group_index in range(group_count)
        for _ in range(blocks_per_group)
    )
    blocks = tuple(
        f"g{group_index}-b{block_index:03d}"
        for group_index in range(group_count)
        for block_index in range(blocks_per_group)
    )

    v1_reject = 0
    v2_reject = 0
    for simulation_index in range(simulation_count):
        gain = rng.normal(
            loc=0.0,
            scale=1.0,
            size=group_count * blocks_per_group,
        )
        local_seed = seed + 100003 * (simulation_index + 1)
        v1 = audit_simultaneous_group_certification(
            gain,
            groups,
            blocks=blocks,
            familywise_confidence_level=confidence_level,
            bootstrap_draws=bootstrap_draws,
            seed=local_seed,
            minimum_blocks_per_group=8,
            gain_tolerance=0.0,
        )
        v2 = audit_simultaneous_group_certification_v2(
            gain,
            groups,
            blocks=blocks,
            familywise_confidence_level=confidence_level,
            bootstrap_draws=bootstrap_draws,
            seed=local_seed,
            minimum_blocks_per_group=8,
            gain_tolerance=0.0,
        )
        if any(row.max_t_status != "uncertain" for row in v1.groups):
            v1_reject += 1
        if any(row.bootstrap_t_status != "uncertain" for row in v2.groups):
            v2_reject += 1

    v1_rate = float(v1_reject / simulation_count)
    v2_rate = float(v2_reject / simulation_count)
    # With only 160 Monte Carlo worlds, a tight 0.05 target would be brittle.
    # The 0.12 ceiling is a CI regression guardrail, not a claimed confidence
    # interval for the operating characteristic itself.
    return BootstrapTCalibrationResult(
        seed=seed,
        simulation_count=simulation_count,
        group_count=group_count,
        blocks_per_group=blocks_per_group,
        bootstrap_draws=bootstrap_draws,
        confidence_level=float(confidence_level),
        v1_familywise_rejection_count=v1_reject,
        v2_familywise_rejection_count=v2_reject,
        v1_familywise_rejection_rate=v1_rate,
        v2_familywise_rejection_rate=v2_rate,
        v2_within_ci_guardrail=bool(v2_rate <= 0.12),
        v2_not_materially_worse_than_v1=bool(v2_rate <= v1_rate + 0.025),
    )
