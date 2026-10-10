"""Gold-standard source calibration at distinct WITHIN-SEASON clock-day blocks.

All four designs observe the SAME exact number of independently labeled
true passages, stratified by 16 heldout physical cameras, original 2
rising/falling daylength branches and six original CIVIL four-hour bins.
Source group lengths 1/3/7/41 each sample passage date independently
UNIFORMLY among its predeclared group days. A pooled success is thereby
genuinely IID Bernoulli(group mean q), not a Poisson-binomial sample
with fixed heterogeneous date counts.

EXTERNAL pre-specified Lipschitz |q_(j+1)-q_j|<=L converts a group-mean
CP interval to its constituent daily q interval by enlarging each
side by L*(group length-1)/2. This is an absolute probability bound,
NOT a measured empirical time-series model in original EcoBank.

Fix the trained five temporal models and independent physical sites,
use SAME original 96 CIVIL 15-minute event bins, and test per-site
positive q-robust score gaps via exact Binomial(16,.5) at .025/4,
with source simultaneous group-q Clopper-Pearson alpha=.025.

All source-free, no animal, source uptime, sensor references or GPS read.
"""
from __future__ import annotations

from collections.abc import Mapping
import math
import numpy as np

from .uljin_common_clock_mechanistic_comparison_v0 import (
    KINDS,TRAIN_SITES,original_days,precompute_profiles
)
from .uljin_station_season_camera_q_v0 import (
    physical_site_q,calibrate_site_q,vectorized_source_ratio_bounds
)
from .uljin_within_branch_daily_q_drift_v0 import (
    true_daily_q,synthetic_detected_events
)
from .uljin_joint_q_site_majority_v0 import exact_site_majority_right_tail

try:
    from scipy.special import betaincinv
except ImportError as exc:
    raise ImportError("optional SciPy required for exact grouped q CP calibration") from exc

METHOD="uljin_q_reference_time_block_resolution_lipschitz_v0"
LENGTHS=(1,3,7,41)
PATTERNS=(("branch_stationary",0.,0.),
          ("daily_cosine_drift",.35,.03))
DAILY_COUNTS=(32,128)
TOTALS=(251904,1007616)
REF_SEED=2026101029
TRUTH_IDS=("fixed_clock","sunrise_sunset_tracking","residual_seasonal_phase_shift")
EVENT_COUNTS=(20,200)
PAIRS=(
 ("solar_phase","civil_clock"),
 ("solar_phase_plus_branch","solar_phase"),
 ("solar_noon","civil_clock"),
 ("average_anchor","solar_phase")
)
ALPHA_Q=.025
ALPHA_SITE_EACH=.00625
N_SITE=16


def validate_contract(plan:Mapping[str,object],parent:Mapping[str,object])->None:
    q=plan.get("uniform_reference_opportunities",{})
    s=plan.get("statistical_procedure",{})
    obs=plan.get("original_observation_contract",{})
    rep=plan.get("reporting",{})
    actual_parent=parent.get("scenario_counts",[])
    if (
        not isinstance(plan,Mapping) or not isinstance(parent,Mapping)
        or plan.get("schema_version")!=1
        or plan.get("contract_id")!=METHOD
        or plan.get("stage")!=
            "FROZEN_AFTER_PR261_FIRST_SOURCE_FREE_OUTCOME_BEFORE_NEW_TEMPORAL_POOLING_OUTPUT"
        or plan.get("parent_pr")!=261
        or plan.get("parent_first_workflow_run")!=38035769887
        or plan.get("parent_first_result_ledger")!=
            "ULJIN_WITHIN_BRANCH_DAILY_Q_DRIFT_V0_FIRST_RESULT_LEDGER.json"
        or obs.get("astronomy_mirror_pairs")!=41
        or obs.get("dates")!=82
        or obs.get("original_civil_15minute_bins")!=96
        or obs.get("training_physical_sites")!=16
        or obs.get("independent_heldout_physical_sites")!=N_SITE
        or obs.get("site_branch_clock_reference_cells")!=192
        or obs.get("four_pairs")!=[list(x) for x in PAIRS]
        or obs.get("animal_generating_truths")!=list(TRUTH_IDS)
        or obs.get("event_count_per_site_date")!=list(EVENT_COUNTS)
        or [dict(x) for x in plan.get("q_data_generating_worlds",[])]!=[
            {"id":name,"amplitude":amp,
             "external_absolute_Lipschitz_cap_per_original_pair_day":L}
            for name,amp,L in PATTERNS]
        or q.get("reference_seed")!=REF_SEED
        or q.get("time_pooling_lengths")!=list(LENGTHS)
        or q.get("reference_budgets")!=[
            {"n_independent_true_passages_per_day_per_original_site_branch_clock_block":n,
             "total_independent_true_passages":T}
            for n,T in zip(DAILY_COUNTS,TOTALS)]
        or s.get("q_joint_alpha")!=ALPHA_Q
        or s.get("site_majority_alpha_each_fixed_model_pair")!=ALPHA_SITE_EACH
        or s.get("combined_per_selected_design_alpha_with_truthful_external_L_and_iid_sites")!=.05
        or rep.get("paired_model_cases")!=96
        or rep.get("q_time_pooling_methods_per_case")!=4
        or rep.get("total_q_source_calibrated_score_results")!=384
        or rep.get("external_q_reference_receipts")!=16
        or parent.get("record_type")!=
            "FIRST_FROZEN_WITHIN_BRANCH_DAILY_CAMERA_Q_DRIFT_V0_TERMINAL_SOURCE_FREE"
        or parent.get("first_scored_workflow_run")!=38035769887
        or parent.get("first_source_free_artifact_id")!=11663816059
        or len(actual_parent)!=8
        or not parent.get("parent_PR260_branch_specific_first_13_of_48_site_majority_positive_replayed")
    ):
        raise ValueError("frozen q source block-length design or parent lineage mismatch")


