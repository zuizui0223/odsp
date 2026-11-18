#!/usr/bin/env python3
"""Reconcile independent publication/code/source-count evidence without downloading sources.

This is a POST-result source-provenance audit, not a pre-registered model
comparison. It reads only the three already-frozen counts-only source receipts,
not the GPS, individual-season CSV, reproductive labels or forecast files.
"""
from __future__ import annotations
import argparse
import hashlib
import json
from pathlib import Path

ROOT=Path(__file__).resolve().parents[1]
MATRIX=ROOT/"research/BOP_RED_KITE_2024_PAPER_SOURCE_COUNT_AUDIT_V1.json"
IDENTITY=ROOT/"BOP_RED_KITE_RAW_GROUP_PREFIX_ONLY_V1_FIRST_RECEIPT.json"
GPS=ROOT/"BOP_RED_KITE_GER_GPS_ELIGIBILITY_V1_FIRST_RECEIPT.json"
STAGES=ROOT/"BOP_RED_KITE_GER_GPS_STAGE_ATTRITION_V1_FIRST_RECEIPT.json"

def evaluate(evidence:dict,identity:dict,gps:dict,stages:dict)->dict:
    pub=evidence["references"]["paper"]
    zen=evidence["references"]["zenodo"]
    code=evidence["references"]["contemporary_code"]
    script=evidence["references"]["archive_script_evidence"]
    orig=evidence["frozen_internal_evidence"]
    diff=evidence["source_to_paper_discrepancies"]
    unresolved=evidence["additional_unresolved"]
    limits=evidence["statistical_claim_ceiling"]
    if (evidence["audit_id"]!="bop-red-kite-2024-publication-source-count-provenance-v1"
        or evidence["role"]!="POSTPUBLICATION_CODE_PROVENANCE_AND_SOURCE_COUNT_RECONCILIATION_NO_NEW_DATA_ACCESS"
        or pub["doi"]!="10.1111/jav.03246"
        or (pub["reported_original_GER_bird_years"],pub["reported_original_GER_birds"],
            pub["reported_eligible_GER_bird_years"],pub["reported_eligible_GER_birds"])!=(163,65,99,63)
        or zen["record_id"]!=13736049
        or zen["archive_script_file"]!="NestTool_archived_full_analysis.r"
        or zen["archive_script_provider_md5"]!="f3878bd76bd851d0ea048950ee84e8f9"
        or code["commit"]!="8fdf3884b5f6079afdffdc5c563c9050766670a4"
        or code["blob_sha"]!="3fa42eddbfb852d5dbc29364281bffef8410563e"
        or code["exact_counting_operator"]!="number_of_fixes > minlocs"
        or script["unfiltered_R_expression"]!="length(unique(GERseasondata$bird_id))"
        or script["filtered_R_expression"]!="GERseasondata %>% filter(year_id %in% unique(GER_data_input$summary$year_id))"
        or script["unfiltered_global_GER_bird_count_line"]!=486
        or script["filtered_GER_supplement_age_sex_lines"]!=[487,494]
        or script["direct_GER_data_prep_lines"]!=[299,315]
        or code["direct_2024_GitHub_to_Zenodo_binary_package_SHA_parity_verified"] is not False):
        raise ValueError("published code/source documentary anchors changed")

    source=identity["original_source_output"]["sources"][0]
    rows=gps["observed_source"]["all_12_fixed_arms"]
    levels=stages["observed_first"]["stages"]
    if (
        identity["receipt_id"]!="bop-redkite-official-key-prefix-only-first-v1"
        or gps["receipt_id"]!="bop-redkite-german-original-gps-eligibility-first-v1"
        or stages["receipt_id"]!="bop-redkite-GER-five-stage-eligibility-first-v1"
        or source["source"]!="GER_indseasondata.csv"
        or source["physical_record_lines"]!=159
        or source["distinct_bird_ID_strings"]!=63
        or source["distinct_year_ID_strings"]!=159
        or source["source_full_file_md5_verified"] is not True
        or rows[0]!=["fixed_2023_DOY_ordinal__observed_source_events__strict_gt_800",99,49]
        or levels[0]!=["S0_all_GER_metadata_seasons",159,63,0,0]
        or levels[-1]!=["S4_gt_800_valid_GPS_event_rows_after_S3",99,49,60,14]
        or len(levels)!=5
        or stages["observed_first"]["full_provider_MD5s_verified"] is not True
        or gps["observed_source"]["GPS_original_Zenodo_md5_verified"] is not True):
        raise ValueError("frozen provider count receipts no longer imply source-only 159/63 -> 99/49")
    if (orig["source_raw_seasons"],orig["source_raw_bird_ID_strings"],
        orig["source_GPS_eligible_seasons"],orig["source_GPS_eligible_bird_ID_strings"],
        orig["threshold_excluded_seasons"],orig["threshold_excluded_bird_strings"])!=(159,63,99,49,60,14):
        raise ValueError("immutable source count evidence has been reclassified")

    expected_differences={
        "original_season_difference_report_minus_archive":4,
        "original_bird_difference_report_minus_archive":2,
        "eligible_season_difference_report_minus_archive":0,
        "eligible_bird_difference_report_minus_archive":14,
    }
    if (any(diff[k]!=v for k,v in expected_differences.items())
        or diff["paper_63_may_be_unfiltered_count"]!="PLAUSIBLE_NOT_PROVEN"
        or diff["paper_99_seasons_may_come_from_same_archive"]!="NUMERIC_MATCH_ONLY_NOT_PROOF"
        or diff["paper_eligible_63_birds_reproduced"] is not False
        or unresolved["exact_provider_Zenodo_2024_package_source_binary_match"] is not False
        or unresolved["exact_original_upstream_GPS_60_min_resampling_recipe_unknown"] is not True
        or unresolved["published_preselection_163_65_to_archive_159_63_source_stage_unknown"] is not True
        or unresolved["no_new_empirical_probability_gain"] is not True
        or limits["BOP_historical_terminal"]!="empirical_state_prediction_mixed"
        or limits["BOP_original_Dryad"]!="NOT_ADMITTED"
        or limits["red_kite_real_group_rank"]!="HOLD_NO_FROZEN_NEW_NEST_STATE_MODEL_OR_IDENTITY_ROSTER"):
        raise ValueError("post-result publication discrepancy misrepresented as confirmed mechanism")
    assert len({x[1] for x in rows})>1  # alternative prior thinning rules have different season totals
    return {
        "status":"CODE_COUNT_PATH_DISCREPANCY_IDENTIFIED_AUTHOR_CAUSE_UNCONFIRMED",
        "published_original":{"seasons":163,"birds":65},
        "frozen_source_original":{"seasons":159,"bird_id_strings":63},
        "published_eligible":{"seasons":99,"birds":63},
        "frozen_source_eligibility":{"seasons":99,"bird_id_strings":49},
        "source_birds_lost_at_GPS_threshold":14,
        "source_seasons_lost_at_GPS_threshold":60,
        "raw_unfiltered_bird_ID_count_equals_published_eligible_count":True,
        "archived_script_explicit_unfiltered_count":True,
        "proves_author_error":False,
        "recomputed_outcomes_or_predictions":False,
        "verified_biological_individuals":False,
        "historical_BOP_terminal":"empirical_state_prediction_mixed",
        "red_kite_biological_terminal":"HOLD_NO_FROZEN_NEW_NEST_STATE_MODEL_OR_IDENTITY_ROSTER",
        "evidence_matrix_sha256":hashlib.sha256(MATRIX.read_bytes()).hexdigest(),
    }

def run()->dict:
    return evaluate(
        json.loads(MATRIX.read_text(encoding="utf-8")),
        json.loads(IDENTITY.read_text(encoding="utf-8")),
        json.loads(GPS.read_text(encoding="utf-8")),
        json.loads(STAGES.read_text(encoding="utf-8")),
    )

def main()->None:
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--out",type=Path,required=True)
    args=parser.parse_args()
    if args.out.resolve() in {MATRIX.resolve(),IDENTITY.resolve(),GPS.resolve(),STAGES.resolve()}:
        raise ValueError("output may not overwrite audited source or contract evidence")
    result=run()
    args.out.write_text(json.dumps(result,sort_keys=True,indent=2,allow_nan=False)+"\n",encoding="utf-8")
    print(json.dumps(result,sort_keys=True))
if __name__=="__main__":
    main()
