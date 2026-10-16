#!/usr/bin/env python3
"""Snapshot Serengeti: within-camera photo timing vs among-camera PHOTO mix.

All outputs are exploratory PHOTO-detection descriptive quantities, not
animal behavior, migration, or camera q/uptime-corrected activity. The algebra
decomposes ONLY a common PHOTO-positive camera roster C, explicitly NOT
the all-camera species population. See matching frozen contract.
"""
from __future__ import annotations

import argparse
from collections import Counter, defaultdict
from datetime import timedelta
import json
import math
from pathlib import Path

from scripts.run_serengeti_photo_weather_cycle_alignment_v0 import (
    original_first_receipt_verified, raw_source_data
)
from scripts.run_serengeti_same_station_trophic_photo_time_v0 import (
    derive_calendar_eligibility
)
from scripts.run_serengeti_source_recorded_solar_season_v0 import (
    INDEPENDENCE_MINUTES, load_effort, zone
)

YEARS=(2010, 2011, 2012)
FOCAL=("zebra","wildebeest","gazelleThomsons","hyenaSpotted",
       "buffalo","giraffe","lionFemale")
SOURCE_EXPECTED_EVENTS=38792
SOURCE_EXPECTED_SITES=186

def safe_div(a,b):
    return a/b if b>0 else None

def source_time_night(counts:Counter)->int:
    return int(counts.get("night",0))

def source_time_day(counts:Counter)->int:
    return int(counts.get("core",0)+counts.get("edge",0))

def compute_common_support_decomposition(
    source_by_camera:dict[str,dict[str,Counter]],
)->dict:
    """Exact symmetric Kitagawa arithmetic under same-camera PHOTO positivity.

    source_by_camera[site]["rising"|"falling"] contains source-record counts
    for solar NIGHT and all DAYLIGHT. Missing calendar branch treated as
    ZERO PHOTO COUNTS (never as zero hardware exposure).
    """
    all_sites=sorted(source_by_camera)
    full={b:{"night":0,"day":0,"photos":0,"photo_positive_sites":0}
          for b in ("rising","falling")}
    common=[]
    for site in all_sites:
        branches=source_by_camera[site]
        N={}
        for b in ("rising","falling"):
            c=branches.get(b,Counter())
            night=source_time_night(c)
            day=source_time_day(c)
            total=night+day
            N[b]=total
            full[b]["night"]+=night
            full[b]["day"]+=day
            full[b]["photos"]+=total
            if total:
                full[b]["photo_positive_sites"]+=1
        if N["rising"] and N["falling"]:
            common.append(site)

    result={
        "source_sites_with_either_branch_photo":len(all_sites),
        "source_sites_with_rising_photo":full["rising"]["photo_positive_sites"],
        "source_sites_with_falling_photo":full["falling"]["photo_positive_sites"],
        "common_photo_positive_camera_count":len(common),
        "rising_photo_records_all_sites":full["rising"]["photos"],
        "falling_photo_records_all_sites":full["falling"]["photos"],
        "all_sites_night_photo_fraction":{
            b:safe_div(full[b]["night"],full[b]["photos"])
            for b in ("rising","falling")
        },
    }
    ra=result["all_sites_night_photo_fraction"]["rising"]
    fa=result["all_sites_night_photo_fraction"]["falling"]
    result["all_site_photo_night_fraction_change"]=(
        fa-ra if fa is not None and ra is not None else None
    )

    totals={b:sum(
        source_time_night(source_by_camera[i].get(b,Counter()))+
        source_time_day(source_by_camera[i].get(b,Counter()))
        for i in common
    ) for b in ("rising","falling")}
    result["common_photo_records"]={b:int(totals[b]) for b in totals}
    result["common_photo_fraction_of_all_records"]={
        b:safe_div(totals[b],full[b]["photos"]) for b in totals
    }

    if not common or not totals["rising"] or not totals["falling"]:
        result.update({
            "common_photo_night_fraction_change":None,
            "within_station_photo_schedule_term":None,
            "among_station_photo_weight_term":None,
            "photo_station_total_variation":None,
            "composition_absolute_share":None,
            "decomposition_identity_error":None,
            "support_display_eligible":False,
            "status":"UNDEFINED_COMMON_PHOTO_ROSTER",
        })
        return result

    W=B=tv=pf=pr=0.0
    for site in common:
        def n_p_w(b):
            c=source_by_camera[site].get(b,Counter())
            n=source_time_night(c)
            N=n+source_time_day(c)
            assert N>0
            return n/N,N/totals[b]
        p_r,w_r=n_p_w("rising")
        p_f,w_f=n_p_w("falling")
        W+=0.5*(w_f+w_r)*(p_f-p_r)
        B+=0.5*(p_f+p_r)*(w_f-w_r)
        pf+=w_f*p_f
        pr+=w_r*p_r
        tv+=abs(w_f-w_r)*0.5
    delta=pf-pr
    mismatch=abs((W+B)-delta)
    if mismatch>1e-12:
        raise ValueError("DECOMPOSITION_IDENTITY_VIOLATION")
    share=safe_div(abs(B),abs(W)+abs(B))
    eligible=(len(common)>=20 and
              min(result["common_photo_fraction_of_all_records"].values())>=0.5 and
              full["rising"]["photos"]>=100 and full["falling"]["photos"]>=100)
    result.update({
        "common_photo_night_fraction_change":delta,
        "within_station_photo_schedule_term":W,
        "among_station_photo_weight_term":B,
        "photo_station_total_variation":tv,
        "composition_absolute_share":share,
        "decomposition_identity_error":mismatch,
        "support_display_eligible":eligible,
        "status":"DESCRIPTIVE_COMMON_PHOTO_ROSTER_DECOMPOSITION",
    })
    return result