def groups_for_41_days(length:int)->tuple[tuple[int,...],...]:
    if length not in LENGTHS:
        raise ValueError("unfrozen per-branch independent passage date partition")
    chunks=tuple(tuple(range(j,min(41,j+length)))
                 for j in range(0,41,length))
    if tuple(j for group in chunks for j in group)!=tuple(range(41)):
        raise ValueError("original 41 days lost/duplicated")
    return chunks


def pooled_source_reference(
    day_q:np.ndarray,pattern_index:int,budget_index:int,
    length:int
)->dict[str,object]:
    if (
        day_q.shape!=(32,82,6) or pattern_index not in (0,1)
        or budget_index not in (0,1) or length not in LENGTHS
    ):
        raise ValueError("source 32×82×6 q and fixed calibration length required")
    n_day=DAILY_COUNTS[budget_index]
    total=TOTALS[budget_index]
    if total!=16*2*6*41*n_day:
        raise ValueError("source total gold reference opportunities mismatched")
    groups=groups_for_41_days(length)
    n_cells=16*2*len(groups)*6
    tail=ALPHA_Q/(2*n_cells)
    rng=np.random.default_rng(
        np.random.SeedSequence(
            [REF_SEED,pattern_index,budget_index,length,999]))
    _,_,L=PATTERNS[pattern_index]
    day_lo=np.empty((16,82,6),dtype=float)
    day_hi=np.empty((16,82,6),dtype=float)
    coverage=True
    for branch in (0,1):
        for g in groups:
            dates=np.array([2*j+branch for j in g],dtype=int)
            actual=day_q[16:,dates,:]
            group_mean=actual.mean(axis=1)
            trials=n_day*len(g)
            source_counts=rng.binomial(trials,group_mean)
            k=source_counts.astype(float)
            lower=np.zeros_like(k)
            upper=np.ones_like(k)
            nonzero=k>0
            incomplete=k<trials
            lower[nonzero]=betaincinv(
                k[nonzero],trials-k[nonzero]+1,tail)
            upper[incomplete]=betaincinv(
                k[incomplete]+1,trials-k[incomplete],1-tail)
            coverage=coverage and bool(
                np.all(lower<=group_mean)&np.all(group_mean<=upper))
            margin=L*(len(g)-1)/2
            day_lo[:,dates,:]=np.maximum(0.,lower[:,None,:]-margin)
            day_hi[:,dates,:]=np.minimum(1.,upper[:,None,:]+margin)
    true_coverage=bool(
        np.all((day_lo<=day_q[16:])&(day_q[16:]<=day_hi)))
    q_lower_zero=bool(np.any(day_lo<=0))
    return {
        "partition_days":length,
        "group_count_per_branch":len(groups),
        "n_source_groups_simultaneous":n_cells,
        "total_reference_opportunities":total,
        "source_passage_opportunities_each_original_day":n_day,
        "q_group_means_CP_joint_coverage_ORACLE_ONLY":coverage,
        "individual_day_q_joint_coverage_ORACLE_ONLY":true_coverage,
        "external_abs_adjacent_day_L_assumed":L,
        "daily_lower":day_lo,
        "daily_upper":day_hi,
        "HOLD_source_q_daily_lower_zero":q_lower_zero,
        "source_date_iid_uniform_for_every_passage":True,
        "all_original_41_dates_retained":True,
    }


