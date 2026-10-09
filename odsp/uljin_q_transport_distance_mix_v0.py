"""Source-free camera detector q transport across passage-distance composition.

A camera can be 90% sensitive to NEAR passages and 30% to FAR passages
at every season×solar bin, yet a changing mix of passage distances
creates an apparent seasonal detected-time odds ratio. Detector q from
a reference mixture cannot be substituted for true animal opportunity
mixtures without transport weights.

Compare an intentionally invalid "reference-mixture-only" detector
calibration to a 12-cell simultaneous externally calibrated
8 q(distance,branch,bin)+4 target distance-mixing w(branch,bin)
confidence envelope. Alpha budgets .0125+.0125+.025 = .05. The
target-standardized q effective interval optimizes over q and w
confidence endpoint corners, never refits wildlife outcomes.

One synthetic site/date pair, prechosen 2 phase bins, original 41
astronomical dates remain untouched and genuine EcoBank source absent.
"""
from __future__ import annotations

from collections.abc import Mapping
import math
import numpy as np

from .uljin_independent_q_split_alpha_v0 import (
    _draw_site_four_count_table,_tail_from_margins
)
from .uljin_detector_bias_robust_or_v0 import FourCells

try:
    from scipy.special import betaincinv
except ImportError as exc:
    raise ImportError("optional SciPy required by dedicated q-transport workflow") from exc

METHOD="uljin_q_transport_two_distance_strata_v0"
ALPHA_Q=.0125
ALPHA_W=.0125
ALPHA_TEST=.025
NS=(50,200,1000)
REPS=200
SEED=2026100916
NEAR=(.9,)*4
FAR=(.3,)*4
WREF=(.5,)*4
WORLDS=(
 ("null_same_distance_mix",1.,(.5,.5,.5,.5),(80,80,80,80)),
 ("null_mixing_confounded",1.,(.2,.8,.8,.2),(80,80,80,80)),
 ("null_reverse_mixing",1.,(.8,.2,.2,.8),(80,80,80,80)),
 ("positive_encounter_with_mixing",2.,(.2,.8,.8,.2),(200,200,200,200))
)


def guard(plan:Mapping[str,object])->None:
    if (
        not isinstance(plan,Mapping)
        or plan.get("schema_version")!=1
        or plan.get("contract_id")!=METHOD
        or plan.get("status")!="FROZEN_AFTER_PARENT_Q_RESULTS_BEFORE_FIRST_TRANSPORT_OUTCOME"
        or plan.get("frozen_axes",{}).get("season_phase")!=[
            "rising_early","rising_late","falling_early","falling_late"]
        or plan.get("q_truth")!={"near":list(NEAR),"far":list(FAR)}
        or plan.get("reference_distance_mix")!=list(WREF)
        or plan.get("source_free_sample_sizes_per_cell")!=list(NS)
        or plan.get("synthetic_monte_carlo",{}).get("replicates_per_world_n")!=REPS
        or plan.get("synthetic_monte_carlo",{}).get("seed")!=SEED
        or [(w.get("id"),w.get("true_latent_encounter_OR"),
             tuple(w.get("target_near_mix",[])),
             tuple(w.get("artificial_conditional_margins_counts",[])))
            for w in plan.get("worlds",[])]!=list(WORLDS)
        or plan.get("methods",{}).get("calibration_joint_alpha") is not None
    ):
        raise ValueError("frozen distance-composition calibration contract changed")


def q_effective(
    near:tuple[float,...],far:tuple[float,...],
    mix:tuple[float,...]
)->np.ndarray:
    if not (len(near)==len(far)==len(mix)==4):
        raise ValueError("four season/phase cells required")
    a,b,w=map(lambda x:np.asarray(x,dtype=float),(near,far,mix))
    if (np.any(a<=0) or np.any(b<=0) or np.any(a>1) or np.any(b>1)
        or np.any(w<0) or np.any(w>1)):
        raise ValueError("invalid strata detector q or independent opportunity mix")
    return w*a+(1.-w)*b


def detector_crossproduct(q:np.ndarray)->float:
    if q.shape!=(4,) or np.any(q<=0):
        raise ValueError("four strictly positive detection probabilities required")
    return float(q[2]*q[1]/(q[0]*q[3]))


def cp_one_cell(s:int,n:int,tail:float)->tuple[float,float]:
    if (type(s) is not int or type(n) is not int or n<1
        or not 0<=s<=n or not 0<tail<.5):
        raise ValueError("invalid binomial q calibration")
    lower=float(betaincinv(s,n-s+1,tail)) if s>0 else 0.
    upper=float(betaincinv(s+1,n-s,1.-tail)) if s<n else 1.
    if not 0<=lower<=upper<=1:
        raise ValueError("exact CP bounds invalid")
    return lower,upper