def analyze(consensus:Path,effort:Path)->dict:
    original=original_first_receipt_verified(consensus,effort)
    cycles,_=load_effort(effort)
    geos,events=raw_source_data(consensus,set(cycles))
    if len(geos)!=SOURCE_EXPECTED_SITES:
        raise ValueError("FROZEN_FIRST_CAMERA_GEOMETRY_DRIFT")
    eligible,structural_sitecycles=derive_calendar_eligibility(cycles,geos)
    all_taxa=[x["species"] for x in original["taxa"]]
    known=set(all_taxa)
    cells=defaultdict(lambda:defaultdict(Counter))
    last={}
    used=0
    for site,sp,time in events:
        prior=last.get((site,sp))
        if prior is not None and time-prior<timedelta(minutes=INDEPENDENCE_MINUTES):
            continue
        last[(site,sp)]=time
        branch=eligible.get((site,time.date()))
        if branch is None:
            continue
        if sp not in known:
            raise ValueError("FROZEN_FIRST_TAXON_MEMBERSHIP_DRIFT")
        cycle,b=branch
        if cycle not in YEARS:
            raise ValueError("UNREGISTERED_SOLSTICE_CYCLE")
        cells[sp][(site,cycle,b)][zone(time,*geos[site])]+=1
        used+=1
    if used!=SOURCE_EXPECTED_EVENTS:
        raise ValueError("FROZEN_FIRST_SOURCE_PHOTO_COUNT_DRIFT")

    # Original all 43 source taxon×branch×zone complete replay lock.
    for tax in original["taxa"]:
        sp=tax["species"]
        totals=defaultdict(Counter)
        for (site,y,b),counts in cells[sp].items():
            totals[b].update(counts)
        for branch in ("rising","falling"):
            for z in ("core","edge","night"):
                expected=tax["source_camera_events_by_branch_solar_zone"][branch][z]
                if totals[branch][z]!=expected:
                    raise ValueError("FROZEN_FIRST_SOURCE_SPECIES_ZONE_DRIFT")

    summaries=[]
    for sp in all_taxa:
        peryear=[]
        for year in YEARS:
            source_site_counts=defaultdict(dict)
            for (site,cy,b),counts in cells[sp].items():
                if cy==year:
                    source_site_counts[site][b]=counts
            descriptor=compute_common_support_decomposition(source_site_counts)
            peryear.append({"solstice_cycle_year":year,**descriptor})
        summaries.append({
            "source_taxon":sp,
            "year_cycles":peryear,
        })

    candidate=[{"source_taxon":x["source_taxon"],
                 "year_cycles":[
                     {k:v for k,v in yr.items()
                      if k in ("solstice_cycle_year","common_photo_positive_camera_count",
                               "common_photo_fraction_of_all_records",
                               "common_photo_night_fraction_change",
                               "within_station_photo_schedule_term",
                               "among_station_photo_weight_term",
                               "photo_station_total_variation",
                               "support_display_eligible","status")}
                     for yr in x["year_cycles"]]
                } for x in summaries if x["source_taxon"] in FOCAL]

    return {
        "status":"EXPLORATORY_SERENGETI_COMMON_CAMERA_PHOTO_TIME_VERSUS_PHOTO_LOCATION",
        "source_first_result_sha256":
            "0b70f7425d8ade2489a989bebc7b22fda997d82b2190e5e7d3c5d6f83ee71ef3",
        "original_matched_source_photo_count_replayed":used,
        "original_matched_site_date_pairs_replayed":24290,
        "original_structural_source_camera_count":len(geos),
        "original_structural_site_cycles":len(structural_sitecycles),
        "all_source_taxon_labels":summaries,
        "focal_descriptive_after_prior_outcomes":candidate,
        "total_outcome_taxon_labels":len(summaries),
        "camera_site_identifiers_and_event_date_exported":False,
        "common_support_selected_on_positive_camera_photo_records":True,
        "independent_hourly_camera_uptime_or_detection_q_available":False,
        "true_mammal_migration_or_circadian_reallocation_identified":False,
        "other_independent_ecosystems_replicated":False,
        "interpretation":"Within-vs-composition exactly decomposes a same-taxon common-positive-photo camera NIGHT fraction. Station weights may reflect movement OR observation q/effort/detection. No animal behavior or habitat selection causality inferred.",
    }

