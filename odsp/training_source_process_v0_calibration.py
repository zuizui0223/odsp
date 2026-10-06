"""Prospective operating-characteristic panels for training-source process v0."""
from __future__ import annotations

from dataclasses import asdict, dataclass
import math
import numpy as np

from .training_source_process_v0 import (
    evaluate_training_source_process_positive_iut_v0,
)


GENERATOR_VERSION = "nested_source_refit_x_validation_c2_v0"
PROCESS_SHA = "7" * 64
SCENARIOS = (
    ("balanced-normal-s8-r8-b8", "normal", 8, 8, 8, 0.5, 0.5, 0.5, 0.5, 0.5),
    ("source-dominant-normal-s8-r20-b20", "normal", 8, 20, 20, 0.8, 0.2, 0.2, 0.3, 0.2),
    ("inner-dominant-normal-s20-r8-b20", "normal", 20, 8, 20, 0.2, 0.8, 0.2, 0.2, 0.5),
    ("validation-dominant-normal-s20-r20-b8", "normal", 20, 20, 8, 0.2, 0.2, 0.8, 0.3, 0.2),
    ("interaction-dominant-normal-s8-r8-b8", "normal", 8, 8, 8, 0.1, 0.1, 0.1, 0.9, 0.7),
    ("balanced-t3-s8-r8-b20", "student_t3", 8, 8, 20, 0.5, 0.5, 0.5, 0.5, 0.5),
)


@dataclass(frozen=True)
class SourceV0NullScenario:
    scenario_id: str
    distribution: str
    source_draw_count: int
    inner_refit_count: int
    blocks_per_group: int
    simulations: int
    component_false_positive_rates: tuple[float, ...]
    maximum_component_false_positive_rate: float
    minimum_component_false_positive_rate: float
    terminal_false_generalizing_rate: float
    maximum_accepted_component_rate: float
    acceptance_pass: bool

    def as_dict(self):
        d=asdict(self)
        d["component_false_positive_rates"]=list(self.component_false_positive_rates)
        return d


@dataclass(frozen=True)
class SourceV0NullCalibration:
    generator_version: str
    seed: int
    simulations_per_scenario: int
    group_count: int
    contrast_count: int
    scenarios: tuple[SourceV0NullScenario, ...]
    qualification_pass: bool

    def as_dict(self):
        d=asdict(self)
        d["scenarios"]=[x.as_dict() for x in self.scenarios]
        return d


@dataclass(frozen=True)
class SourceV0PowerScenario:
    scenario_id: str
    distribution: str
    source_draw_count: int
    inner_refit_count: int
    blocks_per_group: int
    simulations: int
    oracle_cell_standard_error: float
    moderate_gain_shift: float
    moderate_terminal_power: float
    strong_gain_shift: float
    strong_terminal_power: float
    minimum_accepted_strong_terminal_power: float
    monotonic_power: bool
    acceptance_pass: bool

    def as_dict(self):
        return asdict(self)


@dataclass(frozen=True)
class SourceV0PowerCalibration:
    generator_version: str
    seed: int
    simulations_per_scenario: int
    group_count: int
    contrast_count: int
    moderate_shift_oracle_standard_errors: float
    strong_shift_oracle_standard_errors: float
    minimum_accepted_strong_terminal_power: float
    scenarios: tuple[SourceV0PowerScenario, ...]
    qualification_pass: bool

    def as_dict(self):
        d=asdict(self)
        d["scenarios"]=[x.as_dict() for x in self.scenarios]
        return d


def _primitive(rng, shape, distribution):
    if distribution == "normal":
        return rng.standard_normal(shape)
    if distribution == "student_t3":
        return rng.standard_t(3, size=shape) / math.sqrt(3.0)
    raise ValueError("unknown distribution")


