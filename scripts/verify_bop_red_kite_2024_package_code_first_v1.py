#!/usr/bin/env python3
"""Verify the original 2024 NestTool code ZIP first-source fingerprint offline."""
from __future__ import annotations
import argparse
import hashlib
import json
from pathlib import Path

ROOT=Path(__file__).resolve().parents[1]
RECEIPT=ROOT/"BOP_RED_KITE_2024_PACKAGE_CODE_V1_FIRST_RECEIPT.json"
CONTRACT=ROOT/"research/BOP_RED_KITE_2024_PACKAGE_CODE_V1_CONTRACT.json"

def verify(receipt:dict,contract:dict,*,raw:bytes|None=None)->dict:
    a=receipt["first_actions"]
    p=receipt["original_archived_provider"]
    code=receipt["code_parity"]
    scope=receipt["scientific_limit"]
    expected_contract="61150a97df8a1b07b05837341350ffbc5f81b9bf77043c5747bfa763048aadfa"
    expected_json="bb5a0a9251c4396b71caa239046b48de7996b03807ebad9f9677f473604775f9"
    expected_artifact_zip="b9aa6ae7ef7b687adbc368405b630963ecfccfda07b4f16a144efd65208e2fe9"
    expected_data_prep_sha="d398cddb6bc6b2ef7453618ac20a3e57e654777db35114a06a35683911e532cd"
    if (
        receipt.get("receipt_id")!="bop-red-kite-first-official-2024-code-ZIP-parity-v1"
        or receipt.get("original_frozen_contract_commit")!="be5623ac3680e89d2023d576003e6a28982a789d"
        or contract["contract_id"]!="bop-red-kite-frozen-2024-package-code-only-v1"
        or a["workflow_run_id"]!=44288291609
        or a["original_source_job_id"]!=134746762799
        or a["original_head_sha"]!="1c4859c77687842bfabf3df47d26ad92249c84cb"
        or a["artifact_id"]!=14420740820
        or a["original_artifact_ZIP_size_bytes"]!=1375
        or a["original_artifact_ZIP_sha256"]!=expected_artifact_zip
        or a["original_JSON_size_bytes"]!=2665
        or a["original_JSON_sha256"]!=expected_json
        or a["frozen_contract_sha256"]!=expected_contract
        or hashlib.sha256(CONTRACT.read_bytes()).hexdigest()!=expected_contract
        or a["first_source_job_conclusion"]!="success"
        or a["synthetic_python_matrix_success"]!=["3.10","3.12","3.13"]
    ):
        raise ValueError("code-only original source contract, workflow or artifact drifted")
    if (
        p["zenodo_record_id"]!=13736049
        or p["code_ZIP_file"]!="NestTool-1.0.0.zip"
        or p["code_ZIP_size_bytes"]!=6578763
        or p["code_ZIP_provider_MD5_verified"] is not True
        or p["code_ZIP_sha256"]!="ce9737f120aaf039d8252525a9a96d869c3975030f5bf3960c8d86615455bdc9"
        or p["archived_script_file"]!="NestTool_archived_full_analysis.r"
        or p["archived_script_provider_MD5_verified"] is not True
        or p["archived_script_sha256"]!="fad4f86f8c5ad401ba305e0090654edfeef5ec058e3e1e32898b308b71f02e5d"
        or p["R_source_member_count"]!=13
        or p["total_R_source_uncompressed_bytes"]!=146094
    ):
        raise ValueError("official Zenodo code ZIP or script metadata was reinterpreted")
    if (
        code["compared_path"]!="NestTool-1.0.0/R/data_prep.R"
        or code["historical_reference"]!="Vogelwarte/NestTool@8fdf3884b5f6079afdffdc5c563c9050766670a4:R/data_prep.R"
        or code["historical_reference_git_blob_sha1"]!="3fa42eddbfb852d5dbc29364281bffef8410563e"
        or code["zipped_R_data_prep_git_blob_sha1"]!=code["historical_reference_git_blob_sha1"]
        or code["both_R_data_prep_sha256"]!=expected_data_prep_sha
        or code["exact_byte_equal"] is not True
        or code["only_EOL_difference"] is not False
        or code["historical_ZIP_R_data_prep_strict_gt_800_line"]!=163
        or code["historical_ZIP_R_data_prep_ordinal_DOY_filter_line"]!=108
        or code["archived_script_unfiltered_count_expression_line"]!=501
        or code["prior_source_count_audit_line_486_needs_correction"] is not True
        or code["all_13_R_file_parity_checked"] is not False
        or code["upstream_60min_resampling_code_found"] is not False
    ):
        raise ValueError("archived exact-byte match or manuscript correction improperly promoted")
    if (
        scope["code_parity_does_not_prove_paper_bird_roster"] is not True
        or scope["author_counting_error_not_confirmed"] is not True
        or scope["historic_BOP_terminal"]!="empirical_state_prediction_mixed"
        or scope["red_kite_biological_terminal"]!="HOLD_NO_FROZEN_NEW_NEST_STATE_MODEL_OR_IDENTITY_ROSTER"
        or scope["no_GPS_CSV_or_breeding_labels_accessed_in_this_route"] is not True
        or scope["no_new_biological_model_or_calibration"] is not True
    ):
        raise ValueError("code-only file parity promoted into unsupported biological conclusion")
    if raw is not None:
        if len(raw)!=2665 or hashlib.sha256(raw).hexdigest()!=expected_json:
            raise ValueError("latest source code-only result is not byte-identical to first GitHub Actions output")
        new=json.loads(raw)
        if (
            new["status"]!="PACKAGE_CODE_EXACT_GIT_MATCH"
            or new["zip_R_data_prep_digest"]["git_blob_sha1"]!=code["historical_reference_git_blob_sha1"]
            or new["archived_top_level_script"]["pattern_line_numbers"]["length(unique(GERseasondata$bird_id))"]!=[501]
            or new["zip_data_prep_static_patterns"]["number_of_fixes > minlocs"]!=[163]
            or new["no_GPS_or_reproductive_labels_accessed"] is not True
            or new["original_GER_99_63_eligible_animal_roster_reconstructed"] is not False
        ):
            raise ValueError("source code fingerprints or biological claim limits changed")
    return {
        "original_Zenodo_code_archive_verified":True,
        "first_run":a["workflow_run_id"],
        "R_data_prep_byte_identical_to_prepublication_GitHub":True,
        "unfiltered_bird_count_original_script_line":501,
        "all_13_R_source_files_compared":False,
        "upstream_60min_method_known":False,
        "red_kite_real_biological_prediction_gain":"HOLD_NO_FROZEN_NEW_NEST_STATE_MODEL_OR_IDENTITY_ROSTER",
    }

def main():
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument("--result",type=Path)
    args=p.parse_args()
    raw=args.result.read_bytes() if args.result else None
    print(json.dumps(verify(json.loads(RECEIPT.read_text(encoding="utf-8")),
                            json.loads(CONTRACT.read_text(encoding="utf-8")),
                            raw=raw),sort_keys=True))
if __name__=="__main__":
    main()
