"""Source-preserving temporal information for biodiversity occurrences.

This module normalizes observation-time metadata without turning it into a new
niche model or silently increasing temporal precision. GBIF and iNaturalist
record-management timestamps are deliberately not used as observation time.
"""
from __future__ import annotations

from dataclasses import asdict, dataclass
from datetime import date, datetime, time, timezone
import re
from typing import Any, Mapping


_PRECISION_ORDER = {
    "unknown": 0,
    "year": 1,
    "month": 2,
    "day": 3,
    "minute": 4,
    "second": 5,
    "interval": 6,
}

_GBIF_TIME_FIELDS = (
    "eventDate",
    "eventTime",
    "year",
    "month",
    "day",
    "startDayOfYear",
    "endDayOfYear",
    "verbatimEventDate",
)

_INAT_TIME_FIELDS = (
    "observed_on",
    "observed_on_string",
    "time_observed_at",
    "time_observed_at_utc",
    "time_zone",
    "zic_time_zone",
)

_INAT_RECORD_MANAGEMENT_FIELDS = (
    "created_at",
    "updated_at",
    "created_at_utc",
    "updated_at_utc",
)


@dataclass(frozen=True)
class TemporalObservation:
    """Canonical occurrence-time record with explicit source precision."""

    source: str
    source_occurrence_id: str | None
    observed_date: str | None
    observed_datetime: str | None
    observed_datetime_utc: str | None
    interval_start: str | None
    interval_end: str | None
    timezone_name: str | None
    utc_offset_minutes: int | None
    temporal_precision: str
    clock_basis: str
    year: int | None
    month: int | None
    day: int | None
    day_of_year: int | None
    hour: int | None
    minute: int | None
    second: int | None
    raw_time_fields: dict[str, Any]
    temporal_quality_flags: tuple[str, ...]

    def __post_init__(self) -> None:
        if self.temporal_precision not in _PRECISION_ORDER:
            raise ValueError(f"unknown temporal precision: {self.temporal_precision}")

    def as_dict(self) -> dict[str, Any]:
        """Return a JSON-serializable dictionary."""

        return asdict(self)


@dataclass(frozen=True)
class _ParsedTemporal:
    observed_date: str | None = None
    observed_datetime: str | None = None
    observed_datetime_utc: str | None = None
    interval_start: str | None = None
    interval_end: str | None = None
    utc_offset_minutes: int | None = None
    precision: str = "unknown"
    clock_basis: str = "unknown"
    year: int | None = None
    month: int | None = None
    day: int | None = None
    day_of_year: int | None = None
    hour: int | None = None
    minute: int | None = None
    second: int | None = None


def _text(value: Any) -> str | None:
    if value is None:
        return None
    value = str(value).strip()
    return value or None


def _integer(value: Any) -> int | None:
    if value is None or value == "":
        return None
    try:
        return int(value)
    except (TypeError, ValueError):
        return None


def _iso_for_python(value: str) -> str:
    return value[:-1] + "+00:00" if value.endswith("Z") else value


def _datetime_precision(raw: str) -> str:
    match = re.search(r"[T ](\d{2}):(\d{2})(?::(\d{2})(?:\.\d+)?)?", raw)
    if not match:
        return "unknown"
    return "second" if match.group(3) is not None else "minute"


