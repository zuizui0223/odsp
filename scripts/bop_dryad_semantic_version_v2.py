#!/usr/bin/env python3
"""Dryad semantic version/file-list fingerprint, not a GPS or score analysis.

A previous BOP Dryad preflight verified public API access but a replay failed
because the *entire* /versions JSON byte SHA changed. This independent v2
route freezes a semantic identity comparison (published DOI, latest-version
self link/publication date and five filename/size pairs) rather than
mistaking volatile response metadata for scientific source replacement.
The v1 first result and its failed byte-level replay are never rewritten.
"""
from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path
import re
import urllib.error
import urllib.parse
import urllib.request

ROOT=Path(__file__).resolve().parents[1]
CONTRACT=ROOT/"research/BOP_DRYAD_SEMANTIC_VERSION_V2_CONTRACT.json"
DOI="doi:10.5061/dryad.n8pk0p398"
DATASET_URL="https://datadryad.org/api/v2/datasets/doi%3A10.5061%2Fdryad.n8pk0p398"
VERSIONS_URL=DATASET_URL+"/versions"
EXPECTED_FILES=(
    "README.md","Study_areas_bounding_boxes.csv",
    "Complete_succesful_breeding_seasons.csv","Data_1a.csv","Data_2a.csv"
)
_VERSION_LINK=re.compile(r"^/api/v2/versions/([1-9][0-9]*)$")
_FILE_LINK=re.compile(
    r"^https://datadryad[.]org/api/v2/versions/([1-9][0-9]*)/files[?]per_page=100$"
)


class _NoRedirect(urllib.request.HTTPRedirectHandler):
    def redirect_request(self,req,fp,code,msg,headers,newurl):
        raise ValueError("unpinned redirect in official Dryad metadata source")


def _digest(obj:object)->str:
    data=json.dumps(obj,sort_keys=True,ensure_ascii=False,separators=(",",":"),allow_nan=False).encode("utf-8")
    return hashlib.sha256(data).hexdigest()


def load_contract(path:Path=CONTRACT)->dict:
    contract=json.loads(path.read_text(encoding="utf-8"))
    s=contract.get("source",{})
    old=contract.get("historical_first_result_unchanged",{})
    if (
        contract.get("id")!="bop-dryad-semantic-version-identity-v2"
        or contract.get("role")!="post_v1_response_byte_drift_semantic_provenance_correction"
        or s.get("doi")!=DOI
        or s.get("api_dataset")!=DATASET_URL
        or s.get("api_versions")!=VERSIONS_URL
        or tuple(s.get("expected_file_names",()))!=EXPECTED_FILES
        or s.get("no_GPS_or_file_stream_access") is not True
        or s.get("allow_only_three_small_json_api_gets") is not True
        or old.get("original_source_only_run")!=40275944700
        or old.get("no_reinterpretation_of_historical_v1_replay_failure") is not True
        or contract.get("decision",{}).get("historical_BOP_status")!="empirical_state_prediction_mixed"
    ):
        raise ValueError("v2 semantic Dryad source contract changed")
    return contract


def _check_url(url:str,*,latest_version_id:int|None=None)->None:
    parts=urllib.parse.urlsplit(url)
    if parts.scheme!="https" or parts.hostname!="datadryad.org" or parts.fragment or parts.username:
        raise ValueError("only official uncredentialed Dryad HTTPS metadata is allowed")
    if url in (DATASET_URL,VERSIONS_URL):
        return
    if latest_version_id is None or not isinstance(latest_version_id,int) or latest_version_id<1:
        raise ValueError("file inventory requires an independently verified numeric version id")
    if _FILE_LINK.fullmatch(url) is None or int(_FILE_LINK.fullmatch(url).group(1))!=latest_version_id:
        raise ValueError("forbidden file download or non-frozen version metadata URL")


