"""Valid pooled camera-q calibration may not transport to physical cameras.

A reference TRUE passage independently samples camera type A/B at 50:50
before independently testing the focal detector. Even with heterogeneous
site q, the reference-population source count is genuinely iid Binomial
(n,mean(qA,qB)) and exact Clopper-Pearson coverage is valid for THAT
source mixture. It does NOT certify q of any particular heldout camera.

Compare that deliberately NONTRANSPORTABLE pooled camera source with
valid station-specific (16 independent stations x 6 clock 4h blocks)
simultaneous CP q calibration at the SAME number of independently
labeled reference passages. Each site score uses the original 82 dates
and 96 local-CIVIL 15min bins with the original five fixed model
families. Site types are IID, and the exact site-sign test uses
n=16 physical stations and four-pair Bonferroni alpha=.00625.

This is source-free. The external camera q is artificially STATIONARY
across 82 dates and CONSTANT inside original 4h clock blocks. Bounds
optimized by date independently are OUTER/conservative, NOT sharp for
q shared across dates. No original NIE/EcoBank events or device logs.
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

try:
    from scipy.special import betaincinv
except ImportError as exc:
    raise ImportError("optional SciPy required by dedicated station q calibration CI") from exc

METHOD="uljin_site_specific_camera_q_transport_v0"
PATTERNS=(
    ("homogeneous_site_q",(.62,.66,.57,.60,.64,.67),(.62,.66,.57,.60,.64,.67)),
    ("heterogeneous_site_q",(.95,.85,.35,.32,.60,.90),(.30,.43,.90,.91,.73,.35))
)
TRUTH_IDS=("fixed_clock","sunrise_sunset_tracking","residual_seasonal_phase_shift")
COUNTS=(20,200)
BUDGETS=((38400,400,6400),(153600,1600,25600))
METHODS=("pooled_reference_iid_station_mixture","site_stratified_reference")
PAIRS=(
    ("solar_phase","civil_clock"),
    ("solar_phase_plus_branch","solar_phase"),
    ("solar_noon","civil_clock"),
    ("average_anchor","solar_phase")
)
SITE_SEED=2026101019
EVENT_SEED=2026101020
REFERENCE_SEED=2026101021
ALPHA_Q=.025
ALPHA_PAIR=.00625
SITE_N=16


def frozen_guard(plan:Mapping[str,object],parent:Mapping[str,object])->None:
    if not isinstance(plan,Mapping) or not isinstance(parent,Mapping):
        raise ValueError("source-free station-specific q freeze/lineage required")
    frame=plan.get("common_observation_frame",{})
    sites=plan.get("site_generation",{})
    ext=plan.get("external_calibration",{})
    status=plan.get("expected_results",{})
    if (
        plan.get("schema_version")!=1
        or plan.get("contract_id")!=METHOD
        or plan.get("state")!=
            "PRE_OUTCOME_FROZEN_AFTER_PR258_FIRST_COMPLETE_SITE_MAJORITY_RESULTS"
        or plan.get("parent_pr")!=258
        or plan.get("parent_first_ci")!=38014938577
        or plan.get("parent_first_result")!=
            "ULJIN_JOINT_Q_SITE_MAJORITY_V0_FIRST_RESULT_LEDGER.json"
        or frame.get("original_41_astronomy_pairs") is not True
        or frame.get("date_count")!=82
        or frame.get("civil_clock_bins")!=96
        or frame.get("train_sites")!=TRAIN_SITES
        or frame.get("heldout_sites")!=SITE_N
        or frame.get("generating_truths")!=list(TRUTH_IDS)
        or frame.get("detected_events_per_physical_site_date")!=list(COUNTS)
        or frame.get("pairwise_models")!=[list(x) for x in PAIRS]
        or [(x.get("id"),tuple(x.get("site_type_A",())),
             tuple(x.get("site_type_B",()))) for x in
            plan.get("true_camera_site_patterns",[])]!=list(PATTERNS)
        or sites.get("site_type_seed")!=SITE_SEED
        or sites.get("animal_event_seed")!=EVENT_SEED
        or sites.get("site_q_stationary_across_calendar_82_dates") is not True
        or ext.get("q_source_alpha")!=ALPHA_Q
        or ext.get("four_fixed_pairwise_site_test_alpha_each")!=ALPHA_PAIR
        or ext.get("two_equal_gold_reference_budgets")!=[
            {"total_independent_passage_reference_opportunities":total,
             "n_each_16site_x_6blocks":site_n,
             "n_each_6_pooled_blocks":pool_n}
            for total,site_n,pool_n in BUDGETS
        ]
        or ext.get("source_reference_rng")!=REFERENCE_SEED
        or status.get("original_cases")!=96
        or status.get("misportability_held_pooled_heterogeneous")!=24
        or parent.get("record_type")!=
            "FIRST_FROZEN_JOINT_96BIN_Q_AND_INDEPENDENT_SITE_MAJORITY_V0_TERMINAL_RESULT"
        or parent.get("first_complete_ci_run")!=38014938577
        or parent.get("first_artifact_id")!=11655159899
    ):
        raise ValueError("frozen station-specific detector q method/parent altered")


def make_32_physical_site_types(pattern_index:int)->np.ndarray:
    if type(pattern_index) is not int or not 0<=pattern_index<len(PATTERNS):
        raise ValueError("unknown source-free physical camera truth")
    rng=np.random.default_rng(
        np.random.SeedSequence([SITE_SEED,pattern_index,1]))
    labels=rng.integers(0,2,size=TOTAL_SITES)
    if labels.shape!=(32,):
        raise ValueError("incomplete site population sample")
    return labels


def source_q_and_station_q(
    pattern_index:int,types:np.ndarray
)->tuple[np.ndarray,np.ndarray]:
    if types.shape!=(32,) or np.any((types!=0)&(types!=1)):
        raise ValueError("independently sampled complete physical site roster required")
    _,A,B=PATTERNS[pattern_index]
    a,b=np.asarray(A),np.asarray(B)
    site_q=np.where(types[:,None]==0,a[None,:],b[None,:])
    pooled=(a+b)/2
    if np.any(site_q<=0) or np.any(site_q>=1):
        raise ValueError("frozen site-camera detector sensitivity invalid")
    return site_q,pooled


def exact_joint_cp(
    successes:np.ndarray,n:int,alpha:float=ALPHA_Q
)->tuple[np.ndarray,np.ndarray]:
    if (
        type(n) is not int or n<=0 or not 0<alpha<1
        or successes.shape not in ((6,),(16,6))
        or np.any(successes<0) or np.any(successes>n)
        or not np.issubdtype(successes.dtype,np.integer)
    ):
        raise ValueError("independent per-camera or iid pooled q-source counts invalid")
    tail=alpha/(2*successes.size)
    s=successes.astype(float)
    lo=np.zeros_like(s)
    hi=np.ones_like(s)
    positive=s>0
    incomplete=s<n
    lo[positive]=betaincinv(s[positive],n-s[positive]+1,tail)
    hi[incomplete]=betaincinv(s[incomplete]+1,n-s[incomplete],1-tail)
    if not (np.isfinite(lo).all() and np.isfinite(hi).all()
            and np.all(lo<=hi) and np.all(lo>=0) and np.all(hi<=1)):
        raise ValueError("simultaneous station detector CP interval malformed")
    return lo,hi


def frozen_reference_calibration(
    pattern_index:int,budget_index:int,method_index:int,
    site_q:np.ndarray,pool_q:np.ndarray
)->dict[str,object]:
    if (
        type(pattern_index) is not int or not 0<=pattern_index<2
        or type(budget_index) is not int or not 0<=budget_index<2
        or type(method_index) is not int or not 0<=method_index<2
        or site_q.shape!=(32,6) or pool_q.shape!=(6,)
    ):
        raise ValueError("out-of-frame q calibration")
    total,nsite,npool=BUDGETS[budget_index]
    if total!=16*6*nsite or total!=6*npool:
        raise ValueError("unaligned external passage reference budgets")
    rng=np.random.default_rng(np.random.SeedSequence(
        [REFERENCE_SEED,pattern_index,budget_index,method_index,999]))
    if method_index==0:
        source_counts=rng.binomial(npool,pool_q)
        lo,hi=exact_joint_cp(source_counts,npool)
        source_true=pool_q
        site_lo=np.broadcast_to(lo,(16,6))
        site_hi=np.broadcast_to(hi,(16,6))
    else:
        source_counts=rng.binomial(nsite,site_q[16:])
        lo,hi=exact_joint_cp(source_counts,nsite)
        source_true=site_q[16:]
        site_lo,site_hi=lo,hi
    source_joint=bool(np.all(lo<=source_true) and np.all(source_true<=hi))
    site_coverage=bool(np.all(site_lo<=site_q[16:])
                       and np.all(site_q[16:]<=site_hi))
    return {
        "method":METHODS[method_index],
        "q_lower_for_each_heldout_site":np.asarray(site_lo),
        "q_upper_for_each_heldout_site":np.asarray(site_hi),
        "source_joint_q_coverage_ORACLE_AUDIT_ONLY":source_joint,
        "heldout_site_specific_q_coverage_ORACLE_AUDIT_ONLY":site_coverage,
        "heldout_individual_site_q_cells_covered_ORACLE_AUDIT_ONLY":
            int(np.sum(np.all(
                (site_lo<=site_q[16:])&(site_q[16:]<=site_hi),
                axis=1))),
        "source_sampling_correct_iid_binomial":True,
        "source_reference_target":(
            "iid_reference_population_site_type_mixture_mean"
            if method_index==0 else
            "each_physical_heldout_camera_site_six_original_clock_blocks"),
        "source_to_physical_site_transport_valid":(
            pattern_index==0 or method_index==1),
        "reference_trials_per_source_group":(
            npool if method_index==0 else nsite),
        "number_independent_calibration_groups":lo.size,
        "total_reference_passage_opportunities":total,
        "HOLD_any_q_lower_zero":bool(np.any(lo<=0)),
    }


def site_masses_and_counts(
    profiles:dict[str,np.ndarray],branch:np.ndarray,
    pattern_index:int,truth_id:str,n:int,
    site_q:np.ndarray
)->tuple[np.ndarray,dict[str,np.ndarray],dict[str,object]]:
    if site_q.shape!=(32,6) or truth_id not in TRUTH_IDS or n not in COUNTS:
        raise ValueError("invalid physical station/calendar truth")
    j=next(i for i,z in enumerate(TRUTHS) if z[0]==truth_id)
    _,kind,rise,fall=TRUTHS[j]
    base=profiles["solar_phase" if kind=="solar_phase_plus_branch" else kind]
    rise_idx=int(np.flatnonzero(np.isclose(PEAKS,rise))[0])
    fall_idx=int(np.flatnonzero(np.isclose(PEAKS,fall))[0])
    latent=np.stack([
        base[d,:,rise_idx if b==0 else fall_idx]
        for d,b in enumerate(branch)
    ])
    q96=np.repeat(site_q,16,axis=1)
    detected=latent[None,:,:]*q96[:,None,:]
    detected/=detected.sum(axis=2,keepdims=True)
    if detected.shape!=(32,82,96) or not np.allclose(
        detected.sum(axis=2),1,atol=1e-12
    ):
        raise ValueError("invalid site-camera recorded event law")
    rng=np.random.default_rng(np.random.SeedSequence(
        [EVENT_SEED,pattern_index,j,n]))
    # NumPy multinomial draws independent physical site×date event rows
    counts=np.stack([
        np.stack([rng.multinomial(n,p) for p in site]) for site in detected])
    fit=_fit_and_score(profiles,counts,branch)
    forecasts={
        m:fitted_civil_masses(profiles,branch,fit,m) for m in KINDS
    }
    return counts[16:],forecasts,fit


def vectorized_date_fractional_extrema(
    a:np.ndarray,b:np.ndarray,lo:np.ndarray,hi:np.ndarray
)->tuple[np.ndarray,np.ndarray]:
    """Per-date SHARP extrema, summed over dates => valid OUTER envelope.

    a,b: 82 dates ×6 civil 4hour mass per group.
    lo,hi:16 sites ×6 source q CP interval.
    Note q is physically constant over 82 dates per site; optimizing
    q SEPARATELY by date enlarges the feasible set, hence these
    are conservative OUTER bounds, not the sharp joint-day optimum.
    """
    if (
        a.shape!=(82,6) or b.shape!=(82,6)
        or lo.shape!=(16,6) or hi.shape!=(16,6)
        or np.any(a<=0) or np.any(b<=0) or np.any(lo<=0)
        or np.any(lo>hi) or np.any(hi>1)
    ):
        raise ValueError("positive six civil q groups and valid source bounds required")
    aa=a[None,:,:]
    bb=b[None,:,:]
    low0=(a/b).min(axis=1)[None,:]
    high0=(a/b).max(axis=1)[None,:]
    extremes=[]
    for minimum in (True,False):
        L=np.broadcast_to(low0,(16,82)).copy()
        R=np.broadcast_to(high0,(16,82)).copy()
        for _ in range(65):
            middle=(L+R)/2
            coeff=aa-middle[:,:,None]*bb
            q=np.where(coeff>=0,
                       lo[:,None,:] if minimum else hi[:,None,:],
                       hi[:,None,:] if minimum else lo[:,None,:])
            signed=(coeff*q).sum(axis=2)
            if minimum:
                L=np.where(signed>0,middle,L)
                R=np.where(signed>0,R,middle)
            else:
                L=np.where(signed>0,middle,L)
                R=np.where(signed>0,R,middle)
        extremes.append((L+R)/2)
    if np.any(extremes[0]>extremes[1]+1e-10):
        raise ValueError("joint-source ratio outer bounds inverted")
    return extremes[0],extremes[1]


def station_site_majority(
    heldout:np.ndarray,a:np.ndarray,b:np.ndarray,
    true_site_q:np.ndarray,reference:Mapping[str,object]
)->dict[str,object]:
    if (
        heldout.shape!=(16,82,96) or a.shape!=(82,96)
        or b.shape!=(82,96) or true_site_q.shape!=(16,6)
        or np.any(heldout<0) or np.any(a<=0) or np.any(b<=0)
    ):
        raise ValueError("original 16 site, 82 day, 96 civil-bin response must be fixed")
    counts=heldout.sum(axis=2)
    totals=counts.sum(axis=1)
    if np.any(totals<=0):
        raise ValueError("site without detected events requires new missingness route")
    evt=np.einsum("sdk,dk->s",heldout,np.log(a/b))/totals
    a6=a.reshape(82,6,16).sum(axis=2)
    b6=b.reshape(82,6,16).sum(axis=2)
    qtrue=true_site_q
    true_ln=np.log(
        ((a6[None,:,:]*qtrue[:,None,:]).sum(axis=2))/
        ((b6[None,:,:]*qtrue[:,None,:]).sum(axis=2))
    )
    true_gap=evt-np.sum(counts*true_ln,axis=1)/totals
    true_K=int(np.sum(true_gap>1e-12))
    lo=reference["q_lower_for_each_heldout_site"]
    hi=reference["q_upper_for_each_heldout_site"]
    transport=reference["source_to_physical_site_transport_valid"]
    if not transport or reference["HOLD_any_q_lower_zero"]:
        return {
            "scope":"HOLD_POOLED_Q_NOT_PORTABLE_TO_INDIVIDUAL_SITE" if not transport
                    else "HOLD_NO_FINITE_SOURCE_CAMERA_Q_LOWER",
            "site_majority_certified":None,
            "physical_robust_positive_site_count":None,
            "exact_16_site_one_sided_p":None,
            "descriptive_true_q_positive_site_count_ORACLE_ONLY":true_K,
            "pooled_source_q_joint_coverage_ORACLE_ONLY":reference[
                "source_joint_q_coverage_ORACLE_AUDIT_ONLY"],
            "individual_site_q_joint_coverage_ORACLE_ONLY":reference[
                "heldout_site_specific_q_coverage_ORACLE_AUDIT_ONLY"],
            "no_oracle_q_coverage_decision_gate":True,
        }
    ratio_min,ratio_max=vectorized_date_fractional_extrema(
        a6,b6,lo,hi)
    lower=evt-np.sum(counts*np.log(ratio_max),axis=1)/totals
    upper=evt-np.sum(counts*np.log(ratio_min),axis=1)/totals
    if not np.all(lower<=upper+1e-10):
        raise ValueError("sitewise common detector interval invalid")
    if reference["heldout_site_specific_q_coverage_ORACLE_AUDIT_ONLY"]:
        if np.any(true_gap<lower-1e-10) or np.any(true_gap>upper+1e-10):
            raise ValueError("valid detector q calibration should enclose true q site score")
    K=int(np.sum(lower>1e-12))
    exact_p=exact_site_majority_right_tail(K)
    return {
        "scope":"SOURCE_SITE_Q_CALIBRATION_TRANSPORTS_TO_TARGET",
        "site_majority_certified":bool(exact_p<.00625),
        "physical_robust_positive_site_count":K,
        "exact_16_site_one_sided_p":exact_p,
        "descriptive_true_q_positive_site_count_ORACLE_ONLY":true_K,
        "descriptive_lower_site_score_bounds":[float(z) for z in lower],
        "descriptive_upper_site_score_bounds":[float(z) for z in upper],
        "source_q_coverage_ORACLE_ONLY":reference[
            "source_joint_q_coverage_ORACLE_AUDIT_ONLY"],
        "individual_site_q_joint_coverage_ORACLE_ONLY":reference[
            "heldout_site_specific_q_coverage_ORACLE_AUDIT_ONLY"],
        "no_oracle_q_coverage_decision_gate":True,
        "outer_not_sharp_due_82day_q_stationarity":True,
    }


def run_first_site_q_transport_panel(
    plan:Mapping[str,object],parent:Mapping[str,object],
    calendar:Mapping[str,object]
)->dict[str,object]:
    frozen_guard(plan,parent)
    days,branch=original_days(calendar)
    if len(days)!=82:
        raise ValueError("original calendar refrozen differently")
    profiles=precompute_profiles(days)
    rows=[]
    source_receipts=[]
    for pi,(name,A,B) in enumerate(PATTERNS):
        types=make_32_physical_site_types(pi)
        site_q,ref_q=source_q_and_station_q(pi,types)
        for bi,(budget,nsite,npool) in enumerate(BUDGETS):
            cals=[frozen_reference_calibration(
                pi,bi,mi,site_q,ref_q) for mi in (0,1)]
            for cal in cals:
                source_receipts.append({
                    "true_station_q_structure":name,
                    "budget_total_passages":budget,
                    "method":cal["method"],
                    "source_group_count":cal["number_independent_calibration_groups"],
                    "reference_trials_per_group":cal["reference_trials_per_source_group"],
                    "source_ref_q_joint_coverage_oracle_only":
                        cal["source_joint_q_coverage_ORACLE_AUDIT_ONLY"],
                    "target_site_q_joint_coverage_oracle_only":
                        cal["heldout_site_specific_q_coverage_ORACLE_AUDIT_ONLY"],
                    "individual_sites_all_six_q_cells_covered_oracle_only":
                        cal["heldout_individual_site_q_cells_covered_ORACLE_AUDIT_ONLY"],
                    "source_q_correct_iid_binomial":
                        cal["source_sampling_correct_iid_binomial"],
                    "source_q_transport_valid_for_each_site":
                        cal["source_to_physical_site_transport_valid"],
                    "no_finite_source_q_lower_hold":cal["HOLD_any_q_lower_zero"],
                })
            for truth in TRUTH_IDS:
                for n in COUNTS:
                    data,preds,fit=site_masses_and_counts(
                        profiles,branch,pi,truth,n,site_q)
                    for aa,bb in PAIRS:
                        calibrated={}
                        for cal in cals:
                            calibrated[cal["method"]]=station_site_majority(
                                data,preds[aa],preds[bb],
                                site_q[16:],cal)
                        rows.append({
                            "true_camera_site_q_pattern":name,
                            "synthetic_animal_time_truth":truth,
                            "detected_events_per_site_date":n,
                            "reference_opportunity_budget":budget,
                            "ordered_model_A":aa,
                            "ordered_model_B":bb,
                            "fitted_training_peak_A":fit[aa][
                                "training_only_peak_parameters"],
                            "fitted_training_peak_B":fit[bb][
                                "training_only_peak_parameters"],
                            "both_equal_cost_reference_calibration_methods":
                                calibrated,
                        })
    if len(rows)!=96 or len(source_receipts)!=8:
        raise ValueError("not all frozen q site transport alternatives preserved")
    held=[r for r in rows if r[
        "both_equal_cost_reference_calibration_methods"][METHODS[0]]["scope"]==
        "HOLD_POOLED_Q_NOT_PORTABLE_TO_INDIVIDUAL_SITE"]
    unique_hold_pairs={
        (r["synthetic_animal_time_truth"],r["detected_events_per_site_date"],
         r["ordered_model_A"],r["ordered_model_B"])
        for r in held
    }
    if len(held)!=48 or len(unique_hold_pairs)!=24:
        raise ValueError("source mixture q must HOLD 24 distinct model cases across two budgets")
    if any(out["site_majority_certified"] is True and
           out["physical_robust_positive_site_count"]<14
           for r in rows
           for out in r["both_equal_cost_reference_calibration_methods"].values()):
        raise ValueError("wrong 16-site binomial multiple-test threshold")
    return {
        "schema_version":1,
        "method":METHOD,
        "status":"SOURCE_FREE_IID_POOLED_VERSUS_SITE_SPECIFIC_CAMERA_Q",
        "original_41_matched_astronomy_pairs":41,
        "original_same_civil_time_quarter_hour_bins":96,
        "heldout_independent_physical_sites":16,
        "calibration_q_simultaneous_alpha":ALPHA_Q,
        "four_site_majority_hypotheses_each_alpha":ALPHA_PAIR,
        "per_scenario_total_false_certification_alpha_under_iid_sites_and_valid_q":.05,
        "all_8_independent_reference_calibration_receipts":source_receipts,
        "all_96_precommitted_model_comparisons":rows,
        "total_precommitted_scenarios":96,
        "pooled_iid_q_source_valid_but_may_not_transport":True,
        "station_q_assumed_time_constant_over_all_original_calendar_dates":True,
        "station_q_outer_bounds_by_independently_extremizing_dates":True,
        "true_site_q_oracle_audits_not_used_for_inferential_decisions":True,
        "real_original_EcoBank_species_camera_hours_or_reference_q_not_accessed":True,
        "all_existing_ODSP_qualified_routes_unchanged":True,
    }
