"""Post-schema-exposure exploratory source adapter tests on invented rows ONLY."""
from __future__ import annotations

from datetime import datetime
import json
from pathlib import Path

import pytest

from odsp.ri_solar_clock_schema_v1 import (
    VERSION, DEPLOYMENT_HEADER, DETECTION_HEADER,
    _season, _datetime, _validate_contract,
    v1_events_from_two_tables,
)
from odsp.ri_solar_clock_transfer_v0 import site_is_sealed

ROOT=Path(__file__).resolve().parents[1]
PLAN=json.loads((ROOT/"RI_SOLAR_CLOCK_SCHEMA_V1_EXPLORATORY_CONTRACT.json").read_text())


def dep(site="site-one",station="station-a",camera="device-1",
        season="Winter2019",lat="41.3",lon="-71.5"):
    vals=("Winter2019",site,station,camera,"2019-01-02",
          "2019-02-28",lat,lon)
    data=dict(zip(DEPLOYMENT_HEADER,vals))
    data["YearSeason"]=season
    return data


def detect(site="site-one",station="station-a",camera="device-1",
           season="Winter2019",when="2019-02-01 12:30:00",
           taxon="Vulpes vulpes"):
    vals=(season,site,station,camera,when,"2019-02-01","12:30:00",
          "red fox","Mammalia","Carnivora","Canidae","Vulpes",
          "vulpes",taxon,"1")
    return dict(zip(DETECTION_HEADER,vals))


def test_post_schema_exposure_is_recorded_and_original_route_not_promoted():
    _validate_contract(PLAN)
    assert PLAN["source_v0"]["prior_source_rows_parsed_in_memory"] is True
    assert PLAN["source_v0"]["no_historical_full_nonaccess_claim"] is True
    assert PLAN["analysis_status"]=="FROZEN_NEW_EXPLORATORY_VERSION_AFTER_V0_ALREADY_READ_ARCHIVE_ROWS"
    assert PLAN["unchanged_scientific_invariants"]["heldout_site_fold"]==0
    assert PLAN["key_map"]["deployment_match_composite"]==[
        "YearSeason","Primary.Site.ID","Trap.Station.Name","Camera.Name"
    ]


@pytest.mark.parametrize("text,expect",[
    ("Winter2018",("winter",2018)),
    ("2018Winter",("winter",2018)),
    ("Winter_2019",("winter",2019)),
    ("Summer 2023",("summer",2023)),
    ("2022 Summer",("summer",2022)),
    ("Fall 2019",None),
    ("winter2025",None),
    ("Nov 2022",None),
])
def test_literal_frozen_season_encoding(text,expect):
    assert _season(text)==expect


def test_declared_datetime_formats_and_fallback_only_when_blank():
    assert _datetime(detect())==datetime(2019,2,1,12,30)
    a=detect(when="")
    assert _datetime(a)==datetime(2019,2,1,12,30)
    b=detect(when="source-malformed")
    assert _datetime(b) is None


def test_exact_physical_station_camera_join_not_just_site_camera_join():
    dep_rows=[dep(station="station-a"),dep(station="station-b",lat="41.31")]
    events,audit=v1_events_from_two_tables(
        dep_rows,[
            detect(station="station-a"),
            detect(station="station-b",when="2019-02-01 13:30:00"),
        ],
        PLAN,
    )
    assert len(events)==2
    assert {e.site_id for e in events}=={"site-one"}
    assert {e.latitude for e in events}=={41.3,41.31}
    assert audit["unique_site_station_camera_season_join_keys"]==2
    assert audit["source_schema_selected_after_v0_data_rows_may_have_been_read"] is True
    assert audit["physical_site_ids_and_camera_coordinates_exposed"] is False


def test_duplicate_images_29_minutes_apart_removed_but_30_minutes_retained():
    rows=[
        detect(when="2019-02-01 12:30:00"),
        detect(when="2019-02-01 12:59:00"),
        detect(when="2019-02-01 13:00:00"),
        detect(when="2019-02-01 13:31:00"),
    ]
    events,audit=v1_events_from_two_tables([dep()],rows,PLAN)
    assert len(events)==3
    assert audit["detection_filter_counts"][
        "suppressed_within_30min_photo_duplicates"
    ]==1


def test_invalid_independent_unit_key_rejected_before_model_fit():
    with pytest.raises(ValueError,match="2%"):
        v1_events_from_two_tables(
            [dep()],
            [detect(station="station-elsewhere")],
            PLAN,
        )


def test_unfrozen_taxon_column_substitution_is_not_allowed():
    wrong=json.loads(json.dumps(PLAN))
    wrong["key_map"]["species"]="Common.Name"
    with pytest.raises(ValueError,match="source primary site"):
        _validate_contract(wrong)


def test_raw_header_drift_cannot_be_auto_harmonized_after_results():
    a=dep()
    a["SiteID"]=a.pop("Primary.Site.ID")
    with pytest.raises(ValueError,match="deployment member header changed"):
        v1_events_from_two_tables([a],[detect()],PLAN)


def test_same_composite_key_with_different_coordinates_fails_closed():
    with pytest.raises(ValueError,match="conflicting coordinates"):
        v1_events_from_two_tables(
            [dep(),dep(lat="41.35")],
            [detect()],
            PLAN,
        )


def test_sites_not_split_by_camera_device_or_season():
    one="fixed-physical-site"
    assert site_is_sealed(one)==site_is_sealed(one)
    detections=[
        detect(site=one,camera="device-1"),
        detect(site=one,camera="device-2",when="2019-02-01 15:30:00"),
    ]
    events,_=v1_events_from_two_tables(
        [dep(site=one,camera="device-1"),
         dep(site=one,camera="device-2")],
        detections,PLAN
    )
    assert {e.site_id for e in events}=={one}
    assert VERSION=="odsp-ri-solar-vs-clock-schema-v1-exploratory"
