#!/usr/bin/env python3
"""Dryad CC0 crane README/one-bird 1Hz GPS pilot without altitude use.

Access policy: request ONLY exact official Dryad file download API endpoints,
without credentials, cookies, proxy tricks or inferred mirror paths. A 401 or
403 is an explicit access boundary. File results remain UNAVAILABLE.
"""
from __future__ import annotations

import argparse,csv,hashlib,json,math,os,urllib.request,urllib.error
from collections import Counter,defaultdict
from datetime import datetime,timezone
from pathlib import Path

RECORD="10.5061/dryad.t76hdr871"
README=("2905498","dd3db1998b00a4e7a601bfd49586c7c2d213d4b14be7bc69f21f5d90dbe5ab83",13330,"README.md")
PILOT=("2905456","543ddd5b9233c40d982ef109574c9f9c9294471baa6d42f5cfb2ec5e4af8e1a7",2706910,"16113_1HzGPS_and_ACC_annotated.csv")
NON_VERTICAL_HEADER={"Tag","TimeCont","Latitude","Longitude",
                     "OverSeaOrLand","running_Flap_rate","blh",
                     "sstDiff","windSpeed850","msshf"}
# READ OBSERVATION: NEVER look up CSV row["Altitude_m"] or
# ["AleAboveTerrain"]; these are biological outcomes held back for later.
PILOT_MIN_POINTS_DAY=20


def fetch_exact(item,folder):
    identifier,checksum,nbytes,name=item
    url=f"https://datadryad.org/api/v2/files/{identifier}/download"
    path=folder/name
    record={"filename":name,"official_url":url,"sha256_expected":checksum,
            "expected_bytes":nbytes,"source_file_id":identifier,
            "downloaded":False,"http_status":None,"reason":None}
    h=hashlib.sha256();length=0
    req=urllib.request.Request(url,headers={
        "User-Agent":"ODSP-transparent-CC0-GPS-access-audit/1.0",
        "Accept":"application/octet-stream"
    })
    try:
        with urllib.request.urlopen(req,timeout=120) as f:
            record["http_status"]=f.status
            with path.open("wb") as out:
                for chunk in iter(lambda:f.read(1024*1024),b""):
                    out.write(chunk);h.update(chunk);length+=len(chunk)
    except urllib.error.HTTPError as err:
        record["http_status"]=err.code
        record["reason"]=f"Official Dryad API returned HTTP {err.code}. No source data downloaded; do not work around authorization."
        if path.exists():path.unlink()
        return record
    except (TimeoutError,urllib.error.URLError,OSError) as err:
        record["reason"]="Official endpoint inaccessible: "+str(err)[:240]
        if path.exists():path.unlink()
        return record
    record["actual_bytes"]=length;record["sha256_actual"]=h.hexdigest()
    if length!=nbytes or h.hexdigest()!=checksum:
        record["reason"]="Source bytes or published SHA256 changed; quarantine and do not inspect."
        path.unlink(missing_ok=True)
        return record
    record["downloaded"]=True
    record["reason"]="Exact official source file and checksum verified."
    return record


def maybe_timestamp(text):
    val=(text or "").strip()
    if val in ("","NA","NaN","NAN"):return None
    try:
        parsed=datetime.fromisoformat(val.replace("Z","+00:00"))
    except ValueError:
        # This is an isolated source-schema pilot. Do not infer timestamps
        # from arbitrary numeric values or choose time filters by altitude.
        return None
    if parsed.tzinfo is not None:
        parsed=parsed.astimezone(timezone.utc)
    return parsed


def finite_number(value):
    try:z=float(value)
    except (ValueError,TypeError):return None
    return z if math.isfinite(z) else None


