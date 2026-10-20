#!/usr/bin/env python3
"""Outcome-blind stationary GPS structural control for DELTATRACK 2021.

This program NEVER looks up GPS height, pressure, barometric height, or any
derived vertical outcome; only UTC time, horizontal coordinates, ID and speed.
"""
from __future__ import annotations

import argparse
from collections import Counter,defaultdict
import csv
import gzip
import hashlib
import json
import math
from pathlib import Path
from pyproj import Transformer

TAXA=("Larus argentatus","Larus fuscus")
EXPECTED_FILE="DELTATRACK-gps-2021.csv.gz"
EXPECTED_MD5="1a3145234cccd1a48b280b0fb485d679"
MIN_PER_DAY=20
MIN_SELF_OTHER_DAY=10
MIN_OTHERS_OTHER_DATE=10
MIN_REPEATED_DAYS=2
MIN_BIRDS=10


def _finite(value):
    try:return float(value)
    except (ValueError,TypeError):return float("nan")


def _projector():
    return Transformer.from_crs("EPSG:4326","EPSG:32631",always_xy=True)


def _checksum(path):
    md5=hashlib.md5()
    with path.open("rb") as stream:
        for chunk in iter(lambda:stream.read(1<<20),b""):md5.update(chunk)
    if path.name!=EXPECTED_FILE or md5.hexdigest()!=EXPECTED_MD5:
        raise ValueError("Frozen 2021 source mismatch")
    return md5.hexdigest()


def _support(earliest:dict, cellsize:int, taxon:str) ->dict:
    proj=_projector()
    by_bird_day=defaultdict(Counter)
    for (sp,bird,day,tm),(stamp,lon,lat) in earliest.items():
        if sp!=taxon:continue
        x,y=proj.transform(lon,lat)
        if not(math.isfinite(x) and math.isfinite(y)):continue
        cell=(math.floor(x/cellsize),math.floor(y/cellsize))
        by_bird_day[bird,day][cell]+=1
    qualified={}
    for (bird,day),cells in by_bird_day.items():
        # Horizontal-only deterministic mode; sort breaks a count tie.
        cell,n=sorted(cells.items(),key=lambda q:(-q[1],q[0]))[0]
        if n>=MIN_PER_DAY:
            qualified[bird,day]=(cell,n)

    own_cell=Counter();all_cell=Counter();date_cell=Counter()
    for (bird,day),(cell,n) in qualified.items():
        own_cell[bird,cell]+=n;all_cell[cell]+=n;date_cell[day,cell]+=n

    eligible_days=Counter()
    filtered_bins=0
    for (bird,day),(cell,n) in qualified.items():
        own_other_day=own_cell[bird,cell]-n
        other_individual_other_date=(
            all_cell[cell]-own_cell[bird,cell]-date_cell[day,cell]+n
        )
        if min(own_other_day,other_individual_other_date)<0:
            raise AssertionError("Count algebra must be nonnegative")
        if own_other_day>=MIN_SELF_OTHER_DAY and other_individual_other_date>=MIN_OTHERS_OTHER_DATE:
            eligible_days[bird]+=1
            filtered_bins+=n
    birds={bird for bird,days in eligible_days.items() if days>=MIN_REPEATED_DAYS}
    accepted_bins=sum(
        n for (bird,day),(cell,n) in qualified.items()
        if bird in birds and own_cell[bird,cell]-n>=MIN_SELF_OTHER_DAY
        and all_cell[cell]-own_cell[bird,cell]-date_cell[day,cell]+n>=MIN_OTHERS_OTHER_DATE
    )
    return {
        "cell_m":cellsize,
        "source_birds_with_stationary_proxy":len({k[0] for k in by_bird_day}),
        "source_bird_days":len(by_bird_day),
        "dominant_cell_bird_days_ge20":len(qualified),
        "dominant_cells_count":len({c for c,n in qualified.values()}),
        "days_meeting_repeated_self_and_other_support":sum(eligible_days.values()),
        "eligible_birds":len(birds),
        "eligible_days":sum(days for bird,days in eligible_days.items() if bird in birds),
        "eligible_scored_bins":accepted_bins,
        "structurally_admissible":len(birds)>=MIN_BIRDS,
        "outcome_tested":False,
    }


