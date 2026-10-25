"""Freeze provider-original source filenames/UUID/checksums for all 24 UNUSED
source archives selected from the previous complete Movebank GPS header audit.

NO event rows or solar/weather outcomes may be accessed in this step.
"""
from __future__ import annotations
import argparse,hashlib,json
from pathlib import Path
from scripts.movebank_native_ecology_20261019 import HERE,original_files

CONTRACT=HERE/"research/SOLAR_RADIATION_EXTERNAL_24_ORIGINAL_SOURCE_V0_CONTRACT.json"
CATALOG=HERE/"research/seasonal_database_catalog/2026-10-19/movebank/catalog.json"
OLDER=HERE/"research/GLOBAL_SOLAR_AZIMUTH_INDEPENDENT_12SOURCE_V1_CONTRACT.json"
FIRST12=HERE/"research/GLOBAL_SOLAR_AZIMUTH_12_NEW_SOURCE_FROZEN_ORIGINAL_FILE_MANIFEST_20261025.json"
FIRST24=HERE/"research/GLOBAL_SOLAR_AZIMUTH_NEW24_PROVIDER_FROZEN_SOURCE_FILE_MANIFEST_20261025.json"


def frozen_source_metadata_roster():
    c=json.loads(CONTRACT.read_text(encoding="utf-8"))
    if c["version"]!="external-24-original-GPS-solar-radiation-validation-v0":
        raise ValueError("Pre-outcome external original source contract changed")
    full=json.loads(CATALOG.read_text(encoding="utf-8"))["packages"]
    if len(full)!=437 or len({x["package_uuid"] for x in full})!=437:
        raise ValueError("Provider original 437-package catalog incomplete")
    prior9=json.loads(OLDER.read_text(encoding="utf-8"))["previous_sources"]
    prior12=[x["package_uuid"] for x in json.loads(FIRST12.read_text(encoding="utf-8"))["sample_original_file_source_entries"]]
    prior24=[x["package_uuid"] for x in json.loads(FIRST24.read_text(encoding="utf-8"))["source_file_entries"]]
    excludes=prior9+prior12+prior24
    if len(excludes)!=45 or len(set(excludes))!=45:
        raise ValueError("Cannot certify complete previous 45 source exclusions")
    previous={x["package_uuid"]:x for x in full if x["package_uuid"] in excludes}
    if len(previous)!=45:raise ValueError("Previous original source study frame changed")
    priorstudy={study for x in previous.values() for study in x.get("repository_study_ids") or []}

    selection=c["selected_source_roster"]
    if len(selection)!=24 or len({x["package_uuid"] for x in selection})!=24:
        raise ValueError("Exactly 24 external original source candidates were not frozen")
    sources={x["package_uuid"]:x for x in full}
    seen_taxa=set()
    seen_study=set()
    seen_hashes=[]
    output=[]
    for i,s in enumerate(selection):
        if s["rank"]!=i+1 or s["package_uuid"] in excludes:
            raise ValueError("New external source order or overlap changed")
        uuid=s["package_uuid"]
        p=sources.get(uuid)
        if p is None:
            raise ValueError("Original 437-frame missing selected source UUID")
        names=set(p.get("scientific_names") or [])
        studies=set(p.get("repository_study_ids") or [])
        if names!={s["taxon"]} or s["taxon"]=="Homo sapiens":
            raise ValueError("Original registered nonhuman source species changed")
        if len(studies)!=1 or studies&priorstudy or studies&seen_study:
            raise ValueError("Prior or repeated original Movebank study-ID cannot enter heldout source sample")
        if s["taxon"] in seen_taxa:
            raise ValueError("Duplicate literal source taxon in heldout sample")
        if not set(p.get("sensor_names") or [])&{"GPS","GNSS"}:
            raise ValueError("Selected original archive no longer GPS/GNSS-labelled")
        if p["reported_animal_count"] is not None and p["reported_animal_count"]<0:
            raise ValueError("Original repository source animal-count metadata invalid")
        digest=hashlib.sha256((c["seed"]+uuid).encode("utf-8")).hexdigest()
        if seen_hashes and digest<=seen_hashes[-1]:
            raise ValueError("Source hashed rank order not ascending")
        seen_hashes.append(digest)
        seen_taxa.add(s["taxon"])
        seen_study.update(studies)
        output.append({"original_source_package_uuid":uuid,
                       "original_taxon":s["taxon"],
                       "original_repository_study_ids":list(studies),
                       "original_dois":p.get("dois") or [],
                       "original_licenses":p.get("licenses") or [],
                       "frozen_metadata_rank":s["rank"],
                       "selection_SHA256":digest,
                       "expected_original_primary_csv_bytes":s["expected_original_primary_csv_bytes"]})
    return output


