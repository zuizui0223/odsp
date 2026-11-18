#!/usr/bin/env python3
"""Recheck original German GPS 12-arm eligibility receipt and exact rerun bytes.

No source network access. The canonical first Actions ZIP/JSON digests were
saved before writing this verifier. Never output bird/year IDs or coordinates.
"""
from __future__ import annotations
import argparse
import hashlib
import json
from pathlib import Path

ROOT=Path(__file__).resolve().parents[1]
RECEIPT=ROOT/"BOP_RED_KITE_GER_GPS_ELIGIBILITY_V1_FIRST_RECEIPT.json"
CONTRACT=ROOT/"research/BOP_RED_KITE_GER_GPS_ELIGIBILITY_V1_CONTRACT.json"

def verify(receipt:dict,contract:dict,*,raw:bytes|None=None)->dict:
    first=receipt["first_actions"]
    obs=receipt["observed_source"]
    limits=receipt["claim_ceiling"]
    expected_head="ada575be835269d7300ecaa8b7582bf06fcb05db"
    expected_zip="c9aa95cf66a0f6c24200d8de4555abe5d9164b844be43bf9685b678ac73d953a"
    expected_json="ecc07e3e522c4687745b184e9304d319fba72baad659b99ff218acd9e10761b2"
    expected_contract="a00822d4e62c0dd9af449b6f656ae9e3e3deb7d865e6945629cdaeefa3eca5b0"
    if (
        receipt["receipt_id"]!="bop-redkite-german-original-gps-eligibility-first-v1"
        or receipt["first_contract_commit_before_GPS"]!="6520f133694a78991f0fcc28c323b3d98a3f31d3"
        or first["run_id"]!=44258858756
        or first["official_source_job_id"]!=134647223699
        or first["original_branch_head"]!=expected_head
        or first["artifact_id"]!=14407162400
        or first["artifact_zip_sha256"]!=expected_zip
        or first["original_json_sha256"]!=expected_json
        or first["original_json_bytes"]!=5143
        or first["frozen_contract_sha256"]!=expected_contract
        or hashlib.sha256(CONTRACT.read_bytes()).hexdigest()!=expected_contract
        or first["official_source_conclusion"]!="success"
        or first["synthetic_python_versions_success"]!=["3.10","3.12","3.13"]
        or contract["contract_id"]!="bop-redkite-german-gps-eligibility-12-fixed-rules-v1"
    ):
        raise ValueError("original GPS/Actions contract or artifact provenance drifted")
    if raw is not None and (
        len(raw)!=first["original_json_bytes"]
        or hashlib.sha256(raw).hexdigest()!=first["original_json_sha256"]
    ):
        raise ValueError("latest source result is not byte-identical to first real GPS result")

    fixed_names=[
        f"{date}__{thin}__{minimum}"
        for date in ("fixed_2023_DOY_ordinal","actual_calendar_month_day")
        for thin in ("observed_source_events","unique_utc_hour_bin","rolling_3600_seconds")
        for minimum in ("strict_gt_800","inclusive_ge_800")
    ]
    rows=obs["all_12_fixed_arms"]
    if (
        [x[0] for x in rows]!=fixed_names
        or len(rows)!=12
        or any(len(row)!=3 for row in rows)
        or [tuple(x[1:]) for x in rows]!=[(99,49)]*2+[(90,46)]*2+[(83,44)]*2+[(99,49)]*2+[(90,46)]*2+[(83,44)]*2
        or obs["arm_columns"]!=["name","eligible_seasons","distinct_bird_ID_strings"]
        or obs["GPS_physical_record_lines"]!=500778
        or obs["malformed_or_missing_fields"]!=1
        or obs["GPS_matched_metadata_lines"]!=498253
        or obs["GPS_unlinked_metadata_lines"]!=2524
        or obs["GPS_matched_metadata_lines"]+obs["GPS_unlinked_metadata_lines"]+obs["malformed_or_missing_fields"]!=obs["GPS_physical_record_lines"]
        or obs["linked_GPS_geo_bounds_rejected_lines"]!=79051
        or obs["ordinal_GPS_season_lines"]!=236989
        or obs["calendar_GPS_season_lines"]!=237254
        or obs["GPS_year_ID_multiple_bird_strings"]!=0
        or obs["GPS_original_Zenodo_md5_verified"] is not True
        or obs["GER_metadata_original_Zenodo_md5_verified"] is not True
        or obs["GER_original_metadata_seasons"]!=159
        or obs["GER_original_metadata_birds"]!=63
    ):
        raise ValueError("12-arm eligibility or source integrity count was changed")
    if (
        not limits["published_GER_original_163_65_not_reproduced"]
        or not limits["published_GER_eligible_99_63_not_reproduced"]
        or not limits["some_99_season_arithmetic_matches_but_49_not_63_birds"]
        or limits["all_12_arms_nominal_match_both_99_and_63"] is not False
        or limits["no_breeding_labels_accessed"] is not True
        or limits["no_location_or_event_time_values_persisted"] is not True
        or limits["no_new_model_probabilities_scored"] is not True
        or limits["biological_terminal"]!="HOLD_NO_FROZEN_NEW_NEST_STATE_MODEL_OR_IDENTITY_ROSTER"
        or limits["original_BOP_terminal"]!="empirical_state_prediction_mixed"
        or limits["original_Dryad"]!="NOT_ADMITTED"
    ):
        raise ValueError("posthoc source counts were promoted to biological prediction")
    if raw is not None:
        p=json.loads(raw)
        if (
            p.get("status")!="GPS_SOURCE_ELIGIBILITY_SENSITIVITY_ONLY"
            or p.get("preaccess_contract_sha256")!=expected_contract
            or p.get("GPS",{}).get("raw_GPS_physical_record_lines")!=obs["GPS_physical_record_lines"]
            or [(r["arm"],r["eligible_seasons"],r["distinct_bird_ID_strings_in_eligible_seasons"])
                for r in p["GPS"]["all_12_prespecified_eligibility_arms"]]!=[tuple(x) for x in rows]
            or p.get("reproductive_labels_accessed_or_parsed") is not False
            or p.get("GPS_positions_or_exact_times_emitted") is not False
            or p.get("original_BOP_empirical_terminal")!="empirical_state_prediction_mixed"
        ):
            raise ValueError("GPS result content not aligned to biological claim ceiling")
    return {
        "original_source_12arm_aggregate_rechecked":True,
        "official_first_run":first["run_id"],
        "primary_GER_seasons":99,"primary_GER_bird_ID_strings":49,
        "original_paper_GER_eligible_seasons":99,"original_paper_GER_birds":63,
        "exact_individual_roster_reconstructed":False,
        "any_arm_reproduced_original_99_63":False,
        "labels_opened":False,
        "biological_terminal":limits["biological_terminal"]
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
