#!/usr/bin/env python3
"""Site-level ecology from public *author-published* Bukhansan tables.

Source Jeong, Shin & Kim (2025) DOI 10.14397/jals.2025.59.5.111,
Tables 1-2: 11 published camera codes x 24 printed clock-bin frequencies,
already reduced in v1 to three bins and independently checked against
author's per-hour and species/habitat margins.

Post-publication exploratory DESCRIPTIVE inference only. Site-wise counts
are detected photos/animals under an imperfect, uncalibrated camera process.
No dated event histories, independent on-camera hours, q, independent
site/animal uncertainty, solar phase or Uljin 41 pairs.
"""
from __future__ import annotations

from itertools import combinations
import json
from math import isclose
from pathlib import Path

from run_bukhansan_author_published_same_camera_windows_v1 import (
    PLAN as SOURCE_PATH,
    SITES,
    read_source_contract,
    stratified
)

ROOT = Path(__file__).resolve().parents[1]
PLAN = ROOT / "BUKHANSAN_PUBLISHED_CAMERA_SITE_INFLUENCE_V2_CONTRACT.json"
STATUS = "PUBLISHED_SPATIAL_CAMERA_CONCENTRATION_AND_LOO_DESCRIPTIVE_ONLY"
SPECIES = ("water_deer", "wild_boar")
WINDOWS = ("01to06", "19to24")


def check_plan(plan: dict) -> None:
    if (
        plan.get("schema_version") != 1
        or plan.get("contract_id") !=
            "bukhansan_2025_published_camera_spatial_temporal_influence_v2"
        or plan.get("analysis_stage") !=
            "POST_PUBLICATION_EXPLORATORY_SITE_INFLUENCE_NOT_PRE_REGISTERED"
        or plan.get("origin_doi") != "10.14397/jals.2025.59.5.111"
        or plan.get("parent_source_contract") != SOURCE_PATH.name
        or plan.get("analysis_species") != list(SPECIES)
        or plan.get("analysis_clock_windows") != list(WINDOWS)
        or plan.get("site_roster_immutable") != list(SITES)
    ):
        raise ValueError("HOLD_PUBLISHED_SOURCE_SITE_INFLUENCE_V2_PLAN_CHANGED")
    guard = plan.get("negative_controls")
    if not isinstance(guard, dict) or len(guard) != 10 or any(
        value is not False for value in guard.values()
    ):
        raise ValueError("HOLD_CAMERA_SOURCE_OR_INFERENCE_CLAIM_PROMOTED")


def site_clock_profile(row: dict) -> dict | None:
    a = row["water_deer"]
    b = row["wild_boar"]
    n_w = a["01to06"]+a["19to24"]
    n_b = b["01to06"]+b["19to24"]
    if n_w == 0 or n_b == 0:
        return None
    p_w = a["01to06"]/n_w
    p_b = b["01to06"]/n_b
    return {
        "site": row["site"],
        "habitat": row["habitat"],
        "water_clock_window_counts": n_w,
        "boar_clock_window_counts": n_b,
        "water_late_01to06_share": p_w,
        "boar_late_01to06_share": p_b,
        "water_minus_boar_late_fraction": p_w-p_b,
    }


