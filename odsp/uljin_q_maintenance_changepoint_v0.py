"""Known maintenance change in station×branch camera detector q.

Reference passages independently sample calendar DATE uniformly from each
predeclared time group, then detector triggering with that day's true q:
group successes are genuinely iid Bernoulli(group mean q) under the
artificial model. Valid source CP intervals for a 7day pooled MEAN are
not necessarily valid for individual days across a hardware step.

A genuinely independent maintenance log (synthetic-only) establishes a
q change at original matched pair index j=20. Time groups split there
are constant-q and transport; unchanged 7day groups that STRADDLE the
break are HOLD without testing if a model appears to win. Daily groups
transport without an assumed maintenance log. Everything retains the
same 41 mirror calendar pairs, 96 common CIVIL event bins, and 16 IID
heldout PHYSICAL station-site score majority targets.
"""
from __future__ import annotations

import math
from collections.abc import Mapping
import numpy as np
from .uljin_common_clock_mechanistic_comparison_v0 import (
    KINDS,TRUTHS,PEAKS,TRAIN_SITES,TOTAL_SITES,original_days,
    precompute_profiles,_fit_and_score
)
from .uljin_common_96bin_detector_envelope_v0 import fitted_civil_masses
from .uljin_station_season_camera_q_v0 import physical_site_q
from .uljin_within_branch_daily_q_drift_v0 import synthetic_detected_events
from .uljin_q_temporal_pooling_lipschitz_v0 import (
    groups_for_41_days,_site_result
)
try:
    from scipy.special import betaincinv
except ImportError as exc:
    raise ImportError("optional exact CP camera q source quantiles required") from exc

METHOD="uljin_camera_q_known_maintenance_step_time_pooling_v0"
WORLDS=("station_branch_stable","externally_logged_step_index20")
METHODS=("daily_source","seven_day_unaware","seven_day_maintenance_split")
BUDGETS=((32,251904),(128,1007616))
TRUTH_IDS=("fixed_clock","sunrise_sunset_tracking",
           "residual_seasonal_phase_shift")
N_LEVELS=(20,200)
PAIRS=(("solar_phase","civil_clock"),
       ("solar_phase_plus_branch","solar_phase"),
       ("solar_noon","civil_clock"),
       ("average_anchor","solar_phase"))
REF_SEED=2026101031
EVENT_SEED=2026101032
STEP_DAY=20
ALPHA=.025
N_SITE=16


def validate_contract(plan:Mapping[str,object],parent:Mapping[str,object])->None:
    f=plan.get("original_time_frame",{})
    stats=plan.get("statistical_budget",{})
    sr=plan.get("synthetic_rng",{})
    full=plan.get("full_results",{})
    worlds=plan.get("q_truth_worlds",[])
    if (not isinstance(plan,Mapping) or not isinstance(parent,Mapping)
        or plan.get("schema_version")!=1
        or plan.get("contract_id")!=METHOD
        or plan.get("stage")!=
          "FROZEN_AFTER_PR262_FIRST_SOURCE_FREE_RESULTS_BEFORE_NEW_STEP_OUTCOMES"
        or plan.get("parent_pr")!=262
        or plan.get("parent_first_ci_run")!=38045380294
        or plan.get("parent_first_ledger")!=
          "ULJIN_Q_TEMPORAL_POOLING_LIPSCHITZ_V0_FIRST_RESULT_LEDGER.json"
        or f.get("mirrored_photoperiod_pairs")!=41
        or f.get("dates")!=82
        or f.get("original_civil_15min_bins")!=96
        or f.get("physical_training_sites")!=TRAIN_SITES
        or f.get("independent_physical_heldout_sites")!=N_SITE
        or f.get("fixed_pairs")!=[list(x) for x in PAIRS]
        or f.get("animal_truths")!=list(TRUTH_IDS)
        or f.get("site_date_n")!=list(N_LEVELS)
        or [x.get("id") for x in worlds]!=list(WORLDS)
        or [x.get("step_index") for x in worlds]!=[None,STEP_DAY]
        or plan.get("reference_method_names")!=list(METHODS)
        or plan.get("equal_gold_reference_budgets")!=[
             {"per_day_per_site_branch_clock_cell":n,
              "total_gold_passages":T} for n,T in BUDGETS]
        or sr.get("reference_seed")!=REF_SEED
        or sr.get("animal_step_seed")!=EVENT_SEED
        or sr.get("station_q_original_pattern")!=1
        or stats.get("source_q_CP_simultaneous_alpha")!=ALPHA
        or stats.get("each_pair_exact_one_sided_alpha")!=.00625
        or stats.get("iid_heldout_physical_sites")!=16
        or stats.get("minimum_robust_positive_sites_for_certification")!=14
        or full.get("paired_cases")!=96
        or full.get("all_method_results")!=288
        or full.get("calibration_source_receipts")!=12
        or parent.get("record_type")!=
          "FIRST_FROZEN_ULJIN_DETECTOR_Q_TEMPORAL_POOLING_LIPSCHITZ_V0_TERMINAL_SOURCE_FREE"
        or parent.get("first_completed_scored_ci_run")!=38045380294
        or parent.get("first_result_artifact_id")!=11667303281):
        raise ValueError("frozen maintenance-q source calibration or parent modified")


