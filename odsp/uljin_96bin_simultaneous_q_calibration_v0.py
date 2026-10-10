"""Joint source-free camera-q calibration for the same 96 civil clock bins.

Previous PR256 used sharp mathematical q-box sensitivity, not sampling
confidence bounds. This distinct route obtains simultaneous 97.5%-coverage
Clopper-Pearson intervals from INDEPENDENT correctly labeled true-passage
reference sensors at each of 82 dates x six 4h civil blocks OR x 96
individual 15min civil bins. Equal total source reference opportunity
budgets are used for the two choices.

The four-hour calibration is valid for four-hour AVERAGE camera q even
if actual q varies inside a block. But its 4h interval MUST NOT be
treated as a confidence interval for individual quarter-hour q without
additional within-block invariance evidence. Explicitly stress that
model misspecification independently of CP sampling calibration.
"""
from __future__ import annotations

import math
from collections.abc import Mapping
import numpy as np

from .uljin_common_clock_mechanistic_comparison_v0 import (
    KINDS,TRUTHS,PEAKS,BINS,TRAIN_SITES,TOTAL_SITES,
    original_days,precompute_profiles,_fit_and_score
)
from .uljin_common_96bin_detector_envelope_v0 import (
    ratio_extrema,fitted_civil_masses
)

try:
    from scipy.special import betaincinv
except ImportError as exc:
    raise ImportError("Optional SciPy required by dedicated 96-bin q calibration workflow") from exc

METHOD="uljin_same_clock_empirical_q_96bin_joint_calibration_v0"
SEED=2026101017
TRUTH_IDS=("fixed_clock","sunrise_sunset_tracking",
           "residual_seasonal_phase_shift")
COUNTS=(20,200)
PATTERNS=("genuine_4hour_constant","within_block_quarterhour_heterogeneous")
METHODS=("six_clock_4hour_blocks","individual_96_civil_15min_bins")
BUDGETS=((251904,512,32),(1007616,2048,128))
PAIRINGS=(
 ("solar_phase","civil_clock"),
 ("solar_phase_plus_branch","solar_phase"),
 ("solar_noon","civil_clock"),
 ("average_anchor","solar_phase")
)
RISING=(.78,.75,.66,.57,.54,.65)
FALLING=(.56,.60,.74,.81,.70,.57)
ALPHA=.025


def freeze_guard(contract:Mapping[str,object],
                 prior:Mapping[str,object])->None:
    if not isinstance(contract,Mapping) or not isinstance(prior,Mapping):
        raise ValueError("source-free q calibration freeze/parent required")
    f=contract.get("calendar",{})
    q=contract.get("biological_q_truth",{})
    p=contract.get("calibration_experiment",{})
    if (
        contract.get("schema_version")!=1
        or contract.get("contract_id")!=METHOD
        or contract.get("state")!=
            "FROZEN_POST_PR256_RESULTS_BEFORE_NEW_CALIBRATION_OUTCOMES"
        or contract.get("parent_pr")!=256
        or contract.get("parent_first_result")!=
            "ULJIN_COMMON_96BIN_DETECTOR_ENVELOPE_V0_FIRST_RESULT_LEDGER.json"
        or contract.get("parent_first_ci")!=38013624606
        or f.get("original_41_day_pairs") is not True
        or f.get("local_civil_bins")!=96
        or f.get("days")!=82
        or f.get("training_sites")!=16
        or f.get("heldout_sites")!=16
        or contract.get("predeclared_worlds")!=list(TRUTH_IDS)
        or f.get("site_date_event_count_levels")!=list(COUNTS)
        or f.get("synthetic_generation_seed")!=SEED
        or q.get("rising_six_fourhour_blocks")!=list(RISING)
        or q.get("falling_six_fourhour_blocks")!=list(FALLING)
        or [w.get("id") for w in q.get("temporal_patterns",[])]!=list(PATTERNS)
        or p.get("simultaneous_detector_alpha")!=ALPHA
        or p.get("fixed_reference_budgets")!=[
            {"total_gold_standard_passage_opportunities":t,
             "per_82date_six_fourhour_block":n6,
             "per_82date_96_clock_bin":n96}
            for t,n6,n96 in BUDGETS
        ]
        or p.get("methods")!=list(METHODS)
        or contract.get("time_model_pairs")!=[list(x) for x in PAIRINGS]
        or prior.get("record_type")!=
            "FIRST_FROZEN_COMMON_CIVIL_96BIN_SHARED_DETECTOR_Q_SENSITIVITY_V0_TERMINAL_RESULT"
        or prior.get("first_scored_ci_run")!=38013624606
        or prior.get("first_scored_artifact_id")!=11655347386
    ):
        raise ValueError("frozen pre-outcome 96-bin simultaneous detector-q design altered")


