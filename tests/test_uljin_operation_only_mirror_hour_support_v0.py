"""Synthetic hour-accurate operation support tests: ZERO animal detections."""
from __future__ import annotations
import json
from pathlib import Path
import pytest

from odsp.uljin_operation_only_mirror_hour_support_v0 import (
    summarize_mirror_camera_hour_support,
)

ROOT=Path(__file__).resolve().parents[1]
CALENDAR=json.loads(
    (ROOT/"ULJIN_PHOTOPERIOD_MIRROR_2022_V0_DESIGN_CONTRACT.json").read_text()
)
PLAN=json.loads(
    (ROOT/"ULJIN_OPERATION_ONLY_MIRRORED_DAY_EXPOSURE_V0_CONTRACT.json").read_text()
)


def deployment(site,start="2022-04-01T00:00:00+09:00",
               end="2022-10-01T00:00:00+09:00"):
    return {"Station":site,"DeploymentStart":start,"DeploymentEnd":end}


def outage(site,start,end):
    return {"Station":site,"DowntimeStart":start,"DowntimeEnd":end}


def _run(dep,down=()):
    return summarize_mirror_camera_hour_support(
        CALENDAR,PLAN,dep,list(down)
    )


def test_original_dates_and_full_day_source_stations_are_eligible_without_events():
    result=_run([
        deployment("UJ1-001"),deployment("UJ2-001"),
    ])
    assert result["original_unchanged_astronomical_date_pairs"]==41
    assert result["original_source_region_counts"]["UJ1"][
        "station_day_pairs_with_both_dates_meeting_hourly_coverage"
    ]==41
    assert result["original_source_region_counts"]["UJ2"][
        "station_day_pairs_with_both_dates_meeting_hourly_coverage"
    ]==41
    assert result["total_normalized_input_stations"]==2
    assert result["species_detection_data_opened"] is False
    assert result["animal_activity_or_hysteresis_result_estimated"] is False
    assert result["operation_metadata_independent_of_photos_attested"] is False
    assert result["original_EcoBank_v1p1_operation_logs_verified"] is False
    assert result["per_station_identifiers_emitted"] is False
    assert result["real_Uljin_camera_support_claimed"] is False
    output=json.dumps(result,allow_nan=False)
    assert "UJ1-001" not in output and "UJ2-001" not in output


def test_one_camera_six_hour_outage_on_matched_date_removes_one_pair_only():
    d=[deployment("UJ1-001")]
    day_out=outage(
        "UJ1-001","2022-05-01T00:00:00+09:00",
        "2022-05-01T06:00:00+09:00"
    )
    result=_run(d,[day_out])
    assert result["original_source_region_counts"]["UJ1"][
        "station_day_pairs_with_both_dates_meeting_hourly_coverage"
    ]==40
    assert result["original_source_region_counts"]["UJ1"][
        "stations_with_all_41_source_eligible_pairs"
    ]==0


def test_union_overlapping_deployment_and_downtime_does_not_double_count():
    dep=[
        deployment("UJ1-001"),
        deployment("UJ1-001","2022-04-20T00:00:00+09:00",
                   "2022-09-05T00:00:00+09:00"),
    ]
    a=outage("UJ1-001","2022-05-01T00:00:00+09:00",
             "2022-05-01T05:00:00+09:00")
    b=outage("UJ1-001","2022-05-01T03:00:00+09:00",
             "2022-05-01T06:00:00+09:00")
    result=_run(dep,[a,b])
    assert result["original_source_region_counts"]["UJ1"][
        "station_day_pairs_with_both_dates_meeting_hourly_coverage"
    ]==40


def test_hour_level_partial_coverage_minimum_three_in_every_bin():
    dep=[deployment("UJ1-001")]
    # 1 hour in each 4-hour interval is lost: 3 hours remain => pass.
    downs=[
        outage("UJ1-001",f"2022-05-01T{hour:02d}:00:00+09:00",
               f"2022-05-01T{hour+1:02d}:00:00+09:00")
        for hour in (0,4,8,12,16,20)
    ]
    assert _run(dep,downs)["original_source_region_counts"]["UJ1"][
        "station_day_pairs_with_both_dates_meeting_hourly_coverage"
    ]==41
    # Another extra second fails the fixed six-bin threshold.
    with_extra=downs+[
        outage("UJ1-001","2022-05-01T01:00:00+09:00",
               "2022-05-01T01:00:01+09:00")
    ]
    assert _run(dep,with_extra)["original_source_region_counts"]["UJ1"][
        "station_day_pairs_with_both_dates_meeting_hourly_coverage"
    ]==40


@pytest.mark.parametrize("bad_deployment,bad_outage",[
    ([deployment("UJ1-001","2022-10-01T00:00:00+09:00",
                "2022-04-01T00:00:00+09:00")],[],),
    ([deployment("UJ1-001","2022-04-01T00:00:00",
                "2022-10-01T00:00:00")],[],),
    ([deployment("UJ1-001")],[
        outage("UJ1-001","2022-03-01T00:00:00+09:00",
               "2022-03-02T00:00:00+09:00")
    ]),
    ([deployment("UJ1-001")],[
        outage("UJ2-001","2022-05-01T00:00:00+09:00",
               "2022-05-01T03:00:00+09:00")
    ]),
])
def test_invalid_clock_or_downtime_metadata_stops(bad_deployment,bad_outage):
    with pytest.raises(ValueError):
        _run(bad_deployment,bad_outage)


def test_original_calendar_or_coverage_gate_cannot_be_changed_postoutcome():
    adjusted=json.loads(json.dumps(PLAN))
    adjusted["predeclared_stations_and_pairs"][
        "minimum_functional_hours_in_EACH_4h_bin"]=0.
    with pytest.raises(ValueError,match="eligibility gates"):
        summarize_mirror_camera_hour_support(
            CALENDAR,adjusted,[deployment("UJ1-001")],[]
        )
    altered=json.loads(json.dumps(CALENDAR))
    altered["preoutcome_structural_pairing"][
        "pair_min_calendar_separation_days"]=1
    with pytest.raises(ValueError,match="pairing rules"):
        summarize_mirror_camera_hour_support(
            altered,PLAN,[deployment("UJ1-001")],[]
        )
