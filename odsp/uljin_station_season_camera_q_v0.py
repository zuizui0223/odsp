"""Independent station x rising/falling-branch camera q for same-clock forecasts.

Source-free extension of the previous physically independent camera
sign-majority route. Both calibration arms use EQUAL counts of
independently labeled true passage opportunities:

- For each physical station x original six CIVIL 4-hour bins,
  a SOURCE opportunity independently chooses the season branch
  rising/falling 50:50, then focal trigger Bernoulli(q_branch).
  This is a LEGITIMATE iid Binomial(n, (q_rise+q_fall)/2) SOURCE.
  It does NOT transport to branch-specific q when seasons differ.
- Independently measured site x branch x clock-block q source:
  exact Bonferroni 192-cell Clopper-Pearson intervals, alpha_q=.025,
  used with original 16-site four-pair exact sign test.

A model pair A/B predicts the SAME original 96 clock bins, and uses
the SAME physical q_{site,branch,block} in both normalizers.
Individual site score lower bounds are conservatively extremized
independently by date even though actual q is constant across
dates in its season. They are OUTER, not sharp, bounds.

All EcoBank and NIE original animal and hardware records remain HOLD.
"""
from __future__ import annotations

from collections.abc import Mapping
import math
import numpy as np

from .uljin_common_clock_mechanistic_comparison_v0 import (
    KINDS,TRUTHS,PEAKS,TRAIN_SITES,TOTAL_SITES,
    original_days,precompute_profiles,_fit_and_score
)
from .uljin_common_96bin_detector_envelope_v0 import fitted_civil_masses
from .uljin_joint_q_site_majority_v0 import exact_site_majority_right_tail
from .uljin_site_specific_camera_q_transport_v0 import (
    vectorized_date_fractional_extrema
)

try:
    from scipy.special import betaincinv
except ImportError as exc:
    raise ImportError("Optional SciPy for independent site×branch q references") from exc

METHOD="uljin_station_by_photoperiod_branch_q_calibration_v0"
SEED_SITES=2026101022
SEED_ANIMAL=2026101023
SEED_REFERENCE=2026101024
PATTERNS=(
    ("site_heterogeneous_but_branch_invariant",
     (.95,.85,.35,.32,.60,.90),(.95,.85,.35,.32,.60,.90),
     (.30,.43,.90,.91,.73,.35),(.30,.43,.90,.91,.73,.35)),
    ("site_heterogeneous_and_branch_shifted",
     (.95,.85,.35,.32,.60,.90),(.35,.40,.80,.90,.75,.40),
     (.30,.43,.90,.91,.73,.35),(.85,.80,.35,.40,.55,.85)),
)
TRUTH_IDS=("fixed_clock","sunrise_sunset_tracking",
           "residual_seasonal_phase_shift")
EVENT_COUNTS=(20,200)
PAIRS=(("solar_phase","civil_clock"),
       ("solar_phase_plus_branch","solar_phase"),
       ("solar_noon","civil_clock"),
       ("average_anchor","solar_phase"))
BUDGETS=((38400,400,200),(153600,1600,800))
METHODS=("site_only_pooled_branches","site_x_branch_calibrated")
ALPHA_Q=.025
ALPHA_EACH=.00625
N_SITE=16