def step_day_q(branch:np.ndarray,q_base:np.ndarray,
               world_index:int)->np.ndarray:
    if (branch.shape!=(82,) or q_base.shape!=(32,2,6)
        or world_index not in (0,1)
        or not np.array_equal(branch,np.tile((0,1),41))):
        raise ValueError("same mirror calendar and physical camera q required")
    original=q_base[:,branch,:]
    result=original.copy()
    if world_index==1:
        idx=np.arange(82)//2>=STEP_DAY
        result[:,idx,:]=.4+.2*original[:,idx,:]
    if result.shape!=(32,82,6) or np.any(result<=0) or np.any(result>=1):
        raise ValueError("camera hardware q step source invalid")
    return result


def source_date_groups(method:str)->tuple[tuple[int,...],...]:
    if method not in METHODS:
        raise ValueError("unknown frozen q maintenance source grouping")
    if method==METHODS[0]:
        return groups_for_41_days(1)
    groups=groups_for_41_days(7)
    if method==METHODS[1]:
        return groups
    pieces=[]
    for group in groups:
        left=tuple(i for i in group if i<STEP_DAY)
        right=tuple(i for i in group if i>=STEP_DAY)
        if left: pieces.append(left)
        if right: pieces.append(right)
    out=tuple(pieces)
    if tuple(j for group in out for j in group)!=tuple(range(41)):
        raise ValueError("externally logged break corrupted source time eligibility")
    return out


def source_reference(
    qday:np.ndarray,world_index:int,budget_index:int,
    method_index:int)->dict[str,object]:
    if (qday.shape!=(32,82,6) or world_index not in (0,1)
        or budget_index not in (0,1) or method_index not in (0,1,2)):
        raise ValueError("unknown camera source reference request")
    n_day,T=BUDGETS[budget_index]
    if T!=16*2*6*41*n_day:
        raise ValueError("reference cost not equal at every time resolution")
    method=METHODS[method_index]
    groups=source_date_groups(method)
    group_count=16*2*6*len(groups)
    tail=ALPHA/(2*group_count)
    rng=np.random.default_rng(np.random.SeedSequence([
        REF_SEED,world_index,budget_index,method_index,999]))
    low=np.empty((16,82,6),dtype=float)
    high=np.empty((16,82,6),dtype=float)
    source_covered=True
    for b in (0,1):
        for group in groups:
            days=np.array([2*j+b for j in group],dtype=int)
            true_source=qday[16:,days,:].mean(axis=1)
            independent_n=n_day*len(group)
            success=rng.binomial(independent_n,true_source)
            counts=success.astype(float)
            l=np.zeros_like(counts)
            u=np.ones_like(counts)
            positive=counts>0
            incomplete=counts<independent_n
            l[positive]=betaincinv(
                counts[positive],independent_n-counts[positive]+1,tail)
            u[incomplete]=betaincinv(
                counts[incomplete]+1,independent_n-counts[incomplete],1-tail)
            source_covered=bool(source_covered and np.all(l<=true_source)
                                and np.all(true_source<=u))
            low[:,days,:]=l[:,None,:]
            high[:,days,:]=u[:,None,:]
    daily_covered=bool(np.all(low<=qday[16:]) and np.all(qday[16:]<=high))
    admissible=(world_index==0 or method_index!=1)
    return {
        "method":method,
        "q_group_means_CP_joint_coverage_ORACLE_ONLY":source_covered,
        "individual_day_q_joint_coverage_ORACLE_ONLY":daily_covered,
        "source_iid_Binomial_for_GROUP_MEAN":True,
        "source_to_individual_date_transport_attested":admissible,
        "n_q_groups":group_count,
        "n_independent_gold_passages_per_original_day":n_day,
        "n_independent_gold_passages_total":T,
        "group_date_index_partition":groups,
        "daily_lower":low,"daily_upper":high,
        "HOLD_source_q_daily_lower_zero":bool(np.any(low<=0)),
    }