def true_detector_q(branch:np.ndarray,pattern:str)->np.ndarray:
    if pattern not in PATTERNS or branch.ndim!=1 or len(branch)!=82 or (
        not np.all((branch==0)|(branch==1))):
        raise ValueError("unknown source-free detector temporal truth")
    base=np.asarray([RISING if b==0 else FALLING for b in branch])
    q=np.repeat(base,16,axis=1)
    if pattern==PATTERNS[1]:
        cycle=.13*np.sin(2*np.pi*(np.arange(16)+.5)/16)
        if abs(float(cycle.mean()))>1e-14:
            raise ValueError("within-block q heterogeneity must average zero")
        q=q+np.tile(cycle,6)[None,:]
    if q.shape!=(82,96) or not np.all((q>0)&(q<1)):
        raise ValueError("invalid camera time-specific true detection")
    return q


def _binomial_joint_cp(
    successes:np.ndarray,n:int,alpha:float
)->tuple[np.ndarray,np.ndarray]:
    """Exact two-sided CP 82*G-cells simultaneous via union bound."""
    if (
        successes.ndim!=2 or successes.shape[0]!=82
        or successes.shape[1] not in (6,96)
        or type(n) is not int or n<1
        or np.any(successes<0) or np.any(successes>n)
        or not 0<alpha<1
    ):
        raise ValueError("independent source q reference frame malformed")
    groups=successes.size
    tail=alpha/(2*groups)
    s=successes.astype(float)
    lower=np.zeros_like(s)
    upper=np.ones_like(s)
    mid=s>0
    if np.any(mid):
        lower[mid]=betaincinv(s[mid],n-s[mid]+1,tail)
    mid=s<n
    if np.any(mid):
        upper[mid]=betaincinv(s[mid]+1,n-s[mid],1-tail)
    if not (np.isfinite(lower).all() and np.isfinite(upper).all()
            and np.all((lower>=0)&(lower<=upper)&(upper<=1))):
        raise ValueError("source detector CP confidence bands invalid")
    return lower,upper


def independent_detector_calibration(
    actual_q:np.ndarray,pattern_index:int,budget_index:int,
    method_index:int
)->dict[str,object]:
    """The calibration is generated ONE time per detector truth and budget."""
    if (actual_q.shape!=(82,96)
        or not 0<=pattern_index<len(PATTERNS)
        or not 0<=budget_index<len(BUDGETS)
        or not 0<=method_index<len(METHODS)):
        raise ValueError("unknown independent q reference scenario")
    budget,n6,n96=BUDGETS[budget_index]
    if 82*6*n6!=budget or 82*96*n96!=budget:
        raise ValueError("not equal independent q reference opportunity budgets")
    method=METHODS[method_index]
    if method_index==0:
        true_group_q=actual_q.reshape(82,6,16).mean(axis=2)
        n=n6
    else:
        true_group_q=actual_q
        n=n96
    rng=np.random.default_rng(np.random.SeedSequence(
        [SEED,pattern_index,budget_index,method_index,999]))
    counts=rng.binomial(n,true_group_q)
    lower,upper=_binomial_joint_cp(counts,n,ALPHA)
    source_q_joint_coverage=bool(
        np.all(lower<=true_group_q) and np.all(true_group_q<=upper))
    detector_true_96_coverage=bool(
        np.all(np.repeat(lower,16,axis=1)<=actual_q)
        and np.all(actual_q<=np.repeat(upper,16,axis=1))
        if method_index==0 else
        np.all(lower<=actual_q) and np.all(actual_q<=upper)
    )
    hold=bool(np.any(lower<=0))
    return {
        "method":method,
        "q_lower":lower,
        "q_upper":upper,
        "number_external_calibrated_source_cells":lower.size,
        "reference_trials_per_cell":n,
        "total_external_reference_opportunities":budget,
        "simultaneous_source_q_confidence_coverage":source_q_joint_coverage,
        "simultaneous_TRUE_96_CLOCK_BIN_q_coverage":detector_true_96_coverage,
        "HOLD_some_reference_q_lower_is_zero":hold,
        "calibration_q_group_law_is_exact_binomial":True,
        "calibration_groups_may_not_reflect_quarterhour_q":(
            method_index==0 and pattern_index==1),
    }


