"""Exact conditional 2x2 sample size under known balanced margins.

This does NOT use original wildlife counts. For one artificial physical
station and one date-pair, rising and falling each contribute exactly n
detections across predeclared EARLY/LATE solar bins. Each solar-bin
column also has exactly n detections. With no exposure/detection
crossproduct confounding, the upper-tail conditional odds-ratio test is
an exact noncentral hypergeometric (one-sided Fisher) procedure.

For theta>0 and X=falling-early in the 2x2 table, the conditional law is
   P_theta(X=x) proportional to C(n,x)^2 theta^x, x=0..n.
The null is theta=1. Conditioning removes the row and column nuisance
margins in this artificial design. The result is a sampling power curve,
not a posterior, a full six-bin diel test, or latent activity inference.
"""
from __future__ import annotations

import math
from collections.abc import Mapping
import numpy as np

ID="uljin_balanced_exact_two_bin_or_power_v0"
THETA=(1.,1.5,2.,3.)
GRID=(10,20,40,80,160,320,640)
ALPHA=.05
MIN_N=5
MAX_N=640
POWER_TARGET=.8


def _verify(plan:Mapping[str,object])->None:
    t=plan.get("test",{})
    s=plan.get("scan_n_per_season",{})
    if (
        not isinstance(plan,Mapping)
        or plan.get("schema_version")!=1
        or plan.get("contract_id")!=ID
        or plan.get("stage")!=
           "FROZEN_SOURCE_FREE_BEFORE_FIRST_EXACT_POWER_CALCULATION"
        or plan.get("parent_pr")!=241
        or plan.get("null_odds_ratio")!=1
        or plan.get("true_odds_ratio_scenarios")!=list(THETA)
        or plan.get("n_per_season_grid")!=list(GRID)
        or t.get("alpha")!=ALPHA
        or t.get("alternative")!="greater"
        or t.get("critical_value_rule")!=
            "smallest integer c with P_theta=1(X>=c)<=alpha; none means cannot reject"
        or s!={"min":MIN_N,"max":MAX_N,"integer_step":1,
                "target_power":POWER_TARGET,
                "report_first_crossing_and_sustained_from_n_through_max":True}
        or plan.get("scope_restrictions",{}).get(
            "hypothetical_balanced_fixed_margins_not_observed") is not True
        or plan.get("scope_restrictions",{}).get(
            "detection_probability_odds_crossproduct_assumed_one") is not True
    ):
        raise ValueError("frozen exact conditional odds-ratio power contract altered")


def _conditional_log_combinations(n:int)->np.ndarray:
    if type(n) is not int or n<1:
        raise ValueError("positive integer margin n required")
    return np.array([
        2.*(math.lgamma(n+1)-math.lgamma(x+1)-math.lgamma(n-x+1))
        for x in range(n+1)
    ],dtype=float)


def exact_noncentral_pmf(n:int,theta:float,
                         precomputed:np.ndarray|None=None)->np.ndarray:
    if (not isinstance(theta,(int,float)) or isinstance(theta,bool)
        or not math.isfinite(theta) or theta<=0):
        raise ValueError("positive finite odds ratio required")
    lc=_conditional_log_combinations(n) if precomputed is None else precomputed
    if lc.shape!=(n+1,) or not np.isfinite(lc).all():
        raise ValueError("incorrect exact log-combination support")
    z=lc+np.arange(n+1)*math.log(float(theta))
    mass=np.exp(z-z.max())
    prob=mass/mass.sum()
    if not math.isfinite(float(prob.sum())) or abs(prob.sum()-1.)>1e-12:
        raise ValueError("conditional probabilities did not normalize")
    return prob


def first_exact_upper_tail_rejection_threshold(
    null_pmf:np.ndarray,alpha:float=ALPHA
)->tuple[int,float]:
    if (null_pmf.ndim!=1 or len(null_pmf)<2
        or np.any(null_pmf<0) or not np.isfinite(null_pmf).all()
        or abs(null_pmf.sum()-1)>1e-10
        or not 0<alpha<1):
        raise ValueError("null distribution and alpha invalid")
    upper=np.cumsum(null_pmf[::-1])[::-1]
    hits=np.flatnonzero(upper<=alpha+1e-15)
    if len(hits)==0:
        return len(null_pmf),0.
    c=int(hits[0])
    return c,float(upper[c])


