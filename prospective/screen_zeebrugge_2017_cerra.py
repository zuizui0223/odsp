#!/usr/bin/env python3
"""2017 Zeebrugge outcome-blind bird×site×weather structural gate.

Source year 2017 was frozen after the completed 2016 positive and before any
2017 animal altitude response was read. No height field is ever accessed here.
"""
from __future__ import annotations

import argparse
from collections import Counter, defaultdict
import csv
import gzip
import hashlib
import json
import math
from pathlib import Path
import statistics
import time
import urllib.parse
import urllib.request

import numpy as np

from . import screen_zeebrugge_cerra_2016 as src

SOURCE_GPS="LBBG_ZEEBRUGGE-gps-2017.csv.gz"
SOURCE_MD5="8724b5de0d4ff0117af328d1dde15a0e"
SELECTION_YEAR=2017
SOURCE_REFERENCE=src.REF_NAME
REFERENCE_MD5=src.REF_MD5


def find_2017_events(rows):
    first={}
    animal_tag_pairs=defaultdict(set)
    counts=Counter()
    taxon_seen=Counter()
    for row in rows:
        counts["raw_rows"]+=1
        taxon=(row.get("individual-taxon-canonical-name") or "").strip()
        taxon_seen[taxon]+=1
        if taxon not in {"Larus fuscus","Larus fuscus intermedius"}:
            continue
        if any((row.get(field) or "").strip().lower() in {"true","t","1","yes","y"}
               for field in ("import-marked-outlier","manually-marked-outlier")):
            counts["outliers"]+=1;continue
        stamp=(row.get("timestamp") or "").strip()
        bird=(row.get("individual-local-identifier") or "").strip()
        tag=(row.get("tag-local-identifier") or "").strip()
        try:
            yr,month,hr,minute=int(stamp[:4]),int(stamp[5:7]),int(stamp[11:13]),int(stamp[14:16])
        except (TypeError,ValueError):
            counts["bad_datetime"]+=1;continue
        if yr!=SELECTION_YEAR or month not in (5,6,7) or not bird or not (0<=hr<24 and 0<=minute<60):
            continue
        animal_tag_pairs[bird].add((bird,tag))
        lon=src.num(row.get("location-long"))
        lat=src.num(row.get("location-lat"))
        speed=src.num(row.get("ground-speed"))
        if lon is None or lat is None or speed is None or not(-180<=lon<=180 and -90<=lat<=90):
            counts["invalid_xy_speed"]+=1;continue
        if not 5<=speed<=55:continue
        counts["raw_flying_proxy"]+=1
        key=(bird,stamp[:10],hr*12+minute//5)
        if key not in first or stamp<first[key][0]:
            first[key]=(stamp,lon,lat)
    counts["first_flying_5min_bins"]=len(first)
    return first,animal_tag_pairs,{"counts":dict(counts),"native_taxa":dict(taxon_seen)}


def site_winds_2017(centers):
    regimes={};sources={}
    for site,place in sorted(centers.items()):
        args={
            "latitude":f"{place['latitude']:.6f}",
            "longitude":f"{place['longitude']:.6f}",
            "start_date":"2017-05-01","end_date":"2017-07-31",
            "hourly":"wind_speed_100m,wind_speed_10m",
            "wind_speed_unit":"ms","timezone":"UTC","models":"cerra",
        }
        url=src.WEATHER_ENDPOINT+"?"+urllib.parse.urlencode(args)
        weather=None
        for i in range(3):
            try:
                req=urllib.request.Request(url,headers={"User-Agent":"Open-ecology-outcome-blind/2017"})
                with urllib.request.urlopen(req,timeout=100) as fp:
                    weather=json.load(fp)
                break
            except Exception:
                if i==2:raise
                time.sleep(4*(i+1))
        if weather.get("utc_offset_seconds")!=0 or weather["hourly_units"]["wind_speed_100m"]!="m/s":
            raise ValueError("Unexpected CERRA time or wind units")
        hours=weather["hourly"]
        daywinds=defaultdict(list)
        for stamp,velocity in zip(hours["time"],hours["wind_speed_100m"]):
            x=src.num(velocity)
            if x is not None:
                daywinds[stamp[:10]].append(x)
        averages={day:float(statistics.mean(q)) for day,q in daywinds.items() if len(q)>=20}
        grouped=defaultdict(list)
        for d,wind in averages.items():
            grouped[d[:7]].append(wind)
        thresholds={}
        for month,ws in sorted(grouped.items()):
            q25,q75=np.quantile(ws,[.25,.75])
            thresholds[month]={"q25":float(q25),"q75":float(q75),"n_calendar_days":len(ws)}
        labels={}
        for day,val in averages.items():
            q=thresholds[day[:7]]
            labels[day]="low" if val<=q["q25"] else ("high" if val>=q["q75"] else "middle")
        regimes[site]=labels
        sources[site]={
            "query":args,
            "response_grid_latitude":weather["latitude"],
            "response_grid_longitude":weather["longitude"],
            "thresholds_by_month":thresholds,
            "complete_weather_days":len(averages),
            "low_days":sum(v=="low" for v in labels.values()),
            "high_days":sum(v=="high" for v in labels.values())
        }
    return sources,regimes


def outcome_blind_procedure(reference, gps_rows, original_2016_receipt):
    ref_meta=src.reference_meta(reference)
    centers=ref_meta["site_centers"]
    if centers!=original_2016_receipt["reference"]["site_centers"]:
        raise ValueError("2016 original site-centroid anchor changed")
    first,animal_labels,gps= find_2017_events(gps_rows)
    cross=src.safe_crosswalk(reference,animal_labels)
    climate,regimes=site_winds_2017(centers)
    support=src.xysupport(first,cross["site_by_bird"],regimes)
    digest=hashlib.sha256(json.dumps(regimes,sort_keys=True).encode()).hexdigest()
    return {
        "phase":"PREHEIGHT_2017_CERRA_OUTCOME_BLIND",
        "source":"https://zenodo.org/records/22273603",
        "GPS_file":SOURCE_GPS,
        "GPS_md5":SOURCE_MD5,
        "reference_md5":REFERENCE_MD5,
        "anchor_2016_site_centers":centers,
        "crosswalk":{k:v for k,v in cross.items() if k!="site_by_bird"},
        "gps":gps,
        "CERRA_wind":climate,
        "CERRA_site_calendar_state_sha256":digest,
        "support":support,
        "2017_native_altitude_opened":False,
        "independent_source_study":False,
        "temporal_next_year_validation_only":True,
        "no_rescue":"Do not move to a later year or change 2016 frozen min-day/cell thresholds if 2017 is unavailable.",
    }


def main():
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument("--gps",required=True,type=Path)
    p.add_argument("--reference",required=True,type=Path)
    p.add_argument("--anchor-receipt",required=True,type=Path)
    p.add_argument("--output",required=True,type=Path)
    args=p.parse_args()
    src.ensure_md5(args.gps,SOURCE_MD5,SOURCE_GPS)
    src.ensure_md5(args.reference,REFERENCE_MD5,SOURCE_REFERENCE)
    anchored=json.loads(args.anchor_receipt.read_text(encoding="utf-8"))
    if anchored["height_or_biological_effect_opened"] is not False:
        raise ValueError("2016 source anchor is not outcome blind")
    with args.reference.open("rt",newline="",encoding="utf-8-sig") as f:
        refs=list(csv.DictReader(f))
    with gzip.open(args.gps,"rt",newline="",encoding="utf-8-sig") as f:
        rows=csv.DictReader(f)
        mandatory={"timestamp","individual-local-identifier","tag-local-identifier",
                   "individual-taxon-canonical-name","location-long","location-lat","ground-speed"}
        if not mandatory<=set(rows.fieldnames or []):
            raise ValueError("Native 2017 non-altitude fields missing")
        result=outcome_blind_procedure(refs,rows,anchored)
        result["source_has_height_field"]="height-above-msl" in set(rows.fieldnames or [])
    args.output.parent.mkdir(parents=True,exist_ok=True)
    args.output.write_text(json.dumps(result,indent=2,sort_keys=True)+"\n")
    print(json.dumps({
        "birds_with_flight":result["support"]["source_birds_with_any_flight_bin"],
        "birds_shared_xy":result["support"]["baseline_shared_cell_birds"],
        "birds_both_wind_regimes":result["support"]["wind_both_regimes_birds"],
        "source_admitted":result["support"]["wind_gate_admitted"],
        "crosswalk":result["crosswalk"]["accepted"],
        "2017_altitude_opened":False
    },sort_keys=True))


if __name__=="__main__":
    main()