def main()->None:
    parser=argparse.ArgumentParser()
    parser.add_argument("--consensus",type=Path,required=True)
    parser.add_argument("--effort",type=Path,required=True)
    parser.add_argument("--output",type=Path,required=True)
    a=parser.parse_args()
    try:
        r=analyze(a.consensus,a.effort)
    except (OSError,ValueError,TypeError,KeyError,IndexError) as exc:
        r={"status":"HOLD_FROZEN_SOURCE_OR_SOURCE_CALCULATION_FAILED",
           "error_type":type(exc).__name__,
           "biological_conclusion":None}
    a.output.parent.mkdir(parents=True,exist_ok=True)
    a.output.write_text(json.dumps(r,indent=2,sort_keys=True)+"\n",encoding="utf-8")
    log={
        "status":r["status"],
        "original_source_photo_events":r.get("original_matched_source_photo_count_replayed"),
        "original_taxa":r.get("total_outcome_taxon_labels"),
        "focal":[
            {"taxon":x["source_taxon"],
             "cycles":[{
                 "y":v["solstice_cycle_year"],
                 "n_common":v["common_photo_positive_camera_count"],
                 "common_coverage":v["common_photo_fraction_of_all_records"],
                 "d":v["common_photo_night_fraction_change"],
                 "within":v["within_station_photo_schedule_term"],
                 "composition":v["among_station_photo_weight_term"],
                 "tv":v["photo_station_total_variation"],
                 "support":v["support_display_eligible"],
             } for v in x["year_cycles"]]}
            for x in r.get("focal_descriptive_after_prior_outcomes",[])
        ],
        "latent_animal_behavior":False,
    }
    print(json.dumps(log,sort_keys=True))
    if r["status"].startswith("HOLD"):
        raise SystemExit(2)

if __name__=="__main__": main()
