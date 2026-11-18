#!/usr/bin/env python3
"""Offline first German GPS stage-attrition receipt verification."""
from __future__ import annotations
import argparse
import hashlib
import json
from pathlib import Path

ROOT=Path(__file__).resolve().parents[1]
RECEIPT=ROOT/"BOP_RED_KITE_GER_GPS_STAGE_ATTRITION_V1_FIRST_RECEIPT.json"
CONTRACT=ROOT/"research/BOP_RED_KITE_GER_GPS_STAGE_ATTRITION_V1_CONTRACT.json"

def verify(receipt:dict,contract:dict,*,raw:bytes|None=None):
    first=receipt["first_official"]
    obs=receipt["observed_first"]
    bounds=receipt["scientific_limits"]
    stages=[
        ["S0_all_GER_metadata_seasons",159,63,0,0],
        ["S1_any_valid_GPS_event_matching_exact_year_bird_pair",159,63,0,0],
        ["S2_at_least_one_GPS_event_lat_gt_50_lon_gt_9",159,63,0,0],
        ["S3_at_least_one_GPS_event_UTC_ordinal_DOY_74_through_191",159,63,0,0],
        ["S4_gt_800_valid_GPS_event_rows_after_S3",99,49,60,14],
    ]
    if (
        receipt.get("receipt_id")!="bop-redkite-GER-five-stage-eligibility-first-v1"
        or receipt.get("pre_result_frozen_contract_commit")!="fbb244938950fe5c3c0fdfc73c24429c0c44e087"
        or first["run_id"]!=44260229713
        or first["source_job_id"]!=134651672448
        or first["artifact_id"]!=14407028545
        or first["head_sha"]!="dde578585213574f61c463b172705199ccc38c98"
        or first["zip_sha256"]!="3e5699905f1eb82a2eaf24c8c5e6c1b6acac261c1892fd7dc20cefc53df69841"
        or first["json_sha256"]!="2acd0ea576398b0de7a9181b2943679adc9c7e802aa011556c8ed996d2920539"
        or first["json_bytes"]!=2203
        or first["frozen_contract_sha256"]!="372cabae75a4eec2dbacc80148e1cabfca95aacfd1177bc676b437ee128aa957"
        or hashlib.sha256(CONTRACT.read_bytes()).hexdigest()!=first["frozen_contract_sha256"]
        or first["source_status"]!="success"
        or first["python_test_versions"]!=["3.10","3.12","3.13"]
        or contract["contract_id"]!="bop-redkite-german-gps-fixed-stage-attrition-v1"
    ):
        raise ValueError("first stage-source contract, workflow or artifact fingerprint drifted")
    if (
        obs["stages"]!=stages
        or obs["stage_columns"]!=["stage","seasons","bird_ID_strings","seasons_lost","bird_ID_strings_lost"]
        or obs["raw_provider_GPS_lines"]!=500778
        or obs["missing_or_invalid"]!=1
        or obs["unlinked_year_id_rows"]!=2524
        or obs["metadata_year_bird_mismatch_rows"]!=0
        or obs["valid_linked_event_rows"]!=498253
        or obs["missing_or_invalid"]+obs["unlinked_year_id_rows"]+obs["metadata_year_bird_mismatch_rows"]+obs["valid_linked_event_rows"]!=obs["raw_provider_GPS_lines"]
        or obs["full_provider_MD5s_verified"] is not True
        or obs["first_GPS_99_49_reconfirmed"] is not True
    ):
        raise ValueError("frozen five-stage GPS attrition or provider counts changed")
    if (
        not bounds["published_163_65_raw_not_reproduced"]
        or not bounds["published_99_63_eligible_not_reproduced"]
        or not bounds["exact_cause_of_publication_sample_count_mismatch_unresolved"]
        or not bounds["stage_loss_60_seasons_14_birds_reproducible_under_declared_filter"]
        or not bounds["no_raw_or_hashed_bird_year_ID_exported"]
        or not bounds["no_gps_positions_timestamps_exported"]
        or not bounds["no_nest_HR_success_values_accessed"]
        or not bounds["no_real_prediction_gain"]
        or bounds["biological_terminal"]!="HOLD_NO_FROZEN_NEW_NEST_STATE_MODEL_OR_IDENTITY_ROSTER"
        or bounds["original_BOP_terminal"]!="empirical_state_prediction_mixed"
    ):
        raise ValueError("reproduced dataset mismatch promoted to new biological inference")
    if raw is not None:
        if len(raw)!=first["json_bytes"] or hashlib.sha256(raw).hexdigest()!=first["json_sha256"]:
            raise ValueError("real new source funnel is not byte-identical to the first official result")
        p=json.loads(raw)
        actual=[
            [z["stage"],z["season_ID_strings"],z["bird_ID_strings"],
             z["seasons_lost_from_previous_stage"],z["birds_lost_from_previous_stage"]]
            for z in p["result"]["source_stage_funnel"]
        ]
        if (
            actual!=stages
            or p["status"]!="SOURCE_ONLY_GER_GPS_STAGE_ATTRITION_RECORDED"
            or p["provider_full_GPS_and_metadata_MD5_verified"] is not True
            or p["breeding_labels_accessed_or_parsed"] is not False
            or p["bird_or_year_ID_strings_logged"] is not False
            or p["GPS_exact_positions_or_times_logged"] is not False
            or p["original_99_season_63_bird_publication_reconciled"] is not False
        ):
            raise ValueError("source result content or scientific ceiling changed")
    return {
        "original_source_five_stages_verified":True,
        "raw_seasons":159,"raw_bird_strings":63,
        "pre_800fix_seasons":159,"pre_800fix_birds":63,
        "eligible_seasons":99,"eligible_birds":49,
        "seasons_lost_at_fix_threshold":60,"birds_lost_at_fix_threshold":14,
        "paper_99_63_reconciled":False,
        "biology_terminal":"HOLD_NO_FROZEN_NEW_NEST_STATE_MODEL_OR_IDENTITY_ROSTER",
    }


def main():
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument("--result",type=Path)
    a=p.parse_args()
    receipt=json.loads(RECEIPT.read_text(encoding="utf-8"))
    contract=json.loads(CONTRACT.read_text(encoding="utf-8"))
    raw=a.result.read_bytes() if a.result else None
    print(json.dumps(verify(receipt,contract,raw=raw),sort_keys=True))

if __name__=="__main__":
    main()
