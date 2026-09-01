"""Outcome-blind structural preflight for the selected Chapter-N2 bat lane.

The module is deliberately unable to compute altitude distributions or niche
thickness. A native height field is inspected only for presence/missingness;
its values are never converted to numbers here.
"""
from __future__ import annotations

from collections import defaultdict
from dataclasses import asdict, dataclass
from datetime import datetime, timezone
import hashlib
import math
from typing import Callable, Iterable, Mapping, Sequence

HEIGHT_FIELD_PRIORITY = (
    "height_above_mean_sea_level",
    "height_above_ellipsoid",
    "height_raw",
)


@dataclass(frozen=True)
class BatStructuralPreflightSummary:
    native_height_field: str
    total_events: int
    individual_count: int
    events_with_finite_xy: int
    events_with_height_present: int
    events_with_xy_and_height_present: int
    consecutive_interval_count: int
    intervals_20_40_seconds: int
    intervals_gt_40_seconds: int
    nonpositive_or_duplicate_intervals: int
    schedule_conformance_fraction: float | None
    sealed_individual_count: int
    model_individual_count: int
    model_pool_cells_with_any_event: int
    model_pool_estimable_cells: int
    structural_available: bool
    reasons: tuple[str, ...]
    fingerprint: str

    def as_dict(self) -> dict[str, object]:
        return asdict(self)


def resolve_native_height_field(attribute_names: Iterable[str]) -> str:
    """Resolve the primary native GPS height field without inspecting values."""

    available = {str(name).strip() for name in attribute_names}
    for field in HEIGHT_FIELD_PRIORITY:
        if field in available:
            return field
    raise ValueError("no frozen-priority native GPS height field is present")


def deterministic_individual_split(
    individual_ids: Iterable[str], *, sealed_fraction: float = 0.25
) -> dict[str, str]:
    """Assign whole individuals deterministically without reading axis values."""

    unique = sorted({str(value).strip() for value in individual_ids if str(value).strip()})
    if not unique:
        raise ValueError("no individual identifiers")
    if not 0.0 < sealed_fraction < 1.0:
        raise ValueError("sealed_fraction must lie strictly between 0 and 1")
    ordered = sorted(
        unique,
        key=lambda value: hashlib.sha256(
            f"odsp-n2-bat-v1|{value}".encode("utf-8")
        ).hexdigest(),
    )
    sealed_n = max(1, math.ceil(sealed_fraction * len(ordered)))
    if sealed_n >= len(ordered):
        raise ValueError("whole-individual split leaves no model individuals")
    sealed = set(ordered[:sealed_n])
    return {value: ("sealed" if value in sealed else "model") for value in unique}


def _text(row: Mapping[str, object], key: str) -> str:
    value = row.get(key)
    return "" if value is None else str(value).strip()


def _individual(row: Mapping[str, object]) -> str:
    value = _text(row, "individual_local_identifier") or _text(row, "individual_id")
    if not value:
        raise ValueError("event lacks individual identifier")
    return value


def _finite_float(value: object) -> float | None:
    try:
        number = float(value)
    except (TypeError, ValueError):
        return None
    return number if math.isfinite(number) else None


def _parse_timestamp(value: object) -> datetime:
    text = "" if value is None else str(value).strip()
    if not text:
        raise ValueError("event lacks timestamp")
    normalized = text.replace("Z", "+00:00")
    try:
        timestamp = datetime.fromisoformat(normalized)
    except ValueError as exc:
        raise ValueError(f"unsupported timestamp: {text!r}") from exc
    if timestamp.tzinfo is None:
        timestamp = timestamp.replace(tzinfo=timezone.utc)
    return timestamp.astimezone(timezone.utc)


def _has_height(row: Mapping[str, object], field: str) -> bool:
    # Presence only: do not parse, compare, bin, summarize or otherwise inspect
    # the numerical height value.
    return bool(_text(row, field))


