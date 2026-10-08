"""Zero-preserving exposure-offset conditional branch-shape inference, SYNTHETIC ONLY.

Poisson pair:
  A_i ~ Pois(E_A,i * lambda_i)
  D_i ~ Pois(E_D,i * lambda_i * exp(beta_bin))
Condition on N_i=A_i+D_i:
  D_i | N_i ~ Binomial(N_i, sigmoid(log(E_D/E_A)+beta_bin))

Unknown station × pair × species × bin baseline lambda_i cancels.
Consequently a one-day-only detection IS informative when both days
were operational; zero/zero cells remain in the observation frame but
yield exactly zero conditional log score. A zero-exposure/zero-count
cell is not a valid missing-day negative sample or an informative
binomial comparison; positive count at zero exposure is invalid.

Null beta_bin=alpha for ALL six bins permits any constant overall
branch rate change. Alternative beta_bin may vary by bin with frozen
quadratic penalty toward their common mean. Only heldout PHYSICAL
stations can be used to evaluate a gain, and every model predicts the
identical falling-branch event count given total and the same operating
hour offsets. A positive heldout gain would imply *conditional detected
time shape* improvement, NOT photoperiod causality or occupancy.

No original EcoBank animal, camera-operation or station source records
are downloaded or opened here. Actual independent source-log lineage,
camera operation and region sampling are not established.
"""
from __future__ import annotations

from dataclasses import asdict, dataclass
import math
from typing import Sequence

import numpy as np

VERSION="uljin_mirror_exposure_offset_conditional_binomial_v0"
BINS=6
LAMBDA=2.
RIDGE_INTERCEPT=1e-6
MAX_ITER=120
TOL=1e-9
BOUND=25.


@dataclass(frozen=True)
class MirrorCountCell:
    station:str
    region:str
    taxon:str
    pair_id:str
    clock_bin:int
    rising_count:int
    falling_count:int
    rising_active_hours:float
    falling_active_hours:float

    def __post_init__(self):
        if any(not isinstance(v,str) or not v.strip()
               for v in (self.station,self.region,self.taxon,self.pair_id)):
            raise ValueError("missing physical station/pair/species identity")
        if self.region not in ("UJ1","UJ2") or not self.station.startswith(self.region):
            raise ValueError("station/region identity mismatch")
        if type(self.clock_bin) is not int or not 0<=self.clock_bin<6:
            raise ValueError("exact six-bin common civil-clock category required")
        if any(type(n) is not int or n<0 for n in
               (self.rising_count,self.falling_count)):
            raise ValueError("count must be a nonnegative integer")
        for label,exposure,n in (
            ("rising",self.rising_active_hours,self.rising_count),
            ("falling",self.falling_active_hours,self.falling_count),
        ):
            if (
                isinstance(exposure,bool)
                or not isinstance(exposure,(float,int))
                or not math.isfinite(exposure)
                or not 0<=exposure<=4
            ):
                raise ValueError(f"{label} hourly camera exposure must lie in [0,4]")
            if exposure==0 and n!=0:
                raise ValueError("positive detection at zero independently logged exposure")

    @property
    def is_informative(self)->bool:
        return (self.rising_active_hours>0 and self.falling_active_hours>0
                and self.rising_count+self.falling_count>0)


@dataclass(frozen=True)
class FrozenBranchModel:
    model:str
    six_branch_log_rate_ratios:tuple[float,...]
    penalty_lambda:float
    informative_training_cells:int
    informative_training_detections:int
    objective_at_solution:float
    target:"str"="Falling-branch detections conditional on total, with operational offset"

    def as_dict(self)->dict[str,object]:
        return asdict(self)


def _validate_unique(rows:Sequence[MirrorCountCell])->None:
    seen=set()
    for row in rows:
        if not isinstance(row,MirrorCountCell):
            raise ValueError("all original station x pair x taxon x bin cells required")
        key=(row.station,row.pair_id,row.taxon,row.clock_bin)
        if key in seen:
            raise ValueError("duplicated physical station×pair×taxon×clock-bin")
        seen.add(key)


