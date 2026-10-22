#!/usr/bin/env python3
"""Official Dryad version-4 file manifest, metadata-only.

Never download or inspect numeric Altitude_m / AleAboveTerrain. The 2024
paper's 44 tagged cranes are *not* identical to the 32 individual raw 1Hz
CSV files present in the current archived dataset version.
"""
from __future__ import annotations
import argparse
import json
import re
import urllib.request
from pathlib import Path

SOURCE_DOI="10.5061/dryad.t76hdr871"
VERSION=277770
URL=f"https://datadryad.org/api/v2/versions/{VERSION}/files?page=1&per_page=50"
N_FILES=37
N_INDIVIDUAL_GPS_FILES=32
PILOT={
    "README.md":("2905498","dd3db1998b00a4e7a601bfd49586c7c2d213d4b14be7bc69f21f5d90dbe5ab83",13330),
    "16113_1HzGPS_and_ACC_annotated.csv":("2905456","543ddd5b9233c40d982ef109574c9f9c9294471baa6d42f5cfb2ec5e4af8e1a7",2706910)
}

def parse_filelist(source):
    if source.get("total")!=N_FILES:
        raise ValueError("Dryad 2024 archive file total drift")
    files=source.get("_embedded",{}).get("stash:files")
    if not isinstance(files,list) or len(files)!=N_FILES:
        raise ValueError("Dryad page incomplete; do not silently accept partial file list")
    manifest={}
    for entry in files:
        name=entry.get("path")
        size=entry.get("size")
        sha=entry.get("digest")
        link=entry.get("_links",{}).get("self",{}).get("href","")
        ident=link.rsplit("/",1)[-1]
        if not name or name in manifest:
            raise ValueError("Bad or duplicate source member identity")
        if not isinstance(size,int) or size<=0 or not re.fullmatch("[0-9a-f]{64}",sha or ""):
            raise ValueError("Missing exact published source SHA256 or size for "+str(name))
        if not ident.isdigit():
            raise ValueError("Official file resource identifier missing")
        manifest[name]=dict(
            bytes=size,sha256=sha,official_file_id=ident,
            official_download=f"https://datadryad.org/api/v2/files/{ident}/download")
    raw=[n for n in manifest if re.fullmatch(r"\d+_1HzGPS_and_ACC_annotated\.csv",n)]
    if len(raw)!=N_INDIVIDUAL_GPS_FILES:
        raise ValueError("Archived original individual GPS file count drift")
    for name,(id,sha,size) in PILOT.items():
        v=manifest.get(name)
        if not v or (v["official_file_id"],v["sha256"],v["bytes"])!=(id,sha,size):
            raise ValueError("Fixed pilot source file changed "+name)
    other=[n for n in manifest if n not in raw]
    return {
        "analysis":"GRUS_GRUS_DRYAD_VERSION4_OFFICIAL_FILE_MANIFEST_V1",
        "source_DOI":SOURCE_DOI,"source_archive_version_id":VERSION,
        "official_url":URL,
        "record_study_species":"Grus grus",
        "source_reported_tracking_birds":44,
        "raw_individual_1Hz_csv_files":len(raw),
        "record_files":len(manifest),
        "other_source_files":other,
        "total_archived_bytes":sum(v["bytes"] for v in manifest.values()),
        "files":dict(sorted(manifest.items())),
        "native_GPS_height_values_read":False,
        "native_AGL_or_height_missingness_checked":False,
        "biology_outcome_tested":False,
        "stage":"PREHEIGHT_SOURCE_MANIFEST_ONLY",
        "provenance_caveat":"No native event-day or independent cohort counts inferred from 44 publication birds or 32 archived raw-file names."
    }


def main():
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument("--output",required=True,type=Path)
    opt=p.parse_args()
    request=urllib.request.Request(URL,headers={
        "User-Agent":"ODSP-research-source-audit/1.0","Accept":"application/json"
    })
    with urllib.request.urlopen(request,timeout=90) as fp:
        out=parse_filelist(json.load(fp))
    opt.output.parent.mkdir(parents=True,exist_ok=True)
    opt.output.write_text(json.dumps(out,indent=2,sort_keys=True)+"\n")
    print(json.dumps({
        "files":out["record_files"],
        "individual_1Hz_files":out["raw_individual_1Hz_csv_files"],
        "bytes_total":out["total_archived_bytes"],
        "README_sha":out["files"]["README.md"]["sha256"],
        "height_values_read":False
    },sort_keys=True))


if __name__=="__main__":
    main()
