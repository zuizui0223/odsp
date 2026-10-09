"""Exact four-cell Clopper-Pearson versus Hoeffding detector calibration.

Source-free POST-PR248, before first CP outputs. Reuses EXACT parent animal
count tables, independent simulated camera reference q and α=.025+.025
familywise budget. Clopper-Pearson uses exact Binomial inversion with
α_cal/(2*4) at each one-sided tail, retaining simultaneous >=97.5%
four-cell coverage by Bonferroni. Does not claim a new theorem or
the coverage of actual source camera calibration.

The 16 fixed rounded-success examples are deterministic illustrations,
NOT sampled calibrations and NOT comparative Monte Carlo power.
"""
from __future__ import annotations

from functools import lru_cache
import math
from collections.abc import Mapping
import numpy as np

from .uljin_independent_q_split_alpha_v0 import (
    TRUTHS,N_REF,ALPHA_CAL,ALPHA_TEST,
    independent_hoeffding_bounds,QBounds,
)
from .uljin_detector_bias_robust_or_v0 import (
    FourCells, upper_tail,exact_lower_bound_count_OR,
)

ID="uljin_clopper_pearson_vs_hoeffding_four_cell_detector_v0"
TAIL_ALPHA=ALPHA_CAL/(2*4)
BOUNDS_ITERATIONS=52


def _verify(plan:Mapping[str,object],prior:Mapping[str,object])->None:
    if (
        not isinstance(plan,Mapping)
        or plan.get("schema_version")!=1
        or plan.get("contract_id")!=ID
        or plan.get("stage")!=
            "FROZEN_POST_HOEFFDING_RESULTS_BEFORE_CP_FIRST_OUTPUT"
        or plan.get("parent_pr")!=248
        or plan.get("calibration_alpha_joint")!=ALPHA_CAL
        or plan.get("animals_exact_test_alpha")!=ALPHA_TEST
        or plan.get("overall_alpha")!=ALPHA_CAL+ALPHA_TEST
        or plan.get("source_access")!={
            "EcoBank_original_zip_verified":False,
            "original_camera_q_reference_trials_measured":False,
            "original_independent_hourly_uptime_verified":False,
            "animal_events_opened":False,
        }
        or prior.get("record_type")!=
            "FIRST_FROZEN_INDEPENDENT_DETECTOR_Q_SPLIT_ALPHA_V0_TERMINAL_RESULT"
        or prior.get("first_complete_ci_run")!=37888152647
        or len(prior.get("worlds",[]))!=4
    ):
        raise ValueError("frozen post-Hoeffding exact CP method/provenance changed")


@lru_cache(maxsize=6)
def _binom_log_choose(n:int)->np.ndarray:
    if type(n) is not int or not 1<=n<=5000:
        raise ValueError("n out of predeclared detector calibration support")
    L=math.lgamma(n+1)
    out=np.fromiter((
        L-math.lgamma(k+1)-math.lgamma(n-k+1) for k in range(n+1)
    ),dtype=float,count=n+1)
    out.setflags(write=False)
    return out


def _binomial_tails(
    n:int,k:int,p:float,log_choose:np.ndarray,
)->tuple[float,float]:
    """P_p(X>=k) and P_p(X<=k), with exact Binomial weights."""
    if (type(k) is not int or not 0<=k<=n
        or not isinstance(p,(int,float)) or isinstance(p,bool)
        or not math.isfinite(p) or not 0<=p<=1
        or log_choose.shape!=(n+1,)):
        raise ValueError("bad binomial tail request")
    if p==0:
        return (1. if k==0 else 0.),1.
    if p==1:
        return 1.,(1. if k==n else 0.)
    xs=np.arange(n+1,dtype=float)
    z=log_choose+xs*math.log(p)+(n-xs)*math.log1p(-p)
    a=np.exp(z-np.max(z))
    a/=a.sum()
    # Both tails inclusive of observation k; their sum=1+P(X=k).
    return float(a[k:].sum()),float(a[:k+1].sum())


def exact_clopper_pearson(
    successes:int,n:int,
)->tuple[float,float,float,float]:
    """Single-cell two-sided CP with Bonferroni 4-cell confidence.

    Return qL,qU,lower-tail residual,upper-tail residual.
    """
    if type(successes) is not int or type(n) is not int or not 0<=successes<=n:
        raise ValueError("successes exceed independent reference opportunities")
    logc=_binom_log_choose(n)
    if successes==0:
        lower=0.
        lower_residual=0.
    else:
        lo,hi=0.,1.
        for _ in range(BOUNDS_ITERATIONS):
            mid=(lo+hi)*.5
            surviving,_=_binomial_tails(n,successes,mid,logc)
            if surviving>=TAIL_ALPHA:
                hi=mid
            else:
                lo=mid
        lower=hi
        lower_residual=abs(
            _binomial_tails(n,successes,lower,logc)[0]-TAIL_ALPHA
        )
    if successes==n:
        upper=1.
        upper_residual=0.
    else:
        lo,hi=0.,1.
        for _ in range(BOUNDS_ITERATIONS):
            mid=(lo+hi)*.5
            _,cdf=_binomial_tails(n,successes,mid,logc)
            if cdf>=TAIL_ALPHA:
                lo=mid
            else:
                hi=mid
        upper=hi
        upper_residual=abs(
            _binomial_tails(n,successes,upper,logc)[1]-TAIL_ALPHA
        )
    if (not 0<=lower<=upper<=1
        or max(lower_residual,upper_residual)>5e-8):
        raise ValueError("exact CP tail inversion numerically failed")
    return lower,upper,lower_residual,upper_residual


