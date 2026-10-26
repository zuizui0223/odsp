#!/usr/bin/env python3
"""Fail-closed replay of Dryad source-only preflight; never reads biological GPS.

Byte-identity of the first GitHub Actions ZIP and original JSON is pinned
separately from the intentionally reserialized deidentified GitHub copy.
Actual score, altitude and animal source rows remain unopened.
"""
from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path

ROOT=Path(__file__).resolve().parents[1]
CONTRACT=ROOT/"research/BOP_DRYAD_EXTERNAL_SCHEMA_PREFLIGHT_V1_CONTRACT.json"
FIRST=ROOT/"research/BOP_DRYAD_EXTERNAL_SCHEMA_PREFLIGHT_V1_FIRST_RESULT.json"
RECEIPT=ROOT/"BOP_DRYAD_EXTERNAL_SCHEMA_PREFLIGHT_V1_TERMINAL_RECEIPT.json"


def _sha(raw:bytes)->str:
    return hashlib.sha256(raw).hexdigest()


def _git_blob_sha(raw:bytes)->str:
    return hashlib.sha1(
        b"blob "+str(len(raw)).encode("ascii")+b"\0"+raw
    ).hexdigest()


def _first_difference(a,b,path="$")->str|None:
    if type(a)!=type(b):
        return path+" (type)"
    if isinstance(a,dict):
        if set(a)!=set(b):
            return path+" (keys)"
        for k in sorted(a):
            found=_first_difference(a[k],b[k],path+"."+k)
            if found is not None:return found
    elif isinstance(a,list):
        if len(a)!=len(b):return path+" (length)"
        for i,(x,y) in enumerate(zip(a,b)):
            found=_first_difference(x,y,path+"["+str(i)+"]")
            if found is not None:return found
    elif a!=b:
        return path+" (value)"
    return None


def validate_dryad_first_result(result:dict,receipt:dict,
                               contract_bytes:bytes,first_bytes:bytes)->dict:
    frozen=receipt["frozen_contract"]
    evidence=receipt["first_official_execution"]
    source=receipt["positive_source_result"]
    compat=receipt["original_model_compatibility"]
    terminal=receipt["terminal"]
    if _sha(contract_bytes)!=frozen["contract_sha256"]:
        raise ValueError("pre-source Dryad scientific contract drifted")
    if _git_blob_sha(first_bytes)!=evidence["github_canonical_semantic_copy_git_blob_sha1"]:
        raise ValueError("original first-result semantic-copy bytes drifted")
    if (
        receipt["scientific_role"]!="outcome_blind_external_source_metadata_and_original_RF_schema_gate"
        or evidence["workflow_run_id"]!=40275944700
        or evidence["workflow_job_id"]!=121418698626
        or evidence["artifact_id"]!=12630760184
        or evidence["artifact_zip_sha256"]!="ddc23a16ea20e51e1c630cdc45b2466af0e421e0745aa282b7bb5331283922cd"
        or evidence["artifact_raw_result_json_sha256"]!="10181566debf005c51d5a28f6d058a9134fddca33580621d1d9a2ce40b32669e"
        or evidence["byte_level_difference_disclosed"] is not True
    ):
        raise ValueError("first official source-evidence identity changed")
    difference=_first_difference(result,json.loads(first_bytes))
    if difference is not None:
        raise ValueError("official Dryad metadata-only replay differs at "+difference)
    if (
        result.get("contract_id")!="bop-dryad-2026-external-schema-and-source-preflight-v1"
        or result.get("contract_sha256")!=frozen["contract_sha256"]
        or result.get("dataset_doi")!="10.5061/dryad.n8pk0p398"
        or result.get("candidate_admission")!="NOT_ADMITTED"
        or result.get("raw_gps_or_height_outcomes_accessed") is not False
        or result.get("BOP_existing_mixed_terminal_reclassified") is not False
        or result.get("BOP_2026_same_study_count_gate_reopened") is not False
        or terminal["candidate"]!="NOT_ADMITTED"
        or terminal["historical_BOP_terminal"]!="empirical_state_prediction_mixed"
    ):
        raise ValueError("original BOP or new Dryad terminal reclassified")
    if (
        result["metadata_source_status"]!="AT_LEAST_ONE_OFFICIAL_SOURCE_READ"
        or result["official_metadata_api"]["dataset"]["status"]!=source["official_dataset_metadata_api_status"]
        or result["official_metadata_api"]["versions"]["status"]!=source["official_version_metadata_api_status"]
        or result["official_metadata_api"]["dataset"]["sha256"]!=source["metadata_document_sha256"]
        or result["official_metadata_api"]["versions"]["sha256"]!=source["versions_metadata_sha256"]
        or result["official_metadata_api"]["dataset"]["explicit_provider_license"]!=source["provider_explicit_license_url"]
    ):
        raise ValueError("source API or license changed since first run")
    if any(
        entry["status"]!="SOURCE_HOLD"
        or entry["error_code"]!="HTTP_403"
        for entry in result["small_non_gps_file_checks"].values()
    ) or len(result["small_non_gps_file_checks"])!=3:
        raise ValueError("source file availability changed since first run")
    model=result["feature_compatibility"]
    if (
        model["original_bop_rf_direct_external_scoring_admissible"] is not False
        or model["documented_missing_required_features"]!=["external-temperature"]
        or model["precision_changed_features"]!=["location-lat","location-long"]
        or result["original_BOP_RF_direct_external_transfer_status"]!=compat["direct_external_predictor_reuse"]
        or result["documented_species_total"]!=280
        or result["documented_data_1a_individuals"]!=271
        or result["documented_common_BOP_taxa_total"]!=217
        or result["individual_cross_study_identity_overlap_status"]!="UNKNOWN_NOT_EVALUABLE_WITH_PUBLISHED_COUNTS"
    ):
        raise ValueError("original BOP feature and external-source claim ceiling bypassed")
    return {
        "validated":True,
        "candidate":"NOT_ADMITTED",
        "original_RF":"ORIGINAL_RF_PREDICTOR_INCOMPATIBLE",
        "provider_license":"CC0-1.0",
        "public_api_retrieved":True,
        "three_small_files":"HTTP_403_SOURCE_HOLD",
        "GPS_or_BOP_outcome_data_accessed":False,
        "historical_BOP_terminal_changed":False,
    }


def main()->None:
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--result",type=Path,default=FIRST)
    args=parser.parse_args()
    output=validate_dryad_first_result(
        json.loads(args.result.read_text(encoding="utf-8")),
        json.loads(RECEIPT.read_text(encoding="utf-8")),
        CONTRACT.read_bytes(),FIRST.read_bytes(),
    )
    print(json.dumps(output,sort_keys=True))


if __name__=="__main__":
    main()