def validate_frozen(plan:Mapping[str,object],parent:Mapping[str,object])->None:
    if not isinstance(plan,Mapping) or not isinstance(parent,Mapping):
        raise ValueError("source-free station×season q frozen plan required")
    frame=plan.get("common_response",{})
    site=plan.get("site_and_detector_truth",{})
    calibration=plan.get("calibration_design",{})
    out=plan.get("output_contract",{})
    expected_worlds=[
        {"id":name,
         "q_type_A_rising":list(a0),"q_type_A_falling":list(a1),
         "q_type_B_rising":list(b0),"q_type_B_falling":list(b1)}
        for name,a0,a1,b0,b1 in PATTERNS
    ]
    expected_budgets=[
        {"total_true_independent_passages":total,
         "site_only_per_96_cells":n0,
         "site_x_branch_per_192_cells":n1}
        for total,n0,n1 in BUDGETS
    ]
    if (
        plan.get("schema_version")!=1
        or plan.get("contract_id")!=METHOD
        or plan.get("stage")!=
          "FROZEN_AFTER_PR259_FIRST_SOURCE_FREE_OUTCOMES_BEFORE_NEW_RESULTS"
        or plan.get("parent_pr")!=259
        or plan.get("parent_first_ledger")!=
          "ULJIN_SITE_SPECIFIC_CAMERA_Q_V0_FIRST_RESULT_LEDGER.json"
        or plan.get("parent_first_ci_run")!=38015829149
        or frame.get("calendar_pairs")!=41
        or frame.get("dates")!=82
        or frame.get("original_civil_15min_bins")!=96
        or frame.get("physical_training_sites")!=16
        or frame.get("physical_heldout_sites")!=16
        or frame.get("preselected_model_pairs")!=[list(v) for v in PAIRS]
        or frame.get("artificial_animal_truths")!=list(TRUTH_IDS)
        or frame.get("site_date_detected_event_count_levels")!=list(EVENT_COUNTS)
        or site.get("two_q_worlds")!=expected_worlds
        or site.get("site_type_IID_Bernoulli_half_over_32_physical_cameras") is not True
        or site.get("q_constant_within_4h_block") is not True
        or calibration.get("two_equal_total_independent_reference_budgets")!=expected_budgets
        or calibration.get("site_types_seed")!=SEED_SITES
        or calibration.get("animal_event_seed")!=SEED_ANIMAL
        or calibration.get("source_reference_seed")!=SEED_REFERENCE
        or calibration.get("q_alpha_joint")!=ALPHA_Q
        or calibration.get("each_precommitted_comparison_one_sided_alpha")!=ALPHA_EACH
        or calibration.get("no_oracle_gating")!=
           "True known synthetic q in confidence intervals is saved only for debugging, never used to decide pass/HOLD/site sign test. Source q interval miscoverage is already paid by alpha_q."
        or out.get("paired_model_cases")!=96
        or out.get("method_arms_per_case")!=2
        or out.get("reference_receipts")!=8
        or out.get("pooled_branch_source_to_target_HOLD_cases")!=48
        or parent.get("record_type")!=
          "FIRST_FROZEN_IID_POOLED_VERSUS_PHYSICAL_SITE_CAMERA_Q_TRANSPORT_V0_TERMINAL_RESULT"
        or parent.get("first_complete_ci_run")!=38015829149
        or parent.get("first_result_artifact_id")!=11656805488
    ):
        raise ValueError("frozen independent site×season q plan or parent receipt changed")


def physical_site_q(pattern_index:int)->tuple[np.ndarray,np.ndarray]:
    if type(pattern_index) is not int or not 0<=pattern_index<2:
        raise ValueError("unknown predeclared physical camera population")
    _,a0,a1,b0,b1=PATTERNS[pattern_index]
    rng=np.random.default_rng(
        np.random.SeedSequence([SEED_SITES,pattern_index,1]))
    site_type=rng.integers(0,2,size=TOTAL_SITES)
    a=np.array([a0,a1])
    b=np.array([b0,b1])
    q=np.where(site_type[:,None,None]==0,a[None,:,:],b[None,:,:])
    if q.shape!=(32,2,6) or np.any(q<=0) or np.any(q>=1):
        raise ValueError("not the original 32 physical camera season roster")
    return site_type,q


def exact_joint_cp(k:np.ndarray,n:int,alpha:float=ALPHA_Q
                   )->tuple[np.ndarray,np.ndarray]:
    if (k.shape not in ((16,6),(16,2,6))
        or type(n) is not int or n<1 or not 0<alpha<1
        or not np.issubdtype(k.dtype,np.integer)
        or np.any(k<0) or np.any(k>n)):
        raise ValueError("independent source 96/192 detector q interval input invalid")
    tail=alpha/(2*k.size)
    s=k.astype(float)
    lo=np.zeros_like(s)
    hi=np.ones_like(s)
    pos=s>0
    neg=s<n
    lo[pos]=betaincinv(s[pos],n-s[pos]+1,tail)
    hi[neg]=betaincinv(s[neg]+1,n-s[neg],1-tail)
    if not np.all(np.isfinite(lo)) or not np.all(np.isfinite(hi)) or (
        not np.all((lo>=0)&(lo<=hi)&(hi<=1))):
        raise ValueError("invalid simultaneous CP detector q")
    return lo,hi


