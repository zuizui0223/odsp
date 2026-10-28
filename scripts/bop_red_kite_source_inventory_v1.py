#!/usr/bin/env python3
"""No-response Zenodo metadata inventory for an independent ODSP state candidate.

The v1 contract was committed before any direct call to the provider's
official JSON API. Only ONE pinned Zenodo metadata document is read.
NO tracking file, individual-season (reproductive-label) CSV, GPS
position or original published analysis code is downloaded.

An inventory pass does not prove eligible birds, exchangeable new
individuals, nest-state predictive gain, or altitude compatibility.
"""
from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path
from typing import Mapping
import urllib.request
from urllib.parse import urlparse

ROOT=Path(__file__).resolve().parents[1]
CONTRACT=ROOT/"research/BOP_RED_KITE_SOURCE_INVENTORY_V1_CONTRACT.json"
_RETAINED_FIELDS=("key","checksum","size","role")
_TERMINAL_HOLD="HOLD_NEW_NEST_STATE_TARGET_AND_AUTHENTIC_GROUP_ROSTER_NOT_YET_FROZEN"


def _sha(raw:bytes)->str:
    return hashlib.sha256(raw).hexdigest()


def _pinned_contract()->dict:
    spec=json.loads(CONTRACT.read_text(encoding="utf-8"))
    target=spec.get("target_source",{})
    files=spec.get("expected_files",[])
    if (
        spec.get("contract_id")!="bop-red-kite-nest-state-external-source-inventory-v1"
        or spec.get("frozen_date")!="2026-10-28"
        or target.get("zenodo_record_id")!=13736049
        or target.get("allowed_metadata_api")!="https://zenodo.org/api/records/13736049"
        or target.get("maximum_metadata_json_bytes")!=500000
        or len(files)!=6
        or any(f.get("key","").lower().endswith(".csv") and not f.get("role","").endswith("DO_NOT_OPEN") for f in files)
        or target.get("allow_event_or_summary_csv_download") is not False
        or target.get("allow_file_content_download") is not False
        or target.get("allow_altitude_or_location_access") is not False
        or spec.get("criteria",{}).get("biology_terminal_always")!=_TERMINAL_HOLD
    ):
        raise ValueError("frozen source/no-response contract changed")
    for file in files:
        digest=file["md5"]
        if len(digest)!=32 or any(c not in "0123456789abcdef" for c in digest):
            raise ValueError("frozen source file MD5 malformed")
    return spec


def _provider_get_exact_metadata(url:str,byte_cap:int)->bytes:
    """Read exact allowlisted API only; never follow a non-API redirect."""
    if url!="https://zenodo.org/api/records/13736049":
        raise ValueError("unapproved source URL")
    req=urllib.request.Request(url,headers={
        "Accept":"application/json",
        "User-Agent":"ODSP-BOP-source-metadata-only/1.0",
    })
    with urllib.request.urlopen(req,timeout=30) as stream:
        final=urlparse(stream.geturl())
        if final.scheme!="https" or final.netloc!="zenodo.org" or final.path!="/api/records/13736049":
            raise ValueError("source redirected outside frozen metadata API")
        body=stream.read(byte_cap+1)
    if not body or len(body)>byte_cap:
        raise ValueError("source metadata absent or oversized")
    return body


def _md5(value:object)->str:
    if not isinstance(value,str):
        raise ValueError("provider MD5 not a string")
    digest=value.removeprefix("md5:")
    if len(digest)!=32 or any(c not in "0123456789abcdef" for c in digest):
        raise ValueError("provider MD5 malformed")
    return digest


def _license(metadata:Mapping)->str|None:
    item=metadata.get("license")
    if isinstance(item,str):
        return item[:120] if item else None
    if isinstance(item,Mapping):
        label=item.get("id") or item.get("title")
        if isinstance(label,str) and label:
            return label[:120]
    return None


