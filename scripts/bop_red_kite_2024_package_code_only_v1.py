#!/usr/bin/env python3
"""Code-only 2024 NestTool archived-package versus dated GitHub source audit.

No GPS, outcome CSV, biological ID, RData or model file is opened. Only two
provider-pinned CODE archives and one immutable public GitHub R source file
are downloaded. ZIP metadata are inspected and only source R members are
decompressed in memory, with strict limits. No R code is executed.
"""
from __future__ import annotations

import argparse
from collections import Counter
import hashlib
import io
import json
from pathlib import Path, PurePosixPath
import re
import urllib.request
from urllib.parse import unquote, urlparse
import zipfile

ROOT=Path(__file__).resolve().parents[1]
CONTRACT=ROOT/"research/BOP_RED_KITE_2024_PACKAGE_CODE_V1_CONTRACT.json"
INVENTORY=ROOT/"BOP_RED_KITE_SOURCE_INVENTORY_V1_FIRST_RECEIPT.json"

def _digest(raw:bytes)->dict[str,str]:
    return {
        "sha256":hashlib.sha256(raw).hexdigest(),
        "git_blob_sha1":hashlib.sha1(b"blob "+str(len(raw)).encode("ascii")+b"\0"+raw).hexdigest(),
    }

def _load_frozen():
    c=json.loads(CONTRACT.read_text(encoding="utf-8"))
    i=json.loads(INVENTORY.read_text(encoding="utf-8"))
    files=c.get("authorized_downloads",[])
    z=c.get("strict_access",{})
    pub=c.get("no_claim_promotion",{})
    ref=c.get("reference_source",{})
    if (
        c.get("contract_id")!="bop-red-kite-frozen-2024-package-code-only-v1"
        or c.get("frozen_date")!="2026-11-18"
        or c.get("source_record_id")!=13736049
        or [x.get("name") for x in files]!=["NestTool-1.0.0.zip","NestTool_archived_full_analysis.r"]
        or [x.get("size_bytes") for x in files]!=[6578763,26930]
        or [x.get("provider_md5") for x in files]!=["b172b87191f00f221e9d0151c61d65a6","f3878bd76bd851d0ea048950ee84e8f9"]
        or z.get("no_CSV_or_GPS_file_downloads") is not True
        or z.get("no_model_or_RData_RDS_binary_member_extraction") is not True
        or z.get("inspect_source_members_only_R_files") is not True
        or z.get("required_unique_normalized_member")!="R/data_prep.R"
        or z.get("max_zip_bytes")!=6578763
        or z.get("max_zip_entries")!=1000
        or z.get("max_single_R_source_member_uncompressed_bytes")!=1048576
        or z.get("max_all_R_source_members_uncompressed_bytes")!=4194304
        or z.get("do_not_allow_archive_member_traversal") is not True
        or ref.get("source_commit")!="8fdf3884b5f6079afdffdc5c563c9050766670a4"
        or ref.get("git_blob_sha1")!="3fa42eddbfb852d5dbc29364281bffef8410563e"
        or pub.get("red_kite_biological_terminal")!="HOLD_NO_FROZEN_NEW_NEST_STATE_MODEL_OR_IDENTITY_ROSTER"
        or pub.get("BOP_historical_terminal")!="empirical_state_prediction_mixed"
    ):
        raise ValueError("original pre-access code-only source contract changed")
    mf={x["key"]:x for x in i["source_manifest_observation"]["manifest"]}
    for obj in files:
        k=obj["name"]
        if (obj["url"]!=f"https://zenodo.org/records/13736049/files/{k}?download=1"
            or mf[k]["md5"]!=obj["provider_md5"]
            or mf[k]["bytes"]!=obj["size_bytes"]):
            raise ValueError("provider-original source version or checksum not pinned")
    if ref["url"] != (
        "https://raw.githubusercontent.com/Vogelwarte/NestTool/"
        "8fdf3884b5f6079afdffdc5c563c9050766670a4/R/data_prep.R"
    ):
        raise ValueError("historical GitHub blob not pinned")
    return c

