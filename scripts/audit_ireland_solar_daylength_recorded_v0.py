#!/usr/bin/env python3
"""Published Caravaggi et al 2018 Northern Ireland source-record camera-time audit.

NO hardware ON-hours, independent q, true wildlife activity inference, p-value,
or out-of-region validation. Source dates with recorded photos determine source
date eligibility, so the conditional comparison is **selection affected**.
"""
from __future__ import annotations
import argparse
from collections import Counter, defaultdict
import csv
from datetime import date, datetime
import hashlib
import json
import math
from pathlib import Path

GIT_BLOB_SHA = "2084dfac55acb75efe6e61c1abc306aeda0904eb"
BASE_ALL_ROWS = 9411
BASE_ORIGINAL_EXCLUDED_LABELS = {"Sika", "Muntjac", "Hedgehog", "Rat"}
BASE_ORIGINAL_INCLUDED_ROWS = 8761
MIRROR_TOL_MIN = 10
MIN_SOLSTICE_GAP_DAYS = 7
ALLOWED_YEARS = {2013, 2014, 2015, 2016}
SOURCE_FIELDS = ["site","spp_1","species","count","day","month","season",
                 "year","time","sunrise","sunset","m_60"]


def parse_minutes(value: str) -> float:
    xs=value.strip().split(":")
    if len(xs) not in (2,3):
        raise ValueError("INVALID_AUTHOR_SOLAR_OR_CLOCK_TIMESTAMP")
    v=[int(x) for x in xs]
    if v[0]<0 or v[0]>23 or v[1]<0 or v[1]>59 or (len(v)==3 and (v[2]<0 or v[2]>59)):
        raise ValueError("INVALID_AUTHOR_SOLAR_OR_CLOCK_TIMESTAMP")
    return v[0]*60+v[1]+(v[2]/60 if len(v)==3 else 0.0)


def zone(clock:float, sunrise:float, sunset:float) -> str:
    if clock < sunrise or clock >= sunset:
        return "night"
    dur=sunset-sunrise
    return "core" if sunrise+dur*.25 <= clock < sunrise+dur*.75 else "edge"


def mh(strata):
    a=b=0.0
    for x,y,z,w in strata:
        n=x+y+z+w
        if n>0:
            a+=x*w/n
            b+=y*z/n
    return a/b if a>0 and b>0 else None


def pooled(a,b,c,d):
    return (a*d)/(b*c) if min(a,b,c,d)>0 else None


