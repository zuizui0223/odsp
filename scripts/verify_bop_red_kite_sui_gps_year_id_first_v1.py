#!/usr/bin/env python3
"""Offline audit of first official Swiss red-kite source sample and group reuse.

No network, source CSVs, locations, bird/year IDs, nesting labels or fitted
models. Recomputes 12 original source counts and mathematical expectations
from the original provider-verified aggregate-only receipt.
"""
from __future__ import annotations
import argparse
from collections import Counter
import hashlib
import json
from pathlib import Path
import sys

ROOT=Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0,str(ROOT))

from scripts.bop_red_kite_sui_gps_year_id_admission_v1 import expected_shared_birds

RECEIPT=ROOT/"BOP_RED_KITE_SUI_GPS_YEAR_ID_ADMISSION_V1_FIRST_RECEIPT.json"
CONTRACT=ROOT/"research/BOP_RED_KITE_SUI_GPS_YEAR_ID_ADMISSION_V1_CONTRACT.json"

EXPECTED_COUNTS=[
    ("fixed_2023_DOY_ordinal__observed_source_events__strict_gt_800",697,258),
    ("fixed_2023_DOY_ordinal__observed_source_events__inclusive_ge_800",697,258),
    ("fixed_2023_DOY_ordinal__unique_UTC_hour_bin__strict_gt_800",697,258),
    ("fixed_2023_DOY_ordinal__unique_UTC_hour_bin__inclusive_ge_800",697,258),
    ("fixed_2023_DOY_ordinal__rolling_3600_seconds__strict_gt_800",620,246),
    ("fixed_2023_DOY_ordinal__rolling_3600_seconds__inclusive_ge_800",621,246),
    ("actual_calendar_month_day__observed_source_events__strict_gt_800",697,258),
    ("actual_calendar_month_day__observed_source_events__inclusive_ge_800",697,258),
    ("actual_calendar_month_day__unique_UTC_hour_bin__strict_gt_800",697,258),
    ("actual_calendar_month_day__unique_UTC_hour_bin__inclusive_ge_800",697,258),
    ("actual_calendar_month_day__rolling_3600_seconds__strict_gt_800",622,246),
    ("actual_calendar_month_day__rolling_3600_seconds__inclusive_ge_800",623,246),
]
PRIMARY_HIST={"1":66,"2":51,"3":62,"4":56,"5":20,"6":2,"7":1}

