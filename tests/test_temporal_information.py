from __future__ import annotations

import pytest

from odsp.temporal_information import (
    normalize_gbif_time,
    normalize_inaturalist_time,
    normalize_occurrence_time,
)


def test_gbif_event_datetime_preserves_offset_and_precision():
    row = {
        "key": 123,
        "eventDate": "2026-05-17T21:34:12+09:00",
        "year": 2026,
        "month": 5,
        "day": 17,
        "verbatimEventDate": "17 May 2026 21:34:12 JST",
    }
    result = normalize_gbif_time(row)

    assert result.source == "gbif"
    assert result.source_occurrence_id == "123"
    assert result.temporal_precision == "second"
    assert result.observed_date == "2026-05-17"
    assert result.observed_datetime == "2026-05-17T21:34:12+09:00"
    assert result.observed_datetime_utc == "2026-05-17T12:34:12Z"
    assert result.utc_offset_minutes == 540
    assert (result.year, result.month, result.day) == (2026, 5, 17)
    assert (result.hour, result.minute, result.second) == (21, 34, 12)
    assert "timezone_missing" not in result.temporal_quality_flags


def test_gbif_date_plus_event_time_is_combined_without_inventing_timezone():
    row = {
        "gbifID": "abc",
        "eventDate": "2026-06-01",
        "eventTime": "05:42",
    }
    result = normalize_gbif_time(row)

    assert result.source_occurrence_id == "abc"
    assert result.temporal_precision == "minute"
    assert result.observed_datetime == "2026-06-01T05:42"
    assert result.observed_datetime_utc is None
    assert (result.hour, result.minute, result.second) == (5, 42, None)
    assert "timezone_missing" in result.temporal_quality_flags


def test_gbif_partial_date_stays_partial():
    result = normalize_gbif_time({"occurrenceID": "x", "year": 2024, "month": 9})

    assert result.observed_date == "2024-09"
    assert result.temporal_precision == "month"
    assert result.day is None
    assert result.day_of_year is None
    assert result.hour is None
    assert "date_only" in result.temporal_quality_flags


def test_gbif_date_mismatch_is_flagged_not_silently_resolved():
    result = normalize_gbif_time(
        {"eventDate": "2025-07-11", "year": 2025, "month": 7, "day": 12}
    )

    assert result.observed_date == "2025-07-11"
    assert "date_field_mismatch" in result.temporal_quality_flags


def test_gbif_interval_remains_interval():
    result = normalize_gbif_time({"eventDate": "2025-05-01/2025-05-03"})

    assert result.temporal_precision == "interval"
    assert result.interval_start == "2025-05-01"
    assert result.interval_end == "2025-05-03"
    assert result.observed_date is None
    assert "interval" in result.temporal_quality_flags


def test_inaturalist_preserves_local_and_utc_observation_times():
    row = {
        "id": 358817890,
        "observed_on": "2026-03-12",
        "observed_on_string": "2026-03-12 18:22:00",
        "time_observed_at": "2026-03-12T18:22:00+02:00",
        "time_observed_at_utc": "2026-03-12T16:22:00Z",
        "time_zone": "Pretoria",
        "zic_time_zone": "Africa/Johannesburg",
        "created_at": "2026-05-06T06:07:09+02:00",
    }
    result = normalize_inaturalist_time(row)

    assert result.source == "inaturalist"
    assert result.source_occurrence_id == "358817890"
    assert result.observed_date == "2026-03-12"
    assert result.observed_datetime == "2026-03-12T18:22:00+02:00"
    assert result.observed_datetime_utc == "2026-03-12T16:22:00Z"
    assert result.timezone_name == "Africa/Johannesburg"
    assert result.utc_offset_minutes == 120
    assert result.temporal_precision == "second"
    assert (result.hour, result.minute, result.second) == (18, 22, 0)
    assert "utc_timestamp_mismatch" not in result.temporal_quality_flags
    assert "created_at" not in result.raw_time_fields


def test_inaturalist_date_only_does_not_become_midnight():
    result = normalize_inaturalist_time(
        {"id": 10, "observed_on": "2026-04-05", "created_at": "2026-04-06T00:00:00Z"}
    )

    assert result.temporal_precision == "day"
    assert result.observed_date == "2026-04-05"
    assert result.observed_datetime is None
    assert result.hour is None
    assert "date_only" in result.temporal_quality_flags


def test_inaturalist_created_at_is_never_used_as_observation_time():
    result = normalize_inaturalist_time(
        {"id": 11, "created_at": "2026-08-01T12:30:00Z", "updated_at": "2026-08-02T12:30:00Z"}
    )

    assert result.temporal_precision == "unknown"
    assert result.observed_date is None
    assert result.observed_datetime is None
    assert result.observed_datetime_utc is None
    assert "missing_or_unparsed_observation_time" in result.temporal_quality_flags
    assert "record_management_timestamp_present_not_used" in result.temporal_quality_flags


def test_inaturalist_utc_disagreement_is_flagged():
    result = normalize_inaturalist_time(
        {
            "time_observed_at": "2026-01-01T10:00:00+09:00",
            "time_observed_at_utc": "2026-01-01T03:00:00Z",
        }
    )

    assert "utc_timestamp_mismatch" in result.temporal_quality_flags


def test_dispatcher_aliases_and_unknown_source():
    assert normalize_occurrence_time("inat", {"observed_on": "2026-01-01"}).source == "inaturalist"
    assert normalize_occurrence_time("GBIF", {"year": 2026}).source == "gbif"
    with pytest.raises(ValueError, match="unsupported temporal occurrence source"):
        normalize_occurrence_time("other", {})
