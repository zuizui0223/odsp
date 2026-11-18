#!/usr/bin/env python3
"""Offline verification of immutable first anonymous Movebank study-metadata HOLD.

This verifier performs NO Movebank HTTP requests. It preserves the original
failed first result instead of turning HTTPError into guessed owner permission.
"""
from __future__ import annotations
import argparse
import hashlib
import json
from pathlib import Path

ROOT=Path(__file__).resolve().parents[1]
CONTRACT=ROOT/"research/BOP_RED_KITE_GER_MOVEBANK_STUDY_METADATA_V1_CONTRACT.json"
RECEIPT=ROOT/"BOP_RED_KITE_GER_MOVEBANK_STUDY_META_V1_FIRST_RECEIPT.json"

def _git_blob_sha(b:bytes)->str:
    return hashlib.sha1(b"blob "+str(len(b)).encode("ascii")+b"\0"+b).hexdigest()

def verify_first(receipt:dict,contract:dict,*,raw:bytes|None=None)->dict:
    first=receipt["original_actions"]
    state=receipt["observed_first_source_result"]
    limit=receipt["scientific_limits"]
    original=receipt["first_original_source_output"]
    sha="bb8814a3265cc9a0676c5e1006e20da6c92f8682b71a695652cb7fbeb855b309"
    zipsha="f23338f33b326c40dc214706e0fdc7830f5b725b2b014bcf0ef9a40e583caa7b"
    blob="b2577b084c63ffd3839f25f9ff4c0912b3a10af1"
    if (
        receipt.get("receipt_id")!="bop-red-kite-Movebank-GER-first-anonymous-study-metadata-access-hold-v1"
        or receipt.get("first_preaccess_contract_commit")!="69836d5888a36f5a21a1f604c6ef2528400cc69d"
        or receipt.get("first_preaccess_contract_git_blob_sha1")!=blob
        or _git_blob_sha(CONTRACT.read_bytes())!=blob
        or contract["contract_id"]!="bop-red-kite-Movebank-DE-study-public-metadata-v1"
        or contract["narrow_source"]["url"]!="https://www.movebank.org/movebank/service/direct-read?entity_type=study&study_id=294443150"
        or contract["safety"]["no_GPS_or_other_event_data"] is not True
        or first["workflow_run_id"]!=44299216766
        or first["source_job_id"]!=134785441531
        or first["original_source_branch_head_sha"]!="fc12108beae9640cb5e84c7f29461d2cfc8b095d"
        or first["source_job_conclusion"]!="failure"
        or first["failure_reason_class"]!="HTTPError"
        or first["artifact_id"]!=14425263270
        or first["artifact_name"]!="bop-red-kite-ger-movebank-study-meta-first"
        or first["first_actions_artifact_ZIP_sha256"]!=zipsha
        or first["original_JSON_filename"]!="bop-redkite-movebank-study-meta-first.json"
        or first["original_JSON_bytes"]!=665
        or first["original_JSON_sha256"]!=sha
        or first["preaccess_contract_commit_preceded_first_request"] is not True
        or first["offline_python_safety_versions_success"]!=["3.10","3.12","3.13"]
    ):
        raise ValueError("first Movebank source access or immutable contract provenance drifted")
    canonical=(json.dumps(original,sort_keys=True,indent=2,allow_nan=False)+"\n").encode("utf-8")
    if len(canonical)!=665 or hashlib.sha256(canonical).hexdigest()!=sha:
        raise ValueError("first original provider result does not reproduce Actions JSON SHA256")
    if raw is not None and (len(raw)!=665 or hashlib.sha256(raw).hexdigest()!=sha):
        raise ValueError("offered raw source result differs from first archived failed attempt")
    if (
        state["status"]!="STUDY_METADATA_ACCESS_HOLD"
        or state["error_type"]!="HTTPError"
        or state["source_role"]!="ANONYMOUS_LIVE_STUDY_SUMMARY_ONLY"
        or state["provider_record_id"]!=294443150
        or not state["actual_HTTP_status_not_recorded"]
        or not state["no_study_row_parsed"]
        or not state["no_provider_current_individual_count_verified"]
        or state["original_2024_163_65_roster_verified"] is not False
        or state["published_99_63_eligible_birds_verified"] is not False
        or state["archived_GER_99_49_source_result_unchanged"] is not True
        or state["no_individual_tag_deployment_or_event_records_opened"] is not True
        or state["no_reproductive_labels_opened"] is not True
    ):
        raise ValueError("unavailable Movebank metadata was promoted to eligible-bird evidence")
    for key,expected in {
        "no_GPS_or_reference_data_accessed_in_this_route":True,
        "HTTPError_does_not_establish_permission_denial_vs_other_server_error":True,
        "one_study_live_summary_not_complete_two_German_population_2024_roster":True,
        "no_second_url_retry_or_credentials_in_followup_CI":True,
        "current_Movebank_count_unavailable":True,
        "no_new_independent_bird_groups_admitted":True,
        "exact_prearchive_60min_GPS_processing_still_unknown":True,
        "historical_BOP_terminal":"empirical_state_prediction_mixed",
        "original_Dryad":"NOT_ADMITTED",
        "redkite_biological_terminal":"HOLD_NO_FROZEN_NEW_NEST_STATE_MODEL_OR_IDENTITY_ROSTER"
    }.items():
        if limit.get(key)!=expected:
            raise ValueError("source access HOLD or established biological terminal rewritten")
    return {
        "first_source_result_verified_offline":True,
        "status":"STUDY_METADATA_ACCESS_HOLD",
        "reason":"HTTPError_STATUS_CODE_NOT_CAPTURED",
        "first_actions_run_id":first["workflow_run_id"],
        "first_actions_artifact_id":first["artifact_id"],
        "anonymous_provider_count_established":False,
        "original_2024_163_65_verified":False,
        "original_2024_99_63_verified":False,
        "previous_Zenodo_99_49_unchanged":True,
        "provider_recontacted":False,
        "biological_terminal":"HOLD_NO_FROZEN_NEW_NEST_STATE_MODEL_OR_IDENTITY_ROSTER",
    }

def main():
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument("--result",type=Path)
    args=p.parse_args()
    raw=args.result.read_bytes() if args.result else None
    print(json.dumps(verify_first(
        json.loads(RECEIPT.read_text(encoding="utf-8")),
        json.loads(CONTRACT.read_text(encoding="utf-8")),raw=raw),sort_keys=True))
if __name__=="__main__":
    main()
