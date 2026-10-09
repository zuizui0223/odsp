"""Common-observation-space clock/astronomy/season ecological comparison.

Source-free v0. Different time coordinates MUST predict the SAME 96 local
civil-clock 15-minute observation bins with exactly the same device-operation
intervals. A candidate predicts an EVENT DENSITY per own coordinate-hour;
therefore its civil-clock density carries the exact change-of-variable
Jacobian. Comparing differently binned event log scores is forbidden.

The five families differ in astronomical mechanism, not the response:
clock, solar-noon shift, sunrise/sunset double anchoring, average anchoring,
and phase with rising-vs-falling photoperiod branch-specific peak.

Finite synthetic benchmark fits peaks ONLY on training physical sites and
scores untouched distinct whole sites. Never claims biological photoperiod
memory or accesses authentic ungulate/device records.
"""
from __future__ import annotations
from datetime import date
from collections.abc import Mapping,Sequence
import math
import numpy as np

from .uljin_photoperiod_mirror_design_v0 import generate_preoutcome_2022_mirror_calendar
from .uljin_original_pairs_equation_of_time_v0 import civil_solar_geometry

METHOD="uljin_common_clock_mechanistic_time_comparison_v0"
KINDS=("civil_clock","solar_noon","solar_phase","average_anchor",
       "solar_phase_plus_branch")
TRUTHS=(
 ("fixed_clock","civil_clock",7.5,7.5),
 ("solar_noon_tracking","solar_noon",7.5,7.5),
 ("sunrise_sunset_tracking","solar_phase",7.5,7.5),
 ("average_anchor_tracking","average_anchor",7.5,7.5),
 ("residual_seasonal_phase_shift","solar_phase_plus_branch",7.5,9.),
)
PEAKS=np.arange(0,24,.5,dtype=float)
BINS=96
KAPPA=4.
BACKGROUND=.04
NODES,WEIGHTS=np.polynomial.legendre.leggauss(8)
SEEDS=(2026100909,2026100910,2026100911)
COUNTS=(20,200)
TRAIN_SITES=16
TOTAL_SITES=32


def verify_contract(plan:Mapping[str,object])->None:
    if (
        not isinstance(plan,Mapping)
        or plan.get("schema_version")!=1
        or plan.get("contract_id")!=METHOD
        or plan.get("status")!=
            "FROZEN_SYNTHETIC_BEFORE_FIRST_MODEL_COMPARISON_OUTCOME"
        or plan.get("original_41_day_pairs_preserved") is not True
        or plan.get("candidate_models") is None
        or [item.get("id") for item in plan["candidate_models"]]!=list(KINDS)
        or plan.get("training_testing",{}).get("synthetic_physical_sites")!=32
        or plan.get("training_testing",{}).get("training_sites")!=16
        or plan.get("training_testing",{}).get("untouched_heldout_sites")!=16
        or plan.get("training_testing",{}).get(
            "event_count_per_site_date_scenarios")!=list(COUNTS)
        or plan.get("training_testing",{}).get("synthetic_seeds")!=list(SEEDS)
        or plan.get("integration",{}).get("civil_bin_width_minutes")!=15
        or plan.get("integration",{}).get("method")!=
            "8-point Gauss-Legendre separately split by device interval bounds, sunrise/sunset and civil bin edges"
        or plan.get("common_shape",{}).get("concentration_kappa")!=KAPPA
        or plan.get("common_shape",{}).get("background_relative_rate")!=BACKGROUND
        or plan.get("astronomy_context",{}).get("source_gps_qualified") is not False
        or [(x.get("id"),x.get("generating_model"),x.get("peak_rising"),
             x.get("peak_falling")) for x in plan.get("synthetic_truth_worlds",[])]!=
            list(TRUTHS)
        or plan.get("interpretation_boundaries",{}).get(
            "proof_of_original_ungulate_hysteresis") is not False
    ):
        raise ValueError("frozen common-clock ecological comparison contract changed")


def original_days(calendar:Mapping[str,object])->tuple[list[date],np.ndarray]:
    pairs=generate_preoutcome_2022_mirror_calendar(calendar)["matched_dates"]
    if (len(pairs)!=41
        or len({p["ascending_date"] for p in pairs})!=41
        or len({p["descending_date"] for p in pairs})!=41):
        raise ValueError("unmodified original 41 matched date pairs required")
    days=[date.fromisoformat(p[k]) for p in pairs
          for k in ("ascending_date","descending_date")]
    branch=np.array([b for _ in pairs for b in (0,1)],dtype=int)
    return days,branch


def geometry(day:date)->tuple[float,float,float]:
    g=civil_solar_geometry(day,36.85,129.2)
    sr,ss=g["sunrise_clock_minute"]/60,g["sunset_clock_minute"]/60
    noon=g["solar_noon_clock_minute"]/60
    if not (0<sr<noon<ss<24):
        raise ValueError("astronomical geometry out of civil daily support")
    return sr,ss,noon


def average_anchors(days:Sequence[date])->tuple[float,float]:
    arr=np.asarray([geometry(d) for d in days],dtype=float)
    return float(arr[:,0].mean()),float(arr[:,1].mean())


