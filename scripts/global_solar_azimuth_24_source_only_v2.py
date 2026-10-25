"""Source-only freeze of 24 original primary CSV UUID/MD5; no GPS rows."""
from __future__ import annotations
import argparse,json
from pathlib import Path
from scripts.movebank_native_ecology_20261019 import HERE,original_files
from scripts.global_solar_azimuth_259_original_source_metadata_v0 import SUFFIXES

CONTRACT=HERE/"research/GLOBAL_SOLAR_AZIMUTH_24_SCHEMA_QUALIFIED_NEW_SOURCE_V2_CONTRACT.json"
CATALOG=HERE/"research/seasonal_database_catalog/2026-10-19/movebank/catalog.json"


def source_only_entry(spec,p):
    entry={
       "package_uuid":spec["package_uuid"],
       "source_group":spec["source_type"],
       "source_group_rank":spec["within_group_rank"],
       "original_species_labels":list(dict.fromkeys(p.get("scientific_names") or [])),
       "original_dois":p.get("dois") or [],
       "original_licenses":p.get("licenses") or [],
       "source_study_ids":p.get("repository_study_ids") or [],
       "sample_stratum":spec["source_type"],
       "within_stratum_metadata_rank":spec["within_group_rank"],
       "original_file":None,
       "status":"SOURCE_HOLD",
       "observed_original_GPS_rows":0,
    }
    try:
        allfiles=original_files(spec["package_uuid"])
        candidates=[
            x for x in allfiles
            if str(x.get("name") or "").lower().endswith(".csv")
            and "reference-data" not in str(x.get("name") or "").lower()
            and "__macosx" not in str(x.get("name") or "").lower()
            and not str(x.get("name") or "").split("/")[-1].startswith("._")
        ]
        if len(candidates)!=1:
            entry["hold_reason"]="original single uncompressed CSV no longer uniquely identifiable"
            return entry
        file=candidates[0]
        if file["bytes"]!=spec["expected_original_file_bytes"]:
            entry["hold_reason"]="original source archived byte count differs from header-screen snapshot"
            return entry
        ck=file.get("checksum") or {}
        if ck.get("checkSumAlgorithm","").upper() not in ("MD5","SHA256","SHA-256") or not ck.get("value"):
            entry["hold_reason"]="no valid exact original provider checksum"
            return entry
        entry["original_file"]={
            "bitstream_uuid":file["bitstream_uuid"],"filename":file["name"],
            "bytes":file["bytes"],"checksum":file["checksum"]}
        entry["status"]="ORIGINAL_FILE_METADATA_ADMISSIBLE"
    except Exception as e:
        entry["hold_reason"]=f"{type(e).__name__}: {str(e)[:120]}"
    return entry


def main():
    a=argparse.ArgumentParser()
    a.add_argument("--out",type=Path,required=True)
    args=a.parse_args();args.out.mkdir(parents=True,exist_ok=True)
    c=json.loads(CONTRACT.read_text(encoding="utf-8"))
    catalog=json.loads(CATALOG.read_text(encoding="utf-8"))["packages"]
    if len(catalog)!=437 or len({x["package_uuid"] for x in catalog})!=437:
        raise ValueError("Frozen original full source catalog changed")
    if c["version"]!="global-solar-azimuth-all259-original-header-qualified-24-source-v2":
        raise ValueError("Prospective source qualification contract changed")
    selected=c["source_groups"]
    if len(selected)!=24 or len({x["package_uuid"] for x in selected})!=24:
        raise ValueError("Fixed twenty-four new original source IDs changed")
    byid={x["package_uuid"]:x for x in catalog}
    if not set(x["package_uuid"] for x in selected)<=byid.keys():
        raise ValueError("Previously selected source ID missing from original catalog")
    rows=[]
    for s in selected:
        result=source_only_entry(s,byid[s["package_uuid"]])
        rows.append(result)
    report={
        "version":c["version"],
        "status":"source_metadata_frozen_before_new_v2_original_displacement_outcomes",
        "source_registry_count":437,
        "selected_source_count":24,
        "source_metadata_MD5_listed":sum(x["status"]=="ORIGINAL_FILE_METADATA_ADMISSIBLE" for x in rows),
        "source_meta_HOLD":sum(x["status"]=="SOURCE_HOLD" for x in rows),
        "previous_header_audit_SHA256":c["original_full_259_header_JSON_sha256"],
        "original_GPS_event_rows_opened":0,
        "source_file_entries":rows,
        "scope":"Original bundle UUID, filename, byte count and checksum metadata only; not body orientation, position tracking or a scientifically qualified source."
    }
    (args.out/"v2_original_twentyfour_source_file_manifest.json").write_text(
        json.dumps(report,indent=2,ensure_ascii=False)+"\n",encoding="utf-8")
    print("AZIMUTH_V2_NEW_FILE_SOURCE_PREFLIGHT "+
          json.dumps(report,sort_keys=True,ensure_ascii=False),flush=True)


if __name__=="__main__":
    main()
