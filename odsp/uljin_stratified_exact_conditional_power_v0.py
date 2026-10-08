"""Exact site-conditioned seasonal early/late interaction: a source-free study.

For site i, preserve the 2x2 margins N_i total, K_i early-phase total,
D_i falling-season total. Under the null of NO within-site season×bin
interaction, X_i=falling-early is central hypergeometric. Site-dependent
overall season rate and site-dependent phase profiles are permitted.
The sum T=Σ_i X_i has an exact convolution distribution conditional
on every site's margins. For a COMMON conditional OR theta, exponential
tilting of the central distribution gives exact noncentral power.

Do not confuse site-conditional design power with real camera detections.
None of the artificial margins comes from the EcoBank event/uptime files.
"""
from __future__ import annotations

from dataclasses import dataclass
from collections.abc import Mapping
from math import lgamma, log, exp, isfinite
import numpy as np

METHOD="uljin_stratified_exact_conditional_power_v0"
ALPHA=.05
SIZES=(2,4,8,16)
THETAS=(1.,1.5,2.,3.)
TEMPLATES=("sparse_balanced","moderate_balanced",
           "composition_confounded_alternating")


@dataclass(frozen=True)
class FixedSiteMargins:
    N:int
    K:int
    D:int

    def __post_init__(self):
        if any(type(x) is not int for x in (self.N,self.K,self.D)):
            raise ValueError("physical-site margins must be integers")
        if not (self.N>0 and 0<=self.K<=self.N and 0<=self.D<=self.N):
            raise ValueError("invalid site-conditional row/column totals")

    @property
    def bounds(self)->tuple[int,int]:
        return max(0,self.K+self.D-self.N),min(self.K,self.D)


def _freeze(plan:Mapping[str,object])->None:
    rows=plan.get("stratum_templates",[])
    if (
        not isinstance(plan,Mapping)
        or plan.get("schema_version")!=1
        or plan.get("contract_id")!=METHOD
        or plan.get("stage")!="FROZEN_SOURCE_FREE_BEFORE_FIRST_STRATIFIED_CONDITIONAL_OUTCOME"
        or plan.get("parent_pr")!=242
        or plan.get("previous_idealized_fisher_contract")!=
            "ULJIN_EXACT_TWO_BIN_OR_POWER_V0_CONTRACT.json"
        or plan.get("true_common_OR")!=list(THETAS)
        or plan.get("site_count_grid")!=list(SIZES)
        or plan.get("nominal_alpha")!=ALPHA
        or [r.get("id") for r in rows]!=list(TEMPLATES)
        or rows[0]!={"id":"sparse_balanced","N":4,"K":2,"D":2}
        or rows[1]!={"id":"moderate_balanced","N":20,"K":10,"D":10}
        or rows[2]!={"id":"composition_confounded_alternating","sites":[
            {"site_type":"early_profile_high_falling_rate",
             "N":80,"K":72,"D":60,"witness_falling_early":54},
            {"site_type":"late_profile_low_falling_rate",
             "N":80,"K":8,"D":20,"witness_falling_early":2}
        ]}
        or plan.get("source_provenance")!={
            "original_EcoBank_outcomes_read":False,
            "original_camera_uptime_read":False,
            "site_coordinates_read":False
        }
    ):
        raise ValueError("source-free site-conditional pre-outcome contract altered")


def _log_choose(n:int,k:int)->float:
    if not 0<=k<=n:
        return float("-inf")
    return lgamma(n+1)-lgamma(k+1)-lgamma(n-k+1)


def central_site_hypergeom(m:FixedSiteMargins)->tuple[int,np.ndarray]:
    lo,hi=m.bounds
    logweights=np.asarray([
        _log_choose(m.K,x)+_log_choose(m.N-m.K,m.D-x)
        for x in range(lo,hi+1)],dtype=float)
    w=np.exp(logweights-logweights.max())
    p=w/w.sum()
    if not isfinite(float(p.sum())) or abs(float(p.sum())-1)>1e-12:
        raise ValueError("hypergeometric probability failed normalization")
    return lo,p


