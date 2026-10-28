"""Check original first Zenodo four CSV headers without any biological rows."""
from __future__ import annotations

from copy import deepcopy
import hashlib
import json

import pytest

from scripts.verify_bop_red_kite_header_first_result_v1 import (
    CONTRACT,RECEIPT,verify_first_header_only,
)


def _original_fields():
    rec=json.loads(RECEIPT.read_text(encoding="utf-8"))
    c=json.loads(CONTRACT.read_text(encoding="utf-8"))
    ordered=[
        rec["verified_first_header"][key]
        for key in ("GER_indseasondata","SUI_indseasondata",
                    "GER_trackingdata","SUI_trackingdata")
    ]
    fields=[
        {
            "file":row["filename"],
            "header_sha256":row["header_sha256"],
            "header_bytes_only":row["header_byte_length"],
            "HTTP_status":206,
            "columns":row["column_names"],
            "year_id_key_present":True,
            "candidate_animal_ID_field_aliases":["bird_id"],
            "candidate_outcome_field_names_only":(
                ["HR","nest","success"] if row["filename"].endswith("indseasondata.csv") else []
            ),
            "source_manifest_md5_string":next(
                f["source_manifest_md5"]
                for f in c["authorized_header_requests"] if f["key"]==row["filename"]
            ),
            "source_full_content_MD5_verified":False,
            "GPS_or_breeding_outcome_row_parsed":False,
        }
        for row in ordered
    ]
    o={
        "schema_version":1,
        "contract_id":c["contract_id"],
        "source_role":"OBSERVED_CSV_HEADERS_ONLY_NO_RESPONSES",
        "structural_header_status":"SOURCE_HEADERS_RECORDED_NO_FULL_DATA_ACCESS",
        "scientific_terminal":"HOLD_NO_FROZEN_NEW_NEST_STATE_MODEL_OR_IDENTITY_ROSTER",
        "all_four_sources_have_year_id":True,
        "individual_season_headers_have_candidate_animal_key":True,
        "per_animal_source_counts_verified":False,
        "outcome_values_parsed":False,
        "GPS_event_values_parsed":False,
        "source_file_content_MD5_verified":False,
        "published_German_bird_count_63_admitted":False,
        "real_external_probability_gain_scored":False,
        "original_BOP_terminal":"empirical_state_prediction_mixed",
        "header_fields":fields,
    }
    return o,rec,c


def test_original_first_header_record_and_scientific_stop_preserved():
    original,rec,c=_original_fields()
    p=verify_first_header_only(original,rec,c)
    assert p["original_first_header_schema_confirmed"] is True
    assert p["first_actions_run"]==40637728704
    assert p["source_headers"]==4
    assert p["German_individual_key"]==p["Swiss_individual_key"]=="bird_id"
    assert p["season_join_key"]=="year_id"
    assert p["nesting_outcome_header_present_both"] is True
    assert p["source_temperature_predictor_common"] is False
    assert p["real_biological_rows_scored"] is False
    assert rec["first_actions"]["artifact_id"]==12793992320
    assert rec["first_actions"]["original_header_JSON_bytes"]==4001
    assert rec["source_contract"]["preaccess_freeze_commit"]=="81cb2bc6816a4622d4d97a8328f4c967d04ec792"
    assert all(
        hashlib.sha256((",".join(row["column_names"])+"\r\n").encode()).hexdigest()==row["header_sha256"]
        for row in rec["verified_first_header"].values()
    )


@pytest.mark.parametrize("field,value,error",[
    ("outcome_values_parsed",True,"promoted"),
    ("GPS_event_values_parsed",True,"promoted"),
    ("real_external_probability_gain_scored",True,"promoted"),
    ("source_file_content_MD5_verified",True,"promoted"),
    ("published_German_bird_count_63_admitted",True,"promoted"),
    ("structural_header_status","FULL_PREDICTION_SUCCESS","promoted"),
    ("original_BOP_terminal","generalizing","promoted"),
])
def test_no_metadata_promotion_to_real_prediction(field,value,error):
    result,rec,c=_original_fields()
    result[field]=value
    with pytest.raises(ValueError,match=error):
        verify_first_header_only(result,rec,c)


def test_wrong_header_field_or_first_JSON_byte_hash_fails_closed():
    result,rec,c=_original_fields()
    result["header_fields"][0]["columns"][1]="fake_bird"
    with pytest.raises(ValueError,match="first-line schema differs"):
        verify_first_header_only(result,rec,c)
    original,rec,c=_original_fields()
    with pytest.raises(ValueError,match="not identical"):
        verify_first_header_only(original,rec,c,raw=b'{"fabricated":true}\n')


def test_published_values_are_not_exported():
    _,rec,_=_original_fields()
    alltext=json.dumps(rec)
    assert '"individual_years":' not in alltext
    assert '"bird_ids":' not in alltext
    assert '"nest_values":' not in alltext
    assert "HOLD_NO_FROZEN_NEW_NEST_STATE_MODEL_OR_IDENTITY_ROSTER" in alltext
    assert rec["critical_limits"]["no_GPS_event_values_parsed"] is True
    assert rec["critical_limits"]["no_individual_year_values_parsed"] is True