def _site_result(
    events:np.ndarray,A:np.ndarray,B:np.ndarray,
    real_qday:np.ndarray,cal:Mapping[str,object]
)->dict[str,object]:
    if (events.shape!=(16,82,96) or A.shape!=(82,96) or B.shape!=(82,96)
        or real_qday.shape!=(16,82,6) or np.any(events<0)
        or np.any(A<=0) or np.any(B<=0)):
        raise ValueError("not original 16 independent sites×82 dates×96 clock bins")
    n_date=events.sum(axis=2)
    n_site=n_date.sum(axis=1)
    if np.any(n_site<=0):
        raise ValueError("zero-count physical site")
    a=A.reshape(82,6,16).sum(axis=2)
    b=B.reshape(82,6,16).sum(axis=2)
    term=np.einsum("sdk,dk->s",events,np.log(A/B))/n_site
    qtrue_ratio=(a[None,:,:]*real_qday).sum(axis=2)/(
        b[None,:,:]*real_qday).sum(axis=2)
    true_score=term-(n_date*np.log(qtrue_ratio)).sum(axis=1)/n_site
    true_pos=int(np.sum(true_score>1e-12))
    if cal["HOLD_source_q_daily_lower_zero"]:
        return {
            "status":"HOLD_Q_REFERENCE_LOWER_ZERO",
            "physical_robust_positive_site_count":None,
            "site_majority_certified":None,
            "exact_site_majority_p_value":None,
            "true_q_positive_sites_ORACLE_ONLY":true_pos,
            "joint_group_mean_q_coverage_ORACLE_ONLY":
                cal["q_group_means_CP_joint_coverage_ORACLE_ONLY"],
            "oracle_coverage_not_a_decision_gate":True
        }
    q_lo=cal["daily_lower"]
    q_hi=cal["daily_upper"]
    ratios_min,ratios_max=vectorized_source_ratio_bounds(
        a,b,q_lo,q_hi)
    lower=term-(n_date*np.log(ratios_max)).sum(axis=1)/n_site
    upper=term-(n_date*np.log(ratios_min)).sum(axis=1)/n_site
    if np.any(lower>upper+1e-10):
        raise ValueError("daily q score outer interval reversed")
    # ONLY verify structural implication of coverage, never use
    # coverage to admit or reject an actual physical site test.
    if cal["q_group_means_CP_joint_coverage_ORACLE_ONLY"]:
        if not cal["individual_day_q_joint_coverage_ORACLE_ONLY"]:
            raise ValueError("externally attested L + covered source group mean must cover every day q")
    if cal["individual_day_q_joint_coverage_ORACLE_ONLY"] and (
        np.any(true_score<lower-1e-10) or np.any(true_score>upper+1e-10)
    ):
        raise ValueError("actual daily q is outside legitimate outer score bound")
    k=int(np.sum(lower>1e-12))
    exact_p=exact_site_majority_right_tail(k)
    return {
        "status":"VALID_SYNTHETIC_EXTERNAL_L_GROUP_Q_BOUNDS",
        "physical_robust_positive_site_count":k,
        "exact_site_majority_p_value":exact_p,
        "site_majority_certified":bool(exact_p<ALPHA_SITE_EACH),
        "true_q_positive_sites_ORACLE_ONLY":true_pos,
        "joint_group_mean_q_coverage_ORACLE_ONLY":
            cal["q_group_means_CP_joint_coverage_ORACLE_ONLY"],
        "true_individual_day_q_coverage_ORACLE_ONLY":
            cal["individual_day_q_joint_coverage_ORACLE_ONLY"],
        "oracle_coverage_not_a_decision_gate":True,
        "daywise_frozen_q_outer_score_lower":[float(x) for x in lower],
        "daywise_frozen_q_outer_score_upper":[float(x) for x in upper],
        "q_time_trajectory_extremum_conservative_outer_not_sharp":True
    }