def stratified_null_convolution(
    sites:list[FixedSiteMargins],
)->tuple[int,np.ndarray]:
    if not sites or not all(isinstance(m,FixedSiteMargins) for m in sites):
        raise ValueError("requires original separate physical site margins")
    lo=0
    p=np.array([1.])
    for site in sites:
        offset,q=central_site_hypergeom(site)
        lo+=offset
        p=np.convolve(p,q)
        p/=p.sum()
    if np.any(p<0) or abs(float(p.sum())-1)>1e-12:
        raise ValueError("stratum-conditioned null distribution invalid")
    return lo,p


def common_OR_tilt(offset:int,central:np.ndarray,theta:float)->np.ndarray:
    if (
        type(offset) is not int or offset<0
        or not isinstance(theta,(int,float)) or isinstance(theta,bool)
        or not isfinite(theta) or theta<=0
        or central.ndim!=1 or not len(central)
        or np.any(central<0) or not np.isfinite(central).all()
        or abs(float(central.sum())-1)>1e-10
    ):
        raise ValueError("invalid conditional distribution/OR tilt")
    if theta==1:
        return central.copy()
    with np.errstate(divide="ignore"):
        lp=np.log(central)
    logw=lp+np.arange(len(central))*log(theta)
    finite=np.isfinite(logw)
    if not finite.any():
        raise ValueError("conditional tilted support empty")
    z=np.exp(logw-np.max(logw[finite]))
    q=z/z.sum()
    if not isfinite(float(q.sum())) or abs(float(q.sum())-1)>1e-12:
        raise ValueError("noncentral distribution failed normalization")
    return q


def exact_upper_tail_threshold(offset:int,p:np.ndarray,
                               alpha:float=ALPHA)->tuple[int,float]:
    if (p.ndim!=1 or not len(p) or not 0<alpha<1
        or np.any(p<0) or not np.isfinite(p).all()
        or abs(float(p.sum())-1)>1e-10):
        raise ValueError("exact upper-tail input invalid")
    tails=np.cumsum(p[::-1])[::-1]
    hit=np.flatnonzero(tails<=alpha+1e-14)
    if len(hit)==0:
        return offset+len(p),0.
    k=int(hit[0])
    return offset+k,float(tails[k])


def rejection_prob(offset:int,p:np.ndarray,threshold:int)->float:
    idx=threshold-offset
    return float(p[max(0,idx):].sum())


def sites_for_design(kind:str,R:int)->list[FixedSiteMargins]:
    if kind not in TEMPLATES or R not in SIZES:
        raise ValueError("only the frozen site families and sizes are admissible")
    if kind=="sparse_balanced":
        return [FixedSiteMargins(4,2,2) for _ in range(R)]
    if kind=="moderate_balanced":
        return [FixedSiteMargins(20,10,10) for _ in range(R)]
    return [FixedSiteMargins(80,72,60) if i%2==0
            else FixedSiteMargins(80,8,20) for i in range(R)]


def pooled_margins(sites:list[FixedSiteMargins])->FixedSiteMargins:
    return FixedSiteMargins(sum(v.N for v in sites),sum(v.K for v in sites),
                            sum(v.D for v in sites))


def witness_composition()->dict[str,object]:
    sites=sites_for_design("composition_confounded_alternating",2)
    x=(54,2)
    if any(not m.bounds[0]<=z<=m.bounds[1] for m,z in zip(sites,x)):
        raise ValueError("witness cells violate frozen sites")
    odds=[]
    for m,z in zip(sites,x):
        rise_early=m.K-z
        rise_late=(m.N-m.D)-rise_early
        fall_late=m.D-z
        if min(z,rise_early,rise_late,fall_late)<=0:
            raise ValueError("witness contains impossible nonpositive cell")
        odds.append((z*rise_late)/(rise_early*fall_late))
    pooled=pooled_margins(sites)
    total_x=sum(x)
    pooled_or=(total_x*(pooled.N-pooled.K-pooled.D+total_x))/(
        (pooled.K-total_x)*(pooled.D-total_x))
    strata_lo,p=stratified_null_convolution(sites)
    s_p=rejection_prob(strata_lo,p,total_x)
    pool_lo,q=central_site_hypergeom(pooled)
    p_p=rejection_prob(pool_lo,q,total_x)
    if any(abs(t-1.)>1e-12 for t in odds) or pooled_or<=1:
        raise ValueError("Simpson witness within-site null not reproduced")
    return {
       "two_fixed_physical_site_margins":[{"N":v.N,"K":v.K,"D":v.D}
                                            for v in sites],
       "falling_early_counts_per_site":list(x),
       "within_site_observed_OR":odds,
       "naively_pooled_observed_OR":pooled_or,
       "observed_total_falling_early":total_x,
       "stratified_null_conditional_expectation":
           sum(m.D*m.K/m.N for m in sites),
       "stratified_exact_one_sided_p":s_p,
       "naive_pooled_one_sided_fisher_p":p_p,
       "fixed_total_event_count":pooled.N,
       "witness_is_synthetic_not_observed":True,
    }