def _informative(rows:Sequence[MirrorCountCell]):
    data=[r for r in rows if r.is_informative]
    bins=np.array([r.clock_bin for r in data],dtype=int)
    offset=np.array([
        math.log(r.falling_active_hours/r.rising_active_hours) for r in data
    ],dtype=float)
    n=np.array([r.rising_count+r.falling_count for r in data],dtype=float)
    y=np.array([r.falling_count for r in data],dtype=float)
    return bins,offset,n,y


def _probability(logit:np.ndarray)->np.ndarray:
    val=np.clip(logit,-BOUND,BOUND)
    return 1./(1.+np.exp(-val))


def _objective(beta:np.ndarray,bins:np.ndarray,offset:np.ndarray,
               n:np.ndarray,y:np.ndarray,ridge:float)->float:
    eta=offset+beta[bins]
    base=float(np.sum(y*eta-n*np.logaddexp(0.,eta)))
    if beta.size==1:
        penalty=.5*RIDGE_INTERCEPT*beta[0]*beta[0]
    else:
        centered=beta-beta.mean()
        penalty=.5*ridge*np.sum(centered**2)
        penalty+=.5*RIDGE_INTERCEPT*beta.mean()**2
    return base-float(penalty)


def fit_conditional_branch_model(
    rows:Sequence[MirrorCountCell],
    *,
    allow_branch_shape:bool,
    lambda_penalty:float=LAMBDA,
)->FrozenBranchModel:
    """Training-only penalized conditional likelihood, no source rows."""
    if type(allow_branch_shape) is not bool or lambda_penalty!=LAMBDA:
        raise ValueError("null/shape switch or frozen ridge penalty invalid")
    _validate_unique(rows)
    bins,offset,n,y=_informative(rows)
    if len(n)==0 or n.sum()<30:
        raise ValueError("insufficient informative training events")
    if allow_branch_shape:
        beta=np.zeros(6)
        cols=bins
        ridge=LAMBDA
    else:
        beta=np.zeros(1)
        cols=np.zeros_like(bins)
        ridge=0.
    for _ in range(MAX_ITER):
        eta=offset+beta[cols]
        p=_probability(eta)
        gradient=np.bincount(cols,weights=y-n*p,minlength=beta.size)
        weights=np.bincount(cols,weights=n*p*(1-p),minlength=beta.size)
        H=np.diag(weights)
        if allow_branch_shape:
            avg=beta.mean()
            gradient-=ridge*(beta-avg)
            gradient-=RIDGE_INTERCEPT*avg/6
            H+=ridge*(np.eye(6)-np.ones((6,6))/6)
            H+=RIDGE_INTERCEPT*np.ones((6,6))/36
        else:
            gradient-=RIDGE_INTERCEPT*beta[0]
            H[0,0]+=RIDGE_INTERCEPT
        if np.max(np.abs(gradient))<TOL:
            break
        try:
            direction=np.linalg.solve(H,gradient)
        except np.linalg.LinAlgError as exc:
            raise ValueError("ill-conditioned frozen conditional model") from exc
        old_obj=_objective(beta,cols,offset,n,y,ridge)
        for k in range(40):
            rate=2.**-k
            new=np.clip(beta+rate*direction,-BOUND,BOUND)
            value=_objective(new,cols,offset,n,y,ridge)
            if value>=old_obj-1e-10:
                beta=new
                break
        else:
            raise ValueError("fixed-penalty conditional fit did not converge")
        if np.max(np.abs(rate*direction))<1e-9:
            break
    else:
        raise ValueError("conditional model did not converge in frozen iterations")
    return FrozenBranchModel(
        model="branch_by_clock_bin" if allow_branch_shape else "common_branch_rate",
        six_branch_log_rate_ratios=tuple(
            float(x) for x in (beta if allow_branch_shape else np.repeat(beta,6))
        ),
        penalty_lambda=ridge,
        informative_training_cells=len(n),
        informative_training_detections=int(n.sum()),
        objective_at_solution=_objective(beta,cols,offset,n,y,ridge),
    )