def full_frozen_temporal_pooling_panel(
    plan:Mapping[str,object],parent:Mapping[str,object],
    calendar:Mapping[str,object]
)->dict[str,object]:
    validate_contract(plan,parent)
    dates,branch=original_days(calendar)
    if len(dates)!=82 or len(branch)!=82:
        raise ValueError("modified original 41 astronomy pairs")
    profiles=precompute_profiles(dates)
    types,source_mean=physical_site_q(1)
    all_comparisons=[]
    ref_receipts=[]
    for wi,(world,amp,L) in enumerate(PATTERNS):
        daily_q=true_daily_q(branch,source_mean,types,amp)
        # External Lipschitz guarantee is fixed from the frozen synthetic
        # generator, not inferred from animal events or CP oracle coverage.
        d0=daily_q[:,0::2,:]
        d1=daily_q[:,1::2,:]
        observed_max=float(max(np.abs(np.diff(d0,axis=1)).max(),
                               np.abs(np.diff(d1,axis=1)).max()))
        if observed_max>L+1e-12:
            raise ValueError("independently assumed external Lipschitz cap fails physical q truth")
        for bi,(n_day,total) in enumerate(zip(DAILY_COUNTS,TOTALS)):
            calibrations={length:pooled_source_reference(
                daily_q,wi,bi,length) for length in LENGTHS}
            for length,cal in calibrations.items():
                ref_receipts.append({
                    "q_true_world":world,
                    "independent_source_budget":total,
                    "source_q_temporal_pool_days":length,
                    "external_Lipschitz_q_abs_per_day":L,
                    "maximum_true_q_abs_adjacent_day_diagnostic_only":
                        observed_max,
                    "reference_group_count":cal["n_source_groups_simultaneous"],
                    "reference_independent_trials_each_day":n_day,
                    "source_iid_group_mean_q_covered_ORACLE_ONLY":
                        cal["q_group_means_CP_joint_coverage_ORACLE_ONLY"],
                    "real_target_day_q_covered_ORACLE_ONLY":
                        cal["individual_day_q_joint_coverage_ORACLE_ONLY"],
                    "q_interval_zero_lower_HOLD":cal["HOLD_source_q_daily_lower_zero"],
                    "total_source_passage_opportunities":cal[
                        "total_reference_opportunities"]
                })
            for truth in TRUTH_IDS:
                for n in EVENT_COUNTS:
                    obs,forecast,fit=synthetic_detected_events(
                        profiles,branch,daily_q,source_mean,wi,truth,n)
                    for A,B in PAIRS:
                        per_method={
                            str(length):_site_result(
                                obs,forecast[A],forecast[B],
                                daily_q[16:],calibrations[length])
                            for length in LENGTHS
                        }
                        all_comparisons.append({
                            "q_true_world":world,
                            "independent_source_budget":total,
                            "animal_time_truth":truth,
                            "synthetic_events_per_site_date":n,
                            "ordered_forecast_A":A,"ordered_forecast_B":B,
                            "frozen_training_peak_A":fit[A][
                                "training_only_peak_parameters"],
                            "frozen_training_peak_B":fit[B][
                                "training_only_peak_parameters"],
                            "four_predeclared_grouped_q_calibration_results":
                                per_method
                        })
    if len(ref_receipts)!=16 or len(all_comparisons)!=96:
        raise ValueError("all 384 original source-free score comparisons not retained")
    if any(set(r["four_predeclared_grouped_q_calibration_results"])!=
           set(map(str,LENGTHS)) for r in all_comparisons):
        raise ValueError("original 4 reference time scales were dropped")
    return {
        "schema_version":1,
        "method":METHOD,
        "status":"SOURCE_FREE_SOURCE_Q_TEMPORAL_POOLING_LIPSCHITZ_FULL_V0",
        "matched_original_mirror_date_pairs":41,
        "same_civil_15min_clock_bins":96,
        "independent_heldout_physical_sites":16,
        "qmean_simultaneous_group_CP_alpha":ALPHA_Q,
        "four_exact_site_sign_tests_familywise_alpha":.025,
        "site_majority_each_pair_one_sided_alpha":ALPHA_SITE_EACH,
        "per_original_selected_design_false_certification_alpha_with_external_L":.05,
        "all_first_96_model_cases_x_four_q_temporal_scales":all_comparisons,
        "all_16_external_q_reference_calibration_receipts":ref_receipts,
        "total_predeclared_time_pooling_results":384,
        "source_q_group_mean_binomial_exact_under_independent_uniform_reference_dates":True,
        "individual_day_q_bounds_require_independent_external_Lipschitz_cap":True,
        "source_true_q_oracle_coverage_not_used_for_model_inference":True,
        "conservative_outer_not_sharp_over_temporally_linked_daily_q":True,
        "prior_ODSP_qualified_routes_and_parent_PR261_first_ledger_unchanged":True,
        "real_original_EcoBank_animals_camera_operation_reference_true_passages_unavailable":True,
    }
