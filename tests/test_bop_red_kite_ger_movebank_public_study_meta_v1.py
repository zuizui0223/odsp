"""Offline tests for anonymous, source-only Movebank red-kite study summary."""
from __future__ import annotations
from copy import deepcopy
import json
import pytest
from scripts.bop_red_kite_ger_movebank_public_study_meta_v1 import (
    CONTRACT,ALLOWED_URL,load_frozen,classify_response,
)

def sample_response(study_id="294443150",name="Red Kites (Milvus milvus) in Saxony-Anhalt"):
    # Fake Movebank study response with private-like contact fields that must
    # NEVER appear in any JSON receipt or printed output.
    return (
        "id,name,number_of_individuals,number_of_deployments,number_of_tags,"
        "number_of_deployed_locations,i_can_see_data,i_have_download_access,"
        "there_are_data_which_i_cannot_see,principal_investigator_email\n"
        f"{study_id},{name},123,124,120,55555,true,false,true,private@example.org\n"
    ).encode("utf-8")

def test_frozen_anonymous_one_study_only_contract():
    c=load_frozen()
    assert c["paper"]["Movebank_study_ids_as_published"]==[230545451,1356790386,294443150]
    assert c["narrow_source"]["url"]==ALLOWED_URL
    assert c["narrow_source"]["study_id"]==294443150
    assert c["narrow_source"]["account_authentication"]=="NONE"
    assert c["safety"]["no_GPS_or_other_event_data"] is True
    assert c["safety"]["no_individual_reference_data"] is True
    assert c["safety"]["no_accepting_licence_or_terms_on_behalf_of_user"] is True
    assert c["decisions"]["never_reclassify_fixed_source_99_49_as_99_63"] is True

def test_one_current_public_study_emits_only_safe_summary_fields():
    c=load_frozen()
    obj=classify_response(sample_response(),200,ALLOWED_URL,c)
    assert obj["status"]=="CURRENT_MOVEBANK_STUDY_METADATA_ONLY"
    assert obj["current_total_provider_individuals"]==123
    assert obj["current_total_provider_deployments"]==124
    assert obj["current_total_provider_tags"]==120
    assert obj["current_total_provider_locations"]==55555
    assert obj["public_can_view"] is True
    assert obj["anonymous_download_access"] is False
    assert obj["public_data_may_be_partial"] is True
    assert obj["historical_99_63_eligible_birds_verified"] is False
    assert obj["entire_GER_163_65_original_paper_roster_verified"] is False
    assert obj["individual_tag_deployment_or_event_rows_accessed"] is False
    assert obj["archived_GER_99_season_49_bird_ID_result_unchanged"] is True
    out=json.dumps(obj)
    assert "private@example.org" not in out
    assert "principal_investigator_email" not in out
    assert "Red Kites (Milvus" not in out

def test_refuse_outcome_or_event_endpoint_even_for_same_study_id():
    c=load_frozen()
    for url in [
        ALLOWED_URL.replace("entity_type=study","entity_type=event"),
        ALLOWED_URL.replace("entity_type=study","entity_type=individual"),
        ALLOWED_URL.replace("294443150","294443151"),
    ]:
        with pytest.raises(ValueError,match="disallowed"):
            classify_response(sample_response(),200,url,c)

@pytest.mark.parametrize("body,reason",[
    (b"<p>No data available.</p><p>Please contact the data owner for permission</p>",
     "PROVIDER_PERMISSION_OR_TERMS"),
    (b"The requested download may contain copyrighted material. License Terms:",
     "PROVIDER_PERMISSION_OR_TERMS"),
    (b"<html><body>Not permitted</body></html>","NOT_PUBLIC_CSV"),
])
def test_denied_or_licence_terms_are_source_hold(body,reason):
    c=load_frozen()
    obj=classify_response(body,200,ALLOWED_URL,c)
    assert obj["status"]=="STUDY_METADATA_ACCESS_HOLD"
    assert obj["reason"]==reason
    assert obj["historical_99_63_eligible_birds_verified"] is False

def test_http_non200_is_hold_without_guessing_study_count():
    c=load_frozen()
    obj=classify_response(b"Unauthorized",401,ALLOWED_URL,c)
    assert obj["status"]=="STUDY_METADATA_ACCESS_HOLD"
    assert obj["reason"]=="HTTP_NON_200"
    assert "current_total_provider_individuals" not in obj

@pytest.mark.parametrize("body",[
    sample_response(study_id="294443151"),
    sample_response(name="Other study"),
    b"id,name,number_of_individuals\n",
    b"",
    b"id,name\n294443150,Red Kites\n294443150,Red Kites\n",
    b"<p>Strange provider error</p>",
])
def test_missing_wrong_schema_or_study_id_fails_closed(body):
    c=load_frozen()
    obj=classify_response(body,200,ALLOWED_URL,c)
    assert obj["status"]!="CURRENT_MOVEBANK_STUDY_METADATA_ONLY"
    assert obj["historical_99_63_eligible_birds_verified"] is False

def test_large_provider_payload_rejected_before_csv_parse():
    c=load_frozen()
    with pytest.raises(ValueError,match="too large"):
        classify_response(b"x"*65537,200,ALLOWED_URL,c)
