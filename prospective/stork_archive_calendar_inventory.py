#!/usr/bin/env python3
"""Pure timing and horizontal-coverage inventory of frozen Movebank stork GPS.

Never access any altitude values or assess altitude missingness, mean, variance.
This is a follow-up to terminal no-2014-record preflight; not a rescue of that
pre-registered test, but a source inventory to choose a *new* future protocol.
"""
from __future__ import annotations
import argparse,csv,io,json,zipfile
from collections import Counter,defaultdict
from pathlib import Path
from .stork_2014_xytime_source_screen import (
    EXPECTED_NAME,EXPECTED_MD5,REFERENCE_NAME,REFERENCE_MD5,check,read_reference
)


def inspect_calendar(rows,stages):
    raw_years=Counter()
    unique_ids_by_year=defaultdict(set)
    speed_birds=defaultdict(set)
    speed_events=Counter()
    by_month=Counter()
    stage_flight_by_year=defaultdict(lambda:defaultdict(set))
    n=0
    for r in rows:
        n+=1
        d=(r.get("timestamp") or "").strip()
        bird=(r.get("individual-local-identifier") or "").strip()
        try:
            year=int(d[:4]);month=int(d[5:7])
        except (ValueError,TypeError):continue
        if not 1900<=year<=2100 or not 1<=month<=12:continue
        raw_years[year]+=1
        if not bird:continue
        unique_ids_by_year[year].add(bird)
        by_month[(year,month)]+=1
        try:
            speed=float(r.get("ground-speed"))
            lon=float(r.get("location-long"))
            lat=float(r.get("location-lat"))
        except (TypeError,ValueError):
            continue
        if not (5<=speed<=55 and -180<=lon<=180 and -86<=lat<=86):continue
        if (r.get("visible") or "").lower()=="false":continue
        speed_events[year]+=1
        speed_birds[year].add(bird)
        stage_flight_by_year[year][stages.get(bird,"unknown")].add(bird)
    metadata={}
    for year in sorted(raw_years):
        metadata[year]={
            "raw_GPS_rows":raw_years[year],
            "unique_birds_with_any_GPS":len(unique_ids_by_year[year]),
            "raw_flight_speed_GPS_rows":speed_events[year],
            "distinct_birds_with_flight_speed_GPS":len(speed_birds[year]),
            "distinct_flight_birds_by_age_label":{
                age:len(ids) for age,ids in sorted(stage_flight_by_year[year].items())
            },
            "raw_monthly_GPS_rows":{
                str(month):by_month[year,month] for month in range(1,13)
                if by_month[year,month]
            }
        }
    valid=[year for year in sorted(raw_years) if len(speed_birds[year])>=10]
    return {
        "mode":"OUTCOME_BLIND_SOURCE_CALENDAR_INVENTORY_ONLY",
        "source_record":"10.5441/001/1.hn1bd23k",
        "raw_total_rows":n,
        "year_counts":metadata,
        "preoutcome_latest_year_10plus_birds":max(valid) if valid else None,
        "GPS_height_values_read":False,
        "GPS_height_missingness_tested":False,
        "ecological_outcome_tested":False,
        "old_2014_hypothesis_terminal":"2014 unavailable because archive contains no GPS events in 2014; no adaptive year switch within old endpoint",
        "next_source_plan":"Use largest latest year with >=10 independent bird identifiers as a new prospective phase before inspecting any heights, preserving source-year history."
    }


def main():
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument("--gps-zip",type=Path,required=True)
    p.add_argument("--reference",type=Path,required=True)
    p.add_argument("--output",type=Path,required=True)
    a=p.parse_args()
    check(a.gps_zip,EXPECTED_NAME,EXPECTED_MD5)
    check(a.reference,REFERENCE_NAME,REFERENCE_MD5)
    with a.reference.open("r",newline="",encoding="utf-8-sig") as f:
        stages,meta=read_reference(csv.DictReader(f))
    with zipfile.ZipFile(a.gps_zip) as z:
        members=[m for m in z.namelist() if m.lower().endswith(".csv") and not m.startswith("__MACOSX")]
        if len(members)!=1:raise ValueError("Unexpected archive structure")
        with z.open(members[0]) as inner,io.TextIOWrapper(inner,encoding="utf-8-sig",newline="") as text:
            result=inspect_calendar(csv.DictReader(text),stages)
    result["reference"]=meta
    a.output.parent.mkdir(parents=True,exist_ok=True)
    a.output.write_text(json.dumps(result,indent=2,sort_keys=True)+"\n")
    print(json.dumps({
       "years":{k:{"GPS_birds":v["unique_birds_with_any_GPS"],
                   "flight_speed_birds":v["distinct_birds_with_flight_speed_GPS"]}
                for k,v in result["year_counts"].items()},
       "next_frozen_source_year":result["preoutcome_latest_year_10plus_birds"],
       "altitude_opened":False
    },sort_keys=True))


if __name__=="__main__":
    main()
