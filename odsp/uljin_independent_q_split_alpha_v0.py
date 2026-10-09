"""Independent four-cell detector calibration with simultaneous coverage.

Four independent reference trigger samples produce finite-sample
simultaneous Hoeffding bands for q_(rising/falling,early/late).
Allocate α_cal=.025 to the q family and α_test=.025 to the exact
Fisher test of the animal detection counts. Under the explicit
independent binomial calibration and Poisson observation assumptions,
union-bound false certification probability <=.05; it is NOT correct
to use .05 for BOTH intervals and biological test.

Synthetic worlds model one physical station and ONE prespecified
two-bin astronomical comparison. Do NOT apply to real EcoBank data
until independently original device-hour and q calibration records
are verified and source-specific pre-outcome contracts are frozen.
"""
from __future__ import annotations

from collections.abc import Mapping
from dataclasses import dataclass
from functools import lru_cache
import math
import numpy as np

from .uljin_detector_bias_robust_or_v0 import (
    FourCells, central_logweights, upper_tail,
    exact_lower_bound_count_OR,
)

METHOD="uljin-independent-binomial-detector-q-coverage-v0"
ALPHA_CAL=.025
ALPHA_TEST=.025
ALPHA_ALL=.05
N_REF=(50,200,1000,5000)
REPS=600
SEED=2026100914
TRUTHS=(
    ("null_no_bias",(.85,.85,.85,.85),(4.,4.,4.,4.),
     (40,40,40,40),1.),
    ("null_effort_only",(.85,.85,.85,.85),(4.,4.,8.,4.),
     (40,40,80,40),1.),
    ("null_detector_only",(.8,.8,.8,.4),(4.,4.,4.,4.),
     (80,80,160,80),1.),
    ("alternative_strong_encounter",(.85,.85,.85,.85),
     (4.,4.,4.,4.),(200,200,280,120),2.),
)


def _guard(plan:Mapping[str,object]) -> None:
    if not isinstance(plan,Mapping):
        raise ValueError("source-free independent-calibration contract missing")
    block=plan.get("combined_inference",{})
    mc=plan.get("monte_carlo",{})
    truths=plan.get("synthetic_truth_worlds",[])
    expected=[{
        "id":name,
        "reference_q":list(q),
        "device_hours":list(e),
        "fixed_margin_source_counts":list(c),
        "true_latent_OR":theta,
    } for name,q,e,c,theta in TRUTHS]
    if (
        plan.get("schema_version")!=1
        or plan.get("contract_id")!=METHOD
        or plan.get("status")!=
            "FROZEN_BEFORE_FIRST_CALIBRATION_AND_SEASONAL_INFERENCE_OUTCOME"
        or plan.get("parent_pr")!=247
        or plan.get("previous_first_result_ledger")!=
            "ULJIN_DETECTOR_BIAS_ROBUST_OR_V0_FIRST_RESULT_LEDGER.json"
        or plan.get("reference_trial_counts_per_cell")!=list(N_REF)
        or truths!=expected
        or block.get("overall_one_sided_alpha")!=ALPHA_ALL
        or block.get("calibration_joint_failure_budget")!=ALPHA_CAL
        or block.get("animal_count_exact_conditional_test_budget")!=ALPHA_TEST
        or mc.get("world_replicates_per_case")!=REPS
        or mc.get("root_seed")!=SEED
        or plan.get("claim_boundaries",{}).get(
           "source_free_synthetic_only") is not True
    ):
        raise ValueError("pre-result independent q coverage contract altered")


@dataclass(frozen=True)
class QBounds:
    lower:tuple[float,float,float,float]
    upper:tuple[float,float,float,float]
    opportunities:int
    successes:tuple[int,int,int,int]

    @property
    def detector_gamma_upper(self)->float:
        lo,hi=self.lower,self.upper
        if lo[0]<=0 or lo[3]<=0:
            return math.inf
        return hi[2]*hi[1]/(lo[0]*lo[3])

    def covers(self,truth:tuple[float,float,float,float])->bool:
        return all(a-1e-15<=q<=b+1e-15
                   for a,b,q in zip(self.lower,self.upper,truth))


