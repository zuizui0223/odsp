"""Post-result matched physical site x taxon seasonal solar-clock diagnosis.

Recomputes UNCHANGED frozen v2 source/astronomy/scoring before describing
winter minus summer at the SAME (physical site, taxon), but never claims
confirmatory inference. The original first-run overall means, 19,916 scored
events and 43 distinct validation sites MUST numerically replay or the
new descriptive analysis terminates UNAVAILABLE.

A pair is one physical site x taxon with at least 5 scored detections
in BOTH seasons. Within each pair: average per year first, then average
represented heldout years, then compare winter-summer. Report separate
pair-, physical-site-, and taxon-balanced descriptive summaries; these
are new targets, not the original all-detection site-season target.
"""
from __future__ import annotations

from collections import Counter,defaultdict
import hashlib
import json
import math
from pathlib import Path
from typing import Mapping,Sequence,Any

import numpy as np

from .ri_solar_clock_transfer_v0 import (
    DielEvent,fit_species_profiles,score_new_site_future_year,
    site_is_sealed,summarize_site_level_transfer,
)
from .ri_solar_clock_yearseason_v2 import (
    v2_events_from_two_tables,_validate_contract as validate_v2_contract,
)
from .ri_solar_source_v0 import _member_zip_csv

METHOD="ri_solar_v2_postoutcome_matched_site_taxon_v0"
SEASONS=("winter","summer")
NON_WILD_OR_UNRESOLVED=frozenset((
    "aves sp.","rodentia sp.","meleagris gallopavo","canis familiaris"
))


def _expect_plan(plan:Mapping[str,object])->Mapping[str,object]:
    if (plan.get("schema_version")!=1
        or plan.get("analysis_id")!="ri-v2-solar-clock-matched-site-taxon-pair-v0"
        or plan.get("status")!="POST_EXPOSURE_EXPLORATORY_MATCHED_SUPPORT_ONLY"
        or plan.get("expected_result_state")!=
            "POST_OUTCOME_MATCHED_CELL_DESCRIPTION_ONLY_OR_UNAVAILABLE"):
        raise ValueError("unrecognized post-outcome matched-cell contract")
    cfg=plan.get("matched_cell_rule",{})
    if (cfg.get("min_dedup_scored_events_in_each_season")!=5
        or cfg.get("min_total_paired_site_taxon_cells_to_report")!=8
        or cfg.get("min_pairs_to_report_individual_taxon")!=3
        or cfg.get("new_p_values_or_bootstrap_ci") is not False
        or set(cfg.get("taxon_taxonomic_name_exclusion_for_secondary",[]))
            !=NON_WILD_OR_UNRESOLVED):
        raise ValueError("post-outcome matched cell thresholds changed")
    evidence=plan.get("evidence_chronology",{})
    if (evidence.get("first_result_json_sha256")!=
        "5d4bca0efc079ec3ae58d1062d4c1fb4c0b6476b64d56eead6d79e39ae83edab"
        or evidence.get("first_scored_events")!=19916
        or evidence.get("first_heldout_physical_sites")!=43):
        raise ValueError("first empirical reference receipt identity changed")
    return cfg


