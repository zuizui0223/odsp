"""Freeze the very first official source-only red-kite identity/year observation."""
from __future__ import annotations
from copy import deepcopy
import json
import pytest

from scripts.verify_bop_red_kite_raw_group_first_v1 import (
    RECEIPT,CONTRACT,verify_first,
)

def _objects():
    return (json.loads(RECEIPT.read_text(encoding="utf-8")),
            json.loads(CONTRACT.read_text(encoding="utf-8")))

def test_first_official_zip_json_checksum_and_counts_reproduce():
    receipt,contract=_objects()
    out=verify_first(receipt,contract)
    assert out["official_source_aggregate_reproduced"] is True
    assert out["first_run_id"]==44257226379
    assert out["official_artifact_id"]==14406462430
    assert out["GER_raw_metadata_seasons"]==159
    assert out["GER_raw_metadata_birds"]==63
    assert out["SUI_raw_metadata_seasons"]==2866
    assert out["SUI_raw_metadata_birds"]==553
    assert out["GPS_eligibility_reproduced"] is False
    assert out["nesting_outcomes_opened"] is False

@pytest.mark.parametrize("path,value",[
    (("original_source_output","sources",0,"distinct_bird_ID_strings"),65),
    (("original_source_output","sources",0,"physical_record_lines"),163),
    (("original_source_output","sources",1,"physical_record_lines"),697),
    (("original_source_output","sources",1,"source_full_file_md5_verified"),False),
    (("original_source_output","GPS_events_opened"),True),
    (("original_source_output","breeding_response_suffix_values_parsed"),True),
    (("original_source_output","status"),"VALIDATED_EXTERNAL_MODEL"),
    (("original_source_output","source_pair_bird_ID_exact_string_overlap"),2),
    (("first_actions","original_source_json_bytes"),2000),
    (("first_actions","original_artifact_zip_sha256"),"0"*64),
    (("source_biology_limits","published_GER_eligible_63_birds_99_seasons_not_reconstructed"),False),
])
def test_source_result_or_biological_promotion_tamper_fails(path,value):
    receipt,contract=_objects()
    x=deepcopy(receipt)
    cur=x
    for key in path[:-1]:
        cur=cur[key]
    cur[path[-1]]=value
    with pytest.raises(ValueError):
        verify_first(x,contract)

def test_rerun_drift_is_distinguished_from_original_result():
    receipt,contract=_objects()
    source=deepcopy(receipt["original_source_output"])
    source["sources"][0]["distinct_bird_ID_strings"]=64
    with pytest.raises(ValueError,match="not identical"):
        verify_first(receipt,contract,result=source)

def test_no_animal_ids_exposed_in_permanent_receipt():
    receipt,contract=_objects()
    source=receipt["original_source_output"]
    assert all(set(x)=={
        "source","source_full_file_md5_verified","source_bytes","physical_record_lines",
        "distinct_bird_ID_strings","distinct_year_ID_strings","duplicate_year_ID_lines",
        "year_ID_to_multiple_bird_IDs","number_of_birds_with_multiple_season_records",
        "max_season_records_per_bird","season_records_per_bird_histogram",
    } for x in source["sources"])
    assert source["source_pair_lexical_overlap_not_canonical_identity_proof"] is True
    assert receipt["source_biology_limits"]["no_breeding_labels_parsed"] is True
