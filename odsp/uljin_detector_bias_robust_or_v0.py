"""Within-site detector-efficiency sensitivity for a seasonal two-bin contrast.

Pure source-free mathematical evaluation. Let observed event counts be
rising_early=a, rising_late=b, falling_early=c, falling_late=d, with
independently logged operating hours E and unknown detection sensitivity q.

Independent Poisson cell means satisfy mu=E * latent_encounter * q,
so observed count-rate crossproduct theta_count equals
theta_E * theta_latent * theta_q. After conditioning on EXACTLY the
observed season and bin totals, X=falling_early follows a Fisher
noncentral hypergeometric law parameterized by theta_count.

For a detector crossproduct theta_q <= B and null latent encounter
OR <= 1, the largest null noncentrality is theta_E * B. The
nonrandomized one-sided exact upper tail calculated there provides a
size-controlled robust test. Inverting that tail gives an exact
one-sided lower confidence bound on the latent OR *only if* the
external detector bound is certified and device-hours are verified.

This is not proof of latent behavior, photoperiod memory, causal season
history, detector response independence, or real source eligibility.
"""
from __future__ import annotations

from collections.abc import Mapping
from math import lgamma, log, exp, isfinite, inf
from dataclasses import dataclass
import numpy as np

ID="uljin_detector_bias_robust_within_site_seasonal_OR_v0"
ALPHA=.05
BS=(1.,1.25,1.5,2.,3.)
TABLES=(
 ("no_season_shift",(40,40,40,40),(4.,4.,4.,4.)),
 ("weak_shift",(80,80,100,60),(4.,4.,4.,4.)),
 ("strong_shift",(200,200,280,120),(4.,4.,4.,4.)),
 ("unequal_effort_only",(40,40,80,40),(4.,4.,8.,4.)),
 ("seasonal_detector_only",(80,80,160,80),(4.,4.,4.,4.)),
)
CALIBRATIONS=(
 ("narrow_q_each_0p9_to_1",(.9,.9,.9,.9),(1.,1.,1.,1.)),
 ("asymmetric_q_intervals",(.8,.8,.85,.75),(.95,.95,.98,.9)),
)


def guard_contract(plan:Mapping[str,object])->None:
    cases=plan.get("source_free_tables",[])
    q=plan.get("hypothetical_independent_calibration",[])
    frozen_cases=[
       {"id":name,"counts":list(counts),"operating_hours":list(hrs)}
       for name,counts,hrs in TABLES
    ]
    frozen_q=[
       {"id":name,"q_cell_lower":list(lo),"q_cell_upper":list(hi)}
       for name,lo,hi in CALIBRATIONS
    ]
    if (
        not isinstance(plan,Mapping)
        or plan.get("schema_version")!=1
        or plan.get("contract_id")!=ID
        or plan.get("stage")!=
            "PRE_OUTCOME_FROZEN_SOURCE_FREE_TWO_BIN_DETECTOR_SENSITIVITY"
        or plan.get("parent_pr")!=246
        or plan.get("parent_exact_tests")!=[242,243]
        or plan.get("index_order")!=[
            "rising_early","rising_late","falling_early","falling_late"]
        or cases!=frozen_cases
        or plan.get("detector_crossproduct_max_B")!=list(BS)
        or q!=frozen_q
        or plan.get("alpha_one_sided")!=ALPHA
        or plan.get("source_state")!={
            "ecobank_v1p1_archive_verified":False,
            "independent_hourly_uptime_verified":False,
            "independent_detector_calibration_verified":False,
            "real_animal_detection_events_read":False,
        }
    ):
        raise ValueError("frozen source-free detector sensitivity contract altered")