def _get_json(url:str,*,max_bytes:int=131072,latest_version_id:int|None=None)->dict:
    _check_url(url,latest_version_id=latest_version_id)
    if max_bytes<1 or max_bytes>131072:
        raise ValueError("provider API response length exceeds frozen ceiling")
    request=urllib.request.Request(
        url,method="GET",headers={"User-Agent":"odsp-bop-dryad-semantic-v2/1.0","Accept":"application/json"}
    )
    opener=urllib.request.build_opener(_NoRedirect())
    with opener.open(request,timeout=20) as response:
        b=response.read(max_bytes+1)
    if not b or len(b)>max_bytes:
        raise ValueError("Dryad response empty or oversized")
    try:
        parsed=json.loads(b)
    except (ValueError,UnicodeError) as exc:
        raise ValueError("Dryad metadata response is not JSON") from exc
    if not isinstance(parsed,dict):
        raise ValueError("Dryad metadata JSON must be an object")
    return parsed


def semantic_version_identity(dataset:dict,versions:dict,contract:dict)->dict:
    """Only stable publication fields participate in the fingerprint."""
    if dataset.get("identifier")!=DOI:
        raise ValueError("Dryad dataset DOI disagrees with frozen candidate")
    if dataset.get("license")!=contract["source"]["expected_license"]:
        raise ValueError("Dryad explicitly stated license has changed")
    if dataset.get("curationStatus")!="Published":
        raise ValueError("Dryad version not publication-qualified")
    embedded=versions.get("_embedded")
    if not isinstance(embedded,dict) or not isinstance(embedded.get("stash:versions"),list):
        raise ValueError("Dryad published-version roster is unavailable")
    raw_versions=embedded["stash:versions"]
    if len(raw_versions)<1 or len(raw_versions)>20:
        raise ValueError("unexpected published version roster length")
    stable=[]
    for v in raw_versions:
        if not isinstance(v,dict) or not isinstance(v.get("versionNumber"),int) or not isinstance(v.get("publicationDate"),str):
            raise ValueError("published Dryad version lacks numeric version/date")
        href=v.get("_links",{}).get("self",{}).get("href")
        if not isinstance(href,str) or _VERSION_LINK.fullmatch(href) is None:
            raise ValueError("published Dryad version has invalid official self link")
        if v.get("curationStatus") not in (None,"Published"):
            raise ValueError("version roster includes nonpublished state")
        stable.append({
            "versionNumber":v["versionNumber"],
            "publicationDate":v["publicationDate"],
            "self":href,
        })
    if stable!=sorted(stable,key=lambda v:(v["publicationDate"],v["versionNumber"])):
        raise ValueError("Dryad published version roster order differs from documented semantics")
    latest=stable[-1]
    link=dataset.get("_links",{}).get("stash:version",{}).get("href")
    if link!=latest["self"]:
        raise ValueError("Dryad dataset latest-version link differs from published roster")
    if dataset.get("versionNumber")!=latest["versionNumber"]:
        raise ValueError("Dryad dataset version number differs from latest published version")
    if dataset.get("publicationDate")!=latest["publicationDate"]:
        raise ValueError("Dryad current publication date differs from current published version")
    if latest["publicationDate"]!=contract["source"]["expected_publication_date"]:
        raise ValueError("latest public dataset publication date differs from frozen candidate")
    vid=int(_VERSION_LINK.fullmatch(link).group(1))
    return {
        "doi":DOI,
        "license":dataset["license"],
        "curationStatus":"Published",
        "versionNumber":latest["versionNumber"],
        "version_publication_date":latest["publicationDate"],
        "published_version_id":vid,
        "published_version_roster":stable,
    }


def parse_file_inventory(files:dict,expected_version_id:int)->list[dict[str,object]]:
    embedded=files.get("_embedded")
    if not isinstance(embedded,dict) or not isinstance(embedded.get("stash:files"),list):
        raise ValueError("Dryad version file-list schema unavailable")
    entries=embedded["stash:files"]
    if files.get("total")!=len(entries):
        raise ValueError("Dryad file list paginated/incomplete: refuse partial source selection")
    if len(entries)!=5:
        raise ValueError("source file count differs from five frozen public README files")
    records=[]
    for f in entries:
        if not isinstance(f,dict):
            raise ValueError("invalid Dryad file metadata row")
        path=f.get("path")
        size=f.get("size")
        if path not in EXPECTED_FILES or type(size) is not int or size<=0:
            raise ValueError("file path or size missing from provider metadata")
        # No GPS content is read, even for large Data_1a/Data_2a.
        records.append({"name":path,"size":size})
    if len({r["name"] for r in records})!=5:
        raise ValueError("duplicate provider file names in latest version")
    return sorted(records,key=lambda d:d["name"])


