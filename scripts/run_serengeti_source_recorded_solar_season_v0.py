#!/usr/bin/env python3
"""Exploratory solar-season photo-time analysis, source/claim ceiling frozen in
research/SERENGETI_SOLAR_SEASON_RECORDED_EVENT_V0_CONTRACT.json.

This is NOT independently verified hourly camera operation, q calibration,
genuine latent animal activity, causation or new-region ecological inference.
No exact site coordinates or event-level times leave the local analysis.
"""
from __future__ import annotations

import argparse
from collections import Counter, defaultdict
import csv
from datetime import date, datetime, timedelta
import hashlib
import json
import math
from pathlib import Path
from typing import Any

from pyproj import Transformer
from scripts.assess_serengeti_solstice_mirror_effort_v0 import (
    EFFORT_MD5, MIN_MIRROR_PAIRS, mirror_pairs, merge_intervals, parse_date
)

CONSENSUS_MD5 = "5ed2d32fd09127c178cf9dca8ccfd623"
TZ_HOURS = 3
REFRACTION_ZENITH_DEGREES = 90.833
DAYLENGTH_MISMATCH_MAX_MINUTES = 1.0
# Original observational quality/independence controls from frozen N2 lane.
CERTAINTY_MIN = 0.8
INDEPENDENCE_MINUTES = 30
EXCLUDED = {"human", "birdother", "otherbird", "reptiles", "reptile", "rodents", "rodent"}


def md5_file(path: Path) -> str:
    d=hashlib.md5()
    with path.open("rb") as handle:
        for chunk in iter(lambda:handle.read(1<<20),b""):
            d.update(chunk)
    return d.hexdigest()


def colmap(names) -> dict[str,str]:
    if not names:
        raise ValueError("NO_CSV_FIELDS")
    return {"".join(c for c in n.casefold() if c.isalnum()):n for n in names}


def key(cols, name):
    norm="".join(c for c in name.casefold() if c.isalnum())
    if norm not in cols:
        raise ValueError("MISSING_SOURCE_COLUMN_"+name)
    return cols[norm]


def load_effort(path: Path):
    if md5_file(path)!=EFFORT_MD5:
        raise ValueError("SOURCE_EFFORT_MD5_MISMATCH")
    per=defaultdict(list)
    with path.open(newline="",encoding="utf-8-sig") as handle:
        dr=csv.DictReader(handle)
        cols=colmap(dr.fieldnames)
        for row in dr:
            site=row[key(cols,"SiteID")].strip()
            if not site:
                raise ValueError("MISSING_SOURCE_PHYSICAL_SITE")
            per[site].append((
                parse_date(row[key(cols,"Start date")]),
                parse_date(row[key(cols,"End date")]),
            ))
    merged={site:merge_intervals(v) for site,v in per.items()}
    base={}
    all_pair_count=0
    any_cycle_site_count=0
    for site,interval in merged.items():
        site_cycles={}
        for year in range(min(a.year for a,b in interval)-1,
                          max(b.year for a,b in interval)+1):
            pairs=mirror_pairs(interval,year)
            all_pair_count+=len(pairs)
            if len(pairs)>=MIN_MIRROR_PAIRS:
                site_cycles[year]=pairs
        if site_cycles:
            any_cycle_site_count+=1
            base[site]=site_cycles
    if (len(per),all_pair_count,any_cycle_site_count)!=(225,25016,186):
        raise ValueError("ORIGINAL_20261015_SOURCE_ONLY_DATE_PREFLIGHT_MISMATCH")
    return base,merged


def parse_timestamp(s: str) -> datetime:
    return datetime.fromisoformat(s.strip())


