#!/usr/bin/env python3
"""Fail-closed replay of FIRST published Zenodo red-kite metadata-only result.

Never reads any outcome/animal/GPS files. Distinguish provider MANIFEST
identity from checksums of actually DOWNLOADED data (not examined here).
"""
from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path
from typing import Mapping

ROOT=Path(__file__).resolve().parents[1]
CONTRACT=ROOT/"research/BOP_RED_KITE_SOURCE_INVENTORY_V1_CONTRACT.json"
RECEIPT=ROOT/"BOP_RED_KITE_SOURCE_INVENTORY_V1_FIRST_RECEIPT.json"
_SHA256ZIP="109fe897235724db921f0c1cdcbbec7c2f504dc501e0e4dc2126a92dc62bd966"


def _sha(raw:bytes)->str:
    return hashlib.sha256(raw).hexdigest()


def verify_first_source_only(
    obj:Mapping, receipt:Mapping, contract:Mapping, *,
    raw_result:bytes|None=None,
)->dict[str,object]:
    p=receipt["source_contract"]
    first=receipt["initial_verified_actions"]
    manifest=receipt["source_manifest_observation"]
    sci=receipt["scientific_terminal"]
    if (
        receipt.get("receipt_id")!="bop-red-kite-zenodo-source-metadata-first-success-v1"
        or receipt.get("role")!="OFFICIAL_ZENODO_METADATA_ONLY_NOT_CSV_CONTENT_NOT_EXTERNAL_PREDICTIVE_INFERENCE"
        or p["original_frozen_commit"]!="8f12d441ab2ee1cb826838a7a65fc52df6d88a12"
        or p["original_source_allowed"]!="https://zenodo.org/api/records/13736049"
        or contract.get("target_source",{}).get("allowed_metadata_api")!=p["original_source_allowed"]
        or contract.get("criteria",{}).get("biology_terminal_always")!=sci["biological"]
        or first["workflow_run_id"]!=40636304599
        or first["workflow_artifact_id"]!=12792739938
        or first["original_zip_sha256"]!=_SHA256ZIP
    ):
        raise ValueError("first official metadata archive or frozen contract identity changed")
    if raw_result is not None and (
        len(raw_result)!=first["first_result_bytes"]
        or _sha(raw_result)!=first["first_result_sha256"]
    ):
        raise ValueError("original first Actions JSON changed or metadata drifted")
    if (
        obj.get("source_doi")!=manifest["source_doi"]
        or obj.get("record_id")!=manifest["source_record_id"]
        or obj.get("published") is not True
        or obj.get("provider_license_id")!=manifest["provider_license_id"]
        or obj.get("metadata_version")!=manifest["manifest_version_string"]
        or obj.get("metadata_sha256")!=first["raw_official_metadata_sha256"]
        or obj.get("file_count")!=manifest["source_file_count"]
        or obj.get("total_provider_file_bytes")!=manifest["total_manifest_bytes"]
        or obj.get("official_file_inventory_verified") is not True
        or obj.get("source_inventory_terminal")!=sci["inventory"]
        or obj.get("biology_terminal")!=sci["biological"]
        or obj.get("outcome_rows_accessed") is not False
        or obj.get("real_external_group_gain_estimated") is not False
        or obj.get("German_sample_roster_opened") is not False
        or obj.get("original_BOP_RF_altitude_validation") is not False
        or obj.get("published_sample_count_not_validated_against_files") is not True
        or obj.get("historical_BOP_mixed_preserved") is not True
        or obj.get("old_Dryad_original_RF_gate_reopened") is not False
        or obj.get("read_actions")!=["EXACT_PUBLIC_ZENODO_METADATA_API_ONLY"]
    ):
        raise ValueError("metadata-only manifest promoted to unsupported biological inference")
    actual=obj.get("declared_file_list")
    if not isinstance(actual,list) or len(actual)!=6:
        raise ValueError("six pinned source files are required")
    source_by_name={f["key"]:f for f in contract["expected_files"]}
    expected=manifest["manifest"]
    if set(source_by_name)!={x["key"] for x in expected}:
        raise ValueError("file list changed since preaccess source contract")
    if {f["key"] for f in actual}!={f["key"] for f in expected}:
        raise ValueError("source file manifest name mismatch")
    actual_by_key={f["key"]:f for f in actual}
    if len(actual_by_key)!=len(actual):
        raise ValueError("duplicate source file manifest entry")
    for entry in expected:
        key=entry["key"]
        row=actual_by_key[key]
        if (
            set(row)!={"key","manifest_md5","provider_size_bytes","role","file_bytes_downloaded"}
            or row["manifest_md5"]!=entry["md5"]
            or row["manifest_md5"]!=source_by_name[key]["md5"]
            or row["provider_size_bytes"]!=entry["bytes"]
            or row["role"]!=source_by_name[key]["role"]
            or row["file_bytes_downloaded"] is not False
        ):
            raise ValueError("provider source file MD5, size or no-download role changed")
    if (
        sci["no_breeding_success_outcomes_accessed"] is not True
        or sci["no_tracking_CSVs_or_GPS_accessed"] is not True
        or sci["new_group_gain_calibration_performed"] is not False
        or sci["historical_BOP"]!="empirical_state_prediction_mixed"
    ):
        raise ValueError("original BOP or no-access scientific boundary changed")
    return {
        "schema_version":1,
        "first_metadata_result_verified":True,
        "original_workflow":first["workflow_run_id"],
        "original_artifact_zip_sha256":first["original_zip_sha256"],
        "pinned_manifest_files":6,
        "license":manifest["provider_license_id"],
        "source_inventory_status":"SOURCE_FILE_INVENTORY_VERIFIED_ONLY",
        "nest_state_biology_status":sci["biological"],
        "original_BOP_unchanged":True,
        "data_files_or_GPS_accessed":False,
        "new_empirical_prediction_scored":False,
    }


def main()->None:
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--result",type=Path,required=True)
    args=parser.parse_args()
    raw=args.result.read_bytes()
    status=verify_first_source_only(
        json.loads(raw),
        json.loads(RECEIPT.read_text(encoding="utf-8")),
        json.loads(CONTRACT.read_text(encoding="utf-8")),
        raw_result=raw,
    )
    print(json.dumps(status,sort_keys=True))


if __name__=="__main__":
    main()
