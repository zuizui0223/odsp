#!/usr/bin/env python3
"""Erasmy site×height bats source ONLY: official Dryad v2 metadata and CSV header.

No response numbers, correlations, associations, model fitting, or source
species-specific mean activities are inspected. 401/403 => SOURCE_ACCESS_STOP.
"""
from __future__ import annotations
from collections import Counter
import csv
import hashlib
import io
import json
from pathlib import Path
from urllib.parse import urljoin
from urllib.request import Request,urlopen
from urllib.error import HTTPError

HOST="https://datadryad.org"
DOI="10.5061/dryad.cjsxksn6m"
ROOT=HOST+"/api/v2/datasets/doi%3A10.5061%2Fdryad.cjsxksn6m"
ALLOWED={"species_act.csv","guildact.csv","README_verticalstrat_models.txt"}
TARGET="species_act.csv"
CAP=150_000

def official_json(url):
    req=Request(url,headers={"User-Agent":"odsp-public-source-only/1.0",
                             "Accept":"application/json",
                             "X-API-Version":"2.1.0"})
    with urlopen(req,timeout=30) as r:
        raw=r.read(2_000_001)
    if len(raw)>2_000_000:
        raise ValueError("publisher metadata exceeds bounds")
    return json.loads(raw.decode("utf-8"))

def embedded_list(value, preferred):
    if isinstance(value,list):
        return value
    if isinstance(value,dict):
        e=value.get("_embedded",{})
        if isinstance(e,dict):
            for name in preferred:
                if isinstance(e.get(name),list):
                    return e[name]
            options=[v for k,v in e.items() if isinstance(v,list)]
            if len(options)==1:
                return options[0]
        for name in ("items","results","files","versions"):
            if isinstance(value.get(name),list):
                return value[name]
    raise ValueError("official metadata lacks unambiguous array")

def select_version(data):
    a=embedded_list(data,("stash:versions","versions"))
    # Official Dryad HAL version responses often omit a literal "id";
    # canonical version IDs are then encoded in _links.self.href.
    # This is a technical metadata grammar correction made after a
    # pre-response STOP, not a source-outcome or modelling change.
    def version_id(v):
        if isinstance(v.get("id"),int):
            return v["id"]
        h=(v.get("_links") or {}).get("self")
        href=h.get("href") if isinstance(h,dict) else None
        if not isinstance(href,str):
            return None
        from urllib.parse import urlparse
        parsed=urlparse(urljoin(HOST,href))
        if parsed.scheme!="https" or parsed.netloc!="datadryad.org":
            raise ValueError("published version links must stay on Dryad")
        import re
        match=re.fullmatch(r"/api/v2/versions/(\\d+)",parsed.path)
        if not match:
            raise ValueError("invalid publisher version self-link")
        return int(match.group(1))
    active=[(v,version_id(v)) for v in a if isinstance(v,dict)]
    active=[(v,id_) for v,id_ in active if id_ is not None]
    if not active:
        raise ValueError("published dataset has no usable publisher version self-link")
    # Latest by the publisher versionNumber, with official version ID only
    # as an unambiguous tie breaker for genuinely numbered versions.
    versions=[(int(v.get("versionNumber",id_)),id_) for v,id_ in active]
    maximum=max(versions)
    if sum(pair==maximum for pair in versions)!=1:
        raise ValueError("publisher version numbering ambiguous")
    return maximum[1]

def list_file_metadata(value):
    a=embedded_list(value,("stash:files","files"))
    out={}
    for f in a:
        if not isinstance(f,dict):
            continue
        name=f.get("path") or f.get("filename") or f.get("name")
        if isinstance(name,str) and name:
            name=name.split("/")[-1]
            if name in out:
                raise ValueError("duplicate publisher source filename")
            out[name]=f
    if set(out)!=ALLOWED:
        raise ValueError(f"unexpected publisher file roster: {sorted(out)}")
    return out