def coordinate_jacobian(
    t:np.ndarray,day:date,kind:str,averaged:tuple[float,float]
)->tuple[np.ndarray,np.ndarray]:
    """Map any civil-hour samples to coordinate time and J=|du/dt|."""
    if kind not in KINDS:
        raise ValueError("unknown solar clock candidate")
    sr,ss,noon=geometry(day)
    if kind=="civil_clock":
        return np.mod(t,24.),np.ones_like(t)
    if kind=="solar_noon":
        return np.mod(t-(noon-12.),24.),np.ones_like(t)
    daylen=ss-sr
    nightlen=24-daylen
    daymask=(t>=sr)&(t<ss)
    unwrapped=np.where(t>=ss,t,t+24.)
    phase=np.where(daymask,6.+12*(t-sr)/daylen,
                   np.mod(18.+12*(unwrapped-ss)/nightlen,24.))
    if kind in ("solar_phase","solar_phase_plus_branch"):
        j=np.where(daymask,12./daylen,12./nightlen)
        return phase,j
    avgsr,avgss=averaged
    avgday=avgss-avgsr
    avgnight=24-avgday
    coord=np.where(daymask,avgsr+(t-sr)*avgday/daylen,
                   np.mod(avgss+(unwrapped-ss)*avgnight/nightlen,24.))
    return coord,np.where(daymask,avgday/daylen,avgnight/nightlen)


def _validated_operation_intervals(
    intervals:Sequence[tuple[float,float]],
)->list[tuple[float,float]]:
    if not isinstance(intervals,(list,tuple)):
        raise ValueError("need independently recorded source operation chronology")
    ordered=[]
    for item in intervals:
        if not isinstance(item,(list,tuple)) or len(item)!=2:
            raise ValueError("operation interval requires start/end")
        a,b=item
        if any(isinstance(v,bool) or not isinstance(v,(int,float))
               or not math.isfinite(v) for v in (a,b)) or not 0<=a<b<=24:
            raise ValueError("invalid positive clock-time operation interval")
        ordered.append((float(a),float(b)))
    merged=[]
    for a,b in sorted(ordered):
        if merged and a<=merged[-1][1]:
            merged[-1]=(merged[-1][0],max(b,merged[-1][1]))
        else:
            merged.append((a,b))
    return merged


def civil_bin_probabilities(
    day:date,kind:str,average:tuple[float,float],
    operation_intervals:Sequence[tuple[float,float]],
    peaks:np.ndarray=PEAKS,
)->np.ndarray:
    """All 96 common clock-bin probabilities for PEAKS, same device support."""
    operations=_validated_operation_intervals(operation_intervals)
    if not operations:
        raise ValueError("HOLD_NO_POSITIVE_EXPOSURE")
    sr,ss,_=geometry(day)
    masses=np.zeros((BINS,len(peaks)),dtype=float)
    for k in range(BINS):
        a,b=k*.25,(k+1)*.25
        for op_a,op_b in operations:
            left=max(a,op_a)
            right=min(b,op_b)
            if left>=right:
                continue
            cuts=[left]+[v for v in (sr,ss) if left<v<right]+[right]
            for p,q in zip(cuts[:-1],cuts[1:]):
                t=(p+q)/2+(q-p)/2*NODES
                w=(q-p)/2*WEIGHTS
                coord,jac=coordinate_jacobian(t,day,kind,average)
                phase=2*np.pi*(coord[:,None]-peaks[None,:])/24
                rate=BACKGROUND+np.exp(KAPPA*(np.cos(phase)-1.))
                masses[k]+=np.sum((w*jac)[:,None]*rate,axis=0)
    denom=masses.sum(axis=0)
    if np.any(denom<=0) or not np.isfinite(denom).all():
        raise ValueError("zero device support or invalid normalized density")
    return masses/denom


def _support_and_logs(prob:np.ndarray,counts:np.ndarray)->np.ndarray:
    if (prob.shape!=counts.shape
        or np.any(counts<0) or not np.isfinite(counts).all()
        or np.any(prob<0) or not np.isfinite(prob).all()
        or np.any((counts>0)&(prob<=0))):
        raise ValueError("positive animal event in a zero-effort clock bin")
    return np.where(counts>0,np.log(np.maximum(prob,1e-300))*counts,0.)


def precompute_profiles(days:list[date])->dict[str,np.ndarray]:
    avg=average_anchors(days)
    models={}
    for kind in KINDS[:-1]:
        models[kind]=np.stack([
            civil_bin_probabilities(day,kind,avg,[(0.,24.)])
            for day in days],axis=0)
    # Branch candidate shares astronomical phase transform, not separate bins.
    models["solar_phase_plus_branch"]=models["solar_phase"]
    return models


