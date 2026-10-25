"""Original CSV header-only qualification over ALL 259 Movebank GPS/GNSS packages.

Never accesses original animal response values or publishes GPS tracks.
Original full files must be provider-checksum verified before animal analysis.
"""
from __future__ import annotations
import argparse
from collections import Counter
from concurrent.futures import ThreadPoolExecutor, as_completed
import csv
from io import StringIO
import json
from pathlib import Path
from urllib.request import Request,urlopen
from scripts.movebank_native_ecology_20261019 import HERE,ROOT,original_files

CONTRACT=HERE/"research/GLOBAL_SOLAR_AZIMUTH_ALL259_ORIGINAL_CSV_HEADER_V0_CONTRACT.json"
CATALOG=HERE/"research/seasonal_database_catalog/2026-10-19/movebank/catalog.json"
CAP=8192
MAX_TRANSFER_BYTES=120000000
ALLOWED=(".csv",".csv.gz",".zip")
REQUIRED={"timestamp","individual-local-identifier","location-lat","location-long"}


def supported_original_files(original):
    return [p for p in original
            if str(p.get("name") or "").lower().endswith(ALLOWED)
            and "reference-data" not in str(p.get("name") or "").lower()
            and not str(p.get("name") or "").split("/")[-1].startswith("._")
            and "__macosx" not in str(p.get("name") or "").lower()]


def parse_header_preview(raw):
    """Only FIRST CSV header row is used; do not emit any original source row."""
    if not raw or raw[:2]==b"PK" or raw[:2]==b"\x1f\x8b":
        return {"schema_hint":"BINARY_OR_EMPTY","valid_required_columns":False}
    text=raw.decode("utf-8-sig",errors="replace")
    idx=text.find("\n")
    if idx < 0:
        return {"schema_hint":"HEADER_TOO_LONG_OR_NO_NEWLINE","valid_required_columns":False}
    first=text[:idx].rstrip("\r")
    try:
        headers=next(csv.reader(StringIO(first)))
    except (StopIteration,csv.Error):
        return {"schema_hint":"HEADER_CSV_PARSE_FAIL","valid_required_columns":False}
    normalized=[str(x).strip().lower() for x in headers]
    supported=REQUIRED.issubset(set(normalized)) and len(set(normalized))==len(normalized)
    return {
        "schema_hint":"CANONICAL_GPS_HEADER" if supported else "MISSING_REQUIRED_OR_DUPLICATE_HEADERS",
        "valid_required_columns":supported,
        "native_taxon_column_present":"individual-taxon-canonical-name" in normalized,
        "n_original_columns":len(normalized),
        "n_required_columns_present":sum(k in normalized for k in REQUIRED),
    }


def source_first_header(uuid):
    url=ROOT+"/core/bitstreams/"+uuid+"/content"
    req=Request(url,headers={"User-Agent":"ODSP-public-original-header-audit/20261025",
                             "Range":"bytes=0-"+str(CAP-1),
                             "Accept":"application/octet-stream"})
    with urlopen(req,timeout=30) as response:
        # A provider may ignore Range; never read more than the fixed CAP.
        raw=response.read(CAP)
        code=response.status
    return raw,code