def _fetch_exact(url:str,expected_bytes:int,expected_md5:str|None,*,is_archive:bool)->bytes:
    request=urllib.request.Request(url,headers={
        "User-Agent":"ODSP-NestTool-2024-code-only-source-verification/1.0",
        "Accept-Encoding":"identity",
    })
    with urllib.request.urlopen(request,timeout=90) as r:
        final=urlparse(r.geturl())
        host=final.hostname
        path=unquote(final.path)
        if final.scheme!="https" or int(r.status)!=200:
            raise ValueError("unapproved code-only source HTTP status/scheme")
        if is_archive:
            key=urlparse(url).path.split("/")[-1]
            if (host not in ("zenodo.org","www.zenodo.org")
                or "/13736049/" not in path or key not in path):
                raise ValueError("code-only Zenodo request redirected to unpinned source")
        elif (host!="raw.githubusercontent.com"
              or not path.endswith("/8fdf3884b5f6079afdffdc5c563c9050766670a4/R/data_prep.R")):
            raise ValueError("historical source GitHub commit or URL drifted")
        buf=bytearray()
        while True:
            b=r.read(min(65536,expected_bytes+1-len(buf)))
            if not b:
                break
            buf.extend(b)
            if len(buf)>expected_bytes:
                raise ValueError("provider source exceeds fixed byte budget")
    raw=bytes(buf)
    if is_archive and (len(raw)!=expected_bytes or hashlib.md5(raw).hexdigest()!=expected_md5):
        raise ValueError("provider code ZIP or R script MD5/size does not match frozen manifest")
    if not is_archive and not raw:
        raise ValueError("GitHub dated source is empty")
    return raw

def _safe_name(info:zipfile.ZipInfo)->str:
    name=info.filename
    if not name or "\\" in name or "\0" in name or name.startswith("/"):
        raise ValueError("unsafe ZIP member path")
    parts=PurePosixPath(name).parts
    if any(s in (".","..","") for s in parts):
        raise ValueError("unsafe nested ZIP member name")
    return name

def _is_R_source(name:str)->bool:
    parts=PurePosixPath(name).parts
    return bool(len(parts)>=2 and parts[-2]=="R" and parts[-1].lower().endswith(".r"))

def _is_data_prep(name:str)->bool:
    return _is_R_source(name) and PurePosixPath(name).name=="data_prep.R"

def extract_R_sources(zip_raw:bytes,limits:dict)->dict[str,bytes]:
    """Unzip only R source text, never RData/RDS/CSV/model or vignette files."""
    with zipfile.ZipFile(io.BytesIO(zip_raw)) as z:
        infos=z.infolist()
        if len(infos)>limits["max_zip_entries"]:
            raise ValueError("ZIP entry count violates pinned safety limit")
        out={}
        total=0
        for info in infos:
            name=_safe_name(info)
            if info.is_dir() or not _is_R_source(name):
                continue
            if info.file_size>limits["max_single_R_source_member_uncompressed_bytes"]:
                raise ValueError("ZIP code member exceeds per-member uncompressed cap")
            total+=info.file_size
            if total>limits["max_all_R_source_members_uncompressed_bytes"]:
                raise ValueError("ZIP code members exceed total uncompressed cap")
            if name in out:
                raise ValueError("ZIP duplicate R source member path")
            with z.open(info) as reader:
                b=reader.read(limits["max_single_R_source_member_uncompressed_bytes"]+1)
            if len(b)!=info.file_size:
                raise ValueError("ZIP code-member size mismatch")
            try:
                b.decode("utf-8-sig")
            except UnicodeDecodeError as err:
                raise ValueError("ZIP source member not UTF-8") from err
            out[name]=b
    if sum(1 for name in out if _is_data_prep(name))!=1:
        raise ValueError("required one and only one R/data_prep.R source member")
    return out

def _norm_eol(raw:bytes)->bytes:
    return raw.replace(b"\r\n",b"\n")

def source_pattern_hits(raw:bytes,patterns:list[str],*,max_lines:int=8)->dict[str,list[int]]:
    text=raw.decode("utf-8-sig")
    lines=text.splitlines()
    return {p:[i for i,line in enumerate(lines,1) if p.casefold() in line.casefold()][:max_lines]
            for p in patterns}

