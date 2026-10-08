"""Prospective known-p calibration for the DISTINCT refit-level IUT v2.

Frozen before seeing any v2 simulation output. Generator scenarios and
thresholds are inherited unchanged from the failed v1 contract, while v2
replaces the validation-family max-t with per-refit IUT and alpha_v/R.
"""
from __future__ import annotations

from dataclasses import asdict, dataclass
import math

import numpy as np

from .training_process_future_refit_success_probability_calibration import (
    COVERAGE_SCENARIOS,
    POWER_SCENARIOS,
    _known_probability_world,
    _flatten_world,
)
from .training_process_future_refit_probability_iut_v2 import (
    certify_future_refit_probability_refit_iut_v2,
)

GENERATOR_VERSION = "future_refit_success_probability_refit_iut_known_p_v2"
PROCESS_SHA = "9" * 64


@dataclass(frozen=True)
class CoverageRow:
    scenario_id: str
    true_success_probability: float
    simulations: int
    overall_overclaim_rate: float
    validation_overcertification_rate: float
    mean_certified_success_count: float
    mean_probability_lower_bound: float
    maximum_accepted_overclaim_rate: float
    maximum_accepted_overcertification_rate: float
    acceptance_pass: bool

    def as_dict(self) -> dict[str, object]:
        return asdict(self)


@dataclass(frozen=True)
class PowerRow:
    scenario_id: str
    simulations: int
    all_refits_certified_power: float
    mean_certified_success_count: float
    mean_probability_lower_bound: float
    minimum_accepted_power: float
    acceptance_pass: bool

    def as_dict(self) -> dict[str, object]:
        return asdict(self)


@dataclass(frozen=True)
class RefitIUTV2Calibration:
    schema_version: int
    generator_version: str
    seed: int
    simulations_per_scenario: int
    group_count: int
    contrast_count: int
    validation_alpha: float
    process_alpha: float
    coverage_rows: tuple[CoverageRow, ...]
    power_rows: tuple[PowerRow, ...]
    qualification_pass: bool

    def as_dict(self) -> dict[str, object]:
        result = asdict(self)
        result["coverage_rows"] = [row.as_dict() for row in self.coverage_rows]
        result["power_rows"] = [row.as_dict() for row in self.power_rows]
        return result


def _run(world: np.ndarray):
    gain, groups, blocks = _flatten_world(world)
    return certify_future_refit_probability_refit_iut_v2(
        gain,
        groups,
        blocks=blocks,
        refit_ids=tuple(f"r{i:03d}" for i in range(gain.shape[0])),
        training_process_id="known-p-v2",
        training_process_manifest_sha256=PROCESS_SHA,
        contrast_names=("pooled->coarse","coarse->fine"),
    )


def run_future_refit_probability_refit_iut_v2_calibration(
    *,
    seed: int = 20261019,
    simulations_per_scenario: int = 1000,
    group_count: int = 6,
    contrast_count: int = 2,
) -> RefitIUTV2Calibration:
    if isinstance(simulations_per_scenario,bool) or not isinstance(simulations_per_scenario,int) or simulations_per_scenario<100:
        raise ValueError("simulations_per_scenario must be >=100")
    if group_count !=6 or contrast_count !=2:
        raise ValueError("v2 calibration scope frozen to 6 groups and 2 contrasts")
    if seed!=20261019:
        raise ValueError("frozen v2 calibration requires seed 20261019")
    rng=np.random.default_rng(seed)
    max_overclaim=0.05+2.0*math.sqrt(0.05*0.95/simulations_per_scenario)
    max_overcert=0.025+2.0*math.sqrt(0.025*0.975/simulations_per_scenario)
    coverage_rows=[]

    for scenario_id, dist, R, B, p_true in COVERAGE_SCENARIOS:
        overclaim=overcert=0
        counts=[]; bounds=[]
        for _ in range(simulations_per_scenario):
            world, success, _mean=_known_probability_world(
                rng,
                refit_count=R,
                blocks_per_group=B,
                group_count=group_count,
                contrast_count=contrast_count,
                p_success=p_true,
                positive_shift_oracle_se=6.0,
                training_cross_refit_validation_noise_correlation=0.35,
                contrast_correlation=0.50,
                distribution=dist,
            )
            audit=_run(world)
            k=audit.certified_success_count
            bounds.append(audit.future_refit_success_probability_lower_bound)
            counts.append(k)
            overcert+=int(k>int(np.count_nonzero(success)))
            overclaim+=int(audit.future_refit_success_probability_lower_bound>p_true+1e-12)
        claim_rate=float(overclaim)/simulations_per_scenario
        cert_rate=float(overcert)/simulations_per_scenario
        coverage_rows.append(CoverageRow(
            scenario_id=scenario_id,
            true_success_probability=p_true,
            simulations=simulations_per_scenario,
            overall_overclaim_rate=claim_rate,
            validation_overcertification_rate=cert_rate,
            mean_certified_success_count=float(np.mean(counts)),
            mean_probability_lower_bound=float(np.mean(bounds)),
            maximum_accepted_overclaim_rate=float(max_overclaim),
            maximum_accepted_overcertification_rate=float(max_overcert),
            acceptance_pass=(claim_rate<=max_overclaim and cert_rate<=max_overcert),
        ))

    power_rows=[]
    for scenario_id,dist,R,B in POWER_SCENARIOS:
        counts=[]; bounds=[]; passed=0
        for _ in range(simulations_per_scenario):
            world,success,_mean=_known_probability_world(
                rng,
                refit_count=R,
                blocks_per_group=B,
                group_count=group_count,
                contrast_count=contrast_count,
                p_success=1.0,
                positive_shift_oracle_se=8.0,
                training_cross_refit_validation_noise_correlation=0.35,
                contrast_correlation=0.50,
                distribution=dist,
            )
            assert bool(np.all(success))
            audit=_run(world)
            k=audit.certified_success_count
            counts.append(k)
            bounds.append(audit.future_refit_success_probability_lower_bound)
            passed+=int(k==R)
        power=float(passed)/simulations_per_scenario
        power_rows.append(PowerRow(
            scenario_id=scenario_id,
            simulations=simulations_per_scenario,
            all_refits_certified_power=power,
            mean_certified_success_count=float(np.mean(counts)),
            mean_probability_lower_bound=float(np.mean(bounds)),
            minimum_accepted_power=0.80,
            acceptance_pass=(power>=0.80),
        ))
    return RefitIUTV2Calibration(
        schema_version=2,
        generator_version=GENERATOR_VERSION,
        seed=seed,
        simulations_per_scenario=simulations_per_scenario,
        group_count=group_count,
        contrast_count=contrast_count,
        validation_alpha=0.025,
        process_alpha=0.025,
        coverage_rows=tuple(coverage_rows),
        power_rows=tuple(power_rows),
        qualification_pass=all(x.acceptance_pass for x in coverage_rows+power_rows),
    )
