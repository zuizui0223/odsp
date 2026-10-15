#!/usr/bin/env python3
"""Wetland micro-site heterogeneity in REAL published Bukhansan camera counts.

Jeong, Shin & Kim (2025), doi:10.14397/jals.2025.59.5.111,
public 11-camera×24-clock-hour tables; this script uses already
source-margin-checked 3-window camera counts. Ecological questions:
  1. Does the forest/wetland record association represent BOTH wetlands?
  2. How different are the two wetland camera records from each other?
  3. Is the author-labelled 2-camera 'wetland' set unusual among 55
     hypothetical 2-site subsets AS OBSERVED SOURCE RECORDS?

Conditional photo-label Fisher and hypothetical camera-label enumerations are
FORMAL MATHEMATICAL BENCHMARKS, not independent animal/population p-values:
the animals/cameras are not independently replicated or randomly assigned,
and neither camera on-time nor optical detector q was recovered.

This is a post-outcome v5 route; frozen original ODSP Uljin 2022 41 date
pairs and separately unverified EcoBank v1.1 release stay SOURCE-HOLD.
"""
from __future__ import annotations

from itertools import combinations
from math import comb, isclose
import json
from pathlib import Path

from run_bukhansan_author_published_same_camera_windows_v1 import (
    read_source_contract, SITES
)

ROOT=Path(__file__).resolve().parents[1]
PLAN=ROOT/"BUKHANSAN_PUBLISHED_WETLAND_CAMERA_HETEROGENEITY_V5_CONTRACT.json"
SOURCE=ROOT/"BUKHANSAN_PUBLISHED_SITE_HOUR_WINDOWS_V1_CONTRACT.json"
SPECIES=("water_deer","wild_boar")
WETLAND_SITES=("M1","M2")
STATUS="PUBLISHED_M2_LOCALIZED_WETLAND_PHOTO_ASSOCIATION_NOT_CAUSAL"


def validate_plan(plan:dict)->None:
    p=plan.get("author_source",{})
    r=plan.get("roster_and_comparisons",{})
    if (plan.get("schema_version")!=1
        or plan.get("contract_id")!="bukhansan_2025_published_camera_specific_wetland_ecology_v5"
        or plan.get("analysis_stage")!="POST_SOURCE_EXPOSURE_EXPLORATORY_SITE_LEVEL_HABITAT_INTERPRETATION"
        or p.get("doi")!="10.14397/jals.2025.59.5.111"
        or p.get("source_path")!=SOURCE.name
        or p.get("known_station_ids")!=list(SITES)
        or p.get("source_water_records")!=184
        or p.get("source_boar_records")!=273
        or r.get("wetland_site_codes")!=list(WETLAND_SITES)
        or r.get("forest_site_count")!=9
        or r.get("site_label_assignment_was_randomized_in_real_field_study") is not False
        or r.get("exact_probability_uses_original_individual_photograph_exchangeability_only") is not False):
        raise ValueError("HOLD_POSTPUBLICATION_WETLAND_SOURCE_PLAN_CHANGED")
    guard=plan.get("negative_controls")
    if (not isinstance(guard,dict) or len(guard)!=11
        or any(v is not False for v in guard.values())):
        raise ValueError("HOLD_CAMERA_ECOLOGICAL_SIGNIFICANCE_PROMOTION")


def hypergeom_upper_tail(*,population:int,category_total:int,
                         draws:int,observed_category_draws:int)->dict:
    """Exact *record-label* reference, not an ecologically valid p-value.

    Population=all photographic records; category=source pooled wetland or
    source camera M2. Draws=source Water-deer photos, with Water and Boar
    labels hypothetically exchangeable over source photographic events.
    """
    if (not all(isinstance(n,int) for n in
                (population,category_total,draws,observed_category_draws))
        or not 0<category_total<population
        or not 0<draws<population):
        raise ValueError("HOLD_INVALID_FORMAL_PHOTOGRAPH_HYPERGEOMETRIC_PARAMETERS")
    lo=max(0,draws-(population-category_total))
    hi=min(category_total,draws)
    if not lo<=observed_category_draws<=hi:
        raise ValueError("HOLD_OBSERVED_PHOTOGRAPH_WATER_CELL_OUTSIDE_SUPPORT")
    denominator=comb(population,draws)
    masses=[comb(category_total,x)*comb(population-category_total,draws-x)
            for x in range(lo,hi+1)]
    if sum(masses)!=denominator:
        raise ValueError("HOLD_EXACT_PHOTOGRAPH_HYPERGEOMETRIC_NORMALIZATION")
    numerator=sum(masses[observed_category_draws-lo:])
    return {
        "source_observed_Water_photos_in_record_category":observed_category_draws,
        "fixed_combined_species_photo_category_total":category_total,
        "exact_FORMAL_record_label_one_sided_P_at_least_observed_NOT_ECOLOGICAL_P":
            numerator/denominator,
        "exact_photo_probability_numerator":str(numerator),
        "exact_photo_probability_denominator":str(denominator),
        "actual_independent_animal_replicates_or_randomized_habitat_assumed_proven":False,
    }