@dataclass(frozen=True)
class FourCells:
    counts:tuple[int,int,int,int]
    operating_hours:tuple[float,float,float,float]

    def __post_init__(self):
        if (
            len(self.counts)!=4 or len(self.operating_hours)!=4
            or any(type(x) is not int or x<0 for x in self.counts)
            or any(isinstance(e,bool) or not isinstance(e,(float,int))
                   or not isfinite(e) or e<=0 for e in self.operating_hours)
        ):
            raise ValueError("four nonnegative count cells and four positive exposure cells required")

    @property
    def effort_OR(self)->float:
        a,b,c,d=self.operating_hours
        return c*b/(a*d)

    @property
    def observed_count_OR(self)->float:
        a,b,c,d=self.counts
        if a*d==0:
            return inf if b*c>0 else float("nan")
        return c*b/(a*d)

    @property
    def observed_effort_adjusted_OR(self)->float:
        return self.observed_count_OR/self.effort_OR

    @property
    def margins(self)->tuple[int,int,int]:
        a,b,c,d=self.counts
        return a+b+c+d,a+c,c+d


def _choose_log(n:int,k:int)->float:
    if k<0 or k>n:
        return -inf
    return lgamma(n+1)-lgamma(k+1)-lgamma(n-k+1)


def central_logweights(table:FourCells)->tuple[int,np.ndarray]:
    N,K,D=table.margins
    lo=max(0,K+D-N)
    hi=min(K,D)
    values=np.array([
        _choose_log(K,x)+_choose_log(N-K,D-x)
        for x in range(lo,hi+1)],dtype=float)
    if len(values)==0 or not np.isfinite(values).all():
        raise ValueError("no valid conditional count support")
    return lo,values


def conditional_nchypergeom(table:FourCells,theta:float
                            )->tuple[int,np.ndarray]:
    if not isinstance(theta,(float,int)) or isinstance(theta,bool) or not isfinite(theta) or theta<=0:
        raise ValueError("conditional count OR must be finite positive")
    lo,lw=central_logweights(table)
    xs=np.arange(lo,lo+len(lw),dtype=float)
    z=lw+xs*log(theta)
    p=np.exp(z-z.max())
    p/=p.sum()
    if not np.isfinite(p).all() or abs(p.sum()-1)>1e-11:
        raise ValueError("conditional probability normalization failed")
    return lo,p


def upper_tail(table:FourCells,theta:float)->float:
    lo,p=conditional_nchypergeom(table,theta)
    observed=table.counts[2]
    if not lo<=observed<lo+len(p):
        raise ValueError("observed falling/early count outside conditional support")
    raw=float(p[observed-lo:].sum())
    if not -1e-12<=raw<=1+1e-12:
        raise ValueError("noncentral exact tail invalid")
    return min(1.,max(0.,raw))


def exact_lower_bound_count_OR(table:FourCells,alpha:float=ALPHA)->float:
    """Nonrandomized exact one-sided lower confidence limit for OR.

    One-sided test H0 theta<=theta0 rejects for P_theta0(X>=x)<alpha.
    At the inverted lower limit, exact right-tail = alpha. If x is
    conditional minimum, the lower limit is zero (no evidence).
    """
    if not 0<alpha<1:
        raise ValueError("invalid one-sided alpha")
    N,K,D=table.margins
    low=max(0,K+D-N)
    if table.counts[2]==low:
        return 0.
    # At tiny theta, P(X>=observed) -> 0; at huge theta it -> 1.
    low_log=-48.
    hi_log=48.
    if upper_tail(table,exp(low_log))>alpha+1e-13:
        raise ValueError("lower search bracket unsupported")
    if upper_tail(table,exp(hi_log))<alpha-1e-13:
        raise ValueError("upper search bracket unsupported")
    for _ in range(110):
        m=(low_log+hi_log)/2
        if upper_tail(table,exp(m))>=alpha:
            hi_log=m
        else:
            low_log=m
    lower=exp(hi_log)
    if abs(upper_tail(table,lower)-alpha)>1e-10:
        raise ValueError("exact inverted lower limit unstable")
    return lower


def detector_gamma_interval(
    lower:tuple[float,float,float,float],
    upper:tuple[float,float,float,float],
)->tuple[float,float]:
    """External SIMULTANEOUS interval for detector q, not uncalibrated QA."""
    if len(lower)!=4 or len(upper)!=4 or any(
        not isinstance(a,(float,int)) or isinstance(a,bool)
        or not isinstance(b,(float,int)) or isinstance(b,bool)
        or not isfinite(a) or not isfinite(b) or not 0<a<=b<=1
        for a,b in zip(lower,upper)
    ):
        raise ValueError("external detector bounds require joint positive calibration intervals")
    # index rising_early, rising_late, falling_early, falling_late
    gamma_min=lower[2]*lower[1]/(upper[0]*upper[3])
    gamma_max=upper[2]*upper[1]/(lower[0]*lower[3])
    return gamma_min,gamma_max


