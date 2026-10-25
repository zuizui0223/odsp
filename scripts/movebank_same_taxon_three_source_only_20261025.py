#!/usr/bin/env python3
"""First data-independent source screening for three SAME-TAXON Movebank archives.

Source files were chosen from 437-package public metadata BEFORE these files'
GPS step/displacement outcomes were opened. Exact source UUID/MD5/size and
no source speed values are read; timing and coordinates are processed ephemerally
to count individual calendar observation opportunity only. No individual IDs,
GPS positions, original timestamps, raw source rows or sensor velocities go
into source receipts.
"""
from __future__ import annotations

import argparse
import csv
import hashlib
import json
from pathlib import Path

from scripts.movebank_native_ecology_20261019 import (
    HERE, original_files, checksum_and_download, inspect_csv,
)

CONTRACT = HERE / "research/MOVEBANK_SAME_TAXON_THREE_SOURCE_PREFLIGHT_20261025.json"
EXPECTED_LABELS = ("wolves_yellowstone","white_tail_florida","elk_southwest_alberta")
SOURCE_COLUMNS_FOR_TAXON = (
    "individual-taxon-canonical-name",
    "taxon-canonical-name",
    "individual_taxon_canonical_name",
    "species"
)


def contract_sources(path: Path=CONTRACT):
    c=json.loads(path.read_text(encoding="utf-8"))
    arr=c["candidate_source_files"]
    if c["id"]!="MOVEBANK_SAME_TAXON_THREE_INDEPENDENT_SOURCE_ROSTER_V0_20261025":
        raise ValueError("HOLD_SOURCE_ONLY_REGISTERED_COHORT_SET_DRIFT")
    if tuple(x["label"] for x in arr)!=EXPECTED_LABELS or len(set(x["data_bitstream"] for x in arr))!=3:
        raise ValueError("HOLD_FROZEN_SOURCE_ORDER_OR_ID_DRIFT")
    return arr


def source_metadata_gate(source: dict, fs: list[dict])->dict:
    target=[x for x in fs if x.get("bitstream_uuid")==source["data_bitstream"]]
    if len(target)!=1:
        raise ValueError("HOLD_ORIGINAL_BITSTREAM_MISSING_NOT_UNIQUE")
    file=target[0]
    ck=file.get("checksum") or {}
    if (ck.get("checkSumAlgorithm","").upper()!="MD5"
        or ck.get("value","").lower()!=source["checksum_md5"].lower()
        or file.get("bytes")!=source["file_bytes"]):
        raise ValueError("HOLD_PROVIDER_MD5_OR_BYTE_COUNT_CHANGED")
    if file.get("name")!=source["filename"]:
        raise ValueError("HOLD_PROVIDER_ORIGINAL_FILENAME_CHANGED")
    return file


def taxonomy_source_only_summary(path:Path, expected_taxon:str)->dict:
    """Inspect the distinct taxonomy values only, never publish row identifiers."""
    with path.open(newline="",encoding="utf-8-sig") as f:
        reader=csv.DictReader(f)
        cols=reader.fieldnames or []
        col=next((x for x in cols if x.casefold().strip() in SOURCE_COLUMNS_FOR_TAXON),None)
        if col is None:
            return {"status":"TAXON_RESTRICTED_BY_ORIGINAL_PACKAGE_METADATA_ONLY",
                    "original_csv_taxon_column_present":False}
        count=0
        off_target=0
        missing=0
        for row in reader:
            value=(row.get(col) or "").strip()
            count+=1
            if not value:missing+=1
            elif value.casefold()!=expected_taxon.casefold():off_target+=1
    return {"status":"ORIGINAL_SOURCE_TAXON_REVIEWED",
            "original_csv_taxon_column_present":True,
            "original_taxon_rows_checked":count,
            "off_target_taxon_rows":off_target,
            "taxon_label_missing_rows":missing}


