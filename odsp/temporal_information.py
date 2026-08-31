"""Source-preserving temporal information for biodiversity occurrences.

Observation time is normalized without turning upload/ingestion timestamps into
biological time and without silently increasing temporal precision.
"""
from __future__ import annotations

from dataclasses import asdict, dataclass
from datetime import date, datetime, time, timezone
import re
from typing import Any, Mapping


PRECISIONS = {"unknown", "year", "month", "day", "minute", "second", "interval"}

GBIF_TIME_FIELDS = (
    "eventDate",
    "eventTime",
    "year",
    "month",
    "day",
    "startDayOfYear",
    "endDayOfYear",
    "verbatimEventDate",
)
INAT_TIME_FIELDS = (
    "observed_on",
    "observed_on_string",
    "time_observed_at",
    "time_observed_at_utc",
    "time_zone",
    "zic_time_zone",
)
INAT_MANAGEMENT_FIELDS = (
    "created_at",
    "updated_at",
    "created_at_utc",
    "updated_at_utc",
)


@dataclass(frozen=True)
class TemporalObservation:
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
        if self.temporal_precision not in PRECISIONS:
            raise ValueError(f"unknown temporal precision: {self.temporal_precision}")

    def as_dict(self) -> dict[str, Any]:
        return asdict(self)


@dataclass(frozen=True)
class _Parsed:
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
    try:
        return None if value in (None, "") else int(value)
    except (TypeError, ValueError):
        return None


def _python_iso(raw: str) -> str:
    return raw[:-1] + "+00:00" if raw.endswith("Z") else raw


def _clock_precision(raw: str) -> str:
    match = re.search(r"[T ]\d{2}:\d{2}(?::\d{2}(?:\.\d+)?)?", raw)
    if not match:
        return "unknown"
    return "second" if re.search(r"[T ]\d{2}:\d{2}:\d{2}", raw) else "minute"


