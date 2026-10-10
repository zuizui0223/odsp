"""Sharp shared-detector-q bounds on matched civil-clock predictive log scores.

All candidate time-anchoring models predict the SAME original 96 quarter-
hour civil bins. A candidate's already device-integrated civil mass m[k]
is distorted by UNKNOWN common detector sensitivity q[k] into

    p_m[k | q] = m[k] q[k] / sum_j m[j] q[j].

For a fixed event table, candidate A vs B logscore difference cancels
q in every event-specific log ratio. Only the ratio of two normalizers
depends on q. Extremize Z_A/Z_B *JOINTLY with the same q*, as a
linear-fractional program, using sharp monotone root signs. This is
not the invalid procedure that optimizes each model independently.

This is a deterministic SET-IDENTIFICATION/sensitivity result conditional
on external q bounds, not a sampling confidence interval or real data.
"""
from __future__ import annotations

from collections.abc import Mapping
import math
import numpy as np

from .uljin_common_clock_mechanistic_comparison_v0 import (
    KINDS,TRUTHS,PEAKS,BINS,TRAIN_SITES,TOTAL_SITES,
    original_days,precompute_profiles,_fit_and_score
)

METHOD="uljin_common_civil_96_detector_envelope_v0"
TRUTH_IDS=("fixed_clock","sunrise_sunset_tracking",
           "residual_seasonal_phase_shift")
N_LEVELS=(20,200)
SEED=2026101008
DELTAS=(0.,.02,.05,.1,.2)
BOXES=("independent_civil_96bins","fixed_civil_6blocks")
PAIRS=(
    ("solar_phase","civil_clock"),
    ("solar_phase_plus_branch","solar_phase"),
    ("solar_noon","civil_clock"),
    ("average_anchor","solar_phase"),
)
MAX_ITER=65


def verify_frozen(plan:Mapping[str,object],parent:Mapping[str,object])->None:
    if not isinstance(plan,Mapping) or not isinstance(parent,Mapping):
        raise ValueError("source-free 96-bin contract and parent needed")
    f=plan.get("data_frame",{})
    d=plan.get("physical_detector_model",{})
    m=plan.get("mathematics",{})
    if (
        plan.get("schema_version")!=1
        or plan.get("contract_id")!=METHOD
        or plan.get("stage")!=
           "FROZEN_AFTER_255_RESULTS_BEFORE_NEW_96_BIN_SCORE_OUTCOMES"
        or plan.get("parent_pr")!=255
        or plan.get("parent_first_result")!=
           "ULJIN_Q_W_VARIANCE_BUDGET_V0_FIRST_RESULT_LEDGER.json"
        or plan.get("first_parent_ci")!=38013040523
        or f.get("original_41_mirrored_date_pairs") is not True
        or f.get("civil_bin_count")!=BINS
        or f.get("civil_bin_minutes")!=15
        or f.get("independent_training_physical_sites")!=TRAIN_SITES
        or f.get("untouched_heldout_physical_sites")!=TOTAL_SITES-TRAIN_SITES
        or f.get("days")!=82
        or f.get("generated_truths")!=list(TRUTH_IDS)
        or f.get("events_per_site_date")!=list(N_LEVELS)
        or f.get("source_generating_seed")!=SEED
        or plan.get("fixed_pairwise_comparisons")!=[list(x) for x in PAIRS]
        or d.get("q_near")!=.9 or d.get("q_far")!=.3
        or d.get("reference_near_fraction")!=.5
        or d.get("delta_grid")!=list(DELTAS)
        or [x.get("id") for x in
            d.get("two_external_constraint_classes",[])]!=list(BOXES)
        or m.get("sharp_extrema")!=
           "For positive masses a_k,b_k, q group g lower<=q_g<=upper, extrema of (sum_g A_g q_g)/(sum_g B_g q_g) are attained at group endpoint vertices. Solve fractional-linear roots via signed-coefficient extrema and 65 deterministic bisections; optimize common q not two independent denominators."
        or plan.get("limitations",{}).get(
            "no_q_calibration_joint_96bin_confidence_intervals") is not True
        or parent.get("record_type")!=
           "FIRST_FROZEN_ULJIN_Q_W_VARIANCE_BUDGET_V0_TERMINAL_SOURCE_FREE"
        or parent.get("first_ci_run")!=38013040523
        or parent.get("first_artifact_id")!=11655326146
    ):
        raise ValueError("frozen 96-bin detector envelope or previous receipt changed")