def semantic_fingerprint(version:dict,files:list[dict[str,object]])->str:
    return _digest({
        "schema_version":2,
        "doi":version["doi"],
        "license":version["license"],
        "current_published_version":version["published_version_roster"][-1],
        "all_public_versions":version["published_version_roster"],
        "exact_five_filenames_sizes":files,
    })


def run_v2(*,contract_path:Path=CONTRACT,fetcher=None)->dict:
    c=load_contract(contract_path)
    fetch=fetcher or _get_json
    answer={
        "contract_id":c["id"],
        "contract_sha256":hashlib.sha256(contract_path.read_bytes()).hexdigest(),
        "role":c["role"],
        "historical_BOP":"empirical_state_prediction_mixed",
        "v1_first_byte_hash_still_archived":True,
        "v1_replay_raw_metadata_drift_not_erased":True,
        "historical_90pct_new_animal_coverage_inferred":False,
        "raw_GPS_event_data_downloaded":False,
        "external_candidate_admitted":False,
        "original_BOP_RF_directly_usable":False,
    }
    _check_url(c["source"]["api_dataset"])
    _check_url(c["source"]["api_versions"])
    try:
        d=fetch(c["source"]["api_dataset"],max_bytes=131072)
        v=fetch(c["source"]["api_versions"],max_bytes=131072)
    except Exception as exc:
        return {**answer,"source_status":"API_UNAVAILABLE",
                "error_class":type(exc).__name__}
    try:
        identity=semantic_version_identity(d,v,c)
    except ValueError as exc:
        return {**answer,"source_status":"VERSION_METADATA_MISMATCH",
                "error_class":type(exc).__name__,
                "rejected_semantic_field":str(exc)[:140]}
    vid=identity["published_version_id"]
    file_url=f"https://datadryad.org/api/v2/versions/{vid}/files?per_page=100"
    _check_url(file_url,latest_version_id=vid)
    try:
        file_meta=fetch(file_url,max_bytes=131072,latest_version_id=vid)
    except Exception as exc:
        return {**answer,"source_status":"FILE_INVENTORY_UNAVAILABLE",
                "error_class":type(exc).__name__,
                "stable_published_version":identity}
    try:
        names=parse_file_inventory(file_meta,vid)
    except ValueError as exc:
        return {**answer,"source_status":"FILE_INVENTORY_SCHEMA_MISMATCH",
                "rejected_semantic_field":str(exc)[:140],
                "stable_published_version":identity}
    return {
        **answer,
        "source_status":"SEMANTIC_METADATA_VERSION_VERIFIED_ONLY",
        "stable_published_version":identity,
        "file_inventory":names,
        "semantic_fingerprint_sha256":semantic_fingerprint(identity,names),
        "gps_file_contents_read":False,
        "training_or_validation_individual_roster_verified":False,
    }


def main()->None:
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument("--out",type=Path)
    args=p.parse_args()
    answer=run_v2()
    encoded=json.dumps(answer,ensure_ascii=False,sort_keys=True,indent=2,allow_nan=False)+"\n"
    if args.out:
        if args.out.resolve()==CONTRACT.resolve():
            raise ValueError("cannot overwrite frozen method contract")
        args.out.write_text(encoded,encoding="utf-8")
    print(json.dumps({
        "status":answer["source_status"],
        "fingerprint":answer.get("semantic_fingerprint_sha256"),
        "published_version":answer.get("stable_published_version",{}).get("published_version_id"),
        "gps_read":False,
        "old_v1_drift_preserved":True,
    },sort_keys=True))


if __name__=="__main__":
    main()