def calibrate_site_q(pattern_index:int,budget_index:int,method_index:int,
                     q:np.ndarray)->dict[str,object]:
    if (q.shape!=(32,2,6)
        or not 0<=pattern_index<2 or not 0<=budget_index<2
        or not 0<=method_index<2):
        raise ValueError("source q station × photoperiod branch not known")
    budget,npooled,nbranch=BUDGETS[budget_index]
    if 16*6*npooled!=budget or 16*2*6*nbranch!=budget:
        raise ValueError("source reference opportunity budget not matched")
    rng=np.random.default_rng(np.random.SeedSequence(
        [SEED_REFERENCE,pattern_index,budget_index,method_index,999]))
    targets=q[16:]
    if method_index==0:
        src=(targets[:,0,:]+targets[:,1,:])/2
        successes=rng.binomial(npooled,src)
        l,h=exact_joint_cp(successes,npooled)
        lo=np.repeat(l[:,None,:],2,axis=1)
        hi=np.repeat(h[:,None,:],2,axis=1)
        source_n=npooled
    else:
        src=targets
        successes=rng.binomial(nbranch,src)
        lo,hi=exact_joint_cp(successes,nbranch)
        source_n=nbranch
    source_coverage=bool(
        np.all((l<=src)&(src<=h)) if method_index==0 else
        np.all((lo<=src)&(src<=hi)))
    target_coverage=bool(np.all((lo<=targets)&(targets<=hi)))
    return {
        "method":METHODS[method_index],
        "lower":lo,"upper":hi,
        "actual_ref_target_q_branch_specific":method_index==1 or pattern_index==0,
        "source_binomial_iid_correct":True,
        "source_CP_joint_coverage_ORACLE_ONLY":source_coverage,
        "station_by_branch_target_CP_joint_coverage_ORACLE_ONLY":target_coverage,
        "heldout_sites_all_twelve_q_cells_covered_ORACLE_ONLY":int(
            np.sum(np.all((lo<=targets)&(targets<=hi),axis=(1,2)))),
        "q_source_groups":successes.size,
        "source_reference_per_group":source_n,
        "total_true_passage_reference_opportunities":budget,
        "HOLD_zero_q_interval_lower":bool(np.any(lo<=0)),
    }


def generate_site_event_counts(
    profiles:dict[str,np.ndarray],branch:np.ndarray,
    pattern_index:int,truth:str,n:int,q:np.ndarray
)->tuple[np.ndarray,dict[str,np.ndarray],dict[str,object]]:
    if q.shape!=(32,2,6) or truth not in TRUTH_IDS or n not in EVENT_COUNTS:
        raise ValueError("invalid season×camera count generation")
    i=next(j for j,v in enumerate(TRUTHS) if v[0]==truth)
    _,family,rise,fall=TRUTHS[i]
    source=profiles["solar_phase" if family=="solar_phase_plus_branch" else family]
    p0=int(np.flatnonzero(np.isclose(PEAKS,rise))[0])
    p1=int(np.flatnonzero(np.isclose(PEAKS,fall))[0])
    latent=np.stack([source[d,:,p0 if b==0 else p1]
                     for d,b in enumerate(branch)])
    true_q_96=np.repeat(q[:,branch,:],16,axis=2)
    detected=latent[None,:,:]*true_q_96
    detected/=detected.sum(axis=2,keepdims=True)
    if detected.shape!=(32,82,96) or not np.allclose(
        detected.sum(axis=2),1,atol=1e-12):
        raise ValueError("source-free seasonal detector q event law invalid")
    rng=np.random.default_rng(
        np.random.SeedSequence([SEED_ANIMAL,pattern_index,i,n]))
    events=np.stack([np.stack([rng.multinomial(n,p) for p in site])
                     for site in detected])
    fitted=_fit_and_score(profiles,events,branch)
    forecasts={m:fitted_civil_masses(profiles,branch,fitted,m) for m in KINDS}
    return events[16:],forecasts,fitted