def ratio_extrema(
    a:np.ndarray,b:np.ndarray,
    lower:np.ndarray,upper:np.ndarray
)->tuple[float,float]:
    """Sharp min/max (a·q)/(b·q) over q∈[lower,upper].

    Every a,b strictly positive; lower>0 ensures normalizers positive.
    The fractional objective is quasimonotone, so its sharp
    optima lie at q lower/upper vertices. For min, the signed
    residual min_q (a-rb)·q crosses zero at the unique ratio min;
    the max residual gives the max. Exactly 65 bisections.
    """
    a,b,lower,upper=(np.asarray(x,dtype=float) for x in
                      (a,b,lower,upper))
    if (a.ndim!=1 or any(x.shape!=a.shape for x in (b,lower,upper))
        or len(a)<1 or not all(np.isfinite(x).all()
                               for x in (a,b,lower,upper))
        or np.any(a<=0) or np.any(b<=0)
        or np.any(lower<=0) or np.any(lower>upper)
        or np.any(upper>1)):
        raise ValueError("fractional q envelope needs positive common finite support")
    component_ratio=a/b
    low=float(np.min(component_ratio))
    high=float(np.max(component_ratio))
    if high==low:
        return low,high
    def root(is_min:bool)->float:
        lo,hi=low,high
        for _ in range(MAX_ITER):
            r=(lo+hi)/2.
            coef=a-r*b
            q=np.where(coef>=0,lower if is_min else upper,
                       upper if is_min else lower)
            g=float(np.dot(coef,q))
            if is_min:
                if g>0:
                    lo=r
                else:
                    hi=r
            else:
                if g>0:
                    lo=r
                else:
                    hi=r
        return float((lo+hi)/2)
    return root(True),root(False)


def normalize_q_groups(
    a:np.ndarray,b:np.ndarray,structure:str
)->tuple[np.ndarray,np.ndarray]:
    if a.shape!=(BINS,) or b.shape!=(BINS,):
        raise ValueError("all observed time families must use same 96 civil bins")
    if structure=="independent_civil_96bins":
        return a,b
    if structure=="fixed_civil_6blocks":
        return (a.reshape(6,16).sum(axis=1),
                b.reshape(6,16).sum(axis=1))
    raise ValueError("unfrozen detector response granularity")


def fitted_civil_masses(
    profiles:dict[str,np.ndarray],branch:np.ndarray,
    fit:dict[str,object],kind:str
)->np.ndarray:
    if kind not in KINDS or kind not in fit or kind not in profiles:
        raise ValueError("unrecognized frozen fitted time family")
    means=profiles[kind]
    nday=len(branch)
    if means.shape!=(nday,BINS,len(PEAKS)):
        raise ValueError("event-time model lacks original 96 civil bins")
    peaks=fit[kind]["training_only_peak_parameters"]
    if kind=="solar_phase_plus_branch":
        if len(peaks)!=2:
            raise ValueError("photoperiod branch family must have two fitted peaks")
        out=np.empty((nday,BINS))
        for which in (0,1):
            selected=int(np.flatnonzero(np.isclose(PEAKS,peaks[which]))[0])
            out[branch==which]=means[branch==which,:,selected]
    else:
        if len(peaks)!=1:
            raise ValueError("station-invariant family must have one fitted peak")
        selected=int(np.flatnonzero(np.isclose(PEAKS,peaks[0]))[0])
        out=means[:,:,selected]
    if np.any(out<=0) or np.max(np.abs(out.sum(axis=1)-1))>1e-10:
        raise ValueError("fitted civil masses not positive and normalized")
    return out