def audit(input_csv: Path)->dict:
    raw=input_csv.read_bytes()
    digest=hashlib.sha1(b"blob "+str(len(raw)).encode()+b"\0"+raw).hexdigest()
    if digest != GIT_BLOB_SHA:
        raise ValueError("SOURCE_GIT_BLOB_SHA_MISMATCH")
    raw_year=Counter()
    rows=[]
    with input_csv.open(newline="",encoding="utf-8-sig") as h:
        rd=csv.DictReader(h)
        if rd.fieldnames != SOURCE_FIELDS:
            raise ValueError("AUTHOR_CSV_SCHEMA_CHANGED")
        for row in rd:
            rows.append(row)
            raw_year[row["year"]]+=1
    if len(rows) != BASE_ALL_ROWS:
        raise ValueError("AUTHOR_TOTAL_PHOTO_RECORD_ROWS_MISMATCH")
    biological_rows=[r for r in rows if r["spp_1"] not in BASE_ORIGINAL_EXCLUDED_LABELS]
    if len(biological_rows)!=BASE_ORIGINAL_INCLUDED_ROWS:
        raise ValueError("ORIGINAL_AUTHORS_8761_EXCLUSION_NOT_REPRODUCED")
    species=sorted({r["species"] for r in biological_rows})
    datezones={}
    conflicted_dates=set()
    for r in biological_rows:
        try:
            yy,mm,dd=(int(r[k]) for k in ("year","month","day"))
            if yy not in ALLOWED_YEARS:
                continue
            d=date(yy,mm,dd)
            sr=parse_minutes(r["sunrise"]);ss=parse_minutes(r["sunset"])
            if not (0<ss-sr<24*60):
                continue
        except (ValueError,TypeError):
            continue
        k=(r["site"],yy,d)
        if k in datezones:
            old=datezones[k]
            if abs(old[0]-sr)>3 or abs(old[1]-ss)>3:
                conflicted_dates.add(k)
        else:
            datezones[k]=(sr,ss)
    for k in conflicted_dates:
        datezones.pop(k,None)

    # Recorded photo days only: NOT independent actual camera ON-day support.
    by_site_year=defaultdict(lambda: {"rising":[],"falling":[]})
    for site,yy,d in datezones:
        solstice=date(yy,6,21)
        delta=(d-solstice).days
        if abs(delta)<MIN_SOLSTICE_GAP_DAYS:
            continue
        branch="rising" if delta<0 else "falling"
        sunrise,sunset=datezones[(site,yy,d)]
        by_site_year[(site,yy)][branch].append((d,sunset-sunrise))
    match_pairs_by_site_year={}
    all_eligible=set()
    for k,v in by_site_year.items():
        pairs=[(d0,d1) for d0,dl0 in v["rising"]
                        for d1,dl1 in v["falling"]
                        if abs(dl0-dl1)<=MIRROR_TOL_MIN]
        if not pairs: continue
        match_pairs_by_site_year[k]=len(pairs)
        for left,right in pairs:
            all_eligible.add((k[0],k[1],left,"rising"))
            all_eligible.add((k[0],k[1],right,"falling"))

    # Photo timing observations; source already represents author's
    # independent events. Do not create additional animal independence claims.
    pop=defaultdict(lambda:defaultdict(Counter))
    used=0
    by_taxon=Counter()
    no_date=0
    for r in biological_rows:
        try:
            y,m,d=(int(r[k]) for k in ("year","month","day"))
            if y not in ALLOWED_YEARS:
                no_date+=1
                continue
            obsdate=date(y,m,d)
            clock=parse_minutes(r["time"])
        except ValueError:
            no_date+=1
            continue
        rise_set=datezones.get((r["site"],y,obsdate))
        if rise_set is None:
            continue
        solstice=date(y,6,21)
        branch="rising" if obsdate<solstice else "falling"
        if (r["site"],y,obsdate,branch) not in all_eligible:
            continue
        pop[r["species"]][(r["site"],y,branch)][zone(clock,*rise_set)]+=1
        used+=1
        by_taxon[r["species"]]+=1

    summaries=[]
    for sp in species:
        obs=pop[sp]
        grand=defaultdict(Counter)
        groups=sorted(match_pairs_by_site_year)
        edge_s=[];night_s=[]
        for site,yy in groups:
            rise=obs.get((site,yy,"rising"),Counter())
            fall=obs.get((site,yy,"falling"),Counter())
            grand["rising"].update(rise)
            grand["falling"].update(fall)
            edge_s.append((site,fall["edge"],fall["core"],rise["edge"],rise["core"]))
            night_s.append((site,fall["night"],fall["edge"]+fall["core"],rise["night"],rise["edge"]+rise["core"]))
        a,b=grand["falling"],grand["rising"]
        all_sites=sorted({key[0] for key in groups})
        leave_out={}
        for tag,strata in [("edge_core",edge_s),("night_day",night_s)]:
            loo=[mh([line[1:] for line in strata if line[0]!=site]) for site in all_sites]
            loo=[x for x in loo if x is not None]
            leave_out[tag]=[min(loo),max(loo)] if loo else None
        summaries.append({
            "taxon":sp,
            "source_recorded_events_in_matched_recorded_day_windows":by_taxon[sp],
            "rising_zone_counts":{z:b[z] for z in ("core","edge","night")},
            "falling_zone_counts":{z:a[z] for z in ("core","edge","night")},
            "pooled_edge_core_OR":pooled(a["edge"],a["core"],b["edge"],b["core"]),
            "pooled_night_day_OR":pooled(a["night"],a["edge"]+a["core"],b["night"],b["edge"]+b["core"]),
            "site_year_stratified_MH_edge_core_OR":mh([s[1:] for s in edge_s]),
            "site_year_stratified_MH_night_day_OR":mh([s[1:] for s in night_s]),
            "leave_one_site_out_edge_core_MH_min_max":leave_out["edge_core"],
            "leave_one_site_out_night_day_MH_min_max":leave_out["night_day"],
        })
    top=max(match_pairs_by_site_year.values()) if match_pairs_by_site_year else 0
    return {
        "status":"EXPLORATORY_DETECTION_CONDITIONED_DATES_NO_HOURLY_CAMERA_OPERATION",
        "source":{"paper_doi":"10.7717/peerj.5827",
                  "original_git_tag":"v1.2.1","pinned_original_blob_sha1":digest,
                  "total_source_rows":len(rows),
                  "original_author_excluded_group_counts":{s:sum(r["spp_1"]==s for r in rows) for s in sorted(BASE_ORIGINAL_EXCLUDED_LABELS)},
                  "original_author_taxa_included_rows":len(biological_rows),
                  "year_value_counts_all_rows":dict(sorted(raw_year.items()))},
        "recorded_date_support":{
            "site_years_with_at_least_one_cross_branch_near_equal_daylength_photo_day_pair":len(match_pairs_by_site_year),
            "distinct_physical_site_names_in_record_day_pairs":len({k[0] for k in match_pairs_by_site_year}),
            "candidate_recorded_day_pairs":sum(match_pairs_by_site_year.values()),
            "largest_one_site_year_fraction_of_candidate_pairs":(
                top/sum(match_pairs_by_site_year.values())
                if match_pairs_by_site_year else None),
            "unique_matched_photographed_site_calendar_dates":len(all_eligible),
            "site_calendar_dates_with_conflicting_original_solar_times_removed":len(conflicted_dates),
            "documented_independent_physical_camera_on_hours":False,
            "selection_based_on_detection_day_presence":True
        },
        "source_recorded_events_in_matched_windows":used,
        "taxa":summaries,
        "true_animal_activity_identified":False,
        "independent_within_landscape_camera_sampling_inferred":False,
        "independent_additional_ecological_region":True,
        "confirmed_cross_region_seasonal_hysteresis":False,
        "causal_sun_vs_climate_evidence":False,
        "interpretation":"Matches only original camera photo-recorded dates; site-year matched photos cannot stand in for missing actual camera operation exposure, site q or independent animal passages. No p-values or causal conclusions."
    }