def screen_one(p):
    row={
        "package_uuid":p["package_uuid"],
        "repository_study_ids":p.get("repository_study_ids") or [],
        "scientific_name_labels":p.get("scientific_names") or [],
        "original_sensor_labels":p.get("sensor_names") or [],
        "original_dois":p.get("dois") or [],
        "original_license_labels":p.get("licenses") or [],
        "status":"SOURCE_HOLD",
        "original_candidate_count":None,
        "source_header_previewed":False,
        "source_GPS_records_qualified":0
    }
    try:
        files=supported_original_files(original_files(p["package_uuid"]))
        row["original_candidate_count"]=len(files)
        if len(files)!=1:
            row["status"]="AMBIGUOUS_OR_MISSING_SINGLE_ORIGINAL_FILE"
            return row
        f=files[0]
        row["file_suffix_type"]="zip" if f["name"].lower().endswith(".zip") else (
            "gz" if f["name"].lower().endswith(".csv.gz") else "csv")
        row["source_original_file_bytes"]=f.get("bytes")
        row["provider_checksum_listed"]=bool((f.get("checksum") or {}).get("value"))
        if not row["provider_checksum_listed"]:
            row["status"]="NO_ORIGINAL_PROVIDER_CHECKSUM"
        elif not isinstance(f.get("bytes"),int) or f["bytes"]>MAX_TRANSFER_BYTES:
            row["status"]="FILE_TOO_LARGE_FOR_V1_ORIGINAL_TRANSFER_CAP"
        elif row["file_suffix_type"] in ("zip","gz"):
            row["status"]="COMPRESSED_ORIGINAL_REQUIRES_VERIFIED_DOWNLOAD"
        else:
            raw,http_code=source_first_header(f["bitstream_uuid"])
            row["source_header_previewed"]=True
            row["http_code"]=http_code
            report=parse_header_preview(raw)
            row.update(report)
            row["status"]="CANONICAL_ORIGINAL_CSV_HEADER" if report["valid_required_columns"] else "ORIGINAL_HEADER_MISSING_REQUIRED_FIELDS"
    except Exception as ex:
        row["status"]="SOURCE_HEADER_HOLD"
        # Never log raw page, GPS values, user/source credentials or coordinates.
        row["error_type"]=type(ex).__name__
        row["http_error_code"]=getattr(ex,"code",None)
    return row


def main():
    parser=argparse.ArgumentParser()
    parser.add_argument("--out",required=True,type=Path)
    parser.add_argument("--workers",default=8,type=int)
    args=parser.parse_args()
    if not 1<=args.workers<=8:raise ValueError("Pre-registered upper limit eight concurrent calls")
    args.out.mkdir(parents=True,exist_ok=True)
    contract=json.loads(CONTRACT.read_text(encoding="utf-8"))
    if contract["version"]!="global-azimuth-all259-original-GPS-header-snapshot-v0":
        raise ValueError("Header audit protocol not frozen")
    packages=json.loads(CATALOG.read_text(encoding="utf-8"))["packages"]
    if len(packages)!=437 or len({p["package_uuid"] for p in packages})!=437:
        raise ValueError("Original public catalog not complete")
    selection=[p for p in packages if any(v in ("GPS","GNSS") for v in p.get("sensor_names") or [])]
    if len(selection)!=259:
        raise ValueError("Original GPS/GNSS frame is no longer exactly 259")
    rows=[]
    with ThreadPoolExecutor(max_workers=args.workers) as pool:
        fs=[pool.submit(screen_one,p) for p in selection]
        for f in as_completed(fs):
            rows.append(f.result())
    rows.sort(key=lambda x:x["package_uuid"])
    statuses=dict(sorted(Counter(x["status"] for x in rows).items()))
    summary={
        "original_registry_packages":437,
        "GPS_GNSS_original_candidate_packages":259,
        "source_package_results":len(rows),
        "status_counts":statuses,
        "canonical_GPS_header_source_candidates":statuses.get("CANONICAL_ORIGINAL_CSV_HEADER",0),
        "original_source_rows_processed_or_qualified":0,
        "original_bitstream_full_MD5_verified_by_header_probe":0,
        "result_scope":"Source original first HEADER only: no cadence, timestamp provenance, independent population unit or GPS-step validity proven."
    }
    (args.out/"all259_original_GPS_header_preview_per_source.json").write_text(
        json.dumps(rows,indent=2,ensure_ascii=False)+"\n",encoding="utf-8")
    (args.out/"all259_GPS_header_screen_summary.json").write_text(
        json.dumps(summary,indent=2,ensure_ascii=False)+"\n",encoding="utf-8")
    print("GLOBAL_SOLAR_259_HEADER_SCREEN_SUMMARY "+
          json.dumps(summary,sort_keys=True,ensure_ascii=False),flush=True)


if __name__=="__main__":
    main()