def independent_hoeffding_bounds(
    successes:tuple[int,int,int,int],n:int,
    alpha_cal:float=ALPHA_CAL,
)->QBounds:
    if (type(n) is not int or n<1 or type(successes) is not tuple
        or len(successes)!=4 or any(type(x) is not int or not 0<=x<=n
                                     for x in successes)
        or alpha_cal!=ALPHA_CAL):
        raise ValueError("frozen four-cell independent calibration required")
    epsilon=math.sqrt(math.log(8/alpha_cal)/(2*n))
    lo=tuple(max(0.,x/n-epsilon) for x in successes)
    hi=tuple(min(1.,x/n+epsilon) for x in successes)
    return QBounds(lo,hi,n,successes)


def _valid_q(q:tuple[float,...])->None:
    if len(q)!=4 or any(
        isinstance(x,bool) or not isinstance(x,(float,int))
        or not math.isfinite(x) or x<=0 or x>1 for x in q
    ):
        raise ValueError("camera detection probability q must be (0,1]")


def true_detector_crossproduct(q:tuple[float,...])->float:
    _valid_q(q)
    return q[2]*q[1]/(q[0]*q[3])


@lru_cache(maxsize=128)
def _fixed_margins_logweights(counts:tuple[int,int,int,int]
                              )->tuple[int,np.ndarray]:
    original=FourCells(counts,(1.,)*4)
    lo,logw=central_logweights(original)
    logw.setflags(write=False)
    return lo,logw


def _noncentral_exact_pmf(
    counts:tuple[int,int,int,int],theta:float
)->tuple[int,np.ndarray]:
    if not math.isfinite(theta) or theta<=0:
        raise ValueError("conditional count OR must be finite positive")
    offset,w=_fixed_margins_logweights(counts)
    xx=np.arange(len(w),dtype=float)
    z=w+xx*math.log(theta)
    s=np.exp(z-np.max(z))
    p=s/s.sum()
    if abs(float(p.sum())-1)>1e-12 or np.any(p<0):
        raise ValueError("invalid noncentral Fisher distribution")
    return offset,p


def _tail_from_margins(
    source_counts:tuple[int,int,int,int], x:int,theta:float
)->float:
    off,p=_noncentral_exact_pmf(source_counts,theta)
    idx=x-off
    if not 0<=idx<len(p):
        raise ValueError("observed animal event count outside fixed margins")
    return max(0.,min(1.,float(p[idx:].sum())))


def _draw_site_four_count_table(
    rng:np.random.Generator,
    frozen_counts:tuple[int,int,int,int],
    theta_count:float,
)->tuple[int,int,int,int]:
    offset,p=_noncentral_exact_pmf(frozen_counts,theta_count)
    x=offset+int(rng.choice(len(p),p=p))
    a,b,c,d=frozen_counts
    N=a+b+c+d
    K=a+c
    D=c+d
    result=(K-x,N-K-D+x,x,D-x)
    if (min(result)<0 or result[0]+result[2]!=K
        or result[2]+result[3]!=D
        or sum(result)!=N):
        raise ValueError("fixed original site marginals not retained")
    return result


def _draw_one(
    truth_index:int,n_index:int,rep:int,
)->dict[str,object]:
    name,q,e,source,theta_latent=TRUTHS[truth_index]
    n=N_REF[n_index]
    rng=np.random.default_rng(np.random.SeedSequence(
        [SEED,truth_index,n_index,rep]))
    successes=tuple(int(x) for x in rng.binomial(n,np.array(q)))
    bounds=independent_hoeffding_bounds(successes,n)
    theta_e=FourCells(source,e).effort_OR
    theta_q=true_detector_crossproduct(q)
    observed=_draw_site_four_count_table(rng,source,
                                        theta_e*theta_q*theta_latent)
    x=observed[2]
    B=bounds.detector_gamma_upper
    # If an estimated q lower limit includes 0, no finite bound on
    # detector crossproduct is certified. Never divide by zero.
    if math.isfinite(B):
        p_robust=_tail_from_margins(source,x,theta_e*B)
        selected=p_robust<ALPHA_TEST
    else:
        p_robust=1.
        selected=False
    uncalibrated=_tail_from_margins(source,x,theta_e)
    return {
        "calibration_joint_q_coverage":bounds.covers(q),
        "calibration_gamma_upper":B,
        "detector_q_lower_zero_hold":not math.isfinite(B),
        "robust_joint_alpha_rejects_latent_OR_le_1":selected,
        "naive_detector_ignorant_5pct_rejection":uncalibrated<ALPHA_ALL,
    }