def summarize(package:bytes,analysis_script:bytes,git_ref:bytes,c:dict)->dict:
    limits=c["strict_access"]
    manifest=c["authorized_downloads"]
    if (len(package)!=manifest[0]["size_bytes"]
        or hashlib.md5(package).hexdigest()!=manifest[0]["provider_md5"]
        or len(analysis_script)!=manifest[1]["size_bytes"]
        or hashlib.md5(analysis_script).hexdigest()!=manifest[1]["provider_md5"]):
        raise ValueError("unmodified official archive CODE data are required")
    git_hash=_digest(git_ref)
    if git_hash["git_blob_sha1"]!=c["reference_source"]["git_blob_sha1"]:
        raise ValueError("GitHub historical R/data_prep.R blob bytes mismatch")
    if len(git_ref)>limits["max_reference_R_source_bytes"]:
        raise ValueError("historical R reference too large")
    sources=extract_R_sources(package,limits)
    data_prep_name=next(name for name in sources if _is_data_prep(name))
    data_prep=sources[data_prep_name]
    extracted_hash=_digest(data_prep)
    exact=(data_prep==git_ref)
    eol=(_norm_eol(data_prep)==_norm_eol(git_ref))
    status=("PACKAGE_CODE_EXACT_GIT_MATCH" if exact
            else "PACKAGE_CODE_EOL_ONLY_DIFFERENCE" if eol
            else "PACKAGE_CODE_DIFFERENCE")
    patterns=c["predeclared_output"]["analyze_predeclared_static_patterns"]
    data_hits=source_pattern_hits(data_prep,patterns)
    script_hits=source_pattern_hits(analysis_script,patterns)
    thinning_terms=("floor_date(","round_date(","thin","subsampl","60 min","60min","3600")
    pattern_by_file=[]
    for name,src in sources.items():
        these=source_pattern_hits(src,list(thinning_terms))
        if any(these.values()):
            pattern_by_file.append({
                "path":name,
                "thinning_related_literals":{p:hits for p,hits in these.items() if hits},
            })
    return {
        "schema_version":1,
        "status":status,
        "source_role":"ORIGINAL_2024_CODE_ONLY_NO_CSV_GPS_OR_OUTCOMES",
        "frozen_contract_sha256":hashlib.sha256(CONTRACT.read_bytes()).hexdigest(),
        "zip":{**_digest(package),"provider_md5_verified":True,
               "original_size_bytes":len(package),
               "R_member_count":len(sources),
               "R_source_uncompressed_bytes":sum(map(len,sources.values()))},
        "archived_top_level_script":{**_digest(analysis_script),
                 "provider_md5_verified":True,
                 "pattern_line_numbers":{p:v for p,v in script_hits.items() if v}},
        "historical_git_R_data_prep":git_hash,
        "zip_R_data_prep_member_path":data_prep_name,
        "zip_R_data_prep_digest":extracted_hash,
        "data_prep_exact_bytes_equal":exact,
        "data_prep_equal_after_EOL_normalization":eol,
        "zip_data_prep_static_patterns":{p:v for p,v in data_hits.items() if v},
        "thinning_literals_in_R_source_files":pattern_by_file,
        "original_GER_163_65_source_sample_reconstructed":False,
        "original_GER_99_63_eligible_animal_roster_reconstructed":False,
        "verified_GER_archive_GPS_eligible_99_seasons_49_bird_ID_strings_unchanged":True,
        "true_upstream_German_60min_recipe_resolved":False,
        "no_GPS_or_reproductive_labels_accessed":True,
        "red_kite_biological_terminal":"HOLD_NO_FROZEN_NEW_NEST_STATE_MODEL_OR_IDENTITY_ROSTER",
        "BOP_historical_terminal":"empirical_state_prediction_mixed",
    }

def run()->dict:
    c=_load_frozen()
    files=c["authorized_downloads"]
    package=_fetch_exact(files[0]["url"],files[0]["size_bytes"],files[0]["provider_md5"],is_archive=True)
    script=_fetch_exact(files[1]["url"],files[1]["size_bytes"],files[1]["provider_md5"],is_archive=True)
    ref=c["reference_source"]
    github=_fetch_exact(ref["url"],c["strict_access"]["max_reference_R_source_bytes"],None,is_archive=False)
    return summarize(package,script,github,c)

def main():
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument("--out",required=True,type=Path)
    args=p.parse_args()
    if args.out.resolve() in (CONTRACT.resolve(),INVENTORY.resolve()):
        raise ValueError("do not overwrite source contract or original Zenodo manifest")
    try:
        result=run()
    except (OSError,ValueError,UnicodeError,zipfile.BadZipFile,RuntimeError) as exc:
        result={
            "schema_version":1,"status":"SOURCE_PACKAGE_CODE_HOLD",
            "error_type":type(exc).__name__,
            "no_GPS_or_reproductive_labels_accessed":True,
            "red_kite_biological_terminal":"HOLD_NO_FROZEN_NEW_NEST_STATE_MODEL_OR_IDENTITY_ROSTER",
            "BOP_historical_terminal":"empirical_state_prediction_mixed",
        }
    args.out.write_text(json.dumps(result,indent=2,sort_keys=True,allow_nan=False)+"\n",encoding="utf-8")
    print(json.dumps(result,sort_keys=True,allow_nan=False))
    if result["status"]=="SOURCE_PACKAGE_CODE_HOLD":
        raise SystemExit("CODE_PACKAGE_ACCESS_OR_INTEGRITY_HOLD: no new biological inference")

if __name__=="__main__":
    main()
