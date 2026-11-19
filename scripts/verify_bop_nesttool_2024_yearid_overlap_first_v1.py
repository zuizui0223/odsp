#!/usr/bin/env python3
"""Offline immutable first-run NestTool 2024 trainer source/overlap audit.

No provider request; all claims are limited to original code provenance and
expected animal overlap under uniform *season* partitioning.
"""
from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path
import sys

REPO_ROOT=Path(__file__).resolve().parents[1]
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0,str(REPO_ROOT))

from scripts.bop_nesttool_2024_yearid_animal_overlap_v1 import (
    sharp_expected_overlap_bounds,
)

ROOT=Path(__file__).resolve().parents[1]
CONTRACT=ROOT/"research/BOP_NESTTOOL_2024_YEARID_SPLIT_ANIMAL_OVERLAP_V1_CONTRACT.json"
RECEIPT=ROOT/"BOP_NESTTOOL_2024_YEARID_ANIMAL_OVERLAP_V1_FIRST_RECEIPT.json"

def verify_first(receipt:dict,contract:dict)->dict:
    run=receipt["first_actions"]
    source=receipt["original_zip"]
    math=receipt["math"]
    limits=receipt["claim_limits"]
    if (
        receipt.get("receipt_id")!="bop-nesttool-2024-three-trainer-source-and-yearid-overlap-first-v1"
        or receipt.get("contract_frozen_before_source")!="3b50495405731eec92f925654740cb13906b316a"
        or contract.get("contract_id")!="bop-nesttool-2024-training-yearid-split-expected-animal-overlap-v1"
        or run.get("run_id")!=44307730106
        or run.get("source_job_id")!=134819982555
        or run.get("first_branch_head")!="3f90fa6721d17706fd06ef449105faf4a0c8ae69"
        or run.get("source_job_conclusion")!="success"
        or run.get("artifact_id")!=14429691808
        or run.get("artifact_name")!="bop-nesttool-yearid-animal-overlap-first"
        or run.get("original_artifact_zip_bytes")!=1577
        or run.get("original_artifact_zip_sha256")!="48c7a408f08f7a9a5aa7d85ff6347617cb738c0e16db0641ee6c45d3c7d07fee"
        or run.get("original_json_filename")!="bop-nesttool-yearid-overlap-first.json"
        or run.get("original_json_bytes")!=4657
        or run.get("original_json_sha256")!="f2617e20b3a16b089a365ed8257e3011d56b013933294d0c480b5ef919b38f60"
        or run.get("contract_sha256")!="fe7332979ba7320968c19a60752ac1592fd5b760c2c03ee3708e3ce6321bcbde"
        or run.get("contract_sha256")!=hashlib.sha256(CONTRACT.read_bytes()).hexdigest()
        or run.get("offline_python_matrix_success")!=["3.10","3.12","3.13"]
    ):
        raise ValueError("original source parity run, immutable artifact or contract drift")
    if (
        source.get("zenodo_record")!=13736049
        or source.get("code_zip_name")!="NestTool-1.0.0.zip"
        or source.get("provider_MD5_and_SHA256_verified") is not True
        or source.get("original_zip_sha256")!="ce9737f120aaf039d8252525a9a96d869c3975030f5bf3960c8d86615455bdc9"
        or source.get("historical_github_commit")!="8fdf3884b5f6079afdffdc5c563c9050766670a4"
        or source.get("exact_three_r_source_byte_match") is not True
    ):
        raise ValueError("2024 code archive is not the exact verified source")
    trainers=source.get("trainer_split_source")
    expected=[
        ("R/train_home_range_detection.R","47c7b5f6dbcfb53c2df8a014a65fe59cf8a258dd",69,70,73,75),
        ("R/train_nest_detection.R","c028e728e0fdf646c3bf6f46e10b3ae6b8f55bcd",69,70,73,75),
        ("R/train_nest_success.R","c657973023308201cc11c2fa0c8830fd6655ec5b",95,96,99,101)
    ]
    if not isinstance(trainers,list) or len(trainers)!=3:
        raise ValueError("must verify exactly three frozen trainers")
    for item,(name,sha,source_line,sample_line,train_line,test_line) in zip(trainers,expected):
        if (
            item.get("path")!=name
            or item.get("git_blob_sha1")!=sha
            or item.get("unique_year_id_line")!=source_line
            or item.get("random_sample_line")!=sample_line
            or item.get("train_filter_line")!=train_line
            or item.get("test_filter_line")!=test_line
        ):
            raise ValueError("archived source uses different split unit/byte provenance")
    recomputed=sharp_expected_overlap_bounds(697,258,7,488)
    if (
        (math.get("sample_season_rows"),math.get("published_bird_count"),
         math.get("max_seasons_per_bird"),math.get("training_season_rows"),
         math.get("validation_season_rows"))!=(697,258,7,488,209)
        or math.get("original_random_split_grouping")!="year_id"
        or math.get("biological_grouping_required_for_new_birds")!="bird_id"
        or math.get("conditional_minimum_expected_birds_in_both_roles")!=
          recomputed["minimum_expected_birds_shared_between_train_and_test"]
        or math.get("conditional_maximum_expected_birds_in_both_roles")!=
          recomputed["maximum_expected_birds_shared_between_train_and_test"]
        or math.get("minimizer_histogram")!=recomputed["minimum_extremal_histogram"]
        or math.get("maximizer_histogram")!=recomputed["maximum_extremal_histogram"]
        or math.get("discrete_concavity_and_extreme_histograms_verified") is not True
        or math.get("bounds_are_expectations_only") is not True
        or math.get("unknown_original_realized_train_test_overlap") is not True
        or math.get("no_accuracy_inflation_or_independent_group_prediction_inferred") is not True
    ):
        raise ValueError("mathematical expectation mislabelled as realized bird-level error")
    if (
        limits.get("actual_2024_data_split_random_seed_or_bird_roster_read") is not False
        or limits.get("individual_tracking_rows_opened") is not False
        or limits.get("reproductive_outcome_values_opened") is not False
        or limits.get("model_probabilities_calculated") is not False
        or limits.get("Swiss_to_Germany_external_validation_not_reassessed") is not True
        or limits.get("nest_success_smaller_conditioned_training_sample_not_scored") is not True
        or limits.get("original_BOP_terminal")!="empirical_state_prediction_mixed"
        or limits.get("redkite_real_gain_terminal")!="HOLD_NO_FROZEN_NEW_NEST_STATE_MODEL_OR_IDENTITY_ROSTER"
        or limits.get("method_claim")!="SEASON_LEVEL_SPLIT_CAN_REUSE_BIRDS_ACROSS_TRAIN_AND_TEST"
    ):
        raise ValueError("mathematical/source-only observation improperly promoted to predictive gain")
    return {
        "status":"FIRST_SOURCE_CODE_AND_EXPECTATION_BOUNDS_VERIFIED",
        "first_run_id":44307730106,
        "first_artifact_id":14429691808,
        "three_Zenodo_trainers_byte_identical_to_2024_GitHub":True,
        "all_three_split_on_year_id_not_bird_id":True,
        "minimum_expected_duplicated_birds":67.462949,
        "maximum_expected_duplicated_birds":146.540230,
        "original_realized_train_test_overlap_verified":False,
        "model_accuracy_inflation_measured":False,
        "redkite_new_bird_validation":"HOLD_NO_FROZEN_NEW_NEST_STATE_MODEL_OR_IDENTITY_ROSTER",
    }

def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.parse_args()
    output=verify_first(
        json.loads(RECEIPT.read_text(encoding="utf-8")),
        json.loads(CONTRACT.read_text(encoding="utf-8"))
    )
    print(json.dumps(output,sort_keys=True))

if __name__=="__main__":
    main()