def frozen_joint_calibration_panel(plan:Mapping[str,object])->dict[str,object]:
    _guard(plan)
    cases=[]
    for wi,(name,q,e,source,truth_or) in enumerate(TRUTHS):
        theta_e=FourCells(source,e).effort_OR
        theta_q=true_detector_crossproduct(q)
        for ni,n in enumerate(N_REF):
            draws=[_draw_one(wi,ni,k) for k in range(REPS)]
            def frac(key:str)->float:
                return float(sum(bool(d[key]) for d in draws)/REPS)
            finiteB=sorted(d["calibration_gamma_upper"] for d in draws
                           if math.isfinite(d["calibration_gamma_upper"]))
            center=tuple(int(round(n*p)) for p in q)
            exemplary=independent_hoeffding_bounds(center,n)
            # Preplanned fixed artificial count table, independent reference
            # point demonstration; exact α_test lower bound is calculated
            # ONCE, not fitted on favorable calibration simulation worlds.
            lower_theta=exact_lower_bound_count_OR(
                FourCells(source,e),alpha=ALPHA_TEST)
            B=exemplary.detector_gamma_upper
            cases.append({
                "synthetic_truth":name,
                "true_latent_season_bin_OR":truth_or,
                "true_detector_crossproduct":theta_q,
                "true_effort_crossproduct":theta_e,
                "independent_reference_opportunities_per_4_cells":n,
                "replicates":REPS,
                "empirical_joint_q_band_coverage":frac(
                    "calibration_joint_q_coverage"),
                "fraction_with_insufficient_positive_q_lower_bounds":
                    frac("detector_q_lower_zero_hold"),
                "fraction_robustly_rejecting_latent_OR_le_1":
                    frac("robust_joint_alpha_rejects_latent_OR_le_1"),
                "naive_unadjusted_fisher_5pct_rejection_fraction":
                    frac("naive_detector_ignorant_5pct_rejection"),
                "median_finite_detector_gamma_upper":
                    (float(np.median(finiteB)) if finiteB else None),
                "predefined_rounded_expected_calibration_counts":
                    list(center),
                "illustrative_joint_detector_gamma_upper":
                    (B if math.isfinite(B) else None),
                "illustrative_synthetic_count_table_exact_97p5pct_lower_latent_OR":
                    (lower_theta/(theta_e*B) if math.isfinite(B) else 0.),
                "joint_calibration_coverage_analytic_guarantee":
                    1-ALPHA_CAL,
                "animal_exact_test_independent_budget":ALPHA_TEST,
                "unconditional_false_certification_alpha_bound":
                    ALPHA_CAL+ALPHA_TEST,
            })
    if (len(cases)!=len(TRUTHS)*len(N_REF)
        or not all(r["replicates"]==REPS for r in cases)
        or any(r["unconditional_false_certification_alpha_bound"]>ALPHA_ALL
               for r in cases)):
        raise ValueError("not all frozen independent q calibration cases completed")
    return {
        "schema_version":1,
        "method":METHOD,
        "status":"SOURCE_FREE_INDEPENDENT_Q_CALIBRATION_SPLIT_ALPHA_ONLY",
        "calibration_joint_error_budget":ALPHA_CAL,
        "animal_exact_test_error_budget":ALPHA_TEST,
        "guaranteed_total_false_certification_upper_bound":ALPHA_ALL,
        "guarantee_conditional_on_independence_and_model":True,
        "worlds_per_case":REPS,
        "case_count":len(cases),
        "all_precommitted_cases":cases,
        "empirical_monte_carlo_fraction_not_formal_size_proof":True,
        "uncalibrated_detector_efficiency_latent_activity_not_identifiable":True,
        "original_animal_events_or_reference_sensor_calibration_not_opened":True,
        "original_independent_device_hours_not_attested":True,
        "previous_qualified_ODSP_routes_unchanged":True,
    }
