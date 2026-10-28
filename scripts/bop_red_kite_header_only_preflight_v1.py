#!/usr/bin/env python3
"""Headers-only, no-response preflight for the pinned Oppel red-kite release.

The strict allowed access is one HTTP Range request per four pinned CSV
paths, consuming at most the FIRST PHYSICAL LINE of each file. Never
parse or retain any per-animal season value, GPS row or nesting outcome.
Published file MD5 strings were verified in Zenodo metadata but the CSV
content MD5 is NOT verified by a header-only read.
"""
from __future__ import annotations

import argparse
import csv
import hashlib
import io
import json
from pathlib import Path
from typing import Mapping
from urllib.parse import unquote,urlparse
import urllib.request

ROOT=Path(__file__).resolve().parents[1]
CONTRACT=ROOT/"research/BOP_RED_KITE_HEADER_ONLY_V1_CONTRACT.json"
PRIOR=ROOT/"BOP_RED_KITE_SOURCE_INVENTORY_V1_FIRST_RECEIPT.json"

def _sha(raw:bytes)->str:
    return hashlib.sha256(raw).hexdigest()


def _pinned():
    c=json.loads(CONTRACT.read_text(encoding="utf-8"))
    r=json.loads(PRIOR.read_text(encoding="utf-8"))
    files=c.get("authorized_header_requests",[])
    original={x["key"]:x for x in r["source_manifest_observation"]["manifest"]}
    expected=[
        "GER_indseasondata.csv","SUI_indseasondata.csv",
        "GER_trackingdata.csv","SUI_trackingdata.csv",
    ]
    if (
        c.get("contract_id")!="bop-red-kite-sealed-header-only-source-schema-v1"
        or c.get("frozen_date")!="2026-10-28"
        or c.get("technical_access",{}).get("max_header_bytes_per_file")!=4096
        or c.get("technical_access",{}).get("send_HTTP_Range")!="bytes=0-4095"
        or c.get("technical_access",{}).get("never_read_GPS_event_rows") is not True
        or c.get("technical_access",{}).get("never_read_NestTool_individual_season_data_rows") is not True
        or c.get("predeclared_interpretation",{}).get("biological_terminal_always")!="HOLD_NO_FROZEN_NEW_NEST_STATE_MODEL_OR_IDENTITY_ROSTER"
        or [x.get("key") for x in files]!=expected
        or r["scientific_terminal"]["no_breeding_success_outcomes_accessed"] is not True
        or r["scientific_terminal"]["no_tracking_CSVs_or_GPS_accessed"] is not True
    ):
        raise ValueError("frozen response-free schema or upstream receipt drifted")
    for x in files:
        name=x["key"]
        if (
            x["url"]!=f"https://zenodo.org/records/13736049/files/{name}?download=1"
            or name not in original
            or x["source_manifest_md5"]!=original[name]["md5"]
            or not name.endswith(".csv")
        ):
            raise ValueError("source file allowlist or original MD5 manifest changed")
    return c,r


def _read_exact_first_physical_line(url:str,key:str,limit:int)->tuple[bytes,int]:
    """Do not call .read() on whole CSV; consume only until first newline."""
    if url!=f"https://zenodo.org/records/13736049/files/{key}?download=1":
        raise ValueError("not an authorized header-only source URL")
    request=urllib.request.Request(url,headers={
        "User-Agent":"ODSP-BOP-redkite-CSV-header-only/1.0",
        "Range":"bytes=0-4095",
        "Accept-Encoding":"identity",
    })
    with urllib.request.urlopen(request,timeout=30) as response:
        final=urlparse(response.geturl())
        path=unquote(final.path)
        if (
            final.scheme!="https"
            or final.hostname not in ("zenodo.org","www.zenodo.org")
            or "/13736049/" not in path
            or key not in path
        ):
            raise ValueError("unexpected host or file redirect for header-only URL")
        status=int(response.status)
        if status not in (200,206):
            raise ValueError("unexpected provider status for source header")
        line=bytearray()
        while len(line)<=limit:
            one=response.read(1)
            if not one:
                break
            line.extend(one)
            if one==b"\n":
                break
    if not line or line[-1:]!=b"\n" or len(line)>limit:
        raise ValueError("single complete physical CSV header not available within limit")
    if b"\x00" in line or b"\r" in line[:-2]:
        raise ValueError("unexpected binary/header line format")
    return bytes(line),status


def _parse_header(raw:bytes)->tuple[str,...]:
    if not raw.endswith(b"\n"):
        raise ValueError("complete header with terminal newline required")
    try:
        decoded=raw.decode("utf-8-sig")
    except UnicodeDecodeError as exc:
        raise ValueError("header is not UTF-8") from exc
    # Parse exactly one physical line, never the full CSV nor the first row.
    parsed=list(csv.reader(io.StringIO(decoded),strict=True))
    if len(parsed)!=1 or not parsed[0]:
        raise ValueError("not a single valid CSV header")
    columns=tuple(parsed[0])
    if any(
        not isinstance(col,str) or not col or col!=col.strip()
        for col in columns
    ) or len(set(columns))!=len(columns):
        raise ValueError("duplicate, empty or malformed header column")
    if any("\n" in name or "\r" in name for name in columns):
        raise ValueError("multiline CSV headers are unsupported")
    return columns


