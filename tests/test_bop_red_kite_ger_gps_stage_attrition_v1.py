"""Known-truth fixed German GPS attrition funnel without source data."""
from __future__ import annotations
import json
import pytest
from scripts.bop_red_kite_ger_gps_stage_attrition_v1 import _fixed,summarize_stages

HEADER=b"year_id,bird_id,timestamp,long_wgs,lat_wgs,long_eea,lat_eea\r\n"

def r(y,b,t,lon="11.3",lat="51.5"):
    return f"{y},{b},{t},{lon},{lat},444,333\r\n".encode()

def test_frozen_original_source_and_no_outcome_boundary():
    c,h,first=_fixed()
    assert c["frozen_date"]=="2026-11-18"
    assert c["method"]["fixes_minimum"]=="strictly_more_than_800_events_before_any_new_hourly_thinning"
    assert c["method"]["no_raw_ID_or_ID_hash_or_lat_lon_or_timestamp_in_output"] is True
    assert c["authorized_source_files"][0]["projection"]==["year_id","bird_id"]
    assert c["authorized_source_files"][1]["md5"]=="ec5dd057fc6d704a09f15bbbffe00129"
    assert first["observed_source"]["all_12_fixed_arms"][0][1:]==[99,49]

def test_funnel_reports_four_distinct_source_drop_steps_without_identifiers():
    records=[HEADER]
    records.extend(r("yearA","birdA","2021-05-05 11:00:00") for _ in range(801))
    records.append(r("yearB","birdB","2021-05-05 12:00:00",lon="8.8"))
    records.append(r("unknown","birdC","2021-05-05 12:00:00"))
    records.append(r("yearB","WRONG_BIRD","2021-05-05 12:00:00"))
    out=summarize_stages({"yearA":"birdA","yearB":"birdB","yearC":"birdC"},iter(records),HEADER)
    assert out["input_GPS_physical_lines"]==804
    assert out["unknown_GPS_year_ID_rows"]==1
    assert out["GPS_year_ID_with_different_bird_ID_rows"]==1
    assert out["linked_valid_GPS_rows"]==802
    assert [x["season_ID_strings"] for x in out["source_stage_funnel"]]==[3,2,1,1,1]
    assert [x["bird_ID_strings"] for x in out["source_stage_funnel"]]==[3,2,1,1,1]
    assert out["source_stage_funnel"][1]["birds_lost_from_previous_stage"]==1
    assert out["source_stage_funnel"][2]["birds_lost_from_previous_stage"]==1
    assert out["source_primary_99_seasons_49_bird_strings_rechecked"] is False
    encoded=json.dumps(out)
    for value in ("yearA","birdB","WRONG_BIRD","2021-05","11.3","51.5"):
        assert value not in encoded

def test_paper_800_boundary_does_not_get_changed_posthoc():
    rows=[HEADER]+[r("yr","b","2021-05-04 12:00:00") for _ in range(800)]
    out=summarize_stages({"yr":"b"},iter(rows),HEADER)
    assert out["source_stage_funnel"][3]["season_ID_strings"]==1
    assert out["source_stage_funnel"][4]["season_ID_strings"]==0
    assert out["source_stage_funnel"][4]["birds_lost_from_previous_stage"]==1

def test_mismatched_header_fails_before_any_records():
    with pytest.raises(ValueError,match="header"):
        summarize_stages({"y":"b"},iter([HEADER.replace(b"year_id",b"track_id")]),HEADER)

def test_ordinal_and_geographic_filter_are_cumulative():
    rows=[HEADER,
        r("yr1","b1","2020-03-14 12:00:00"),
        r("yr2","b2","2020-03-13 12:00:00"),
        r("yr3","b3","2020-03-15 12:00:00",lon="8.5"),
    ]
    out=summarize_stages({"yr1":"b1","yr2":"b2","yr3":"b3"},iter(rows),HEADER)
    assert [x["season_ID_strings"] for x in out["source_stage_funnel"]][:4]==[3,3,2,1]