def solar_boundaries(d: date, lat: float, lon: float) -> tuple[float,float,float]:
    """NOAA fractional-year approximation, solar sunrise/sunset in local minutes."""
    n=d.timetuple().tm_yday
    leap=(d.year%4==0 and (d.year%100!=0 or d.year%400==0))
    gamma=2*math.pi/(366 if leap else 365)*(n-1)
    eq=229.18*(.000075+.001868*math.cos(gamma)-.032077*math.sin(gamma)
               -.014615*math.cos(2*gamma)-.040849*math.sin(2*gamma))
    dec=(.006918-.399912*math.cos(gamma)+.070257*math.sin(gamma)
         -.006758*math.cos(2*gamma)+.000907*math.sin(2*gamma)
         -.002697*math.cos(3*gamma)+.00148*math.sin(3*gamma))
    phi=math.radians(lat)
    cosha=(math.cos(math.radians(REFRACTION_ZENITH_DEGREES))/
           (math.cos(phi)*math.cos(dec))-math.tan(phi)*math.tan(dec))
    if abs(cosha)>1:
        raise ValueError("NO_SUNRISE_SUNSET_AT_SOURCE_SITE_DATE")
    ha=math.degrees(math.acos(cosha))
    noon=720-4*lon-eq+60*TZ_HOURS
    sunrise=noon-4*ha
    sunset=noon+4*ha
    return sunrise,sunset,sunset-sunrise


def zone(t: datetime, lat: float, lon: float) -> str:
    sunrise,sunset,_=solar_boundaries(t.date(),lat,lon)
    minutes=t.hour*60+t.minute+t.second/60.0
    if minutes<sunrise or minutes>=sunset:
        return "night"
    left=sunrise+(sunset-sunrise)*.25
    right=sunrise+(sunset-sunrise)*.75
    return "core" if left<=minutes<right else "edge"


def tax_norm(s: str) -> str:
    return "".join(c for c in s.casefold() if c.isalnum())


def _odds(left_a:float,left_b:float,right_a:float,right_b:float):
    if min(left_a,left_b,right_a,right_b)<=0:
        return None
    return (left_a/left_b)/(right_a/right_b)


def _mh(strata: list[tuple[str,int,int,int,int]]):
    # (site, falling target, falling comparator, rising target, rising comparator).
    numerator=denominator=0.0
    for site,a,b,c,d in strata:
        n=a+b+c+d
        if n:
            numerator+=a*d/n
            denominator+=b*c/n
    if not numerator or not denominator:
        return None
    return numerator/denominator


def summarize_taxon(species:str, cells:dict):
    tot=defaultdict(Counter)
    for (site,cycle,branch),counts in cells.items():
        tot[branch].update(counts)
    up=tot["rising"];down=tot["falling"]
    branch_counts={k:{z:int(tot[k][z]) for z in ("core","edge","night")}
                   for k in ("rising","falling")}
    strata_edge=[]
    strata_night=[]
    both=0
    observed_site_ids=set()
    for (site,cy,b),counts in cells.items():
        observed_site_ids.add(site)
    tuples=sorted({(site,cy) for site,cy,branch in cells})
    for site,cy in tuples:
        f=cells.get((site,cy,"falling"),Counter())
        r=cells.get((site,cy,"rising"),Counter())
        if sum(f.values()) and sum(r.values()):
            both+=1
        strata_edge.append((site,f["edge"],f["core"],r["edge"],r["core"]))
        strata_night.append((site,f["night"],f["core"]+f["edge"],
                             r["night"],r["core"]+r["edge"]))
    edge_mh=_mh(strata_edge)
    night_mh=_mh(strata_night)
    e_lo=[]
    n_lo=[]
    for site in sorted(observed_site_ids):
        e=_mh([s for s in strata_edge if s[0]!=site])
        n=_mh([s for s in strata_night if s[0]!=site])
        if e is not None: e_lo.append(e)
        if n is not None: n_lo.append(n)
    return {
        "species":species,
        "source_camera_events_by_branch_solar_zone":branch_counts,
        "events_all_zones":int(sum(up.values())+sum(down.values())),
        "recorded_on_both_branches_site_cycles":both,
        "recording_sites_with_any_detection":len(observed_site_ids),
        "eligible_descriptive_display":(
             sum(up.values())>=100 and sum(down.values())>=100 and both>=10),
        "pooled_edge_core_falling_vs_rising_record_odds":_odds(down["edge"],down["core"],up["edge"],up["core"]),
        "pooled_night_day_falling_vs_rising_record_odds":_odds(down["night"],down["core"]+down["edge"],up["night"],up["core"]+up["edge"]),
        "site_cycle_stratified_MH_record_odds_edge_core":edge_mh,
        "site_cycle_stratified_MH_record_odds_night_day":night_mh,
        "leave_one_physical_site_out_MH_edge_core_min_max":(
            [min(e_lo),max(e_lo)] if e_lo else None),
        "leave_one_physical_site_out_MH_night_day_min_max":(
            [min(n_lo),max(n_lo)] if n_lo else None),
    }


