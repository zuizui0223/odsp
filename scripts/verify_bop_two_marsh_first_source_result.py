#!/usr/bin/env python3
"""Verify source-only results against original immutable Zenodo reference first run.

The original first-run artifact and frozen initial schema HOLD are never
overwritten or recategorized. The post-header audit remains descriptive.
"""
from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path
from typing import Mapping

if __package__:
    from .bop_two_marsh_reference_only_preflight import V1_PATH,V2_PATH
else:
    from bop_two_marsh_reference_only_preflight import V1_PATH,V2_PATH

ROOT=Path(__file__).resolve().parents[1]
RECEIPT=ROOT/"BOP_TWO_MARSH_REFERENCE_ONLY_V1_V2_FIRST_RECEIPT.json"


def _sha(raw:bytes)->str:
    return hashlib.sha256(raw).hexdigest()


def verify_two_marsh_first_result(
    result:Mapping[str,object], receipt:Mapping[str,object],
    *,
    exact_result_json_bytes:bytes|None=None,
)->dict[str,object]:
    p=receipt["preaccess_v1"]
    v=receipt["postheader_v2"]
    first=receipt["first_official_run"]
    expected=receipt["first_result"]
    if (
        receipt["receipt_id"]!="bop-two-marsh-reference-source-only-first-verified-v1-v2"
        or p["original_terminal"]!="SOURCE_SCHEMA_HOLD"
        or p["frozen_commit"]!="e13490fa2c2c314e5129a32a7fa7b5f6e31a2897"
        or _sha(V1_PATH.read_bytes())!=p["contract_sha256"]
        or _sha(V2_PATH.read_bytes())!=v["contract_sha256"]
        or v["header_observed_before_contract"] is not True
        or v["real_external_sample_admitted"] is not False
        or first["artifact_id"]!=12786202874
        or first["workflow_run_id"]!=40618963940
        or first["artifact_zip_sha256"]!="a5c854089722cb16bcb833ee2a409c4b32a956dfa6834c77de0f42be91fb2bbc"
    ):
        raise ValueError("original source/contract/first Actions provenance has drifted")
    if exact_result_json_bytes is not None and (
        _sha(exact_result_json_bytes)!=first["artifact_original_json_sha256"]
        or len(exact_result_json_bytes)!=first["artifact_original_json_bytes"]
    ):
        raise ValueError("new source-only result is not byte-identical to first provider-verified result")
    if (
        result.get("source_access")!="TWO_MD5_VERIFIED_REFERENCE_CSV_FILES_ONLY"
        or result.get("original_v1_terminal")!="SOURCE_SCHEMA_HOLD"
        or result.get("status")!="REFERENCE_ID_AND_TAG_REUSE_AUDIT_ONLY"
        or result.get("external_rank_admission_status")!="HOLD_POPULATION_AND_IDENTITY_EXCHANGEABILITY_UNVERIFIED"
        or result.get("GPS_height_or_location_events_accessed") is not False
        or result.get("new_external_prediction_claim") is not False
        or result.get("original_BOP_terminal")!="empirical_state_prediction_mixed"
        or result.get("Dryad_original_RF_gate")!="ORIGINAL_RF_PREDICTOR_INCOMPATIBLE"
        or result.get("historical_MH_ANTWERPEN_already_opened_and_excluded") is not True
        or result.get("actual_same_animal_under_different_IDs_not_excluded") is not True
        or result.get("v1_contract_sha256")!=p["contract_sha256"]
        or result.get("v2_contract_sha256")!=v["contract_sha256"]
        or result.get("raw_animal_tag_IDs_in_result") is not False
    ):
        raise ValueError("source-only admission, evidence role or original schema HOLD was promoted")
    studies=result.get("studies")
    if (
        not isinstance(studies,list) or len(studies)!=2
        or [x.get("study") for x in studies]!=["MH_WATERLAND","H_GRONINGEN"]
    ):
        raise ValueError("first official sources/order altered")
    for study in studies:
        name=study["study"]
        if (
            study.get("official_reference_md5_verified") is not True
            or study.get("reference_sha256")!=expected["source_sha256"][name]
            or study.get("reference_byte_count")!=expected["source_bytes"][name]
            or study.get("source_reference_rows")!=expected["reference_rows"][name]
            or study.get("unique_species_animals")!=expected["source_Circus_aeruginosus_individuals"][name]
            or study.get("unique_tag_identifiers")!=expected["distinct_tags"][name]
            or study.get("different_animals_sharing_a_tag_count")!=expected["tags_reused_between_different_animals"][name]
            or study.get("largest_number_of_animals_per_reused_tag")!=expected["max_animals_sharing_a_tag"][name]
            or study.get("one_study_can_supply_9_calibration_plus_1_validation") is not False
        ):
            raise ValueError("per-study reference animal/tag counts differ from first MD5-confirmed run")
    if (
        result.get("identical_animal_id_strings_shared_across_studies")!=expected["exact_ID_string_overlap_across_sources"]
        or result.get("identical_tag_id_strings_shared_across_studies")!=expected["exact_tag_string_overlap_across_sources"]
        or result.get("upper_bound_distinct_candidate_animals_by_exact_string")!=expected["optimistic_upper_bound_candidate_animals"]
        or result.get("within_study_rank_90pct_nonvacuous_any") is not False
        or result.get("hypothetical_pooled_count_at_least_10") is not True
        or result.get("study_cluster_count")!=expected["two_study_clusters"]
    ):
        raise ValueError("cross-study count-only result differs from first verified run")
    return {
        "first_source_only_artifact_replayed":True,
        "first_workflow_run":first["workflow_run_id"],
        "first_zip_sha256":first["artifact_zip_sha256"],
        "sources_MD5_verified":len(studies),
        "candidate_ID_string_upper_bound":expected["optimistic_upper_bound_candidate_animals"],
        "real_transmitter_reuse_found":True,
        "v1_terminal":"SOURCE_SCHEMA_HOLD",
        "v2_terminal":"REFERENCE_ID_AND_TAG_REUSE_AUDIT_ONLY",
        "external_prediction_admitted":False,
        "no_GPS_or_altitude_access":True,
    }


def main()->None:
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument("--result",type=Path,required=True)
    args=p.parse_args()
    raw=args.result.read_bytes()
    receipt=json.loads(RECEIPT.read_text(encoding="utf-8"))
    try:
        report=verify_two_marsh_first_result(json.loads(raw),receipt,exact_result_json_bytes=raw)
    except ValueError as err:
        raise SystemExit("original source-only outcome replay HOLD: "+str(err)) from err
    print(json.dumps(report,sort_keys=True))


if __name__=="__main__":
    main()
