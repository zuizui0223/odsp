#!/usr/bin/env python3
"""Structural GPS eligibility screening without reading numeric altitude outcomes.

Source files are archived annual .csv.gz Movebank GPS event exports. This
screen consumes timestamps, individual aliases, GPS x-y, ground speed and the
source-marked outlier flag. It deliberately NEVER accesses altitude, its error,
its values, their missingness, or any inferred vertical effect.
"""
from __future__ import annotations

import argparse
import csv
from collections import Counter, defaultdict
import gzip
import hashlib
import json
import math
from pathlib import Path
import re

from pyproj import Transformer

DATE_PATTERN = re.compile(r"^\d{4}-\d{2}-\d{2}[ T]\d{2}:\d{2}")
PRIMARY_MONTHS = {5, 6, 7}            # Fixed breeding-season proxy
PRIMARY_SPEED_MS = 5.0                 # Flight proxy, not flight-state truth
THIN_MINUTES = 5                       # One earliest flight GPS event per bin
GRID_METERS = 5000                     # Fixed 5-km projected x-y cells
MIN_EVENTS_PER_DAY = 50                # Already 5-min thinned events
MIN_TRAIN_PER_CELL = 10                # Same animal, other day(s)
MIN_OTHER_PER_CELL = 10                # Other conspecific(s), same year
MIN_REPEATED_DAYS = 2
MIN_ELIGIBLE_ANIMALS_SOURCE = 10

SOURCE_CRS = {
    "lbbg": "EPSG:32632",             # North Sea / Schiermonnikoog
    "medgull": "EPSG:32631",          # Antwerp
}


def truthy_outlier(value: str) -> bool:
    return (value or "").strip().lower() in {"true", "t", "1", "yes", "y"}