def four_cell_cp_bounds(
    counts:tuple[int,int,int,int],n:int,
)->tuple[QBounds,float]:
    if len(counts)!=4:
        raise ValueError("four reference q calibration cells required")
    values=[exact_clopper_pearson(x,n) for x in counts]
    return (
        QBounds(tuple(r[0] for r in values),
                tuple(r[1] for r in values),n,counts),
        max(max(r[2],r[3]) for r in values)
    )


def compare_all_fixed_reference_calibrations(
    plan:Mapping[str,object],prior:Mapping[str,object]
)->dict[str,object]:
    _verify(plan,prior)
    scenarios=[]
    for name,q,effort,counts,truth_latent in TRUTHS:
        observed=FourCells(counts,effort)
        exact_lower=exact_lower_bound_count_OR(
            observed,alpha=ALPHA_TEST
        )
        for n in N_REF:
            successes=tuple(int(round(n*p)) for p in q)
            cp,residual=four_cell_cp_bounds(successes,n)
            ho=independent_hoeffding_bounds(successes,n)
            def account(b:QBounds)->dict[str,object]:
                B=b.detector_gamma_upper
                hold=not math.isfinite(B)
                if hold:
                    p=1.
                    lower=0.
                else:
                    p=upper_tail(observed,observed.effort_OR*B)
                    lower=exact_lower/(observed.effort_OR*B)
                return {
                    "reference_detector_gamma_max":
                        (B if not hold else None),
                    "HOLD_no_positive_detector_lower":hold,
                    "robust_one_sided_exact_animal_null_p":p,
                    "one_sided_97p5pct_lower_latent_encounter_OR":lower,
                    "certifies_encounter_OR_above_one":bool(
                        not hold and p<ALPHA_TEST
                    ),
                    "q_cell_lower":list(b.lower),
                    "q_cell_upper":list(b.upper),
                    "four_q_reference_truth_covered_in_illustrative_sample":
                        b.covers(q),
                }
            cases={
                "synthetic_world":name,
                "true_latent_encounter_OR":truth_latent,
                "reference_binomial_opportunities_per_cell":n,
                "rounded_representative_q_successes":list(successes),
                "fixed_synthetic_animal_count_table":list(counts),
                "original_known_device_effort_hours":list(effort),
                "exact_CP":account(cp),
                "Hoeffding":account(ho),
                "max_CP_tail_inversion_residual":residual,
                "both_methods_same_external_calibration_alpha":ALPHA_CAL,
                "both_methods_same_animal_test_alpha":ALPHA_TEST,
            }
            if (not cases["exact_CP"]["four_q_reference_truth_covered_in_illustrative_sample"]
                or not cases["Hoeffding"]["four_q_reference_truth_covered_in_illustrative_sample"]):
                raise ValueError("pre-fixed representative q sample unexpectedly excludes q truth")
            scenarios.append(cases)
    if len(scenarios)!=16:
        raise ValueError("all fixed exact CP vs Hoeffding sample cases required")
    def first_threshold(world:str,method:str)->int|None:
        for x in scenarios:
            if (x["synthetic_world"]==world
                and x[method]["certifies_encounter_OR_above_one"]):
                return x["reference_binomial_opportunities_per_cell"]
        return None
    targets={m:first_threshold("alternative_strong_encounter",m)
             for m in ("exact_CP","Hoeffding")}
    return {
        "schema_version":1,
        "method":ID,
        "status":"SOURCE_FREE_EXACT_CP_VS_HOEFFDING_JOINT_Q_DESIGN_ONLY",
        "all_16_fixed_calibration_cases":scenarios,
        "cp_one_sided_binomial_tail_spend":TAIL_ALPHA,
        "four_cell_joint_detector_q_coverage_guaranteed_by_union_bound":1-ALPHA_CAL,
        "independent_exact_animal_test_alpha":ALPHA_TEST,
        "total_combined_false_certification_error_upper_bound":
            ALPHA_CAL+ALPHA_TEST,
        "strong_animal_effect_first_certifying_reference_n_per_cell_on_frozen_grid":
            targets,
        "no_monte_carlo_power_or_sample_cost_calculated":True,
        "representative_rounding_not_a_stochastic_calibration_observation":True,
        "real_ecobank_reference_or_wildlife_records_opened":False,
        "prior_qualified_ODSP_routes_unchanged":True
    }
