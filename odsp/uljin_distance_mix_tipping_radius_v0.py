"""Partial identification of seasonal encounter timing under UNKNOWN distance mix.

The external reference population has fixed 50/50 near and far passages.
Independent TARGET wildlife near proportions may lie anywhere inside
[.5-delta,.5+delta] in EACH of four preselected season×solar-phase cells.

Even an exact camera q for each distance group does not recover animal
encounter timing without bounding those four target proportions.

Compute exact worst-case detector odds ratio B(delta), then the exact
conditional Fisher 97.5% one-sided lower animal encounter OR, with
alpha_cal=.025 for eight jointly calibrated q and alpha_animal=.025.
The delta-radius is NOT calibrated by wildlife data in this v0.
"""
from __future__ import annotations

import math
from collections.abc import Mapping
import numpy as np

from .uljin_detector_bias_robust_or_v0 import (
    FourCells, exact_lower_bound_count_OR, upper_tail
)
from .uljin_q_transport_distance_mix_v0 import (
    cp_band,mixed_detector_q_bounds,detector_gamma_upper,
    q_effective, detector_crossproduct
)

METHOD="uljin_distance_mix_tipping_radius_v0"
ALPHA_Q=.025
ALPHA_ANIMAL=.025
DELTAS=(0.,.05,.1,.15,.2,.3)
NS=(50,200,1000,5000)
NEAR=(.9,)*4
FAR=(.3,)*4
REF=(.5,)*4
OBSERVATIONS=(
 ("no_season_shift",(40,40,40,40),(4.,4.,4.,4.)),
 ("weak_shift",(80,80,100,60),(4.,4.,4.,4.)),
 ("strong_shift",(200,200,280,120),(4.,4.,4.,4.)),
 ("unequal_effort_algebra_only",(40,40,80,40),(4.,4.,8.,4.)),
 ("observed_OR_2_generic",(80,80,160,80),(4.,4.,4.,4.))
)


def frozen_guard(plan:Mapping[str,object],parent:Mapping[str,object])->None:
    if (
        not isinstance(plan,Mapping)
        or plan.get("schema_version")!=1
        or plan.get("contract_id")!=METHOD
        or plan.get("stage")!=
            "FROZEN_POST_PARENT_RESULTS_BEFORE_FIRST_RADIUS_OUTPUT"
        or plan.get("parent_pr")!=252
        or plan.get("parent_first_ledger")!=
            "ULJIN_IID_REFERENCE_Q_TRANSPORT_V1_FIRST_RESULT_LEDGER.json"
        or plan.get("delta_grid")!=list(DELTAS)
        or plan.get("calibration_n_per_eight_distance_q_cells")!=list(NS)
        or plan.get("synthetic_detector_truth",{}).get("near_q")!=list(NEAR)
        or plan.get("synthetic_detector_truth",{}).get("far_q")!=list(FAR)
        or plan.get("synthetic_detector_truth",{}).get("reference_near_fraction")!=list(REF)
        or plan.get("synthetic_observed_tables")!=[
            {"id":name,"counts":list(counts),"operating_hours":list(hrs)}
            for name,counts,hrs in OBSERVATIONS]
        or plan.get("combined_error_bound",{}).get("calibration_q_alpha")!=ALPHA_Q
        or plan.get("combined_error_bound",{}).get("animal_test_alpha")!=ALPHA_ANIMAL
        or plan.get("combined_error_bound",{}).get(
            "external_delta_bounds_are_deterministic_and_valid") is not True
        or plan.get("status_limitations",{}).get("no_actual_target_mix_bound") is not True
        or parent.get("record_type")!=
            "FIRST_FROZEN_VALID_IID_SOURCE_Q_DISTANCE_MIX_TRANSPORT_V1_TERMINAL_RESULT"
        or parent.get("first_full_ci_run")!=37896989425
    ):
        raise ValueError("frozen target distance mix radius contract/provenance modified")


