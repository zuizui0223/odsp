#!/usr/bin/env python3
"""French Gyps low-motion GPS NEGATIVE CONTROL, altitude-blind source gate.

Only the pre-height already admitted 28 biological bird IDs, native source
timestamps, geodesy, ground-speed 0..1m/s and source quality flags are used.
No source GPS-MSL or barometric height values or missingness are inspected.
"""
from __future__ import annotations

import argparse
import csv
import hashlib
import io
import json
import math
import re
import zipfile
from collections import Counter,defaultdict
from datetime import date
from pathlib import Path

from pyproj import Transformer

ORIGINAL_MD5="b18cc8004d311d19ff24060f655178bf"
ORIGINAL_BYTES=1093170227
ORIGINAL_NAME="windTurbineAvoidance.zip"
PRESCREEN_ORIGINAL_FLIGHT_BIRD_IDS_SHA="031d6226418cc0291a48d7d4eb44f1cae003df3a411ef3767a5229dbd45b1928"
SOURCE_TAXON="Gyps fulvus"
FILE_REGEX=re.compile(r"Vulturestracks_(Jan_to_May|Jun_to_Aug|Sep_to_Dec)(2019|2020|2021)\.csv$")
FIELDS={"individual-local-identifier","individual-taxon-canonical-name","timestamp",
   "location-long","location-lat","ground-speed","visible",
   "import-marked-outlier","gps:hdop","gps:satellite-count","tag-local-identifier"}
YEARS={"2019","2020","2021"}
MAX_SLOW_SPEED_M_S=1.0
CELL_M=5000
MIN_SELF_OTHER_DAY=10
MIN_OTHER_BIRD_OTHER_DATE=10
MIN_TARGET_DAY=50
MIN_BIRD_DAYS=2
MIN_BIRDS=10
PROJ=Transformer.from_crs("EPSG:4326","EPSG:6933",always_xy=True)


def check_immutable_source(path):
    if path.name!=ORIGINAL_NAME or path.stat().st_size!=ORIGINAL_BYTES:
        raise ValueError("Original immutable source basename/size mismatch")
    h=hashlib.md5()
    with path.open("rb") as f:
        for buf in iter(lambda:f.read(1024*1024),b""):
            h.update(buf)
    if h.hexdigest()!=ORIGINAL_MD5:
        raise ValueError("Published GPS archive MD5 changed")


def numeric(s):
    try:r=float(s)
    except (TypeError,ValueError):return None
    return r if math.isfinite(r) else None


def original_preheight_bird_roster(meta):
    if meta.get("numeric_native_GPS_height_values_read") is not False:
        raise ValueError("Source roster is not height-blind")
    if meta.get("phase")!="FRENCH_GYPS_2019_2021_XYTIME_INSTRUMENT_ONLY_PREHEIGHT":
        raise ValueError("Expected original tracking source prescreen")
    if meta.get("source_zip_md5")!=ORIGINAL_MD5:
        raise ValueError("Original archive checksum does not match roster")
    if "Test géodésie ornitela" not in meta.get("quarantined_nonbiological_animal_IDs",[]):
        raise ValueError("Original source geodesy test label was not identified")
    source=meta["horizontal_day_eligibility_by_cell_m"]["5000"]
    birds=set(source["admitted_bird_ids"])
    sha=hashlib.sha256("\n".join(sorted(birds)).encode()).hexdigest()
    if (len(birds)!=28 or sha!=PRESCREEN_ORIGINAL_FLIGHT_BIRD_IDS_SHA
            or sha!=source["source_bird_ID_sha256"]):
        raise ValueError("Frozen preheight 28-bird source population drift")
    if "Test géodésie ornitela" in birds:
        raise ValueError("Non-biological instrument cannot be a focal bird")
    return birds