def source_only_one(source:dict,outdir:Path)->dict:
    rec={
        "label":source["label"],"taxon":source["taxon"],
        "doi":source["doi"],"license":source["license"],
        "source_metadata_reported_animals":source["reported_animals_archive"],
        "source_metadata_reported_GPS_fixes":source["reported_locations_archive"],
        "original_source_MD5_registered":source["checksum_md5"],
        "original_source_file_size_registered":source["file_bytes"],
        "baseline_comparison_cohort":source["baseline_cohort"],
        "status":"HOLD_ORIGINAL_SOURCE_NOT_ADMITTED",
        "original_GPS_steps_or_speed_values_inspected":False,
        "animal_behavior_or_ecological_season_effect_calculated":False,
        "individual_ID_source_coordinates_or_datetimes_exported":False,
    }
    path=outdir/(source["label"]+".csv")
    try:
        items=original_files(source["package_uuid"])
        f=source_metadata_gate(source,items)
        rec["provider_original_file_metadata_matches_frozen_source"]=True
        result=checksum_and_download(f,path)
        rec["original_download_integrity"]=result
        a=inspect_csv(path)
        rec["source_calendar_feasibility"]={
            k:v for k,v in a.items()
            if k in ("status","csv_rows","valid_position_time_individual_rows",
                      "invalid_or_missing_rows","distinct_individuals_with_valid_fixes",
                      "distinct_local_individual_days",
                      "individual_years_with_both_day_and_night_support",
                      "individual_years_ge_5_pairs",
                      "individual_years_ge_10_pairs",
                      "individual_years_ge_20_pairs",
                      "max_conservative_matched_day_pairs")}
        rec["original_taxon_metadata_check"]=taxonomy_source_only_summary(path,source["taxon"])
        if a["status"]!="coverage_evaluated":
            rec["status"]="HOLD_ORIGINAL_TRACKING_SCHEMA_NOT_ADMITTED"
        elif rec["original_taxon_metadata_check"].get("off_target_taxon_rows",0)>0:
            rec["status"]="HOLD_PACKAGE_CONTAINS_MIXED_TARGET_TAXA"
        else:
            rec["status"]="SOURCE_ONLY_CALENDAR_FEASIBILITY_VERIFIED"
        rec["source_only_ge10_animal_years"]=a.get("individual_years_ge_10_pairs",0)
        # Data source has not passed true movement 30–120min and GPS-step
        # balance filters; no source group effect is shown here.
    except Exception as exc:
        rec.update(status="HOLD_ORIGINAL_SOURCE_NOT_ADMITTED",
                   error_type=type(exc).__name__,
                   reason=str(exc)[:220])
    finally:
        path.unlink(missing_ok=True)
    return rec


def main():
    parser=argparse.ArgumentParser()
    parser.add_argument("--output-dir",required=True,type=Path)
    args=parser.parse_args()
    sources=contract_sources()
    args.output_dir.mkdir(parents=True,exist_ok=True)
    data=[]
    for source in sources:
        row=source_only_one(source,args.output_dir)
        data.append(row)
        print("SAME_TAXON_SOURCE_ONLY "+json.dumps(row,sort_keys=True),flush=True)
    output={
        "status":"EXTERNAL_SAME_TAXON_MAMMAL_GPS_SOURCE_ONLY_CALENDAR_AUDIT",
        "source_selection":"FROM_METADATA_BEFORE_NEW_ANIMAL_OUTCOMES",
        "all_original_three_sources_reported":len(data)==3,
        "sources":data,
        "n_original_source_archives_verified":sum(r["status"]=="SOURCE_ONLY_CALENDAR_FEASIBILITY_VERIFIED" for r in data),
        "n_with_any_ge10_source_calendar_year":sum(r.get("source_only_ge10_animal_years",0)>0 for r in data),
        "source_GPS_movement_outcomes_evaluated":False,
        "independent_source_licenses":{r["label"]:r["license"] for r in data},
        "no_cross_region_animal_response_or_causal_claim":True
    }
    (args.output_dir/"original_same_taxon_three_source_feasibility_20261025.json").write_text(
        json.dumps(output,sort_keys=True,indent=2)+"\n",encoding="utf-8")
    print("SAME_TAXON_SOURCE_ONLY_FINAL "+json.dumps({
        "verified_archives":output["n_original_source_archives_verified"],
        "candidate_archives_with_source_calendar_support":output["n_with_any_ge10_source_calendar_year"],
        "no_movement_outcomes":True,
        "sources":[{"label":r["label"],"status":r["status"],
                    "source_years_ge_10":r.get("source_only_ge10_animal_years"),
                    "original_file_integrity":r.get("original_download_integrity",{}).get("provider_checksum_verified")}
                   for r in data]},sort_keys=True))


if __name__=="__main__":
    main()