def classify_zenodo_inventory(record:Mapping, spec:Mapping, *, raw_metadata:bytes)->dict:
    """Compare only provider manifest filenames/checksums, not file content."""
    source=spec["target_source"]
    expected=spec["expected_files"]
    entry=record.get("id")
    meta=record.get("metadata")
    if (
        type(entry) is not int or entry!=source["zenodo_record_id"]
        or not isinstance(meta,Mapping)
    ):
        raise ValueError("Zenodo source record/version metadata identity mismatch")
    doi=record.get("doi") or meta.get("doi")
    if doi!=source["zenodo_doi"]:
        raise ValueError("Zenodo DOI is not pinned version")
    raw_files=record.get("files")
    if not isinstance(raw_files,list):
        raise ValueError("Zenodo file manifest missing")
    actual={}
    for item in raw_files:
        if not isinstance(item,Mapping):
            raise ValueError("provider file manifest row malformed")
        name=item.get("key") or item.get("filename")
        if not isinstance(name,str) or name in actual or not name:
            raise ValueError("provider file name missing or duplicated")
        digest=_md5(item.get("checksum"))
        size=item.get("size")
        if type(size) is not int or size<0 or size>2_000_000_000:
            raise ValueError("unexpected provider source file size")
        actual[name]={"key":name,"md5":digest,"size":size}
    expected_map={e["key"]:e for e in expected}
    if set(actual)!=set(expected_map):
        raise ValueError("Zenodo file roster differs from frozen data source")
    if any(
        actual[key]["md5"]!=item["md5"]
        for key,item in expected_map.items()
    ):
        raise ValueError("Zenodo file metadata MD5 differs from frozen expected")
    is_published=record.get("is_published") is True or record.get("status")=="published"
    if not is_published:
        raise ValueError("Zenodo provider metadata not explicitly published")
    declared_files=[
        {
            "key":row["key"],
            "manifest_md5":row["md5"],
            "provider_size_bytes":row["size"],
            "role":expected_map[row["key"]]["role"],
            "file_bytes_downloaded":False,
        }
        for row in (actual[k] for k in sorted(actual))
    ]
    return {
        "schema_version":1,
        "source_doi":doi,
        "record_id":entry,
        "published":True,
        "provider_license_id":_license(meta),
        "metadata_version":str(meta.get("version") or "UNDECLARED")[:90],
        "metadata_sha256":_sha(raw_metadata),
        "file_count":len(actual),
        "official_file_inventory_verified":True,
        "declared_file_list":declared_files,
        "total_provider_file_bytes":sum(row["size"] for row in actual.values()),
        "read_actions":["EXACT_PUBLIC_ZENODO_METADATA_API_ONLY"],
        "source_inventory_terminal":"SOURCE_FILE_INVENTORY_VERIFIED_ONLY",
        "biology_terminal":_TERMINAL_HOLD,
        "outcome_rows_accessed":False,
        "historical_BOP_mixed_preserved":True,
        "original_BOP_RF_altitude_validation":False,
        "German_sample_roster_opened":False,
        "published_sample_count_not_validated_against_files":True,
        "real_external_group_gain_estimated":False,
        "old_Dryad_original_RF_gate_reopened":False,
    }


def run()->dict:
    c=_pinned_contract()
    raw=_provider_get_exact_metadata(
        c["target_source"]["allowed_metadata_api"],
        c["target_source"]["maximum_metadata_json_bytes"],
    )
    obj=json.loads(raw)
    if not isinstance(obj,Mapping):
        raise ValueError("provider JSON is not a record")
    return classify_zenodo_inventory(obj,c,raw_metadata=raw)


def main()->None:
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--out",required=True,type=Path)
    args=parser.parse_args()
    try:
        result=run()
    except (OSError, ValueError, json.JSONDecodeError) as exc:
        result={
            "schema_version":1,
            "source_inventory_terminal":"SOURCE_METADATA_ACCESS_OR_VERSION_HOLD",
            "biology_terminal":_TERMINAL_HOLD,
            "error_category":type(exc).__name__,
            "read_actions":["EXACT_PUBLIC_ZENODO_METADATA_API_ATTEMPT_ONLY"],
            "outcome_rows_accessed":False,
            "historical_BOP_mixed_preserved":True,
            "original_BOP_RF_altitude_validation":False,
            "real_external_group_gain_estimated":False,
        }
    dest=args.out.resolve()
    if dest==CONTRACT.resolve():
        raise ValueError("cannot replace frozen contract")
    args.out.write_text(json.dumps(result,indent=2,sort_keys=True,allow_nan=False)+"\n",encoding="utf-8")
    print(json.dumps({
        "inventory":result["source_inventory_terminal"],
        "biology":result["biology_terminal"],
        "files":result.get("file_count"),
        "outcome_accessed":result["outcome_rows_accessed"],
    },sort_keys=True))
    if result["source_inventory_terminal"]!="SOURCE_FILE_INVENTORY_VERIFIED_ONLY":
        raise SystemExit("SOURCE_METADATA_ACCESS_OR_VERSION_HOLD: no outcome file opened")


if __name__=="__main__":
    main()