def download_href(f):
    links=f.get("_links",{})
    if not isinstance(links,dict):
        raise ValueError("file has no publisher download links")
    options=[]
    for key,v in links.items():
        if "download" in key.lower():
            if isinstance(v,dict) and isinstance(v.get("href"),str):
                options.append(v["href"])
            elif isinstance(v,str):
                options.append(v)
    options=list(dict.fromkeys(options))
    if len(options)!=1:
        raise ValueError("file download link is ambiguous or absent")
    href=urljoin(HOST,options[0])
    if not href.startswith(HOST+"/") or not href.startswith("https://"):
        raise ValueError("file link points outside canonical Dryad host")
    return href

def get_original_file(href):
    req=Request(href,headers={"User-Agent":"odsp-public-source-only/1.0",
                             "Accept":"text/csv,*/*",
                             "X-API-Version":"2.1.0"})
    with urlopen(req,timeout=45) as r:
        raw=r.read(CAP+1)
    if not (0<len(raw)<=CAP):
        raise ValueError("original file too large/empty for frozen source gate")
    return raw

def inspect_original_header(raw):
    try:
        s=raw.decode("utf-8-sig")
    except UnicodeDecodeError:
        s=raw.decode("latin-1")
    source=csv.reader(io.StringIO(s,newline=""))
    header=next(source)
    if len(header)<4 or any(not x.strip() for x in header):
        raise ValueError("missing or empty dataset header")
    if len(header)!=len(set(h.strip().lower() for h in header)):
        raise ValueError("duplicate case-insensitive source header")
    widths=Counter()
    for row in source:
        if row:widths[len(row)]+=1
    if not widths or set(widths)!={len(header)}:
        raise ValueError("ragged/empty source table")
    # Source science values may be present in rows but are NEVER converted,
    # accumulated or printed. We inspect only their existence/width.
    return {"header_fields":header,"source_design_rows":sum(widths.values()),
            "all_rows_same_number_columns":True,
            "bat_activity_numeric_values_inspected":False,
            "site_groups_species_values_inspected":False}

def run():
    receipt={"source_doi":DOI,"source_dataset_endpoint":ROOT,
             "original_species_activity_values_opened":False,
             "source_analysis_unblinded":False,"stage":"start"}
    try:
        dat=official_json(ROOT)
        receipt["stage"]="dataset_metadata"
        if not isinstance(dat,dict):
            raise ValueError("metadata missing publisher object")
        versions=official_json(ROOT+"/versions")
        receipt["stage"]="versions"
        version_id=select_version(versions)
        receipt["selected_original_version_id"]=version_id
        listing=official_json(HOST+f"/api/v2/versions/{version_id}/files")
        receipt["stage"]="version_files"
        files=list_file_metadata(listing)
        receipt["original_files"]={name:{
            "size_bytes_publisher":entry.get("size"),
            "digest_publisher":entry.get("digest")}
            for name,entry in files.items()}
        f=files[TARGET]
        href=download_href(f)
        receipt["stage"]="single_original_species_csv_download"
        raw=get_original_file(href)
        receipt["original_species_file_sha256"]=hashlib.sha256(raw).hexdigest()
        receipt["original_species_file_bytes"]=len(raw)
        receipt.update(inspect_original_header(raw))
        receipt["stage"]="source_header_audited"
        receipt["status"]="source_schema_header_admitted_numeric_outcomes_sealed"
    except HTTPError as exc:
        receipt.update({"status":"publisher_source_access_stop","http_status":int(exc.code),
                        "stop_step":receipt["stage"],
                        "reason":"original Dryad REST access did not authorize this request"})
    except Exception as exc:
        receipt.update({"status":"publisher_schema_or_protocol_stop",
                        "stop_step":receipt["stage"],"exception":type(exc).__name__,
                        "reason":str(exc)[:350]})
    return receipt

def main():
    result=run()
    path=Path("results/erasmy_site_height_source_gate_v1.json")
    path.parent.mkdir(parents=True,exist_ok=True)
    path.write_text(json.dumps(result,indent=2,sort_keys=True)+"\n",encoding="utf-8")
    print(json.dumps(result,indent=2,sort_keys=True))
    return 0

if __name__=="__main__":
    raise SystemExit(main())
