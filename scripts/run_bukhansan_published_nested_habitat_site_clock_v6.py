#!/usr/bin/env python3
"""Ecological hierarchical *recorded-distribution* description of Bukhansan.

Jeong, Shin & Kim (2025), DOI 10.14397/jals.2025.59.5.111,
original author-published Tables 1/2 contain 11 physical camera codes
×24 clock-bin counts, separately for each ungulate. The archived v1
source-derived 11×3 counts are independently checked against their
published 24 per-species hour margins and four habitat group totals.

This route is AFTER results, not preregistered. We compare the same
source counts at increasingly detailed groupings: (1) Forest/Wetland,
(2) 11 cameras nested within habitat, (3) 3 clock bins within camera.
An exact total-variation telescoping identity is NOT a causal
variance partition. Source actual camera uptime, detector q, animal
identity and dated solar phase are unavailable. The 2022 Uljin 41
frozen matched dates remain source HOLD and are NOT analyzed here.
"""
from __future__ import annotations

import json
from math import isclose
from pathlib import Path

from run_bukhansan_author_published_same_camera_windows_v1 import (
    read_source_contract, SITES,
)
from run_bukhansan_published_joint_space_clock_overlap_v3 import (
    compute as v3_compute,
)

ROOT = Path(__file__).resolve().parents[1]
PLAN = ROOT / "BUKHANSAN_NESTED_HABITAT_SITE_CLOCK_V6_CONTRACT.json"
SOURCE = ROOT / "BUKHANSAN_PUBLISHED_SITE_HOUR_WINDOWS_V1_CONTRACT.json"
V3PLAN = ROOT / "BUKHANSAN_PUBLIC_JOINT_SPACE_CLOCK_OVERLAP_V3_CONTRACT.json"
SPECIES = ("water_deer", "wild_boar")
HABITATS = ("Forest", "Wetland")
PERIODS = ("01to06", "07to18", "19to24")
STATUS = "PUBLISHED_11_CAMERA_NESTED_HABITAT_SITE_CLOCK_RECORDS_DESCRIPTIVE_ONLY"


def guard(plan:dict)->None:
    if (plan.get("schema_version")!=1
        or plan.get("contract_id")!="bukhansan_published_nested_habitat_site_clock_observational_v6"
        or plan.get("stage")!="POST_PUBLICATION_SOURCE_EXPOSED_EXPLORATORY_NESTED_ECOLOGY"
        or plan.get("parent_author_doi")!="10.14397/jals.2025.59.5.111"
        or plan.get("parent_source_path")!=SOURCE.name
        or plan.get("source_species")!=list(SPECIES)
        or plan.get("original_public_station_roster")!=list(SITES)
        or plan.get("original_habitat_categories")!=list(HABITATS)
        or plan.get("source_clock_bins")!=list(PERIODS)
        or plan.get("fixed_full_source_counts")!={"water_deer":184,"wild_boar":273}):
        raise ValueError("HOLD_HIERARCHICAL_AUTHOR_SOURCE_AND_POSTDATA_CONTRACT")
    exact=plan.get("observational_statistics",{})
    if (exact.get("single_camera_omission")!=
        "all 11 original site codes; independently recompute both species totals, every marginal and joint TV after one camera omission, original forest/wetland label preserved"
        or exact.get("ordered_nested_TV")!=
        "TV(habitat) + [TV(camera)-TV(habitat)] + [TV(camera×clock)-TV(camera)] = TV(camera×clock)"):
        raise ValueError("HOLD_HIERARCHICAL_REFINEMENT_DEFINED_INCORRECTLY")
    holds=plan.get("source_and_inference_holds")
    if (not isinstance(holds,dict) or len(holds)!=12
        or any(v is not True for v in holds.values())):
        raise ValueError("HOLD_UNJUSTIFIED_SOURCE_OR_CAUSAL_CLAIM")


def total(row:dict,species:str)->int:
    return sum(row[species][z] for z in PERIODS)


def finite_tv(pairs:list[tuple[float,float]])->float:
    if not pairs:raise ValueError("HOLD_EMPTY_SOURCE_RECORD_PROBABILITIES")
    if any(not 0<=a<=1 or not 0<=b<=1 for a,b in pairs):
        raise ValueError("HOLD_SOURCE_DISTRIBUTION_NOT_PROBABILITY")
    if (not isclose(sum(a for a,_ in pairs),1,rel_tol=0,abs_tol=1e-12)
        or not isclose(sum(b for _,b in pairs),1,rel_tol=0,abs_tol=1e-12)):
        raise ValueError("HOLD_ORIGINAL_SOURCE_RECORD_COUNTS_NOT_NORMALIZED")
    return .5*sum(abs(a-b) for a,b in pairs)


def grouped_counts(rows:list[dict], habitat:str|None=None)->dict:
    sel=[r for r in rows if habitat is None or r["habitat"]==habitat]
    return {sp:sum(total(r,sp) for r in sel) for sp in SPECIES}


