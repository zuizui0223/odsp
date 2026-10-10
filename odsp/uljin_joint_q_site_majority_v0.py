"""One-sided exact independent-site majority with simultaneous detector q bands.

FROZEN source-free extension of PR257's original 96 CIVIL clock bins.
Each model pair's trained peaks, observed heldout physical sites and
independent reference Binomial q calibration are EXACTLY replayed.

The new inferential target is P(new physical site: model A's FIXED
observed-event clock-bin score exceeds model B's) > 1/2, conditional on
original training and the same 82 matched dates, not an expected logscore
mean, causal zeitgeber, latent animal rate or photoperiod memory.

For each physical site, optimize the SHARED detector q over the
independent source confidence box. Count sites that are positive for
ALL q in that box. One-sided Binomial(n=16,p=.5) majority test spends
.025/4 per original pair, while source simultaneous detector q CP
intervals spend .025. Calibration noncoverage is ALLOCATED as error;
do NOT peek at synthetic oracle truth coverage to gate decisions.
"""
from __future__ import annotations

from collections.abc import Mapping
from math import comb,log,isfinite
import numpy as np

from .uljin_common_clock_mechanistic_comparison_v0 import (
    KINDS,TRAIN_SITES,TOTAL_SITES,original_days,precompute_profiles
)
from .uljin_96bin_simultaneous_q_calibration_v0 import (
    TRUTH_IDS,COUNTS,PATTERNS,METHODS,BUDGETS,PAIRINGS,ALPHA,
    true_detector_q,independent_detector_calibration,
    _frozen_heldout_observations
)
from .uljin_common_96bin_detector_envelope_v0 import ratio_extrema

METHOD="uljin_joint_q_and_site_majority_predictive_test_v0"
N_SITE=16
ALPHA_Q=.025
ALPHA_SITES=.025
ALPHA_PER_PAIR=.00625
N_REPS=len(TRUTH_IDS)*len(COUNTS)*len(PATTERNS)*len(BUDGETS)*len(METHODS)*len(PAIRINGS)
SITE_TAIL_THRESHOLD=14


def frozen_plan_guard(plan:Mapping[str,object],parent:Mapping[str,object])->None:
    if not isinstance(plan,Mapping) or not isinstance(parent,Mapping):
        raise ValueError("frozen source-free q+site test contract absent")
    sc=plan.get("sampling",{})
    err=plan.get("error_allocation",{})
    scope=plan.get("temporal_source_scope",{})
    report=plan.get("reporting",{})
    if (
        plan.get("schema_version")!=1
        or plan.get("contract_id")!=METHOD
        or plan.get("status")!="PRE_OUTCOME_FROZEN_AFTER_96BIN_CP_FIRST_RESULTS"
        or plan.get("parent_pr")!=257
        or plan.get("parent_first_completed_workflow")!=38014370170
        or plan.get("parent_first_result")!=
            "ULJIN_96BIN_SIMULTANEOUS_Q_CALIBRATION_V0_FIRST_RESULT_LEDGER.json"
        or sc.get("calendar_original_41_matched_pairs") is not True
        or sc.get("local_civil_bins")!=96
        or sc.get("calendar_dates")!=82
        or sc.get("training_sites")!=TRAIN_SITES
        or sc.get("independent_heldout_sites")!=N_SITE
        or sc.get("site_event_counts_each_date")!=list(COUNTS)
        or sc.get("synthetic_worlds")!=list(TRUTH_IDS)
        or sc.get("detector_true_patterns")!=list(PATTERNS)
        or sc.get("reference_budgets")!=[z[0] for z in BUDGETS]
        or sc.get("q_calibration_methods")!=list(METHODS)
        or sc.get("fixed_pairs")!=[list(x) for x in PAIRINGS]
        or err.get("q_reference_joint_noncoverage_alpha")!=ALPHA_Q
        or err.get("site_majority_four_comparisons_alpha_total")!=ALPHA_SITES
        or err.get("site_majority_each_of_four_pairwise_one_sided_alpha")!=ALPHA_PER_PAIR
        or err.get("overall_fwer_per_predeclared_scenario")!=.05
        or scope.get("coverage_leak_prevention")!=
           "Whether true q was contained in the ACTUAL randomly sampled CP reference interval is an ORACLE outcome audit only, NEVER a prerequisite for an inferential label. Selection based on realized coverage is infeasible in real research and breaks nominal coverage interpretation."
        or report.get("rows_expected")!=N_REPS
        or report.get("true_heterogeneous_4hour_scope_held_rows")!=48
        or report.get("other_valid_scope_rows")!=144
        or parent.get("record_type")!=
           "FIRST_FROZEN_ULJIN_82DAY_SIMULTANEOUS_CP_Q_COMMON_CLOCK_96BIN_V0"
        or parent.get("first_complete_ci_run")!=38014370170
        or parent.get("first_artifact_id")!=11654423645
    ):
        raise ValueError("frozen source-free q+site exact majority route changed")


