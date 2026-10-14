#!/usr/bin/env python3
"""Author-published Bukhansan camera x clock-zone ecological overlap audit.

This is an after-publication *record-distribution* reanalysis. Actual source
Jeong et al (2025) original Tables 1-2 give 11 camera codes x 24 clock rows,
and the v1 derived contract was checked against independent printed species
hour and habitat totals. The three clocks here are NOT sunrise/sunset phases.
Never claim latent animal niche partition, causal avoidance, camera-hour
effort adjustment, animal-level confidence, or Uljin's 41 mirror dates.
"""
from __future__ import annotations

from itertools import combinations
import json
from math import isclose, sqrt
from pathlib import Path

from run_bukhansan_author_published_same_camera_windows_v1 import (
    read_source_contract, SITES
)

ROOT=Path(__file__).resolve().parents[1]
PLAN=ROOT/"BUKHANSAN_PUBLIC_JOINT_SPACE_CLOCK_OVERLAP_V3_CONTRACT.json"
SOURCE=ROOT/"BUKHANSAN_PUBLISHED_SITE_HOUR_WINDOWS_V1_CONTRACT.json"
PERIODS=("01to06","07to18","19to24")
TAXA=("water_deer","wild_boar")
STATUS="PUBLISHED_JOINT_SITE_CLOCK_RECORDED_OVERLAP_REFINEMENT_ONLY"


def validate_plan(p:dict)->None:
    if (p.get("schema_version")!=1 or
        p.get("contract_id")!="bukhansan_published_camera_x_clock_distribution_refinement_v3" or
        p.get("analysis_class")!="POST_PUBLICATION_EXPLORATORY_SOURCE_VERIFIED_RECORD_DISTRIBUTIONS" or
        p.get("original_paper_doi")!="10.14397/jals.2025.59.5.111" or
        p.get("parent_source_path")!=SOURCE.name or
        p.get("source_species")!=list(TAXA) or
        p.get("source_public_site_roster")!=list(SITES) or
        p.get("source_clock_periods")!=list(PERIODS) or
        p.get("source_total_counts")!={"water_deer":184,"wild_boar":273}):
        raise ValueError("HOLD_AUTHENTIC_SOURCE_PLAN_OR_SCOPE_MISMATCH")
    defs=p.get("definitions",{})
    if (defs.get("primary_refinement_order")!="spatial_then_clock" or
        defs.get("minimum_both_species_record_sensitivity")!=[1,5] or
        defs.get("three_marginal_overlap_targets")!=
            ["site","clock_window","site×clock_window"]):
        raise ValueError("HOLD_FROZEN_POST_PUBLICATION_STUDY_DEFINITIONS_CHANGED")
    controls=p.get("output_guards")
    if (not isinstance(controls,dict) or len(controls)!=12 or
        any(value is not False for value in controls.values())):
        raise ValueError("HOLD_INFERENCE_PROMOTION_OR_SOURCE_GATE_BYPASS")


def overlap(xs:list[float],ys:list[float])->float:
    if len(xs)!=len(ys) or not xs:
        raise ValueError("HOLD_MARGINAL_SUPPORT_MISMATCH")
    if any(x<0 or x>1 for x in xs+ys):
        raise ValueError("HOLD_INVALID_RECORDED_PROBABILITIES")
    if not isclose(sum(xs),1.0,abs_tol=1e-12,rel_tol=0) or not isclose(sum(ys),1.0,abs_tol=1e-12,rel_tol=0):
        raise ValueError("HOLD_SOURCE_PROBABILITY_MASS_NOT_ONE")
    return sum(min(a,b) for a,b in zip(xs,ys))


def rank_no_tie(xs:list[float])->list[int]:
    if len(set(xs))!=len(xs):
        raise ValueError("HOLD_SITE_BALANCE_OR_LOCAL_OVERLAP_RANK_TIE")
    order=sorted(range(len(xs)),key=lambda i:xs[i])
    ans=[0]*len(xs)
    for rank,index in enumerate(order,start=1):
        ans[index]=rank
    return ans


def spearman(xs:list[float],ys:list[float])->float|None:
    if len(xs)!=len(ys) or len(xs)<3:
        return None
    a,b=rank_no_tie(xs),rank_no_tie(ys)
    n=len(xs)
    diff=sum((x-y)**2 for x,y in zip(a,b))
    return 1-6*diff/(n*(n*n-1))