def _world(
    rng,
    *,
    distribution,
    source_count,
    inner_count,
    blocks,
    groups=6,
    contrasts=2,
    source_sd,
    inner_sd,
    validation_sd,
    source_validation_sd,
    inner_validation_sd,
    source_cross_cell_correlation=0.35,
    inner_cross_cell_correlation=0.35,
    contrast_correlation=0.5,
):
    source = source_sd * (
        math.sqrt(source_cross_cell_correlation)
        * _primitive(rng, (source_count, 1, 1), distribution)
        + math.sqrt(1.0-source_cross_cell_correlation)
        * _primitive(rng, (source_count, groups, contrasts), distribution)
    )
    inner = inner_sd * (
        math.sqrt(inner_cross_cell_correlation)
        * _primitive(rng, (source_count, inner_count, 1, 1), distribution)
        + math.sqrt(1.0-inner_cross_cell_correlation)
        * _primitive(rng, (source_count, inner_count, groups, contrasts), distribution)
    )
    validation = validation_sd * (
        math.sqrt(contrast_correlation)
        * _primitive(rng, (groups, blocks, 1), distribution)
        + math.sqrt(1.0-contrast_correlation)
        * _primitive(rng, (groups, blocks, contrasts), distribution)
    )
    source_validation = source_validation_sd * (
        math.sqrt(contrast_correlation)
        * _primitive(rng, (source_count, groups, blocks, 1), distribution)
        + math.sqrt(1.0-contrast_correlation)
        * _primitive(rng, (source_count, groups, blocks, contrasts), distribution)
    )
    inner_validation = inner_validation_sd * (
        math.sqrt(contrast_correlation)
        * _primitive(rng, (source_count, inner_count, groups, blocks, 1), distribution)
        + math.sqrt(1.0-contrast_correlation)
        * _primitive(rng, (source_count, inner_count, groups, blocks, contrasts), distribution)
    )
    return (
        source[:, None, :, None, :]
        + inner[:, :, :, None, :]
        + validation[None, None, :, :, :]
        + source_validation[:, None, :, :, :]
        + inner_validation
    )


def _flatten(world):
    s,r,g,b,c=world.shape
    gain=np.empty((s,r,g*b,c),dtype=float)
    groups=[]
    blocks=[]
    row=0
    for gi in range(g):
        for bi in range(b):
            gain[:,:,row,:]=world[:,:,gi,bi,:]
            groups.append(f"g{gi:02d}")
            blocks.append(f"g{gi:02d}-b{bi:03d}")
            row+=1
    return gain,tuple(groups),tuple(blocks)


def _evaluate(world):
    gain,groups,blocks=_flatten(world)
    s,r=world.shape[:2]
    return evaluate_training_source_process_positive_iut_v0(
        gain,
        groups,
        blocks=blocks,
        source_draw_ids=tuple(f"s{i:03d}" for i in range(s)),
        inner_refit_ids_by_source=tuple(
            tuple(f"r{j:03d}" for j in range(r)) for _ in range(s)
        ),
        source_process_id="known-source-v0-calibration",
        source_process_manifest_sha256=PROCESS_SHA,
        contrast_names=("pooled->coarse","coarse->fine"),
        minimum_source_draws=8,
        minimum_inner_refits_per_source=8,
        minimum_blocks_per_group=8,
    )


def _oracle_se(s,r,b,source_sd,inner_sd,validation_sd,sv_sd,iv_sd):
    variance=(
        source_sd**2/s
        + inner_sd**2/(s*r)
        + validation_sd**2/b
        + sv_sd**2/(s*b)
        + iv_sd**2/(s*r*b)
    )
    return float(math.sqrt(variance))


def run_training_source_v0_null_calibration(
    *,
    seed=20261016,
    simulations_per_scenario=1000,
    group_count=6,
    contrast_count=2,
):
    if simulations_per_scenario < 100:
        raise ValueError("simulations_per_scenario must be >= 100")
    if group_count != 6 or contrast_count != 2:
        raise ValueError("v0 calibration is frozen to 6 groups and 2 contrasts")
    alpha=0.05
    max_rate=float(alpha+2*math.sqrt(alpha*(1-alpha)/simulations_per_scenario))
    rng=np.random.default_rng(seed)
    rows=[]
    for spec in SCENARIOS:
        sid,dist,s,r,b,ss,rs,vs,svs,ivs=spec
        counts=np.zeros(group_count*contrast_count,dtype=int)
        terminal=0
        for _ in range(simulations_per_scenario):
            result=_evaluate(_world(
                rng,distribution=dist,source_count=s,inner_count=r,blocks=b,
                groups=group_count,contrasts=contrast_count,
                source_sd=ss,inner_sd=rs,validation_sd=vs,
                source_validation_sd=svs,inner_validation_sd=ivs,
            ))
            positive=np.asarray([
                cell.status=="robust_positive"
                for contrast in result.contrasts for cell in contrast.groups
            ],dtype=bool)
            counts += positive.astype(int)
            terminal += int(np.all(positive))
        rates=counts/simulations_per_scenario
        rows.append(SourceV0NullScenario(
            scenario_id=sid,distribution=dist,source_draw_count=s,
            inner_refit_count=r,blocks_per_group=b,simulations=simulations_per_scenario,
            component_false_positive_rates=tuple(float(x) for x in rates),
            maximum_component_false_positive_rate=float(np.max(rates)),
            minimum_component_false_positive_rate=float(np.min(rates)),
            terminal_false_generalizing_rate=float(terminal/simulations_per_scenario),
            maximum_accepted_component_rate=max_rate,
            acceptance_pass=bool(np.max(rates)<=max_rate),
        ))
    return SourceV0NullCalibration(
        generator_version=GENERATOR_VERSION,seed=seed,
        simulations_per_scenario=simulations_per_scenario,
        group_count=group_count,contrast_count=contrast_count,
        scenarios=tuple(rows),
        qualification_pass=all(x.acceptance_pass for x in rows),
    )


