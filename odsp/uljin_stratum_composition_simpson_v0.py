"""Source-free Simpson-composition stress test: pooled vs partially pooled
vs EXACT stratum-conditional phase-shape inference.

Each physical station contributes ONE active matched date-pair; the
original 41-pair/site roster is represented by an exact 41*6-cell/site
heldout score denominator (other 40 station-pairs contain no events).
This is a deliberately sparse SYNTHETIC adversary, not EcoBank evidence.

Within each site, null worlds have the same true six-bin phase profile
in spring and autumn, differing only by an overall branch rate.
Correlating that rate with site-specific early/late activity profiles
can create an aggregated branch-by-time interaction (Simpson mixing).
"""
from __future__ import annotations
import math
from typing import Mapping
import numpy as np

from .uljin_finite_sample_clock_alias_selection_v0 import (
    heldout_site_equal_gain, TRAIN_IDX, TEST_IDX, CELL_DENOMINATOR,
)

ID="uljin_stratum_specific_season_rate_simpson_v0"
SITES=82
PAIR_COUNT=41
BIN_COUNT=6
PERMS=99
WORLDS=100
SCALES=(0.1,1.2)
SEED=2026100823
EARLY=np.array([8.,1.,1.,1.,1.,1.])
LATE=np.array([1.,1.,1.,1.,1.,8.])
SCENARIOS=(
 ("homogeneous_null",1.,1.,np.zeros(6)),
 ("composition_confound_null",3.,1./3.,np.zeros(6)),
 ("true_within_stratum_shape",1.,1.,
  np.log(np.array([2.,1.5,1.,1.,2./3.,.5]))),
)
LAMBDAS=(.2,10.)
SHAPE_RIDGE=2.
INTERCEPT_RIDGE=1e-6


def verify_contract(plan:Mapping[str,object])->None:
    d=plan.get("synthetic_frame",{})
    m=plan.get("estimators",{})
    scenarios=plan.get("scenarios",[])
    if (
        plan.get("schema_version")!=1
        or plan.get("contract_id")!=ID
        or plan.get("stage")!="FROZEN_BEFORE_FIRST_SYNTHETIC_OUTCOME"
        or plan.get("parent_pr")!=237
        or plan.get("count_scales")!=list(SCALES)
        or plan.get("seed")!=SEED
        or plan.get("worlds_per_case")!=WORLDS
        or d.get("physical_sites")!=SITES
        or d.get("matched_dates_represented")!=PAIR_COUNT
        or d.get("one_active_matched_pair_per_site") is not True
        or plan.get("bin_baselines")!={"early":[8,1,1,1,1,1],
                                       "late":[1,1,1,1,1,8]}
        or len(scenarios)!=3
        or [s.get("id") for s in scenarios]!=[t[0] for t in SCENARIOS]
        or any(abs(float(s["early_branch_multiplier"])-float(t[1]))>1e-13
               or abs(float(s["late_branch_multiplier"])-float(t[2]))>1e-13
               or not np.allclose(s["shape_log_multipliers"],t[3],rtol=0,atol=1e-14)
               for s,t in zip(scenarios,SCENARIOS))
        or "lambda_u=0.2 and lambda_u=10" not in m.get("partial_pooling","")
        or "99 null draws" not in m.get("exact_conditioning","")
        or plan.get("hard_stops",{}).get("no_real_ungulate_events") is not True
    ):
        raise ValueError("frozen source-free Simpson panel contract altered")


def two_type_population_oracle()->dict[str,object]:
    """Constructive expectation: a within-type constant branch ratio
    becomes radically different bin ratios after mixing types.
    """
    across_rise=EARLY+LATE
    across_fall=3*EARLY+LATE/3
    ratios=across_fall/across_rise
    if not (ratios[0]>1 and ratios[-1]<1):
        raise ValueError("source-free Simpson counterexample invalid")
    return {
        "early_site_true_branch_rate_ratio":3.,
        "late_site_true_branch_rate_ratio":1./3.,
        "true_branch_by_bin_interaction_within_each_type":False,
        "pooled_first_bin_ratio":float(ratios[0]),
        "pooled_last_bin_ratio":float(ratios[-1]),
        "pooled_log_rate_ratio_first_minus_last":
            float(math.log(ratios[0]/ratios[-1])),
    }


