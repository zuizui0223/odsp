#!/usr/bin/env python3
"""Pin Zenodo 2026 multi-taxon source manifest before any vertical outcomes.

Reads ONLY official Zenodo record metadata; downloads no data bytes, and opens
no per-GPS altitude/behavior/environment response values.
"""
from __future__ import annotations

import argparse
import json
import urllib.request
from pathlib import Path

DOI="10.5281/zenodo.21915776"
RECORD_ID=21915776
ZENODO_URL=f"https://zenodo.org/api/records/{RECORD_ID}"
ESSENTIAL={"Data.zip","Readme_Metadata.txt","Table_allDatasets_contacts_permits.pdf"}


def parse_record(record:dict)->dict:
    if int(record.get("id",-1)) != RECORD_ID:
        raise ValueError("Zenodo record identity mismatch")
    actual_doi=(record.get("doi") or record.get("pids",{}).get("doi",{}).get("identifier") or "")
    if actual_doi != DOI:
        raise ValueError("Exact parent version DOI mismatch")
    files=record.get("files")
    if not isinstance(files,list):
        raise ValueError("Record files list absent / archived API contract changed")
    by_name={}
    for file in files:
        name=file.get("key")
        if not name or name in by_name:raise ValueError("No unique file key")
        checks=file.get("checksum")
        if not checks or not checks.startswith("md5:"):
            raise ValueError("Missing checksum for "+name)
        size=file.get("size")
        if not isinstance(size,int) or size<0:
            raise ValueError("Missing integer file size for "+name)
        by_name[name]={
            "bytes":size,
            "md5":checks.split(":",1)[1],
            "direct_url":f"https://zenodo.org/records/{RECORD_ID}/files/{name}?download=1"
        }
    if not ESSENTIAL<=set(by_name):
        raise ValueError("New source data files or names have drifted: "+repr(ESSENTIAL-set(by_name)))
    metadata=record.get("metadata") or {}
    license_obj=metadata.get("license") or {}
    resource_type=metadata.get("resource_type") or {}
    access=record.get("access") or {}
    source={
        "catalog":"SCACCO_CROSS_GUILD_PUBLIC_RECORD_METADATA_V1",
        "record_id":RECORD_ID,
        "doi":actual_doi,
        "source":"https://zenodo.org/records/21915776",
        "title":metadata.get("title"),
        "publication_date":metadata.get("publication_date"),
        "created":record.get("created"),
        "updated":record.get("updated"),
        "version":metadata.get("version"),
        "license_id":license_obj.get("id"),
        "license_url":license_obj.get("url"),
        "license_title":license_obj.get("title"),
        "access_status":access.get("record"),
        "files_status":access.get("files"),
        "resource_type":resource_type,
        "files":dict(sorted(by_name.items())),
        "data_zip_mb":round(by_name["Data.zip"]["bytes"]/1e6,3),
        "file_bytes_sum":sum(v["bytes"] for v in by_name.values()),
        "native_gps_altitude_values_read":False,
        "original_biological_outcome_reanalyzed":False,
        "stage":"ARCHIVE_MANIFEST_ONLY"
    }
    return source


def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--out",required=True,type=Path)
    args=parser.parse_args()
    request=urllib.request.Request(ZENODO_URL,headers={
        "Accept":"application/json",
        "User-Agent":"odsp-reproducibility-source-inventory/1.0"
    })
    with urllib.request.urlopen(request,timeout=90) as fp:
        j=json.load(fp)
    result=parse_record(j)
    args.out.parent.mkdir(parents=True,exist_ok=True)
    args.out.write_text(json.dumps(result,indent=2,ensure_ascii=False,sort_keys=True)+"\n",encoding="utf-8")
    print(json.dumps({
        "data_zip_mb":result["data_zip_mb"],
        "license":result["license_id"],
        "files_access":result["files_status"],
        "files":{k:{"bytes":v["bytes"],"md5":v["md5"]} for k,v in result["files"].items()},
        "height_opened":False,
    },sort_keys=True))


if __name__=="__main__":
    main()
