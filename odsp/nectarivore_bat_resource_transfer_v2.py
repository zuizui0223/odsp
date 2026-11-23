"""Source-observation level nectar-height transfer on Bat camera visit *counts*.

Original author already established nectar/visitation correlation, so this
fixed leave-plant-out score is only exploratory predictive transport in one
forest and one liana species. No true organism 3D niche or calibrated q.
"""
from __future__ import annotations

from dataclasses import dataclass
from itertools import product
from math import exp, fsum, isfinite, log
from random import Random
from statistics import mean

LAYERS=("Low","Middle","High")
ALPHA_GRID=tuple(-2+.5*i for i in range(9))
BETA_GRID=tuple(-2+.5*i for i in range(9))
BETA_RIDGE=.02
N_BOOT=10000
SEED=20261123


@dataclass(frozen=True)
class Layer:
    name:str
    exposure:float
    resource:float
    visits:int


@dataclass(frozen=True)
class Plant:
    identity:str
    layers:tuple[Layer,...]


def validate(profiles:list[Plant]):
    if len(profiles)<5:
        raise ValueError("at least five distinct paired original plants required")
    ids=[p.identity for p in profiles]
    if len(set(ids))!=len(ids):
        raise ValueError("duplicate source plant identity")
    for p in profiles:
        if len(p.layers)<2 or len(p.layers)>3:
            raise ValueError("source plant must have two or three source camera strata")
        names=[z.name for z in p.layers]
        if any(z not in LAYERS for z in names) or len(set(names))!=len(names):
            raise ValueError("invalid or duplicate source layer")
        if any(not isfinite(z.exposure) or z.exposure<=0 or
               not isfinite(z.resource) or z.resource<0 or
               type(z.visits) is not int or z.visits<0 for z in p.layers):
            raise ValueError("invalid paired positive effort, resource or count")
        if sum(z.visits for z in p.layers)==0:
            raise ValueError("SOURCE_RESPONSE_STOP: original bat visits absent from full plant")


def score_plant(plant:Plant, a_middle:float, a_high:float, beta:float)->float:
    alpha={"Low":0.0,"Middle":a_middle,"High":a_high}
    logits=[log(z.exposure)+alpha[z.name]+beta*log(1+z.resource)
            for z in plant.layers]
    shift=max(logits)
    lden=shift+log(fsum(exp(v-shift) for v in logits))
    n=sum(z.visits for z in plant.layers)
    return fsum((z.visits/n)*(v-lden) for z,v in zip(plant.layers,logits))


def fit(profiles:list[Plant], include_resource:bool):
    validate(profiles)
    beta_candidates=BETA_GRID if include_resource else (0.0,)
    best=None
    best_params=None
    for am,ah,beta in product(ALPHA_GRID,ALPHA_GRID,beta_candidates):
        objective=mean(score_plant(p,am,ah,beta) for p in profiles)-BETA_RIDGE*beta*beta
        candidate=(round(objective,14), -abs(beta),-(abs(am)+abs(ah)),
                   -abs(am),-abs(ah),-beta,-am,-ah)
        if best is None or candidate>best:
            best=candidate
            best_params=(am,ah,beta)
    return best_params


def _percentile(sorted_values,q):
    n=len(sorted_values)
    idx=(n-1)*q
    lo=int(idx)
    hi=min(lo+1,n-1)
    return sorted_values[lo]+(idx-lo)*(sorted_values[hi]-sorted_values[lo])


def evaluate(profiles:list[Plant]):
    validate(profiles)
    out=[]
    for heldout in sorted(profiles,key=lambda p:p.identity):
        training=[p for p in profiles if p.identity!=heldout.identity]
        if any(p.identity==heldout.identity for p in training):
            raise RuntimeError("original plant heldout leakage")
        m0=fit(training,False)
        m1=fit(training,True)
        b0=score_plant(heldout,*m0)
        b1=score_plant(heldout,*m1)
        out.append({"source_plant_id":heldout.identity,
                    "n_strata":len(heldout.layers),
                    "total_visit_count":sum(z.visits for z in heldout.layers),
                    "b0":b0,"b1":b1,"delta":b1-b0,
                    "training_beta":m1[2]})
    gain=[r["delta"] for r in out]
    rng=Random(SEED)
    boots=sorted(mean(rng.choice(gain) for _ in gain) for _ in range(N_BOOT))
    positives=sum(x>0 for x in gain)
    return {
        "status":"original_source_leave_plant_out_model_evaluated",
        "target":"Bat camera recorded visit allocation across source sampled forest layers",
        "n_heldout_original_plants":len(out),
        "paired_height_cell_count":sum(len(p.layers) for p in profiles),
        "total_scored_bat_visits":sum(r["total_visit_count"] for r in out),
        "mean_B0_nats_per_recorded_visit":mean(r["b0"] for r in out),
        "mean_B1_nats_per_recorded_visit":mean(r["b1"] for r in out),
        "mean_B1_minus_B0_nats_per_recorded_visit":mean(gain),
        "positive_heldout_plant_folds":positives,
        "fold_sign_category":"all-positive" if positives==len(gain) else
          ("all-nonpositive" if positives==0 else "mixed"),
        "plant_bootstrap_95pct_descriptive":[_percentile(boots,.025),_percentile(boots,.975)],
        "source_plant_folds":[{"fold":i+1,
            "source_recorded_layers":z["n_strata"],
            "heldout_bat_visit_count":z["total_visit_count"],
            "B0":z["b0"],"B1":z["b1"],
            "delta":z["delta"],"train_resource_beta":z["training_beta"]}
            for i,z in enumerate(out)],
        "model_beta_grid":[-2,2,.5],
        "model_stratum_alpha_grid":[-2,2,.5],
        "fixed_resource_beta_ridge":BETA_RIDGE,
        "source_plant_ids_redacted_from_result":True,
        "not_bat_species_or_GPS_flight_height":True,
        "no_species_stratum_detector_calibration":True,
        "not_between_forest_prediction":True,
        "prior_author_nectar_visit_association_published":True,
    }