def cp_band(successes:tuple[int,...],n:int,alpha:float)->tuple[np.ndarray,np.ndarray]:
    if not len(successes) in (4,8):
        raise ValueError("four mix or eight distance×season detector calibration cells")
    if type(n) is not int or n<1:
        raise ValueError("calibration sample count per cell invalid")
    if not 0<alpha<.05:
        raise ValueError("invalid simultaneous confidence budget")
    tail=alpha/(2*len(successes))
    pairs=[cp_one_cell(s,n,tail) for s in successes]
    return np.array([a for a,b in pairs]),np.array([b for a,b in pairs])


def mixed_detector_q_bounds(
    qnear_lo:np.ndarray,qnear_hi:np.ndarray,
    qfar_lo:np.ndarray,qfar_hi:np.ndarray,
    mix_lo:np.ndarray,mix_hi:np.ndarray
)->tuple[np.ndarray,np.ndarray]:
    if any(x.shape!=(4,) for x in (
        qnear_lo,qnear_hi,qfar_lo,qfar_hi,mix_lo,mix_hi
    )):
        raise ValueError("all source stratification bounds must cover same 4 cells")
    if (np.any(qnear_lo>qnear_hi) or np.any(qfar_lo>qfar_hi)
        or np.any(mix_lo>mix_hi)
        or np.any(mix_lo<0) or np.any(mix_hi>1)):
        raise ValueError("invalid simultaneous q/mix bounds")
    w_for_low=np.where(qnear_lo<qfar_lo,mix_hi,mix_lo)
    w_for_hi=np.where(qnear_hi>qfar_hi,mix_hi,mix_lo)
    lo=w_for_low*qnear_lo+(1-w_for_low)*qfar_lo
    hi=w_for_hi*qnear_hi+(1-w_for_hi)*qfar_hi
    if np.any(lo<0) or np.any(lo>hi) or np.any(hi>1+1e-12):
        raise ValueError("transported detector interval not valid")
    return lo,hi


def detector_gamma_upper(qlo:np.ndarray,qhi:np.ndarray)->float:
    if qlo.shape!=(4,) or qhi.shape!=(4,) or np.any(qlo<0) or np.any(qhi>1):
        raise ValueError("invalid effective detector q support")
    if qlo[0]<=0 or qlo[3]<=0:
        return math.inf
    return float(qhi[2]*qhi[1]/(qlo[0]*qlo[3]))


def trial(wi:int,ni:int,rep:int)->dict[str,object]:
    if not(0<=wi<len(WORLDS) and 0<=ni<len(NS) and 0<=rep<REPS):
        raise ValueError("only frozen distance-transport coordinates")
    name,theta_latent,mix,source=WORLDS[wi]
    n=NS[ni]
    rng=np.random.default_rng(np.random.SeedSequence([SEED,wi,ni,rep]))
    # The pooled reference sample has exactly 50:50 near/far reference
    # opportunities by design: 2n per season-bin, but their Bernoulli
    # success probabilities differ; a naively pooled binomial CP
    # interval is itself misspecified. Its ecological inference is
    # explicitly an INVALID comparator, not a nominal alpha test.
    near_s=tuple(int(x) for x in rng.binomial(n,np.array(NEAR)))
    far_s=tuple(int(x) for x in rng.binomial(n,np.array(FAR)))
    target_s=tuple(int(x) for x in rng.binomial(n,np.array(mix)))
    qref_s=tuple(a+b for a,b in zip(near_s,far_s))
    ref_lo,ref_hi=cp_band(qref_s,2*n,.025)
    naive_gamma=detector_gamma_upper(ref_lo,ref_hi)

    near_lo,near_hi=cp_band(near_s,n,ALPHA_Q)
    far_lo,far_hi=cp_band(far_s,n,ALPHA_Q)
    mix_lo,mix_hi=cp_band(target_s,n,ALPHA_W)
    calibrated_lo,calibrated_hi=mixed_detector_q_bounds(
        near_lo,near_hi,far_lo,far_hi,mix_lo,mix_hi)
    corrected_gamma=detector_gamma_upper(calibrated_lo,calibrated_hi)

    actual_effq=q_effective(NEAR,FAR,mix)
    actual_gamma=detector_crossproduct(actual_effq)
    # original within-stratum true q has no season/time interaction
    theta_obs=theta_latent*actual_gamma
    events=_draw_site_four_count_table(rng,source,theta_obs)
    x=events[2]
    def test(B:float)->bool:
        return (math.isfinite(B)
                and _tail_from_margins(source,x,B)<ALPHA_TEST)
    joint_q=bool(np.all(near_lo<=NEAR) and np.all(NEAR<=near_hi)
                 and np.all(far_lo<=FAR) and np.all(FAR<=far_hi))
    joint_mix=bool(np.all(mix_lo<=mix) and np.all(mix<=mix_hi))
    return {
        "true_target_detector_gamma":actual_gamma,
        "reference_mixture_detector_gamma":detector_crossproduct(
            q_effective(NEAR,FAR,WREF)),
        "reference_naive_CP_certifies":test(naive_gamma),
        "transported_CP_certifies":test(corrected_gamma),
        "transport_q_joint_coverage":joint_q,
        "transport_mix_joint_coverage":joint_mix,
        "transport_all_12_joint_coverage":joint_q and joint_mix,
        "transport_B":corrected_gamma,
        "naive_reference_B":naive_gamma,
        "transport_HOLD":not math.isfinite(corrected_gamma),
        "detected_event_counts":events,
    }