def _offset_minutes(value: datetime) -> int | None:
    offset = value.utcoffset()
    if offset is None:
        return None
    return int(offset.total_seconds() // 60)


def _from_datetime(value: datetime, raw: str, *, clock_basis: str) -> _ParsedTemporal:
    aware = value.utcoffset() is not None
    utc_value = value.astimezone(timezone.utc) if aware else None
    return _ParsedTemporal(
        observed_date=value.date().isoformat(),
        observed_datetime=value.isoformat(),
        observed_datetime_utc=(
            utc_value.isoformat().replace("+00:00", "Z") if utc_value is not None else None
        ),
        utc_offset_minutes=_offset_minutes(value),
        precision=_datetime_precision(raw),
        clock_basis=clock_basis,
        year=value.year,
        month=value.month,
        day=value.day,
        day_of_year=value.timetuple().tm_yday,
        hour=value.hour,
        minute=value.minute,
        second=value.second if _datetime_precision(raw) == "second" else None,
    )


def _parse_single_temporal(value: Any, *, clock_basis: str = "source") -> _ParsedTemporal:
    raw = _text(value)
    if raw is None:
        return _ParsedTemporal()

    if re.fullmatch(r"\d{4}", raw):
        return _ParsedTemporal(
            observed_date=raw,
            precision="year",
            clock_basis="date_only",
            year=int(raw),
        )
    if re.fullmatch(r"\d{4}-\d{2}", raw):
        year, month = (int(x) for x in raw.split("-"))
        if not 1 <= month <= 12:
            return _ParsedTemporal()
        return _ParsedTemporal(
            observed_date=raw,
            precision="month",
            clock_basis="date_only",
            year=year,
            month=month,
        )
    if re.fullmatch(r"\d{4}-\d{2}-\d{2}", raw):
        try:
            parsed = date.fromisoformat(raw)
        except ValueError:
            return _ParsedTemporal()
        return _ParsedTemporal(
            observed_date=raw,
            precision="day",
            clock_basis="date_only",
            year=parsed.year,
            month=parsed.month,
            day=parsed.day,
            day_of_year=parsed.timetuple().tm_yday,
        )

    try:
        parsed_dt = datetime.fromisoformat(_iso_for_python(raw))
    except ValueError:
        return _ParsedTemporal()
    basis = "utc" if parsed_dt.utcoffset() is not None and _offset_minutes(parsed_dt) == 0 else clock_basis
    if parsed_dt.utcoffset() is None:
        basis = "source_local_unknown_timezone"
    return _from_datetime(parsed_dt, raw, clock_basis=basis)


def _parse_interval(value: Any) -> _ParsedTemporal | None:
    raw = _text(value)
    if raw is None or "/" not in raw:
        return None
    left, right = raw.split("/", 1)
    start = _parse_single_temporal(left)
    end = _parse_single_temporal(right)
    if start.precision == "unknown" or end.precision == "unknown":
        return _ParsedTemporal(
            interval_start=_text(left),
            interval_end=_text(right),
            precision="interval",
            clock_basis="interval",
        )
    return _ParsedTemporal(
        interval_start=start.observed_datetime or start.observed_date,
        interval_end=end.observed_datetime or end.observed_date,
        precision="interval",
        clock_basis="interval",
    )


def _parse_temporal(value: Any, *, clock_basis: str = "source") -> _ParsedTemporal:
    interval = _parse_interval(value)
    if interval is not None:
        return interval
    return _parse_single_temporal(value, clock_basis=clock_basis)


def _parse_event_time(value: Any) -> tuple[time | None, str]:
    raw = _text(value)
    if raw is None or "/" in raw:
        return None, "unknown"
    candidate = _iso_for_python(raw)
    try:
        parsed = time.fromisoformat(candidate)
    except ValueError:
        return None, "unknown"
    precision = "second" if re.fullmatch(r"\d{2}:\d{2}:\d{2}(?:\.\d+)?(?:Z|[+-]\d{2}:?\d{2})?", raw) else "minute"
    return parsed, precision


def _with_event_time(base: _ParsedTemporal, event_time: Any) -> _ParsedTemporal:
    if base.precision != "day" or base.year is None or base.month is None or base.day is None:
        return base
    parsed_time, precision = _parse_event_time(event_time)
    if parsed_time is None:
        return base
    combined = datetime.combine(date(base.year, base.month, base.day), parsed_time)
    basis = "source_local_unknown_timezone"
    if parsed_time.utcoffset() is not None:
        basis = "utc" if int(parsed_time.utcoffset().total_seconds()) == 0 else "source_offset"
    raw = combined.isoformat(timespec="seconds" if precision == "second" else "minutes")
    return _from_datetime(combined, raw, clock_basis=basis)


def _component_date(year: int | None, month: int | None, day: int | None) -> _ParsedTemporal:
    if year is None:
        return _ParsedTemporal()
    if month is None:
        return _parse_single_temporal(f"{year:04d}")
    if day is None:
        return _parse_single_temporal(f"{year:04d}-{month:02d}")
    return _parse_single_temporal(f"{year:04d}-{month:02d}-{day:02d}")


def _date_tuple(parsed: _ParsedTemporal) -> tuple[int | None, int | None, int | None]:
    return parsed.year, parsed.month, parsed.day


def _source_id(record: Mapping[str, Any], fields: tuple[str, ...]) -> str | None:
    for field in fields:
        value = _text(record.get(field))
        if value is not None:
            return value
    return None


def _raw_fields(record: Mapping[str, Any], fields: tuple[str, ...]) -> dict[str, Any]:
    return {field: record[field] for field in fields if field in record and record[field] not in (None, "")}


def normalize_gbif_time(record: Mapping[str, Any]) -> TemporalObservation:
    """Normalize GBIF Darwin Core observation-event time fields."""

    flags: set[str] = set()
    raw = _raw_fields(record, _GBIF_TIME_FIELDS)
    event_date = _text(record.get("eventDate"))
    parsed = _parse_temporal(event_date, clock_basis="source_offset") if event_date else _ParsedTemporal()

    component = _component_date(
        _integer(record.get("year")),
        _integer(record.get("month")),
        _integer(record.get("day")),
    )
    if parsed.precision == "unknown" and component.precision != "unknown":
        parsed = component
    elif (
        parsed.precision not in {"unknown", "interval"}
        and component.precision == "day"
        and _date_tuple(parsed) != _date_tuple(component)
    ):
        flags.add("date_field_mismatch")

    event_time = record.get("eventTime")
    if event_time not in (None, ""):
        if parsed.precision == "day":
            enriched = _with_event_time(parsed, event_time)
            if enriched.precision != "day":
                parsed = enriched
            else:
                flags.add("unparsed_event_time")
        elif parsed.precision in {"year", "month", "unknown"}:
            flags.add("time_without_complete_date")

    if parsed.precision == "interval":
        flags.add("interval")
    elif parsed.precision in {"year", "month", "day"}:
        flags.add("date_only")
    if parsed.precision == "unknown":
        flags.add("missing_or_unparsed_observation_time")
    if parsed.hour is not None and parsed.utc_offset_minutes is None:
        flags.add("timezone_missing")

    return TemporalObservation(
        source="gbif",
        source_occurrence_id=_source_id(record, ("key", "gbifID", "occurrenceID")),
        observed_date=parsed.observed_date,
        observed_datetime=parsed.observed_datetime,
        observed_datetime_utc=parsed.observed_datetime_utc,
        interval_start=parsed.interval_start,
        interval_end=parsed.interval_end,
        timezone_name=None,
        utc_offset_minutes=parsed.utc_offset_minutes,
        temporal_precision=parsed.precision,
        clock_basis=parsed.clock_basis,
        year=parsed.year,
        month=parsed.month,
        day=parsed.day,
        day_of_year=parsed.day_of_year,
        hour=parsed.hour,
        minute=parsed.minute,
        second=parsed.second,
        raw_time_fields=raw,
        temporal_quality_flags=tuple(sorted(flags)),
    )


def normalize_inaturalist_time(record: Mapping[str, Any]) -> TemporalObservation:
    """Normalize iNaturalist observation time without using upload timestamps."""

    flags: set[str] = set()
    raw = _raw_fields(record, _INAT_TIME_FIELDS)
    local_raw = _text(record.get("time_observed_at"))
    utc_raw = _text(record.get("time_observed_at_utc"))
    date_raw = _text(record.get("observed_on"))

    local = _parse_temporal(local_raw, clock_basis="source_offset") if local_raw else _ParsedTemporal()
    utc = _parse_temporal(utc_raw, clock_basis="utc") if utc_raw else _ParsedTemporal()
    observed_date = _parse_temporal(date_raw) if date_raw else _ParsedTemporal()

    if local.precision != "unknown":
        parsed = local
    elif observed_date.precision != "unknown":
        parsed = observed_date
    elif utc.precision != "unknown":
        parsed = utc
    else:
        parsed = _ParsedTemporal()

    if (
        parsed.precision not in {"unknown", "interval"}
        and observed_date.precision == "day"
        and _date_tuple(parsed) != _date_tuple(observed_date)
    ):
        flags.add("date_field_mismatch")

    explicit_utc = utc.observed_datetime_utc or utc.observed_datetime
    if local.observed_datetime_utc and explicit_utc:
        try:
            left = datetime.fromisoformat(_iso_for_python(local.observed_datetime_utc))
            right = datetime.fromisoformat(_iso_for_python(explicit_utc))
            if abs((left - right).total_seconds()) > 1:
                flags.add("utc_timestamp_mismatch")
        except ValueError:
            flags.add("unparsed_utc_timestamp")

    if parsed.precision == "interval":
        flags.add("interval")
    elif parsed.precision in {"year", "month", "day"}:
        flags.add("date_only")
    if parsed.precision == "unknown":
        flags.add("missing_or_unparsed_observation_time")
        if any(record.get(field) not in (None, "") for field in _INAT_RECORD_MANAGEMENT_FIELDS):
            flags.add("record_management_timestamp_present_not_used")
    if parsed.hour is not None and parsed.utc_offset_minutes is None and not explicit_utc:
        flags.add("timezone_missing")

    timezone_name = _text(record.get("zic_time_zone")) or _text(record.get("time_zone"))
    observed_datetime_utc = local.observed_datetime_utc or explicit_utc

    return TemporalObservation(
        source="inaturalist",
        source_occurrence_id=_source_id(record, ("id", "uuid")),
        observed_date=parsed.observed_date,
        observed_datetime=parsed.observed_datetime,
        observed_datetime_utc=observed_datetime_utc,
        interval_start=parsed.interval_start,
        interval_end=parsed.interval_end,
        timezone_name=timezone_name,
        utc_offset_minutes=parsed.utc_offset_minutes,
        temporal_precision=parsed.precision,
        clock_basis=parsed.clock_basis,
        year=parsed.year,
        month=parsed.month,
        day=parsed.day,
        day_of_year=parsed.day_of_year,
        hour=parsed.hour,
        minute=parsed.minute,
        second=parsed.second,
        raw_time_fields=raw,
        temporal_quality_flags=tuple(sorted(flags)),
    )


def normalize_occurrence_time(source: str, record: Mapping[str, Any]) -> TemporalObservation:
    """Dispatch to a source-specific observation-time normalizer."""

    key = str(source).strip().lower()
    if key == "gbif":
        return normalize_gbif_time(record)
    if key in {"inaturalist", "inat", "i_naturalist"}:
        return normalize_inaturalist_time(record)
    raise ValueError(f"unsupported temporal occurrence source: {source}")