def exact_site_majority_right_tail(k:int,n:int=N_SITE)->float:
    """Exact nonrandomized p-value under P(site A improves)<=1/2."""
    if (type(k) is not int or type(n) is not int or n!=N_SITE or not 0<=k<=n):
        raise ValueError("original 16 independent physical sites required")
    return sum(comb(n,j) for j in range(k,n+1))/(2**n)


def sitewise_shared_q_score_bounds(
    heldout:np.ndarray,a:np.ndarray,b:np.ndarray,
    actual_q:np.ndarray,calibration:Mapping[str,object]
)->dict[str,object]:
    """Sharp each-site sample forecast A-B gap over SAME 82×clock q box.

    The calibration's oracle true-q joint coverage is an AUDIT field,
    *never* used to set an inference decision or qualify a confidence
    interval from the observed calibration data.
    """
    if (heldout.shape!=(N_SITE,82,96)
        or a.shape!=(82,96) or b.shape!=(82,96)
        or actual_q.shape!=(82,96)
        or not np.isfinite(a).all() or not np.isfinite(b).all()
        or np.any(a<=0) or np.any(b<=0)
        or np.any(heldout<0) or not np.isfinite(heldout).all()
        or calibration["method"] not in METHODS):
        raise ValueError("same 96 original civil bins and 16 sites required")
    n_by_site_day=heldout.sum(axis=2).astype(float)
    n_by_site=n_by_site_day.sum(axis=1)
    if np.any(n_by_site<=0):
        raise ValueError("zero-event physical sites need a separately qualified method")
    events=np.einsum(
        "sdk,dk->s",heldout,np.log(a/b)
    )/n_by_site
    true_norm=np.log(
        (a*actual_q).sum(axis=1)/(b*actual_q).sum(axis=1))
    true_score=events-(n_by_site_day@true_norm)/n_by_site
    nominal=events-np.sum(
        n_by_site_day*np.log(a.sum(axis=1)/b.sum(axis=1))[None,:],
        axis=1
    )/n_by_site
    granular_valid=not calibration["calibration_groups_may_not_reflect_quarterhour_q"]
    if not granular_valid:
        return {
            "admission_status":"HOLD_TIME_RESOLUTION_NOT_ADMISSIBLE",
            "robust_site_positive_count":None,
            "exact_site_majority_p_value":None,
            "inferential_site_majority_decision":None,
            "source_q_joint_coverage_ORACLE_AUDIT_ONLY":calibration[
                "simultaneous_source_q_confidence_coverage"],
            "true_96bin_q_joint_coverage_ORACLE_AUDIT_ONLY":calibration[
                "simultaneous_TRUE_96_CLOCK_BIN_q_coverage"],
            "true_q_site_score_diagnostics":[float(x) for x in true_score],
            "nominal_q_constant_site_score_diagnostics":[float(x) for x in nominal],
            "true_q_site_positive_count_ORACLE_ONLY":int((true_score>1e-12).sum()),
            "oracle_coverage_never_used_as_decision_gate":True,
        }
    if calibration["HOLD_some_reference_q_lower_is_zero"]:
        return {
            "admission_status":"HOLD_Q_REFERENCE_LOWER_ZERO",
            "robust_site_positive_count":None,
            "exact_site_majority_p_value":None,
            "inferential_site_majority_decision":None,
            "source_q_joint_coverage_ORACLE_AUDIT_ONLY":calibration[
                "simultaneous_source_q_confidence_coverage"],
            "true_96bin_q_joint_coverage_ORACLE_AUDIT_ONLY":calibration[
                "simultaneous_TRUE_96_CLOCK_BIN_q_coverage"],
            "true_q_site_score_diagnostics":[float(x) for x in true_score],
            "nominal_q_constant_site_score_diagnostics":[float(x) for x in nominal],
            "true_q_site_positive_count_ORACLE_ONLY":int((true_score>1e-12).sum()),
            "oracle_coverage_never_used_as_decision_gate":True,
        }
    if calibration["method"]==METHODS[0]:
        aa=a.reshape(82,6,16).sum(axis=-1)
        bb=b.reshape(82,6,16).sum(axis=-1)
    else:
        aa,bb=a,b
    lo_q,hi_q=calibration["q_lower"],calibration["q_upper"]
    lowlog=[]
    highlog=[]
    for d in range(82):
        low,high=ratio_extrema(aa[d],bb[d],lo_q[d],hi_q[d])
        if not 0<low<=high+1e-12:
            raise ValueError("bad shared q conditional normalizer ratio")
        lowlog.append(log(low))
        highlog.append(log(high))
    lowlog=np.array(lowlog)
    highlog=np.array(highlog)
    lower=events-(n_by_site_day@highlog)/n_by_site
    upper=events-(n_by_site_day@lowlog)/n_by_site
    if np.any(lower>upper+1e-10):
        raise ValueError("sitewise source confidence intervals reversed")
    k=int(np.sum(lower>1e-12))
    p=exact_site_majority_right_tail(k)
    certified=bool(p<ALPHA_PER_PAIR)
    # The above decision does NOT depend on actual_q, oracle
    # coverage, or which synthetic animal process generated the data.
    in_q=bool(calibration["simultaneous_TRUE_96_CLOCK_BIN_q_coverage"])
    if in_q and (np.any(true_score<lower-1e-10)
                 or np.any(true_score>upper+1e-10)):
        raise ValueError("covered true 96-clock detector q must lie in sitewise envelope")
    return {
        "admission_status":"SOURCE_TEMPORAL_SCOPE_VALID_Q_CI_FOR_SITE_TEST",
        "robust_site_positive_count":k,
        "exact_site_majority_p_value":p,
        "site_majority_alpha_bonferroni":ALPHA_PER_PAIR,
        "inferential_site_majority_decision":(
            "A_BETTER_AT_MAJORITY_OF_NEW_SITES_CERTIFIED"
            if certified else "NOT_CERTIFIED_FOR_NEW_SITE_MAJORITY"),
        "fixed_training_and_all_82_original_dates":True,
        "independent_heldout_physical_sites":N_SITE,
        "sitewise_robust_lower":[float(v) for v in lower],
        "sitewise_robust_upper":[float(v) for v in upper],
        "source_q_joint_coverage_ORACLE_AUDIT_ONLY":calibration[
            "simultaneous_source_q_confidence_coverage"],
        "true_96bin_q_joint_coverage_ORACLE_AUDIT_ONLY":in_q,
        "true_q_site_score_diagnostics":[float(x) for x in true_score],
        "nominal_q_constant_site_score_diagnostics":[float(x) for x in nominal],
        "true_q_site_positive_count_ORACLE_ONLY":int((true_score>1e-12).sum()),
        "q_interval_contained_true_q_site_scores_ORACLE_ONLY":bool(np.all(
            (true_score>=lower-1e-10)&(true_score<=upper+1e-10))),
        "oracle_coverage_never_used_as_decision_gate":True,
    }