def _fit_and_score(
    arrays:dict[str,np.ndarray],
    data:np.ndarray,branch:np.ndarray,
)->dict[str,object]:
    """Same heldout counts in same civil bins, irrespective of model."""
    if (data.ndim!=3 or data.shape[0]!=TOTAL_SITES or data.shape[2]!=BINS
        or data.shape[1]!=len(branch) or np.any(data<0)):
        raise ValueError("all original site×date×clock bins needed")
    total=data.sum(axis=2)
    if np.any(total<=0):
        raise ValueError("zero-count site-day requires separate effort-aware scoring")
    train=data[:TRAIN_SITES].sum(axis=0)
    results={}
    for kind in KINDS:
        p=arrays[kind]
        if p.shape!=(len(branch),BINS,len(PEAKS)):
            raise ValueError("all models must predict identical clock cells")
        scores=np.einsum("dk,dkp->p",train,np.log(np.maximum(p,1e-300)))
        if kind=="solar_phase_plus_branch":
            idx=[]
            for b in (0,1):
                group=branch==b
                branch_score=np.einsum(
                    "dk,dkp->p",train[group],np.log(np.maximum(p[group],1e-300)))
                idx.append(int(branch_score.argmax()))
            predictions=np.empty((len(branch),BINS))
            for b in (0,1):
                predictions[branch==b]=p[branch==b,:,idx[b]]
            peaks=[float(PEAKS[j]) for j in idx]
        else:
            idx=int(scores.argmax())
            predictions=p[:,:,idx]
            peaks=[float(PEAKS[idx])]
        if np.any((data[TRAIN_SITES:]>0)&
                  (predictions[None,:,:]<=0)):
            raise ValueError("model missed positive-event exposure")
        heldout=_support_and_logs(
            np.broadcast_to(predictions,data[TRAIN_SITES:].shape),
            data[TRAIN_SITES:]
        )
        site_event_count=data[TRAIN_SITES:].sum(axis=(1,2))
        site_scores=heldout.sum(axis=(1,2))/site_event_count
        results[kind]={
            "training_only_peak_parameters":peaks,
            "heldout_equal_site_logscore_nats_per_event":
                float(np.mean(site_scores)),
        }
    results["uniform_device_time"]={
        "training_only_peak_parameters":[],
        "heldout_equal_site_logscore_nats_per_event":float(-math.log(BINS))
    }
    return results


def run_frozen_common_clock_panel(
    calendar:Mapping[str,object],plan:Mapping[str,object]
)->dict[str,object]:
    verify_contract(plan)
    days,branch=original_days(calendar)
    arrays=precompute_profiles(days)
    scenarios=[]
    for truth_i,(truth,kind,rise,fall) in enumerate(TRUTHS):
        source=arrays["solar_phase" if kind=="solar_phase_plus_branch" else kind]
        idx0=int(np.flatnonzero(np.isclose(PEAKS,rise))[0])
        idx1=int(np.flatnonzero(np.isclose(PEAKS,fall))[0])
        truth_p=np.stack([source[i,:,idx0 if b==0 else idx1]
                          for i,b in enumerate(branch)])
        if np.any(truth_p<=0) or np.max(abs(truth_p.sum(axis=1)-1))>1e-10:
            raise ValueError("synthetic model truth not normalized")
        for n in COUNTS:
            for rep,seed in enumerate(SEEDS):
                rng=np.random.default_rng(np.random.SeedSequence(
                    [seed,truth_i,n]))
                data=np.stack([rng.multinomial(n,truth_p,size=TOTAL_SITES)
                               for truth_p in truth_p],axis=1)
                out=_fit_and_score(arrays,data,branch)
                candidate_scores={m:out[m][
                    "heldout_equal_site_logscore_nats_per_event"] for m in KINDS}
                winning=max(KINDS,key=lambda m:candidate_scores[m])
                for m in KINDS:
                    out[m]["improvement_over_civil_clock_nats_per_event"]=(
                        candidate_scores[m]-candidate_scores["civil_clock"])
                    out[m]["improvement_over_solar_phase_nats_per_event"]=(
                        candidate_scores[m]-candidate_scores["solar_phase"])
                scenarios.append({
                    "truth":truth,
                    "generating_model":kind,
                    "counts_per_site_date":n,
                    "world_seed":seed,
                    "trained_on_sites":TRAIN_SITES,
                    "untouched_heldout_sites":TOTAL_SITES-TRAIN_SITES,
                    "best_descriptive_heldout_model":winning,
                    "all_common_clock_heldout_scores":out,
                    "all_date_pair_events_binned_in_same_civil_cells":True,
                })
    if len(scenarios)!=len(TRUTHS)*len(COUNTS)*len(SEEDS):
        raise ValueError("frozen ecological time comparison matrix incomplete")
    return {
        "schema_version":1,
        "method":METHOD,
        "status":"SOURCE_FREE_COMMON_CLOCK_MECHANISTIC_COMPARISON_ONLY",
        "original_calendar_pairs":41,
        "candidate_models":list(KINDS),
        "common_civil_clock_bin_count":BINS,
        "scenarios":scenarios,
        "all_scenarios_kept":True,
        "formal_model_selection_pvalues_computed":False,
        "original_animal_events_or_camera_log_opened":False,
        "causal_zeitgeber_or_hysteresis_identified":False,
        "existing_qualified_ODSP_routes_unchanged":True,
    }