def run_stratified_exact_panel(plan:Mapping[str,object])->dict[str,object]:
    _freeze(plan)
    all_cases=[]
    for kind in TEMPLATES:
        for R in SIZES:
            sites=sites_for_design(kind,R)
            off,null=stratified_null_convolution(sites)
            cs,size=exact_upper_tail_threshold(off,null)
            pool=pooled_margins(sites)
            offpool,poolnull=central_site_hypergeom(pool)
            cp,pooled_nominal_conditional_size=exact_upper_tail_threshold(
                offpool,poolnull)
            actual_pooled_null_rejection=rejection_prob(off,null,cp)
            cases_theta=[]
            last_power=-1.
            for theta in THETAS:
                true_dist=common_OR_tilt(off,null,theta)
                exact_power=rejection_prob(off,true_dist,cs)
                naive_reject=rejection_prob(off,true_dist,cp)
                if exact_power+1e-12<last_power:
                    raise ValueError("common odds-ratio power ordering failed")
                last_power=exact_power
                cases_theta.append({
                    "true_common_within_site_OR":theta,
                    "stratified_exact_conditional_rejection_probability":
                        exact_power,
                    "pooled_naive_conditional_rejection_probability":
                        naive_reject,
                })
            if abs(cases_theta[0][
                 "stratified_exact_conditional_rejection_probability"]-size)>1e-12:
                raise ValueError("conditional null size not preserved")
            if size>ALPHA+1e-12:
                raise ValueError("site-stratified exact conditional size exceeded alpha")
            all_cases.append({
                "template":kind,
                "independent_physical_site_count":R,
                "total_fixed_synthetic_detections":pool.N,
                "pooled_early_phase_count":pool.K,
                "pooled_falling_branch_count":pool.D,
                "true_null_within_each_site_branch_phase_OR":1,
                "stratified_rejection_threshold":cs,
                "stratified_exact_null_rejection_probability":size,
                "naive_pooled_rejection_threshold":cp,
                "naive_pooled_nominal_5pct_size_if_sites_ignored":
                    pooled_nominal_conditional_size,
                "naive_pooled_ACTUAL_null_rejection_probability_under_site_margins":
                    actual_pooled_null_rejection,
                "by_common_true_OR":cases_theta,
            })
    worst=max(c["naive_pooled_ACTUAL_null_rejection_probability_under_site_margins"]
              for c in all_cases if c["template"]=="composition_confounded_alternating")
    if (
        len(all_cases)!=12 or sum(len(z["by_common_true_OR"]) for z in all_cases)!=48
        or worst<=ALPHA+1e-8
    ):
        raise ValueError("frozen stratified adversarial calibration matrix incomplete")
    return {
        "schema_version":1,
        "method":METHOD,
        "status":"SOURCE_FREE_SITE_STRATIFIED_EXACT_CONDITIONAL_SIZE_POWER",
        "nominal_one_sided_alpha":ALPHA,
        "truth_common_ORs":list(THETAS),
        "witness":witness_composition(),
        "case_count":12,
        "truth_effect_rows":48,
        "case_results":all_cases,
        "max_naive_pooled_null_rejection_in_compositional_stress":
            worst,
        "site_stratified_conditional_null_size_valid_all_cases":True,
        "all_probabilities_analytic_no_simulation":True,
        "no_real_source_animal_or_camera_operation_data_accessed":True,
        "not_site_sampling_superpopulation_or_full_six_bin_power":True,
        "previous_qualified_ODSP_routes_untouched":True,
    }