def outer_site_score_bounds(
    events:np.ndarray,a:np.ndarray,b:np.ndarray,
    true_q:np.ndarray,branch:np.ndarray,
    calibration:Mapping[str,object]
)->dict[str,object]:
    if (events.shape!=(16,82,96) or a.shape!=(82,96) or b.shape!=(82,96)
        or true_q.shape!=(16,2,6) or branch.shape!=(82,)
        or np.any(events<0) or np.any(a<=0) or np.any(b<=0)):
        raise ValueError("not the frozen source original clock-bin observations")
    nday=events.sum(axis=2)
    nsite=nday.sum(axis=1)
    if np.any(nsite<=0):
        raise ValueError("zero-event physical site requires a separate model")
    term=np.einsum("sdk,dk->s",events,np.log(a/b))/nsite
    am=a.reshape(82,6,16).sum(axis=2)
    bm=b.reshape(82,6,16).sum(axis=2)
    qreal=true_q[:,branch,:]
    true_z=(am[None,:,:]*qreal).sum(axis=2)/(bm[None,:,:]*qreal).sum(axis=2)
    oracle_gap=term-np.sum(nday*np.log(true_z),axis=1)/nsite
    true_K=int(np.sum(oracle_gap>1e-12))
    source_transport=calibration["actual_ref_target_q_branch_specific"]
    if not source_transport or calibration["HOLD_zero_q_interval_lower"]:
        return {
            "scope":("HOLD_SITE_ONLY_Q_NOT_PORTABLE_TO_BRANCH" if not source_transport
                     else "HOLD_SOURCE_Q_LOWER_ZERO"),
            "majority_new_site_certified":None,
            "independent_site_positive_robust_count":None,
            "exact_site_majority_p":None,
            "true_q_16site_positive_ORACLE_ONLY":true_K,
            "source_q_joint_coverage_ORACLE_ONLY":
                calibration["source_CP_joint_coverage_ORACLE_ONLY"],
            "true_target_q_joint_coverage_ORACLE_ONLY":
                calibration["station_by_branch_target_CP_joint_coverage_ORACLE_ONLY"],
            "oracle_coverage_not_in_decision":True
        }
    lower=calibration["lower"][:,branch,:]
    upper=calibration["upper"][:,branch,:]
    ratios_min,ratios_max=vectorized_source_ratio_bounds(am,bm,lower,upper)
    site_lower=term-np.sum(nday*np.log(ratios_max),axis=1)/nsite
    site_upper=term-np.sum(nday*np.log(ratios_min),axis=1)/nsite
    if np.any(site_lower>site_upper+1e-10):
        raise ValueError("frozen per-date outer envelope inverted")
    if calibration["station_by_branch_target_CP_joint_coverage_ORACLE_ONLY"]:
        if np.any(oracle_gap<site_lower-1e-10) or np.any(oracle_gap>site_upper+1e-10):
            raise ValueError("calibrated q TRUE site scores outside q-box envelope")
    k=int(np.sum(site_lower>1e-12))
    pv=exact_site_majority_right_tail(k)
    return {
        "scope":"SOURCE_STATION_X_BRANCH_Q_TARGET_VALID",
        "majority_new_site_certified":bool(pv<ALPHA_EACH),
        "independent_site_positive_robust_count":k,
        "exact_site_majority_p":pv,
        "source_q_joint_coverage_ORACLE_ONLY":
            calibration["source_CP_joint_coverage_ORACLE_ONLY"],
        "true_target_q_joint_coverage_ORACLE_ONLY":
            calibration["station_by_branch_target_CP_joint_coverage_ORACLE_ONLY"],
        "true_q_16site_positive_ORACLE_ONLY":true_K,
        "q_robust_site_lower_outer":[float(x) for x in site_lower],
        "q_robust_site_upper_outer":[float(x) for x in site_upper],
        "outer_bound_not_sharp_over_41dates_in_branch":True,
        "oracle_coverage_not_in_decision":True
    }


def vectorized_source_ratio_bounds(
    a:np.ndarray,b:np.ndarray,lo:np.ndarray,hi:np.ndarray
)->tuple[np.ndarray,np.ndarray]:
    """65-step sharp PER-DATE fractional q bounds; date-sum is OUTER."""
    if (a.shape!=(82,6) or b.shape!=(82,6)
        or lo.shape!=(16,82,6) or hi.shape!=lo.shape
        or np.any(a<=0) or np.any(b<=0)
        or np.any(lo<=0) or np.any(lo>hi) or np.any(hi>1)):
        raise ValueError("invalid 16-station 82-calendar six-civil-q-cell box")
    A=a[None,:,:];B=b[None,:,:]
    l0=np.min(a/b,axis=1)[None,:]
    h0=np.max(a/b,axis=1)[None,:]
    res=[]
    for minimize in (True,False):
        l=np.broadcast_to(l0,(16,82)).copy()
        h=np.broadcast_to(h0,(16,82)).copy()
        for _ in range(65):
            m=(l+h)/2
            c=A-m[:,:,None]*B
            q=np.where(c>=0,lo if minimize else hi,
                       hi if minimize else lo)
            positive=(c*q).sum(axis=2)>0
            l=np.where(positive,m,l)
            h=np.where(positive,h,m)
        res.append((l+h)/2)
    if np.any(res[0]>res[1]+1e-10):
        raise ValueError("fractional extrema reversed")
    return res[0],res[1]


