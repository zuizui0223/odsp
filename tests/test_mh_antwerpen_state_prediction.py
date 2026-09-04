from __future__ import annotations

from datetime import datetime, timedelta, timezone

from odsp.mh_antwerpen_prediction import (
    MarshHarrierEvent,
    altitude_state,
    endpoint_decision,
    individual_admission,
    parse_admissible_row,
    thin_10min_earliest,
)


def _event(individual: str, minute: int, height: float, temp: float = 12.0):
    return MarshHarrierEvent(
        timestamp_utc=datetime(2020, 5, 1, tzinfo=timezone.utc) + timedelta(minutes=minute),
        longitude=4.4,
        latitude=51.2,
        external_temperature_c=temp,
        height_m_amsl=height,
        individual_id=individual,
        altitude_state=altitude_state(height),
        source_file="synthetic.csv.gz",
    )


def test_fixed_altitude_states():
    assert altitude_state(-10) == "low_lt50"
    assert altitude_state(49.9) == "low_lt50"
    assert altitude_state(50) == "lower_mid_50_200"
    assert altitude_state(199.9) == "lower_mid_50_200"
    assert altitude_state(200) == "upper_mid_200_500"
    assert altitude_state(499.9) == "upper_mid_200_500"
    assert altitude_state(500) == "high_ge500"


def test_row_parser_applies_frozen_quality_rules():
    row = {
        "timestamp": "2020-05-01 12:01:00",
        "location-long": "4.4",
        "location-lat": "51.2",
        "external-temperature": "14.5",
        "height-above-msl": "175",
        "individual-local-identifier": "bird-a",
        "import-marked-outlier": "false",
        "manually-marked-outlier": "false",
    }
    event, reason = parse_admissible_row(row, source_file="x.csv.gz")
    assert reason is None
    assert event is not None
    assert event.altitude_state == "lower_mid_50_200"
    assert len(event.features) == 7

    row["manually-marked-outlier"] = "true"
    event, reason = parse_admissible_row(row, source_file="x.csv.gz")
    assert event is None
    assert reason == "manually_marked_outlier"


def test_10_minute_thinning_keeps_earliest_per_individual():
    events = [_event("a", 1, 10), _event("a", 7, 20), _event("a", 11, 30), _event("b", 7, 20)]
    thinned = thin_10min_earliest(events)
    assert [(e.individual_id, e.timestamp_utc.minute) for e in thinned] == [
        ("a", 1),
        ("a", 11),
        ("b", 7),
    ]


def test_individual_admission_requires_events_and_two_supported_states():
    events = []
    for i in range(300):
        events.append(_event("eligible", i * 10, 20 if i < 150 else 100))
    for i in range(300):
        events.append(_event("one-state", i * 10, 20))
    admission = {x.individual_id: x for x in individual_admission(events)}
    assert admission["eligible"].eligible is True
    assert admission["one-state"].eligible is False
    assert "too_few_supported_altitude_states" in admission["one-state"].exclusion_reasons


def test_endpoint_decision_is_fail_closed_before_four_individuals():
    admissions = individual_admission(
        [
            _event(ind, i * 10, 20 if i < 150 else 100)
            for ind in ("a", "b", "c")
            for i in range(300)
        ]
    )
    decision = endpoint_decision(admissions, [])
    assert decision["terminal_category"] == "empirical_state_prediction_unavailable"
    assert decision["reason"] == "fewer_than_minimum_eligible_individuals"