def summarize_bat_structural_preflight(
    rows: Sequence[Mapping[str, object]],
    *,
    native_height_field: str,
    projector: Callable[[float, float], tuple[float, float]],
    cell_size_m: float = 5000.0,
    minimum_events_per_cell: int = 30,
    minimum_distinct_model_individuals_per_cell: int = 3,
    minimum_estimable_primary_cells: int = 5,
    minimum_total_individuals_with_xy_and_height: int = 8,
) -> BatStructuralPreflightSummary:
    """Evaluate source/schedule/x-y support without opening the height outcome."""

    if native_height_field not in HEIGHT_FIELD_PRIORITY:
        raise ValueError("native_height_field violates frozen priority set")
    if cell_size_m <= 0:
        raise ValueError("cell_size_m must be positive")
    if not rows:
        raise ValueError("event stream is empty")

    individuals = [_individual(row) for row in rows]
    split = deterministic_individual_split(individuals)

    finite_xy = 0
    height_present = 0
    xy_height_present = 0
    xy_height_individuals: set[str] = set()
    timestamps_by_individual: dict[str, list[datetime]] = defaultdict(list)
    cell_buckets: dict[tuple[int, int], dict[str, object]] = defaultdict(
        lambda: {"events": 0, "individuals": set()}
    )

    for row in rows:
        individual = _individual(row)
        timestamp = _parse_timestamp(row.get("timestamp"))
        timestamps_by_individual[individual].append(timestamp)

        lat = _finite_float(row.get("location_lat"))
        lon = _finite_float(row.get("location_long"))
        has_xy = bool(
            lat is not None
            and lon is not None
            and -90.0 <= lat <= 90.0
            and -180.0 <= lon <= 180.0
        )
        has_height = _has_height(row, native_height_field)
        if has_xy:
            finite_xy += 1
        if has_height:
            height_present += 1
        if not (has_xy and has_height):
            continue

        xy_height_present += 1
        xy_height_individuals.add(individual)
        if split[individual] != "model":
            continue
        easting, northing = projector(float(lon), float(lat))
        if not (math.isfinite(easting) and math.isfinite(northing)):
            raise ValueError("projector returned non-finite coordinates")
        cell = (math.floor(easting / cell_size_m), math.floor(northing / cell_size_m))
        bucket = cell_buckets[cell]
        bucket["events"] += 1
        bucket["individuals"].add(individual)

    interval_total = 0
    interval_in_schedule = 0
    interval_long = 0
    interval_nonpositive = 0
    for timestamps in timestamps_by_individual.values():
        ordered = sorted(timestamps)
        for previous, current in zip(ordered, ordered[1:]):
            delta = (current - previous).total_seconds()
            interval_total += 1
            if delta <= 0:
                interval_nonpositive += 1
            elif 20.0 <= delta <= 40.0:
                interval_in_schedule += 1
            elif delta > 40.0:
                interval_long += 1

    estimable_cells = 0
    for bucket in cell_buckets.values():
        if (
            int(bucket["events"]) >= minimum_events_per_cell
            and len(bucket["individuals"]) >= minimum_distinct_model_individuals_per_cell
        ):
            estimable_cells += 1

    model_count = sum(1 for value in split.values() if value == "model")
    sealed_count = sum(1 for value in split.values() if value == "sealed")
    reasons: list[str] = []
    if len(xy_height_individuals) < minimum_total_individuals_with_xy_and_height:
        reasons.append("too_few_individuals_with_joint_xy_and_native_height_presence")
    if estimable_cells < minimum_estimable_primary_cells:
        reasons.append("too_few_estimable_primary_xy_cells")
    if interval_nonpositive:
        reasons.append("duplicate_or_nonpositive_timestamp_intervals_present")

    payload = {
        "native_height_field": native_height_field,
        "total_events": len(rows),
        "individual_count": len(set(individuals)),
        "events_with_finite_xy": finite_xy,
        "events_with_height_present": height_present,
        "events_with_xy_and_height_present": xy_height_present,
        "consecutive_interval_count": interval_total,
        "intervals_20_40_seconds": interval_in_schedule,
        "intervals_gt_40_seconds": interval_long,
        "nonpositive_or_duplicate_intervals": interval_nonpositive,
        "sealed_individual_count": sealed_count,
        "model_individual_count": model_count,
        "model_pool_cells_with_any_event": len(cell_buckets),
        "model_pool_estimable_cells": estimable_cells,
        "reasons": reasons,
    }
    fingerprint = hashlib.sha256(
        repr(sorted(payload.items())).encode("utf-8")
    ).hexdigest()

    return BatStructuralPreflightSummary(
        native_height_field=native_height_field,
        total_events=len(rows),
        individual_count=len(set(individuals)),
        events_with_finite_xy=finite_xy,
        events_with_height_present=height_present,
        events_with_xy_and_height_present=xy_height_present,
        consecutive_interval_count=interval_total,
        intervals_20_40_seconds=interval_in_schedule,
        intervals_gt_40_seconds=interval_long,
        nonpositive_or_duplicate_intervals=interval_nonpositive,
        schedule_conformance_fraction=(
            None if interval_total == 0 else interval_in_schedule / interval_total
        ),
        sealed_individual_count=sealed_count,
        model_individual_count=model_count,
        model_pool_cells_with_any_event=len(cell_buckets),
        model_pool_estimable_cells=estimable_cells,
        structural_available=not reasons,
        reasons=tuple(reasons),
        fingerprint=fingerprint,
    )
