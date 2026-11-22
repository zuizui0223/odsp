#!/usr/bin/env python3
"""Gomes original Zenodo v1: preregistered (v3) detected-record night transfer.

No 'Number' column, solar/lunar values, source row index X, or original bat
spatial location is read. CSV rows, not verified individuals, are scored.
"""
from __future__ import annotations
import csv
import hashlib
import io
import json
from pathlib import Path
from urllib.request import Request,urlopen

from odsp.detected_vertical_transfer import Record,score_recorded_stratum_by_day
from scripts.gomes_zenodo_vertical_source_preflight_v1 import URL,EXPECTED_MD5
from scripts.gomes_zenodo_structure_v2 import KNOWN_HEADER

SOURCE_SHA256="4a3b84e7175c29110bb6220f5cdf5889152897501b371fad3e2d9a74523773c9"
EXPECTED_ROWS=7854
EXPECTED_DAYS=9
EXPECTED_BAT_LABELS=21
EXPECTED_HOURS=13

def records_from_original(raw):
    if hashlib.md5(raw).hexdigest()!=EXPECTED_MD5 or hashlib.sha256(raw).hexdigest()!=SOURCE_SHA256:
        raise ValueError("original source hash mismatch")
    try: s=raw.decode("utf-8-sig")
    except UnicodeError: s=raw.decode("latin-1")
    rows=csv.reader(io.StringIO(s,newline=""))
    header=next(rows)
    if header!=KNOWN_HEADER: raise ValueError("frozen source header mismatch")
    selected=tuple(header.index(k) for k in ("DAY","HOUR","Bat","POS"))
    out=[]
    for raw_row in rows:
        if len(raw_row)!=len(header):raise ValueError("ragged original source")
        day,hour,bat,pos=(raw_row[k].strip() for k in selected)
        if not hour.isdecimal():raise ValueError("invalid source HOUR")
        out.append(Record(day,int(hour),bat,pos))
    if (len(out)!=EXPECTED_ROWS or len({r.day for r in out})!=EXPECTED_DAYS or
        len({r.bat_label for r in out})!=EXPECTED_BAT_LABELS or
        len({r.hour for r in out})!=EXPECTED_HOURS):
        raise ValueError("unmatched original source support")
    return out

def main():
    req=Request(URL,headers={"User-Agent":"odsp-gomes-detected-height-v3/1.0"})
    with urlopen(req,timeout=180) as r:
        source=r.read(4_000_001)
    records=records_from_original(source)
    summary=score_recorded_stratum_by_day(records)
    outcome={
        "source_doi":"10.5281/zenodo.4019867", "source_version":"v1",
        "source_sha256":SOURCE_SHA256, "original_data_are_individual_GPS_altitudes":False,
        "is_geographically_independent_site_validation":False,
        "sensor_stratum_detection_calibrated":False,
        "sensor_height_not_equivalent_to_bat_flight_height":True,
        "author_prior_art_detected_vertical_stratification":True,
        "preopening_protocol":"docs/gomes_zenodo_detected_height_night_holdout_v3_preopen.md",
        **summary,
    }
    out=Path("results/gomes_zenodo_detected_height_v3.json")
    out.parent.mkdir(parents=True,exist_ok=True)
    out.write_text(json.dumps(outcome,indent=2,sort_keys=True)+"\n",encoding="utf-8")
    print(json.dumps(outcome,indent=2,sort_keys=True))
    return 0

if __name__=="__main__":
    raise SystemExit(main())