def site_equal_pair_bound(
    counts:np.ndarray,a:np.ndarray,b:np.ndarray,
    delta:float,structure:str
)->dict[str,object]:
    """Exact q-box range for A-B equal-heldout-physical-site log score.

    One common q for ALL 16 heldout sites on a given date, independent
    between the 82 dates. Counts are the ORIGINAL shared clock bins.
    The frozen trained predicted masses are held fixed (not q-refit).
    """
    if (counts.ndim!=3 or counts.shape[0]!=16 or counts.shape[2]!=BINS
        or a.shape!=(counts.shape[1],BINS) or b.shape!=a.shape
        or np.any(counts<0) or np.any(a<=0) or np.any(b<=0)
        or not math.isfinite(delta) or delta not in DELTAS):
        raise ValueError("invalid original heldout same-clock response frame")
    site_n=counts.sum(axis=(1,2))
    if np.any(site_n<=0):
        raise ValueError("source frame contains empty heldout physical-site count")
    # each heldout physical site receives EQUAL 1/16 weight, regardless
    # of its event total; no recomputation of training peaks.
    weights=counts/site_n[:,None,None]/len(site_n)
    weighted=weights.sum(axis=0)
    date_n=weighted.sum(axis=1)
    event_term=float(np.sum(weighted*np.log(a/b)))
    baseline=event_term-float(np.sum(date_n*np.log(a.sum(axis=1)/b.sum(axis=1))))
    assert abs(float(date_n.sum())-1)<1e-10
    # External target near w=.5 ± delta maps q=.6 ± .6*delta.
    qlo=.6-.6*delta
    qhi=.6+.6*delta
    normalizer_min=0.
    normalizer_max=0.
    for d in range(len(a)):
        aa,bb=normalize_q_groups(a[d],b[d],structure)
        low,high=ratio_extrema(
            aa,bb,np.full(len(aa),qlo),np.full(len(aa),qhi))
        if not 0<low<=high+1e-12:
            raise ValueError("invalid joint detector q normalizer ratio")
        normalizer_min+=float(date_n[d])*math.log(low)
        normalizer_max+=float(date_n[d])*math.log(high)
    lower=event_term-normalizer_max
    upper=event_term-normalizer_min
    if not lower-1e-10<=baseline<=upper+1e-10:
        raise ValueError("baseline q must be within shared detector sensitivity envelope")
    status=("A_robustly_better" if lower>1e-12 else
            "B_robustly_better" if upper< -1e-12 else
            "INDETERMINATE")
    return {
        "q_target_near_mix_max_deviation":delta,
        "q_common_detector_structure":structure,
        "baseline_nominal_common_q_logscore_gap_nats_per_event":baseline,
        "exact_shared_q_lower_logscore_gap_nats_per_event":lower,
        "exact_shared_q_upper_logscore_gap_nats_per_event":upper,
        "fixed_fitted_models_predictive_order":status,
        "common_q_not_reoptimized_per_model":True,
        "day_shared_q_across_heldout_physical_sites":True,
        "source_free_conditional_sensitivity_not_confidence_interval":True,
    }