def shared_site_distributions(rows: list[dict]) -> dict:
    observed = [item for row in rows
                if (item := site_clock_profile(row)) is not None]
    if not observed:
        return {"status": "NO_SHARED_SOURCE_POSITIVE_CAMERA",
                "late_fraction_species_difference_pp": None}
    wtotal = sum(r["water_clock_window_counts"] for r in observed)
    btotal = sum(r["boar_clock_window_counts"] for r in observed)
    wlate = sum(r["water_clock_window_counts"]*r["water_late_01to06_share"]
                for r in observed)/wtotal
    blate = sum(r["boar_clock_window_counts"]*r["boar_late_01to06_share"]
                for r in observed)/btotal
    equal = sum(r["water_minus_boar_late_fraction"] for r in observed)/len(observed)
    within = sum(
        .5*(r["water_clock_window_counts"]/wtotal +
            r["boar_clock_window_counts"]/btotal)*
        r["water_minus_boar_late_fraction"] for r in observed
    )
    mixed = sum(
        .5*(r["water_late_01to06_share"]+r["boar_late_01to06_share"])*
        (r["water_clock_window_counts"]/wtotal -
         r["boar_clock_window_counts"]/btotal) for r in observed
    )
    if not isclose(within + mixed, wlate-blate, rel_tol=0, abs_tol=1e-13):
        raise ValueError("HOLD_SHARED_CAMERA_COMPOSITION_IDENTITY_BROKEN")
    return {
        "status": "SOURCE_DETECTED_COMMON_CAMERA_CLOCK_WINDOW_FRACTIONS",
        "common_positive_site_codes": [r["site"] for r in observed],
        "number_of_source_positive_both_species_camera_codes": len(observed),
        "total_water_photos_used": wtotal,
        "total_boar_photos_used": btotal,
        "water_01to06_fraction": round(wlate, 9),
        "boar_01to06_fraction": round(blate, 9),
        "detected_late_fraction_species_difference_pp": round(100*(wlate-blate), 9),
        "equal_camera_weight_mean_species_difference_pp": round(100*equal, 9),
        "noncausal_symmetrical_within_site_component_pp": round(100*within, 9),
        "noncausal_symmetrical_camera_weight_component_pp": round(100*mixed, 9),
        "independent_site_or_individual_uncertainty_calculated": False,
        "site_exposure_or_detector_q_adjusted": False,
    }


def spatial_concentration(rows: list[dict]) -> dict:
    totals = {sp:sum(sum(r[sp].values()) for r in rows) for sp in SPECIES}
    if totals != {"water_deer": 184, "wild_boar": 273}:
        raise ValueError("HOLD_WRONG_SOURCE_EVENT_TOTALS")
    fractions = {
        sp:{r["site"]:sum(r[sp].values())/totals[sp] for r in rows}
        for sp in SPECIES
    }
    occupied={sp:sum(w>0 for w in fractions[sp].values()) for sp in SPECIES}
    effective={
        sp:1/sum(w*w for w in fractions[sp].values()) for sp in SPECIES
    }
    site_overlap=1-.5*sum(
        abs(fractions["water_deer"][site]-fractions["wild_boar"][site])
        for site in SITES
    )
    if not (0<=site_overlap<=1):
        raise ValueError("HOLD_INVALID_SOURCE_SPATIAL_OVERLAP")
    m2={sp:round(fractions[sp]["M2"],9) for sp in SPECIES}
    return {
        "status": "PUBLISHED_DETECTION_COUNTS_SPATIAL_CONCENTRATION_NOT_OCCUPANCY",
        "source_photos_by_species": totals,
        "public_camera_codes_with_positive_record": occupied,
        "inverse_Herfindahl_effective_camera_count_of_detected_records":{
            sp:round(effective[sp], 9) for sp in SPECIES
        },
        "Schoener_site_record_distribution_overlap_not_latent_occupancy":
            round(site_overlap, 9),
        "M2_record_share_by_species":m2,
        "does_not_estimate_animal_abundance_occupancy_or_independent_replicates":True,
    }