def run_frozen_transport_panel(plan:Mapping[str,object],
                               *,_test_replicates:int|None=None)->dict[str,object]:
    guard(plan)
    reps=REPS if _test_replicates is None else _test_replicates
    if type(reps) is not int or not 1<=reps<=REPS:
        raise ValueError("invalid frozen detector transport preflight count")
    scenarios=[]
    for wi,(name,theta,mix,source) in enumerate(WORLDS):
        for ni,n in enumerate(NS):
            draws=[trial(wi,ni,j) for j in range(reps)]
            def average(key:str)->float:
                return float(sum(bool(v[key]) for v in draws)/reps)
            diff=np.asarray([int(z["transported_CP_certifies"])-
                             int(z["reference_naive_CP_certifies"])
                             for z in draws],dtype=float)
            finite=[z["transport_B"] for z in draws
                    if math.isfinite(z["transport_B"])]
            valid_qmix=all(z["true_target_detector_gamma"]==
                          draws[0]["true_target_detector_gamma"] for z in draws)
            if not valid_qmix:
                raise ValueError("fixed truth detector composition changed across draws")
            scenarios.append({
                "world":name,
                "true_latent_encounter_OR":theta,
                "n_q_opportunities_per_8_stratum_cells":n,
                "n_independent_target_mix_opportunities_per_4_cells":n,
                "reference_q_opportunities_total":8*n,
                "independent_target_mix_opportunities_total":4*n,
                "replicates":reps,
                "true_detector_gamma":draws[0]["true_target_detector_gamma"],
                "reference_50pct_detector_gamma":1.,
                "naive_reference_CP_false_or_true_certification_fraction":
                    average("reference_naive_CP_certifies"),
                "stratified_target_standardized_CP_certification_fraction":
                    average("transported_CP_certifies"),
                "paired_corrected_minus_naive_fraction":float(diff.mean()),
                "paired_difference_mc_se":(
                    float(diff.std(ddof=1)/math.sqrt(reps)) if reps>1 else None),
                "true_distance_stratum_q_joint_coverage":average("transport_q_joint_coverage"),
                "true_target_distance_mix_joint_coverage":average("transport_mix_joint_coverage"),
                "all_12_q_and_mix_joint_coverage":average("transport_all_12_joint_coverage"),
                "transported_q_bound_zero_HOLD_fraction":average("transport_HOLD"),
                "median_finite_target_calibrated_detector_B":
                    (float(np.median(finite)) if finite else None),
            })
    if len(scenarios)!=len(WORLDS)*len(NS):
        raise ValueError("frozen q transport scenario matrix incomplete")
    return {
        "schema_version":1,
        "method":METHOD,
        "status":("SOURCE_FREE_DISTANCE_MIX_TRANSPORT_FULL_PANEL"
                  if reps==REPS else "SOURCE_FREE_DISTANCE_MIX_PREFLIGHT"),
        "first_frozen_worlds":scenarios,
        "world_count":len(scenarios),
        "replicates_per_world":reps,
        "calibration_q_alpha":ALPHA_Q,
        "mix_alpha":ALPHA_W,
        "animal_exact_test_alpha":ALPHA_TEST,
        "corrected_joint_error_bound_if_reference_valid":
            ALPHA_Q+ALPHA_W+ALPHA_TEST,
        "pooled_reference_is_not_target_transport_valid":True,
        "pooled_heterogeneous_counts_CP_not_nominal_binomial_valid":True,
        "independent_true_passage_labels_assumed_not_verified":True,
        "original_Uljin_animal_or_source_camera_data_read":False,
        "original_registered_ODSP_routes_unchanged":True,
    }