def main():
    p=argparse.ArgumentParser()
    p.add_argument("--source",type=Path,required=True)
    p.add_argument("--output",type=Path,required=True)
    args=p.parse_args()
    result=audit(args.source)
    args.output.parent.mkdir(parents=True,exist_ok=True)
    args.output.write_text(json.dumps(result,indent=2,sort_keys=True,ensure_ascii=False)+"\n")
    print(json.dumps({
        "status":result["status"],
        "original_included_rows":result["source"]["original_author_taxa_included_rows"],
        "site_years_with_photo_date_pairs":result["recorded_date_support"]["site_years_with_at_least_one_cross_branch_near_equal_daylength_photo_day_pair"],
        "matched_photo_day_pairs":result["recorded_date_support"]["candidate_recorded_day_pairs"],
        "matched_photo_record_events":result["source_recorded_events_in_matched_windows"],
        "max_one_site_year_candidate_pair_share":result["recorded_date_support"]["largest_one_site_year_fraction_of_candidate_pairs"],
        "taxon_odds_recorded_only":[{"taxon":t["taxon"],"n":t["source_recorded_events_in_matched_recorded_day_windows"],
          "edge_core_OR":t["site_year_stratified_MH_edge_core_OR"],
          "night_day_OR":t["site_year_stratified_MH_night_day_OR"]}
          for t in result["taxa"]],
        "latent_behavior_supported":False,
    },sort_keys=True))


if __name__=="__main__":
    main()