def utc_day_and_bin(value: str):
    """Parse only immutable ISO-like temporal fields (not any vertical state)."""
    s = (value or "").strip()
    if not DATE_PATTERN.match(s):
        return None
    y, m, d = int(s[0:4]), int(s[5:7]), int(s[8:10])
    hour, minute = int(s[11:13]), int(s[14:16])
    if not (1 <= m <= 12 and 1 <= d <= 31 and 0 <= hour < 24 and 0 <= minute < 60):
        return None
    return f"{y:04d}-{m:02d}-{d:02d}", hour * (60 // THIN_MINUTES) + minute // THIN_MINUTES, m


def audit_one_year(path: Path, source: str, expected_year: int) -> dict:
    if source not in SOURCE_CRS:
        raise ValueError("Unknown source name")
    transformer = Transformer.from_crs("EPSG:4326", SOURCE_CRS[source], always_xy=True)

    counts = Counter()
    # Only x-y cell indices are retained; no elevation, altitude or dive values.
    by_day_bin = {}   # (id, day, 5-min-bin) -> (UTC-time-string, horizontal-cell)
    with gzip.open(path, "rt", encoding="utf-8-sig", newline="") as stream:
        reader = csv.DictReader(stream)
        names = set(reader.fieldnames or [])
        essential = {
            "timestamp", "location-long", "location-lat",
            "ground-speed", "individual-local-identifier",
        }
        if not essential.issubset(names):
            raise ValueError(f"{path.name} missing non-vertical fields {sorted(essential - names)}")
        outlier_fields = sorted(names & {"import-marked-outlier", "manually-marked-outlier"})
        for r in reader:
            counts["all_rows"] += 1
            # IMPORTANT: r["height-above-msl"] must never be accessed here.
            if any(truthy_outlier(r.get(c, "")) for c in outlier_fields):
                counts["source_marked_outliers"] += 1
                continue
            parsed = utc_day_and_bin(r.get("timestamp", ""))
            if not parsed:
                counts["bad_timestamp"] += 1
                continue
            date, time_bin, month = parsed
            if int(date[0:4]) != expected_year:
                counts["mismatched_year"] += 1
                continue
            if month not in PRIMARY_MONTHS:
                counts["outside_primary_months"] += 1
                continue
            ind = (r.get("individual-local-identifier") or "").strip()
            if not ind:
                counts["missing_individual"] += 1
                continue
            try:
                lon = float(r["location-long"])
                lat = float(r["location-lat"])
            except (TypeError, ValueError):
                counts["missing_xy"] += 1
                continue
            if not (math.isfinite(lon) and math.isfinite(lat) and -180 <= lon <= 180 and -90 <= lat <= 90):
                counts["bad_xy"] += 1
                continue
            counts["breeding_month_xy_id_rows"] += 1
            try:
                speed = float(r["ground-speed"])
            except (TypeError, ValueError):
                counts["missing_speed"] += 1
                continue
            if not math.isfinite(speed):
                counts["nonfinite_speed"] += 1
                continue
            counts["speed_reported"] += 1
            if speed < PRIMARY_SPEED_MS or speed > 55:
                counts["not_flight_speed_proxy"] += 1
                continue
            x, y = transformer.transform(lon, lat)
            if not (math.isfinite(x) and math.isfinite(y)):
                counts["projected_xy_failed"] += 1
                continue
            cell = (math.floor(x / GRID_METERS), math.floor(y / GRID_METERS))
            t = (r.get("timestamp") or "").strip()
            key = (ind, date, time_bin)
            current = by_day_bin.get(key)
            if current is None or t < current[0]:
                by_day_bin[key] = (t, cell)
            counts["flight_proxy_raw_rows"] += 1

    by_day_cell = Counter()
    by_id_cell = Counter()
    by_cell = Counter()
    birds_by_cell = defaultdict(set)
    days_by_id = defaultdict(set)
    for (ind, day, _), (_, cell) in by_day_bin.items():
        by_day_cell[ind, day, cell] += 1
        by_id_cell[ind, cell] += 1
        by_cell[cell] += 1
        birds_by_cell[cell].add(ind)
        days_by_id[ind].add(day)

    day_scored = Counter()
    raw_days = Counter()
    for (ind, day, cell), n in by_day_cell.items():
        raw_days[ind, day] += n
        if by_id_cell[ind, cell] - n >= MIN_TRAIN_PER_CELL and (
            by_cell[cell] - by_id_cell[ind] >= MIN_OTHER_PER_CELL
        ):
            day_scored[ind, day] += n
    repeated_days = Counter()
    for (ind, day), n in day_scored.items():
        if n >= MIN_EVENTS_PER_DAY:
            repeated_days[ind] += 1
    eligible_ids = sorted(i for i, days in repeated_days.items() if days >= MIN_REPEATED_DAYS)

    return {
        "year": expected_year,
        "gps_file": path.name,
        "gzip_sha256": _digest(path),
        "counts": dict(sorted(counts.items())),
        "flight_proxy_5min_unique_bins": len(by_day_bin),
        "individuals_with_flight_proxy": len(days_by_id),
        "individuals_with_2_raw_days_50_bins": len({
            i for i in days_by_id
            if sum(v >= MIN_EVENTS_PER_DAY for (j, d), v in raw_days.items() if i == j) >= 2
        }),
        "individuals_with_2_scorable_days_50_bins": len(eligible_ids),
        "scorable_heldout_days": sum(
            n >= MIN_EVENTS_PER_DAY and i in eligible_ids
            for (i, d), n in day_scored.items()
        ),
        "support_cells_5km": len(by_cell),
        "eligible_animal_ids_internal": eligible_ids,
        "eligible_roster_fingerprint": hashlib.sha256(
            ("\n".join(eligible_ids)).encode("utf-8")
        ).hexdigest(),
        "horizontal_overlap_screen": "other-day_self>=10_and_same-year_other-conspecific>=10_per_cell",
    }


def _digest(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as f:
        for chunk in iter(lambda: f.read(1024 * 1024), b""):
            h.update(chunk)
    return h.hexdigest()


def audit_files(source: str, paths: list[Path]) -> dict:
    result = []
    seen = set()
    for path in sorted(paths):
        try:
            year = int(re.search(r"-gps-(\d{4})\.csv\.gz$", path.name).group(1))
        except (AttributeError, ValueError) as e:
            raise ValueError(f"Bad annual GPS basename: {path.name}") from e
        if year in seen:
            raise ValueError("Duplicate year in source")
        seen.add(year)
        result.append(audit_one_year(path, source, year))
    ids = {x for a in result for x in a["eligible_animal_ids_internal"]}
    output_years = []
    for a in result:
        public = {k: v for k, v in a.items() if k != "eligible_animal_ids_internal"}
        output_years.append(public)
    return {
        "source": source,
        "frozen_rule_version": "prospective-cross-taxon-gps-support-v1",
        "status": "XY_TIME_FLIGHT_PROXY_SCREEN_ONLY",
        "gps_altitude_values_read": False,
        "gps_altitude_missingness_tested": False,
        "vertical_shape_tested": False,
        "breeding_month_proxy": "May-July UTC",
        "flight_proxy": "source_ground_speed_5_to_55_m_per_s",
        "thinning": "earliest_eligible_fix_per_bird_per_UTC_5min_bin",
        "grid": {"size_m": GRID_METERS, "projection": SOURCE_CRS[source]},
        "source_individuals_with_2_scorable_days_any_year": len(ids),
        "source_metadata_stage_potential": len(ids) >= MIN_ELIGIBLE_ANIMALS_SOURCE,
        "biological_study_admitted": False,
        "not_admission_reasons": [
            "vertical-field availability/quality withheld for later frozen gate",
            "biological flight-state independent corroboration unavailable",
            "tag-specific altitude calibration not completed",
            "all independent panel endpoints remain unopened",
        ],
        "by_year": output_years,
    }


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--source", required=True, choices=sorted(SOURCE_CRS))
    parser.add_argument("--gps", required=True, nargs="+", type=Path)
    parser.add_argument("--out", required=True, type=Path)
    ns = parser.parse_args()
    r = audit_files(ns.source, ns.gps)
    ns.out.parent.mkdir(exist_ok=True, parents=True)
    ns.out.write_text(json.dumps(r, sort_keys=True, indent=2) + "\n", encoding="utf-8")
    print(f"{ns.source}: {r['source_individuals_with_2_scorable_days_any_year']} candidate individuals;"
          f" stage candidate={r['source_metadata_stage_potential']};"
          " no altitude outcomes opened")


if __name__ == "__main__":
    main()