def classify_headers(
    headers:Mapping[str,tuple[bytes,int]],spec:Mapping,prior:Mapping
)->dict:
    pinned=spec["authorized_header_requests"]
    if set(headers)!={x["key"] for x in pinned}:
        raise ValueError("exact four response-free source headers required")
    names=[]
    candidates=spec["provisional_schema_signals"]
    for item in pinned:
        key=item["key"]
        physical,status=headers[key]
        if len(physical)>spec["technical_access"]["max_header_bytes_per_file"]:
            raise ValueError("header source exceeded fixed byte budget")
        cols=_parse_header(physical)
        lowered={name.casefold():name for name in cols}
        alias=[x for x in candidates["candidate_animal_field_aliases"] if x.casefold() in lowered]
        outcomes=[x for x in candidates["candidate_season_outcome_fields"] if x.casefold() in lowered]
        names.append({
            "file":key,
            "header_sha256":_sha(physical),
            "header_bytes_only":len(physical),
            "HTTP_status":status,
            "columns":list(cols),
            "year_id_key_present":candidates["sequence_link_key"].casefold() in lowered,
            "candidate_animal_ID_field_aliases":alias,
            "candidate_outcome_field_names_only":outcomes,
            "source_manifest_md5_string":item["source_manifest_md5"],
            "source_full_content_MD5_verified":False,
            "GPS_or_breeding_outcome_row_parsed":False,
        })
    all_year_keys=all(x["year_id_key_present"] for x in names)
    indseason=[x for x in names if x["file"].endswith("_indseasondata.csv")]
    has_animal_alias=all(bool(x["candidate_animal_ID_field_aliases"]) for x in indseason)
    return {
        "schema_version":1,
        "contract_id":spec["contract_id"],
        "contract_sha256":_sha(CONTRACT.read_bytes()),
        "upstream_source_inventory_first_artifact":prior["initial_verified_actions"]["workflow_artifact_id"],
        "source_role":"OBSERVED_CSV_HEADERS_ONLY_NO_RESPONSES",
        "file_count":4,
        "header_fields":names,
        "all_four_sources_have_year_id":all_year_keys,
        "individual_season_headers_have_candidate_animal_key":has_animal_alias,
        "structural_header_status":(
            "SOURCE_HEADERS_RECORDED_NO_FULL_DATA_ACCESS"
            if all_year_keys and has_animal_alias
            else "HOLD_MISSING_YEAR_OR_ANIMAL_IDENTIFIER_SCHEMA"
        ),
        "scientific_terminal":"HOLD_NO_FROZEN_NEW_NEST_STATE_MODEL_OR_IDENTITY_ROSTER",
        "per_animal_source_counts_verified":False,
        "source_file_content_MD5_verified":False,
        "outcome_values_parsed":False,
        "GPS_event_values_parsed":False,
        "published_German_bird_count_63_admitted":False,
        "historical_BOP_original_RF_reestimated":False,
        "original_BOP_terminal":"empirical_state_prediction_mixed",
        "real_external_probability_gain_scored":False,
    }


def run()->dict:
    spec,prior=_pinned()
    out={}
    limit=spec["technical_access"]["max_header_bytes_per_file"]
    for f in spec["authorized_header_requests"]:
        out[f["key"]]=_read_exact_first_physical_line(f["url"],f["key"],limit)
    return classify_headers(out,spec,prior)


def main()->None:
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument("--out",required=True,type=Path)
    args=p.parse_args()
    try:
        result=run()
    except (OSError,ValueError,csv.Error) as exc:
        result={
            "schema_version":1,
            "source_role":"HEADER_ACCESS_OR_SCHEMA_HOLD",
            "scientific_terminal":"HOLD_NO_FROZEN_NEW_NEST_STATE_MODEL_OR_IDENTITY_ROSTER",
            "error_category":type(exc).__name__,
            "outcome_values_parsed":False,
            "GPS_event_values_parsed":False,
            "real_external_probability_gain_scored":False,
            "original_BOP_terminal":"empirical_state_prediction_mixed",
        }
    if args.out.resolve() in (CONTRACT.resolve(),PRIOR.resolve()):
        raise ValueError("do not overwrite preaccess contract or first inventory receipt")
    args.out.write_text(json.dumps(result,indent=2,sort_keys=True,allow_nan=False)+"\n",encoding="utf-8")
    print(json.dumps({
        "header_status":result.get("structural_header_status",result["source_role"]),
        "header_count":result.get("file_count"),
        "outcome_values_parsed":result["outcome_values_parsed"],
        "GPS_event_values_parsed":result["GPS_event_values_parsed"],
        "biological_status":result["scientific_terminal"],
    },sort_keys=True))
    if result["source_role"]=="HEADER_ACCESS_OR_SCHEMA_HOLD":
        raise SystemExit("SOURCE_HEADER_ACCESS_HOLD: biological outputs remain closed")


if __name__=="__main__":
    main()
