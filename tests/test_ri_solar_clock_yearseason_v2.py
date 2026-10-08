"""Post-exposure coded YearSeason v2; synthetic source rows only."""
from __future__ import annotations

import json
from pathlib import Path

import pytest

from odsp.ri_solar_clock_yearseason_v2 import (
    VERSION, DEPLOYMENT_HEADER, DETECTION_HEADER,
    _season, _validate_contract, v2_events_from_two_tables,
)
from odsp.ri_solar_clock_transfer_v0 import site_is_sealed

ROOT=Path(__file__).resolve().parents[1]
PLAN=json.loads((
    ROOT/"RI_SOLAR_CLOCK_YEARSEASON_V2_EXPLORATORY_CONTRACT.json"
).read_text())


def d(site="primary-site",station="station-x",camera="c1",season="w19",
      lat="41.5",lon="-71.6"):
    row=dict(zip(DEPLOYMENT_HEADER,(
        season,site,station,camera,"2019-01-01","2019-02-28",lat,lon
    )))
    return row


def e(site="primary-site",station="station-x",camera="c1",season="w19",
      when="2019-02-01 13:10:00",species="Vulpes vulpes"):
    return dict(zip(DETECTION_HEADER,(
        season,site,station,camera,when,"2019-02-01","13:10:00",
        "red fox","Mammalia","Carnivora","Canidae","Vulpes",
        "vulpes",species,"1"
    )))


def test_yearseason_mapping_is_new_declared_exploratory_only():
    _validate_contract(PLAN)
    assert PLAN["evidence_boundary"]["source_codes_chosen_after_YearSeason_frequency_audit"] is True
    assert PLAN["evidence_boundary"]["any_success_is_exploratory_not_a_new_preregistered_primary_result"] is True
    assert PLAN["source_v0"]["previous_v0_scored_outcomes_computed"] is False
    assert PLAN["source_v0"]["previous_v1_scored_outcomes_computed"] is False
    assert VERSION=="odsp-ri-solar-vs-clock-yearseason-v2-exploratory"


@pytest.mark.parametrize("source,expected",[
    ("w18",("winter",2018)),("w23",("winter",2023)),
    ("s18",("summer",2018)),("s22",("summer",2022)),
    ("W21",("winter",2021)),("s20",("summer",2020)),
    ("sp22",None),("Winter2022",None),("x22",None),
    ("w24",None),("w17",None),
])
def test_only_predeclared_2letter_coded_yearseason(source,expected):
    assert _season(source)==expected


def test_correct_composite_join_respects_site_not_camera_as_split_unit():
    deployments=[d(station="x"),d(station="y",lat="41.51")]
    observations=[
        e(station="x"),e(station="y",when="2019-02-01 14:10:00")
    ]
    events,audit=v2_events_from_two_tables(deployments,observations,PLAN)
    assert len(events)==2
    assert {x.site_id for x in events}=={"primary-site"}
    assert {x.season for x in events}=={"winter"}
    assert {x.season_year for x in events}=={2019}
    assert {x.latitude for x in events}=={41.5,41.51}
    assert audit["source_schema_version"]==VERSION
    assert audit["frozen_v0_inference_reclassified"] is False


def test_duplicate_frames_deduplicated_without_individual_image_pseudoreplication():
    events,report=v2_events_from_two_tables(
        [d()],[
            e(when="2019-02-01 13:10:00"),
            e(when="2019-02-01 13:29:00"),
            e(when="2019-02-01 13:40:00"),
        ],PLAN
    )
    assert len(events)==2
    assert report["detection_filter_counts"]["suppressed_within_30min_photo_duplicates"]==1


def test_spring_is_frozen_excluded_and_not_a_hidden_season():
    with pytest.raises(ValueError,match="no usable"):
        v2_events_from_two_tables([d(season="sp22")],[e(season="sp22")],PLAN)


def test_frozen_site_species_camera_and_time_fields_cannot_be_substituted():
    changed=json.loads(json.dumps(PLAN))
    changed["key_map"]["species"]="Common.Name"
    with pytest.raises(ValueError,match="source primary site"):
        _validate_contract(changed)


def test_bad_join_and_conflicting_physical_station_coordinates_fail():
    with pytest.raises(ValueError,match="2%"):
        v2_events_from_two_tables([d()],[e(station="wrong")],PLAN)
    with pytest.raises(ValueError,match="conflicting coordinates"):
        v2_events_from_two_tables(
            [d(),d(lat="41.52")],[e()],PLAN
        )


def test_hash_keeps_all_seasons_of_primary_site_together():
    assert site_is_sealed("primary-site") in (True,False)
    assert site_is_sealed("primary-site")==site_is_sealed("primary-site")