def synthetic_world(scenario:int,scale:int,world:int)->np.ndarray:
    if not 0<=scenario<len(SCENARIOS) or not 0<=scale<len(SCALES) or not 0<=world<WORLDS:
        raise ValueError("invalid frozen scenario coordinates")
    _,ra,rb,shape=SCENARIOS[scenario]
    base=np.where((np.arange(SITES)%2==0)[:,None],EARLY,LATE)
    r=np.where(np.arange(SITES)%2==0,ra,rb)
    mean_a=SCALES[scale]*base
    mean_d=SCALES[scale]*base*r[:,None]*np.exp(shape)[None,:]
    rng=np.random.default_rng(np.random.SeedSequence([SEED,scenario,scale,world]))
    counts=np.stack([rng.poisson(mean_a),rng.poisson(mean_d)],axis=1)
    assert counts.shape==(SITES,2,BIN_COUNT)
    return counts.astype(np.int64)


def _partial_loglike(
    y:np.ndarray,n:np.ndarray,beta:np.ndarray,u:np.ndarray,lam_u:float,
)->float:
    eta=beta[None,:]+u[:,None]
    centered=beta-beta.mean()
    return float(np.sum(y*eta-n*np.logaddexp(0,eta))
         - .5*SHAPE_RIDGE*np.sum(centered**2)
         - .5*INTERCEPT_RIDGE*beta.mean()**2
         - .5*lam_u*np.sum(u*u))


def partially_pooled_training_fit(
    counts:np.ndarray,lambda_u:float
)->tuple[float,...]:
    """Penalized logistic logit p_fall(s,k)=beta_k+u_s.

    The u_s are pair-wide branch offsets; smaller positive lambda_u
    retains more within-pair heterogeneity. Global beta profile is an
    exploratory descriptive estimate only, not an alpha-calibrated test.
    """
    if (
        counts.shape!=(len(TRAIN_IDX),2,BIN_COUNT)
        or lambda_u not in LAMBDAS
    ):
        raise ValueError("incorrect fixed training support or shrinkage")
    y=counts[:,1,:].astype(float)
    n=counts.sum(axis=1).astype(float)
    nsites=len(TRAIN_IDX)
    beta=np.zeros(BIN_COUNT)
    u=np.zeros(nsites)
    centering=np.eye(BIN_COUNT)-np.ones((BIN_COUNT,BIN_COUNT))/BIN_COUNT
    for _ in range(100):
        eta=beta[None,:]+u[:,None]
        p=np.exp(-np.logaddexp(0.,-eta))
        residual=y-n*p
        w=n*p*(1.-p)
        beta_grad=residual.sum(axis=0)-SHAPE_RIDGE*(beta-beta.mean())
        beta_grad-=INTERCEPT_RIDGE*beta.mean()/BIN_COUNT
        u_grad=residual.sum(axis=1)-lambda_u*u
        beta_hess=np.diag(w.sum(axis=0))+SHAPE_RIDGE*centering
        beta_hess+=INTERCEPT_RIDGE*np.ones((BIN_COUNT,BIN_COUNT))/(BIN_COUNT**2)
        u_hess=w.sum(axis=1)+lambda_u
        cross=w.T
        schur=beta_hess-(cross/u_hess)@cross.T
        g=beta_grad-cross@(u_grad/u_hess)
        try:
            step_beta=np.linalg.solve(schur,g)
        except np.linalg.LinAlgError as e:
            raise ValueError("partial pooling Schur complement singular") from e
        step_u=(u_grad-cross.T@step_beta)/u_hess
        if max(np.max(abs(step_beta)),np.max(abs(step_u)))<1e-8:
            break
        old=_partial_loglike(y,n,beta,u,lambda_u)
        for backtrack in range(35):
            rate=0.5**backtrack
            b_new=np.clip(beta+rate*step_beta,-20.,20.)
            u_new=np.clip(u+rate*step_u,-20.,20.)
            objective=_partial_loglike(y,n,b_new,u_new,lambda_u)
            if objective>=old-1e-10:
                beta,u=b_new,u_new
                break
        else:
            raise ValueError("partial pool line search not converged")
    else:
        raise ValueError("partial pool optimizer iteration limit")
    return tuple(float(x) for x in beta)


def _conditional_components(test_counts:np.ndarray):
    """Condition on each heldout site×pair phase totals and season total."""
    if test_counts.shape!=(len(TEST_IDX),2,BIN_COUNT):
        raise ValueError("heldout sites have to be preserved exactly")
    m=test_counts.sum(axis=1)
    D=test_counts[:,1,:].sum(axis=1)
    M=m.sum(axis=1)
    informative=(M>=2)&(D>0)&(D<M)
    residual=np.zeros(BIN_COUNT)
    variance=np.zeros(BIN_COUNT)
    for counts,summer,n,yes in zip(m,D,M,informative):
        if not yes:continue
        p=counts/n
        variance+=summer*(n-summer)/(n-1)*p*(1.-p)
    return m,D,M,informative,variance


