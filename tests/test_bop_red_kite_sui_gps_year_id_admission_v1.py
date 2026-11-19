"""Known-truth Swiss 12-rule source admission with no breeding response access."""
from __future__ import annotations

from collections import Counter, defaultdict
from datetime import datetime, timedelta
import json
import pytest

from scripts.bop_red_kite_sui_gps_year_id_admission_v1 import (
    CONTRACT,_frozen,_parse_approved_GPS_line,collect_GPS_source,
    _three_counts,expected_shared_birds,summarize_all_12
)
from scripts.bop_nesttool_2024_yearid_animal_overlap_v1 import p_mixed

HEADER=b"event_id,bird_id,year_id,timestamp,year,month,day,long_wgs,lat_wgs,long_eea,lat_eea,external_temperature\r\n"

def row(event,bird,season,time,lon="7",lat="46",suffix="470000,120000,11"):
    # The suffix is never field-decoded by the source-only prefix scanner.
    return f"{event},{bird},{season},{time},2020,3,11,{lon},{lat},{suffix}\r\n".encode("utf-8")

def test_prospectively_frozen_swiss_source_and_no_response_columns():
    c,h=_frozen()
    assert c["frozen_date"]=="2026-11-19"
    assert c["source_zenodo_doi"]=="10.5281/zenodo.13736049"
    assert c["pinned_source_files"][1]["md5"]=="f654300e9a77b8dc41221f44d468ea2c"
    assert c["paper_population_claims"]["published_Swiss_eligible_seasons"]==697
    assert c["paper_population_claims"]["published_Swiss_eligible_birds"]==258
    assert c["paper_population_claims"]["frozen_Zenodo_metadata_seasons"]==2866
    assert c["paper_population_claims"]["frozen_Zenodo_metadata_bird_ID_strings"]==553
    assert c["read_protocol"]["metadata_outcome_columns_never_parsed_or_printed"] is True
    assert c["predeclared_eligibility"]["cannot_select_matching_arm_after_results"] is True
    assert c["predeclared_eligibility"]["primary_descriptive_arm"]=="fixed_2023_DOY_ordinal__unique_UTC_hour_bin__strict_gt_800"
    assert h["verified_first_header"]["SUI_trackingdata"]["column_names"][-1]=="external_temperature"

def test_restricted_prefix_parser_ignores_nonwhitelisted_suffix_even_if_private():
    raw=row(123,"birdA","Y2020A","2020-03-11 12:00:00",suffix="PRIVATE_BREEDING_OUTCOME,OTHER,TOXIC")
    bird,year,when,x,y=_parse_approved_GPS_line(raw)
    assert (bird,year,x,y)==("birdA","Y2020A",7.,46.)
    assert when==datetime(2020,3,11,12)
    with pytest.raises(ValueError):
        _parse_approved_GPS_line(row(123,'"birdA"',"Y2020A","2020-03-11 12:00:00"))

def test_known_truth_leap_year_ordinal_vs_calendar_and_row_rejection():
    src=[HEADER,
        row(1,"a","A","2020-03-10 12:00:00"), # DOY70, before calendar 11 March
        row(2,"a","A","2020-03-11 12:10:00"), # both date arms
        row(3,"b","B","2020-06-24 12:00:00"), # calendar only in leap year
        row(4,"a","A","2020-03-11 12:12:00",lon="3.5"), # outside
        row(5,"wrong","A","2020-03-11 12:12:00"), # mismatched bird/year; fail closed
    ]
    with pytest.raises(ValueError,match="not one-to-one"):
        collect_GPS_source(iter(src),HEADER,{"A":"a","B":"b"})
    src=src[:-1]+[row(6,"c","UNKNOWN","2020-03-11 12:12:00")]
    timeline,counts=collect_GPS_source(iter(src),HEADER,{"A":"a","B":"b"})
    assert counts["source_GPS_physical_rows"]==5
    assert counts["GPS_rows_from_unlisted_year_ID"]==1
    assert counts["GPS_rows_outside_strict_geobounds"]==1
    assert counts["GPS_rows_with_exact_metadata_year_bird_match"]==4
    assert counts["inseason_GPS_event_rows_by_date_arm"]=={
        "fixed_2023_DOY_ordinal":2,"actual_calendar_month_day":2
    }
    assert set(timeline["fixed_2023_DOY_ordinal"])=={"A"}
    assert set(timeline["actual_calendar_month_day"])=={"A","B"}
    public=json.dumps(counts)
    assert "2020-03" not in public and "birdA" not in public and "UNKNOWN" not in public

def test_three_prespecified_source_sampling_counts():
    base=1600000000
    times=[base,base+25*60,base+58*60,base+61*60,base+85*60]
    result=_three_counts(times)
    assert result["observed_source_events"]==5
    assert result["unique_UTC_hour_bin"] in (2,3)  # exact UTC-hour edges may differ
    assert result["rolling_3600_seconds"]==2
    assert result["unique_UTC_hour_bin"]==len({x//3600 for x in times})

def test_fixed_twelfth_grid_uses_animal_bird_histograms_and_source_expected_overlap():
    t={k:defaultdict(list) for k in ("fixed_2023_DOY_ordinal","actual_calendar_month_day")}
    for date in t:
        t[date]["a1"]=[100000000+3600*i for i in range(3)]
        t[date]["a2"]=[100000000+3600*i for i in range(3)]
        t[date]["b1"]=[100000000+3600*i for i in range(2)]
        t[date]["c1"]=[100000000+3600*i for i in range(3)]
    meta={"a1":"A","a2":"A","b1":"B","c1":"C"}
    arms=summarize_all_12(t,meta,cutoff=2)
    assert len(arms)==12 and len({a["arm"] for a in arms})==12
    a=next(x for x in arms if x["arm"]=="fixed_2023_DOY_ordinal__observed_source_events__inclusive_ge_800")
    assert a["eligible_year_ID_strings"]==4
    assert a["distinct_bird_ID_strings"]==3
    assert a["bird_seasons_per_bird_histogram"]=={"1":2,"2":1}
    assert a["birds_with_multiple_eligible_seasons"]==1
    assert a["hypothetical_uniform_year_split_training_seasons"]==3
    assert a["expected_bird_ID_strings_in_both_split_roles"]==pytest.approx(
        p_mixed(2,4,3),abs=1e-6)
    for x in arms:
        assert x["matches_both_published_697_seasons_258_birds_numerically"] is False
        assert x["published_2024_real_split_and_bird_authentication_not_verified"] is True
        assert "a1" not in json.dumps(x) and "birdA" not in json.dumps(x)

def test_strict_800_vs_inclusive_800_uses_same_precommitted_arm_names():
    times=[datetime(2021,5,1,0)+timedelta(minutes=30*i) for i in range(800)]
    ts=[int(t.timestamp()) for t in times]
    a={date:{"a":ts} for date in ("fixed_2023_DOY_ordinal","actual_calendar_month_day")}
    arms=summarize_all_12(a,{"a":"BIRD"},cutoff=800)
    find={x["arm"]:x["eligible_year_ID_strings"] for x in arms}
    assert find["fixed_2023_DOY_ordinal__observed_source_events__inclusive_ge_800"]==1
    assert find["fixed_2023_DOY_ordinal__observed_source_events__strict_gt_800"]==0

def test_expected_shared_birds_refuses_bad_group_population():
    assert expected_shared_birds(Counter({1:2,2:1}),4,3)==pytest.approx(p_mixed(2,4,3))
    with pytest.raises(ValueError):
        expected_shared_birds(Counter({1:1}),4,3)