def calculate_hierarchy(rows:list[dict])->dict:
    if not rows or len({r["site"] for r in rows})!=len(rows):
        raise ValueError("HOLD_SOURCE_PHYSICAL_SITE_ROSTER_UNAVAILABLE")
    n=grouped_counts(rows)
    if min(n.values())<=0:
        raise ValueError("HOLD_NO_BOTH_SPECIES_SOURCE_RECORDS")
    nw,nb=n["water_deer"],n["wild_boar"]
    habitats=[
        (grouped_counts(rows,h)["water_deer"]/nw,
         grouped_counts(rows,h)["wild_boar"]/nb)
        for h in HABITATS
    ]
    cameras=[(total(r,"water_deer")/nw,total(r,"wild_boar")/nb) for r in rows]
    joint=[(r["water_deer"][z]/nw,r["wild_boar"][z]/nb)
           for r in rows for z in PERIODS]
    th=finite_tv(habitats)
    tc=finite_tv(cameras)
    tj=finite_tv(joint)
    add_site=tc-th
    add_time=tj-tc
    if (add_site < -1e-12 or add_time < -1e-12
        or not isclose(th+add_site+add_time,tj,rel_tol=0,abs_tol=1e-12)):
        raise ValueError("HOLD_CATEGORICAL_REFINEMENT_MONOTONICITY")
    # Reconfirm each habitat's contribution directly from source counts:
    # O_hab - O_site. A site in an otherwise 'boar-dominant' forest
    # can flip species-normalized record rank; it may increase TV.
    by_habitat=[]
    for h,(phw,phb) in zip(HABITATS,habitats):
        members=[r for r in rows if r["habitat"]==h]
        marginal_overlap=min(phw,phb)
        station_overlap=sum(min(total(r,"water_deer")/nw,
                                total(r,"wild_boar")/nb) for r in members)
        extra=marginal_overlap-station_overlap
        if extra < -1e-12:
            raise ValueError("HOLD_WITHIN_HABITAT_REFINEMENT_NEGATIVE")
        loc=[]
        for r in members:
            diff=total(r,"water_deer")/nw-total(r,"wild_boar")/nb
            # local reversal *against that habitat's marginal direction*
            # is the exact source of O_hab−O_camera in that habitat.
            reverse=max(0,diff) if phw<phb else max(0,-diff)
            loc.append({
                "source_site_code":r["site"],
                "water_records":total(r,"water_deer"),
                "boar_records":total(r,"wild_boar"),
                "species_normalized_water_minus_boar_site_fraction":
                    round(diff,9),
                "local_direction_reversal_overlap_loss":round(reverse,9),
            })
        if not isclose(sum(max(0,total(r,"water_deer")/nw-
                              total(r,"wild_boar")/nb) if phw<phb
                           else max(0,total(r,"wild_boar")/nb-
                                    total(r,"water_deer")/nw) for r in members),
                       extra,rel_tol=0,abs_tol=1e-12):
            raise ValueError("HOLD_SITE_DIRECTIONAL_REVERSAL_IDENTITY")
        subw=grouped_counts(rows,h)["water_deer"]
        subb=grouped_counts(rows,h)["wild_boar"]
        within=(
            sum(min(total(r,"water_deer")/subw,
                    total(r,"wild_boar")/subb) for r in members)
            if subw>0 and subb>0 else None
        )
        by_habitat.append({
          "habitat":h,
          "source_water_records":subw,
          "source_boar_records":subb,
          "source_camera_count":len(members),
          "contribution_to_habitat_marginal_record_overlap":round(marginal_overlap,9),
          "contribution_to_camera_record_overlap":round(station_overlap,9),
          "additional_within_habitat_camera_TV":round(max(0,extra),9),
          "species_normalized_direction":
              "water_above_boar" if phw>phb else "boar_above_water",
          "local_reversal_station_codes":[x["source_site_code"] for x in loc
                                           if x["local_direction_reversal_overlap_loss"]>1e-12],
          "source_station_distributions":loc,
          "SEPARATE_within_habitat_species_normalized_site_overlap":(
              round(within,9) if within is not None else None),
          "causal_habitat_preference_inferred":False,
        })
    if not isclose(sum(h["additional_within_habitat_camera_TV"] for h in by_habitat),
                   add_site,rel_tol=0,abs_tol=3e-9):
        raise ValueError("HOLD_HABITAT_SITE_CONTRIBUTION_SUM")

    return {
      "status":"SOURCE_DETECTED_RECORDS_EXACT_NESTED_SCALE_IDENTITY",
      "source_total_species_records":n,
      "number_of_public_source_camera_codes":len(rows),
      "number_of_published_wetland_cameras":len([
          r for r in rows if r["habitat"]=="Wetland"]),
      "habitat_level_record_TV":round(th,9),
      "camera_level_record_TV":round(tc,9),
      "camera_x_clock_level_record_TV":round(tj,9),
      "additional_camera_given_habitat_TV":round(add_site,9),
      "additional_clock_given_camera_TV":round(add_time,9),
      "fraction_of_joint_record_mismatch_at_first_habitat_level":round(th/tj,9),
      "fraction_of_joint_record_mismatch_from_additional_camera":round(add_site/tj,9),
      "fraction_of_joint_record_mismatch_from_additional_clock":round(add_time/tj,9),
      "fraction_of_camera_record_mismatch_at_habitat_level":round(th/tc,9),
      "per_habitat_source_station_locus":by_habitat,
      "tv_nested_source_marginalization_exact":True,
      "source_camera_habitat_selection_mechanism_proved":False,
      "period_widths_are_6_12_6_clock_labels_not_solar":True,
    }