def preflight_one(original):
    row={**original,
         "original_file":None,
         "original_source_status":"SOURCE_METADATA_HOLD",
         "original_gps_event_rows_read":0}
    try:
        raw=original_files(original["original_source_package_uuid"])
        data=[
            x for x in raw
            if str(x.get("name") or "").lower().endswith(".csv")
            and "reference-data" not in str(x.get("name") or "").lower()
            and "__macosx" not in str(x.get("name") or "").lower()
            and not str(x.get("name") or "").split("/")[-1].startswith("._")
        ]
        row["original_primary_candidate_count"]=len(data)
        if len(data)!=1:
            row["source_hold_reason"]="Multiple/missing original primary provider CSV"
            return row
        f=data[0]
        if f["bytes"]!=original["expected_original_primary_csv_bytes"]:
            row["source_hold_reason"]="Frozen original source byte count differs from header-source snapshot"
            return row
        ck=f.get("checksum") or {}
        if ck.get("checkSumAlgorithm","").upper() not in ("MD5","SHA256","SHA-256") or not ck.get("value"):
            row["source_hold_reason"]="No supported original provider checksum"
            return row
        row["original_file"]={
            "bitstream_uuid":f["bitstream_uuid"],
            "original_file_name":f["name"],
            "bytes":f["bytes"],
            "provider_checksum":f["checksum"]
        }
        row["original_source_status"]="ORIGINAL_FILE_METADATA_QUALIFIED"
    except Exception as exc:
        row["source_hold_reason"]="Original source metadata unavailable: "+type(exc).__name__
    return row


def main():
    a=argparse.ArgumentParser()
    a.add_argument("--out",type=Path,required=True)
    args=a.parse_args();args.out.mkdir(parents=True,exist_ok=True)
    s=frozen_source_metadata_roster()
    entries=[]
    for original in s:
        entry=preflight_one(original)
        entries.append(entry)
    result={
        "version":"external-24-original-GPS-solar-radiation-validation-v0",
        "date":"2026-10-25",
        "status":"PROVIDER_SOURCE_IDENTITIES_FROZEN_BEFORE_NEW_GPS_OR_WEATHER_OUTCOME",
        "external_source_catalog_frame_size":437,
        "prior_source_exclusion_count":45,
        "source_selection_count":24,
        "provider_original_metadata_qualified":sum(
            s["original_source_status"]=="ORIGINAL_FILE_METADATA_QUALIFIED" for s in entries),
        "provider_original_source_hold":sum(
            s["original_source_status"]=="SOURCE_METADATA_HOLD" for s in entries),
        "original_GPS_positions_or_bearings_read":0,
        "all_selected_original_source_entries":entries
    }
    (args.out/"external_24_provider_source_metadata_before_outcomes.json").write_text(
        json.dumps(result,indent=2,ensure_ascii=False)+"\n",encoding="utf-8")
    print("EXTERNAL_24_ORIGINAL_SOURCE_PREFLIGHT "+
          json.dumps(result,sort_keys=True,ensure_ascii=False),flush=True)


if __name__=="__main__":
    main()