def source_q_bounds(
    source:str,n:int|None
)->tuple[np.ndarray,np.ndarray,np.ndarray,np.ndarray]:
    if source=="oracle":
        if n is not None:
            raise ValueError("oracle calibration has no n")
        near=np.asarray(NEAR)
        far=np.asarray(FAR)
        return near.copy(),near.copy(),far.copy(),far.copy()
    if source!="exact_CP" or n not in NS:
        raise ValueError("unsupported precommitted reference q calibration")
    successes=tuple(int(round(n*z)) for z in (*NEAR,*FAR))
    lower,upper=cp_band(successes,n,ALPHA_Q)
    if lower.shape!=(8,) or upper.shape!=(8,):
        raise ValueError("eight calibrated q cells required")
    return lower[:4],upper[:4],lower[4:],upper[4:]


def q_envelope(
    delta:float,
    q_bounds:tuple[np.ndarray,np.ndarray,np.ndarray,np.ndarray],
)->tuple[np.ndarray,np.ndarray]:
    if (not isinstance(delta,(float,int)) or isinstance(delta,bool)
        or not math.isfinite(delta) or not 0<=delta<=.49):
        raise ValueError("external distance mix radius must be in [0,0.49]")
    wlo=np.full(4,max(0.,.5-delta))
    whi=np.full(4,min(1.,.5+delta))
    return mixed_detector_q_bounds(*q_bounds,wlo,whi)


def oracle_B_formula(delta:float)->float:
    if not 0<=delta<=.49:
        raise ValueError("oracle radius out of scope")
    return ((1+delta)/(1-delta))**2


def result_at_delta(
    table:FourCells, detected_or_lower:float,
    delta:float, qbounds:tuple[np.ndarray,np.ndarray,np.ndarray,np.ndarray],
)->dict[str,object]:
    lo,hi=q_envelope(delta,qbounds)
    B=detector_gamma_upper(lo,hi)
    effort=table.effort_OR
    if math.isfinite(B):
        p=upper_tail(table,effort*B)
        robust_lower=detected_or_lower/(effort*B)
    else:
        p=1.
        robust_lower=0.
    return {
        "target_near_mix_half_width_delta":delta,
        "max_detector_OR_from_q_and_target_mix":B if math.isfinite(B) else None,
        "robust_exact_one_sided_p_under_latent_OR_le_1":p,
        "one_sided_97p5pct_lower_latent_encounter_OR":robust_lower,
        "certifies_positive_with_both_calibration_and_count_alpha":
            bool(math.isfinite(B) and p<ALPHA_ANIMAL),
        "HOLD_if_unknown_positive_detector_lower":not math.isfinite(B),
    }


def certified_delta_supremum(
    table:FourCells,lower_count_OR:float,
    qbounds:tuple[np.ndarray,np.ndarray,np.ndarray,np.ndarray],
)->float|None:
    """Largest allowed deterministic external delta in [0,.49] as a limit.

    At equality exact p=alpha, and nonrandomized p<alpha is not
    certified; the output is a SUPREMUM and not included boundary.
    """
    low=result_at_delta(table,lower_count_OR,0.,qbounds)
    if low["one_sided_97p5pct_lower_latent_encounter_OR"]<=1+1e-12:
        return None
    high=result_at_delta(table,lower_count_OR,.49,qbounds)
    if high["one_sided_97p5pct_lower_latent_encounter_OR"]>1:
        return .49
    lo,hi=0.,.49
    for _ in range(48):
        mid=(lo+hi)/2
        ans=result_at_delta(table,lower_count_OR,mid,qbounds)
        if ans["one_sided_97p5pct_lower_latent_encounter_OR"]>1:
            lo=mid
        else:
            hi=mid
    return lo