def conditional_power_at_n(n:int, theta:float)->dict[str,object]:
    lc=_conditional_log_combinations(n)
    null=exact_noncentral_pmf(n,1.,lc)
    c,size=first_exact_upper_tail_rejection_threshold(null)
    p=exact_noncentral_pmf(n,theta,lc)
    power=float(p[c:].sum())
    if theta==1 and abs(power-size)>1e-12:
        raise ValueError("null rejection size not recovered exactly")
    if size>ALPHA+1e-12 or not -1e-12<=power<=1+1e-12:
        raise ValueError("exact test invalid")
    return {"n_per_branch_and_per_phase_bin_margin":n,
            "total_two_bin_detected_events":2*n,
            "true_observed_rate_OR":theta,
            "smallest_upper_tail_rejection_count":c if c<=n else None,
            "exact_conditional_null_rejection_size":size,
            "exact_conditional_power":power}


def frozen_two_bin_exact_power_panel(plan:Mapping[str,object])->dict[str,object]:
    _verify(plan)
    grid=[]
    first={theta:None for theta in THETA}
    sustained={theta:None for theta in THETA}
    successes={theta:[] for theta in THETA}
    exact_sizes=[]
    for n in range(MIN_N,MAX_N+1):
        lc=_conditional_log_combinations(n)
        null=exact_noncentral_pmf(n,1.,lc)
        c,size=first_exact_upper_tail_rejection_threshold(null)
        exact_sizes.append(size)
        powers={}
        for theta in THETA:
            p=exact_noncentral_pmf(n,theta,lc)
            value=float(p[c:].sum())
            if theta==1. and abs(size-value)>1e-12:
                raise ValueError("exact null size/conditional power mismatch")
            if value<-1e-12 or value>1+1e-12:
                raise ValueError("power probability outside unit interval")
            powers[theta]=value
            if theta>1 and value>=POWER_TARGET:
                if first[theta] is None:
                    first[theta]=n
                successes[theta].append(n)
        if not all(powers[a]<=powers[b]+1e-12
                   for a,b in zip(THETA[:-1],THETA[1:])):
            raise ValueError("true-OR noncentral stochastic ordering violated")
        if size>ALPHA+1e-12:
            raise ValueError("one-sided Fisher conditional null size over alpha")
        if n in GRID:
            grid.extend({
                "n_per_season":n,
                "total_events_in_two_bins":2*n,
                "true_OR":theta,
                "rejection_early_count_threshold":c if c<=n else None,
                "conditional_size_under_null":size,
                "power":powers[theta],
            } for theta in THETA)
    # Because power need not be monotonic in n for a discrete exact test,
    # identify the first n and also an n from which all larger pre-frozen
    # scanned designs keep >=80% power.
    for theta in THETA:
        if theta==1.:
            continue
        all_good=True
        for n in range(MAX_N,MIN_N-1,-1):
            if n not in successes[theta]:
                all_good=False
            if all_good:
                sustained[theta]=n
    if (len(grid)!=len(GRID)*len(THETA)
        or any(first[t] is None for t in THETA if t>1)
        or any(sustained[t] is None for t in THETA if t>1)):
        raise ValueError("pre-frozen power scan incomplete or target not supported")
    return {
        "schema_version":1,
        "method":ID,
        "status":"SOURCE_FREE_EXACT_CONDITIONAL_SAMPLE_SIZE_ONLY",
        "alpha_one_sided":ALPHA,
        "target_conditional_power":POWER_TARGET,
        "scanned_n_per_season":[MIN_N,MAX_N],
        "all_n_null_size_at_most_alpha":True,
        "largest_exact_null_rejection_size":max(exact_sizes),
        "minimum_n_per_season_at_first_80_percent_power":{
            str(t):first[t] for t in THETA if t>1},
        "minimum_n_per_season_sustained_80_percent_through_640":{
            str(t):sustained[t] for t in THETA if t>1},
        "grid":grid,
        "equal_exposure_and_detection_crossproduct_assumed":True,
        "only_one_station_pair_and_preselected_two_bins":True,
        "multiple_bin_or_species_search_not_calibrated":True,
        "published_yearly_ungulate_events_not_used_as_cell_counts":True,
        "real_event_or_device_operation_rows_read":False,
        "ecological_activity_rate_identified":False,
        "qualified_ODSP_route_modified":False,
    }
