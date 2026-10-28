#!/usr/bin/env python3
"""Recheck official first header-only Zenodo CSV result without opening rows."""
from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path

ROOT=Path(__file__).resolve().parents[1]
CONTRACT=ROOT/"research/BOP_RED_KITE_HEADER_ONLY_V1_CONTRACT.json"
RECEIPT=ROOT/"BOP_RED_KITE_HEADER_ONLY_V1_FIRST_RECEIPT.json"


def verify_first_header_only(obj:dict,receipt:dict,contract:dict,*,raw:bytes|None=None)->dict:
    first=receipt["first_actions"]
    source=receipt["source_contract"]
    observed=receipt["verified_first_header"]
    keys=[
        "GER_indseasondata","SUI_indseasondata",
        "GER_trackingdata","SUI_trackingdata"
    ]
    if (
        receipt["receipt_id"]!="bop-red-kite-official-four-headers-only-first-v1"
        or source["preaccess_freeze_commit"]!="81cb2bc6816a4622d4d97a8328f4c967d04ec792"
        or first["run_id"]!=40637728704
        or first["artifact_id"]!=12793992320
        or first["original_zip_sha256"]!="16fc6c53011c1a0aa7062ee979881ea9fa1e47868341749709bc6521aa165985"
        or contract["contract_id"]!=obj.get("contract_id")
        or obj.get("contract_sha256")!="eaa06e023efb403ed215a579ce4c0664ddaa447a01791886566bc3590121af3d"
        or hashlib.sha256(CONTRACT.read_bytes()).hexdigest()!=obj["contract_sha256"]
        or [x["key"] for x in contract["authorized_header_requests"]]!=[observed[k]["filename"] for k in keys]
    ):
        raise ValueError("original pre-access header provider evidence drifted")
    if raw is not None and (
        hashlib.sha256(raw).hexdigest()!=first["original_header_JSON_sha256"]
        or len(raw)!=first["original_header_JSON_bytes"]
    ):
        raise ValueError("new source header JSON is not identical to first archived source output")
    fields=obj.get("header_fields")
    if not isinstance(fields,list) or len(fields)!=4:
        raise ValueError("exact four first-line file headers required")
    if (
        obj.get("source_role")!="OBSERVED_CSV_HEADERS_ONLY_NO_RESPONSES"
        or obj.get("structural_header_status")!="SOURCE_HEADERS_RECORDED_NO_FULL_DATA_ACCESS"
        or obj.get("scientific_terminal")!="HOLD_NO_FROZEN_NEW_NEST_STATE_MODEL_OR_IDENTITY_ROSTER"
        or obj.get("all_four_sources_have_year_id") is not True
        or obj.get("individual_season_headers_have_candidate_animal_key") is not True
        or obj.get("per_animal_source_counts_verified") is not False
        or obj.get("outcome_values_parsed") is not False
        or obj.get("GPS_event_values_parsed") is not False
        or obj.get("source_file_content_MD5_verified") is not False
        or obj.get("published_German_bird_count_63_admitted") is not False
        or obj.get("real_external_probability_gain_scored") is not False
        or obj.get("original_BOP_terminal")!="empirical_state_prediction_mixed"
    ):
        raise ValueError("source-only columns were promoted into biological outcome inference")
    original=receipt["critical_limits"]
    if not (
        original["no_individual_year_values_parsed"]
        and original["no_GPS_event_values_parsed"]
        and not original["real_individual_ID_keys_compared"]
        and not original["source_biological_sample_count_verified"]
        and not original["nest_model_frozen"]
        and not original["real_group_prediction_scored"]
    ):
        raise ValueError("original biological nonaccess statement changed")
    for key,field in zip(keys,fields):
        first_header=observed[key]
        column_names=first_header["column_names"]
        # Official source uses CRLF: exact header hash reconstructed from column
        # names, never needing actual response rows.
        raw_line=(",".join(column_names)+"\r\n").encode("utf-8")
        if (
            field.get("file")!=first_header["filename"]
            or field.get("columns")!=column_names
            or field.get("header_bytes_only")!=first_header["header_byte_length"]
            or first_header["header_byte_length"]!=len(raw_line)
            or field.get("header_sha256")!=first_header["header_sha256"]
            or hashlib.sha256(raw_line).hexdigest()!=first_header["header_sha256"]
            or field.get("HTTP_status")!=206
            or field.get("GPS_or_breeding_outcome_row_parsed") is not False
            or field.get("source_full_content_MD5_verified") is not False
        ):
            raise ValueError("one first-line schema differs from frozen official provider response")
    return {
        "original_first_header_schema_confirmed":True,
        "first_actions_run":first["run_id"],
        "source_headers":4,
        "German_individual_key":"bird_id",
        "Swiss_individual_key":"bird_id",
        "season_join_key":"year_id",
        "nesting_outcome_header_present_both":True,
        "source_temperature_predictor_common":False,
        "real_biological_rows_scored":False,
        "original_BOP_terminal_preserved":True,
        "biological_result":"HOLD_NO_FROZEN_NEW_NEST_STATE_MODEL_OR_IDENTITY_ROSTER",
    }


def main()->None:
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument("--result",required=True,type=Path)
    a=p.parse_args()
    raw=a.result.read_bytes()
    ans=verify_first_header_only(
        json.loads(raw),
        json.loads(RECEIPT.read_text(encoding="utf-8")),
        json.loads(CONTRACT.read_text(encoding="utf-8")),
        raw=raw,
    )
    print(json.dumps(ans,sort_keys=True))


if __name__=="__main__":
    main()