def _frozen_heldout_observations(
    profiles:dict[str,np.ndarray],branch:np.ndarray,
    actual_q:np.ndarray,truth_id:str,n:int,
    pattern_index:int
)->tuple[np.ndarray,dict[str,np.ndarray],dict[str,object]]:
    i=next(j for j,row in enumerate(TRUTHS) if row[0]==truth_id)
    _,kind,rise,fall=TRUTHS[i]
    source=profiles["solar_phase" if kind=="solar_phase_plus_branch" else kind]
    rise_i=int(np.flatnonzero(np.isclose(PEAKS,rise))[0])
    fall_i=int(np.flatnonzero(np.isclose(PEAKS,fall))[0])
    latent=np.stack([
        source[d,:,rise_i if b==0 else fall_i]
        for d,b in enumerate(branch)])
    detected=latent*actual_q
    detected/=detected.sum(axis=1,keepdims=True)
    if (not np.isfinite(detected).all()
        or np.max(abs(detected.sum(axis=1)-1))>1e-10):
        raise ValueError("source-free true detected civil density malformed")
    rng=np.random.default_rng(np.random.SeedSequence(
        [SEED,pattern_index,i,n,722]))
    counts=np.stack([
        rng.multinomial(n,p,size=TOTAL_SITES) for p in detected
    ],axis=1)
    fitted=_fit_and_score(profiles,counts,branch)
    predictions={
        m:fitted_civil_masses(profiles,branch,fitted,m)
        for m in KINDS
    }
    return counts[TRAIN_SITES:],predictions,fitted


def shared_q_calibrated_bound(
    heldout:np.ndarray,a:np.ndarray,b:np.ndarray,
    actual_q:np.ndarray,calibration:Mapping[str,object]
)->dict[str,object]:
    """Sharp conditional SAMPLE heldout predictive score gap at shared q."""
    if (heldout.shape!=(16,82,96) or a.shape!=(82,96)
        or b.shape!=a.shape or actual_q.shape!=a.shape
        or np.any(heldout<0) or np.any(a<=0) or np.any(b<=0)):
        raise ValueError("not original 96 same civil observation cells")
    sites=heldout.sum(axis=(1,2))
    if np.any(sites<=0):
        raise ValueError("empty physical heldout site")
    weights=heldout/sites[:,None,None]/16
    weighted=weights.sum(axis=0)
    date_weight=weighted.sum(axis=1)
    term=float(np.sum(weighted*np.log(a/b)))
    true_gap=term-float(np.sum(
        date_weight*np.log(
            np.sum(a*actual_q,axis=1)/
            np.sum(b*actual_q,axis=1))))
    raw_qlo=calibration["q_lower"]
    raw_qhi=calibration["q_upper"]
    if calibration["HOLD_some_reference_q_lower_is_zero"]:
        return {
            "status":"HOLD_Q_CALIBRATION_LOWER_ZERO",
            "conditional_true_q_gap_diagnostic_only":true_gap,
            "q_reference_joint_coverage":calibration[
                "simultaneous_source_q_confidence_coverage"],
            "actual_96bin_q_is_jointly_covered":calibration[
                "simultaneous_TRUE_96_CLOCK_BIN_q_coverage"],
            "certified_model_order":None,
            "lower":None,"upper":None,
        }
    if calibration["method"]==METHODS[0]:
        aa=a.reshape(82,6,16).sum(axis=2)
        bb=b.reshape(82,6,16).sum(axis=2)
    else:
        aa,bb=a,b
    logs_lo=[]
    logs_hi=[]
    for day in range(82):
        L,U=ratio_extrema(aa[day],bb[day],
                           raw_qlo[day],raw_qhi[day])
        logs_lo.append(math.log(L))
        logs_hi.append(math.log(U))
    lower=term-float(np.dot(date_weight,logs_hi))
    upper=term-float(np.dot(date_weight,logs_lo))
    contains=bool(lower-1e-10<=true_gap<=upper+1e-10)
    # For 4h CP in the within-block nonconstant world this is NOT a
    # valid 96bin confidence set EVEN IF the interval happens to
    # contain the true sample score in this single synthetic sample.
    granularity_valid=not calibration["calibration_groups_may_not_reflect_quarterhour_q"]
    calibrated=bool(
        granularity_valid
        and calibration["simultaneous_source_q_confidence_coverage"]
        and calibration["simultaneous_TRUE_96_CLOCK_BIN_q_coverage"])
    label=("A_robustly_better" if lower>1e-12 else
           "B_robustly_better" if upper< -1e-12 else
           "INDETERMINATE")
    return {
        "status":("VALID_CALIBRATION_SCOPE_FOR_SOURCE_FREE_SAMPLE"
                  if calibrated else "UNQUALIFIED_TIME_BIN_Q_SCOPE_OR_CALIBRATION_NONCOVERAGE"),
        "conditional_true_q_gap_diagnostic_only":true_gap,
        "calibrated_q_envelope_lower_sample_gap":lower,
        "calibrated_q_envelope_upper_sample_gap":upper,
        "contains_true_q_conditional_sample_gap":contains,
        "q_reference_joint_coverage":calibration[
            "simultaneous_source_q_confidence_coverage"],
        "actual_96bin_q_is_jointly_covered":calibration[
            "simultaneous_TRUE_96_CLOCK_BIN_q_coverage"],
        "time_granularity_valid_for_actual_q":granularity_valid,
        "certified_model_order":label if calibrated else None,
        "raw_descriptive_model_order_not_inferential":label
    }


