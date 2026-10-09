"""Out-of-family source-free ecological clock sensitivity and detector alias.

Every truth world is scored using the EXACT same pre-existing v0
civil-clock 96-bin and 16/16 physical-site train/heldout framework.
Two distinct causal/ecological accounts (seasonal activity shift versus
season-dependent camera detection sensitivity) have IDENTICAL observed
conditional civil-bin laws. Their synthetic observed counts are paired
identically, proving nonidentification even when heldout prediction
is excellent. This is not an empirical wildlife result.
"""
from __future__ import annotations

import hashlib
import json
import numpy as np
from collections.abc import Mapping

from .uljin_common_clock_mechanistic_comparison_v0 import (
    KINDS,PEAKS,BINS,TRAIN_SITES,TOTAL_SITES,
    original_days,precompute_profiles,_fit_and_score,
)

ID="uljin_common_clock_out_of_family_ecological_controls_v1"
TRUTHS=("bimodal_sunrise_sunset","mixed_clock_and_solar",
        "real_seasonal_activity","seasonal_detector_only",
        "weak_seasonal_phase_shift")
COUNTS=(20,200)
SEEDS=(2026100912,2026100913,2026100914)


def _check_contract(plan:Mapping[str,object],ledger:Mapping[str,object])->None:
    if (
        not isinstance(plan,Mapping)
        or plan.get("schema_version")!=1
        or plan.get("contract_id")!=ID
        or plan.get("status")!="FROZEN_POST_V0_RESULTS_BEFORE_NEW_TRUTH_OUTCOMES"
        or plan.get("parent_pr")!=245
        or plan.get("common_clock_bins")!=96
        or plan.get("original_calendar_pairs")!=41
        or plan.get("candidates_unchanged")!=list(KINDS)
        or plan.get("training_sites")!=16 or plan.get("heldout_sites")!=16
        or plan.get("site_date_event_counts")!=list(COUNTS)
        or plan.get("seeds")!=list(SEEDS)
        or [p.get("id") for p in plan.get("truth_worlds",[])]!=list(TRUTHS)
        or plan.get("provenance",{}).get("original_EcoBank_zip_verified") is not False
        or ledger.get("record_type")!=
            "FIRST_FROZEN_COMMON_CIVIL_CLOCK_ECOLOGICAL_MODEL_COMPARISON_V0"
        or ledger.get("first_ci_run")!=37863548863
        or ledger.get("worlds")!=30
    ):
        raise ValueError("frozen out-of-family ecological control changed")


def truth_probabilities(
    model_arrays:dict[str,np.ndarray],
    branches:np.ndarray,
    kind:str
)->tuple[np.ndarray,dict[str,object]]:
    """Known observed 15-minute clock-bin law; all source-free."""
    if kind not in TRUTHS:
        raise ValueError("unfrozen ecological truth")
    peakidx=lambda h:int(np.flatnonzero(np.isclose(PEAKS,h))[0])
    ph=model_arrays["solar_phase"]
    clock=model_arrays["civil_clock"]
    p0=ph[:,:,peakidx(7.5)]
    if kind=="bimodal_sunrise_sunset":
        out=.5*ph[:,:,peakidx(6.)]+.5*ph[:,:,peakidx(18.)]
    elif kind=="mixed_clock_and_solar":
        out=.5*clock[:,:,peakidx(7.5)]+.5*p0
    elif kind=="weak_seasonal_phase_shift":
        out=np.stack([
            ph[i,:,peakidx(7.5 if b==0 else 8.)]
            for i,b in enumerate(branches)])
    else:
        target=np.stack([
            ph[i,:,peakidx(7.5 if b==0 else 9.)]
            for i,b in enumerate(branches)])
        if kind=="real_seasonal_activity":
            out=target
        else:
            # Explicit ecological versus detector observational equivalence:
            # latent animal phase remains constant p0, while bin-specific
            # detection sensitivity q rescales the latent EVENT density to
            # precisely the observed seasonal pattern. q in (0,1].
            rate_ratio=target/p0
            scale=rate_ratio.max(axis=1,keepdims=True)
            q=rate_ratio/scale
            if (np.any(q<=0) or np.any(q>1+1e-12)
                or not np.allclose(
                    p0*q/np.sum(p0*q,axis=1,keepdims=True),
                    target,atol=1e-12,rtol=0)):
                raise ValueError("detector-only observational-equivalence proof failed")
            # Preserve the EXACT same observed law after proving the\n            # detection-factorization equivalence above.\n            out=target.copy()
    if (out.shape!=(len(branches),BINS) or np.any(out<=0)
        or np.max(abs(out.sum(axis=1)-1))>1e-10):
        raise ValueError("out-of-family common clock law not normalized")
    return out,{
        "latent_animal_phase_stable_across_branches":
            kind in ("seasonal_detector_only","bimodal_sunrise_sunset"),
        "detection_probability_branch_time_varies":
            kind=="seasonal_detector_only",
        "observed_seasonal_branch_shift_without_identified_cause":
            kind in ("real_seasonal_activity","seasonal_detector_only",
                     "weak_seasonal_phase_shift"),
    }