def conditional_permutation_test(
    test_counts:np.ndarray,rng:np.random.Generator
)->dict[str,object]:
    """Valid conditional Monte Carlo test of within-pair bin×branch shape.

    Under the null, conditional on each site-pair's six bin totals and
    falling branch count, the falling counts are multivariate
    hypergeometric. All site-pairs, even noninformative, are retained.
    """
    m,D,M,informative,var=_conditional_components(test_counts)
    expected=np.divide(D[:,None]*m,M[:,None],out=np.zeros_like(m,dtype=float),
                       where=M[:,None]>0)
    observed=(test_counts[:,1,:]-expected).sum(axis=0)
    usable=var>1e-12
    if not usable.any():
        return {"pvalue":1.,"rejected":False,"informative_strata":0,
                "permutation_variance_bins":0}
    def statistic(t):
        return float(np.sum((t[usable]**2)/var[usable]))
    obs=statistic(observed)
    extreme=0
    for _ in range(PERMS):
        simulated=np.zeros(BIN_COUNT,dtype=float)
        for bin_counts,fall,n,yes,mean_vector in zip(
            m,D,M,informative,expected
        ):
            if yes:
                sample=rng.multivariate_hypergeometric(
                    bin_counts,int(fall),method="marginals")
                simulated+=sample-mean_vector
        if statistic(simulated)>=obs-1e-12:
            extreme+=1
    p=(1+extreme)/(1+PERMS)
    return {
        "pvalue":float(p),
        "rejected":p<=.05,
        "informative_strata":int(informative.sum()),
        "permutation_variance_bins":int(usable.sum()),
    }


def evaluate_world(scenario:int,scale:int,world:int)->dict[str,object]:
    counts=synthetic_world(scenario,scale,world)
    gain=heldout_site_equal_gain(counts)
    beta_weak=partially_pooled_training_fit(counts[TRAIN_IDX],LAMBDAS[0])
    beta_strong=partially_pooled_training_fit(counts[TRAIN_IDX],LAMBDAS[1])
    perm_rng=np.random.default_rng(np.random.SeedSequence(
        [SEED,scenario,scale,world,191]))
    exact=conditional_permutation_test(counts[TEST_IDX],perm_rng)
    return {
        "pooled_gain":gain,
        "pooled_shape_selected":gain>0,
        "partial_weak_shape_range":max(beta_weak)-min(beta_weak),
        "partial_strong_shape_range":max(beta_strong)-min(beta_strong),
        "conditional_rejected":exact["rejected"],
        "informative_strata":exact["informative_strata"],
        "permutation_variance_bins":exact["permutation_variance_bins"],
    }


def run_panel(
    frozen:Mapping[str,object],*,_test_worlds:int|None=None,
)->dict[str,object]:
    verify_contract(frozen)
    w=WORLDS if _test_worlds is None else _test_worlds
    if type(w) is not int or not 1<=w<=WORLDS:
        raise ValueError("invalid simulation count")
    scenarios=[]
    for i,(scenario,*_) in enumerate(SCENARIOS):
        for j,scale in enumerate(SCALES):
            draws=[evaluate_world(i,j,k) for k in range(w)]
            def avg(key):
                return float(np.mean([v[key] for v in draws]))
            scenarios.append({
                "scenario":scenario,"count_scale":scale,
                "worlds":w,
                "pooled_positive_heldout_gain_fraction":avg("pooled_shape_selected"),
                "mean_pooled_heldout_gain_nats_per_original_cell":avg("pooled_gain"),
                "partial_weak_global_shape_range_mean":avg("partial_weak_shape_range"),
                "partial_strong_global_shape_range_mean":avg("partial_strong_shape_range"),
                "exact_conditional_rejection_fraction":avg("conditional_rejected"),
                "mean_informative_heldout_strata":avg("informative_strata"),
                "mean_conditional_variance_supported_bins":avg("permutation_variance_bins"),
            })
    return {
        "schema_version":1,"method":ID,
        "status":"SOURCE_FREE_COMPOSITION_CONFOUNDING_PANEL_UNQUALIFIED",
        "all_original_pair_ids_represented":PAIR_COUNT,
        "worlds_per_scenario":w,
        "population_oracle":two_type_population_oracle(),
        "scenarios":scenarios,
        "pooled_rule_not_a_formal_alpha_test":True,
        "partial_pool_fit_not_a_formal_alpha_test":True,
        "conditional_test_nominal_alpha":.05,
        "no_real_observations_or_uptime_opened":True,
        "no_qualified_ODSP_route_reclassified":True,
    }