def evaluate_frozen_detector_sensitivity(
    plan:Mapping[str,object]
)->dict[str,object]:
    guard_contract(plan)
    cases=[]
    for name,counts,hrs in TABLES:
        t=FourCells(counts,hrs)
        point=t.observed_effort_adjusted_OR
        lower_count=exact_lower_bound_count_OR(t)
        individual=[]
        previous_p=-1.
        previous_lower=inf
        for B in BS:
            adjusted_null=t.effort_OR*B
            p=upper_tail(t,adjusted_null)
            lower_latent=lower_count/adjusted_null
            if p+1e-12<previous_p or lower_latent>previous_lower+1e-12:
                raise ValueError("sensitivity must become weaker as detector bias cap increases")
            previous_p,previous_lower=p,lower_latent
            individual.append({
                "detector_crossproduct_max_B":B,
                "robust_one_sided_exact_p_for_latent_OR_le_1":p,
                "one_sided_95pct_lower_latent_encounter_OR":lower_latent,
                "can_reject_latent_OR_le_1_given_calibrated_B":
                    p<=ALPHA+1e-14,
            })
        calibration=[]
        for label,lo,hi in CALIBRATIONS:
            qlo,qhi=detector_gamma_interval(lo,hi)
            calibration.append({
                "hypothetical_joint_detector_calibration_id":label,
                "permitted_detector_gamma_min":qlo,
                "permitted_detector_gamma_max":qhi,
                "observed_point_latent_OR_identification_interval":[point/qhi,point/qlo],
                "one_sided_95pct_lower_latent_OR_under_joint_calibration":
                    lower_count/(t.effort_OR*qhi),
                "robust_one_sided_exact_p":upper_tail(t,t.effort_OR*qhi),
            })
        cases.append({
            "synthetic_table_id":name,
            "observed_rising_early_late_falling_early_late_counts":list(counts),
            "known_operating_hours":list(hrs),
            "raw_observed_count_OR":t.observed_count_OR,
            "device_hour_exposure_OR":t.effort_OR,
            "effort_adjusted_observed_rate_OR":point,
            "one_sided_95pct_lower_observed_count_OR":lower_count,
            "detector_cap_sensitivity_grid":individual,
            "two_hypothetical_joint_calibration_cases":calibration,
            "unrestricted_detector_response_latent_OR_lower_bound":0.,
            "uncalibrated_detector_sensitivity_real_ecological_conclusion":"HOLD",
        })
    if len(cases)!=5 or any(len(x["detector_cap_sensitivity_grid"])!=5
         or len(x["two_hypothetical_joint_calibration_cases"])!=2
         for x in cases):
        raise ValueError("pre-registered sensitivity scenario count changed")
    effort=next(x for x in cases if x["synthetic_table_id"]=="unequal_effort_only")
    if (abs(effort["raw_observed_count_OR"]-2)>1e-12
        or abs(effort["effort_adjusted_observed_rate_OR"]-1)>1e-12):
        raise ValueError("effort-only negative control unexpectedly fails")
    return {
        "schema_version":1,
        "method":ID,
        "status":"SOURCE_FREE_EXACT_DETECTION_BIAS_SENSITIVITY_NOT_ECOLOGICAL_INFERENCE",
        "all_five_precommitted_tables":cases,
        "nominal_one_sided_alpha":ALPHA,
        "all_calibration_B_values":list(BS),
        "uncalibrated_detection_crossproduct_unbounded":True,
        "true_ungulate_behavior_or_photo_trigger_efficiency_estimated":False,
        "source_original_device_hours_verified":False,
        "source_original_ecobank_event_rows_opened":False,
        "original_qualified_ODSP_routes_reclassified":False,
    }