def first_calibrated_96bin_panel(
    plan:Mapping[str,object],prior:Mapping[str,object],
    calendar:Mapping[str,object]
)->dict[str,object]:
    freeze_guard(plan,prior)
    days,branch=original_days(calendar)
    profiles=precompute_profiles(days)
    report=[]
    calibration_receipts=[]
    for pi,pattern in enumerate(PATTERNS):
        q_true=true_detector_q(branch,pattern)
        for bi,(budget,n6,n96) in enumerate(BUDGETS):
            calibrations=[
                independent_detector_calibration(q_true,pi,bi,mi)
                for mi in range(len(METHODS))
            ]
            for z in calibrations:
                calibration_receipts.append({
                    "true_q_pattern":pattern,
                    "reference_budget":budget,
                    "calibration_method":z["method"],
                    "q_calibrated_cell_count":z["number_external_calibrated_source_cells"],
                    "per_cell_reference_n":z["reference_trials_per_cell"],
                    "source_q_joint_coverage":z["simultaneous_source_q_confidence_coverage"],
                    "actual_96bin_q_joint_coverage":z["simultaneous_TRUE_96_CLOCK_BIN_q_coverage"],
                    "source_binomial_law_valid":z["calibration_q_group_law_is_exact_binomial"],
                    "detector_time_granularity_misspecified":z[
                        "calibration_groups_may_not_reflect_quarterhour_q"],
                    "zero_lower_HOLD":z["HOLD_some_reference_q_lower_is_zero"]
                })
            for truth in TRUTH_IDS:
                for n in COUNTS:
                    heldout,pred,fit=_frozen_heldout_observations(
                        profiles,branch,q_true,truth,n,pi)
                    for aa,bb in PAIRINGS:
                        for z in calibrations:
                            q_result=shared_q_calibrated_bound(
                                heldout,pred[aa],pred[bb],q_true,z)
                            report.append({
                                "true_animal_time_process":truth,
                                "true_camera_q_temporal_pattern":pattern,
                                "synthetic_events_per_station_date":n,
                                "external_reference_budget":budget,
                                "calibration_clock_granularity":z["method"],
                                "model_A":aa,"model_B":bb,
                                "frozen_training_peak_A":fit[aa][
                                    "training_only_peak_parameters"],
                                "frozen_training_peak_B":fit[bb][
                                    "training_only_peak_parameters"],
                                **q_result
                            })
    if (len(report)!=192 or len(calibration_receipts)!=8):
        raise ValueError("must retain all 192 preregistered first results")
    for r in report:
        if (r["status"]=="VALID_CALIBRATION_SCOPE_FOR_SOURCE_FREE_SAMPLE"
            and not r["contains_true_q_conditional_sample_gap"]):
            raise ValueError("valid joint CP q calibration failed true q sample-score containment")
    return {
        "schema_version":1,"method":METHOD,
        "status":"SOURCE_FREE_JOINT_CP_Q_CALIBRATION_96_CIVIL_BIN_SCOPE_AUDIT",
        "original_41_calendar_pairs_retained":True,
        "physical_heldout_sites":16,
        "original_15min_clock_bins":96,
        "simultaneous_detector_calibration_alpha":ALPHA,
        "total_192_precommitted_score_envelopes":len(report),
        "all_8_q_calibration_source_coverage_receipts":calibration_receipts,
        "all_192_model_score_envelope_results":report,
        "joint_CP_coverage_not_independent_site_sampling_confidence":True,
        "four_hour_calibration_not_portable_to_15min_heterogeneous_q":True,
        "real_camera_q_references_and_original_ungulate_events_unopened":True,
        "qualified_original_ODSP_inference_routes_untouched":True
    }