def _offset_minutes(value: datetime) -> int | None:
    offset = value.utcoffset()
    return None if offset is None else int(offset.total_seconds() // 60)


def _format_datetime(value: datetime, precision: str, *, utc: bool = False) -> str:
    timespec = "seconds" if precision == "second" else "minutes"
    text = value.isoformat(timespec=timespec)
    return text.replace("+00:00", "Z") if utc else text


def _parsed_datetime(value: datetime, raw: str, clock_basis: str) -> _Parsed:
    precision = _clock_precision(raw)
    if precision == "unknown":
        return _Parsed()
    aware = value.utcoffset() is not None
    utc_value = value.astimezone(timezone.utc) if aware else None
    basis = clock_basis
    if not aware:
        basis = "source_local_unknown_timezone"
    elif _offset_minutes(value) == 0:
        basis = "utc"
    return _Parsed(
        observed_date=value.date().isoformat(),
        observed_datetime=_format_datetime(value, precision),
        observed_datetime_utc=(
            _format_datetime(utc_value, precision, utc=True) if utc_value is not None else None
        ),
        utc_offset_minutes=_offset_minutes(value),
        precision=precision,
        clock_basis=basis,
        year=value.year,
        month=value.month,
        day=value.day,
        day_of_year=value.timetuple().tm_yday,
        hour=value.hour,
        minute=value.minute,
        second=value.second if precision == "second" else None,
    )


def _parse_single(value: Any, *, clock_basis: str = "source") -> _Parsed:
    raw = _text(value)
    if raw is None:
        return _Parsed()
    if re.fullmatch(r"\d{4}", raw):
        return _Parsed(observed_date=raw, precision="year", clock_basis="date_only", year=int(raw))
    if re.fullmatch(r"\d{4}-\d{2}", raw):
        year, month = map(int, raw.split("-"))
        if not 1 <= month <= 12:
            return _Parsed()
        return _Parsed(
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
            return _Parsed()
        return _Parsed(
            observed_date=raw,
            precision="day",
            clock_basis="date_only",
            year=parsed.year,
            month=parsed.month,
            day=parsed.day,
            day_of_year=parsed.timetuple().tm_yday,
        )
    try:
        parsed = datetime.fromisoformat(_python_iso(raw))
    except ValueError:
        return _Parsed()
    return _parsed_datetime(parsed, raw, clock_basis)


def _parse(value: Any, *, clock_basis: str = "source") -> _Parsed:
    raw = _text(value)
    if raw is None:
        return _Parsed()
    if "/" in raw:
        left, right = raw.split("/", 1)
        start = _parse_single(left)
        end = _parse_single(right)
        return _Parsed(
            interval_start=start.observed_datetime or start.observed_date or _text(left),
            interval_end=end.observed_datetime or end.observed_date or _text(right),
            precision="interval",
            clock_basis="interval",
        )
    return _parse_single(raw, clock_basis=clock_basis)


def _event_time(value: Any) -> tuple[time | None, str]:
    raw = _text(value)
    if raw is None or "/" in raw:
        return None, "unknown"
    try:
        parsed = time.fromisoformat(_python_iso(raw))
    except ValueError:
        return None, "unknown"
    precision = "second" if re.match(r"^\d{2}:\d{2}:\d{2}", raw) else "minute"
    return parsed, precision


def _add_event_time(base: _Parsed, value: Any) -> _Parsed:
    if base.precision != "day" or None in (base.year, base.month, base.day):
        return base
    parsed_time, precision = _event_time(value)
    if parsed_time is None:
        return base
    combined = datetime.combine(date(base.year, base.month, base.day), parsed_time)
    raw = _format_datetime(combined, precision)
    basis = "source_local_unknown_timezone"
    if parsed_time.utcoffset() is not None:
        basis = "utc" if int(parsed_time.utcoffset().total_seconds()) == 0 else "source_offset"
    return _parsed_datetime(combined, raw, basis)


def _from_components(year: int | None, month: int | None, day: int | None) -> _Parsed:
    if year is None:
        return _Parsed()
    if month is None:
        return _parse_single(f"{year:04d}")
    if day is None:
        return _parse_single(f"{year:04d}-{month:02d}")
    return _parse_single(f"{year:04d}-{month:02d}-{day:02d}")


def _date_tuple(value: _Parsed) -> tuple[int | None, int | None, int | None]:
    return value.year, value.month, value.day


def _source_id(record: Mapping[str, Any], names: tuple[str, ...]) -> str | None:
    for name in names:
        value = _text(record.get(name))
        if value is not None:
            return value
    return None


def _raw(record: Mapping[str, Any], names: tuple[str, ...]) -> dict[str, Any]:
    return {name: record[name] for name in names if record.get(name) not in (None, "")}


def _to_observation(
    *,
    source: str,
    occurrence_id: str | None,
    parsed: _Parsed,
    timezone_name: str | None,
    raw_fields: dict[str, Any],
    flags: set[str],
    explicit_utc: str | None = None,
) -> TemporalObservation:
    if parsed.precision == "interval":
        flags.add("interval")
    elif parsed.precision in {"year", "month", "day"}:
        flags.add("date_only")
    if parsed.precision == "unknown":
        flags.add("missing_or_unparsed_observation_time")
    if parsed.hour is not None and parsed.utc_offset_minutes is None and explicit_utc is None:
        flags.add("timezone_missing")
    return TemporalObservation(
        source=source,
        source_occurrence_id=occurrence_id,
        observed_date=parsed.observed_date,
        observed_datetime=parsed.observed_datetime,
        observed_datetime_utc=parsed.observed_datetime_utc or explicit_utc,
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
        raw_time_fields=raw_fields,
        temporal_quality_flags=tuple(sorted(flags)),
    )


def normalize_gbif_time(record: Mapping[str, Any]) -> TemporalObservation:
    """Normalize GBIF Darwin Core event-time fields."""

    flags: set[str] = set()
    parsed = _parse(record.get("eventDate"), clock_basis="source_offset")
    components = _from_components(
        _integer(record.get("year")),
        _integer(record.get("month")),
        _integer(record.get("day")),
    )
    if parsed.precision == "unknown" and components.precision != "unknown":
        parsed = components
    elif parsed.precision not in {"unknown", "interval"} and components.precision == "day":
        if _date_tuple(parsed) != _date_tuple(components):
            flags.add("date_field_mismatch")

    if record.get("eventTime") not in (None, ""):
        if parsed.precision == "day":
            enriched = _add_event_time(parsed, record.get("eventTime"))
            if enriched.precision == "day":
                flags.add("unparsed_event_time")
            else:
                parsed = enriched
        elif parsed.precision in {"year", "month", "unknown"}:
            flags.add("time_without_complete_date")

    return _to_observation(
        source="gbif",
        occurrence_id=_source_id(record, ("key", "gbifID", "occurrenceID")),
        parsed=parsed,
        timezone_name=None,
        raw_fields=_raw(record, GBIF_TIME_FIELDS),
        flags=flags,
    )


def normalize_inaturalist_time(record: Mapping[str, Any]) -> TemporalObservation:
    """Normalize iNaturalist observation time without using record-management time."""

    flags: set[str] = set()
    local = _parse(record.get("time_observed_at"), clock_basis="source_offset")
    utc_value = _parse(record.get("time_observed_at_utc"), clock_basis="utc")
    observed_date = _parse(record.get("observed_on"))

    if local.precision != "unknown":
        parsed = local
    elif observed_date.precision != "unknown":
        parsed = observed_date
    elif utc_value.precision != "unknown":
        parsed = utc_value
    else:
        parsed = _Parsed()

    if parsed.precision not in {"unknown", "interval"} and observed_date.precision == "day":
        if _date_tuple(parsed) != _date_tuple(observed_date):
            flags.add("date_field_mismatch")

    explicit_utc = utc_value.observed_datetime_utc or utc_value.observed_datetime
    if local.observed_datetime_utc and explicit_utc:
        try:
            left = datetime.fromisoformat(_python_iso(local.observed_datetime_utc))
            right = datetime.fromisoformat(_python_iso(explicit_utc))
            if abs((left - right).total_seconds()) > 1:
                flags.add("utc_timestamp_mismatch")
        except ValueError:
            flags.add("unparsed_utc_timestamp")

    if parsed.precision == "unknown" and any(
        record.get(name) not in (None, "") for name in INAT_MANAGEMENT_FIELDS
    ):
        flags.add("record_management_timestamp_present_not_used")

    return _to_observation(
        source="inaturalist",
        occurrence_id=_source_id(record, ("id", "uuid")),
        parsed=parsed,
        timezone_name=_text(record.get("zic_time_zone")) or _text(record.get("time_zone")),
        raw_fields=_raw(record, INAT_TIME_FIELDS),
        flags=flags,
        explicit_utc=explicit_utc,
    )


def normalize_occurrence_time(source: str, record: Mapping[str, Any]) -> TemporalObservation:
    """Normalize observation-time metadata for one supported occurrence source."""

    key = str(source).strip().lower()
    if key == "gbif":
        return normalize_gbif_time(record)
    if key in {"inaturalist", "inat", "i_naturalist"}:
        return normalize_inaturalist_time(record)
    raise ValueError(f"unsupported temporal occurrence source: {source}")
