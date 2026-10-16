#!/usr/bin/env python3
"""Official Dryad public wildebeest GPS 2026 header & SHA256 source-only gate.

Never read GPS data rows, timestamps, individual IDs or coordinates. This
script does NOT claim biological GPS location, movement or true activity.
Original first-party HTTP failure is explicit HOLD; no authentication bypass.
"""
from __future__ import annotations
import argparse
import csv
import hashlib
import io
import json
from pathlib import Path
import urllib.error
import urllib.request

SOURCE="https://datadryad.org/api/v2/files/4763314/download"
EXACT_SOURCE_SHA256="9631aa94bda8b9efd7adbe8ca0004e58f22c98d03b729fcab4df40434a0fc148"
EXPECTED_SIZE=13481100
MAX_SOURCE_BYTES=EXPECTED_SIZE+1
REQUIRED_COLUMNS=("AID","Date","Step_length","SPECIES","COLLAR_ID")

def _normalized(s):
    return "".join(x for x in str(s).lower() if x.isalnum())

def public_header_only_receipt(payload:bytes)->dict:
    digest=hashlib.sha256(payload).hexdigest()
    if digest!=EXACT_SOURCE_SHA256 or len(payload)!=EXPECTED_SIZE:
        raise ValueError("HOLD_ORIGINAL_DRYAD_BYTES_OR_SHA256_MISMATCH")
    f=io.BytesIO(payload)
    line=f.readline(65537)
    if len(line)>65536:
        raise ValueError("HOLD_ABNORMALLY_LONG_CSV_SOURCE_HEADER")
    header=next(csv.reader([line.decode("utf-8-sig")]))
    norm={_normalized(s) for s in header}
    missing=[s for s in REQUIRED_COLUMNS if _normalized(s) not in norm]
    if missing:
        raise ValueError("HOLD_ORIGINAL_GPS_REQUIRED_COLUMNS_MISSING")
    # No data rows are ever parsed or reported, even for 143,168 paper fixes.
    return {
        "source":SOURCE,"filename":"WB2019_2023_data.csv",
        "bytes":len(payload),"sha256":digest,"readiness":"HEADER_ONLY_ORIGINAL_SHA256_VERIFIED_NOT_BIOLOGICAL_OUTCOME",
        "column_names_only":header,
        "original_GPS_event_rows_parsed":0,
        "independent_solar_branch_fix_schedule_verified":False,
        "true_animal_activity_or_calendar_hysteresis_identified":False,
        "future_animal_scoring_permitted":False,
    }

def preflight()->dict:
    try:
        req=urllib.request.Request(SOURCE,headers={
            "User-Agent":"ODSP-source-integrity-check/0.1",
            "Accept":"text/csv, application/octet-stream"
        })
        with urllib.request.urlopen(req,timeout=80) as r:
            payload=r.read(MAX_SOURCE_BYTES+1)
        if len(payload)>MAX_SOURCE_BYTES:
            raise ValueError("HOLD_ORIGINAL_DRYAD_SOURCE_ABOVE_FILE_SIZE_CAP")
        return public_header_only_receipt(payload)
    except (OSError,ValueError,UnicodeError,urllib.error.URLError) as exc:
        return {
            "source":SOURCE,
            "status":"HOLD_ORIGINAL_GPS_2026_SOURCE_NOT_ADMITTED",
            "exception_type":type(exc).__name__,
            "http_status_if_available":getattr(exc,"code",None),
            "GPS_animal_rows_opened":False,
            "no_biological_result_inferred":True
        }

def main()->None:
    p=argparse.ArgumentParser()
    p.add_argument("--output",required=True,type=Path)
    a=p.parse_args()
    result=preflight()
    a.output.parent.mkdir(parents=True,exist_ok=True)
    a.output.write_text(json.dumps(result,sort_keys=True,indent=2)+"\n",encoding="utf-8")
    print(json.dumps({
        "source_status":result.get("readiness",result.get("status")),
        "source_original_sha256":result.get("sha256"),
        "public_HTTP_status":result.get("http_status_if_available"),
        "animal_motion":False
    },sort_keys=True))

if __name__=="__main__":main()
