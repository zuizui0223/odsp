"""Offline tests for outcome-blind *prefix* identity-year projection."""
from __future__ import annotations
import hashlib
import json
from copy import deepcopy

import pytest

from scripts.bop_red_kite_raw_group_prefix_only_v1 import (
    CONTRACT, HEADERS, INVENTORY, _load_contract, project_prefix,
)

GER_HEADER=b"year_id,bird_id,sex,age_cy,HR,nest,success\r\n"
SUI_HEADER=b"bird_id,year,year_id,sex,age_cy,nest_id,home_range_id,success,nest,HR\r\n"

def _spec(content:bytes,source:str):
    if source=="GER":
        cols=["year_id","bird_id","sex","age_cy","HR","nest","success"]
        prefix=["year_id","bird_id"]
    else:
        cols=["bird_id","year","year_id","sex","age_cy","nest_id","home_range_id","success","nest","HR"]
        prefix=["bird_id","year","year_id"]
    return {
        "key":source+"_indseasondata.csv",
        "bytes":len(content),
        "md5":hashlib.md5(content).hexdigest(),
        "header_columns":cols,
        "allowed_prefix_columns":prefix,
    }

def _run(data:bytes,country:str="GER",chunk_size:int=8192):
    spec=_spec(data,country)
    header=GER_HEADER if country=="GER" else SUI_HEADER
    pieces=[data[i:i+chunk_size] for i in range(0,len(data),chunk_size)]
    return project_prefix(pieces,spec,hashlib.sha256(header).hexdigest())

def test_preaccess_contract_is_source_only_and_distinguishes_163_65_from_99_63():
    c,h=_load_contract()
    assert c["frozen_date"]=="2026-11-18"
    assert c["source_zenodo_doi"]=="10.5281/zenodo.13736049"
    assert c["access"]["no_GPS_files_or_tracking_events"] is True
    assert c["access"]["full_CSV_bytes_contain_real_outcomes_but_not_parsed_by_projection"] is True
    assert c["access"]["no_raw_or_hashed_bird_ID_or_year_ID_in_public_receipts"] is True
    assert c["interpretation"]["not_same_as_filtered_GER_group_roster"] is True
    assert c["interpretation"]["no_individual_GPS_eligibility_reproduced"] is True
    assert [f["key"] for f in c["input_files"]]==["GER_indseasondata.csv","SUI_indseasondata.csv"]
    assert "GER_trackingdata.csv" not in json.dumps(c["input_files"])
    assert h["critical_limits"]["no_GPS_event_values_parsed"] is True

@pytest.mark.parametrize("step",[1,2,3,7,43,8192])
def test_german_prefix_streaming_never_exports_ages_sex_or_nesting_labels(step):
    binary=(GER_HEADER+
            b"2011_b1,bird_alpha,m,5,yes,nest,success_yes\r\n"+
            b"2012_b1,bird_alpha,m,6,yes,nest,success_no\r\n"+
            b"2012_b2,bird_beta,f,4,no,no_nest,success_unknown\r\n")
    result,birds,years=_run(binary,"GER",step)
    assert result["source_full_file_md5_verified"] is True
    assert result["physical_record_lines"]==3
    assert result["distinct_bird_ID_strings"]==2
    assert result["distinct_year_ID_strings"]==3
    assert result["season_records_per_bird_histogram"]=={"1":1,"2":1}
    assert result["number_of_birds_with_multiple_season_records"]==1
    assert len(birds)==2 and len(years)==3
    output=json.dumps(result,sort_keys=True)
    for forbidden in ["bird_alpha","bird_beta","2012_b1","success_yes","success_no","no_nest","unknown"]:
        assert forbidden not in output

@pytest.mark.parametrize("step",[1,19,8192])
def test_swiss_three_leading_key_columns_are_only_parsed_fields(step):
    raw=(SUI_HEADER+
         b"bird_x,2012,2012_x,f,6,78,179,yes,nest,yes\r\n"+
         b"bird_x,2013,2013_x,f,7,78,179,no,nest,yes\r\n"+
         b"bird_y,2014,2014_y,m,9,12,13,no,no_nest,no\r\n")
    result,birds,years=_run(raw,"SUI",step)
    assert result["physical_record_lines"]==3
    assert result["distinct_bird_ID_strings"]==2
    assert result["distinct_year_ID_strings"]==3
    assert result["duplicate_year_ID_lines"]==0
    assert not any(v in json.dumps(result) for v in ("bird_x","bird_y","2013_x","no_nest"))

def test_full_file_md5_is_checked_even_though_outcome_bytes_are_not_decoded():
    raw=GER_HEADER+b"2019_z,bird_z,f,5,yes,nest,success_yes\n"
    good=_spec(raw,"GER")
    altered=raw.replace(b"success_yes",b"success_no!")
    with pytest.raises(ValueError,match="MD5"):
        project_prefix([altered],good,hashlib.sha256(GER_HEADER).hexdigest())

@pytest.mark.parametrize("body",[
    b"z1,bird_z,yes,nest,success\nz1,bird_z,yes,nest,success\n",
    b"z1,bird_z,yes,nest,success\nz1,bird_y,yes,nest,success\n",
])
def test_duplicated_year_keys_are_observed_and_must_force_scientific_hold(body):
    result,_,_=_run(GER_HEADER+body)
    assert result["duplicate_year_ID_lines"]==1
    if b"bird_y" in body:
        assert result["year_ID_to_multiple_bird_IDs"]==1

@pytest.mark.parametrize("prefix",[
    b"year_one,,m,5,nest,nest,yes\n",
    b"year_one,\"quoted_bird\",m,5,nest,nest,yes\n",
    b"year_one,m\n",
    b",bird_one,m,5,nest,nest,yes\n",
])
def test_bad_id_prefix_fails_closed(prefix):
    with pytest.raises(ValueError):
        _run(GER_HEADER+prefix)

def test_header_modification_or_missing_data_fails():
    with pytest.raises(ValueError,match="header"):
        _run(GER_HEADER.replace(b"bird_id",b"bird_tag")+b"year_one,bird_one,f,4,nest,nest,yes\n")
    with pytest.raises(ValueError,match="record"):
        _run(GER_HEADER)

def test_real_contract_cannot_be_mutated_in_its_whitelist():
    c,h=_load_contract()
    for f in c["input_files"]:
        assert f["md5"] and f["bytes"]>0
        assert f["allowed_prefix_columns"]==f["header_columns"][:len(f["allowed_prefix_columns"])]
        assert "success" not in f["allowed_prefix_columns"]
        assert "nest" not in f["allowed_prefix_columns"]
