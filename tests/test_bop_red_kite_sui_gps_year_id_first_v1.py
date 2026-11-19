"""Immutable official Swiss source 697/258 row/animal histogram tests."""
from __future__ import annotations

from copy import deepcopy
import json
import pytest

from scripts.verify_bop_red_kite_sui_gps_year_id_first_v1 import (
    CONTRACT,RECEIPT,verify_first,EXPECTED_COUNTS,PRIMARY_HIST,
)

def load():
    return json.loads(RECEIPT.read_text(encoding="utf-8")),json.loads(CONTRACT.read_text(encoding="utf-8"))

def test_original_provider_MD5_and_real_source_bird_histogram_agree():
    r,c=load()
    result=verify_first(r,c)
    assert result["original_first_source_checked"] is True
    assert result["first_run_id"]==44456757144
    assert result["first_artifact_id"]==14498950985
    assert result["Swiss_source_paper_matching_seasons"]==697
    assert result["Swiss_source_paper_matching_bird_ID_strings"]==258
    assert result["Swiss_source_two_or_more_season_bird_ID_strings"]==192
    assert result["conditional_expected_bird_ID_strings_in_both_uniform_488_209_roles"]==121.992374
    assert result["no_actual_2024_split_or_model_scores_recovered"] is True
    assert r["summary"]["primary_source_multiplicity"]==PRIMARY_HIST
    assert sum(PRIMARY_HIST.values())==258
    assert sum(int(k)*v for k,v in PRIMARY_HIST.items())==697
    assert r["first_actions"]["original_JSON_bytes"]==10573

@pytest.mark.parametrize("path,value",[
    (("first_actions","run_id"),1),
    (("first_actions","original_JSON_sha256"),"0"*64),
    (("first_actions","original_artifact_ZIP_sha256"),"0"*64),
    (("first_actions","frozen_contract_sha256"),"0"*64),
    (("summary","primary_eligible_year_ID_strings"),698),
    (("summary","primary_eligible_bird_ID_strings"),259),
    (("summary","primary_source_multiplicity","3"),61),
    (("summary","primary_bird_ID_strings_with_two_or_more_years"),190),
    (("summary","expected_bird_ID_strings_both_roles_under_hypothetical_uniform_488_209_year_split"),120),
    (("original_source_output","GPS_source_aggregate","malformed_GPS_rows"),1),
    (("original_source_output","GPS_source_aggregate","source_GPS_physical_rows"),2395532),
    (("original_source_output","twelve_fixed_eligibility_arms",4,"eligible_year_ID_strings"),697),
    (("original_source_output","twelve_fixed_eligibility_arms",2,"bird_seasons_per_bird_histogram","1"),65),
    (("original_source_output","twelve_fixed_eligibility_arms",2,"expected_bird_ID_strings_in_both_split_roles"),121),
    (("claim_limits","numeric_697_258_match_not_identity_crosswalk"),False),
    (("claim_limits","expected_overlap_not_actual_observed_overlap"),False),
    (("claim_limits","no_HR_nest_success_values_decoded"),False),
    (("claim_limits","no_model_retraining_or_accuracy_inflation_measured"),False),
    (("claim_limits","redkite_biological_terminal"),"GENERALIZING")
])
def test_source_receipt_tamper_and_overpromotion_rejected(path,value):
    r,c=load()
    bad=deepcopy(r)
    node=bad
    for key in path[:-1]:
        node=node[key]
    node[path[-1]]=value
    with pytest.raises(ValueError):
        verify_first(bad,c)

def test_original_source_grid_is_exactly_twelve_and_not_cherry_picked():
    r,c=load()
    a=r["original_source_output"]
    actual=[(x["arm"],x["eligible_year_ID_strings"],x["distinct_bird_ID_strings"]) for x in a["twelve_fixed_eligibility_arms"]]
    assert actual==EXPECTED_COUNTS
    assert sum(x["matches_both_published_697_seasons_258_birds_numerically"] for x in a["twelve_fixed_eligibility_arms"])==8
    assert a["no_posthoc_selection_of_matching_697_258"] is True
    assert a["paper_2024_training_roster_authenticated"] is False
    assert a["original_actual_2024_training_random_seed_observed"] is False
    assert a["no_label_or_GPS_source_individual_record_emitted"] is True

def test_fake_new_source_result_cannot_replace_sha256_of_first():
    r,c=load()
    with pytest.raises(ValueError,match="not byte-identical"):
        verify_first(r,c,raw=b'{"status":"SUI_SOURCE_12_ARM_QUALITY_COUNTS_ONLY"}\n')
