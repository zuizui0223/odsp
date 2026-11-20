#!/usr/bin/env python3
"""Offline immutable first source-free 2022 exact-rank proof and claim audit."""
from __future__ import annotations
import argparse
from io import BytesIO
import hashlib
import json
from pathlib import Path
import sys
import zipfile

ROOT=Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0,str(ROOT))
from scripts.bop_swiss_2022_rank_resolution_v1 import (
    CONTRACT,PRIOR,git_blob_sha1,run
)

RECEIPT=ROOT/"BOP_SWISS_2022_RANK_RESOLUTION_V1_FIRST_RECEIPT.json"
FIRST_ZIP_SHA="64b11cf6a5bdb04be4283e54ac4e6cbcd1929feaae41bfd4e434ffc63744f86f"
FIRST_JSON_SHA="9f228db64e2c08fe466c72c145b74721a943dfc355ff41138759d6aabade6378"

def verify_first(receipt:dict,*,zip_data:bytes|None=None)->dict:
    source=receipt["original_source_unchanged"]
    first=receipt["first_actions"]
    result=receipt["fixed_reference"]
    bounds=receipt["scientific_limits"]
    if (
        receipt.get("receipt_id")!="bop-swiss-2022-four-negative-exact-rank-reference-first-v1"
        or receipt.get("contract_freeze_commit")!="9e335670c28f49f3fc5f52d9495d159daa263916"
        or receipt.get("frozen_contract_git_blob_sha1")!="4074cbb68edd598079ce7a9170325392e0a23760"
        or git_blob_sha1(CONTRACT.read_bytes())!=receipt["frozen_contract_git_blob_sha1"]
        or source.get("prior_first_run_id")!=44746545177
        or source.get("prior_first_artifact_id")!=14633317139
        or source.get("original_receipt_git_blob_sha1")!="82c328cc5bd5b88afa2faf8f0121d607af1a4e72"
        or git_blob_sha1(PRIOR.read_bytes())!=source["original_receipt_git_blob_sha1"]
        or source.get("no_2024_prepared_RDS_or_raw_HR_nest_labels_read") is not True
        or source.get("no_individual_predictions_or_IDs_read") is not True
        or first.get("run_id")!=44752203435
        or first.get("source_free_python_3_10_3_12_3_13_succeeded") is not True
        or first.get("first_job_artifact_id")!=14636041683
        or first.get("first_artifact_name")!="bop-swiss-2022-rank-reference-first"
        or first.get("first_zip_bytes")!=1717
        or first.get("first_zip_sha256")!=FIRST_ZIP_SHA
        or first.get("first_json_filename")!="bop-swiss-2022-rank-reference-v1.json"
        or first.get("first_json_bytes")!=8950
        or first.get("first_json_sha256")!=FIRST_JSON_SHA
    ):
        raise ValueError("original first 2022 finite-rank contract/source artifact drift")
    expected=run()  # original immutable PR #298 receipt; no raw source or external access
    cases=expected["four_original_2022_mean_AUC_random_rank_lower_reference"]
    source_four=[[x["target"],x["mode"],x["original_2022_mean_AUC"],
        x["random_rank_lower_tail_at_observed_mean_AUC_REFERENCE_NOT_P_VALUE"]]
        for x in cases]
    all_baselines=expected["all_twelve_model_accuracies_vs_test_majority_oracle_DIAGNOSTIC_ONLY"]
    source_12=[[x["cutoff"],x["target"],x["mode"],x["fixed_R_RF_accuracy_mean"],
        x["source_test_majority_class_accuracy_DIAGNOSTIC_ONLY"],
        x["fixed_R_RF_accuracy_minus_oracle_majority_benchmark"]]
        for x in all_baselines]
    if (
        (result.get("positive_2022_test_bird_seasons"),
         result.get("negative_2022_test_bird_seasons"),
         result.get("positive_negative_rank_pairs"),
         result.get("exact_tie_free_label_placements"))!=(28,4,112,35960)
        or result.get("one_negative_max_AUC_shift")!=.25
        or result.get("exact_tie_free_random_rank_central_90")!=expected["random_rank_central_90_reference"]
        or result.get("exact_tie_free_random_rank_central_95")!=expected["random_rank_central_95_reference"]
        or result.get("four_original_auc_and_lower_reference")!=source_four
        or result.get("all_twelve_original_accuracy_vs_test_majority_oracle")!=source_12
    ):
        raise ValueError("first source-free finite-rank reference or majority diagnostic reclassified")
    for key,required in {
        "not_exact_8_seed_mean_auc_significance_test":True,
        "actual_RF_probs_may_have_ties":True,
        "repeated_8_forest_seeds_same_32_birds":True,
        "diagnostic_oracle_majority_uses_test_prevalence_not_valid_forecast_baseline":True,
        "original_training_only_prevalence_log_score_reference_unchanged":True,
        "four_negative_2022_cohort_no_ecological_regime_shift_inference":True,
        "all_2020_2021_2022_cutoffs_preserved_no_posthoc_selection":True,
        "no_new_independent_outcome_labels_or_source_model_fits":True,
        "original_BOP":"empirical_state_prediction_mixed",
        "redkite_external":"HOLD_NO_FROZEN_NEW_NEST_STATE_MODEL_OR_IDENTITY_ROSTER",
        "original_Dryad":"NOT_ADMITTED",
    }.items():
        if bounds.get(key)!=required:
            raise ValueError("2022 source-free diagnostic promoted beyond evidence")
    if zip_data is not None:
        if len(zip_data)!=1717 or hashlib.sha256(zip_data).hexdigest()!=FIRST_ZIP_SHA:
            raise ValueError("offered original source-free Actions ZIP does not match first artifact")
        with zipfile.ZipFile(BytesIO(zip_data)) as z:
            if z.namelist()!=[first["first_json_filename"]]:
                raise ValueError("unexpected source rows or identifiers included in original source-free artifact")
            content=z.read(first["first_json_filename"])
            if len(content)!=8950 or hashlib.sha256(content).hexdigest()!=FIRST_JSON_SHA:
                raise ValueError("original source-free diagnostic JSON digest changed")
            if json.loads(content)!=expected:
                raise ValueError("first official source-free output no longer equals recomputed reference")
    return {
        "status":"FIRST_EXACT_2022_FOUR_NEGATIVE_RANK_DIAGNOSTIC_VERIFIED",
        "first_run":44752203435,
        "first_artifact":14636041683,
        "n_test_positive":28,"n_test_negative":4,
        "exact_tie_free_rank_configurations":35960,
        "central_95_random_rank_reference":expected["random_rank_central_95_reference"],
        "2022_purged_HR_mean_AUC":.373884,
        "2022_purged_nest_mean_AUC":.313616,
        "2022_test_majority_accuracy":.875,
        "not_a_p_value_for_repeated_eight_seed_model_means":True,
        "original_BOP":"empirical_state_prediction_mixed",
        "external_redkite":"HOLD_NO_FROZEN_NEW_NEST_STATE_MODEL_OR_IDENTITY_ROSTER"
    }

def main():
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument("--first-artifact-zip",type=Path)
    a=p.parse_args()
    content=a.first_artifact_zip.read_bytes() if a.first_artifact_zip else None
    result=verify_first(json.loads(RECEIPT.read_text(encoding="utf-8")),zip_data=content)
    print(json.dumps(result,sort_keys=True))

if __name__=="__main__":
    main()