def inspect_stationary(rows)->dict:
    earliest={}
    c={t:Counter() for t in TAXA}
    for r in rows:
        taxon=(r.get("individual-taxon-canonical-name") or "").strip()
        if taxon not in TAXA:continue
        c[taxon]["raw_rows"]+=1
        if any((r.get(k) or "").strip().lower() in ("true","t","1","yes","y")
               for k in ("import-marked-outlier","manually-marked-outlier")):
            continue
        t=(r.get("timestamp") or "").strip()
        bird=(r.get("individual-local-identifier") or "").strip()
        try:
            year,month,hour,minute=int(t[:4]),int(t[5:7]),int(t[11:13]),int(t[14:16])
        except (ValueError,TypeError):continue
        if year!=2021 or month not in (5,6,7) or not bird:continue
        if not(0<=hour<24 and 0<=minute<60):continue
        x,y,v=_finite(r.get("location-long")),_finite(r.get("location-lat")),_finite(r.get("ground-speed"))
        if not all(map(math.isfinite,(x,y,v))):continue
        if not(-180<=x<=180 and -90<=y<=90 and 0<=v<=0.5):continue
        c[taxon]["raw_stationary_proxy"]+=1
        key=(taxon,bird,t[:10],hour*12+minute//5)
        if key not in earliest or t<earliest[key][0]:
            earliest[key]=(t,x,y)
    panels={}
    for taxon in TAXA:
        panels[taxon]={
            "raw_source_rows":int(c[taxon]["raw_rows"]),
            "raw_stationary_speed_rows":int(c[taxon]["raw_stationary_proxy"]),
            "primary_100m":_support(earliest,100,taxon),
            "sensitivity_500m":_support(earliest,500,taxon),
        }
    return {
        "status":"STATIONARY_XY_TIME_ONLY",
        "height_values_accessed":False,
        "height_outcomes_tested":False,
        "frozen_file":EXPECTED_FILE,
        "stationary_proxy":"ground_speed_0_to_0.5_m_per_s",
        "first_5min_events_by_species":{
            t:sum(key[0]==t for key in earliest) for t in TAXA
        },
        "species":panels,
        "claim_boundary":"No direct test of true stationary GPS instrument error or ecological identity.",
    }


def main():
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument("--gps",required=True,type=Path)
    p.add_argument("--output",required=True,type=Path)
    args=p.parse_args()
    digest=_checksum(args.gps)
    with gzip.open(args.gps,"rt",encoding="utf-8-sig",newline="") as f:
        reader=csv.DictReader(f)
        necessary={"timestamp","individual-taxon-canonical-name","individual-local-identifier",
                   "location-long","location-lat","ground-speed"}
        if not necessary<=set(reader.fieldnames or []):
            raise ValueError("Non-height source columns missing")
        result=inspect_stationary(reader)
    result["source_md5"]=digest
    result["contract"]="prospective/DELTATRACK_2021_STATIONARY_CONTROL_STRUCTURAL_V1.json"
    args.output.parent.mkdir(parents=True,exist_ok=True)
    args.output.write_text(json.dumps(result,indent=2,sort_keys=True)+"\n",encoding="utf-8")
    print(json.dumps({t:{"primary_birds":x["primary_100m"]["eligible_birds"],
                         "primary_days":x["primary_100m"]["eligible_days"],
                         "500m_birds":x["sensitivity_500m"]["eligible_birds"]}
               for t,x in result["species"].items()},sort_keys=True))


if __name__=="__main__":
    main()
