#!/usr/bin/env python3
"""Source-structure-only admission: Yoh et al. Amazon bat stratum CSV (Dryad).

DO NOT read, parse, summarize, print or convert bat-pass response values.
The only allowed fields are six source keys; the numeric outcome column must
exist but is never referenced except via the header. Does not fit any model.
"""
from __future__ import annotations
from collections import Counter, defaultdict
import csv
import hashlib
import io
import json
from pathlib import Path, PurePosixPath
import re
from urllib.request import Request, urlopen
from zipfile import ZipFile

DOI="10.5061/dryad.0vt4b8h2d"
ARCHIVE_URL="https://datadryad.org/api/v2/datasets/doi%3A10.5061%2Fdryad.0vt4b8h2d/download"
SOURCE_FILE="Auto_UC_species_clean.csv"
EXPECTED=("season","location","transect","distance","habitat","species","no")
KEYS=EXPECTED[:6]

def canon(x):
    return re.sub(r"_+","_",re.sub("[^a-z0-9]+","_",str(x).strip().lower())).strip("_")

def download():
    req=Request(ARCHIVE_URL,headers={"User-Agent":"odsp-source-structure-audit-v1/1.0", "Accept":"application/zip"})
    with urlopen(req,timeout=240) as response:
        payload=response.read()
    archive_sha=hashlib.sha256(payload).hexdigest()
    with ZipFile(io.BytesIO(payload)) as zf:
        candidates=[n for n in zf.namelist() if PurePosixPath(n).name==SOURCE_FILE and not n.endswith("/")]
        if len(candidates)!=1:
            raise RuntimeError(f"expected 1 unambiguous {SOURCE_FILE}, found {len(candidates)}")
        if zf.getinfo(candidates[0]).file_size > 4_000_000:
            raise RuntimeError("source file too large for frozen CSV header gate")
        csv_bytes=zf.read(candidates[0])
    return archive_sha,csv_bytes

def source_only_scan(csv_bytes):
    try:
        csv_text=csv_bytes.decode("utf-8-sig")
    except UnicodeError:
        csv_text=csv_bytes.decode("latin-1")
    reader=csv.reader(io.StringIO(csv_text,newline=""))
    original_headers=next(reader)
    heads=[canon(x) for x in original_headers]
    if len(set(heads))!=len(heads):
        raise RuntimeError("header canonicalization collision")
    if not set(EXPECTED).issubset(heads):
        raise RuntimeError(f"required key/response column absent: {sorted(set(EXPECTED)-set(heads))}")
    idx=[heads.index(x) for x in KEYS]
    keys=Counter()
    sites=defaultdict(set)
    nrows=0
    key_blank=Counter()
    levels={x:set() for x in KEYS}
    for row in reader:
        if len(row)!=len(heads):
            raise RuntimeError("ragged CSV input; source grain cannot be established")
        # Explicitly DO NOT read row[heads.index('no')] -- outcome is sealed.
        vals=tuple(row[i].strip() for i in idx)
        nrows+=1
        for k,v in zip(KEYS,vals):
            if not v: key_blank[k]+=1
            else: levels[k].add(v)
        keys[vals]+=1
        sites[vals[:4]].add(vals[4])
    dupe_keys=sum(n-1 for n in keys.values() if n>1)
    paired=sum(len(v)>=2 for v in sites.values())
    summary={
        "row_count_metadata_only":nrows,
        "distinct_species_or_sonotype_codes":len(levels["species"]),
        "distinct_source_locations":len(levels["location"]),
        "distinct_source_transects":len(levels["transect"]),
        "distinct_season_labels":len(levels["season"]),
        "habitat_labels":sorted(levels["habitat"])[:20],
        "distinct_site_season_distance_keys":len(sites),
        "site_season_distance_keys_with_both_strata":paired,
        "duplicate_six_field_keys":dupe_keys,
        "missing_non_response_key_counts":dict(key_blank),
        "canonical_header_names":heads,
        "bat_pass_values_accessed":False,
        "raw_fine_site_or_species_keys_exported":False,
    }
    eligible=(len(levels["habitat"])>=2 and len(levels["species"])>=2
        and len(levels["location"])>=2 and len(levels["transect"])>=2
        and paired>=10 and dupe_keys==0 and not key_blank)
    summary["status"]="source_structure_pass" if eligible else "source_structure_stop"
    return summary

def main():
    try:
        zip_sha,csv_bytes=download()
        result={
            "dataset_doi":DOI,"source_file":SOURCE_FILE,"archive_sha256":zip_sha,
            "csv_sha256":hashlib.sha256(csv_bytes).hexdigest(),
            "csv_length_bytes":len(csv_bytes),
            **source_only_scan(csv_bytes),
        }
    except Exception as exc:
        result={"dataset_doi":DOI,"source_file":SOURCE_FILE,
                "status":"source_access_or_structure_stop",
                "stop_type":type(exc).__name__,"stop_reason":str(exc)[:400],
                "bat_pass_values_accessed":False}
    path=Path("results/yoh_amazon_vertical_source_preflight_v1.json")
    path.parent.mkdir(parents=True,exist_ok=True)
    path.write_text(json.dumps(result,indent=2,sort_keys=True)+"\n",encoding="utf-8")
    print(json.dumps(result,indent=2,sort_keys=True))
    # Source STOP is scientific, not CI software failure.
    return 0

if __name__=="__main__":
    raise SystemExit(main())