def describe_matched_site_taxon_pairs(
    scores:Sequence[tuple[DielEvent,dict[str,float]]],
    plan:Mapping[str,object],
)->dict[str,Any]:
    """No new model fitting or outcome read; only caller-supplied frozen scores."""
    cfg=_expect_plan(plan)
    minimum=cfg["min_dedup_scored_events_in_each_season"]
    per_site_taxon_season_year:dict[
        tuple[str,str,str,int],list[float]
    ]=defaultdict(list)
    per_season_counts:Counter[tuple[str,str,str]]=Counter()
    taxon_year_sets:dict[str,set[int]]=defaultdict(set)
    all_site_seasons:dict[tuple[str,str],set[str]]=defaultdict(set)
    for event,score in scores:
        if (event.season_year not in (2022,2023)
            or not site_is_sealed(event.site_id)):
            raise ValueError("nonheldout score supplied to matched-cell diagnosis")
        gain=score.get("solar_over_clock")
        if not isinstance(gain,(float,int)) or not math.isfinite(float(gain)):
            raise ValueError("nonfinite or missing original paired score")
        per_site_taxon_season_year[
            event.site_id,event.species,event.season,event.season_year
        ].append(float(gain))
        per_season_counts[event.site_id,event.species,event.season]+=1
        taxon_year_sets[event.species].add(event.season_year)
        all_site_seasons[event.site_id,event.species].add(event.season)
    per_pair_season:dict[
        tuple[str,str,str],list[float]
    ]=defaultdict(list)
    for (site,taxon,season,_year),values in per_site_taxon_season_year.items():
        per_pair_season[site,taxon,season].append(float(np.mean(values)))
    identified_pairs=sorted(
        (site,taxon)
        for site,taxon in all_site_seasons
        if all(
            per_season_counts[site,taxon,season]>=minimum
            for season in SEASONS
        )
    )
    if len(identified_pairs)<cfg["min_total_paired_site_taxon_cells_to_report"]:
        raise ValueError("insufficient predeclared matched site x taxon pairs")
    pair_rows=[]
    for site,taxon in identified_pairs:
        winter=float(np.mean(per_pair_season[site,taxon,"winter"]))
        summer=float(np.mean(per_pair_season[site,taxon,"summer"]))
        pair_rows.append((site,taxon,winter,summer,winter-summer))
    def stats(rows):
        w=np.asarray([r[2] for r in rows],dtype=float)
        s=np.asarray([r[3] for r in rows],dtype=float)
        d=w-s
        return {
            "winter_equal_cell_mean":float(np.mean(w)),
            "summer_equal_cell_mean":float(np.mean(s)),
            "winter_minus_summer_mean":float(np.mean(d)),
            "winter_minus_summer_median":float(np.median(d)),
            "winter_minus_summer_q25":float(np.quantile(d,.25)),
            "winter_minus_summer_q75":float(np.quantile(d,.75)),
            "winter_positive_summer_negative_cell_count":int(np.sum((w>0)&(s<0))),
            "winter_negative_summer_positive_cell_count":int(np.sum((w<0)&(s>0))),
            "winter_better_than_summer_cell_count":int(np.sum(d>0)),
            "winter_worse_than_summer_cell_count":int(np.sum(d<0)),
        }
    site_means:dict[str,list[tuple]]=defaultdict(list)
    taxon_means:dict[str,list[tuple]]=defaultdict(list)
    for row in pair_rows:
        site_means[row[0]].append(row)
        taxon_means[row[1]].append(row)
    taxon_rows=[]
    for taxon,rows in sorted(taxon_means.items()):
        if len(rows)<cfg["min_pairs_to_report_individual_taxon"]:
            continue
        summary=stats(rows)
        taxon_rows.append({
            "taxon":taxon,
            "matched_physical_sites":len(rows),
            "scored_future_years":len(taxon_year_sets[taxon]),
            "meets_both_future_years":len(taxon_year_sets[taxon])>=2,
            "wild_identified_binomial_name":(
                taxon not in NON_WILD_OR_UNRESOLVED
                and not taxon.endswith(" sp.")
                and len(taxon.split())==2
            ),
            **summary,
        })
    def across_groups(source:Mapping[str,list[tuple]])->dict[str,float]:
        w=[float(np.mean([r[2] for r in rows])) for rows in source.values()]
        s=[float(np.mean([r[3] for r in rows])) for rows in source.values()]
        return {
            "winter":float(np.mean(w)),
            "summer":float(np.mean(s)),
            "winter_minus_summer":float(np.mean(np.asarray(w)-np.asarray(s))),
        }
    secondary=[
        row for row in pair_rows
        if row[1] not in NON_WILD_OR_UNRESOLVED
        and not row[1].endswith(" sp.")
        and len(row[1].split())==2
    ]
    return {
        "schema_version":1,
        "method_version":METHOD,
        "category":"POST_OUTCOME_MATCHED_CELL_DESCRIPTION_ONLY",
        "original_ecological_v2_primary_reclassified":False,
        "all_reported_mean_gains_are_descriptive":True,
        "matched_cell_min_events_per_season":minimum,
        "matched_site_taxon_pairs":len(pair_rows),
        "physical_sites_with_at_least_one_paired_taxon":len(site_means),
        "taxa_with_at_least_one_matched_pair":len(taxon_means),
        "all_reported_matched_pairs":stats(pair_rows),
        "site_balanced_matched_pairs":across_groups(site_means),
        "taxon_balanced_matched_pairs":across_groups(taxon_means),
        "wild_identified_mammal_like_matched_pairs_count":len(secondary),
        "wild_identified_mammal_like_site_pair_descriptive":stats(secondary) if secondary else None,
        "taxon_rows_with_at_least_three_paired_sites":taxon_rows,
        "taxon_year_support_across_all_scored_events":{
            taxon:{"observed_future_year_count":len(years),
                   "observed_both_2022_2023":len(years)==2}
            for taxon,years in sorted(taxon_year_sets.items())
        },
        "same_site_taxon_paired_winter_summer_verified":True,
        "photo_detection_effort_bias_removed":False,
        "causal_solar_mechanism_identified":False,
        "all_new_p_values_or_confirmatory_interval_computed":False,
        "no_individual_site_ids_or_detection_time_values_output":True,
        "source_first_results_reclassified":False,
    }


