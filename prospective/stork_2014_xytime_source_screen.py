#!/usr/bin/env python3
"""Altitude-blind migratory white-stork GPS support audit, one immutable ZIP.

Does not access height above ellipsoid, barometric height or altitude outcomes.
Tests whether same 5km-cell different-day within-bird vs other bird is even a
valid comparator for long-distance migrants (vs central-place gulls).
"""
from __future__ import annotations
import argparse,csv,hashlib,io,json,math,zipfile
from collections import Counter,defaultdict
from pathlib import Path
from pyproj import Transformer

EXPECTED_NAME="Fall migrations of juvenile vs. adult white storks (data from Rotics et al. 2016)-gps.csv.zip"
EXPECTED_MD5="2ec22217c0f566650d245ae2da4694bf"
REFERENCE_NAME="Fall migrations of juvenile vs. adult white storks (data from Rotics et al. 2016)-reference-data.csv"
REFERENCE_MD5="b38407ed744cf2bd4806afce929f604a"
YEAR=2014
MONTHS={8,9,10,11}
GRIDS_M=(5000,50000,100000)
MIN_SELF=10
MIN_OTHER=10
MIN_DAY=50
MIN_DAYS=2
MIN_BIRDS=10
MAX_SPEED=55.0
MIN_SPEED=5.0
TRANSFORM=Transformer.from_crs("EPSG:4326","EPSG:6933",always_xy=True)


def digest(path):
    h=hashlib.md5()
    with path.open("rb") as stream:
        for chunk in iter(lambda:stream.read(1<<20),b""):h.update(chunk)
    return h.hexdigest()


def check(path,filename,md5):
    actual=digest(path)
    if path.name!=filename or actual!=md5:
        raise ValueError("Archive filename/checksum mismatch")
    return actual


def read_reference(reader):
    stage_by_bird=defaultdict(set)
    tags=defaultdict(set)
    n=0
    unique=set()
    for row in reader:
        n+=1
        bird=(row.get("animal-id") or "").strip()
        tag=(row.get("tag-id") or "").strip()
        stage=(row.get("animal-life-stage") or "").strip().lower() or "unknown"
        if not bird:continue
        unique.add(bird)
        stage_by_bird[bird].add(stage)
        if tag:tags[bird].add(tag)
    stage={}
    for bird,st in stage_by_bird.items():
        stage[bird]=next(iter(st)) if len(st)==1 else "mixed_or_uncertain"
    return stage,{
        "reference_rows":n,
        "unique_birds":len(unique),
        "unique_tags":len({t for x in tags.values() for t in x}),
        "birds_multiple_tags":sum(len(z)>=2 for z in tags.values()),
        "stage_counts":dict(Counter(stage.values())),
        "age_source":"animal-life-stage literal from reference, otherwise unknown"
    }


def eligible_support(by_day_cell:Counter):
    by_bird_cell=Counter()
    all_cell=Counter()
    by_date_cell=Counter()
    raw_bird_day=Counter()
    for (bird,day,cell),n in by_day_cell.items():
        by_bird_cell[bird,cell]+=n
        all_cell[cell]+=n
        by_date_cell[day,cell]+=n
        raw_bird_day[bird,day]+=n
    scorable=Counter()
    for (bird,day,cell),n in by_day_cell.items():
        own_other_date=by_bird_cell[bird,cell]-n
        other_birds_other_date=all_cell[cell]-by_bird_cell[bird,cell]-by_date_cell[day,cell]+n
        if own_other_date>=MIN_SELF and other_birds_other_date>=MIN_OTHER:
            scorable[bird,day]+=n
    eligible_bird_days=Counter()
    for (bird,day),n in scorable.items():
        if n>=MIN_DAY:eligible_bird_days[bird]+=1
    qualifying={bird for bird,days in eligible_bird_days.items() if days>=MIN_DAYS}
    raw_bird_days=Counter()
    for (bird,day),n in raw_bird_day.items():
        if n>=MIN_DAY:raw_bird_days[bird]+=1
    return {
        "cells_used":len(all_cell),
        "birds_with_any_flight_fix":len({bird for bird,day in raw_bird_day}),
        "birds_with_2_days_of_50_five_minute_fixes":sum(n>=2 for n in raw_bird_days.values()),
        "birds_with_2_scorable_shared_cell_days":len(qualifying),
        "qualifying_bird_days":sum(n for bird,n in eligible_bird_days.items() if bird in qualifying),
        "qualifying_target_fixes":sum(n for (bird,day),n in scorable.items() if bird in qualifying and n>=MIN_DAY),
        "admitted":len(qualifying)>=MIN_BIRDS,
        "eligible_bird_id_fingerprint_sha256":hashlib.sha256("\n".join(sorted(qualifying)).encode()).hexdigest(),
        "stage_excluded_as_unavailable_not_negative":not (len(qualifying)>=MIN_BIRDS)
    }