def synthetic_events(
    profiles:dict[str,np.ndarray],branch:np.ndarray,
    qday:np.ndarray,qbase:np.ndarray,
    world_index:int,truth:str,n:int
)->tuple[np.ndarray,dict[str,np.ndarray],dict[str,object]]:
    if (world_index not in (0,1) or truth not in TRUTH_IDS
        or n not in N_LEVELS or qday.shape!=(32,82,6)):
        raise ValueError("non-frozen camera maintenance wildlife scenario")
    if world_index==0:
        return synthetic_detected_events(
            profiles,branch,qday,qbase,0,truth,n)
    i=next(j for j,x in enumerate(TRUTHS) if x[0]==truth)
    _,family,peak_r,peak_f=TRUTHS[i]
    fam=profiles["solar_phase" if family=="solar_phase_plus_branch" else family]
    i0=int(np.flatnonzero(np.isclose(PEAKS,peak_r))[0])
    i1=int(np.flatnonzero(np.isclose(PEAKS,peak_f))[0])
    latent=np.stack([
        fam[d,:,i0 if b==0 else i1] for d,b in enumerate(branch)])
    q96=np.repeat(qday,16,axis=2)
    p=latent[None,:,:]*q96
    p/=p.sum(axis=2,keepdims=True)
    if p.shape!=(32,82,96) or not np.allclose(
        p.sum(axis=2),1,atol=1e-12):
        raise ValueError("invalid q maintenance day physical event law")
    rng=np.random.default_rng(
        np.random.SeedSequence([EVENT_SEED,world_index,i,n]))
    events=np.stack([
        np.stack([rng.multinomial(n,prob) for prob in site])
        for site in p
    ])
    fitted=_fit_and_score(profiles,events,branch)
    model={m:fitted_civil_masses(profiles,branch,fitted,m) for m in KINDS}
    return events[TRAIN_SITES:],model,fitted


def score_one(
    observed:np.ndarray,aa:np.ndarray,bb:np.ndarray,
    true_qday:np.ndarray,cal:Mapping[str,object]
)->dict[str,object]:
    """Frozen 16 site-majority result, without synthetic oracle admission."""
    if not cal["source_to_individual_date_transport_attested"]:
        return {
            "status":"HOLD_REFERENCE_GROUP_MEAN_NOT_VALID_FOR_STEP_DATE",
            "site_majority_certified":None,
            "robust_positive_physical_site_count":None,
            "site_binomial_p":None,
            "source_group_mean_CP_joint_coverage_ORACLE_ONLY":
                cal["q_group_means_CP_joint_coverage_ORACLE_ONLY"],
            "source_true_date_q_joint_coverage_ORACLE_ONLY":
                cal["individual_day_q_joint_coverage_ORACLE_ONLY"],
            "oracle_coverage_never_an_admission_gate":True
        }
    if observed.shape!=(16,82,96) or aa.shape!=(82,96) or bb.shape!=(82,96):
        raise ValueError("original 96-civil-bin same response missing")
    # Reuse original conservative exact site-score source intervals,
    # but do not introduce an absolute Lipschitz correction because
    # external hardware log attests CONSTANT q inside each group.
    out=_site_result(observed,aa,bb,true_qday,cal)
    return {
        "status":out["status"],
        "site_majority_certified":out.get("site_majority_certified"),
        "robust_positive_physical_site_count":out.get(
            "physical_robust_positive_site_count"),
        "site_binomial_p":out.get("exact_site_majority_p_value"),
        "source_group_mean_CP_joint_coverage_ORACLE_ONLY":
            cal["q_group_means_CP_joint_coverage_ORACLE_ONLY"],
        "source_true_date_q_joint_coverage_ORACLE_ONLY":
            cal["individual_day_q_joint_coverage_ORACLE_ONLY"],
        "true_q_positive_sites_ORACLE_ONLY":out.get(
            "true_q_positive_sites_ORACLE_ONLY"),
        "oracle_coverage_never_an_admission_gate":True,
        "daily_nuisance_box_is_CONSERVATIVE_OUTER":True
    }


