#!/usr/bin/env python3
"""Verify the first official source-only red-kite animal-year aggregate receipt.

No network and no source CSV read. Reconstruct original stored JSON to bind
the exact Actions artifact hash to documented count-only observations.
"""
from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path

ROOT=Path(__file__).resolve().parents[1]
RECEIPT=ROOT/"BOP_RED_KITE_RAW_GROUP_PREFIX_ONLY_V1_FIRST_RECEIPT.json"
CONTRACT=ROOT/"research/BOP_RED_KITE_RAW_GROUP_PREFIX_ONLY_V1_CONTRACT.json"
INVENTORY=ROOT/"BOP_RED_KITE_SOURCE_INVENTORY_V1_FIRST_RECEIPT.json"

def verify_first(receipt:dict,contract:dict,*,result:dict|None=None,raw:bytes|None=None)->dict:
    original=receipt["original_source_output"]
    run=receipt["first_actions"]
    biology=receipt["source_biology_limits"]
    if (receipt.get("receipt_id")!="bop-redkite-official-key-prefix-only-first-v1"
        or receipt.get("first_freeze_contract_commit")!="99f32569bf7b8ee17056f1b9a4c7c90dd82e1694"
        or run["workflow_run_id"]!=44257226379
        or run["source_job_id"]!=134641896994
        or run["first_source_artifact_id"]!=14406462430
        or run["source_run_head_sha"]!="3a9feb059d865e29aac4e20a543e4dd443c37b0a"
        or run["original_artifact_zip_sha256"]!="bf5b9b1bdf29acbbdfcd3ab17709c11a4307df6b7146fba5b0d8705c22e6d9da"
        or run["original_source_json_sha256"]!="efc41dacf264777d06343a283fc620a6575d2879874e1530ed00f749840e3e1e"
        or run["original_source_json_bytes"]!=2161
        or run["test_matrix_python"]!=["3.10","3.12","3.13"]
        or run["source_job_conclusion"]!="success"
        or hashlib.sha256(CONTRACT.read_bytes()).hexdigest()!=original["preaccess_contract_sha256"]
        or original["preaccess_contract_sha256"]!="468f74f1118fda786d6bbcca5acfa77a323a30a97f56bd9befafe8731617d6e1"
        or contract["contract_id"]!="bop-redkite-declared-source-key-prefix-projection-v1"
    ):
        raise ValueError("first provenance freeze/Actions artifact/contract identity drifted")

    first_raw=(json.dumps(original,indent=2,sort_keys=True,allow_nan=False)+"\n").encode("utf-8")
    if (len(first_raw)!=2161
        or hashlib.sha256(first_raw).hexdigest()!=run["original_source_json_sha256"]):
        raise ValueError("published aggregate-only output does not reproduce initial source JSON digest")
    if result is not None and result!=original:
        raise ValueError("rerun source-only output is not identical to the first verified source aggregate")
    if raw is not None and hashlib.sha256(raw).hexdigest()!=run["original_source_json_sha256"]:
        raise ValueError("rerun source-only JSON bytes differ from original official artifact")

    observed=original["sources"]
    expected=[
        ("GER_indseasondata.csv",159,63,46,7,{"1":17,"2":23,"3":7,"4":10,"5":3,"6":1,"7":2},6456),
        ("SUI_indseasondata.csv",2866,553,515,7,{"1":38,"2":46,"3":51,"4":20,"5":63,"6":157,"7":178},117327),
    ]
    if len(observed)!=2:
        raise ValueError("not exactly two source biological metadata files")
    for obj,(name,lines,birds,multi,max_n,hist,nbytes) in zip(observed,expected):
        if (
            obj["source"]!=name or obj["physical_record_lines"]!=lines
            or obj["distinct_bird_ID_strings"]!=birds
            or obj["distinct_year_ID_strings"]!=lines
            or obj["number_of_birds_with_multiple_season_records"]!=multi
            or obj["max_season_records_per_bird"]!=max_n
            or obj["season_records_per_bird_histogram"]!=hist
            or sum(int(k)*v for k,v in hist.items())!=lines
            or sum(hist.values())!=birds
            or obj["duplicate_year_ID_lines"]!=0
            or obj["year_ID_to_multiple_bird_IDs"]!=0
            or obj["source_full_file_md5_verified"] is not True
            or obj["source_bytes"]!=nbytes
        ):
            raise ValueError("source metadata animal/year counts or MD5 limits drifted")
    if (
        original["source_pair_bird_ID_exact_string_overlap"]!=0
        or original["source_pair_year_ID_exact_string_overlap"]!=0
        or original["source_pair_lexical_overlap_not_canonical_identity_proof"] is not True
        or original["GER_GPS_800fix_season_filter_reproduced"] is not False
        or original["animal_identity_crosswalk_authenticated"] is not False
        or original["source_populations_verified_from_source"] is not False
        or original["breeding_response_suffix_values_parsed"] is not False
        or original["GPS_events_opened"] is not False
        or original["real_model_probabilities_scored"] is not False
        or original["status"]!="SOURCE_RAW_YEAR_ID_GROUP_COUNTS_ONLY"
        or original["biological_terminal"]!="HOLD_NO_FROZEN_NEW_NEST_STATE_MODEL_OR_IDENTITY_ROSTER"
        or original["original_BOP_empirical_terminal"]!="empirical_state_prediction_mixed"
        or original["original_BOP_Dryad"]!="NOT_ADMITTED"
        or biology["unfiltered_GER_metadata_birds"]!=63
        or biology["unfiltered_GER_metadata_seasons"]!=159
        or biology["unfiltered_SUI_metadata_birds"]!=553
        or biology["unfiltered_SUI_metadata_seasons"]!=2866
        or not biology["published_initial_GER_65_birds_163_seasons_not_reconstructed"]
        or not biology["published_GER_eligible_63_birds_99_seasons_not_reconstructed"]
        or not biology["published_SUI_eligible_258_birds_697_seasons_not_reconstructed"]
        or not biology["source_CSV_MD5_both_match"]
        or not biology["no_breeding_labels_parsed"]
        or not biology["no_GPS_accessed"]
        or not biology["no_future_animal_gain_scored"]
    ):
        raise ValueError("source-only results reinterpreted as biological model gains or eligible GPS sample")
    return {
        "official_source_aggregate_reproduced":True,
        "first_run_id":run["workflow_run_id"],
        "official_artifact_id":run["first_source_artifact_id"],
        "GER_raw_metadata_seasons":159,
        "GER_raw_metadata_birds":63,
        "SUI_raw_metadata_seasons":2866,
        "SUI_raw_metadata_birds":553,
        "GPS_eligibility_reproduced":False,
        "nesting_outcomes_opened":False,
        "biological_result":original["biological_terminal"],
    }


def main():
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument("--result",type=Path)
    a=p.parse_args()
    receipt=json.loads(RECEIPT.read_text(encoding="utf-8"))
    contract=json.loads(CONTRACT.read_text(encoding="utf-8"))
    if a.result:
        raw=a.result.read_bytes()
        outcome=verify_first(receipt,contract,result=json.loads(raw),raw=raw)
    else:
        outcome=verify_first(receipt,contract)
    print(json.dumps(outcome,sort_keys=True))

if __name__=="__main__":
    main()
