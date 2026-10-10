"""Within-branch daily camera q drift: calibration SOURCE mean versus DATE target.

Artificial within-site source q under independently uniform date references
is genuinely iid Binomial(q_site,branch,4h MEAN), even when q changes across
the original 41 rising/falling days. Exact 192-cell source CP bands for qmean
cannot be transferred to individual animal-recording DATES without a
SEPARATELY warranted relative daily drift bound epsilon.

Given qmean in [L,U] simultaneously and externally attested
|q_date/qmean-1|<=eps, qdate in
[max(0,L(1-eps)), min(1,U(1+eps))]. Optimize the SAME unknown
q for both candidates in the SAME 96 original civil bins; datewise
normalizer extrema produce a conservative OUTER 82-day sitewise score
interval. Site majority n=16, four ordered exact sign tests alpha=.00625
plus qmean familywise CP alpha=.025 => union-bound per-design <=.05
ONLY with correct source reference labels and true external eps bound.

No original EcoBank camera operation or ungulate events; source free.
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
from .uljin_station_season_camera_q_v0 import (
    PATTERNS,TRUTH_IDS,EVENT_COUNTS,PAIRS,BUDGETS,
    physical_site_q,calibrate_site_q,generate_site_event_counts,
    vectorized_source_ratio_bounds
)

METHOD="uljin_within_branch_daily_camera_q_drift_v0"
AMPLITUDES=(0.,.35)
EPS=(0.,.1,.2,.35)
NEW_ANIMAL_SEED=2026101027
ALPHA_Q=.025
ALPHA_PAIR=.00625
SITES=16
EXPECTED_PAIRS=384
COS_PHASE=np.pi/6


def frozen_guard(plan:Mapping[str,object],parent:Mapping[str,object])->None:
    if not isinstance(plan,Mapping) or not isinstance(parent,Mapping):
        raise ValueError("original fixed q-drift contract and parent first receipt needed")
    d=plan.get("day_drift_generator",{})
    x=plan.get("external_relative_daily_envelopes",{})
    s=plan.get("simulations",{})
    prior=parent.get("source_free_result_table",[])
    if (
        plan.get("schema_version")!=1
        or plan.get("contract_id")!=METHOD
        or plan.get("stage")!=
           "FROZEN_AFTER_PR260_FIRST_RESULTS_BEFORE_NEW_DAILY_DRIFT_OUTCOMES"
        or plan.get("parent_pr")!=260
        or plan.get("parent_first_result")!=
           "ULJIN_STATION_SEASON_CAMERA_Q_V0_FIRST_RESULT_LEDGER.json"
        or plan.get("parent_first_ci")!=38016397672
        or d.get("drift_amplitudes")!=list(AMPLITUDES)
        or d.get("site_assignment_rng_reused_from_parent") is not True
        or d.get("source_q_reference_rng_reused_from_parent") is not True
        or d.get("parent_station_q_generation_index")!=1
        or x.get("epsilon_grid")!=list(EPS)
        or x.get("source_q_CI_familywise_alpha")!=ALPHA_Q
        or x.get("ordered_pairwise_one_sided_exact_alpha_each")!=ALPHA_PAIR
        or x.get("total_combined_false_majority_certification_bound_given_external_drift_bound_and_iid_sites")!=.05
        or x.get("oracle_coverage_gate_banned") is not True
        or s.get("original_daylength_mirror_pairs")!=41
        or s.get("original_dates")!=82
        or s.get("original_civil_clock_bins")!=96
        or s.get("independent_training_physical_sites")!=TRAIN_SITES
        or s.get("independent_heldout_physical_sites")!=SITES
        or s.get("artificial_animal_truths")!=list(TRUTH_IDS)
        or s.get("events_per_site_date")!=list(EVENT_COUNTS)
        or s.get("original_four_model_pairs")!=[list(x) for x in PAIRS]
        or s.get("independent_source_reference_budgets")!=[
            {"total_true_passages":t,
             "n_per_192_station_branch_civil_clock_block":nbranch}
            for t,_,nbranch in BUDGETS
        ]
        or s.get("new_animal_rng_seed")!=NEW_ANIMAL_SEED
        or s.get("all_cases")!=EXPECTED_PAIRS
        or parent.get("record_type")!=
           "FIRST_FROZEN_SOURCE_FREE_STATION_BY_PHOTOPERIOD_BRANCH_Q_V0_TERMINAL_RESULT"
        or parent.get("first_focused_ci_run")!=38016397672
        or parent.get("first_full_result_artifact_id")!=11656706264
        or len(prior)!=2
        or prior[1]["site_by_branch"]["certified"]!=13
    ):
        raise ValueError("frozen source-free within-branch q drift design/parent changed")


def true_daily_q(branch:np.ndarray,base_q:np.ndarray,
                 site_types:np.ndarray,amp:float)->np.ndarray:
    """32 physical sites ×82 original mirror calendar dates ×6 civil blocks."""
    if (
        branch.shape!=(82,) or base_q.shape!=(32,2,6)
        or site_types.shape!=(32,) or amp not in AMPLITUDES
        or not np.array_equal(branch,np.tile([0,1],41))
        or np.any((site_types!=0)&(site_types!=1))
    ):
        raise ValueError("source daily q must use original 41 ascending/descending pairs")
    j=(np.arange(82)//2)[None,:,None]
    block=np.arange(6)[None,None,:]
    site=site_types[:,None,None]
    cycles=np.cos(2*np.pi*(j+.5)/41+block*COS_PHASE+site*np.pi/3)
    qbar=base_q[:,branch,:]
    q=qbar+amp*np.minimum(qbar,1-qbar)*cycles
    if (q.shape!=(32,82,6) or np.any(q<=0) or np.any(q>=1)
        or not np.allclose(q[:,branch==0,:].mean(axis=1),base_q[:,0,:],atol=1e-12)
        or not np.allclose(q[:,branch==1,:].mean(axis=1),base_q[:,1,:],atol=1e-12)):
        raise ValueError("true daily q source means not equal correct branch reference q")
    return q


def synthetic_detected_events(
    profiles:dict[str,np.ndarray],branch:np.ndarray,
    true_qday:np.ndarray,base_q:np.ndarray,
    amp_index:int,truth:str,n:int
)->tuple[np.ndarray,dict[str,np.ndarray],dict[str,object]]:
    if (amp_index not in (0,1) or truth not in TRUTH_IDS or n not in EVENT_COUNTS
        or true_qday.shape!=(32,82,6)):
        raise ValueError("out-of-frame detector-day event generation")
    if amp_index==0:
        # Strict replay of ORIGINAL already-frozen PR260 original
        # station-by-branch artificial wildlife and source reference.
        return generate_site_event_counts(profiles,branch,1,truth,n,base_q)
    index=next(j for j,t in enumerate(TRUTHS) if t[0]==truth)
    _,kind,rise,fall=TRUTHS[index]
    generating=profiles[
        "solar_phase" if kind=="solar_phase_plus_branch" else kind]
    p0=int(np.flatnonzero(np.isclose(PEAKS,rise))[0])
    p1=int(np.flatnonzero(np.isclose(PEAKS,fall))[0])
    latent=np.stack([
        generating[i,:,p0 if b==0 else p1]
        for i,b in enumerate(branch)
    ])
    q_clock=np.repeat(true_qday,16,axis=2)
    observed=latent[None,:,:]*q_clock
    observed/=observed.sum(axis=2,keepdims=True)
    if (observed.shape!=(32,82,96) or
        not np.allclose(observed.sum(axis=2),1,atol=1e-12)):
        raise ValueError("synthetic daily detector distorted common clock law wrong")
    rng=np.random.default_rng(np.random.SeedSequence(
        [NEW_ANIMAL_SEED,amp_index,index,n]))
    counts=np.stack([
        np.stack([rng.multinomial(n,p) for p in site])
        for site in observed
    ])
    fitted=_fit_and_score(profiles,counts,branch)
    model_probs={
        k:fitted_civil_masses(profiles,branch,fitted,k)
        for k in KINDS
    }
    return counts[TRAIN_SITES:],model_probs,fitted


def external_qday_bounds(
    reference:Mapping[str,object],branch:np.ndarray,
    eps:float
)->tuple[np.ndarray,np.ndarray]:
    if eps not in EPS or branch.shape!=(82,):
        raise ValueError("unfrozen external daily detector q bound")
    lo=reference["lower"]
    hi=reference["upper"]
    if lo.shape!=(16,2,6) or hi.shape!=(16,2,6):
        raise ValueError("requires physical site×branch source q reference")
    day_lo=np.maximum(0.,lo[:,branch,:]*(1.-eps))
    day_hi=np.minimum(1.,hi[:,branch,:]*(1.+eps))
    if (day_lo.shape!=(16,82,6) or not np.all(day_hi>=day_lo)
        or not np.isfinite(day_lo).all() or not np.isfinite(day_hi).all()):
        raise ValueError("externally bounded qday not valid")
    return day_lo,day_hi


def sitewise_outer_daily_score(
    counts:np.ndarray,a:np.ndarray,b:np.ndarray,
    actual_qday:np.ndarray,calibration:Mapping[str,object],
    branch:np.ndarray,eps:float,amp:float
)->dict[str,object]:
    if (counts.shape!=(16,82,96) or a.shape!=(82,96)
        or b.shape!=(82,96) or actual_qday.shape!=(16,82,6)
        or branch.shape!=(82,) or eps not in EPS or amp not in AMPLITUDES
        or np.any(counts<0) or np.any(a<=0) or np.any(b<=0)):
        raise ValueError("all original clock site/day response cells required")
    n_day=counts.sum(axis=2)
    n_site=n_day.sum(axis=1)
    if np.any(n_site<=0):
        raise ValueError("physical site with no events needs separate effort route")
    a6=a.reshape(82,6,16).sum(axis=2)
    b6=b.reshape(82,6,16).sum(axis=2)
    event_term=np.einsum("sdk,dk->s",counts,np.log(a/b))/n_site
    oracle_z=((a6[None,:,:]*actual_qday).sum(axis=2)/
              (b6[None,:,:]*actual_qday).sum(axis=2))
    true_score=event_term-(n_day*np.log(oracle_z)).sum(axis=1)/n_site
    oracle_site_count=int(np.sum(true_score>1e-12))
    # An independently attested deterministic cap is required before
    # any real source model q can be admitted. For these simulations,
    # the original generator's own amplitude is a pre-frozen safe
    # cap. Do NOT look at the realized CP oracle-coverage status here.
    attested=eps+1e-14>=amp
    if not attested or calibration["HOLD_zero_q_interval_lower"]:
        return {
            "scope":("HOLD_EXTERNAL_DAILY_DRIFT_CAP_NOT_ATTESTED"
                     if not attested else "HOLD_Q_REFERENCE_LOWER_ZERO"),
            "daily_bound_eps":eps,
            "source_q_reference_joint_coverage_ORACLE_ONLY":
                calibration["source_CP_joint_coverage_ORACLE_ONLY"],
            "true_site_q_mean_and_daily_clock_coverage_ORACLE_ONLY":None,
            "independent_physical_sites_robust_positive":None,
            "exact_site_sign_p":None,
            "new_site_majority_certified":None,
            "true_q_site_positive_count_ORACLE_ONLY":oracle_site_count,
            "oracle_coverage_not_used_to_admit_or_reject":True,
        }
    lo,hi=external_qday_bounds(calibration,branch,eps)
    lowz,hiz=vectorized_source_ratio_bounds(a6,b6,lo,hi)
    low=event_term-(n_day*np.log(hiz)).sum(axis=1)/n_site
    high=event_term-(n_day*np.log(lowz)).sum(axis=1)/n_site
    if np.any(low>high+1e-10):
        raise ValueError("physical station daily detector score envelope inverted")
    q_within=bool(np.all((lo<=actual_qday)&(actual_qday<=hi)))
    mean_covered=calibration[
        "station_by_branch_target_CP_joint_coverage_ORACLE_ONLY"]
    if mean_covered and not q_within:
        raise ValueError("genuine external daily drift cap must cover q when CP mean covered")
    if q_within and (
        np.any(true_score<low-1e-10) or np.any(true_score>high+1e-10)
    ):
        raise ValueError("the same true physical qday must lie in conservative site envelope")
    k=int(np.sum(low>1e-12))
    p=exact_site_majority_right_tail(k)
    return {
        "scope":"EXTERNAL_DAILY_DRIFT_BOUND_ASSUMED_VALID_SOURCE_FREE",
        "daily_bound_eps":eps,
        "source_q_reference_joint_coverage_ORACLE_ONLY":mean_covered,
        "true_site_q_mean_and_daily_clock_coverage_ORACLE_ONLY":q_within,
        "independent_physical_sites_robust_positive":k,
        "exact_site_sign_p":p,
        "new_site_majority_certified":bool(p<.00625),
        "true_q_site_positive_count_ORACLE_ONLY":oracle_site_count,
        "site_lower_outer":[float(x) for x in low],
        "site_upper_outer":[float(x) for x in high],
        "true_q_site_gap_ORACLE_ONLY":[float(x) for x in true_score],
        "oracle_coverage_not_used_to_admit_or_reject":True,
        "datewise_q_extrema_outer_not_jointly_sharp":True,
    }


def first_frozen_daily_drift_panel(
    plan:Mapping[str,object],parent:Mapping[str,object],
    calendar:Mapping[str,object]
)->dict[str,object]:
    frozen_guard(plan,parent)
    dates,branch=original_days(calendar)
    if len(dates)!=82 or len(branch)!=82:
        raise ValueError("original astronomy mirrored calendar altered")
    profiles=precompute_profiles(dates)
    site_types,qmean=physical_site_q(1)
    rows=[]
    refs=[]
    parent_replay=[]
    for ai,amp in enumerate(AMPLITUDES):
        qday=true_daily_q(branch,qmean,site_types,amp)
        for bi,(budget,_,per_source) in enumerate(BUDGETS):
            cal=calibrate_site_q(1,bi,1,qmean)
            if (cal["method"]!="site_x_branch_calibrated"
                or cal["total_true_passage_reference_opportunities"]!=budget
                or cal["q_source_groups"]!=192
                or cal["source_reference_per_group"]!=per_source):
                raise ValueError("original station-branch reference calibration not replayed")
            refs.append({
                "qday_drift_amplitude":amp,
                "reference_budget":budget,
                "true_mean_q_reference_model_iid_binomial":True,
                "reference_q_source_group_count":192,
                "reference_q_independent_passages_per_cell":per_source,
                "mean_q_CP_joint_coverage_ORACLE_ONLY":
                    cal["source_CP_joint_coverage_ORACLE_ONLY"],
                "source_reference_mean_does_not_identify_daily_q":bool(amp>0),
            })
            for truth in TRUTH_IDS:
                for n in EVENT_COUNTS:
                    counts,forecasts,fit=synthetic_detected_events(
                        profiles,branch,qday,qmean,ai,truth,n)
                    for A,B in PAIRS:
                        at_eps={}
                        for eps in EPS:
                            item=sitewise_outer_daily_score(
                                counts,forecasts[A],forecasts[B],
                                qday[16:],cal,branch,eps,amp)
                            at_eps[str(eps)]=item
                        valid=[at_eps[str(e)] for e in EPS if e+1e-14>=amp]
                        kprev=None
                        for record in valid:
                            k=record["independent_physical_sites_robust_positive"]
                            if k is not None:
                                if kprev is not None and k>kprev:
                                    raise ValueError("larger drift uncertainty cannot increase robust sites")
                                kprev=k
                        if ai==0:
                            replay=at_eps["0.0"]
                            parent_replay.append(bool(
                                replay["new_site_majority_certified"]))
                        rows.append({
                            "daily_q_generator_amplitude":amp,
                            "synthetic_animal_time_truth":truth,
                            "site_date_detected_event_n":n,
                            "reference_true_passage_budget":budget,
                            "ordered_model_A":A,
                            "ordered_model_B":B,
                            "fitted_training_peak_A":fit[A][
                                "training_only_peak_parameters"],
                            "fitted_training_peak_B":fit[B][
                                "training_only_peak_parameters"],
                            "all_four_precommitted_eps_results":at_eps,
                        })
    if len(rows)!=96 or len(refs)!=4 or len(rows)*len(EPS)!=EXPECTED_PAIRS:
        raise ValueError("not all original 384 daily drift tests retained")
    # Strict numerical consequence of exact replaying PR260 original
    # q calibration and animal event simulations for amp=0 & eps=0.
    old_positive=parent["source_free_result_table"][1]["site_by_branch"]["certified"]
    if len(parent_replay)!=48 or sum(parent_replay)!=old_positive:
        raise ValueError("prior PR260 station-branch first positive count did not replay")
    status_counts={}
    for ai,amp in enumerate(AMPLITUDES):
        for eps in EPS:
            result=[r["all_four_precommitted_eps_results"][str(eps)]
                    for r in rows if r["daily_q_generator_amplitude"]==amp]
            admitted=sum(z["scope"]==
                         "EXTERNAL_DAILY_DRIFT_BOUND_ASSUMED_VALID_SOURCE_FREE"
                         for z in result)
            certified=sum(z["new_site_majority_certified"] is True
                          for z in result)
            hold=sum(z["scope"]=="HOLD_EXTERNAL_DAILY_DRIFT_CAP_NOT_ATTESTED"
                     for z in result)
            status_counts[f"amplitude={amp}:eps={eps}"]={
                "case_count":len(result),
                "admitted_under_predeclared_external_amplitude_bound":admitted,
                "certified_A_new_site_majority":certified,
                "HOLD_unattested_daily_drift_bound":hold
            }
    return {
        "schema_version":1,
        "method":METHOD,
        "status":"SOURCE_FREE_DAILY_DETECTOR_Q_DRIFT_OUTER_SITE_MAJORITY",
        "original_astronomy_pairs":41,
        "original_96_civil_clock_quarterhour_bins":96,
        "independent_heldout_physical_sites":16,
        "source_qmean_exact_CP_familywise_alpha":ALPHA_Q,
        "four_site_majority_tests_familywise_alpha":.025,
        "total_per_attested_design_false_majority_alpha_bound":.05,
        "all_first_96_model_comparisons_by_four_eps":rows,
        "total_frozen_case_x_eps":len(rows)*len(EPS),
        "all_source_reference_qmean_audits":refs,
        "pr260_original_station_branch_eps0_positive_count_replayed":
            sum(parent_replay),
        "summary_by_daily_truth_and_attested_external_eps":status_counts,
        "source_reference_mean_CP_does_not_prove_daily_q_scope":True,
        "inference_requires_independently_attested_daily_drift_bound":True,
        "oracle_q_coverage_only_a_result_audit_not_a_gate":True,
        "separate_date_extrema_are_conservative_outer_not_joint_sharp":True,
        "no_real_original_NIE_EcoBank_animal_events_camera_uptime_q_references":True,
        "previous_qualified_ODSP_inference_routes_unchanged":True,
    }