def run(consensus:Path,effort:Path)->dict:
    if md5_file(consensus)!=CONSENSUS_MD5:
        raise ValueError("SOURCE_CONSENSUS_MD5_MISMATCH")
    cycles,effort_intervals=load_effort(effort)
    coordinate_utm={}
    coordinate_conflicts=set()
    event_candidates=[]
    source_rows=0
    filtered_uncertain=0
    with consensus.open(newline="",encoding="utf-8-sig") as handle:
        rd=csv.DictReader(handle)
        cols=colmap(rd.fieldnames)
        # Require official raw station positions: no representative-site invention.
        s_col=key(cols,"SiteID")
        dt_col=key(cols,"DateTime")
        sp_col=key(cols,"Species")
        vote_col=key(cols,"NumVotes")
        classifier_col=key(cols,"NumClassifications")
        x_col=key(cols,"LocationX")
        y_col=key(cols,"LocationY")
        for row in rd:
            source_rows+=1
            site=row[s_col].strip()
            if site not in cycles:
                continue
            try:
                x=float(row[x_col]); y=float(row[y_col])
                if not math.isfinite(x) or not math.isfinite(y):
                    raise ValueError
                old=coordinate_utm.get(site)
                if old and math.hypot(x-old[0],y-old[1])>500:
                    coordinate_conflicts.add(site)
                elif old is None:
                    coordinate_utm[site]=(x,y)
            except (ValueError,TypeError):
                pass
            try:
                observed=parse_timestamp(row[dt_col])
                species=row[sp_col].strip()
                votes=float(row[vote_col])
                classifiers=float(row[classifier_col])
            except (ValueError,TypeError,KeyError):
                continue
            if (not species or classifiers<=0 or votes/classifiers<CERTAINTY_MIN or
                tax_norm(species) in EXCLUDED):
                filtered_uncertain+=1
                continue
            # Independence de-dup across the COMPLETE eligible station record.
            event_candidates.append((site,species,observed))
    transform=Transformer.from_crs("EPSG:21036","EPSG:4326",always_xy=True)
    geo={}
    for site,(x,y) in coordinate_utm.items():
        if site in coordinate_conflicts: continue
        lon,lat=transform.transform(x,y)
        if (-6<=lat<=3 and 31<=lon<=38 and math.isfinite(lon) and math.isfinite(lat)):
            geo[site]=(lat,lon)
    if len(geo)<0.8*len(cycles):
        return {
            "status":"HOLD_SOURCE_UTM_COORDINATE_SUPPORT_BELOW_80_PERCENT",
            "source_valid_coordinate_sites":len(geo),
            "source_eligible_sites":len(cycles),
            "results_opened":False,
        }

    eligible_day_map={}
    daylength_mismatches=[]
    for site,year_to_pairs in cycles.items():
        if site not in geo: continue
        lat,lon=geo[site]
        for year,pairs in year_to_pairs.items():
            for rising,falling in pairs:
                _,_,day_r=solar_boundaries(rising,lat,lon)
                _,_,day_f=solar_boundaries(falling,lat,lon)
                diff=abs(day_r-day_f)
                if diff<=DAYLENGTH_MISMATCH_MAX_MINUTES:
                    daylength_mismatches.append(diff)
                    eligible_day_map[(site,rising)]=(year,"rising")
                    eligible_day_map[(site,falling)]=(year,"falling")
    event_candidates.sort(key=lambda x:(x[0],x[1],x[2]))
    last_seen={}
    retained=0
    temporal_cells=defaultdict(lambda:defaultdict(Counter))
    deduplicated=0
    invalid_time=0
    for site,species,dt in event_candidates:
        prior=last_seen.get((site,species))
        if prior and dt-prior<timedelta(minutes=INDEPENDENCE_MINUTES):
            deduplicated+=1
            continue
        last_seen[(site,species)]=dt
        pair=eligible_day_map.get((site,dt.date()))
        if pair is None:
            continue
        try:
            z=zone(dt,*geo[site])
        except (ValueError,KeyError):
            invalid_time+=1
            continue
        cy,branch=pair
        temporal_cells[species][(site,cy,branch)][z]+=1
        retained+=1

    summaries=[summarize_taxon(species,temporal_cells[species])
              for species in sorted(temporal_cells)]
    return {
        "status":"EXPLORATORY_SOURCE_RECORDED_TIME_ONLY_NOT_LATENT_ACTIVITY",
        "source":{"consensus_md5":CONSENSUS_MD5,"effort_md5":EFFORT_MD5,
                  "source_total_consensus_rows":source_rows,
                  "candidate_quality_source_records":len(event_candidates),
                  "excluded_by_classification_or_taxonomy":filtered_uncertain,
                  "within_site_species_30min_deduplicated":deduplicated,
                  "retained_events_on_solar_matched_source_date_pairs":retained},
        "source_site_support":{
            "sites_with_original_20plus_calendar_mirror_pairs":len(cycles),
            "sites_with_valid_stable_public_source_geometry":len(geo),
            "accepted_solar_matched_site_day_pairs":len(daylength_mismatches),
            "median_absolute_photoperiod_mismatch_minutes":(
                sorted(daylength_mismatches)[len(daylength_mismatches)//2]
                if daylength_mismatches else None),
            "max_absolute_photoperiod_mismatch_minutes":(
                max(daylength_mismatches) if daylength_mismatches else None),
            "invalid_solar_zone_timestamps":invalid_time,
        },
        "taxa":summaries,
        "counts_provenance":"Original Snapshot Serengeti published exact CSV MD5s; all results PHOTO DETECTIONS, not animal-independent movement",
        "same_region_cross_site_only":True,
        "independently_verified_station_zone_on_hours":False,
        "independent_detector_q_reference":False,
        "true_activity_or_seasonal_memory_identified":False,
        "independent_out_of_region_replication":False,
        "original_n2_terminal_reclassified":False,
    }


def main():
    parser=argparse.ArgumentParser()
    parser.add_argument("--consensus",required=True,type=Path)
    parser.add_argument("--effort",required=True,type=Path)
    parser.add_argument("--output",required=True,type=Path)
    args=parser.parse_args()
    result=run(args.consensus,args.effort)
    args.output.parent.mkdir(parents=True,exist_ok=True)
    args.output.write_text(json.dumps(result,ensure_ascii=False,indent=2,sort_keys=True)+"\n")
    print(json.dumps({
        "status":result["status"],
        "original_consensus_rows":result.get("source",{}).get("source_total_consensus_rows",0),
        "retained_matched_events":result.get("source",{}).get("retained_events_on_solar_matched_source_date_pairs",0),
        "source_geom_sites":result.get("source_site_support",{}).get("sites_with_valid_stable_public_source_geometry",0),
        "matched_date_pairs":result.get("source_site_support",{}).get("accepted_solar_matched_site_day_pairs",0),
        "taxa_with_events":len(result.get("taxa",[])),
        "taxa_summary":[
          {
           "species":x["species"],
           "events":x["events_all_zones"],
           "n_sitecycle_two_branch":x["recorded_on_both_branches_site_cycles"],
           "MH_edge_core":x["site_cycle_stratified_MH_record_odds_edge_core"],
           "MH_night_day":x["site_cycle_stratified_MH_record_odds_night_day"],
           "descriptive_display":x["eligible_descriptive_display"],
          } for x in result.get("taxa",[]) if x["eligible_descriptive_display"]
        ],
        "latent_activity_identified":False,
    },sort_keys=True))


if __name__=="__main__":
    main()