def compute(p:dict,author_contract:dict)->dict:
    validate_plan(p)
    rows=read_source_contract(author_contract)
    if len(rows)!=11 or [r["site"] for r in rows]!=list(SITES):
        raise ValueError("HOLD_REAL_AUTHOR_CAMERA_ROSTER_INCOMPLETE")
    totals=p["source_total_counts"]
    if any(sum(sum(r[sp].values()) for r in rows)!=totals[sp] for sp in TAXA):
        raise ValueError("HOLD_SOURCE_RECORD_COUNTS_CHANGED")

    joint={}
    site_marginal={}
    clock_marginal={}
    for sp in TAXA:
        N=totals[sp]
        joint[sp]={(r["site"],z):r[sp][z]/N for r in rows for z in PERIODS}
        site_marginal[sp]={r["site"]:sum(r[sp].values())/N for r in rows}
        clock_marginal[sp]={z:sum(r[sp][z] for r in rows)/N for z in PERIODS}

    space=overlap([site_marginal["water_deer"][s] for s in SITES],
                  [site_marginal["wild_boar"][s] for s in SITES])
    time=overlap([clock_marginal["water_deer"][z] for z in PERIODS],
                 [clock_marginal["wild_boar"][z] for z in PERIODS])
    space_clock=overlap([joint["water_deer"][(s,z)] for s in SITES for z in PERIODS],
                        [joint["wild_boar"][(s,z)] for s in SITES for z in PERIODS])
    if not (0<=space_clock<=min(space,time)+1e-13):
        raise ValueError("HOLD_MARGINALIZATION_CONTRACTION_THEOREM")

    spatial_first=1-space
    time_given_spatial=space-space_clock
    clock_first=1-time
    spatial_given_clock=time-space_clock
    joint_mismatch=1-space_clock
    # Neutral-to-order arithmetic average of TWO exact marginalization paths.
    # Even this Shapley-style attribution is not causal (more site than
    # clock categories; operational effort and q remain unidentified).
    symmetric_space=(spatial_first+spatial_given_clock)/2
    symmetric_clock=(clock_first+time_given_spatial)/2
    if not isclose(symmetric_space+symmetric_clock,joint_mismatch,rel_tol=0,abs_tol=1e-12):
        raise ValueError("HOLD_SYMMETRIC_BOOKKEEPING_IDENTITY")
    if (not isclose(spatial_first+time_given_spatial,joint_mismatch,rel_tol=0,abs_tol=1e-12) or
        not isclose(clock_first+spatial_given_clock,joint_mismatch,rel_tol=0,abs_tol=1e-12)):
        raise ValueError("HOLD_SCHOENER_REFINEMENT_IDENTITY")

    camera_rows=[]
    for r in rows:
        site=r["site"]
        nw=sum(r["water_deer"].values())
        nb=sum(r["wild_boar"].values())
        pws=site_marginal["water_deer"][site]
        pbs=site_marginal["wild_boar"][site]
        cameraspace=min(pws,pbs)
        camerajoint=sum(min(joint["water_deer"][(site,z)],
                            joint["wild_boar"][(site,z)]) for z in PERIODS)
        extra=cameraspace-camerajoint
        if extra< -1e-13:
            raise ValueError("HOLD_NEGATIVE_WITHIN_CAMERA_OVERLAP_LOSS")
        if nw and nb:
            time_overlap=sum(min(r["water_deer"][z]/nw,r["wild_boar"][z]/nb)
                             for z in PERIODS)
            balance=2*min(nw,nb)/(nw+nb)
        else:
            time_overlap=None
            balance=None
        camera_rows.append({
          "published_camera_code":site,
          "published_habitat_group":r["habitat"],
          "source_detected_water_deer_records":nw,
          "source_detected_wild_boar_records":nb,
          "observed_joint_overlap_contribution":round(camerajoint,9),
          "observed_spatial_overlap_contribution":round(cameraspace,9),
          "extra_overlap_loss_after_clock_conditioning":round(extra,9),
          "source_record_balance_not_independent_cooccurrence":(
              round(balance,9) if balance is not None else None),
          "within_camera_three_clock_bin_overlap_IF_both_recorded":(
              round(time_overlap,9) if time_overlap is not None else None),
          "source_camera_effort_or_animal_independence_established":False
        })
    if not isclose(sum(x["extra_overlap_loss_after_clock_conditioning"] for x in camera_rows),
                   time_given_spatial,abs_tol=7e-9,rel_tol=0):
        raise ValueError("HOLD_STATION_CONTRIBUTIONS_DO_NOT_ADD_TO_TIME_LOSS")
    contributions=sorted(camera_rows,key=lambda r:-r["extra_overlap_loss_after_clock_conditioning"])
    meaningful=[x for x in contributions if x["extra_overlap_loss_after_clock_conditioning"]>1e-8]
    if not meaningful:
        raise ValueError("HOLD_SOURCE_HAS_NO_CLOCK_REFINEMENT_DIVERGENCE")

    # Diagnostic of hypothesis "where recorded spatial coexistence is more
    # balanced, detected clock times should diverge more." Not a causal or
    # statistical field test. Reveal instability if one-record cameras used.
    rank_sensitivity=[]
    for min_both in p["definitions"]["minimum_both_species_record_sensitivity"]:
        subset=[r for r in camera_rows if min(
            r["source_detected_water_deer_records"],r["source_detected_wild_boar_records"]
        )>=min_both]
        balance=[r["source_record_balance_not_independent_cooccurrence"] for r in subset]
        local=[r["within_camera_three_clock_bin_overlap_IF_both_recorded"] for r in subset]
        rho=spearman(balance,local) if len(subset)>2 else None
        rank_sensitivity.append({
            "minimum_source_records_per_species_at_camera":min_both,
            "eligible_published_camera_codes":[x["published_camera_code"] for x in subset],
            "n_sites":len(subset),
            "record_balance_vs_local_temporal_overlap_spearman_rho_POSTHOC":(
                round(rho,9) if rho is not None else None),
            "site_independence_or_significance_established":False,
        })

    return {
       "status":STATUS,
       "paper_doi":p["original_paper_doi"],
       "original_source_11_published_camera_codes":list(SITES),
       "source_totals":totals,
       "source_clock_bins":list(PERIODS),
       "pooled_recorded_overlap":{
          "camera_space_only":round(space,9),
          "three_clock_window_time_only":round(time,9),
          "joint_camera_x_clock_window":round(space_clock,9),
          "joint_detected_record_distribution_total_variation":round(joint_mismatch,9),
          "spatial_first_decomposition":{
             "spatial_marginal_TV":round(spatial_first,9),
             "ADDITIONAL_clock_given_spatial_refinement_TV":round(time_given_spatial,9),
             "fraction_of_joint_discrepancy_visible_already_at_camera_marginal":round(
                spatial_first/joint_mismatch,9),
             "fraction_of_joint_discrepancy_additional_after_adding_clock":round(
                time_given_spatial/joint_mismatch,9),
          },
          "clock_first_alternative":{
             "clock_marginal_TV":round(clock_first,9),
             "ADDITIONAL_spatial_given_clock_refinement_TV":round(spatial_given_clock,9),
          },
          "symmetric_average_over_both_refinement_orders_NOT_CAUSAL":{
              "spatial_record_distribution_component_TV":round(symmetric_space,9),
              "clock_record_distribution_component_TV":round(symmetric_clock,9),
              "spatial_fraction_of_joint_record_discrepancy":round(
                  symmetric_space/joint_mismatch,9),
              "clock_fraction_of_joint_record_discrepancy":round(
                  symmetric_clock/joint_mismatch,9),
              "different_numbers_of_site_and_clock_categories_NOT_CONTROLLED":True,
          },
          "both_exact_marginalization_identities_verified":True,
          "attribution_is_order_dependent_and_not_causal":True,
       },
       "individual_camera_source_record_profiles_all_sites":camera_rows,
       "cameras_accounting_for_observed_additional_clock_refinement": [{
          "site_code":c["published_camera_code"],
          "observed_additional_overlap_loss":c["extra_overlap_loss_after_clock_conditioning"],
          "share_of_total_additional_loss":round(
              c["extra_overlap_loss_after_clock_conditioning"]/time_given_spatial,9)
       } for c in meaningful],
       "post_publication_spatial_record_balance_vs_local_clock_overlap":rank_sensitivity,
       "true_within_camera_competition_causally_tested":False,
       "original_Uljin_41_mirrored_date_pairs_analyzed":False,
       "actual_camera_operation_hours_and_q_read":False,
       "valid_animal_or_independent_camera_significance_computed":False,
    }


def main()->None:
    result=compute(json.loads(PLAN.read_text()),json.loads(SOURCE.read_text()))
    print(json.dumps(result,indent=2,ensure_ascii=False,sort_keys=True))

if __name__=="__main__":
    main()