def verify_first(receipt:dict,contract:dict,*,raw:bytes|None=None)->dict:
    first=receipt["first_actions"]
    summary=receipt["summary"]
    lim=receipt["claim_limits"]
    original=receipt["original_source_output"]
    original_sha="c1fc25a81d2285d0751e4e8b9ef5c85dda0d4e9252a56a464373c3b4dff18a5a"
    archived_contract_sha="52ca9198aa3b6a7f5282186e437c99340f28b03c55ac01c7ef17dbe2d6f01993"
    if (
        receipt.get("receipt_id")!="bop-redkite-SUI-first-official-12-arm-source-eligibility-and-expected-overlap-v1"
        or receipt.get("original_preaccess_contract_commit")!="4826226d4f3ac6d1f3af74191b0e6ebf53fb027f"
        or contract.get("contract_id")!="bop-redkite-SUI-source-year-bird-GPS-eligibility-v1"
        or contract["predeclared_eligibility"]["primary_descriptive_arm"]!="fixed_2023_DOY_ordinal__unique_UTC_hour_bin__strict_gt_800"
        or first["run_id"]!=44456757144
        or first["source_job_id"]!=135336383906
        or first["original_branch_head"]!="59e11769cfc9051de212e8d7dc1936219080e694"
        or first["conclusion"]!="success"
        or first["artifact_id"]!=14498950985
        or first["artifact_name"]!="bop-red-kite-sui-source-first"
        or first["original_artifact_ZIP_bytes"]!=1464
        or first["original_artifact_ZIP_sha256"]!="5db9468c76f294ed2f6f339fb2bb5d1bb56109fc7a17be529161fefe7a63bdeb"
        or first["original_JSON_filename"]!="bop-red-kite-sui-source-first.json"
        or first["original_JSON_bytes"]!=10573
        or first["original_JSON_sha256"]!=original_sha
        or first["frozen_contract_sha256"]!=archived_contract_sha
        or hashlib.sha256(CONTRACT.read_bytes()).hexdigest()!=archived_contract_sha
        or first["synthetic_Python_3_10_3_12_3_13_success"] is not True
    ):
        raise ValueError("original Swiss source contract/Actions provenance or ZIP/JSON digest drifted")
    first_json=(json.dumps(original,sort_keys=True,indent=2,allow_nan=False)+"\n").encode("utf-8")
    if len(first_json)!=10573 or hashlib.sha256(first_json).hexdigest()!=original_sha:
        raise ValueError("original first official source JSON cannot be exactly reconstructed")
    if raw is not None and (len(raw)!=10573 or hashlib.sha256(raw).hexdigest()!=original_sha):
        raise ValueError("offered source output is not byte-identical to first original Actions result")

    gps=original["GPS_source_aggregate"]
    if (
        original["status"]!="SUI_SOURCE_12_ARM_QUALITY_COUNTS_ONLY"
        or original["preaccess_contract_sha256"]!=archived_contract_sha
        or original["original_GPS_and_metadata_full_provider_MD5_verified"] is not True
        or (original["Swiss_source_unfiltered_metadata_year_ID_strings"],
            original["Swiss_source_unfiltered_metadata_bird_ID_strings"])!=(2866,553)
        or gps["source_GPS_physical_rows"]!=2395531
        or gps["GPS_rows_from_unlisted_year_ID"]!=0
        or gps["GPS_rows_with_inconsistent_bird_ID"]!=0
        or gps["GPS_rows_with_exact_metadata_year_bird_match"]!=2395531
        or gps["GPS_rows_outside_strict_geobounds"]!=390753
        or gps["malformed_GPS_rows"]!=0
        or gps["inseason_GPS_event_rows_by_date_arm"]!={"fixed_2023_DOY_ordinal":1138761,"actual_calendar_month_day":1140949}
        or gps["linked_GPS_seasons_having_any_inseason_record_by_date_arm"]!={"fixed_2023_DOY_ordinal":967,"actual_calendar_month_day":967}
    ):
        raise ValueError("Swiss original provider row counts, MD5 or unfiltered cohort drifted")
    arms=original["twelve_fixed_eligibility_arms"]
    if len(arms)!=12 or [(x["arm"],x["eligible_year_ID_strings"],x["distinct_bird_ID_strings"]) for x in arms]!=EXPECTED_COUNTS:
        raise ValueError("source-declared twelve GPS eligibility arms or paper-count discrepancy rewritten")
    for item in arms:
        n=item["eligible_year_ID_strings"]
        birds=item["distinct_bird_ID_strings"]
        hist=Counter({int(k):v for k,v in item["bird_seasons_per_bird_histogram"].items()})
        train=round(0.7*n)
        if (
            sum(hist.values())!=birds
            or sum(k*v for k,v in hist.items())!=n
            or max(hist,default=0)!=item["max_seasons_per_bird"]
            or item["birds_with_multiple_eligible_seasons"]!=sum(v for k,v in hist.items() if k>=2)
            or item["hypothetical_uniform_year_split_training_seasons"]!=train
            or item["hypothetical_uniform_year_split_test_seasons"]!=n-train
            or item["expected_bird_ID_strings_in_both_split_roles"]!=round(expected_shared_birds(hist,n,train),6)
            or item["matches_both_published_697_seasons_258_birds_numerically"]!=(n==697 and birds==258)
            or item["published_2024_real_split_and_bird_authentication_not_verified"] is not True
        ):
            raise ValueError("group histogram cannot reproduce source-only expectation and limits")
    primary=next(x for x in arms if x["arm"]==original["primary_arm_published_before_source"])
    matches=sum(x["matches_both_published_697_seasons_258_birds_numerically"] for x in arms)
    if (
        primary["bird_seasons_per_bird_histogram"]!=PRIMARY_HIST
        or primary["expected_bird_ID_strings_in_both_split_roles"]!=121.992374
        or matches!=8
        or original["no_posthoc_selection_of_matching_697_258"] is not True
        or original["no_label_or_GPS_source_individual_record_emitted"] is not True
        or original["paper_2024_training_roster_authenticated"] is not False
        or original["original_actual_2024_training_random_seed_observed"] is not False
        or original["actual_forecast_probabilities_scored"] is not False
        or original["BOP_historical_terminal"]!="empirical_state_prediction_mixed"
        or original["redkite_biological_terminal"]!="HOLD_NO_FROZEN_NEW_NEST_STATE_MODEL_OR_IDENTITY_ROSTER"
    ):
        raise ValueError("paper-matched Swiss sample overpromoted to authenticated 2024 outcome")
    if (
        summary["source_original_GPS_rows"]!=2395531
        or summary["all_SUI_source_year_ID_strings"]!=2866
        or summary["all_SUI_source_bird_ID_strings"]!=553
        or summary["source_GPS_date_eligible_before_fix_screen"]!=967
        or summary["primary_frozen_arm"]!=primary["arm"]
        or summary["primary_eligible_year_ID_strings"]!=697
        or summary["primary_eligible_bird_ID_strings"]!=258
        or summary["primary_source_multiplicity"]!=PRIMARY_HIST
        or summary["primary_bird_ID_strings_with_two_or_more_years"]!=192
        or summary["expected_bird_ID_strings_both_roles_under_hypothetical_uniform_488_209_year_split"]!=121.992374
        or summary["source_selection_arms_total"]!=12
        or summary["selection_arms_matching_published_697_and_258_numeric_counts"]!=8
    ):
        raise ValueError("official source aggregate and committed first receipt disagree")
    required={
        "provider_full_GPS_and_metadata_MD5_rechecked":True,
        "source_multiplicity_computed_from_exact_original_2024_source":True,
        "original_2024_split_bird_memberships_and_random_seed_unobserved":True,
        "expected_overlap_not_actual_observed_overlap":True,
        "numeric_697_258_match_not_identity_crosswalk":True,
        "no_HR_nest_success_values_decoded":True,
        "no_event_level_GPS_or_identifying_IDs_exported":True,
        "no_model_retraining_or_accuracy_inflation_measured":True,
        "nesting_success_subset_not_reconstructed":True,
        "paper_rejected_336_vs_source_filtered_270_not_reconciled":True,
        "original_BOP_terminal":"empirical_state_prediction_mixed",
        "redkite_biological_terminal":"HOLD_NO_FROZEN_NEW_NEST_STATE_MODEL_OR_IDENTITY_ROSTER"
    }
    for k,v in required.items():
        if lim.get(k)!=v:
            raise ValueError("mathematical expectation or original bird-group independence overclaimed")
    return {
        "original_first_source_checked":True,
        "first_run_id":44456757144,
        "first_artifact_id":14498950985,
        "Swiss_source_paper_matching_seasons":697,
        "Swiss_source_paper_matching_bird_ID_strings":258,
        "Swiss_source_two_or_more_season_bird_ID_strings":192,
        "conditional_expected_bird_ID_strings_in_both_uniform_488_209_roles":121.992374,
        "no_actual_2024_split_or_model_scores_recovered":True,
        "redkite_new_group_prediction":"HOLD_NO_FROZEN_NEW_NEST_STATE_MODEL_OR_IDENTITY_ROSTER"
    }


def main():
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument("--result",type=Path)
    args=p.parse_args()
    raw=args.result.read_bytes() if args.result else None
    result=verify_first(
        json.loads(RECEIPT.read_text(encoding="utf-8")),
        json.loads(CONTRACT.read_text(encoding="utf-8")),
        raw=raw)
    print(json.dumps(result,sort_keys=True))


if __name__=="__main__":
    main()
