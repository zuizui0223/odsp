"""Original first official German source attrition: counts-only immutability."""
from __future__ import annotations
from copy import deepcopy
import json
import pytest
from scripts.verify_bop_red_kite_ger_gps_stage_first_v1 import RECEIPT,CONTRACT,verify

def _objects():
    return json.loads(RECEIPT.read_text(encoding="utf-8")),json.loads(CONTRACT.read_text(encoding="utf-8"))

def test_first_funnel_provenance_and_60_14_stage_loss_are_immutable():
    r,c=_objects()
    out=verify(r,c)
    assert out["original_source_five_stages_verified"] is True
    assert out["pre_800fix_seasons"]==159
    assert out["pre_800fix_birds"]==63
    assert out["eligible_seasons"]==99
    assert out["eligible_birds"]==49
    assert out["seasons_lost_at_fix_threshold"]==60
    assert out["birds_lost_at_fix_threshold"]==14
    assert out["paper_99_63_reconciled"] is False

@pytest.mark.parametrize("path,value",[
    (("observed_first","stages",4,2),63),
    (("observed_first","stages",4,3),0),
    (("observed_first","stages",3,2),49),
    (("observed_first","metadata_year_bird_mismatch_rows"),5),
    (("observed_first","full_provider_MD5s_verified"),False),
    (("scientific_limits","no_nest_HR_success_values_accessed"),False),
    (("scientific_limits","exact_cause_of_publication_sample_count_mismatch_unresolved"),False),
    (("first_official","json_sha256"),"0"*64),
])
def test_false_promotion_or_source_tampering_rejected(path,value):
    r,c=_objects()
    v=deepcopy(r)
    node=v
    for k in path[:-2]:
        node=node[k]
    node[path[-2]]=value
    with pytest.raises((ValueError,TypeError)):
        verify(v,c)

def test_fake_rerun_cannot_match_archived_sha():
    r,c=_objects()
    with pytest.raises(ValueError,match="not byte-identical"):
        verify(r,c,raw=b'{"pretend":"all 63 eligible"}\n')

def test_receipt_contains_only_predeclared_count_labels():
    r,c=_objects()
    a=r["observed_first"]
    assert a["stage_columns"]==["stage","seasons","bird_ID_strings","seasons_lost","bird_ID_strings_lost"]
    assert all(len(row)==5 for row in a["stages"])
    assert r["scientific_limits"]["no_raw_or_hashed_bird_year_ID_exported"] is True