def analyze(plan: dict, source_contract: dict) -> dict:
    check_plan(plan)
    rows=read_source_contract(source_contract)
    shared=shared_site_distributions(rows)
    spatial=spatial_concentration(rows)
    full=stratified(rows)
    if full.get("n_informative_sites")!=7:
        raise ValueError("HOLD_UNEXPECTED_SEVEN_SITE_CONDITIONAL_COMPARISON")
    if "mh_morning_to_evening_water_vs_boar_OR" not in full:
        raise ValueError("HOLD_NO_MH_OVERLAP")
    loo=[]
    for dropped in SITES:
        subset=[r for r in rows if r["site"]!=dropped]
        mh=stratified(subset)
        share=shared_site_distributions(subset)
        odds=mh.get("mh_morning_to_evening_water_vs_boar_OR")
        if odds is None:
            raise ValueError("HOLD_NO_INFORMATIVE_CAMERA_AFTER_OMISSION")
        loo.append({
            "omitted_camera_code":dropped,
            "habitat":next(r["habitat"] for r in rows if r["site"]==dropped),
            "camera_positive_both_species_in_original_table":
                site_clock_profile(next(r for r in rows if r["site"]==dropped)) is not None,
            "post_omit_source_informative_cameras":mh["n_informative_sites"],
            "Mantel_Haenszel_source_count_OR_not_causal":round(odds,9),
            "late_fraction_difference_pp_given_source_positive_cameras":
                share["detected_late_fraction_species_difference_pp"],
            "equal_source_camera_weight_mean_difference_pp":
                share["equal_camera_weight_mean_species_difference_pp"],
            "population_biological_significance_tested":False,
        })
    or_values=[r["Mantel_Haenszel_source_count_OR_not_causal"] for r in loo]
    diffs=[r["late_fraction_difference_pp_given_source_positive_cameras"]
           for r in loo]
    equal=[r["equal_source_camera_weight_mean_difference_pp"] for r in loo]
    m2=next(r for r in loo if r["omitted_camera_code"]=="M2")
    score=full["score"] # existing v1 score is 9-decimal output
    score_wo_m2=stratified([r for r in rows if r["site"]!="M2"])["score"]
    return {
        "status":STATUS,
        "original_public_source_doi":plan["origin_doi"],
        "input":"SOURCE_PUBLISHED_11_STATIONS_AND_24_HOUR_COLUMN_MARGINS_DERIVED_3_CLOCK_WINDOWS",
        "source_all_11_site_roster_preserved":list(SITES),
        "observational_site_detection_spatial_pattern":spatial,
        "source_positive_both_species_clock_comparison":shared,
        "all_11_leave_one_published_camera_out":loo,
        "MH_OR_all_informative_published_cameras":
            full["mh_morning_to_evening_water_vs_boar_OR"],
        "MH_OR_leave_one_station_out_min_max":[round(min(or_values),9),round(max(or_values),9)],
        "MH_OR_direction_above_one_after_every_single_camera_omission":
            all(x>1 for x in or_values),
        "source_shared_roster_late_share_difference_pp_LOO_range":[
            round(min(diffs),9),round(max(diffs),9)],
        "equal_shared_camera_mean_difference_pp_LOO_range":[
            round(min(equal),9),round(max(equal),9)],
        "M2_omission_sensitivity":{
            "MH_OR_without_M2":m2["Mantel_Haenszel_source_count_OR_not_causal"],
            "source_CMH_score_all":score,
            "source_CMH_score_without_M2":score_wo_m2,
            "M2_fraction_of_aggregate_CMH_score_deviation":
                round((score-score_wo_m2)/score,9),
            "conditional_event_independence_p_unvalidated_all":
                full["UNVALIDATED_EVENT_INDEPENDENCE_p"],
            "conditional_event_independence_p_unvalidated_without_M2":
                stratified([r for r in rows if r["site"]!="M2"])["UNVALIDATED_EVENT_INDEPENDENCE_p"],
            "population_significance_or_animal_independence_claimed":False
        },
        "clock_bins_01to06_and_19to24_not_date_solar_phase":True,
        "site_clustering_community_population_or_occupancy_significance_claimed":False,
        "original_uljin_2022_41_fixed_date_pairs_processed":False,
        "published_source_stations_not_camera_operation_hours_or_q":True
    }


if __name__=="__main__":
    print(json.dumps(analyze(json.loads(PLAN.read_text()),
                             json.loads(SOURCE_PATH.read_text())),
                     ensure_ascii=False,sort_keys=True,indent=2))