def expected_falling_probability(
    rising_active_hours:float,falling_active_hours:float,beta:float
)->float | None:
    if not all(math.isfinite(float(v)) for v in (
        rising_active_hours,falling_active_hours,beta
    )) or any(v<0 for v in (rising_active_hours,falling_active_hours)):
        raise ValueError("invalid independently recorded exposure and rate contrast")
    a,b=float(rising_active_hours),float(falling_active_hours)
    if a==0 and b==0:
        return None
    if a==0:return 1.
    if b==0:return 0.
    return float(_probability(np.array([math.log(b/a)+beta]))[0])


def conditional_logprob(
    row:MirrorCountCell,model:FrozenBranchModel,
)->float:
    """Fixed count-conditional log likelihood including one-sided detections."""
    if not isinstance(model,FrozenBranchModel) or len(model.six_branch_log_rate_ratios)!=6:
        raise ValueError("model must supply six frozen branch probabilities")
    if not row.is_informative:
        return 0.
    beta=model.six_branch_log_rate_ratios[row.clock_bin]
    eta=math.log(row.falling_active_hours/row.rising_active_hours)+beta
    n=row.rising_count+row.falling_count
    return (row.falling_count*eta-n*float(np.logaddexp(0.,eta)))


def score_heldout_station_frame(
    training:Sequence[MirrorCountCell],
    heldout:Sequence[MirrorCountCell],
)->dict[str,object]:
    """No post-outcome station selection; score identical conditional counts."""
    _validate_unique(training)
    _validate_unique(heldout)
    training_sites={x.station for x in training}
    test_sites={x.station for x in heldout}
    if not training_sites or not test_sites or training_sites & test_sites:
        raise ValueError("training and heldout physical station frames must be disjoint")
    null=fit_conditional_branch_model(training,allow_branch_shape=False)
    alternative=fit_conditional_branch_model(training,allow_branch_shape=True)
    sites=sorted(test_sites)
    site_rows={site:[r for r in heldout if r.station==site] for site in sites}
    site_results=[]
    for station in sites:
        values=site_rows[station]
        gains=[
            conditional_logprob(r,alternative)-conditional_logprob(r,null)
            for r in values
        ]
        site_results.append({
            "region":values[0].region,
            "site_normalized_gain":float(np.sum(gains)/len(values)),
            "raw_gain":float(np.sum(gains)),
            "station_total_original_cells":len(values),
            "station_informative_cells":sum(r.is_informative for r in values),
            "station_informative_event_count":sum(
                r.rising_count+r.falling_count for r in values if r.is_informative
            ),
        })
    per_region={}
    for name in ("UJ1","UJ2"):
        subs=[r for r in site_results if r["region"]==name]
        per_region[name]={
            "station_count":len(subs),
            "site_equal_mean_gain":(
                float(np.mean([r["site_normalized_gain"] for r in subs]))
                if subs else None
            ),
            "original_station_clock_cells":sum(
                r["station_total_original_cells"] for r in subs
            ),
            "informative_station_clock_cells":sum(
                r["station_informative_cells"] for r in subs
            ),
            "informative_conditioned_event_count":sum(
                r["station_informative_event_count"] for r in subs
            ),
        }
    # Contains no physical IDs: protect the restricted camera location roster.
    return {
        "method_version":VERSION,
        "status":"SYNTHETIC_ONLY_CONDITIONAL_BINOMIAL_HELDOUT_COMPARISON",
        "train_physical_sites":len(training_sites),
        "test_physical_sites":len(test_sites),
        "test_site_equal_mean_conditional_gain":float(np.mean([
            r["site_normalized_gain"] for r in site_results
        ])),
        "test_total_conditional_gain":float(np.sum([r["raw_gain"] for r in site_results])),
        "site_region_support":per_region,
        "training_null":null.as_dict(),
        "training_branch_shape":alternative.as_dict(),
        "includes_one_sided_positive_counts":True,
        "zero_zero_cells_retained_but_conditionally_noninformative":True,
        "model_exposure_values_are_independently_verified_in_real_EcoBank":False,
        "test_source_is_original_EcoBank":False,
        "posterior_or_pvalue_computed":False,
        "between_region_population_inference_supported":False,
        "causal_photoperiod_memory_claimed":False,
        "previous_qualified_ODSP_ecological_routes_reclassified":False,
    }