def first_frozen_maintenance_panel(
    plan:Mapping[str,object],parent:Mapping[str,object],
    calendar:Mapping[str,object]
)->dict[str,object]:
    validate_contract(plan,parent)
    dates,branch=original_days(calendar)
    if len(dates)!=82 or not np.array_equal(branch,np.tile((0,1),41)):
        raise ValueError("original astronomy calendar or photoperiod branch lost")
    profile=precompute_profiles(dates)
    _,base=physical_site_q(1)
    source_receipts=[]
    comparisons=[]
    for wi,name in enumerate(WORLDS):
        qday=step_day_q(branch,base,wi)
        if wi==1 and not np.any(qday[:,38,:]!=qday[:,40,:]):
            raise ValueError("hardware source changepoint disappeared")
        for bi,(perday,total) in enumerate(BUDGETS):
            calibs=[source_reference(qday,wi,bi,mi)
                    for mi in range(len(METHODS))]
            for cal in calibs:
                source_receipts.append({
                    "camera_q_truth":name,"gold_reference_budget":total,
                    "calibration_method":cal["method"],
                    "independent_reference_trials_per_original_day":perday,
                    "simultaneous_source_group_count":cal["n_q_groups"],
                    "source_group_q_means_CP_joint_coverage_ORACLE_ONLY":
                        cal["q_group_means_CP_joint_coverage_ORACLE_ONLY"],
                    "true_target_date_q_CP_joint_coverage_ORACLE_ONLY":
                        cal["individual_day_q_joint_coverage_ORACLE_ONLY"],
                    "external_changepoint_source_scope_admissible":
                        cal["source_to_individual_date_transport_attested"],
                    "HOLD_q_lower_zero":cal["HOLD_source_q_daily_lower_zero"]
                })
            for truth in TRUTH_IDS:
                for n in N_LEVELS:
                    obs,forecasts,fit=synthetic_events(
                        profile,branch,qday,base,wi,truth,n)
                    for aa,bb in PAIRS:
                        arms={
                            cal["method"]:score_one(
                                obs,forecasts[aa],forecasts[bb],
                                qday[16:],cal)
                            for cal in calibs
                        }
                        comparisons.append({
                            "q_truth":name,
                            "reference_total_gold_passages":total,
                            "original_artificial_time_truth":truth,
                            "site_date_detected_events":n,
                            "forecast_model_A":aa,"forecast_model_B":bb,
                            "frozen_training_peak_A":fit[aa][
                                "training_only_peak_parameters"],
                            "frozen_training_peak_B":fit[bb][
                                "training_only_peak_parameters"],
                            "three_equal_cost_calibration_methods":arms
                        })
    if len(comparisons)!=96 or len(source_receipts)!=12:
        raise ValueError("all fixed changepoint reference arms must be retained")
    step_holds=sum(
        row["three_equal_cost_calibration_methods"][METHODS[1]]["status"]==
            "HOLD_REFERENCE_GROUP_MEAN_NOT_VALID_FOR_STEP_DATE"
        for row in comparisons)
    if step_holds!=48:
        raise ValueError("every maintenance step unaware seven-day source must HOLD")
    if any(x["site_majority_certified"] is True and
           x["robust_positive_physical_site_count"]<14
           for row in comparisons
           for x in row["three_equal_cost_calibration_methods"].values()):
        raise ValueError("not exact 16-physical-site majority after 4-way correction")
    return {
        "schema_version":1,
        "method":METHOD,
        "status":"SOURCE_FREE_KNOWN_MAINTENANCE_CHANGEPOINT_Q",
        "same_original_mirrored_astronomy_pairs":41,
        "original_civil_15min_response_bins":96,
        "independent_training_physical_sites":16,
        "independent_heldout_physical_sites":16,
        "simultaneous_q_reference_alpha":ALPHA,
        "four_site_majority_test_alpha_total":.025,
        "per_original_design_combined_type_I_bound":.05,
        "all_96_paired_clock_model_comparisons":comparisons,
        "all_12_reference_source_calibration_receipts":source_receipts,
        "total_predeclared_method_results":288,
        "step_world_unaware_source_HOLD_pairs":step_holds,
        "group_source_iid_binomial_valid_even_with_changepoint":True,
        "externally_documented_maintenance_changepoint_required_to_split":True,
        "no_synthetic_oracle_coverage_gating":True,
        "outer_datewise_q_profile_not_joint_sharp":True,
        "no_authentic_EcoBank_wildlife_camera_source_or_maintenance_data":True,
        "prior_ODSP_qualified_and_parent_synthetic_first_routes_unchanged":True
    }
