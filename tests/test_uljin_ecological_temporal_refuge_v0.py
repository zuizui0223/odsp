"""Ecological (NOT clock-method winner) four-taxon matched-daylength source admission."""
from datetime import date
import json
from pathlib import Path

import pytest
from odsp.uljin_ecological_temporal_refuge_v0 import (
    TAXA,ZONES,assert_frozen_ecology,parse_clock_minutes,
    solar_zone_bounds,classify_event_time,solar_zone_operation_minutes,
    source_timestamp_audit,source_effort_and_ecological_support
)

ROOT=Path(__file__).resolve().parents[1]
PLAN=json.loads((ROOT/"ULJIN_FOUR_UNGULATE_TEMPORAL_REFUGE_ECOLOGY_V0_CONTRACT.json").read_text())
CAL=json.loads((ROOT/"ULJIN_PHOTOPERIOD_MIRROR_2022_V0_DESIGN_CONTRACT.json").read_text())


def test_the_real_precommitted_41_pairs_are_NOT_spring_fall():
    pair_days=assert_frozen_ecology(PLAN,CAL)
    assert len(pair_days)==82
    assert set(pair_days.values())=={"rising","falling"}
    assert all(x.startswith("2022-") for x in pair_days)
    early=[day for day,season in pair_days.items() if season=="rising"]
    late=[day for day,season in pair_days.items() if season=="falling"]
    assert len(early)==len(late)==41
    assert min(early)>="2022-05-01" and max(early)<="2022-06-10"
    assert min(late)>="2022-07-01" and max(late)<="2022-08-31"
    assert PLAN["correct_calendar"]["forbidden_mislabel"].startswith("DO NOT call")


def test_central_daylight_and_two_edges_have_EQUAL_duration():
    for d in (date(2022,5,15),date(2022,7,25)):
        intervals=solar_zone_bounds(d)
        all_bounds=[(a,b,z) for z,seq in intervals.items()
                    for a,b in seq]
        assert len(all_bounds)==5
        durations={k:sum(b-a for a,b in intervals[k]) for k in ZONES}
        assert durations["daylight_core"]==pytest.approx(
            durations["daylight_edge"],abs=1e-10)
        assert sum(durations.values())==pytest.approx(1440.,abs=1e-10)
        assert solar_zone_operation_minutes(d,[(0.,1440.)])["night"]==pytest.approx(
            durations["night"],abs=1e-10)
        for name,limits in intervals.items():
            mid=(limits[0][0]+limits[0][1])/2
            assert classify_event_time(d,mid)==name


def test_event_clock_strict_and_unverified_real_source_cannot_produce_ecology():
    assert parse_clock_minutes("12:34:56")==pytest.approx(12*60+34+56/60)
    for t in ("24:00:00","06:60:00","7:20:00","12:23", "",None):
        with pytest.raises(ValueError):
            parse_clock_minutes(t)
    blocked=source_timestamp_audit(PLAN,CAL,[],source_member_verified=False)
    assert blocked["status"]=="HOLD_ORIGINAL_EVENT_MEMBER_PROVENANCE_UNVERIFIED"
    assert not blocked["real_ecological_conclusion"]


def test_four_species_original_dates_retained_and_no_inference_from_timestamps():
    days=assert_frozen_ecology(PLAN,CAL)
    rising=next(day for day,b in days.items() if b=="rising")
    falling=next(day for day,b in days.items() if b=="falling")
    rows=[
        {"Station":"UJ1_demo","Species":"Wild boar","Date":rising,"Time":"12:00:00"},
        {"Station":"UJ1_demo","Species":"Wild boar","Date":falling,"Time":"12:00:00"},
        {"Station":"UJ1_demo","Species":"Goral","Date":falling,"Time":"02:00:00"},
        {"Station":"UJ2_demo","Species":"Roe deer","Date":"2023-04-01","Time":"12:00:00"},
    ]
    audit=source_timestamp_audit(PLAN,CAL,rows,source_member_verified=True)
    assert audit["status"]=="TIMESTAMP_ONLY_ECOLOGICAL_SUPPORT_AUDIT_NOT_EFFORT_OR_LATENT_ACTIVITY"
    assert not audit["real_ecological_conclusion"]
    assert audit["source_events_within_original_82_dates"]==3
    assert audit["source_events_outside_original_82_dates"]==1
    assert len(audit["species_branch_solar_zone_counts"])==len(TAXA)*2==8
    assert audit["real_independent_hourly_camera_operation_verified"] is False
    all_rows=audit["species_branch_solar_zone_counts"]
    assert next(x for x in all_rows if x["Species"]=="Water deer"
                and x["photoperiod_branch"]=="rising")["all_events"]==0
    assert next(x for x in all_rows if x["Species"]=="Goral"
                and x["photoperiod_branch"]=="falling")["night_detected_events"]==1
    broken=[{"Station":"X","Species":"Unknown","Date":rising,"Time":"02:00:00"}]
    with pytest.raises(ValueError,match="taxonomic"):
        source_timestamp_audit(PLAN,CAL,broken,source_member_verified=True)


def test_source_operation_hours_not_inferred_from_camera_nights_or_incomplete_logs():
    days=assert_frozen_ecology(PLAN,CAL)
    audit=source_timestamp_audit(PLAN,CAL,[],source_member_verified=True)
    unqualified=source_effort_and_ecological_support(
        PLAN,CAL,audit,{},independent_operation_log_attested=False)
    assert unqualified["status"]=="HOLD_NO_HOURLY_OPERATION_DURATION"
    assert unqualified["rate_estimates_computed"] is False
    partial={("UJ1_demo",next(iter(days))):[(0.,1440.)]}
    incomplete=source_effort_and_ecological_support(
        PLAN,CAL,audit,partial,independent_operation_log_attested=True)
    assert incomplete["status"]=="HOLD_INCOMPLETE_STATION_DATE_OPERATION_COVERAGE"
    all_ops={("UJ1_demo",day):[(0.,1440.)] for day in days}
    support=source_effort_and_ecological_support(
        PLAN,CAL,audit,all_ops,independent_operation_log_attested=True)
    assert support["status"]=="SOURCE_OPERATION_HOURLY_EFFORT_ADMITTED_DESCRIPTIVE_SUPPORT_ONLY"
    assert not support["rate_estimates_computed"]
    assert support["fixed_source_station_roster_size"]==1
    assert support["stations_positive_operation_both_branches"]==1
    assert len(support["camera_hours_by_branch_zone"])==6
    assert all(not x["descriptive_support_guard_passed"] for x
               in support["taxa_preserved_with_predeclared_low_support_flags"])
    with pytest.raises(ValueError,match="overlapping"):
        solar_zone_operation_minutes(date(2022,5,15),
            [(300.,600.),(500.,700.)])
    with pytest.raises(ValueError):
        solar_zone_operation_minutes(date(2022,5,15),[(0.,1500.)])


def test_contract_taxa_or_date_redefinition_fails_before_data_access():
    edited=json.loads(json.dumps(PLAN))
    edited["species_predeclared"][0]="Fox"
    with pytest.raises(ValueError,match="freeze"):
        assert_frozen_ecology(edited,CAL)
    edited=json.loads(json.dumps(PLAN))
    edited["correct_calendar"]["late_growing_season_window"][0]="2022-09-01"
    with pytest.raises(ValueError,match="freeze"):
        assert_frozen_ecology(edited,CAL)
