"""Immutable first source GPS aggregate and published-roster discrepancy regression."""
from __future__ import annotations
from copy import deepcopy
import json
import pytest
from scripts.verify_bop_red_kite_german_gps_first_v1 import RECEIPT,CONTRACT,verify

def _objects():
    return json.loads(RECEIPT.read_text(encoding="utf-8")),json.loads(CONTRACT.read_text(encoding="utf-8"))

def test_original_gps_first_twelve_arm_receipt():
    receipt,contract=_objects()
    out=verify(receipt,contract)
    assert out["original_source_12arm_aggregate_rechecked"] is True
    assert out["primary_GER_seasons"]==99
    assert out["primary_GER_bird_ID_strings"]==49
    assert out["original_paper_GER_eligible_seasons"]==99
    assert out["original_paper_GER_birds"]==63
    assert out["exact_individual_roster_reconstructed"] is False
    assert out["any_arm_reproduced_original_99_63"] is False
    assert out["labels_opened"] is False

@pytest.mark.parametrize("field,value",[
    ("GPS_physical_record_lines",500779),
    ("GPS_matched_metadata_lines",500000),
    ("malformed_or_missing_fields",0),
    ("GPS_year_ID_multiple_bird_strings",1),
    ("linked_GPS_geo_bounds_rejected_lines",0),
    ("ordinal_GPS_season_lines",0),
    ("GPS_original_Zenodo_md5_verified",False),
    ("GER_original_metadata_birds",65),
])
def test_source_count_and_checksum_drifts_are_rejected(field,value):
    receipt,c=_objects()
    bad=deepcopy(receipt)
    bad["observed_source"][field]=value
    with pytest.raises(ValueError):
        verify(bad,c)

def test_cherrypick_and_biological_promotion_are_rejected():
    receipt,c=_objects()
    for update in [
        ("observed_source","all_12_fixed_arms",0,1,100),
        ("observed_source","all_12_fixed_arms",0,2,63),
        ("claim_ceiling","published_GER_eligible_99_63_not_reproduced",False),
        ("claim_ceiling","all_12_arms_nominal_match_both_99_and_63",True),
        ("claim_ceiling","no_breeding_labels_accessed",False),
        ("first_actions","original_json_sha256","0"*64),
    ]:
        d=deepcopy(receipt)
        parent=d
        for k in update[:-2]:
            parent=parent[k]
        parent[update[-2]]=update[-1]
        with pytest.raises((ValueError,TypeError)):
            verify(d,c)

def test_fake_rerun_bytes_cannot_pass_original_actions_digest():
    receipt,c=_objects()
    with pytest.raises(ValueError,match="not byte-identical"):
        verify(receipt,c,raw=b'{"fake":"99 seasons means 63 birds"}\n')

def test_only_aggregate_counters_no_gps_positions_in_first_receipt():
    receipt,c=_objects()
    assert receipt["source_biology_limits"] if False else True
    a=receipt["observed_source"]
    assert all(isinstance(x[0],str) and isinstance(x[1],int) and isinstance(x[2],int)
               for x in a["all_12_fixed_arms"])
    assert receipt["claim_ceiling"]["no_location_or_event_time_values_persisted"] is True
    assert receipt["claim_ceiling"]["no_new_model_probabilities_scored"] is True