def predicted_from_frozen_fit(
    arrays:dict[str,np.ndarray],branches:np.ndarray,
    family:str,parameters:list[float]
)->np.ndarray:
    p=arrays[family]
    if family=="solar_phase_plus_branch":
        if len(parameters)!=2:
            raise ValueError("seasonal model must fit both branch peaks")
        out=np.empty((len(branches),BINS))
        for branch in (0,1):
            idx=int(np.flatnonzero(np.isclose(PEAKS,parameters[branch]))[0])
            out[branches==branch]=p[branches==branch,:,idx]
        return out
    if len(parameters)!=1:
        raise ValueError("invariant candidate has one training peak")
    idx=int(np.flatnonzero(np.isclose(PEAKS,parameters[0]))[0])
    return p[:,:,idx]


def score_frozen_out_of_family(
    original_calendar:Mapping[str,object],
    frozen:Mapping[str,object],
    first_parent_ledger:Mapping[str,object]
)->dict[str,object]:
    _check_contract(frozen,first_parent_ledger)
    days,branch=original_days(original_calendar)
    arrays=precompute_profiles(days)
    truth_laws={k:truth_probabilities(arrays,branch,k)
                for k in TRUTHS}
    a=truth_laws["real_seasonal_activity"][0]
    b=truth_laws["seasonal_detector_only"][0]
    if not np.allclose(a,b,rtol=0,atol=1e-12):
        raise ValueError("observational equivalent ecological accounts differ")
    scenarios=[]
    for ti,kind in enumerate(TRUTHS):
        probs,traits=truth_laws[kind]
        for n in COUNTS:
            for seed in SEEDS:
                # Distinct causal worlds 2 and 3 share the same data-generating
                # observed event law AND the same RNG; identical synthetic
                # recorded detections are required, not just equal averages.
                rng_index=2 if kind in (
                    "real_seasonal_activity","seasonal_detector_only"
                ) else ti
                rng=np.random.default_rng(
                    np.random.SeedSequence([seed,rng_index,n]))
                observations=np.stack([
                    rng.multinomial(n,dist,size=TOTAL_SITES)
                    for dist in probs],axis=1)
                digest=hashlib.sha256(
                    np.ascontiguousarray(observations,dtype=np.int64).tobytes()
                ).hexdigest()
                fitted=_fit_and_score(arrays,observations,branch)
                regrets={}
                for family in KINDS:
                    p=predicted_from_frozen_fit(
                        arrays,branch,family,
                        fitted[family]["training_only_peak_parameters"])
                    values=np.sum(probs*np.log(probs/p),axis=1)
                    regret=float(values.mean())
                    if regret < -1e-10:
                        raise ValueError("true KL regret must not be negative")
                    regrets[family]=max(0.,regret)
                predictive={k:fitted[k][
                    "heldout_equal_site_logscore_nats_per_event"] for k in KINDS}
                scenarios.append({
                    "truth_world":kind,
                    "counts_per_site_date":n,
                    "seed":seed,
                    "synthetic_observed_counts_digest":digest,
                    "latent_process_attributes":traits,
                    "all_common_96bin_heldout_scores":predictive,
                    "all_trained_model_peaks":{
                        k:fitted[k]["training_only_peak_parameters"]
                        for k in KINDS},
                    "all_expected_conditional_KL_regrets_nats_per_event":regrets,
                    "best_descriptive_heldout_family":max(
                        KINDS,key=lambda k:predictive[k]),
                    "best_population_regret_family":min(
                        KINDS,key=lambda k:regrets[k])
                })
    if len(scenarios)!=len(TRUTHS)*len(COUNTS)*len(SEEDS):
        raise ValueError("all out-of-family worlds must be reported")
    by={(v["truth_world"],v["counts_per_site_date"],v["seed"]):
        v["synthetic_observed_counts_digest"] for v in scenarios}
    for n in COUNTS:
        for seed in SEEDS:
            if by["real_seasonal_activity",n,seed]!=by[
                    "seasonal_detector_only",n,seed]:
                raise ValueError("paired detector and animal truths produced different observed events")
    return {
        "schema_version":1,
        "method":ID,
        "status":"SOURCE_FREE_ECOLOGICAL_MISSPECIFICATION_AND_DETECTION_ALIAS",
        "original_frozen_astronomical_day_pairs":41,
        "same_96_civil_bins_and_site_split_as_parent":True,
        "parent_candidate_models_unchanged":list(KINDS),
        "all_30_synthetic_scenarios":scenarios,
        "seasonal_biological_shift_and_detector_only_observed_laws_exactly_equal":True,
        "seasonal_biological_shift_and_detector_only_observed_counts_exactly_equal_with_paired_rng":True,
        "holding_out_stations_cannot_identify_animal_vs_detector_cause_alone":True,
        "real_ecological_source_or_camera_operation_accessed":False,
        "biological_causality_claimed":False,
        "earlier_qualified_ODSP_results_unchanged":True,
    }
