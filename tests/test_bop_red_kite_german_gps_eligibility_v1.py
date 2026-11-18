"""Known-truth pure-python tests for a fixed 12-arm German GPS eligibility screen."""
from __future__ import annotations
from collections import defaultdict
from datetime import datetime
import hashlib
import json

import pytest

from scripts.bop_red_kite_german_gps_eligibility_v1 import (
    CONTRACT,HEADERS,DATES,THIN,MINIMUM,_frozen,_timestamp,selected_dates,
    thinning_counts,aggregate_arms,audit_gps_rows,
)

HEAD=b"year_id,bird_id,timestamp,long_wgs,lat_wgs,long_eea,lat_eea\r\n"
HEADER_SHA=hashlib.sha256(HEAD).hexdigest()


def test_preaccess_fixed_grid_cannot_promote_published_99_63():
    contract,header=_frozen()
    assert contract["frozen_date"]=="2026-11-18"
    assert contract["input_sources"][0]["bytes"]==53471439
    assert contract["input_sources"][0]["md5"]=="ec5dd057fc6d704a09f15bbbffe00129"
    assert contract["interpretation"]["source_meta_159_63_not_fully_equivalent_to_paper_input"] is True
    assert contract["interpretation"]["paper_German_outcomes_already_published"] is True
    assert contract["frozen_filters"]["all_12_arm_results_reported_even_if_no_match"] is True
    assert contract["frozen_filters"]["primary_a_priori"]=="fixed_2023_DOY_ordinal__observed_source_events__strict_gt_800"
    assert len(DATES)*len(THIN)*len(MINIMUM)==12
    assert header["critical_limits"]["no_GPS_event_values_parsed"] is True

def test_2023_fixed_ordinal_separates_calendar_on_leap_years():
    # 2020 March 14 is DOY 74 (R fixed-2023 yday lower bound) but before calendar March 15.
    v=selected_dates(datetime(2020,3,14,12))
    assert v["fixed_2023_DOY_ordinal"] is True
    assert v["actual_calendar_month_day"] is False
    w=selected_dates(datetime(2020,3,15,12))
    assert w["fixed_2023_DOY_ordinal"] is True
    assert w["actual_calendar_month_day"] is True
    assert _timestamp("2020-03-15T12:00:00Z")==datetime(2020,3,15,12)
    assert _timestamp("2020-03-15 12:00:00")==datetime(2020,3,15,12)

def test_thinning_arms_compare_source_hours_and_rolling_elapsed():
    times=[datetime(2019,5,1,12,0),datetime(2019,5,1,12,25),
           datetime(2019,5,1,12,58),datetime(2019,5,1,13,1),
           datetime(2019,5,1,13,25)]
    c=thinning_counts(times)
    assert c=={"observed_source_events":5,"unique_utc_hour_bin":2,"rolling_3600_seconds":2}

def test_full_grid_all_12_reported_even_if_none_matches_paper():
    d=defaultdict(list)
    d["a"]=[datetime(2021,4,1,10),datetime(2021,4,1,10,15),datetime(2021,4,1,12)]
    d["b"]=[datetime(2021,4,2,10),datetime(2021,4,2,11)]
    obs=aggregate_arms({arm:d for arm in DATES},{"a":"birdA","b":"birdB"},threshold=2)
    assert len(obs)==12
    assert len({row["arm"] for row in obs})==12
    by={row["arm"]:row for row in obs}
    assert by["fixed_2023_DOY_ordinal__observed_source_events__strict_gt_800"]["eligible_seasons"]==1
    assert by["fixed_2023_DOY_ordinal__observed_source_events__inclusive_ge_800"]["eligible_seasons"]==2
    assert by["fixed_2023_DOY_ordinal__unique_utc_hour_bin__strict_gt_800"]["eligible_seasons"]==0
    assert all(x["matches_paper_99_63_numbers_only"] is False for x in obs)
    assert all(x["not_formal_replication_even_if_matches"] is True for x in obs)

def test_gps_raw_bytes_are_collapsed_to_aggregates_without_positions_or_ID_strings():
    def row(year,bird,t,lon,lat):
        return f"{year},{bird},{t},{lon},{lat},4000000,3400000\r\n".encode()
    raw=[
        HEAD,
        row("yrA","ID-A","2021-05-04 12:00:00",11.3,51.6),
        row("yrA","ID-A","2021-05-04 12:10:00",11.4,51.6),
        row("yrA","ID-A","2021-05-04 13:20:00",11.5,51.9),
        row("yrB","ID-B","2021-05-04 12:00:00",8.9,51.6),
        row("yrB","ID-B","2021-05-04 13:00:00",11.0,51.6),
        row("yrOther","ID-OTHER","2021-05-04 14:00:00",11.3,51.6),
        row("yrA","ID-A","2021-10-04 15:00:00",11.3,51.6),
    ]
    result=audit_gps_rows(raw,["year_id","bird_id","timestamp","long_wgs","lat_wgs","long_eea","lat_eea"],HEADER_SHA,{"yrA","yrB"},{"ID-A","ID-B"},threshold=2)
    assert result["raw_GPS_physical_record_lines"]==7
    assert result["records_unlinked_to_pinned_German_metadata"]==1
    assert result["linked_GPS_rows_outside_geo_bounds"]==1
    assert result["linked_geographic_season_rows_by_rule"]["actual_calendar_month_day"]==4
    assert len(result["all_12_prespecified_eligibility_arms"])==12
    encoded=json.dumps(result)
    for term in ["ID-A","ID-B","yrA","yrB","11.3","51.6","2021-05-04","4000000"]:
        assert term not in encoded

def test_invalid_time_missing_coordinate_or_header_tamper():
    base=[HEAD,b"yrA,ID-A,BAD_TIMESTAMP,11.3,51.6,5,6\r\n"]
    x=audit_gps_rows(base,["year_id","bird_id","timestamp","long_wgs","lat_wgs","long_eea","lat_eea"],HEADER_SHA,{"yrA"},{"ID-A"},2)
    assert x["malformed_or_missing_GPS_fields"]==1
    with pytest.raises(ValueError,match="header"):
        audit_gps_rows([HEAD.replace(b"bird_id",b"tag_id")],["year_id","bird_id","timestamp","long_wgs","lat_wgs","long_eea","lat_eea"],HEADER_SHA,{"yrA"},{"ID-A"},2)

def test_year_id_reused_across_bird_strings_stops():
    lines=[HEAD,
           b"yrA,ID-A,2021-05-04 12:00:00,11.0,51.0,5,6\r\n",
           b"yrA,ID-B,2021-05-04 14:00:00,11.1,51.1,5,6\r\n"]
    with pytest.raises(ValueError,match="multiple bird"):
        audit_gps_rows(lines,["year_id","bird_id","timestamp","long_wgs","lat_wgs","long_eea","lat_eea"],HEADER_SHA,{"yrA"},{"ID-A","ID-B"},2)