def run_frozen_distance_radius(
    plan:Mapping[str,object],parent:Mapping[str,object]
)->dict[str,object]:
    frozen_guard(plan,parent)
    oracle=source_q_bounds("oracle",None)
    sampled={n:source_q_bounds("exact_CP",n) for n in NS}
    rows=[]
    for name,counts,hours in OBSERVATIONS:
        t=FourCells(counts,hours)
        lower=exact_lower_bound_count_OR(t,alpha=ALPHA_ANIMAL)
        frontier_input=lower/t.effort_OR
        analytic_oracle_delta=(
            (math.sqrt(frontier_input)-1)/(math.sqrt(frontier_input)+1)
            if frontier_input>1 else None
        )
        by_source=[]
        for label,n,bounds in [("oracle",None,oracle)]+[
            ("exact_CP_representative",n,sampled[n]) for n in NS
        ]:
            c=certified_delta_supremum(t,lower,bounds)
            deltas=[result_at_delta(t,lower,delta,bounds) for delta in DELTAS]
            for before,after in zip(deltas,deltas[1:]):
                if (after["one_sided_97p5pct_lower_latent_encounter_OR"]>
                    before["one_sided_97p5pct_lower_latent_encounter_OR"]+1e-12
                    or after["robust_exact_one_sided_p_under_latent_OR_le_1"]+1e-12<
                    before["robust_exact_one_sided_p_under_latent_OR_le_1"]):
                    raise ValueError("external q/mix sensitivity monotonicity violated")
            if label=="oracle":
                for delta,r in zip(DELTAS,deltas):
                    if abs(r["max_detector_OR_from_q_and_target_mix"]-
                           oracle_B_formula(delta))>1e-12:
                        raise ValueError("oracle detector radius formula does not match corners")
                if (analytic_oracle_delta is None)!=(c is None):
                    raise ValueError("oracle one-sided tipping result disagreement")
                if c is not None and abs(c-analytic_oracle_delta)>1e-9:
                    raise ValueError("oracle analytic tipping radius not reproduced")
            by_source.append({
                "q_calibration_source":label,
                "q_reference_trial_opportunities_per_eight_q_cell":n,
                "q_intervals_observed_in_field":False,
                "critical_delta_supremum_or_null_if_delta0_fails":c,
                "all_predeclared_radius_results":deltas,
            })
        rows.append({
            "hypothetical_observed_table":name,
            "hypothetical_detected_event_counts":list(counts),
            "hypothetical_device_exposure_hours":list(hours),
            "raw_observed_count_OR":t.observed_count_OR,
            "device_hour_effort_OR":t.effort_OR,
            "exact_one_sided_97p5pct_detected_count_OR_lower":lower,
            "oracle_target_mix_tipping_delta_analytic_or_null":analytic_oracle_delta,
            "source_q_uncertainty_sensitivity":by_source,
            "entirely_source_free":True,
        })
    if len(rows)!=5 or any(len(x["source_q_uncertainty_sensitivity"])!=5
                           for x in rows):
        raise ValueError("not all frozen distance uncertainty cells scored")
    observed_example=detector_crossproduct(
        q_effective(NEAR,FAR,(.2,.8,.8,.2)))
    if abs(observed_example-oracle_B_formula(.3))>1e-12:
        raise ValueError("parent q-transport confound not reproduced")
    return {
        "schema_version":1,
        "method":METHOD,
        "status":"SOURCE_FREE_DISTANCE_MIX_PARTIAL_IDENTIFICATION_RADIUS",
        "all_5_original_observation_tables":rows,
        "total_predeclared_delta_x_calibration_x_table_scores":
            len(rows)*len(DELTAS)*5,
        "distance_mix_30pct_radius_parent_confounded_detector_OR":
            observed_example,
        "exact_oracle_detector_B_at_each_radius":[{
            "delta":d,"B":oracle_B_formula(d)} for d in DELTAS],
        "animal_conditional_test_alpha":ALPHA_ANIMAL,
        "eight_q_cell_simultaneous_calibration_alpha":ALPHA_Q,
        "requires_externally_valid_deterministic_delta_bound":True,
        "statistically_estimated_delta_would_require_extra_error_budget":True,
        "not_a_statistical_power_curve":True,
        "no_real_wildlife_or_camera_calibration_records_read":True,
        "no_actual_distance_distribution_bound_known":True,
        "previous_qualified_ODSP_routes_unchanged":True
    }
