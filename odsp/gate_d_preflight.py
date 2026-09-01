"""Outcome-blind structural preflight for the frozen Tawaki Gate-D contract.

The functions in this module may inspect source identity, denominators, frozen
filter eligibility, cluster structure and location availability.  They must not
calculate depth-bin distributions, niche thickness, projection loss or sealed
scores.
"""
from __future__ import annotations

from collections import Counter, defaultdict
from dataclasses import asdict, dataclass
import hashlib
import math
from typing import Iterable, Mapping

from .gate_d_contract import deterministic_bird_split


@dataclass(frozen=True)
class SourceStratumSummary:
    site: str
    year: str
    rows: int
    qualifying_rows: int
    birds: int
    bird_trips: int

    def as_dict(self) -> dict[str, object]:
        return asdict(self)


@dataclass(frozen=True)
class LocationCoverageSummary:
    site: str
    year: str
    qualifying_dive_rows: int
    location_resolved_rows: int
    coverage_fraction: float | None

    def as_dict(self) -> dict[str, object]:
        return asdict(self)


def git_blob_sha1(data: bytes) -> str:
    """Return Git's content-addressed SHA-1 for raw blob bytes."""

    header = f"blob {len(data)}\0".encode("ascii")
    return hashlib.sha1(header + data).hexdigest()


def sha256_hex(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def _text(row: Mapping[str, object], key: str) -> str:
    value = row.get(key)
    return "" if value is None else str(value).strip()


def _site(row: Mapping[str, object]) -> str:
    value = _text(row, "Site") or _text(row, "Colony")
    if not value:
        raise ValueError("row requires Site or Colony")
    return value


def _float_or_none(value: object) -> float | None:
    try:
        number = float(value)
    except (TypeError, ValueError):
        return None
    return number if math.isfinite(number) else None


def _bird_trip(row: Mapping[str, object]) -> str:
    bird = _text(row, "birdID")
    trip = _text(row, "TripNumber")
    if not bird or not trip:
        raise ValueError("row requires birdID and TripNumber")
    return f"{bird}|{trip}"


def dive_row_qualifies(row: Mapping[str, object]) -> bool:
    """Apply only the already-frozen source event threshold."""

    depth = _float_or_none(row.get("Depth"))
    duration = _float_or_none(row.get("Duration"))
    return bool(
        depth is not None
        and duration is not None
        and depth >= 0.5
        and duration >= 5.0
    )


def linked_row_qualifies(row: Mapping[str, object]) -> bool:
    """Apply frozen threshold to linked events without binning z."""

    depth = _float_or_none(row.get("EvtMaxDepth"))
    duration = _float_or_none(row.get("DiveTime"))
    return bool(
        depth is not None
        and duration is not None
        and depth >= 0.5
        and duration >= 5.0
    )


def row_has_finite_xy(row: Mapping[str, object]) -> bool:
    lat = _float_or_none(row.get("Lat"))
    lon = _float_or_none(row.get("Lon"))
    return bool(
        lat is not None
        and lon is not None
        and -90.0 <= lat <= 90.0
        and -180.0 <= lon <= 180.0
    )


def summarize_dive_strata(
    rows: Iterable[Mapping[str, object]],
) -> tuple[SourceStratumSummary, ...]:
    buckets: dict[tuple[str, str], dict[str, object]] = defaultdict(
        lambda: {"rows": 0, "qualifying": 0, "birds": set(), "trips": set()}
    )
    for row in rows:
        site = _site(row)
        year = _text(row, "Year")
        bird = _text(row, "birdID")
        if not year or not bird:
            raise ValueError("dive row requires Year and birdID")
        bucket = buckets[(site, year)]
        bucket["rows"] += 1
        bucket["birds"].add(bird)
        bucket["trips"].add(_bird_trip(row))
        if dive_row_qualifies(row):
            bucket["qualifying"] += 1

    return tuple(
        SourceStratumSummary(
            site=site,
            year=year,
            rows=int(bucket["rows"]),
            qualifying_rows=int(bucket["qualifying"]),
            birds=len(bucket["birds"]),
            bird_trips=len(bucket["trips"]),
        )
        for (site, year), bucket in sorted(buckets.items())
    )


def infer_bird_year_sites(
    dive_rows: Iterable[Mapping[str, object]],
) -> dict[tuple[str, str], str]:
    """Map each bird-year to its all-dive source site; conflicting sites fail."""

    sites: dict[tuple[str, str], set[str]] = defaultdict(set)
    for row in dive_rows:
        bird = _text(row, "birdID")
        year = _text(row, "Year")
        if not bird or not year:
            raise ValueError("dive row requires birdID and Year")
        sites[(bird, year)].add(_site(row))

    result: dict[tuple[str, str], str] = {}
    for key, values in sorted(sites.items()):
        if len(values) != 1:
            raise ValueError(f"bird-year {key} maps to multiple sites: {sorted(values)}")
        result[key] = next(iter(values))
    return result


def summarize_location_coverage(
    dive_rows: Iterable[Mapping[str, object]],
    linked_rows: Iterable[Mapping[str, object]],
) -> tuple[LocationCoverageSummary, ...]:
    """Compare all qualifying dives with qualifying rows carrying finite x-y.

    This is a structural observation-process denominator only.  No depth state
    frequencies are returned.
    """

    dive_rows = list(dive_rows)
    linked_rows = list(linked_rows)
    bird_sites = infer_bird_year_sites(dive_rows)
    denominator: Counter[tuple[str, str]] = Counter()
    numerator: Counter[tuple[str, str]] = Counter()

    for row in dive_rows:
        if dive_row_qualifies(row):
            denominator[(_site(row), _text(row, "Year"))] += 1

    for row in linked_rows:
        if not linked_row_qualifies(row) or not row_has_finite_xy(row):
            continue
        bird = _text(row, "birdID")
        year = _text(row, "Year")
        key = (bird, year)
        if key not in bird_sites:
            raise ValueError(f"linked bird-year {key} absent from all-dive source")
        numerator[(bird_sites[key], year)] += 1

    keys = sorted(set(denominator) | set(numerator))
    output: list[LocationCoverageSummary] = []
    for site, year in keys:
        den = int(denominator[(site, year)])
        num = int(numerator[(site, year)])
        if num > den:
            raise ValueError(
                f"located qualifying rows exceed all-dive denominator for {site}/{year}"
            )
        output.append(
            LocationCoverageSummary(
                site=site,
                year=year,
                qualifying_dive_rows=den,
                location_resolved_rows=num,
                coverage_fraction=(None if den == 0 else num / den),
            )
        )
    return tuple(output)


def frozen_split_from_all_dives(
    dive_rows: Iterable[Mapping[str, object]],
) -> dict[tuple[str, str, str], str]:
    """Create the contract's whole-bird split from all observed source birds."""

    unique: dict[tuple[str, str, str], dict[str, object]] = {}
    for row in dive_rows:
        site = _site(row)
        year = _text(row, "Year")
        bird = _text(row, "birdID")
        if not year or not bird:
            raise ValueError("dive row requires Year and birdID")
        unique[(site, year, bird)] = {"Site": site, "Year": year, "birdID": bird}
    return deterministic_bird_split(unique.values())
