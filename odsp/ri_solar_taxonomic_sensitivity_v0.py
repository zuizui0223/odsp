"""Post-outcome RI seasonal solar-clock taxon composition sensitivity.

Consumes ONLY the first frozen v2 ecological receipt, never original
camera detections. This is a descriptive STANDARDIZATION across the
reported taxa (not a causal decomposition or confirmatory new endpoint).

A species-averaged gain is not the same target as the original equal
physical-site weighted detection gain. Different sites/years may
contribute to each season within one reported taxon; these aggregates
cannot establish individual plasticity or causal sunlight responses.
"""
from __future__ import annotations

from collections import Counter
from dataclasses import asdict, dataclass
import math
import re
import statistics
from typing import Any, Mapping

METHOD="ri-solar-v2-postoutcome-taxon-composition-sensitivity-v0"
SEASONS=("winter","summer")
METRIC="solar_over_clock"


def _values(info:Mapping[str,object])->tuple[float,float,int,int,int]:
    n=int(info["scored_images_after_dedup"])
    out=[]
    for season in SEASONS:
        row=info[season]
        value=row["metrics"][METRIC]["mean"]
        count=row["unique_physical_site_count"]
        if value is None or not math.isfinite(value):
            raise ValueError("taxon mean missing in frozen first result")
        if isinstance(count,bool) or not isinstance(count,int) or count<0:
            raise ValueError("taxon physical-site count invalid")
        out.extend((float(value),count))
    return (out[0],out[2],out[1],out[3],n)


def summarize_taxonomic_exposure_after_result(
    receipt:Mapping[str,object],
    plan:Mapping[str,object],
)->dict[str,Any]:
    if (
        plan.get("analysis_id")!=METHOD
        or plan.get("status")!="POST_OUTCOME_DESCRIPTIVE_EXPLORATION_NOT_CONFIRMATORY"
        or plan.get("minimum_each_season_site_count")!=8
        or plan.get("minimum_total_taxon_scored_events")!=100
    ):
        raise ValueError("invalid frozen descriptive contract")
    if (
        receipt.get("method_version")!="odsp-ri-solar-vs-clock-yearseason-v2-exploratory"
        or receipt.get("status")!="EXPLORATORY_NOT_SUPPORTED_OR_UNAVAILABLE"
        or receipt.get("schema_version")!=2
        or receipt.get("scored_heldout_events",0)<=0
    ):
        raise ValueError("not the exact frozen exploratory v2 result schema")
    primary=receipt["primary_heldout_solar_clock"]["season_groups"]
    frozen=plan["input"]
    for key,season in (
        ("known_primary_winter_solar_gain","winter"),
        ("known_primary_summer_solar_gain","summer"),
    ):
        value=primary[season]["metrics"][METRIC]["mean"]
        if abs(value-frozen[key])>1e-12:
            raise ValueError("v2 primary score different from locked first result")
    excluded=set(plan["explicit_taxa_nonmammal_or_non_species"])
    expected_excluded={
        "aves sp.","meleagris gallopavo","rodentia sp.","canis familiaris"
    }
    if excluded!=expected_excluded:
        raise ValueError("postresult source taxon exclusions changed")
    rows=[]
    for taxon,info in sorted(receipt["species_secondary_descriptive"].items()):
        winter,summer,w_sites,s_sites,n=_values(info)
        rows.append({
            "taxon":taxon,
            "winter":winter,
            "summer":summer,
            "winter_site_count":w_sites,
            "summer_site_count":s_sites,
            "scored_event_count":n,
            "exclusion_reason":(
                "non-wild-mammal-species-or-unresolved-taxon"
                if taxon in excluded else
                "not a binomial taxon"
                if not re.fullmatch(r"[a-z]+ [a-z]+",taxon) else
                "site/event support too small"
                if (w_sites<8 or s_sites<8 or n<100) else None
            ),
        })
    if not rows:
        raise ValueError("no taxa in first v2 receipt")
    all_means={
        season:statistics.mean(row[season] for row in rows)
        for season in SEASONS
    }
    subset=[row for row in rows if row["exclusion_reason"] is None]
    if not subset:
        raise ValueError("no eligible named wild mammal species for sensitivity")
    subset_means={
        season:statistics.mean(row[season] for row in subset)
        for season in SEASONS
    }
    sign=Counter()
    for row in subset:
        w,s=row["winter"],row["summer"]
        sign[
            "winter_positive_summer_negative" if w>0 and s<0 else
            "winter_negative_summer_positive" if w<0 and s>0 else
            "both_positive" if w>0 and s>0 else
            "both_negative" if w<0 and s<0 else
            "zero_boundary_or_mixed"
        ]+=1
    differences=[r["winter"]-r["summer"] for r in subset]
    raw_total=int(receipt["scored_heldout_events"])
    nonprimary_labels=[
        row for row in rows if row["taxon"] in excluded
    ]
    counted_events=sum(row["scored_event_count"] for row in nonprimary_labels)
    if counted_events>raw_total:
        raise ValueError("excluded taxon detections exceed original scored-event total")
    return {
        "schema_version":1,
        "method_version":METHOD,
        "source_first_v2_scientific_status":receipt["status"],
        "primary_site_weighted_solar_over_clock":{
            season:primary[season]["metrics"][METRIC]["mean"]
            for season in SEASONS
        },
        "all_taxon_equal_weight_descriptive_means":all_means,
        "all_reported_taxon_count":len(rows),
        "selected_identified_wild_mammal_count":len(subset),
        "identified_wild_mammal_equal_weight_descriptive_means":subset_means,
        "selected_taxa_sign_pattern_counts":{
            key:sign[key] for key in (
                "winter_positive_summer_negative",
                "winter_negative_summer_positive",
                "both_positive","both_negative","zero_boundary_or_mixed"
            )
        },
        "within_taxon_winter_minus_summer_descriptives":{
            "mean":statistics.mean(differences),
            "median":statistics.median(differences),
            "minimum":min(differences),
            "maximum":max(differences),
        },
        "selected_identified_wild_mammals":[
            {"taxon":r["taxon"],"winter_gain":r["winter"],
             "summer_gain":r["summer"],"summer_minus_winter":r["summer"]-r["winter"],
             "winter_sites":r["winter_site_count"],
             "summer_sites":r["summer_site_count"],
             "total_scored_events":r["scored_event_count"]}
            for r in subset
        ],
        "excluded_or_insufficient_support_taxa":[
            {"taxon":r["taxon"],"reason":r["exclusion_reason"],
             "total_scored_events":r["scored_event_count"]}
            for r in rows if r["exclusion_reason"] is not None
        ],
        "non_single_species_or_domestic_or_bird_scored_event_count":counted_events,
        "non_single_species_or_domestic_or_bird_scored_event_fraction":counted_events/raw_total,
        "original_event_total":raw_total,
        "post_outcome_descriptive_only":True,
        "real_species_or_site_level_behavioral_plasticity_identified":False,
        "sites_matched_across_species_season_cells_verified":False,
        "detection_process_bias_removed":False,
        "primary_v2_negative_or_mixed_status_overridden":False,
        "qualified_ODSP_routes_modified":False,
    }