def run_original_v2_matched_diagnostic(
    archive_bytes:bytes,
    original_v2_plan:Mapping[str,object],
    matched_plan:Mapping[str,object],
)->dict[str,Any]:
    _expect_plan(matched_plan)
    validate_v2_contract(original_v2_plan)
    members=_member_zip_csv(archive_bytes)
    events,source_audit=v2_events_from_two_tables(
        members["RI_CameraSurvey_Deployments.csv"],
        members["RI_CameraSurvey_Detections.csv"],
        original_v2_plan,
    )
    train=[e for e in events if e.season_year<=2021 and not site_is_sealed(e.site_id)]
    future=[e for e in events if e.season_year>=2022 and site_is_sealed(e.site_id)]
    profiles,train_audit=fit_species_profiles(train)
    scored=[
        (e,score_new_site_future_year(e,profiles[e.species]))
        for e in future if e.species in profiles
    ]
    first=matched_plan["evidence_chronology"]
    if len(scored)!=first["first_scored_events"]:
        raise ValueError("original scored count could not be exactly replayed")
    if len({e.site_id for e,_ in scored})!=first["first_heldout_physical_sites"]:
        raise ValueError("original heldout physical site count changed")
    original=summarize_site_level_transfer(scored)
    for season in SEASONS:
        observed=original["season_groups"][season]["metrics"][
            "solar_over_clock"
        ]["mean"]
        expected=first[f"{season}_first_site_weighted_solar_over_clock_nats"]
        tolerance=matched_plan["exact_scoring"][
            "max_abs_tolerance_for_reproduced_first_winter_summer_mean"
        ]
        if not abs(observed-expected)<=tolerance:
            raise ValueError("original frozen mean log score did not exactly replay")
    matched=describe_matched_site_taxon_pairs(scored,matched_plan)
    return {
        "schema_version":1,
        "analysis_id":"ri-v2-solar-clock-matched-site-taxon-pair-v0",
        "status":matched["category"],
        "first_v2_scientific_status":"EXPLORATORY_NOT_SUPPORTED_OR_UNAVAILABLE",
        "pinned_archive_md5_verified":True,
        "source_original_v2_schema_unchanged":True,
        "original_v2_scoring_means_reproduced_before_decomposition":True,
        "original_source_scored_event_count":len(scored),
        "original_v2_winter_mean":original["season_groups"]["winter"]["metrics"]["solar_over_clock"]["mean"],
        "original_v2_summer_mean":original["season_groups"]["summer"]["metrics"]["solar_over_clock"]["mean"],
        "source_audit_aggregate":{
            "source_detection_image_row_count":source_audit["source_detection_image_row_count"],
            "retained_30min_events":source_audit["detection_filter_counts"].get("retained_independent_30min_detection_events"),
        },
        "training_taxa":len(profiles),
        "matched_pair_description":matched,
        "primary_solar_both_seasons_supported":False,
        "inference_confirmatory":False,
        "prior_v0_v1_v2_results_reclassified":False,
        "sampling_iid_or_camera_uptime_proven":False,
    }