def frozen_full_96bin_panel(
    plan:Mapping[str,object],
    parent:Mapping[str,object],
    calendar:Mapping[str,object]
)->dict[str,object]:
    verify_frozen(plan,parent)
    days,branch=original_days(calendar)
    profiles=precompute_profiles(days)
    all_results=[]
    for truth_id in TRUTH_IDS:
        truth_i=next(i for i,x in enumerate(TRUTHS) if x[0]==truth_id)
        _,kind,rise,fall=TRUTHS[truth_i]
        source=profiles["solar_phase" if kind=="solar_phase_plus_branch" else kind]
        k0=int(np.flatnonzero(np.isclose(PEAKS,rise))[0])
        k1=int(np.flatnonzero(np.isclose(PEAKS,fall))[0])
        true_prob=np.stack([
            source[d,:,k0 if int(branch[d])==0 else k1]
            for d in range(len(days))])
        if not np.allclose(true_prob.sum(axis=1),1,atol=1e-10):
            raise ValueError("original synthetic truth not normalized")
        for n in N_LEVELS:
            rng=np.random.default_rng(
                np.random.SeedSequence([SEED,truth_i,n]))
            count=np.stack([
                rng.multinomial(n,p,size=TOTAL_SITES)
                for p in true_prob],axis=1)
            fit=_fit_and_score(profiles,count,branch)
            predictions={
                m:fitted_civil_masses(profiles,branch,fit,m)
                for m in KINDS
            }
            heldout=count[TRAIN_SITES:]
            for a,b in PAIRS:
                nominal=(
                    fit[a]["heldout_equal_site_logscore_nats_per_event"]-
                    fit[b]["heldout_equal_site_logscore_nats_per_event"])
                rows=[]
                for structure in BOXES:
                    for delta in DELTAS:
                        item=site_equal_pair_bound(
                            heldout,predictions[a],predictions[b],
                            delta,structure)
                        if abs(item[
                            "baseline_nominal_common_q_logscore_gap_nats_per_event"
                        ]-nominal)>1e-10:
                            raise ValueError("failed exact replay of PR245 same-clock score")
                        rows.append(item)
                for structure in BOXES:
                    subset=[r for r in rows if r["q_common_detector_structure"]==structure]
                    subset.sort(key=lambda z:z["q_target_near_mix_max_deviation"])
                    for old,new in zip(subset,subset[1:]):
                        if (new["exact_shared_q_lower_logscore_gap_nats_per_event"]>
                            old["exact_shared_q_lower_logscore_gap_nats_per_event"]+1e-10
                            or new["exact_shared_q_upper_logscore_gap_nats_per_event"]<
                            old["exact_shared_q_upper_logscore_gap_nats_per_event"]-1e-10):
                            raise ValueError("detector sensitivity envelopes must nest")
                for delta in DELTAS:
                    full=next(r for r in rows if r["q_common_detector_structure"]==BOXES[0]
                              and r["q_target_near_mix_max_deviation"]==delta)
                    block=next(r for r in rows if r["q_common_detector_structure"]==BOXES[1]
                               and r["q_target_near_mix_max_deviation"]==delta)
                    if (full["exact_shared_q_lower_logscore_gap_nats_per_event"]>
                        block["exact_shared_q_lower_logscore_gap_nats_per_event"]+1e-10
                        or full["exact_shared_q_upper_logscore_gap_nats_per_event"]<
                        block["exact_shared_q_upper_logscore_gap_nats_per_event"]-1e-10):
                        raise ValueError("six-block q restriction must nest inside 96-bin box")
                all_results.append({
                    "true_model":truth_id,
                    "synthetic_events_per_site_date":n,
                    "pre_frozen_rng_seed":SEED,
                    "comparator_A":a,"comparator_B":b,
                    "training_only_fitted_peaks":{
                        a:fit[a]["training_only_peak_parameters"],
                        b:fit[b]["training_only_peak_parameters"]
                    },
                    "nominal_original_clock_scoring_A_minus_B":nominal,
                    "all_10_q_envelopes":rows
                })
    expected=len(TRUTH_IDS)*len(N_LEVELS)*len(PAIRS)
    if len(all_results)!=expected or any(
        len(z["all_10_q_envelopes"])!=len(DELTAS)*len(BOXES)
        for z in all_results):
        raise ValueError("all frozen 240 q envelope comparisons must be preserved")
    return {
        "schema_version":1,
        "method":METHOD,
        "status":"SOURCE_FREE_SHARP_COMMON_96_CLOCK_BIN_Q_SCORE_ENVELOPES",
        "matched_astronomical_calendar_pairs":41,
        "original_clock_bins":BINS,
        "physical_heldout_sites":TOTAL_SITES-TRAIN_SITES,
        "scored_pairwise_model_cases":len(all_results),
        "total_frozen_reported_q_envelopes":expected*len(DELTAS)*len(BOXES),
        "every_fixed_model_pair_case":all_results,
        "q_bounds_depend_on_unmeasured_external_target_distance_mix":True,
        "sharp_linear_fractional_bounds_not_statistical_CI":True,
        "training_models_frozen_not_refit_for_uncertain_q":True,
        "same_q_for_competing_models_and_same_clock_outcomes":True,
        "no_original_species_events_operation_logs_or_calibration_q_used":True,
        "original_ODSP_qualified_routes_unchanged":True,
    }