def screen_member(reader,known_birds,first,counts,source_year):
    header=next(reader)
    idx={name:k for k,name in enumerate(header)}
    if not FIELDS<=set(idx):
        raise ValueError("Native source lacks required nonheight fields")
    get=lambda row,name:row[idx[name]] if idx[name]<len(row) else ""
    for row in reader:
        counts["all_native_GPS_rows"]+=1
        bird=get(row,"individual-local-identifier").strip()
        if bird not in known_birds:
            counts["outside_28_frozen_birds_or_geodesy_test"]+=1
            continue
        if get(row,"individual-taxon-canonical-name").strip()!=SOURCE_TAXON:
            counts["outside_frozen_taxon"]+=1
            continue
        if get(row,"visible").strip().lower()=="false" or \
             get(row,"import-marked-outlier").strip().lower() in {"true","1","yes","y"}:
            counts["native_GPS_flagged_outlier"]+=1
            continue
        stamp=get(row,"timestamp").strip()
        try:
            yyyy=int(stamp[:4]);mm=int(stamp[5:7]);dd=int(stamp[8:10])
            hh=int(stamp[11:13]);minute=int(stamp[14:16])
            date(yyyy,mm,dd)
        except (ValueError,TypeError):
            counts["invalid_timestamp"]+=1;continue
        if str(yyyy)!=source_year or not(0<=hh<24 and 0<=minute<60):
            counts["year_mismatch"]+=1;continue
        lon=numeric(get(row,"location-long"))
        lat=numeric(get(row,"location-lat"))
        speed=numeric(get(row,"ground-speed"))
        if (lon is None or lat is None or speed is None
            or not(-180<=lon<=180 and -85<=lat<=85)):
            counts["nonheight_GPS_bad_xy_or_speed"]+=1;continue
        if not 0.0<=speed<=MAX_SLOW_SPEED_M_S:
            counts["outside_frozen_low_motion_speed"]+=1;continue
        key=(bird,stamp[:10],hh*12+minute//5)
        hdop=numeric(get(row,"gps:hdop"))
        sats=numeric(get(row,"gps:satellite-count"))
        tag=get(row,"tag-local-identifier").strip()
        chosen=first.get(key)
        if chosen is None or stamp<chosen[0]:
            first[key]=(stamp,lon,lat,hdop,sats,tag)
        counts["native_low_motion_events_before_5min_thin"]+=1


def make_support(first,original):
    bycell=Counter();byyear=defaultdict(lambda:{
        "birds":set(),"bird_days":set(),"events":0,"hdop":0,"satellite":0})
    tags=defaultdict(set)
    for (bird,day,bin5),(stamp,lon,lat,hdop,sats,tag) in first.items():
        x,y=PROJ.transform(lon,lat)
        if not(math.isfinite(x) and math.isfinite(y)):
            raise ValueError("Native longitude/latitude projection invalid")
        cell=(math.floor(x/CELL_M),math.floor(y/CELL_M))
        bycell[bird,day,cell]+=1
        y=byyear[day[:4]]
        y["birds"].add(bird);y["bird_days"].add((bird,day));y["events"]+=1
        y["hdop"]+=hdop is not None;y["satellite"]+=sats is not None
        if tag and tag.upper() not in {"NA","NONE","NAN","NULL"}:tags[bird].add(tag)
    own=Counter();allcell=Counter();dates=Counter()
    for (bird,day,cell),n in bycell.items():
        own[bird,cell]+=n;allcell[cell]+=n;dates[day,cell]+=n
    scored=Counter()
    for (bird,day,cell),n in bycell.items():
        if (own[bird,cell]-n>=MIN_SELF_OTHER_DAY and
            allcell[cell]-own[bird,cell]-dates[day,cell]+n>=MIN_OTHER_BIRD_OTHER_DATE):
            scored[bird,day]+=n
    days=Counter()
    for (bird,day),n in scored.items():
        if n>=MIN_TARGET_DAY:days[bird]+=1
    birds={b for b,n in days.items() if n>=MIN_BIRD_DAYS}
    return {
        "original_previous_flight_eligible_bird_roster_sha256":PRESCREEN_ORIGINAL_FLIGHT_BIRD_IDS_SHA,
        "source_original_flight_eligible_birds":len(original),
        "original_eligible_lowmotion_birds":len(birds),
        "original_eligible_lowmotion_bird_IDs":sorted(birds),
        "lowmotion_eligible_bird_ID_sha256":hashlib.sha256("\n".join(sorted(birds)).encode()).hexdigest(),
        "lowmotion_eligible_bird_days":sum(days[b] for b in birds),
        "lowmotion_eligible_scored_five_minute_events":sum(n for (b,d),n in scored.items() if b in birds and n>=MIN_TARGET_DAY),
        "admitted_for_separately_frozen_negative_control":len(birds)>=MIN_BIRDS,
        "all_source_lowmotion_five_minute_events":len(first),
        "n_source_lowmotion_biological_animals":len({b for b,d,k in first}),
        "years":{year:{
            "birds":len(d["birds"]),"bird_days":len(d["bird_days"]),
            "events":d["events"],
            "hdop_fraction":d["hdop"]/d["events"] if d["events"] else None,
            "satellite_fraction":d["satellite"]/d["events"] if d["events"] else None
            } for year,d in sorted(byyear.items())
        },
        "cell_5km_count":len(allcell),
        "animal_ids_with_multiple_tag_ids":sum(len(inds)>1 for inds in tags.values()),
        "distinct_tag_ids":len({t for v in tags.values() for t in v}),
        "motion_class":"reported GPS ground-speed between 0 and 1 m/s inclusive; low motion not independently confirmed stationary",
        "same_5km_firstfix_vs_highspeed_negative_control_not_spatially_matched":True,
        "independent_native_height_values_opened":False,
        "altitude_missingness_used_in_eligibility":False,
        "biological_lowmotion_identity_tested":False,
        "interpretation_if_admitted":"Sufficient OTHER bird-date lowmotion source samples to attempt later D1. It does not imply identity is biological, or low-motion on ground."
    }


def main():
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument("--source-zip",required=True,type=Path)
    p.add_argument("--flight-preheight",required=True,type=Path)
    p.add_argument("--out",required=True,type=Path)
    args=p.parse_args()
    original=json.loads(args.flight_preheight.read_text(encoding="utf-8"))
    birds=original_preheight_bird_roster(original)
    check_immutable_source(args.source_zip)
    first={};audit=Counter();members=Counter()
    with zipfile.ZipFile(args.source_zip) as z:
        chosen=sorted((info for info in z.infolist() if not info.is_dir()
                       and "Vulturestracks_" in info.filename
                       and info.filename.endswith(".csv")
                       and not info.filename.startswith("__MACOSX/")),
                       key=lambda x:x.filename)
        if len(chosen)!=9:
            raise ValueError("Nine year×season native source files expected")
        for info in chosen:
            years=[y for y in YEARS if info.filename.endswith(y+".csv")]
            if len(years)!=1:raise ValueError("Unknown archived GPS year")
            with z.open(info) as raw,io.TextIOWrapper(
                 raw,encoding="utf-8-sig",errors="replace",newline="") as f:
                screen_member(csv.reader(f),birds,first,audit,years[0])
            members[years[0]]+=1
            print("Noheight LOW motion source:",info.filename,
                  "five-minute-first-fixes",len(first),flush=True)
    result=make_support(first,birds)
    result.update({
        "analysis":"FRANCE_GYPS_LOWMOTION_5KM_OTHER_DAY_SOURCE_GATE_V1",
        "stage":"POST_OUTCOME_EXPLORATORY_LOW_MOTION_PRE_HEIGHT",
        "source_MD5":ORIGINAL_MD5,
        "source_Dataverse_DOI":"10.48579/PRO/IOSZNM",
        "nine_source_CSV_year_count":dict(sorted(members.items())),
        "low_motion_speed_m_s":[0,MAX_SLOW_SPEED_M_S],
        "source_native_row_filter_counts":dict(sorted(audit.items())),
        "user_visible_negative_control_result":"NOT TESTED",
        "reason_low_motion_if_unavailable":"Underlying GPS cell/individual/day support never uses native altitude and is fixed before inspecting low-motion altitude; if fewer than 10, report unavailable rather than changing thresholds."
    })
    args.out.parent.mkdir(parents=True,exist_ok=True)
    args.out.write_text(json.dumps(result,sort_keys=True,indent=2)+"\n")
    print(json.dumps({
        "lowmotion_birds":result["n_source_lowmotion_biological_animals"],
        "lowmotion_5km_repeated_birds":result["original_eligible_lowmotion_birds"],
        "lowmotion_eligible_days":result["lowmotion_eligible_bird_days"],
        "lowmotion_scored_fixes":result["lowmotion_eligible_scored_five_minute_events"],
        "admitted":result["admitted_for_separately_frozen_negative_control"],
        "altitude_unopened":True,
    },sort_keys=True),flush=True)


if __name__=="__main__":
    main()