def analyze(plan:dict,source:dict,v3plan:dict)->dict:
    guard(plan)
    rows=read_source_contract(source)
    if [r["site"] for r in rows]!=list(SITES):
        raise ValueError("HOLD_ALL_11_SOURCE_CAMERA_CODES")
    original=calculate_hierarchy(rows)
    if original["source_total_species_records"]!=plan["fixed_full_source_counts"]:
        raise ValueError("HOLD_AUTHOR_SOURCE_SPECIES_COUNTS_CHANGED")
    previous=v3_compute(v3plan,source)
    if not isclose(
        original["camera_level_record_TV"],
        1-previous["pooled_recorded_overlap"]["camera_space_only"],abs_tol=1e-8):
        raise ValueError("HOLD_EXISTING_PUBLISHED_SITE_OVERLAP_ROUTE_DISAGREES")
    if not isclose(
        original["camera_x_clock_level_record_TV"],
        1-previous["pooled_recorded_overlap"]["joint_camera_x_clock_window"],abs_tol=1e-8):
        raise ValueError("HOLD_EXISTING_PUBLISHED_SITE_CLOCK_ROUTE_DISAGREES")

    omissions=[]
    for site in SITES:
        retained=[r for r in rows if r["site"]!=site]
        o=calculate_hierarchy(retained)
        omissions.append({
          "omitted_original_published_camera":site,
          "original_habitat_label":next(
              r["habitat"] for r in rows if r["site"]==site),
          "retained_water_record_count":o["source_total_species_records"]["water_deer"],
          "retained_boar_record_count":o["source_total_species_records"]["wild_boar"],
          "retained_habitat_cameras":o["number_of_published_wetland_cameras"],
          "habitat_TV":o["habitat_level_record_TV"],
          "camera_TV":o["camera_level_record_TV"],
          "joint_camera_clock_TV":o["camera_x_clock_level_record_TV"],
          "additional_camera_given_habitat_TV":o["additional_camera_given_habitat_TV"],
          "additional_clock_given_camera_TV":o["additional_clock_given_camera_TV"],
          "fraction_of_camera_record_mismatch_at_habitat_level":
              o["fraction_of_camera_record_mismatch_at_habitat_level"],
          "fraction_of_joint_record_mismatch_at_habitat_level":
              o["fraction_of_joint_record_mismatch_at_first_habitat_level"],
          "retained_publication_11_sites_except_omitted":True,
          "species_record_totals_recomputed_for_omission":True,
          "ecological_significance_claimed":False,
        })
    excl={r["omitted_original_published_camera"]:r for r in omissions}
    if (len(omissions)!=11
        or not excl["M2"]["retained_habitat_cameras"]==1
        or not excl["M1"]["retained_habitat_cameras"]==1):
        raise ValueError("HOLD_WETLAND_SITE_OMISSION_ROSTER")
    return {
       "status":STATUS,
       "original_author_published_source_doi":plan["parent_author_doi"],
       "full_11_camera_nested_distribution":original,
       "all_11_leave_single_camera_out_nested_TV":omissions,
       "M2_omission_ecological_scale_change":{
          "original_habitat_share_of_spatial_TV":
              original["fraction_of_camera_record_mismatch_at_habitat_level"],
          "without_M2_habitat_share_of_spatial_TV":
              excl["M2"]["fraction_of_camera_record_mismatch_at_habitat_level"],
          "original_habitat_marginal_TV":original["habitat_level_record_TV"],
          "without_M2_habitat_marginal_TV":excl["M2"]["habitat_TV"],
          "original_within_habitat_camera_additional_TV":
              original["additional_camera_given_habitat_TV"],
          "without_M2_within_habitat_camera_additional_TV":
              excl["M2"]["additional_camera_given_habitat_TV"],
          "actual_independent_multiple_wetland_replicates_after_omission":False,
          "source_camera_q_or_unequal_station_on_hours_adjusted":False,
       },
       "source_assumptions_prior_clock_conditional_null_unaltered":True,
       "source_calendar_dates_and_camera_hourly_uptime_available":False,
       "causal_habitat_or_interspecific_competition_test_performed":False,
       "original_frozen_Uljin_2022_41_matched_pairs_tested":False,
    }


if __name__=="__main__":
    print(json.dumps(analyze(json.loads(PLAN.read_text()),
                             json.loads(SOURCE.read_text()),
                             json.loads(V3PLAN.read_text())),
                     ensure_ascii=False,indent=2,sort_keys=True))