def metadata_of_pilot(path):
    by_day=Counter()
    per_day_first_5min=set()
    fields=Counter()
    source_tag=set();unknown_time=0;valid_xy=0;total=0;nonvertical_valid=Counter()
    with path.open("rt",encoding="utf-8-sig",newline="") as f:
        reader=csv.DictReader(f)
        column_names=set(reader.fieldnames or ())
        if not NON_VERTICAL_HEADER<=column_names:
            return {"schema_ok":False,
                    "missing_nonvertical_fields":sorted(NON_VERTICAL_HEADER-column_names),
                    "no_altitude_values_read":True}
        for rec in reader:
            total+=1
            bird=(rec.get("Tag") or "").strip()
            if bird:source_tag.add(bird)
            ts=maybe_timestamp(rec.get("TimeCont"))
            lon=finite_number(rec.get("Longitude"))
            lat=finite_number(rec.get("Latitude"))
            if ts is None:
                unknown_time+=1
                continue
            if lon is None or lat is None or not (-180<=lon<=180 and -85<=lat<=85):
                continue
            valid_xy+=1
            day=ts.strftime("%Y-%m-%d")
            by_day[day]+=1
            if bird:
                k=(bird,day,ts.hour*12+ts.minute//5)
                per_day_first_5min.add(k)
            for field in ("running_Flap_rate","blh","sstDiff","windSpeed850","msshf"):
                if finite_number(rec.get(field)) is not None:
                    nonvertical_valid[field]+=1
    daycounts=Counter(day for b,day,bin5 in per_day_first_5min)
    return {
       "schema_ok":True,
       "source_rows_one_selected_bird_file":total,
       "distinct_tag_values_in_pilot":len(source_tag),
       "valid_GPS_xy_and_UTC_rows":valid_xy,
       "unparseable_time_rows":unknown_time,
       "distinct_days_with_GPS":len(by_day),
       "days_with_at_least_20_5min_GPS_fixes":sum(x>=PILOT_MIN_POINTS_DAY for x in daycounts.values()),
       "raw_GPS_5minute_bins":len(per_day_first_5min),
       "counts_by_year":dict(sorted(Counter(day[:4] for day in by_day).items())),
       "nonvertical_annotation_finite_fraction":{
          fld:nonvertical_valid[fld]/valid_xy if valid_xy else None
          for fld in ("running_Flap_rate","blh","sstDiff","windSpeed850","msshf")
       },
       "observed_native_height_or_AGL_numbers_read":False,
       "no_altitude_values_read":True,
       "inference_scope":"One source file pilot only; not a 44-bird independent replicate or admitted biological outcome."
    }


def main():
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument("--manifest",required=True,type=Path)
    p.add_argument("--out",required=True,type=Path)
    p.add_argument("--download-dir",type=Path,required=True)
    opt=p.parse_args()
    manifest=json.loads(opt.manifest.read_text())
    if manifest.get("stage")!="PREHEIGHT_SOURCE_MANIFEST_ONLY" or \
       manifest.get("source_archive_version_id")!=277770:
        raise ValueError("Official Dryad manifest was not established before pilot access")
    opt.download_dir.mkdir(parents=True,exist_ok=True)
    result={
        "analysis":"GRUS_GRUS_DRYAD_V4_OFFICIAL_ACCESS_AND_NONALTITUDE_PILOT_V1",
        "source_DOI":RECORD,
        "run_stage":"PUBLIC_OFFICIAL_FILE_ACCESS_DIAGNOSTIC",
        "files":{},
        "native_altitude_or_AGL_values_used_for_selection":False,
        "biological_result":"not_tested",
        "status":"unavailable"
    }
    for item in (README,PILOT):
        if manifest["files"][item[3]]["sha256"]!=item[1]:
            raise ValueError("Manifest/source metadata drift")
        res=fetch_exact(item,opt.download_dir)
        result["files"][item[3]]=res
        if not res["downloaded"]:
            # No probing unofficial URLs, no fallback to another study.
            break
    if all(result["files"].get(item[3],{}).get("downloaded") for item in (README,PILOT)):
        source_text=(opt.download_dir/"README.md").read_text(encoding="utf-8",errors="replace")
        if "AleAboveTerrain" not in source_text or "running_Flap_rate" not in source_text:
            result["status"]="available_codebook_schema_inconsistent"
        else:
            result["pilot_nonvertical"]=metadata_of_pilot(opt.download_dir/PILOT[3])
            result["status"]="verified_public_pilot" if result["pilot_nonvertical"]["schema_ok"] else "schema_mismatch"
    else:
        result["status"]="official_download_unavailable"
    opt.out.parent.mkdir(parents=True,exist_ok=True)
    opt.out.write_text(json.dumps(result,indent=2,sort_keys=True)+"\n")
    print(json.dumps({
        "status":result["status"],
        "files":{k:{"http_status":v["http_status"],"downloaded":v["downloaded"]}
                 for k,v in result["files"].items()},
        "pilot_source_bird_days":result.get("pilot_nonvertical",{}).get("distinct_days_with_GPS"),
        "GPS_altitude_values_read":False
    },sort_keys=True))


if __name__=="__main__":
    main()