def frozen_site_majority_full_panel(
    plan:Mapping[str,object],parent:Mapping[str,object],
    calendar:Mapping[str,object]
)->dict[str,object]:
    frozen_plan_guard(plan,parent)
    days,branch=original_days(calendar)
    if len(days)!=82 or len(branch)!=82:
        raise ValueError("41 astronomy pairs were reselected")
    profiles=precompute_profiles(days)
    results=[]
    external_calibration_checks=[]
    for pi,pattern in enumerate(PATTERNS):
        q=true_detector_q(branch,pattern)
        for bi,(budget,n6,n96) in enumerate(BUDGETS):
            cals=[independent_detector_calibration(q,pi,bi,m)
                  for m in range(2)]
            for cal in cals:
                external_calibration_checks.append({
                    "pattern":pattern,"budget":budget,"method":cal["method"],
                    "source_q_coverage_ORACLE_ONLY":cal[
                        "simultaneous_source_q_confidence_coverage"],
                    "true_clock_q_coverage_ORACLE_ONLY":cal[
                        "simultaneous_TRUE_96_CLOCK_BIN_q_coverage"],
                    "q_interval_lower_zero":cal["HOLD_some_reference_q_lower_is_zero"],
                    "calibration_temporal_scope_assumed_correct":
                        not cal["calibration_groups_may_not_reflect_quarterhour_q"]
                })
            for truth in TRUTH_IDS:
                for n in COUNTS:
                    data,forecast,fit=_frozen_heldout_observations(
                        profiles,branch,q,truth,n,pi)
                    for A,B in PAIRINGS:
                        for cal in cals:
                            result=sitewise_shared_q_score_bounds(
                                data,forecast[A],forecast[B],q,cal)
                            results.append({
                                "truth_time_process":truth,
                                "true_camera_q_temporal_pattern":pattern,
                                "synthetic_events_per_site_date":n,
                                "reference_opportunities_total":budget,
                                "reference_calibration_time_structure":cal["method"],
                                "ordered_model_A":A,"ordered_model_B":B,
                                "training_only_peak_A":fit[A][
                                    "training_only_peak_parameters"],
                                "training_only_peak_B":fit[B][
                                    "training_only_peak_parameters"],
                                **result
                            })
    if len(results)!=N_REPS or len(external_calibration_checks)!=8:
        raise ValueError("full original 192 source-free site tests required")
    rejected=[r for r in results if r["inferential_site_majority_decision"]==
              "A_BETTER_AT_MAJORITY_OF_NEW_SITES_CERTIFIED"]
    if any(r["robust_site_positive_count"]<SITE_TAIL_THRESHOLD
           for r in rejected):
        raise ValueError("not exact conservative 16-site binomial sign test")
    if sum(r["admission_status"]=="HOLD_TIME_RESOLUTION_NOT_ADMISSIBLE"
           for r in results)!=48:
        raise ValueError("heterogeneous q four-hour source scope must HOLD")
    return {
        "schema_version":1,
        "method":METHOD,
        "status":"SOURCE_FREE_JOINT_Q_AND_INDEPENDENT_SITE_MAJORITY_TEST_ONLY",
        "original_astronomical_matched_date_pairs":41,
        "same_civil_15min_time_bins":96,
        "training_physical_sites":16,
        "independent_heldout_physical_sites":16,
        "calibration_familywise_noncoverage_alpha":ALPHA_Q,
        "all_four_site_majority_tests_familywise_alpha":ALPHA_SITES,
        "each_site_majority_one_sided_alpha":ALPHA_PER_PAIR,
        "combined_per_scenario_false_certification_alpha_bound":ALPHA_Q+ALPHA_SITES,
        "exact_sign_p_for_13_of_16":exact_site_majority_right_tail(13),
        "exact_sign_p_for_14_of_16":exact_site_majority_right_tail(14),
        "all_eight_first_source_calibration_audits":external_calibration_checks,
        "all_192_predefined_source_free_q_and_site_cases":results,
        "total_predeclared_cases":len(results),
        "source_q_oracle_coverage_not_an_operational_admission_condition":True,
        "new_site_majority_probability_not_mean_expected_site_score":True,
        "per_design_not_simultaneously_over_all_192_truth_worlds":True,
        "independent_gold_reference_labels_and_independent_new_sites_ASSUMED":True,
        "real_original_EcoBank_wildlife_camera_or_external_reference_NOT_opened":True,
        "prior_qualified_ODSP_inference_routes_unchanged":True
    }