def run_training_source_v0_power_calibration(
    *,
    seed=20261017,
    simulations_per_scenario=1000,
    group_count=6,
    contrast_count=2,
    moderate_shift_oracle_standard_errors=3.0,
    strong_shift_oracle_standard_errors=5.0,
    minimum_accepted_strong_terminal_power=0.8,
):
    if simulations_per_scenario < 100:
        raise ValueError("simulations_per_scenario must be >= 100")
    if group_count != 6 or contrast_count != 2:
        raise ValueError("v0 calibration is frozen to 6 groups and 2 contrasts")
    if not 0 < moderate_shift_oracle_standard_errors < strong_shift_oracle_standard_errors:
        raise ValueError("standardized shifts must satisfy 0 < moderate < strong")
    rng=np.random.default_rng(seed)
    rows=[]
    for spec in SCENARIOS:
        sid,dist,s,r,b,ss,rs,vs,svs,ivs=spec
        oracle=_oracle_se(s,r,b,ss,rs,vs,svs,ivs)
        moderate=moderate_shift_oracle_standard_errors*oracle
        strong=strong_shift_oracle_standard_errors*oracle
        m=0
        q=0
        for _ in range(simulations_per_scenario):
            result=_evaluate(_world(
                rng,distribution=dist,source_count=s,inner_count=r,blocks=b,
                groups=group_count,contrasts=contrast_count,
                source_sd=ss,inner_sd=rs,validation_sd=vs,
                source_validation_sd=svs,inner_validation_sd=ivs,
            ))
            lowers=[cell.lower_bound for contrast in result.contrasts for cell in contrast.groups]
            if any(x is None for x in lowers):
                raise AssertionError("power world unexpectedly unavailable")
            minimum=min(float(x) for x in lowers)
            m += int(minimum+moderate>0)
            q += int(minimum+strong>0)
        mp=float(m/simulations_per_scenario)
        sp=float(q/simulations_per_scenario)
        rows.append(SourceV0PowerScenario(
            scenario_id=sid,distribution=dist,source_draw_count=s,
            inner_refit_count=r,blocks_per_group=b,simulations=simulations_per_scenario,
            oracle_cell_standard_error=oracle,
            moderate_gain_shift=float(moderate),moderate_terminal_power=mp,
            strong_gain_shift=float(strong),strong_terminal_power=sp,
            minimum_accepted_strong_terminal_power=float(minimum_accepted_strong_terminal_power),
            monotonic_power=bool(sp>=mp),
            acceptance_pass=bool(sp>=mp and sp>=minimum_accepted_strong_terminal_power),
        ))
    return SourceV0PowerCalibration(
        generator_version=GENERATOR_VERSION,seed=seed,
        simulations_per_scenario=simulations_per_scenario,
        group_count=group_count,contrast_count=contrast_count,
        moderate_shift_oracle_standard_errors=float(moderate_shift_oracle_standard_errors),
        strong_shift_oracle_standard_errors=float(strong_shift_oracle_standard_errors),
        minimum_accepted_strong_terminal_power=float(minimum_accepted_strong_terminal_power),
        scenarios=tuple(rows),
        qualification_pass=all(x.acceptance_pass for x in rows),
    )