def audit(rows,stage_by_bird=None):
    stages=stage_by_bird or {}
    first={}
    c=Counter()
    raw_birds=set()
    for row in rows:
        c["raw_rows"]+=1
        bird=(row.get("individual-local-identifier") or "").strip()
        if not bird:
            c["missing_bird"]+=1;continue
        raw_birds.add(bird)
        time=(row.get("timestamp") or "").strip()
        try:
            year,month,hour,minute=int(time[:4]),int(time[5:7]),int(time[11:13]),int(time[14:16])
        except (ValueError,TypeError):
            c["invalid_time"]+=1
            continue
        if year!=YEAR or month not in MONTHS or not(0<=hour<24 and 0<=minute<60):
            c["outside_frozen_2014_autumn"]+=1;continue
        flags=["visible","import-marked-outlier","manually-marked-outlier"]
        if str(row.get("visible","")).strip().lower()=="false" or any(
            str(row.get(f,"")).strip().lower() in {"true","1","yes"} for f in flags[1:]
        ):
            c["source_outlier"]+=1;continue
        try:
            lon=float(row.get("location-long"))
            lat=float(row.get("location-lat"))
            speed=float(row.get("ground-speed"))
        except (ValueError,TypeError):
            c["missing_xy_speed"]+=1
            continue
        if not all(math.isfinite(v) for v in (lon,lat,speed)) or not(
            -180<=lon<=180 and -86<=lat<=86 and MIN_SPEED<=speed<=MAX_SPEED
        ):
            c["invalid_or_outside_flight"]+=1;continue
        key=(bird,time[:10],hour*12+minute//5)
        if key not in first or time<first[key][0]:
            first[key]=(time,lon,lat)
        c["raw_flight_proxy_events"]+=1
    c["thinned_flight_5min_bins"]=len(first)
    c["source_birds_before_filters"]=len(raw_birds)
    c["birds_with_thinned_flight"]=len({bird for bird,day,k in first})
    groups={g:Counter() for g in GRIDS_M}
    by_stage=Counter()
    for (bird,day,k),(timestamp,lon,lat) in first.items():
        x,y=TRANSFORM.transform(lon,lat)
        if not(math.isfinite(x) and math.isfinite(y)):continue
        by_stage[stages.get(bird,"unknown")]+=1
        for size in GRIDS_M:
            cell=(math.floor(x/size),math.floor(y/size))
            groups[size][bird,day,cell]+=1
    result={
        "stage":"ALMOST_OUTCOME_BLIND_BIOLOGICAL_SOURCE_SUPPORT_ONLY",
        "taxon":"Ciconia ciconia",
        "source_year":YEAR,
        "months_UTC":sorted(MONTHS),
        "gps_altitude_values_accessed":False,
        "GPS_altitude_missingness_accessed":False,
        "GPS_altitude_shape_tested":False,
        "GPS_time_speed_xy_rows":dict(c),
        "field_presence_checked_but_no_altitude_rows_read":True,
        "thinned_fixes_by_reference_age_label":dict(sorted(by_stage.items())),
        "horizontal_support_by_grid_m":{
            str(size):eligible_support(groups[size]) for size in GRIDS_M
        },
        "frozen_primary_grid_m":5000,
        "claim_boundary":"Failure of repeated 5km cell support indicates migratory movement geometry is unsuitable for the gull primary estimand, not lack of biological vertical individuality."
    }
    return result


def from_archive(path,reference):
    check(path,EXPECTED_NAME,EXPECTED_MD5)
    check(reference,REFERENCE_NAME,REFERENCE_MD5)
    with reference.open("r",encoding="utf-8-sig",newline="") as f:
        r=csv.DictReader(f)
        age,metadata=read_reference(r)
    with zipfile.ZipFile(path) as zf:
        members=[m for m in zf.namelist() if m.lower().endswith(".csv") and not m.startswith("__MACOSX")]
        if len(members)!=1:
            raise ValueError("One CSV in frozen source ZIP expected, got "+str(members))
        with zf.open(members[0]) as compressed,io.TextIOWrapper(compressed,encoding="utf-8-sig",newline="") as fp:
            rows=csv.DictReader(fp)
            required={"timestamp","individual-local-identifier","location-long","location-lat","ground-speed"}
            schema=set(rows.fieldnames or [])
            if not required<=schema:
                raise ValueError("Source missing required non-vertical GPS fields: "+repr(sorted(required-schema)))
            out=audit(rows,age)
            out["GPS_zip_csv_member"]=members[0]
            out["GPS_schema_has_height_above_ellipsoid"]="height-above-ellipsoid" in schema
            out["GPS_schema_has_height_above_msl"]="height-above-msl" in schema
    out["source"]={
        "doi":"10.5441/001/1.hn1bd23k",
        "GPS_archive_md5":EXPECTED_MD5,
        "GPS_zip_compressed_size":path.stat().st_size,
        "reference_md5":REFERENCE_MD5,
        **metadata,
    }
    return out


def main():
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument("--gps-zip",type=Path,required=True)
    p.add_argument("--reference",type=Path,required=True)
    p.add_argument("--output",type=Path,required=True)
    a=p.parse_args()
    res=from_archive(a.gps_zip,a.reference)
    a.output.parent.mkdir(parents=True,exist_ok=True)
    a.output.write_text(json.dumps(res,sort_keys=True,indent=2)+"\n")
    print(json.dumps({"source_birds":res["GPS_time_speed_xy_rows"]["birds_with_thinned_flight"],
         "5km":res["horizontal_support_by_grid_m"]["5000"]["birds_with_2_scorable_shared_cell_days"],
         "50km":res["horizontal_support_by_grid_m"]["50000"]["birds_with_2_scorable_shared_cell_days"],
         "100km":res["horizontal_support_by_grid_m"]["100000"]["birds_with_2_scorable_shared_cell_days"],
         "altitude_opened":res["gps_altitude_values_accessed"]},sort_keys=True))


if __name__=="__main__":
    main()
