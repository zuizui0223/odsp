"""No outcome/GPS output and prespecified German source time-gap bin tests."""
from __future__ import annotations
from datetime import datetime,timedelta
import json
import pytest

from scripts.bop_red_kite_ger_gps_cadence_v1 import (
    CONTRACT,_frozen,read_geo_season_GPS,summarize_intervals,
)

HEADER=b"year_id,bird_id,timestamp,long_wgs,lat_wgs,long_eea,lat_eea\r\n"

def test_frozen_source_whitelist_and_original_99_49_group_boundary():
    c,h=_frozen()
    assert c["frozen_date"]=="2026-11-18"
    assert c["predeclared_source_screen"]["require_original_500778_source_GPS_rows_and_full_MD5"] is True
    assert c["predeclared_source_screen"]["require_exact_metadata_year_to_bird_mapping"] is True
    assert c["source_files"][0]["allowed_fields"]==["year_id","bird_id"]
    assert c["source_files"][1]["md5"]=="ec5dd057fc6d704a09f15bbbffe00129"
    assert c["biological_interpretation"]["original_downsampling_algorithm_not_proven"] is True
    assert c["biological_interpretation"]["red_kite_biological_terminal"]=="HOLD_NO_FROZEN_NEW_NEST_STATE_MODEL_OR_IDENTITY_ROSTER"
    assert h["critical_limits"]["no_GPS_event_values_parsed"] is True

def test_time_interval_bins_keep_subhourly_and_hourly_both():
    c,_=_frozen()
    start=datetime(2021,4,1,9)
    times_a=[start+timedelta(minutes=15*i) for i in range(801)]
    times_b=[start+timedelta(hours=i) for i in range(200)]
    times_b[10]=times_b[9]  # one exact duplicate timestamp
    result=summarize_intervals({"YA":times_a,"YB":times_b},
        {"YA":"bird-A","YB":"bird-B"},
        c["predeclared_source_screen"]["time_gap_bins_seconds"],
        c["predeclared_source_screen"]["cohorts"])
    assert len(result)==2
    all_sample,eligible=result
    assert (all_sample["selected_season_ID_strings"],all_sample["distinct_bird_ID_strings"])==(2,2)
    assert (eligible["selected_season_ID_strings"],eligible["distinct_bird_ID_strings"])==(1,1)
    assert eligible["interval_bin_counts"]["15to30m"]==800
    assert eligible["share_positive_gaps_under_55min"]==1.0
    assert eligible["global_nearest_rank_quantile_minutes"]["q50"]==15.0
    assert all_sample["zero_timestamp_duplicate_pairs"]==1
    assert sum(all_sample["interval_bin_counts"].values())==all_sample["positive_consecutive_GPS_intervals"]
    assert all_sample["season_ID_strings_with_any_under_55min_gap"]==1
    for token in ("bird-A","bird-B","YA","YB","2021-04-01","9:00:00"):
        assert token not in json.dumps(result)

def test_one_per_hour_dataset_is_not_called_subhourly():
    c,_=_frozen()
    start=datetime(2019,5,1,0)
    x=[start+timedelta(hours=i) for i in range(801)]
    result=summarize_intervals({"yr":x},{"yr":"bird"},
        c["predeclared_source_screen"]["time_gap_bins_seconds"],
        c["predeclared_source_screen"]["cohorts"])
    assert all(x["share_positive_gaps_under_55min"]==0 for x in result)
    assert all(x["interval_bin_counts"]["55to65m"]==800 for x in result)
    assert all(x["season_ID_strings_with_any_under_55min_gap"]==0 for x in result)

def test_raw_source_row_screen_cannot_export_positions_or_timestamps():
    records=[
        HEADER,
        b"y1,b1,2021-05-01 01:00:00,11.1,51.3,5,6\r\n",
        b"y1,b1,2021-05-01 01:30:00,11.2,51.3,5,6\r\n",
        b"y1,b1,2021-05-01 02:00:00,8.8,51.3,5,6\r\n",
        b"y2,b2,2021-05-01 03:00:00,11.4,51.3,5,6\r\n",
        b"y9,b9,2021-05-01 03:00:00,11.4,51.3,5,6\r\n",
        b"y1,WRONG,2021-05-01 03:00:00,11.4,51.3,5,6\r\n",
        b"y1,b1,2021-11-01 05:00:00,11.4,51.3,5,6\r\n",
    ]
    groups,counts=read_geo_season_GPS(iter(records),{"y1":"b1","y2":"b2"},HEADER)
    assert counts["original_GPS_physical_lines"]==7
    assert counts["rows_from_unlisted_season_ID"]==1
    assert counts["wrong_bird_ID_for_known_season_rows"]==1
    assert counts["geo_season_source_events"]==3
    assert len(groups["y1"])==2 and len(groups["y2"])==1
    assert "y1" not in json.dumps(counts)
    assert "2021" not in json.dumps(counts)
    assert "11.1" not in json.dumps(counts)

def test_bad_header_is_a_source_hold():
    with pytest.raises(ValueError,match="header"):
        read_geo_season_GPS(iter([b"year,tag,time,x,y\r\n"]),{"y":"b"},HEADER)

def test_no_dynamic_posthoc_cohort_change():
    c,_=_frozen()
    start=datetime(2021,5,1)
    groups={"x":[start,start+timedelta(hours=1)]}
    wrong=[{"id":"all_linked_geo_season_years","min_fix_count":1},
           {"id":"arbitrary_selected","min_fix_count":2}]
    with pytest.raises(ValueError,match="cohorts"):
        summarize_intervals(groups,{"x":"bird"},c["predeclared_source_screen"]["time_gap_bins_seconds"],wrong)