def run_frozen_station_branch_panel(
    plan:Mapping[str,object],parent:Mapping[str,object],
    calendar:Mapping[str,object]
)->dict[str,object]:
    validate_frozen(plan,parent)
    days,branch=original_days(calendar)
    if len(days)!=82 or len(branch)!=82:
        raise ValueError("frozen astronomy calendar changed")
    profiles=precompute_profiles(days)
    all_pairs=[]
    refs=[]
    for pattern_i,(name,*rest) in enumerate(PATTERNS):
        site_types,true_q=physical_site_q(pattern_i)
        for budget_i,(budget,npooled,nbranch) in enumerate(BUDGETS):
            calibs=[
                calibrate_site_q(pattern_i,budget_i,m,true_q) for m in (0,1)]
            for cal in calibs:
                refs.append({
                    "camera_site_q_temporal_world":name,
                    "budget_true_independent_opportunities":budget,
                    "calibration_method":cal["method"],
                    "source_q_group_count":cal["q_source_groups"],
                    "source_reference_opportunities_per_group":
                        cal["source_reference_per_group"],
                    "source_calibration_correct_iid_binomial":
                        cal["source_binomial_iid_correct"],
                    "source_joint_q_coverage_ORACLE_ONLY":
                        cal["source_CP_joint_coverage_ORACLE_ONLY"],
                    "target_station_x_branch_q_joint_coverage_ORACLE_ONLY":
                        cal["station_by_branch_target_CP_joint_coverage_ORACLE_ONLY"],
                    "target_sites_q_all_12_cells_covered_ORACLE_ONLY":
                        cal["heldout_sites_all_twelve_q_cells_covered_ORACLE_ONLY"],
                    "calibration_transports_to_station_x_branch":
                        cal["actual_ref_target_q_branch_specific"],
                    "HOLD_no_positive_q_lower":cal["HOLD_zero_q_interval_lower"]
                })
            for truth in TRUTH_IDS:
                for n in EVENT_COUNTS:
                    data,forecasts,fit=generate_site_event_counts(
                        profiles,branch,pattern_i,truth,n,true_q)
                    for A,B in PAIRS:
                        arms={
                            cal["method"]:outer_site_score_bounds(
                                data,forecasts[A],forecasts[B],
                                true_q[16:],branch,cal)
                            for cal in calibs
                        }
                        all_pairs.append({
                            "camera_q_temporal_world":name,
                            "true_animal_time_world":truth,
                            "site_date_detected_events":n,
                            "reference_budget_true_passages":budget,
                            "ordered_model_A":A,"ordered_model_B":B,
                            "training_peak_A":fit[A]["training_only_peak_parameters"],
                            "training_peak_B":fit[B]["training_only_peak_parameters"],
                            "two_equal_cost_calibration_arms":arms
                        })
    if len(refs)!=8 or len(all_pairs)!=96:
        raise ValueError("predeclared 96 paired comparisons and 8 source receipts required")
    total_hold=sum(z["two_equal_cost_calibration_arms"][METHODS[0]]["scope"]==
                   "HOLD_SITE_ONLY_Q_NOT_PORTABLE_TO_BRANCH"
                   for z in all_pairs)
    if total_hold!=48:
        raise ValueError("all branch-heterogeneous pooled q cases must HOLD")
    if any(arm["majority_new_site_certified"] is True and
           arm["independent_site_positive_robust_count"]<14
           for z in all_pairs for arm in z["two_equal_cost_calibration_arms"].values()):
        raise ValueError("four-comparison physical site sign test threshold violated")
    return {
        "schema_version":1,"method":METHOD,
        "status":"SOURCE_FREE_STATION_X_PHOTOPERIOD_BRANCH_CAMERA_Q_ONLY",
        "original_daylength_mirror_pairs":41,
        "same_original_civil_15min_response_bins":96,
        "independent_training_camera_sites":16,
        "independent_heldout_camera_sites":16,
        "source_q_joint_cp_alpha":ALPHA_Q,
        "site_majority_alpha_each_predeclared_pair":ALPHA_EACH,
        "per_preselected_design_total_error_bound_under_assumptions":.05,
        "frozen_paired_comparisons":all_pairs,
        "frozen_external_reference_calibration_receipts":refs,
        "total_original_paired_cases":len(all_pairs),
        "branch_heterogeneity_pooled_q_HOLD_case_count":total_hold,
        "same_original_five_fixed_trained_clock_and_astronomy_models":True,
        "source_calibration_coverage_oracle_never_gates_a_test":True,
        "site_branch_q_is_true_date_invariant_but_datewise_bounds_outer":True,
        "real_EcoBank_species_events_original_camera_operation_or_q_refs_NOT_read":True,
        "existing_qualified_ODSP_routes_unchanged":True
    }
