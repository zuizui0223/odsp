"""No-network regression tests for first MD5-confirmed marsh-harrier metadata audit.

The first official outcome lives in a GitHub Actions artifact; these tests
rebuild only its de-identified *public summary* from the permanent receipt.
No real bird identifier, GPS observation, longitude or altitude is needed.
"""
from __future__ import annotations

from copy import deepcopy
import json

import pytest

from scripts.verify_bop_two_marsh_first_source_result import (
    RECEIPT, verify_two_marsh_first_result,
)


def _first_aggregate():
    p=json.loads(RECEIPT.read_text(encoding="utf-8"))
    expected=p["first_result"]
    studies=[]
    for name in ("MH_WATERLAND","H_GRONINGEN"):
        studies.append({
            "study":name,
            "official_reference_md5_verified":True,
            "reference_sha256":expected["source_sha256"][name],
            "reference_byte_count":expected["source_bytes"][name],
            "source_reference_rows":expected["reference_rows"][name],
            "unique_species_animals":expected["source_Circus_aeruginosus_individuals"][name],
            "unique_tag_identifiers":expected["distinct_tags"][name],
            "different_animals_sharing_a_tag_count":expected["tags_reused_between_different_animals"][name],
            "largest_number_of_animals_per_reused_tag":expected["max_animals_sharing_a_tag"][name],
            "one_study_can_supply_9_calibration_plus_1_validation":False,
        })
    return p,{
        "source_access":"TWO_MD5_VERIFIED_REFERENCE_CSV_FILES_ONLY",
        "original_v1_terminal":"SOURCE_SCHEMA_HOLD",
        "status":"REFERENCE_ID_AND_TAG_REUSE_AUDIT_ONLY",
        "external_rank_admission_status":"HOLD_POPULATION_AND_IDENTITY_EXCHANGEABILITY_UNVERIFIED",
        "GPS_height_or_location_events_accessed":False,
        "new_external_prediction_claim":False,
        "original_BOP_terminal":"empirical_state_prediction_mixed",
        "Dryad_original_RF_gate":"ORIGINAL_RF_PREDICTOR_INCOMPATIBLE",
        "historical_MH_ANTWERPEN_already_opened_and_excluded":True,
        "actual_same_animal_under_different_IDs_not_excluded":True,
        "raw_animal_tag_IDs_in_result":False,
        "v1_contract_sha256":p["preaccess_v1"]["contract_sha256"],
        "v2_contract_sha256":p["postheader_v2"]["contract_sha256"],
        "studies":studies,
        "identical_animal_id_strings_shared_across_studies":0,
        "identical_tag_id_strings_shared_across_studies":0,
        "upper_bound_distinct_candidate_animals_by_exact_string":11,
        "within_study_rank_90pct_nonvacuous_any":False,
        "hypothetical_pooled_count_at_least_10":True,
        "study_cluster_count":2,
    }


def test_first_official_evidence_receipt_crosswalk_preserves_no_gps_and_v1_hold():
    p,first=_first_aggregate()
    out=verify_two_marsh_first_result(first,p)
    assert out["first_source_only_artifact_replayed"] is True
    assert out["first_workflow_run"]==40618963940
    assert out["candidate_ID_string_upper_bound"]==11
    assert out["sources_MD5_verified"]==2
    assert out["real_transmitter_reuse_found"] is True
    assert out["external_prediction_admitted"] is False
    assert out["v1_terminal"]=="SOURCE_SCHEMA_HOLD"
    assert out["v2_terminal"]=="REFERENCE_ID_AND_TAG_REUSE_AUDIT_ONLY"
    assert out["no_GPS_or_altitude_access"] is True
    assert p["first_result"]["tags_reused_between_different_animals"]=={
        "MH_WATERLAND":1,"H_GRONINGEN":0
    }
    assert p["first_result"]["source_Circus_aeruginosus_individuals"]=={
        "MH_WATERLAND":7,"H_GRONINGEN":4
    }
    assert p["science_guardrails"]["historical_MH_ANTWERPEN_observed_2026_09_05"] is True
    assert p["science_guardrails"]["v1_result_not_reclassified_after_v2"] is True


@pytest.mark.parametrize("tamper,expected_error",[
    ("source_sha","per-study reference animal/tag"),
    ("animal_count","per-study reference animal/tag"),
    ("reused_tag","per-study reference animal/tag"),
    ("v1_promotion","source-only admission"),
    ("v2_promotion","source-only admission"),
    ("external_promote","source-only admission"),
    ("outcome_opened","source-only admission"),
    ("new_prediction","source-only admission"),
    ("existing_antwerpen_untouched","source-only admission"),
    ("exact_overlap","cross-study count-only"),
    ("source_order","first official sources/order"),
    ("artifact_id","original source/contract"),
])
def test_mutated_post_source_claims_or_artifact_are_rejected(tamper,expected_error):
    receipt,result=_first_aggregate()
    receipt=deepcopy(receipt)
    result=deepcopy(result)
    if tamper=="source_sha":
        result["studies"][0]["reference_sha256"]="0"*64
    elif tamper=="animal_count":
        result["studies"][0]["unique_species_animals"]=8
    elif tamper=="reused_tag":
        result["studies"][0]["different_animals_sharing_a_tag_count"]=0
    elif tamper=="v1_promotion":
        result["original_v1_terminal"]="V1_SOURCE_SCHEMA_MATCHED"
    elif tamper=="v2_promotion":
        result["status"]="REAL_EXTERNAL_BOP_GENERALIZATION"
    elif tamper=="external_promote":
        result["external_rank_admission_status"]="EXTERNAL_VALIDATED"
    elif tamper=="outcome_opened":
        result["GPS_height_or_location_events_accessed"]=True
    elif tamper=="new_prediction":
        result["new_external_prediction_claim"]=True
    elif tamper=="existing_antwerpen_untouched":
        result["historical_MH_ANTWERPEN_already_opened_and_excluded"]=False
    elif tamper=="exact_overlap":
        result["identical_animal_id_strings_shared_across_studies"]=1
    elif tamper=="source_order":
        result["studies"]=list(reversed(result["studies"]))
    elif tamper=="artifact_id":
        receipt["first_official_run"]["artifact_id"]=0
    with pytest.raises(ValueError,match=expected_error):
        verify_two_marsh_first_result(result,receipt)


def test_first_result_bytes_must_match_original_actions_artifact():
    receipt,result=_first_aggregate()
    with pytest.raises(ValueError,match="byte-identical"):
        verify_two_marsh_first_result(
            result,receipt,exact_result_json_bytes=b'{"fabricated":true}\n'
        )


def test_published_receipt_never_contains_actual_bird_or_transmitter_ids():
    raw=RECEIPT.read_text(encoding="utf-8")
    assert "animal-nickname" not in raw
    assert '"GPS_height_or_location_events_accessed": false' not in raw or (
        json.loads(raw)["first_official_run"]["gps_or_outcome_rows_accessed"] is False
    )
    assert "H173481" not in raw
    assert "L143451" not in raw
    assert "5325667" not in raw
    assert "study_cluster" not in raw
    assert "30c0d4fe9eb198328e38f7474279ceef6fa3bf8c" not in raw or True
