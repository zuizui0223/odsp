"""Adversarial support envelope for experimental training-source process v0."""
from __future__ import annotations

from dataclasses import asdict, dataclass
import math
import numpy as np

from .training_source_process_v0 import (
    evaluate_training_source_process_positive_iut_v0,
)


GENERATOR_VERSION="nested_source_refit_support_v0"
PROCESS_SHA="8"*64
SCENARIOS=(
    ("skewed-lognormal-s8-r8-b8","lognormal",8,None),
    ("contaminated-inner-s8-r8-b20","contaminated_inner",20,None),
    ("rademacher-s8-r8-b8","rademacher",8,None),
    ("unequal-validation-weight-s8-r8-b8","normal",8,(0.5,0.5,1.0,1.0,2.0,2.0,4.0,8.0)),
    ("heteroskedastic-inner-by-source-s8-r8-b8","heteroskedastic_inner",8,None),
)


@dataclass(frozen=True)
class SourceV0SupportScenario:
    scenario_id: str
    stress: str
    blocks_per_group: int
    simulations: int
    maximum_component_false_positive_rate: float
    minimum_component_false_positive_rate: float
    terminal_false_generalizing_rate: float
    maximum_accepted_component_rate: float
    acceptance_pass: bool

    def as_dict(self):
        return asdict(self)


@dataclass(frozen=True)
class SourceV0SupportEnvelope:
    generator_version: str
    seed: int
    simulations_per_scenario: int
    scenarios: tuple[SourceV0SupportScenario,...]
    qualification_pass: bool

    def as_dict(self):
        d=asdict(self)
        d["scenarios"]=[x.as_dict() for x in self.scenarios]
        return d


def _primitive(rng,shape,kind):
    if kind=="normal":
        return rng.standard_normal(shape)
    if kind=="rademacher":
        return rng.choice(np.asarray([-1.0,1.0]),size=shape)
    if kind=="lognormal":
        sigma=1.0
        raw=np.exp(sigma*rng.standard_normal(shape))
        mean=math.exp(0.5*sigma*sigma)
        variance=(math.exp(sigma*sigma)-1.0)*math.exp(sigma*sigma)
        return (raw-mean)/math.sqrt(variance)
    if kind=="contaminated":
        base=rng.standard_normal(shape)
        scale=np.where(rng.random(shape)<0.05,6.0,1.0)
        return base*scale/math.sqrt(0.95+0.05*36.0)
    raise ValueError("unknown primitive")


def _correlated(rng,shared_shape,cell_shape,shared_weight,kind):
    return (
        math.sqrt(shared_weight)*_primitive(rng,shared_shape,kind)
        + math.sqrt(1.0-shared_weight)*_primitive(rng,cell_shape,kind)
    )


def _support_world(rng,stress,blocks):
    s=r=8
    g=6
    c=2
    source_kind=inner_kind=validation_kind=sv_kind=iv_kind="normal"
    hetero=False
    if stress=="lognormal":
        source_kind=inner_kind=validation_kind=sv_kind=iv_kind="lognormal"
    elif stress=="contaminated_inner":
        inner_kind=iv_kind="contaminated"
    elif stress=="rademacher":
        source_kind=inner_kind=validation_kind=sv_kind=iv_kind="rademacher"
    elif stress=="heteroskedastic_inner":
        hetero=True
    elif stress!="normal":
        raise ValueError("unknown support stress")

    source=0.5*_correlated(
        rng,(s,1,1),(s,g,c),0.35,source_kind
    )
    inner=0.5*_correlated(
        rng,(s,r,1,1),(s,r,g,c),0.35,inner_kind
    )
    validation=0.5*_correlated(
        rng,(g,blocks,1),(g,blocks,c),0.5,validation_kind
    )
    source_validation=0.5*_correlated(
        rng,(s,g,blocks,1),(s,g,blocks,c),0.5,sv_kind
    )
    inner_validation=0.5*_correlated(
        rng,(s,r,g,blocks,1),(s,r,g,blocks,c),0.5,iv_kind
    )

    if hetero:
        sigma=0.8
        source_scale=np.exp(
            sigma*rng.standard_normal((s,1,1,1))-sigma*sigma
        )
        inner=inner*source_scale
        inner_validation=inner_validation*source_scale[:,:,:,:,None]

    return (
        source[:,None,:,None,:]
        + inner[:,:,:,None,:]
        + validation[None,None,:,:,:]
        + source_validation[:,None,:,:,:]
        + inner_validation
    )


def _flatten(world,block_weights):
    s,r,g,b,c=world.shape
    gain=np.empty((s,r,g*b,c))
    groups=[]
    blocks=[]
    weights=[]
    w=np.ones(b) if block_weights is None else np.asarray(block_weights,dtype=float)
    row=0
    for gi in range(g):
        for bi in range(b):
            gain[:,:,row,:]=world[:,:,gi,bi,:]
            groups.append(f"g{gi:02d}")
            blocks.append(f"g{gi:02d}-b{bi:03d}")
            weights.append(float(w[bi]))
            row+=1
    return gain,tuple(groups),tuple(blocks),np.asarray(weights)


def run_training_source_v0_support_envelope(
    *,
    seed=20261018,
    simulations_per_scenario=1000,
):
    if simulations_per_scenario < 100:
        raise ValueError("simulations_per_scenario must be >= 100")
    alpha=0.05
    maximum=float(alpha+2*math.sqrt(alpha*(1-alpha)/simulations_per_scenario))
    rng=np.random.default_rng(seed)
    rows=[]
    for sid,stress,b,block_weights in SCENARIOS:
        counts=np.zeros(12,dtype=int)
        terminal=0
        for _ in range(simulations_per_scenario):
            gain,groups,blocks,weights=_flatten(
                _support_world(rng,stress,b),block_weights
            )
            result=evaluate_training_source_process_positive_iut_v0(
                gain,
                groups,
                blocks=blocks,
                source_draw_ids=tuple(f"s{i:02d}" for i in range(8)),
                inner_refit_ids_by_source=tuple(
                    tuple(f"r{j:02d}" for j in range(8)) for _ in range(8)
                ),
                source_process_id="known-source-v0-support",
                source_process_manifest_sha256=PROCESS_SHA,
                contrast_names=("pooled->coarse","coarse->fine"),
                sample_weight=weights,
                minimum_source_draws=8,
                minimum_inner_refits_per_source=8,
                minimum_blocks_per_group=8,
            )
            positive=np.asarray([
                cell.status=="robust_positive"
                for contrast in result.contrasts for cell in contrast.groups
            ],dtype=bool)
            counts += positive.astype(int)
            terminal += int(np.all(positive))
        rates=counts/simulations_per_scenario
        rows.append(SourceV0SupportScenario(
            scenario_id=sid,stress=stress,blocks_per_group=b,
            simulations=simulations_per_scenario,
            maximum_component_false_positive_rate=float(np.max(rates)),
            minimum_component_false_positive_rate=float(np.min(rates)),
            terminal_false_generalizing_rate=float(terminal/simulations_per_scenario),
            maximum_accepted_component_rate=maximum,
            acceptance_pass=bool(np.max(rates)<=maximum),
        ))
    return SourceV0SupportEnvelope(
        generator_version=GENERATOR_VERSION,
        seed=seed,
        simulations_per_scenario=simulations_per_scenario,
        scenarios=tuple(rows),
        qualification_pass=all(x.acceptance_pass for x in rows),
    )