def group_counts(rows:list[dict],sites:set[str])->dict:
    chosen=[r for r in rows if r["site"] in sites]
    return {sp:sum(sum(r[sp].values()) for r in chosen)
            for sp in SPECIES}


def record_fraction_contrast(group:dict,all_counts:dict)->float:
    if all_counts["water_deer"]<=0 or all_counts["wild_boar"]<=0:
        raise ValueError("HOLD_UNDEFINED_SOURCE_SPECIES_TOTALS")
    return (group["water_deer"]/all_counts["water_deer"]
            -group["wild_boar"]/all_counts["wild_boar"])


def odds_ratio_wetland_vs_forest(wet:dict,forest:dict)->float:
    if min(wet.values())<=0 or min(forest.values())<=0:
        raise ValueError("HOLD_ZERO_ORIGINAL_HABITAT_SOURCE_ODDS")
    return (wet["water_deer"]*forest["wild_boar"]/
            (wet["wild_boar"]*forest["water_deer"]))


def compute(plan:dict,source:dict)->dict:
    validate_plan(plan)
    rows=read_source_contract(source)
    if len(rows)!=11 or [r["site"] for r in rows]!=list(SITES):
        raise ValueError("HOLD_ORIGINAL_PUBLISHED_CAMERA_CODES_CHANGED")
    wetland={r["site"] for r in rows if r["habitat"]=="Wetland"}
    forest={r["site"] for r in rows if r["habitat"]=="Forest"}
    if wetland!=set(WETLAND_SITES) or len(forest)!=9 or forest & wetland:
        raise ValueError("HOLD_AUTHOR_WETLAND_FOREST_LABELS_CHANGED")
    all_counts=group_counts(rows,set(SITES))
    if all_counts!={"water_deer":184,"wild_boar":273}:
        raise ValueError("HOLD_SOURCE_PUBLISHED_RECORD_TOTAL_MISMATCH")

    wet=group_counts(rows,wetland)
    f=group_counts(rows,forest)
    if (wet!={"water_deer":110,"wild_boar":74}
        or f!={"water_deer":74,"wild_boar":199}):
        raise ValueError("HOLD_REPUBLISHED_AUTHOR_WETLAND_MARGINS_MISMATCH")
    original_diff=record_fraction_contrast(wet,all_counts)
    original_or=odds_ratio_wetland_vs_forest(wet,f)
    station_contributions=[]
    for s in WETLAND_SITES:
        c=group_counts(rows,{s})
        diff=record_fraction_contrast(c,all_counts)
        station_contributions.append({
            "source_wetland_camera":s,
            "water_deer_record_count":c["water_deer"],
            "boar_record_count":c["wild_boar"],
            "water_species_whole_network_record_fraction":round(c["water_deer"]/184,9),
            "boar_species_whole_network_record_fraction":round(c["wild_boar"]/273,9),
            "source_record_fraction_differential_contribution_pp":round(100*diff,9),
            "share_of_two_wetland_camera_record_fraction_differential":
                round(diff/original_diff,9),
            "species_fraction_among_combined_photos_at_camera":round(
                c["water_deer"]/(c["water_deer"]+c["wild_boar"]),9)
        })
    if not isclose(sum(x["source_record_fraction_differential_contribution_pp"] for x in station_contributions),
                   100*original_diff,rel_tol=0,abs_tol=2e-9):
        raise ValueError("HOLD_WETLAND_SITE_CONTRIBUTIONS_DO_NOT_SUM")

    leave_wetland=[]
    for omit in WETLAND_SITES:
        keep=set(SITES)-{omit}
        all_after=group_counts(rows,keep)
        remwet=wetland-{omit}
        wafter=group_counts(rows,remwet)
        fafter=group_counts(rows,forest)
        if fafter!=f:
            raise ValueError("HOLD_FOREST_REMAINDER_SHOULD_BE_UNMODIFIED")
        remain_diff=record_fraction_contrast(wafter,all_after)
        leave_wetland.append({
            "omitted_wetland_camera":omit,
            "remaining_wetland_camera":next(iter(remwet)),
            "remaining_water_total_across_retained_cameras":all_after["water_deer"],
            "remaining_boar_total_across_retained_cameras":all_after["wild_boar"],
            "remaining_wetland_water_records":wafter["water_deer"],
            "remaining_wetland_boar_records":wafter["wild_boar"],
            "RECOMPUTED_water_wetland_record_share":round(
                wafter["water_deer"]/all_after["water_deer"],9),
            "RECOMPUTED_boar_wetland_record_share":round(
                wafter["wild_boar"]/all_after["wild_boar"],9),
            "RECOMPUTED_wetland_record_share_species_difference_pp":round(
                100*remain_diff,9),
            "RECOMPUTED_source_record_wetland_vs_forest_OR":round(
                odds_ratio_wetland_vs_forest(wafter,fafter),9),
            "independent_ecological_habitat_replication_claimed":False
        })

    # Descriptive finite combinatorial RANK, NOT a genuine habitat
    # randomization test: camera environments were NOT randomly assigned.
    choices=[]
    for pair in combinations(SITES,2):
        c=group_counts(rows,set(pair))
        choices.append({
            "site_codes":list(pair),
            "observed_two_camera_record_share_species_contrast":
                record_fraction_contrast(c,all_counts)
        })
    if len(choices)!=55:
        raise ValueError("HOLD_WRONG_PUBLIC_CAMERA_PAIR_COUNT")
    actual_pair=next((x for x in choices if x["site_codes"]==list(WETLAND_SITES)),None)
    if actual_pair is None or not isclose(
        actual_pair["observed_two_camera_record_share_species_contrast"],
        original_diff,abs_tol=1e-14,rel_tol=0
    ):
        raise ValueError("HOLD_SOURCE_DESIGNATED_WETLAND_PAIR_NOT_PRESENT")
    larger=sum(x["observed_two_camera_record_share_species_contrast"]>original_diff+1e-13
               for x in choices)
    equal=sum(isclose(x["observed_two_camera_record_share_species_contrast"],
                      original_diff,abs_tol=1e-13,rel_tol=0) for x in choices)
    top=sorted(choices,key=lambda x:-x["observed_two_camera_record_share_species_contrast"])[0]
    if equal!=1 or larger!=1 or top["site_codes"]!=["G19","M2"]:
        raise ValueError("HOLD_SOURCE_PUBLISHED_WETLAND_CAMERA_RANK_CHANGED")

    fisher_habitat=hypergeom_upper_tail(
        population=457,category_total=wet["water_deer"]+wet["wild_boar"],
        draws=all_counts["water_deer"],observed_category_draws=wet["water_deer"])
    m2=group_counts(rows,{"M2"})
    fisher_m2=hypergeom_upper_tail(
        population=457,category_total=m2["water_deer"]+m2["wild_boar"],
        draws=all_counts["water_deer"],observed_category_draws=m2["water_deer"])
    return {
        "status":STATUS,
        "author_published_source_doi":plan["author_source"]["doi"],
        "source_verified_11_public_camera_codes":list(SITES),
        "source_record_grain":"11 CAMERAS x 3 CLOCK WINDOWS FROM ORIGINAL PUBLISHED 11x24 TABLES",
        "forest_source_counts":f,
        "two_wetland_source_counts":wet,
        "wetland_source_photo_record_composition":{
            "water_fraction_of_water_records_in_wetland":round(wet["water_deer"]/184,9),
            "boar_fraction_of_boar_records_in_wetland":round(wet["wild_boar"]/273,9),
            "water_minus_boar_wetland_record_share_pp":round(100*original_diff,9),
            "whole_network_species_record_wetland_vs_forest_OR":round(original_or,9),
            "within_camera_original_record_contributions":station_contributions,
            "M2_fraction_of_observed_wetland_share_differential":next(
                x["share_of_two_wetland_camera_record_fraction_differential"]
                for x in station_contributions if x["source_wetland_camera"]=="M2"),
            "zero_causal_habitat_preference_claim":True,
        },
        "both_single_wetland_camera_omission_studies_RECOMPUTE_DENOMINATORS":
            leave_wetland,
        "all_55_two_camera_set_descriptive_rank":{
            "number_of_possible_source_two_camera_sets":len(choices),
            "actual_source_wetland_pair_ranking_descending":larger+1,
            "actual_pair_number_of_sets_equal_or_more_extreme":larger+equal,
            "actual_pair_upper_fraction_among_all_55_source_camera_pair_scores":
                round((larger+equal)/len(choices),9),
            "highest_record_contrast_pair_in_original_camera_network":top["site_codes"],
            "highest_pair_record_contrast_pp":round(
                100*top["observed_two_camera_record_share_species_contrast"],9),
            "actual_habitat_labels_randomly_assigned":False,
            "source_site_pair_ranking_is_NOT_a_valid_independent_habitat_p_value":True
        },
        "formal_photo_count_label_exchangeability_benchmarks_NOT_POPULATION_P":{
            "forest_vs_both_wetlands":fisher_habitat,
            "M2_vs_other_ten_camera_codes":fisher_m2,
            "actual_photo_and_animal_independence_verified":False
        },
        "source_physical_camera_operational_effort_available":False,
        "species_camera_detector_q_adjusted":False,
        "causal_wetland_vs_forest_habitat_mechanism_proved":False,
        "original_frozen_Uljin_2022_41_daylength_pairs_tested":False,
    }


if __name__=="__main__":
    print(json.dumps(compute(json.loads(PLAN.read_text()),
                             json.loads(SOURCE.read_text())),
                     ensure_ascii=False,indent=2,sort_keys=True))
